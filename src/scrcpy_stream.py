import os
import socket
import struct
import subprocess
import threading
import time
from typing import Optional, Tuple
import av
import cv2
import numpy as np

from adb import get_adb_path, _format_target


def find_available_port(start_port: int = 27183) -> int:
    """Find a free TCP port on localhost starting from start_port."""
    for p in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


class ScrcpyStream:
    """
    Ultra-low latency screen capture streamer using scrcpy-server.
    Decodes raw H.264 stream at 30-60 FPS with ~15-20ms latency.
    """

    def __init__(self, device_serial: str, port: int = 27183, max_size: int = 1280, max_fps: int = 60):
        self.device_serial = device_serial
        self.base_port = port
        self.port = port
        self.max_size = max_size
        self.max_fps = max_fps
        self.adb = get_adb_path()

        self.proc: Optional[subprocess.Popen] = None
        self.video_sock: Optional[socket.socket] = None
        self.control_sock: Optional[socket.socket] = None

        self.latest_frame: Optional[np.ndarray] = None
        self.frame_width: int = 1280
        self.frame_height: int = 720
        self.fps: float = 0.0
        self.frame_count: int = 0
        self.last_frame_time: float = 0.0

        self.is_running: bool = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

    def _ensure_server_jar(self) -> str:
        """Ensure scrcpy-server.jar is pushed to Android storage."""
        local_jar = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "scrcpy-server.jar")
        if not os.path.isfile(local_jar):
            raise FileNotFoundError(f"scrcpy-server.jar not found at {local_jar}")

        target_jar = "/sdcard/scrcpy-server.jar"
        # Quick push to ensure it exists
        subprocess.run(
            [self.adb, "-s", self.device_serial, "push", local_jar, target_jar],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return target_jar

    def start(self) -> bool:
        """Start the scrcpy server and video streaming thread."""
        if self.is_running:
            return True

        try:
            target_jar = self._ensure_server_jar()

            # Ensure free port
            self.port = find_available_port(self.base_port)

            # 1. Setup adb forward for tcp:port -> localabstract:scrcpy
            subprocess.run(
                [self.adb, "-s", self.device_serial, "forward", f"tcp:{self.port}", "localabstract:scrcpy"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
            )

            # 2. Launch scrcpy-server on Android
            cmd = [
                self.adb, "-s", self.device_serial, "shell",
                f"CLASSPATH={target_jar}", "app_process", "/",
                "com.genymobile.scrcpy.Server", "2.4",
                "tunnel_forward=true", "video=true", "audio=false", "control=true",
                f"max_size={self.max_size}", f"max_fps={self.max_fps}", "raw_stream=true"
            ]
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            time.sleep(0.5)

            # 3. Connect Video Socket (Socket 1)
            self.video_sock = socket.socket()
            self.video_sock.settimeout(4.0)
            self.video_sock.connect(("127.0.0.1", self.port))

            # 4. Connect Control Socket (Socket 2)
            self.control_sock = socket.socket()
            self.control_sock.settimeout(4.0)
            self.control_sock.connect(("127.0.0.1", self.port))

            self.is_running = True
            self.worker_thread = threading.Thread(target=self._stream_worker, daemon=True)
            self.worker_thread.start()
            return True
        except Exception as e:
            print(f"[ScrcpyStream] Failed to start on {self.device_serial}: {e}")
            self.stop()
            return False

    def _stream_worker(self):
        """Worker thread decoding H.264 video packets continuously into memory."""
        codec = av.CodecContext.create("h264", "r")
        t_start = time.perf_counter()
        count = 0

        while self.is_running and self.video_sock:
            try:
                chunk = self.video_sock.recv(32768)
                if not chunk:
                    break

                packets = codec.parse(chunk)
                for packet in packets:
                    frames = codec.decode(packet)
                    for frame in frames:
                        img = frame.to_ndarray(format="bgr24")
                        with self.lock:
                            self.latest_frame = img
                            self.frame_height, self.frame_width = img.shape[:2]
                            self.last_frame_time = time.perf_counter()
                            count += 1
                            self.frame_count = count

                        if count % 30 == 0:
                            elapsed = time.perf_counter() - t_start
                            self.fps = count / elapsed if elapsed > 0 else 0.0

            except Exception as e:
                if self.is_running:
                    print(f"[ScrcpyStream] Worker error: {e}")
                break

        self.is_running = False

    def get_frame(self) -> Optional[np.ndarray]:
        """Returns the most recent decoded video frame (zero latency)."""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None

    def wait_for_frame(self, timeout: float = 3.0) -> Optional[np.ndarray]:
        """Wait until at least one frame is decoded and returned, or timeout."""
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < timeout:
            f = self.get_frame()
            if f is not None:
                return f
            time.sleep(0.04)
        return None


    def stop(self):
        """Stop streamer, close sockets and terminate server process."""
        self.is_running = False
        if self.video_sock:
            try:
                self.video_sock.close()
            except Exception:
                pass
            self.video_sock = None

        if self.control_sock:
            try:
                self.control_sock.close()
            except Exception:
                pass
            self.control_sock = None

        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None

        try:
            subprocess.run(
                [self.adb, "-s", self.device_serial, "forward", "--remove", f"tcp:{self.port}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
        except Exception:
            pass

