import os
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

from config import JUMP_BUTTON, SLIDE_BUTTON


class PersistentShellPipe:
    """
    Keeps a single long-lived ADB shell subprocess open to pipe input commands
    directly via stdin. Avoids Windows process creation lag when tapping rapidly.
    Only a fallback: `input` itself still takes ~100-300ms on the device, so
    playback is only frame-accurate through the scrcpy control socket.
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

    def _send(self, line: str):
        with self._lock:
            if not self.proc or self.proc.poll() is not None:
                self._init_process()
            if self.proc and self.proc.stdin:
                try:
                    self.proc.stdin.write(line.encode("utf-8"))
                    self.proc.stdin.flush()
                except Exception:
                    self._init_process()

    def send_tap(self, x: int, y: int):
        # Backgrounded (&) so a slow `input` call never delays the next command in the timeline
        self._send(f"input tap {int(x)} {int(y)} &\n")

    def send_swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int):
        # Backgrounded (&): a swipe blocks for its whole duration, which used to delay every following jump
        self._send(f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)} &\n")

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
    Uses Scrcpy Direct Socket (< 1ms) when available, falling back to Persistent ADB Shell Pipe.
    """

    JUMP_X = JUMP_BUTTON[0]
    JUMP_Y = JUMP_BUTTON[1]
    SLIDE_X = SLIDE_BUTTON[0]
    SLIDE_Y = SLIDE_BUTTON[1]

    # Separate fingers so a jump while sliding does not release the slide (like keymapped play in LDPlayer)
    JUMP_TOUCH_ID = 1
    SLIDE_TOUCH_ID = 2
    TAP_TOUCH_ID = 3
    # How long a jump press is held. DOWN+UP in the same instant can be dropped by the game.
    TAP_HOLD_SEC = 0.035

    def __init__(self, target_serial: str):
        self.target_serial = str(target_serial).strip()
        self.macro_data: Optional[Dict[str, Any]] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._play_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._timeline_stop: Optional[threading.Event] = None
        self._shell_pipe: Optional[PersistentShellPipe] = None
        self._nav_mode = False
        self._relay_started = False
        self._jump_down_scrcpy = False
        self._slide_down_scrcpy = False
        self._warned_adb_fallback = False
        self._log_fn = None

    # ------------------------------------------------------------------
    # Input dispatch
    # ------------------------------------------------------------------
    def _get_shell_pipe(self) -> PersistentShellPipe:
        if self._shell_pipe is None:
            self._shell_pipe = PersistentShellPipe(self.target_serial)
        return self._shell_pipe

    def _scrcpy_touch(self, x: int, y: int, action_name: str, touch_id: int) -> bool:
        try:
            from scrcpy_streamer import scrcpy, stream_manager
            if scrcpy is None:
                return False
            st = stream_manager.get_streamer(self.target_serial)
            ctrl = getattr(st.client, "control", None) if st and st.client else None
            if not ctrl:
                return False
            # Keep the idle cleaner from stopping the stream mid-run
            st.last_access_time = time.time()
            ctrl.touch(int(x), int(y), getattr(scrcpy, action_name), touch_id)
            return True
        except Exception:
            return False

    def _note_adb_fallback(self):
        if not self._warned_adb_fallback:
            self._warned_adb_fallback = True
            if callable(self._log_fn):
                self._log_fn("⚠️ [Macro Play] ไม่ได้เชื่อม scrcpy — ส่งปุ่มผ่าน ADB แทน (ช้ากว่า ~0.1-0.3 วินาที จังหวะจะไม่ตรงเป๊ะ)", "warning")

    def _dispatch_jump_down(self):
        self._jump_down_scrcpy = self._scrcpy_touch(self.JUMP_X, self.JUMP_Y, "ACTION_DOWN", self.JUMP_TOUCH_ID)
        if not self._jump_down_scrcpy:
            self._note_adb_fallback()
            self._get_shell_pipe().send_tap(self.JUMP_X, self.JUMP_Y)

    def _dispatch_jump_up(self):
        if self._jump_down_scrcpy:
            self._scrcpy_touch(self.JUMP_X, self.JUMP_Y, "ACTION_UP", self.JUMP_TOUCH_ID)
            self._jump_down_scrcpy = False

    def _dispatch_slide_down(self, duration_sec: float = 0.40):
        self._slide_down_scrcpy = self._scrcpy_touch(self.SLIDE_X, self.SLIDE_Y, "ACTION_DOWN", self.SLIDE_TOUCH_ID)
        if not self._slide_down_scrcpy:
            self._note_adb_fallback()
            dur_ms = max(60, int(duration_sec * 1000))
            self._get_shell_pipe().send_swipe(self.SLIDE_X, self.SLIDE_Y, self.SLIDE_X, self.SLIDE_Y, dur_ms)

    def _dispatch_slide_up(self):
        if self._slide_down_scrcpy:
            self._scrcpy_touch(self.SLIDE_X, self.SLIDE_Y, "ACTION_UP", self.SLIDE_TOUCH_ID)
            self._slide_down_scrcpy = False

    def _dispatch_tap(self, x: int, y: int, duration: float = 0.03):
        if self._scrcpy_touch(x, y, "ACTION_DOWN", self.TAP_TOUCH_ID):
            time.sleep(max(0.0, min(0.1, float(duration))))
            self._scrcpy_touch(x, y, "ACTION_UP", self.TAP_TOUCH_ID)
            return
        self._get_shell_pipe().send_tap(x, y)

    def _release_touches(self):
        self._dispatch_jump_up()
        self._dispatch_slide_up()

    # Manual test actions (blocking is fine here)
    def jump(self):
        self._dispatch_jump_down()
        time.sleep(self.TAP_HOLD_SEC)
        self._dispatch_jump_up()

    def double_jump(self, air_time: float = 0.16):
        self.jump()
        time.sleep(max(0.16, float(air_time)) - self.TAP_HOLD_SEC)
        self.jump()

    def slide(self, duration_sec: float = 0.4):
        self._dispatch_slide_down(duration_sec)
        time.sleep(max(0.06, float(duration_sec)))
        self._dispatch_slide_up()

    # ------------------------------------------------------------------
    # Timeline management
    # ------------------------------------------------------------------
    def _phase_actions(self, phase: str) -> List[Dict[str, Any]]:
        data = self.macro_data or {}
        if phase == "relay":
            return list(data.get("relay_actions") or [])
        return list(data.get("main_actions") or data.get("actions", []))

    def _phase_cycle_sec(self, phase: str) -> float:
        data = self.macro_data or {}
        key = "relay_duration_seconds" if phase == "relay" else "main_duration_seconds"
        return float(data.get(key) or data.get("duration_seconds") or 0.0)

    def _start_timeline(self, phase: str, anchor_perf: Optional[float] = None, actions: Optional[List[Dict[str, Any]]] = None):
        self._stop_timeline()
        evt = threading.Event()
        self._timeline_stop = evt
        acts = actions if actions is not None else self._phase_actions(phase)
        self._play_thread = threading.Thread(
            target=self._playback_loop,
            args=(acts, evt, anchor_perf, self._phase_cycle_sec(phase)),
            name=f"MacroPlayerTimeline-{phase}-{self.target_serial}",
            daemon=True,
        )
        self._play_thread.start()

    def _stop_timeline(self):
        if self._timeline_stop:
            self._timeline_stop.set()
        if self._play_thread and self._play_thread.is_alive() and self._play_thread is not threading.current_thread():
            self._play_thread.join(timeout=1.0)
        self._play_thread = None
        self._release_touches()

    def start(self, macro_data: Dict[str, Any], anchor_perf: Optional[float] = None, log_fn=None):
        """
        Start the main-cookie timeline (BotEngine path).
        `anchor_perf` is the t=0 moment from macro_sync.anchor_run_start(); defaults to now.
        """
        self.stop()
        if not macro_data or "actions" not in macro_data:
            return

        self.macro_data = macro_data
        self._log_fn = log_fn
        self.is_running = True
        self._nav_mode = False
        self._relay_started = False
        self._warned_adb_fallback = False
        self._stop_event.clear()
        self._start_timeline("main", anchor_perf)

    @property
    def relay_started(self) -> bool:
        return self._relay_started

    def start_relay(self, anchor_perf: Optional[float] = None) -> str:
        """
        Switch to the relay-cookie timeline at t=0 = `anchor_perf`.
        Returns 'relay', 'loop', 'none' (macro has no relay part) or 'skipped' (already switched).
        """
        if not self.macro_data or self._relay_started:
            return "skipped"
        self._relay_started = True

        if self._phase_actions("relay"):
            self.is_running = True
            self._start_timeline("relay", anchor_perf)
            return "relay"
        if bool(self.macro_data.get("loop", False)):
            self.is_running = True
            self._start_timeline("main", anchor_perf)
            return "loop"
        self._stop_timeline()
        if not self._nav_mode:
            self.is_running = False
        return "none"

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
        2. Starts timeline macro execution at t=0.00s (same anchor as the recorder).
        3. Monitors for GAME_RELAY / GAME_COMPLETE, then handles the result screen.
        """
        self.stop()
        if not macro_data or "actions" not in macro_data:
            return

        self.macro_data = macro_data
        self.is_running = True
        self._nav_mode = True
        self._relay_started = False
        self._warned_adb_fallback = False
        self._log_fn = log_fn
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
        from macro_sync import InRunMonitor, anchor_relay_start, anchor_run_start, grab_frame, warm_up_stream

        set_device_context(target, t_port)
        eng = get_engine_for_device(target)
        warm_up_stream(target)

        start_wait = time.time()
        last_action_t = 0.0
        play_tapped_t = 0.0
        items_configured = False
        run_anchor: Optional[float] = None

        # Phase 1: Navigate from Lobby/Purchase into Game Room
        while not self._stop_event.is_set() and (time.time() - start_wait) < 60.0:
            now = time.time()
            # Right after an action only look for START!, but keep looking fast so t=0 is never missed
            throttled = (now - last_action_t) < 1.2
            is_stream = False

            try:
                screen, is_stream = grab_frame(target, t_port)

                if screen is not None:
                    stage = detect_stage(screen, stage_names=["GAME_START"] if throttled else ["MAINMENU", "PURCHASE_ITEM", "GAME_START"])
                    if throttled and stage != "GAME_START":
                        time.sleep(0.03 if is_stream else 0.2)
                        continue

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
                        play_tapped_t = last_action_t
                        continue

                    elif stage == "GAME_START":
                        log("🏁 [Macro Play] ตรวจพบ START! กำลังซิงค์จังหวะเริ่มวิ่ง...", "info")
                        run_anchor = anchor_run_start(target, t_port, eng)
                        log(f"▶️ [Macro Play] เข้าห้องวิ่งแล้ว! เริ่มเล่นตามมาโคร {self.macro_data.get('name')} (t=0.00s)...", "success")
                        break

                    # Fallback: START! never seen long after tapping Play (loading screens also read as None)
                    elif items_configured and stage is None and play_tapped_t and (now - play_tapped_t) >= 10.0:
                        run_anchor = time.perf_counter()
                        log("⚠️ [Macro Play] ไม่พบหน้า START! — เริ่มเล่นมาโครแบบสำรอง (จังหวะ t=0 อาจไม่ตรงกับตอนบันทึก)", "warning")
                        break

            except Exception:
                pass

            time.sleep(0.03 if is_stream else 0.25)

        if self._stop_event.is_set():
            self.is_running = False
            return

        if run_anchor is None:
            run_anchor = time.perf_counter()
            log(f"▶️ [Macro Play] เริ่มเล่นสเต็ปมาโคร {self.macro_data.get('name')} ทันที...", "info")

        # Phase 2: Start timeline execution (Main phase)
        self._start_timeline("main", run_anchor)

        # Phase 3: Monitor for GAME_RELAY and GAME_COMPLETE until the run really ends.
        # (Do not stop when the timeline runs out of actions: the relay usually comes seconds later.)
        monitor = InRunMonitor(target, t_port)
        total_sec = float(self.macro_data.get("duration_seconds") or 0.0)
        max_run_sec = max(600.0, total_sec + 180.0)
        while not self._stop_event.is_set() and (time.perf_counter() - run_anchor) < max_run_sec:
            time.sleep(0.1)
            try:
                stage = monitor.poll()
                if stage == "GAME_RELAY":
                    if self._relay_started:
                        continue
                    log("🍪 [Macro Play] ตรวจพบจังหวะผลัดคุกกี้ (GAME_RELAY) -> กำลังกดปุ่มผลัดคุกกี้...", "info")
                    self._stop_timeline()
                    relay_anchor = anchor_relay_start(target, t_port)
                    mode = self.start_relay(relay_anchor)
                    if mode == "relay":
                        log(f"▶️ [Macro Play] ผลัดคุกกี้สำเร็จ! เริ่มเล่นท่อนคุกกี้ตัวที่ 2 (Relay Phase, {len(self._phase_actions('relay'))} แอ็กชัน) ที่ t=0.00s...", "success")
                    elif mode == "loop":
                        log("🔁 [Macro Play] โหมดวนลูป (Loop Mode): เริ่มวนซ้ำสเต็ปมาโครให้คุกกี้ตัวที่ 2...", "info")
                    elif mode == "none":
                        log("🍪 [Macro Play] ผลัดคุกกี้แล้ว (มาโครนี้ไม่มีท่อนตัวผลัด) -> วิ่งต่อจนจบเกม...", "info")

                elif stage in ["GAME_COMPLETE", "CONGRATULATIONS", "MYSTERY_BOX"]:
                    log(f"🏁 [Macro Play] ตรวจพบจบเกม ({stage})! หยุดการเล่นมาโคร...", "info")
                    break
            except Exception:
                pass

        self._stop_timeline()

        # Stopped by the user -> leave the screen alone
        if self._stop_event.is_set():
            self.is_running = False
            return

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
            while (time.time() - post_start) < 25.0 and not self._stop_event.is_set():
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
        self._stop_timeline()
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)
        self._thread = None
        if self._shell_pipe:
            self._shell_pipe.close()
            self._shell_pipe = None

    @classmethod
    def _build_events(cls, actions_list: List[Dict[str, Any]]) -> List[tuple]:
        """Expand actions into sorted atomic (t, event_type, data) events."""
        events: List[tuple] = []
        for act in actions_list:
            act_type = act.get("action", "")
            t = float(act.get("t", 0.0))
            if act_type == "jump":
                events.append((t, "jump_down", {}))
                events.append((t + cls.TAP_HOLD_SEC, "jump_up", {}))
            elif act_type == "double_jump":
                air_time = max(0.16, float(act.get("air_time", 0.16)))
                for jt in (t, t + air_time):
                    events.append((jt, "jump_down", {}))
                    events.append((jt + cls.TAP_HOLD_SEC, "jump_up", {}))
            elif act_type == "slide":
                dur = float(act.get("duration", 0.40))
                events.append((t, "slide_down", {"duration": dur}))
                events.append((t + dur, "slide_up", {}))
            elif act_type == "tap":
                events.append((t, "tap", {"x": act.get("x", cls.JUMP_X), "y": act.get("y", cls.JUMP_Y), "duration": act.get("duration", 0.03)}))
        # Stable sort keeps DOWN before UP when two events share a timestamp
        events.sort(key=lambda e: e[0])
        return events

    def _playback_loop(
        self,
        actions_list: List[Dict[str, Any]],
        stop_evt: threading.Event,
        anchor_perf: Optional[float] = None,
        cycle_sec: float = 0.0,
    ):
        """High-precision, non-blocking event timeline. t=0 is `anchor_perf` (defaults to now)."""
        events = self._build_events(actions_list or [])
        if not events:
            if not self._nav_mode:
                self.is_running = False
            return

        loop = bool((self.macro_data or {}).get("loop", False))
        if cycle_sec <= 0:
            cycle_sec = events[-1][0] + 2.0

        start_perf = anchor_perf or time.perf_counter()
        total_events = len(events)

        while not stop_evt.is_set():
            ev_idx = 0

            while not stop_evt.is_set() and ev_idx < total_events:
                ev_t, ev_type, ev_data = events[ev_idx]
                rem = ev_t - (time.perf_counter() - start_perf)
                if rem > 0.001:
                    # time.sleep is high-resolution on Windows (Py3.11+); Event.wait is not (~15ms)
                    if rem > 0.015:
                        time.sleep(min(rem - 0.008, 0.05))
                    else:
                        time.sleep(0.0005)
                    continue

                # Instant non-blocking dispatch
                if ev_type == "jump_down":
                    self._dispatch_jump_down()
                elif ev_type == "jump_up":
                    self._dispatch_jump_up()
                elif ev_type == "slide_down":
                    self._dispatch_slide_down(ev_data.get("duration", 0.40))
                elif ev_type == "slide_up":
                    self._dispatch_slide_up()
                elif ev_type == "tap":
                    self._dispatch_tap(ev_data.get("x", self.JUMP_X), ev_data.get("y", self.JUMP_Y), ev_data.get("duration", 0.03))

                ev_idx += 1

            if not loop or stop_evt.is_set():
                break

            # Looping: next cycle starts exactly one cycle after the previous one (no drift)
            start_perf += cycle_sec
            while not stop_evt.is_set() and time.perf_counter() < start_perf:
                time.sleep(min(0.05, max(0.0, start_perf - time.perf_counter())))

        self._release_touches()
        if not self._nav_mode and not stop_evt.is_set():
            self.is_running = False
