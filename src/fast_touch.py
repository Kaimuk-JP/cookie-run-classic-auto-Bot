import os
import socket
import struct
import subprocess
import threading
import time
from typing import Optional


class FastTouchController:
    """
    Sub-millisecond touch injector using scrcpy binary control socket.
    Action latency is < 0.2 ms per command with automatic non-blocking ADB fallback.
    """

    # Scrcpy control message types (scrcpy v2.0+ standard: TYPE_INJECT_TOUCH_EVENT = 2)
    CONTROL_MSG_TYPE_INJECT_TOUCH_EVENT = 2

    # Android MotionEvent actions
    AMOTION_EVENT_ACTION_DOWN = 0
    AMOTION_EVENT_ACTION_UP = 1
    AMOTION_EVENT_ACTION_MOVE = 2

    # Scrcpy virtual pointer ID for generic finger touch
    POINTER_ID_GENERIC_FINGER = 0xFFFFFFFFFFFFFFFE

    # Standard CookieRun button coordinates (1280x720 base)
    # JUMP: Bottom-left round button center (Tapped: 143, 653)
    JUMP_X = 143
    JUMP_Y = 653

    # SLIDE: Bottom-right round button center (Tapped: 1130, 660)
    SLIDE_X = 1130
    SLIDE_Y = 660

    def __init__(
        self,
        control_sock: Optional[socket.socket] = None,
        screen_width: int = 1280,
        screen_height: int = 720,
        device_serial: Optional[str] = None,
    ):
        self.control_sock = control_sock
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.device_serial = device_serial
        self.is_sliding = False
        self.lock = threading.Lock()

    def set_socket(self, sock: socket.socket):
        with self.lock:
            self.control_sock = sock

    def inject_touch(
        self,
        action: int,
        x: int,
        y: int,
        pointer_id: int = POINTER_ID_GENERIC_FINGER,
    ):
        """
        Inject touch event via scrcpy v2 binary packet format (32 bytes total):
        Big-endian:
        - 1 byte:  msg_type (2 = TYPE_INJECT_TOUCH_EVENT)
        - 1 byte:  action (0=DOWN, 1=UP, 2=MOVE)
        - 8 bytes: pointer_id (uint64, 0xFFFFFFFFFFFFFFFE for generic finger)
        - 4 bytes: x (int32)
        - 4 bytes: y (int32)
        - 2 bytes: screen_width (uint16)
        - 2 bytes: screen_height (uint16)
        - 2 bytes: pressure (uint16, 0xFFFF=1.0 for down/move, 0 for up)
        - 4 bytes: action_button (int32, 0 for finger touch)
        - 4 bytes: buttons (int32, 0 for finger touch)
        """
        with self.lock:
            if not self.control_sock:
                self._fallback_touch(action, x, y)
                return

            pressure = 0xFFFF if action in (0, 2) else 0
            action_button = 0
            buttons = 0

            packet = struct.pack(
                ">BBQiiHHHii",
                self.CONTROL_MSG_TYPE_INJECT_TOUCH_EVENT,
                action,
                pointer_id,
                int(x),
                int(y),
                int(self.screen_width),
                int(self.screen_height),
                pressure,
                action_button,
                buttons,
            )
            try:
                self.control_sock.sendall(packet)
            except Exception:
                self._fallback_touch(action, x, y)

    def _fallback_touch(self, action: int, x: int, y: int):
        """Non-blocking ADB fallback if socket is temporarily unavailable."""
        if self.device_serial:
            try:
                from adb import get_adb_path

                adb = get_adb_path()
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                if action == self.AMOTION_EVENT_ACTION_DOWN:
                    subprocess.Popen(
                        [adb, "-s", self.device_serial, "shell", "input", "tap", str(int(x)), str(int(y))],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                    )
            except Exception:
                pass

    def tap(self, x: int, y: int, duration: float = 0.05):
        """Tap at (x, y) with a brief hold duration."""
        self.inject_touch(self.AMOTION_EVENT_ACTION_DOWN, x, y)
        if duration > 0:
            time.sleep(duration)
        self.inject_touch(self.AMOTION_EVENT_ACTION_UP, x, y)

    def jump(self):
        """Execute single jump instantly."""
        self.tap(self.JUMP_X, self.JUMP_Y, duration=0.05)

    def double_jump(self):
        """Execute double jump with optimal airtime interval."""
        self.jump()
        time.sleep(0.12)
        self.jump()

    def slide_down(self):
        """Hold slide button down (crouch)."""
        if not self.is_sliding:
            self.inject_touch(self.AMOTION_EVENT_ACTION_DOWN, self.SLIDE_X, self.SLIDE_Y)
            self.is_sliding = True

    def slide_up(self):
        """Release slide button (stand up)."""
        if self.is_sliding:
            self.inject_touch(self.AMOTION_EVENT_ACTION_UP, self.SLIDE_X, self.SLIDE_Y)
            self.is_sliding = False

