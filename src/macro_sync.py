"""
Shared timing anchors for macro recording and playback.

A recorded macro is a list of timestamps relative to t=0. Playback only matches
what the player pressed if recording and playback pick t=0 at the exact same
in-game moment, so every code path (recorder auto-flow, player navigation flow,
BotEngine loop) must anchor through these helpers.
"""

import threading
import time
from typing import Any, Optional, Tuple

# A scrcpy frame older than this is treated as stale (stream stalled/restarting).
STREAM_FRESH_SEC = 0.35

# Run-start anchor: wait for the "START!" banner to disappear.
RUN_START_TIMEOUT = 3.0

# Relay anchor: after tapping the relay button, wait for the relay banner to clear.
RELAY_SETTLE_TIMEOUT = 2.0

# In-run stage polling interval (identical for record and play so emulator load matches).
MONITOR_INTERVAL_STREAM = 0.5
MONITOR_INTERVAL_ADB = 2.0

# Stages that matter while the cookie is running.
IN_RUN_STAGES = ["GAME_RELAY", "GAME_COMPLETE", "MYSTERY_BOX", "CONGRATULATIONS"]


def warm_up_stream(target: str):
    """Start the scrcpy stream early so frames are live by the time we need an anchor."""
    try:
        from scrcpy_streamer import stream_manager
        stream_manager.get_streamer(target).get_latest_frame()
    except Exception:
        pass


def grab_frame(target: str, port: int, adb_fallback: bool = True) -> Tuple[Optional[Any], bool]:
    """Return (frame, is_stream). Prefers a fresh scrcpy frame; falls back to ADB screencap."""
    try:
        from scrcpy_streamer import stream_manager
        st = stream_manager.get_streamer(target)
        frame = st.get_latest_frame()
        frame_t = getattr(st, "latest_frame_perf", 0.0)
        if frame is not None and st.is_running and (time.perf_counter() - frame_t) <= STREAM_FRESH_SEC:
            return frame, True
    except Exception:
        pass
    if not adb_fallback:
        return None, False
    from adb import device_capture_screen
    return device_capture_screen(target, port), False


def _tap_async(target: str, port: int, x: int, y: int):
    """Fire a tap without blocking: the anchor is the visual result, so polling must start right away."""
    from actions import safe_device_tap
    threading.Thread(target=safe_device_tap, args=(target, port, x, y), daemon=True).start()


def wait_template_gone(target: str, port: int, templates, region, timeout: float) -> float:
    """Poll until `templates` are no longer visible in `region`; return perf_counter() of that moment."""
    from detection import detect_templates
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        frame, is_stream = grab_frame(target, port)
        if frame is not None and not detect_templates(frame, templates, region):
            return time.perf_counter()
        time.sleep(0.008 if is_stream else 0.02)
    return time.perf_counter()


def anchor_run_start(target: str, port: int, eng=None) -> float:
    """
    Called right after GAME_START is detected. Uses Fast Start (when enabled) without
    any random delay, then returns the t=0 anchor: the moment the START! banner clears.
    """
    from config import STAGE_GAME_START_TEMPLATE, STAGE_GAME_START_REGION
    if eng is not None and getattr(eng, "use_fast_start", False):
        from config import FAST_START_USE_BUTTON
        _tap_async(target, port, FAST_START_USE_BUTTON[0], FAST_START_USE_BUTTON[1])
    return wait_template_gone(target, port, STAGE_GAME_START_TEMPLATE, STAGE_GAME_START_REGION, RUN_START_TIMEOUT)


def anchor_relay_start(target: str, port: int, tap: bool = True) -> float:
    """Tap the relay button (no random delay) and return the t=0 anchor of the relay phase."""
    from config import COOKIE_RELAY_USE_BUTTON, STAGE_GAME_RELAY_TEMPLATE, STAGE_GAME_RELAY_REGION
    if tap:
        _tap_async(target, port, COOKIE_RELAY_USE_BUTTON[0], COOKIE_RELAY_USE_BUTTON[1])
    return wait_template_gone(target, port, STAGE_GAME_RELAY_TEMPLATE, STAGE_GAME_RELAY_REGION, RELAY_SETTLE_TIMEOUT)


def detect_in_run_stage(frame) -> Optional[str]:
    from detection import detect_stage
    return detect_stage(frame, stage_names=IN_RUN_STAGES)


class InRunMonitor:
    """
    Rate-limited in-run stage checker shared by recorder and player, so both put the
    same load on the emulator. Uses the free scrcpy frame when available and only falls
    back to a (stutter-inducing) ADB screencap every MONITOR_INTERVAL_ADB seconds.
    """

    def __init__(self, target: str, port: int):
        self.target = target
        self.port = port
        self._last_check = 0.0

    def poll(self) -> Optional[str]:
        now = time.perf_counter()
        frame, is_stream = grab_frame(self.target, self.port, adb_fallback=False)
        interval = MONITOR_INTERVAL_STREAM if is_stream else MONITOR_INTERVAL_ADB
        if now - self._last_check < interval:
            return None
        self._last_check = now
        if frame is None:
            from adb import device_capture_screen
            frame = device_capture_screen(self.target, self.port)
        if frame is None:
            return None
        return detect_in_run_stage(frame)
