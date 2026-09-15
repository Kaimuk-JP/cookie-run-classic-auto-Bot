"""
High-Performance Screen Streamer using Scrcpy (H.264 Hardware Video Stream)
Supports 30 - 60 FPS real-time streaming with smart on-demand resource management.
"""

import collections
import logging
import threading
import time
from typing import Dict, Generator, Optional

import cv2
import numpy as np

import os
import sys

try:
    import scrcpy
except ImportError:
    scrcpy = None

if scrcpy is not None:
    # Ensure scrcpy finds scrcpy-server.jar in standalone/frozen exe environments
    _orig_deploy_server = getattr(scrcpy.Client, "_deploy_server", None)

    def _safe_deploy_server(self):
        try:
            from path_utils import get_project_root
            root = get_project_root()
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates = [
                os.path.join(root, "bin", "scrcpy-server.jar"),
                os.path.join(root, "scrcpy", "scrcpy-server.jar"),
                os.path.join(root, "scrcpy-server.jar"),
                os.path.join(exe_dir, "bin", "scrcpy-server.jar"),
                os.path.join(exe_dir, "scrcpy", "scrcpy-server.jar"),
                os.path.join(exe_dir, "scrcpy-server.jar"),
                getattr(scrcpy, "__file__", "") and os.path.join(os.path.dirname(scrcpy.__file__), "scrcpy-server.jar"),
            ]
            found_jar = None
            for c in candidates:
                if c and os.path.isfile(c):
                    found_jar = os.path.abspath(c)
                    break

            if found_jar and os.path.isfile(found_jar):
                local_size = os.path.getsize(found_jar)
                if self._remote_jar_size() != local_size:
                    self.device.push(found_jar, self._SERVER_REMOTE_PATH)
                server_ver = getattr(getattr(scrcpy, "core", None), "SCRCPY_SERVER_VERSION", "3.3.4")
                self._server_stream = self.device.shell(
                    [
                        "CLASSPATH=" + self._SERVER_REMOTE_PATH,
                        "app_process",
                        "/",
                        "com.genymobile.scrcpy.Server",
                        str(server_ver),
                        "log_level=info",
                        "video=true",
                        "audio=false",
                        "video_codec=h264",
                        f"max_size={self.max_width}",
                        f"video_bit_rate={self.bitrate}",
                        f"max_fps={self.max_fps}",
                        "tunnel_forward=true",
                        "control=true",
                        "display_id=0",
                        "show_touches=false",
                        f"stay_awake={'true' if self.stay_awake else 'false'}",
                        "power_off_on_close=false",
                        "clipboard_autosync=false",
                        "downsize_on_error=true",
                        "cleanup=true",
                        "power_on=true",
                        "send_device_meta=true",
                        "send_frame_meta=false",
                        "send_dummy_byte=true",
                        "send_codec_meta=true",
                    ],
                    stream=True,
                )
                self._server_stream.read(10)
                return
        except Exception as e:
            logger.warning(f"Safe deploy jar error: {e}")

        if _orig_deploy_server:
            return _orig_deploy_server(self)

    if _orig_deploy_server is not None:
        scrcpy.Client._deploy_server = _safe_deploy_server

logger = logging.getLogger("ScrcpyStreamer")


class ScrcpyDeviceStreamer:
    def __init__(self, device_serial: str, max_width: int = 1280, bitrate: int = 4000000, max_fps: int = 60):
        self.device_serial = device_serial.strip()
        self.max_width = max_width
        self.bitrate = bitrate
        self.max_fps = max_fps

        self.client: Optional[scrcpy.Client] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_jpeg: Optional[bytes] = None
        self.frame_event = threading.Event()

        self.subscribers: int = 0
        self.last_access_time: float = time.time()
        self.is_running: bool = False
        self.start_error: Optional[str] = None

        # FPS calculation - rolling 15 frames (~250ms) for responsive, dynamic live FPS telemetry
        self._frame_times = collections.deque(maxlen=15)
        self.current_fps: float = 0.0

    def _on_frame(self, frame: Optional[np.ndarray]):
        if frame is None or frame.size == 0:
            return

        now = time.time()
        self._frame_times.append(now)
        if len(self._frame_times) > 1:
            duration = self._frame_times[-1] - self._frame_times[0]
            if duration > 0:
                self.current_fps = round((len(self._frame_times) - 1) / duration, 1)

        self.latest_frame = frame
        # Encode to JPEG with quality 70 for fast transmission over localhost
        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            self.latest_jpeg = buffer.tobytes()
        except Exception:
            pass

        self.frame_event.set()
        self.frame_event.clear()

    def start(self) -> bool:
        with self._lock:
            if self.is_running and self.client is not None:
                self.last_access_time = time.time()
                return True

            if scrcpy is None:
                self.start_error = "scrcpy module not installed"
                return False

            try:
                self.start_error = None
                self.client = scrcpy.Client(
                    device=self.device_serial,
                    max_width=self.max_width,
                    bitrate=self.bitrate,
                    max_fps=self.max_fps,
                    block_frame=False,
                    connection_timeout=4000,
                )
                self.client.add_listener(scrcpy.EVENT_FRAME, self._on_frame)

                def run_loop():
                    try:
                        self.client.start()
                    except Exception as e:
                        self.start_error = str(e)
                    finally:
                        self.is_running = False

                self._thread = threading.Thread(
                    target=run_loop,
                    name=f"Scrcpy-{self.device_serial}",
                    daemon=True,
                )
                self._thread.start()
                self.is_running = True
                self.last_access_time = time.time()
                return True
            except Exception as e:
                self.start_error = str(e)
                self.is_running = False
                return False

    def stop(self):
        with self._lock:
            if not self.is_running and self.client is None:
                return
            try:
                if self.client:
                    self.client.stop()
            except Exception:
                pass
            finally:
                self.client = None
                self._thread = None
                self.is_running = False
                self.current_fps = 0.0

    def tap(self, x: int, y: int) -> bool:
        """Inject touch event through scrcpy control connection (< 1ms)."""
        if self.client and hasattr(self.client, "control") and self.client.control:
            try:
                self.client.control.touch(int(x), int(y), scrcpy.ACTION_DOWN)
                time.sleep(0.04)
                self.client.control.touch(int(x), int(y), scrcpy.ACTION_UP)
                return True
            except Exception:
                pass
        return False

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return the latest decoded frame from scrcpy video stream (zero overhead, pure RAM buffer)."""
        with self._lock:
            self.last_access_time = time.time()
            if not self.is_running:
                self.start()
        return self.latest_frame

    def add_subscriber(self):
        with self._lock:
            self.subscribers += 1
            self.last_access_time = time.time()
            if not self.is_running:
                self.start()

    def remove_subscriber(self):
        with self._lock:
            self.subscribers = max(0, self.subscribers - 1)
            self.last_access_time = time.time()

    def set_fps(self, fps: int):
        fps = max(10, min(60, fps))
        if fps != self.max_fps:
            self.max_fps = fps
            if self.is_running:
                # Restart with new FPS settings
                self.stop()
                self.start()

    def iter_mjpeg_frames(self, target_fps: int = 60) -> Generator[bytes, None, None]:
        """Yield multipart JPEG frames at target_fps (up to 60 FPS)."""
        self.add_subscriber()
        min_interval = 1.0 / max(1, target_fps)
        last_yield_time = 0.0
        try:
            while True:
                # Wait for next frame event or timeout
                self.frame_event.wait(timeout=0.1)
                now = time.time()
                if now - last_yield_time >= min_interval:
                    jpeg = self.latest_jpeg
                    if jpeg is not None:
                        last_yield_time = now
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                        )
                    else:
                        time.sleep(0.02)
        finally:
            self.remove_subscriber()


class ScrcpyStreamManager:
    """Manages streamers across multiple devices with auto-idle cleanup."""

    def __init__(self):
        self._streamers: Dict[str, ScrcpyDeviceStreamer] = {}
        self._lock = threading.Lock()
        self._cleaner_thread = threading.Thread(target=self._idle_cleaner_loop, daemon=True)
        self._cleaner_thread.start()

    def get_streamer(self, device_serial: str, max_fps: int = 60) -> ScrcpyDeviceStreamer:
        dev = str(device_serial).strip()
        with self._lock:
            if dev not in self._streamers:
                self._streamers[dev] = ScrcpyDeviceStreamer(dev, max_fps=max_fps)
            return self._streamers[dev]

    def _idle_cleaner_loop(self):
        """Stops scrcpy instances that have 0 viewers for more than 20 seconds."""
        while True:
            time.sleep(5)
            now = time.time()
            with self._lock:
                for dev, streamer in list(self._streamers.items()):
                    if streamer.is_running and streamer.subscribers <= 0:
                        if now - streamer.last_access_time > 20.0:
                            streamer.stop()

    def stop_all(self):
        with self._lock:
            for streamer in self._streamers.values():
                streamer.stop()


stream_manager = ScrcpyStreamManager()
