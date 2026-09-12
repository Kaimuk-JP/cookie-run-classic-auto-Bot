import os
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

from config import JUMP_BUTTON, SLIDE_BUTTON


class PersistentShellPipe:
    """
    Keeps a single long-lived ADB shell subprocess open to pipe input commands
    directly via stdin. Reduces ADB tap latency from 200ms down to ~15ms and
    prevents Windows process creation lag when tapping rapidly.
    """

    def __init__(self, target_serial: str):
        self.target_serial = str(target_serial).strip()
        self.proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._init_process()

    def _init_process(self):
        try:
            from adb import _format_target, get_adb_path

            adb = get_adb_path()
            target = _format_target(self.target_serial)
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            self.proc = subprocess.Popen(
                [adb, "-s", target, "shell"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except Exception:
            self.proc = None

    def send_tap(self, x: int, y: int):
        with self._lock:
            if not self.proc or self.proc.poll() is not None:
                self._init_process()
            if self.proc and self.proc.stdin:
                try:
                    cmd = f"input tap {int(x)} {int(y)}\n".encode("utf-8")
                    self.proc.stdin.write(cmd)
                    self.proc.stdin.flush()
                except Exception:
                    self._init_process()

    def send_swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int):
        with self._lock:
            if not self.proc or self.proc.poll() is not None:
                self._init_process()
            if self.proc and self.proc.stdin:
                try:
                    cmd = f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}\n".encode("utf-8")
                    self.proc.stdin.write(cmd)
                    self.proc.stdin.flush()
                except Exception:
                    self._init_process()

    def close(self):
        with self._lock:
            if self.proc:
                try:
                    self.proc.stdin.close()
                    self.proc.terminate()
                except Exception:
                    pass
                self.proc = None


class MacroPlayer:
    """
    High-precision Macro Player engine.
    Executes Jump, Double Jump, and Slide timelines with sub-millisecond precision.
    Uses Scrcpy Direct Socket (< 0.2ms) when available, falling back to Persistent ADB Shell Pipe.
    """

    JUMP_X = JUMP_BUTTON[0]
    JUMP_Y = JUMP_BUTTON[1]
    SLIDE_X = SLIDE_BUTTON[0]
    SLIDE_Y = SLIDE_BUTTON[1]

    def __init__(self, target_serial: str):
        self.target_serial = str(target_serial).strip()
        self.macro_data: Optional[Dict[str, Any]] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._play_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._shell_pipe: Optional[PersistentShellPipe] = None

    def _get_shell_pipe(self) -> PersistentShellPipe:
        if self._shell_pipe is None:
            self._shell_pipe = PersistentShellPipe(self.target_serial)
        return self._shell_pipe

    def _send_down(self, x: int, y: int):
        """Send Touch Down event."""
        # 1. Try Scrcpy control socket (< 0.2ms)
        try:
            from scrcpy_streamer import stream_manager

            streamer = stream_manager.get_streamer(self.target_serial)
            if streamer and streamer.client and hasattr(streamer.client, "control") and streamer.client.control:
                import scrcpy

                streamer.client.control.touch(int(x), int(y), scrcpy.ACTION_DOWN)
                return
        except Exception:
            pass

        # 2. Fallback to Persistent ADB Shell Pipe
        pass

    def _send_up(self, x: int, y: int):
        """Send Touch Up event."""
        try:
            from scrcpy_streamer import stream_manager

            streamer = stream_manager.get_streamer(self.target_serial)
            if streamer and streamer.client and hasattr(streamer.client, "control") and streamer.client.control:
                import scrcpy

                streamer.client.control.touch(int(x), int(y), scrcpy.ACTION_UP)
                return
        except Exception:
            pass

    def _send_tap(self, x: int, y: int, duration: float = 0.04):
        """Send instant Tap (< 0.2ms with scrcpy, ~15ms with persistent pipe)."""
        try:
            from scrcpy_streamer import stream_manager

            streamer = stream_manager.get_streamer(self.target_serial)
            if streamer and streamer.client and hasattr(streamer.client, "control") and streamer.client.control:
                import scrcpy

                streamer.client.control.touch(int(x), int(y), scrcpy.ACTION_DOWN)
                if duration > 0:
                    time.sleep(duration)
                streamer.client.control.touch(int(x), int(y), scrcpy.ACTION_UP)
                return
        except Exception:
            pass

        pipe = self._get_shell_pipe()
        pipe.send_tap(x, y)

    def _send_hold(self, x: int, y: int, duration_sec: float):
        """Hold touch position for duration_sec."""
        try:
            from scrcpy_streamer import stream_manager

            streamer = stream_manager.get_streamer(self.target_serial)
            if streamer and streamer.client and hasattr(streamer.client, "control") and streamer.client.control:
                import scrcpy

                streamer.client.control.touch(int(x), int(y), scrcpy.ACTION_DOWN)
                end_t = time.perf_counter() + duration_sec
                while time.perf_counter() < end_t and not self._stop_event.is_set():
                    time.sleep(0.02)
                streamer.client.control.touch(int(x), int(y), scrcpy.ACTION_UP)
                return
        except Exception:
            pass

        pipe = self._get_shell_pipe()
        duration_ms = int(duration_sec * 1000)
        pipe.send_swipe(x, y, x, y, duration_ms)
        time.sleep(max(0.01, duration_sec))

    def jump(self):
        self._send_tap(self.JUMP_X, self.JUMP_Y, duration=0.03)

    def double_jump(self, air_time: float = 0.16):
        eff_air = max(0.16, float(air_time))
        self.jump()
        time.sleep(eff_air)
        self.jump()

    def slide(self, duration_sec: float = 0.4):
        self._send_hold(self.SLIDE_X, self.SLIDE_Y, duration_sec)

    def start(self, macro_data: Dict[str, Any]):
        """Start playing the macro immediately in a dedicated high-priority timeline thread."""
        self.stop()
        if not macro_data or "actions" not in macro_data:
            return

        self.macro_data = macro_data
        self.is_running = True
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._playback_loop,
            name=f"MacroPlayer-{self.target_serial}",
            daemon=True,
        )
        self._thread.start()

    def start_with_navigation(
        self,
        macro_data: Dict[str, Any],
        device_serial: str,
        port: int = 5555,
        log_fn=None,
    ):
        """
        Full lifecycle macro runner:
        1. Checks current screen:
           - If on MAINMENU -> taps Play to enter item selection
           - If on PURCHASE_ITEM -> buys items per engine settings & taps Play to enter game
           - Waits for GAME_START / in-game screen
        2. Starts timeline macro execution at t=0.00s!
        3. Monitors for GAME_COMPLETE -> stops playback, skips animation, taps Replay!
        """
        self.stop()
        if not macro_data or "actions" not in macro_data:
            return

        self.macro_data = macro_data
        self.is_running = True
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._nav_playback_loop,
            args=(device_serial, port, log_fn),
            name=f"MacroPlayerNav-{self.target_serial}",
            daemon=True,
        )
        self._thread.start()

    def _nav_playback_loop(self, device_serial: str, port: int, log_fn=None):
        def log(msg, mtype="info"):
            if callable(log_fn):
                log_fn(msg, mtype)
            else:
                print(f"[{mtype.upper()}] {msg}")

        target = str(device_serial).strip() or self.target_serial
        t_port = port or 5555

        from actions import (
            set_device_context,
            start_game,
            play_game,
            configure_top_row_items,
            purchase_fast_start,
            purchase_cookie_relay,
            purchase_desired_random_boost,
            safe_device_tap,
        )
        from adb import device_capture_screen
        from detection import detect_stage, extract_item_stock
        from bot_engine import get_engine_for_device

        set_device_context(target, t_port)
        eng = get_engine_for_device(target)

        start_wait = time.time()
        last_action_t = 0.0
        items_configured = False
        in_game_started = False

        # Phase 1: Navigate from Lobby/Purchase into Game Room
        while not self._stop_event.is_set() and (time.time() - start_wait) < 60.0:
            now = time.time()
            if (now - last_action_t) < 1.2:
                time.sleep(0.2)
                continue

            try:
                screen = None
                try:
                    from scrcpy_streamer import stream_manager
                    st = stream_manager.get_streamer(target)
                    if st:
                        screen = st.get_latest_frame()
                except Exception:
                    pass

                if screen is None:
                    screen = device_capture_screen(target, t_port)

                if screen is not None:
                    stage = detect_stage(screen, stage_names=["MAINMENU", "PURCHASE_ITEM", "GAME_START"])

                    if stage == "MAINMENU":
                        log("🎮 [Macro Play] ตรวจพบหน้าล็อบบี้ -> กดปุ่ม Play (เริ่มเกม)...", "info")
                        start_game()
                        last_action_t = time.time()
                        items_configured = False
                        time.sleep(1.0)
                        continue

                    elif stage == "PURCHASE_ITEM":
                        if not items_configured:
                            log("🛒 [Macro Play] ตรวจพบหน้าเลือกไอเทม -> กำลังเลือกและซื้อไอเทมตามการตั้งค่า...", "info")
                            if eng:
                                try:
                                    configure_top_row_items(
                                        screen,
                                        use_hp=getattr(eng, "use_hp_boost", False),
                                        use_extension=getattr(eng, "use_item_extension", False),
                                        use_double_xp=getattr(eng, "use_double_xp", False),
                                        log_fn=log,
                                    )
                                    if getattr(eng, "use_fast_start", False):
                                        stock_fs = extract_item_stock(screen, "fast_start")
                                        if stock_fs <= getattr(eng, "fast_start_min_stock", 0):
                                            log(f"⚡ Fast Start ในคลัง ({stock_fs} ชิ้น <= เกณฑ์) -> กำลังซื้อเพิ่ม...", "info")
                                            purchase_fast_start()

                                    if getattr(eng, "use_cookie_relay", False):
                                        stock_cr = extract_item_stock(screen, "cookie_relay")
                                        if stock_cr <= getattr(eng, "cookie_relay_min_stock", 0):
                                            log(f"🍪 Cookie Relay ในคลัง ({stock_cr} ชิ้น <= เกณฑ์) -> กำลังซื้อเพิ่ม...", "info")
                                            purchase_cookie_relay()

                                    if getattr(eng, "use_desired_random_boost", False):
                                        desired_boost_template, desired_boost_name = eng.get_desired_boost_info()
                                        if desired_boost_template:
                                            log(f"🎲 Rolling boost for: {desired_boost_name}...")
                                            purchase_desired_random_boost(desired_boost_template, desired_boost_name, getattr(eng, "desired_boost_id", None), log_fn=log)
                                except Exception as e:
                                    log(f"⚠️ ตั้งค่าไอเทม: {e}", "warning")

                            items_configured = True

                        log("🎮 [Macro Play] กดปุ่มเริ่มเกมเข้าห้องวิ่ง...", "info")
                        play_game()
                        last_action_t = time.time()
                        time.sleep(1.2)
                        continue

                    elif stage == "GAME_START":
                        log("🏁 [Macro Play] ตรวจพบ START! รอแอนิเมชันเริ่มวิ่ง (1.0s)...", "info")
                        time.sleep(1.0)
                        log(f"▶️ [Macro Play] เข้าห้องวิ่งแล้ว! เริ่มเล่นตามมาโคร {self.macro_data.get('name')} (t=0.00s)...", "success")
                        in_game_started = True
                        break

                    elif items_configured and stage is None:
                        log(f"▶️ [Macro Play] เข้าห้องวิ่งแล้ว! เริ่มเล่นตามมาโคร {self.macro_data.get('name')} (t=0.00s)...", "success")
                        in_game_started = True
                        break

            except Exception:
                pass

            time.sleep(0.25)

        if not in_game_started and not self._stop_event.is_set():
            log(f"▶️ [Macro Play] เริ่มเล่นสเต็ปมาโคร {self.macro_data.get('name')} ทันที...", "info")

        if self._stop_event.is_set():
            self.is_running = False
            return

        # Phase 2: Start timeline execution
        self._play_thread = threading.Thread(
            target=self._playback_loop,
            name=f"MacroPlayerTimeline-{self.target_serial}",
            daemon=True,
        )
        self._play_thread.start()

        # Phase 3: Monitor for GAME_RELAY and GAME_COMPLETE while playing
        while self._play_thread and self._play_thread.is_alive() and not self._stop_event.is_set():
            time.sleep(0.3)
            try:
                screen = None
                try:
                    from scrcpy_streamer import stream_manager
                    st = stream_manager.get_streamer(target)
                    if st:
                        screen = st.get_latest_frame()
                except Exception:
                    pass
                if screen is None:
                    screen = device_capture_screen(target, t_port)
                if screen is not None:
                    stage = detect_stage(screen)

                    # 1. Cookie Relay triggered!
                    if stage == "GAME_RELAY":
                        log("🍪 [Macro Play] ตรวจพบจังหวะผลัดคุกกี้ (GAME_RELAY) -> กำลังกดปุ่มผลัดคุกกี้...", "info")
                        from actions import using_cookie_relay
                        using_cookie_relay()
                        time.sleep(1.2)
                        # Restart timeline playback for relay cookie!
                        log(f"▶️ [Macro Play] ผลัดคุกกี้สำเร็จ! เริ่มเล่นสเต็ปมาโคร {self.macro_data.get('name')} ต่อให้คุกกี้ตัวที่ 2...", "info")
                        if self._play_thread and self._play_thread.is_alive():
                            self._stop_event.set()
                            self._play_thread.join(timeout=1.0)
                        self._stop_event.clear()
                        self._play_thread = threading.Thread(
                            target=self._playback_loop,
                            name=f"MacroPlayerTimelineRelay-{self.target_serial}",
                            daemon=True,
                        )
                        self._play_thread.start()
                        continue

                    # 2. Game finished!
                    elif stage in ["GAME_COMPLETE", "CONGRATULATIONS", "MYSTERY_BOX"]:
                        log(f"🏁 [Macro Play] ตรวจพบจบเกม ({stage})! หยุดการเล่นมาโคร...", "info")
                        self._stop_event.set()
                        break
            except Exception:
                pass

        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2.0)
        self._play_thread = None

        # Phase 4: Handle result screen, exit result, and open mystery boxes!
        try:
            log("📊 [Macro Play] ตรวจพบหน้าจอสรุปผล (Result Screen) -> ข้ามแอนิเมชันคะแนน/เหรียญ...", "info")
            time.sleep(0.8)
            safe_device_tap(target, t_port, 640, 260)
            time.sleep(0.8)
            safe_device_tap(target, t_port, 640, 260)
            time.sleep(0.8)

            # Exit Result screen by tapping OK button
            log("👉 [Macro Play] กดปุ่ม OK เพื่อออกจากหน้าสรุปผล...", "info")
            from config import COMPLETE_FINISH_BUTTON
            safe_device_tap(target, t_port, COMPLETE_FINISH_BUTTON[0], COMPLETE_FINISH_BUTTON[1])
            time.sleep(1.2)

            # Fallback if 1-button screen
            scr = device_capture_screen(target, t_port)
            if scr is not None and detect_stage(scr) == "GAME_COMPLETE":
                safe_device_tap(target, t_port, 640, 625)
                time.sleep(1.0)

            # Transition loop: wait for MYSTERY_BOX, CONGRATULATIONS, LEVEL_UP, MAINMENU
            from actions import accept_mystery_box, accept_congratulations, accept_level_up, accept_set_reward
            post_start = time.time()
            while (time.time() - post_start) < 25.0:
                time.sleep(0.8)
                fresh_screen = device_capture_screen(target, t_port)
                if fresh_screen is None:
                    continue

                p_stage = detect_stage(fresh_screen)
                if p_stage == "MYSTERY_BOX":
                    log("🎁 [Macro Play] ตรวจพบหน้าเปิดกล่องปริศนา (Mystery Box) -> กำลังกดเปิดกล่องและรับรางวัล...", "success")
                    time.sleep(1.0)
                    accept_mystery_box()
                    time.sleep(1.2)
                    # Tap confirm loot
                    safe_device_tap(target, t_port, 650, 645)
                    time.sleep(0.8)

                elif p_stage == "CONGRATULATIONS":
                    log("🎉 [Macro Play] ตรวจพบของรางวัล (Congratulations) -> กดยืนยันรับ...", "info")
                    accept_congratulations()
                    time.sleep(0.8)

                elif p_stage == "LEVEL_UP":
                    log("⭐ [Macro Play] ตรวจพบเลเวลอัป -> กดยืนยัน...", "info")
                    accept_level_up()
                    time.sleep(0.8)

                elif p_stage == "SET_REWARD":
                    log("🎁 [Macro Play] ตรวจพบรางวัลเซ็ต -> กดยืนยัน...", "info")
                    accept_set_reward()
                    time.sleep(0.8)

                elif p_stage in ["MAINMENU", "PURCHASE_ITEM"]:
                    log(f"✅ [Macro Play] ออกจากหน้าสรุปผลและเปิดกล่องเรียบร้อยแล้ว (กลับสู่ {p_stage})", "success")
                    break

        except Exception as e:
            log(f"⚠️ [Macro Play] ข้อผิดพลาด Result/Box: {e}", "warning")

        self.is_running = False

    def stop(self):
        """Stop playback immediately."""
        self.is_running = False
        self._stop_event.set()
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=1.0)
        self._play_thread = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        # Clean up any stuck touches
        self._send_up(self.SLIDE_X, self.SLIDE_Y)
        self._send_up(self.JUMP_X, self.JUMP_Y)
        if self._shell_pipe:
            self._shell_pipe.close()
            self._shell_pipe = None

    def _playback_loop(self):
        """High-precision execution loop using time.perf_counter()."""
        actions = list(self.macro_data.get("actions", []))
        if not actions:
            self.is_running = False
            return

        loop = bool(self.macro_data.get("loop", False))
        duration = float(self.macro_data.get("duration_seconds", 0.0))
        if duration <= 0 and actions:
            duration = actions[-1].get("t", 0.0) + 2.0

        while not self._stop_event.is_set():
            start_perf = time.perf_counter()
            last_jump_exec = 0.0

            for act in actions:
                if self._stop_event.is_set():
                    break

                target_t = float(act.get("t", 0.0))
                # High precision wait until target_t
                while not self._stop_event.is_set():
                    elapsed = time.perf_counter() - start_perf
                    rem = target_t - elapsed
                    if rem <= 0.001:  # Within 1ms, proceed to dispatch
                        break
                    elif rem > 0.015:
                        time.sleep(rem - 0.008)
                    else:
                        time.sleep(0.001)

                if self._stop_event.is_set():
                    break

                # Execute action
                action_type = act.get("action", "")
                if action_type == "jump":
                    now_p = time.perf_counter()
                    if last_jump_exec > 0:
                        gap = now_p - last_jump_exec
                        if gap < 0.16:
                            time.sleep(0.16 - gap)
                    self.jump()
                    last_jump_exec = time.perf_counter()
                elif action_type == "double_jump":
                    air_time = float(act.get("air_time", 0.16))
                    self.double_jump(air_time=air_time)
                    last_jump_exec = time.perf_counter()
                elif action_type == "slide":
                    dur = float(act.get("duration", 0.40))
                    self.slide(duration_sec=dur)
                elif action_type == "tap":
                    tx = int(act.get("x", self.JUMP_X))
                    ty = int(act.get("y", self.JUMP_Y))
                    dur = float(act.get("duration", 0.03))
                    self._send_tap(tx, ty, duration=dur)

            if not loop or self._stop_event.is_set():
                break

            # If looping, wait remaining duration before starting cycle again
            while not self._stop_event.is_set():
                elapsed = time.perf_counter() - start_perf
                if elapsed >= duration:
                    break
                time.sleep(0.05)

        self.is_running = False
