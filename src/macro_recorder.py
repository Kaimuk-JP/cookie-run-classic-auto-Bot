import ctypes
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import macro_manager

user32 = getattr(ctypes, "windll", None) and getattr(ctypes.windll, "user32", None)

VK_SPACE = 0x20  # Space bar (Jump)
VK_Z = 0x5A      # Z (Jump)
VK_X = 0x58      # X (Slide)
VK_LEFT = 0x25   # Left arrow (Jump)
VK_DOWN = 0x28   # Down arrow (Slide)
VK_RIGHT = 0x27  # Right arrow (Slide)


class DeviceMacroRecorder:
    """
    Stateful macro recorder for a single device.
    Supports auto-triggering when entering the in-game running stage
    and hardware-level Windows global key hooks to capture keys
    pressed directly inside LDPlayer or any emulator window.
    """

    def __init__(self, device_serial: str):
        self.device_serial = device_serial
        self.status = "IDLE"  # 'IDLE', 'ARMED', 'RECORDING'
        self.macro_name = ""
        self.start_perf = 0.0
        self.actions: List[Dict[str, Any]] = []
        self.active_slide_start: Optional[float] = None
        self.last_jump_t: Optional[float] = None
        self.last_jump_index: Optional[int] = None
        self._last_call_perf = 0.0
        self._key_listener_thread: Optional[threading.Thread] = None
        self._key_hook_ref = None
        self._is_jump_key_down = False
        self._is_slide_key_down = False
        self._log_fn = None
        self._lock = threading.Lock()

    def set_log_fn(self, log_fn):
        self._log_fn = log_fn

    def arm(self, name: str = ""):
        with self._lock:
            self.status = "ARMED"
            self.macro_name = name.strip() or f"มาโครบันทึกสด_{datetime.now().strftime('%d%m_%H%M')}"
            self.actions = []
            self.start_perf = 0.0
            self.active_slide_start = None
            self.last_jump_t = None
            self.last_jump_index = None
            self._last_call_perf = 0.0
            self._is_jump_key_down = False
            self._is_slide_key_down = False

    def start_auto_flow(self, device_serial: str, port: int = 5555, log_fn=None):
        """
        Background worker that:
        1. Checks screen at Lobby/MAINMENU -> Taps Play button (955, 650).
        2. Checks screen at PURCHASE_ITEM -> Taps Start Game button (895, 620).
        3. Monitors screen until GAME_START / In-Game is detected -> triggers recording (t=0.00s)!
        4. Monitors screen until GAME_COMPLETE -> auto stops and saves JSON!
        """
        self._log_fn = log_fn
        t = threading.Thread(
            target=self._auto_flow_loop,
            args=(device_serial, port, log_fn),
            name=f"MacroAutoFlow-{device_serial}",
            daemon=True,
        )
        t.start()

    def _auto_flow_loop(self, device_serial: str, port: int, log_fn=None):
        def log(msg, mtype="info"):
            if callable(log_fn):
                log_fn(msg, mtype)
            else:
                print(f"[{mtype.upper()}] {msg}")

        target = str(device_serial).strip() or "127.0.0.1:7555"
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

        # CRITICAL: Bind device context for this thread so all actions target this specific emulator
        set_device_context(target, t_port)
        eng = get_engine_for_device(target)

        start_wait_time = time.time()
        last_action_time = 0.0
        items_configured = False

        # Step 1: Wait & navigate until in-game (timeout 60s)
        while self.status == "ARMED" and (time.time() - start_wait_time) < 60.0:
            now = time.time()
            if (now - last_action_time) < 1.2:
                time.sleep(0.2)
                continue

            try:
                screen = None
                try:
                    from scrcpy_streamer import stream_manager
                    streamer = stream_manager.get_streamer(target)
                    if streamer:
                        screen = streamer.get_latest_frame()
                except Exception:
                    pass

                if screen is None:
                    screen = device_capture_screen(target, t_port)

                if screen is not None:
                    # Filter specifically to pre-game stages to prevent false positive relic/popup detection on lobby
                    stage = detect_stage(screen, stage_names=["MAINMENU", "PURCHASE_ITEM", "GAME_START"])

                    # 1. In Lobby / MainMenu -> Tap Play button to enter item prep
                    if stage == "MAINMENU":
                        log("🎮 [Macro Record] ตรวจพบหน้าล็อบบี้ -> กดปุ่ม Play (เริ่มเกม)...", "info")
                        start_game()
                        last_action_time = time.time()
                        items_configured = False
                        time.sleep(1.0)
                        continue

                    # 2. In Item preparation / Purchase screen -> Select/buy items per settings, then play_game!
                    elif stage == "PURCHASE_ITEM":
                        if not items_configured:
                            log("🛒 [Macro Record] ตรวจพบหน้าเลือกไอเทม -> กำลังเลือกและซื้อไอเทมตามการตั้งค่า...", "info")
                            if eng:
                                try:
                                    # Top-row items (HP Boost, Item Extension, Double XP)
                                    configure_top_row_items(
                                        screen,
                                        use_hp=getattr(eng, "use_hp_boost", False),
                                        use_extension=getattr(eng, "use_item_extension", False),
                                        use_double_xp=getattr(eng, "use_double_xp", False),
                                        log_fn=log,
                                    )

                                    # Fast Start check & purchase
                                    if getattr(eng, "use_fast_start", False):
                                        stock_fs = extract_item_stock(screen, "fast_start")
                                        if stock_fs <= getattr(eng, "fast_start_min_stock", 0):
                                            log(f"⚡ Fast Start ในคลัง ({stock_fs} ชิ้น <= เกณฑ์ {getattr(eng, 'fast_start_min_stock', 0)}) -> กำลังซื้อเพิ่ม...", "info")
                                            purchase_fast_start()

                                    # Cookie Relay check & purchase
                                    if getattr(eng, "use_cookie_relay", False):
                                        stock_cr = extract_item_stock(screen, "cookie_relay")
                                        if stock_cr <= getattr(eng, "cookie_relay_min_stock", 0):
                                            log(f"🍪 Cookie Relay ในคลัง ({stock_cr} ชิ้น <= เกณฑ์ {getattr(eng, 'cookie_relay_min_stock', 0)}) -> กำลังซื้อเพิ่ม...", "info")
                                            purchase_cookie_relay()

                                    # Random Boost check & roll
                                    if getattr(eng, "use_desired_random_boost", False):
                                        desired_boost_template, desired_boost_name = eng.get_desired_boost_info()
                                        if desired_boost_template:
                                            log(f"🎲 Rolling boost for: {desired_boost_name}...")
                                            purchase_desired_random_boost(desired_boost_template, desired_boost_name, getattr(eng, "desired_boost_id", None), log_fn=log)
                                except Exception as e:
                                    log(f"⚠️ ตั้งค่าไอเทม: {e}", "warning")

                            items_configured = True

                        log("🎮 [Macro Record] กดปุ่มเริ่มเกมเข้าห้องวิ่ง...", "info")
                        play_game()
                        last_action_time = time.time()
                        time.sleep(1.2)
                        continue

                    # 3. Popups (e.g. RELIC_COMPLETE, CONGRATULATIONS, MYSTERY_BOX)
                    elif stage in ["RELIC_COMPLETE", "CONGRATULATIONS", "MYSTERY_BOX", "LEVEL_UP", "DAILY_CHECKIN", "DAILY_NEW", "DAILY_TREASURE"]:
                        log(f"🔔 [Macro Record] ตรวจพบป๊อปอัป ({stage}) -> กดปิดให้อัตโนมัติ", "info")
                        safe_device_tap(target, t_port, 640, 600)
                        last_action_time = time.time()
                        time.sleep(0.8)
                        continue

                    # 4. In-Game Start detected! ("START!" graphic / entered game room)
                    elif stage == "GAME_START":
                        log("🏁 [Macro Record] ตรวจพบ START! รอแอนิเมชันเริ่มวิ่ง (1.0s)...", "info")
                        time.sleep(1.0)
                        if self.trigger_in_game_start():
                            log("🔴 [Macro Record] เข้าสู่ห้องวิ่งในเกมแล้ว! เริ่มจับเวลาและบันทึกสเต็ปมาโครสดทันที (t=0.00s)", "success")
                        break

                    # 5. If items were configured and stage is None (in-game running)
                    elif items_configured and stage is None:
                        if self.trigger_in_game_start():
                            log("🔴 [Macro Record] เข้าสู่ห้องวิ่งในเกมแล้ว! เริ่มจับเวลาและบันทึกมาโครสดทันที (t=0.00s)", "success")
                        break

            except Exception as e:
                pass

            time.sleep(0.25)

        # Step 2: While RECORDING, monitor for GAME_COMPLETE to auto-stop and save!
        while self.status == "RECORDING":
            try:
                screen = None
                try:
                    from scrcpy_streamer import stream_manager
                    streamer = stream_manager.get_streamer(target)
                    if streamer:
                        screen = streamer.get_latest_frame()
                except Exception:
                    pass

                if screen is None:
                    screen = device_capture_screen(target, t_port)

                if screen is not None:
                    stage = detect_stage(screen)

                    # 1. In-game Cookie Relay trigger! Tap relay button so Cookie 2 continues
                    if stage == "GAME_RELAY":
                        log("🍪 [Macro Record] ตรวจพบคุกกี้ผลัด (Cookie Relay)! แตะเปิดใช้งานคุกกี้ผลัดตัวที่ 2 ให้อัตโนมัติ...", "info")
                        from actions import using_cookie_relay
                        using_cookie_relay()
                        time.sleep(1.2)
                        continue

                    # 2. Game finished -> Stop, save, tap OK on Result, and open Mystery Boxes!
                    if stage in ["GAME_COMPLETE", "CONGRATULATIONS", "MYSTERY_BOX"]:
                        log(f"🏁 [Macro Record] ตรวจพบจบเกม ({stage})! ทำการบันทึกมาโครลงไฟล์ JSON อัตโนมัติ...", "success")
                        saved = self.stop_and_save()
                        if saved:
                            log(f"💾 [Macro Record] บันทึกมาโครสำเร็จ: {saved.get('name')} ({len(saved.get('actions', []))} แอ็กชัน)", "success")

                        # Auto handle result screen: tap OK and open Mystery Box!
                        log("📊 [Macro Record] กำลังดำเนินการ: ข้ามแอนิเมชัน -> กด OK หน้า Result -> เปิดกล่อง Mystery Box...", "info")
                        try:
                            # 1. Skip score animation by tapping screen twice
                            time.sleep(1.0)
                            safe_device_tap(target, t_port, 640, 260)
                            time.sleep(0.8)
                            safe_device_tap(target, t_port, 640, 260)
                            time.sleep(0.8)

                            # 2. Tap OK button on Result screen (460, 625)
                            from actions import complete_finish, accept_mystery_box, accept_congratulations
                            from config import COMPLETE_FINISH_BUTTON, ACCEPT_MYSTERY_BOX_BUTTON

                            log("👉 [Macro Record] กดปุ่ม OK หน้า Result เพื่อออกจากหน้าสรุปผล...", "info")
                            complete_finish()
                            time.sleep(1.2)

                            # 3. Transition loop: Open Mystery Box ("Open all") and dismiss remaining popups back to Lobby
                            post_start = time.time()
                            while (time.time() - post_start) < 25.0:
                                time.sleep(0.8)
                                fresh_screen = device_capture_screen(target, t_port)
                                if fresh_screen is None:
                                    continue

                                p_stage = detect_stage(fresh_screen)

                                # If back to MainMenu / Lobby -> Done!
                                if p_stage == "MAINMENU":
                                    log("🏠 [Macro Record] กลับสู่หน้าล็อบบี้เรียบร้อยแล้ว", "success")
                                    break

                                # If still on Result screen -> Tap OK again
                                elif p_stage == "GAME_COMPLETE":
                                    log("👉 [Macro Record] กดปุ่ม OK หน้า Result ซ้ำ...", "info")
                                    complete_finish(fresh_screen)
                                    time.sleep(1.2)

                                # If Mystery Box screen -> Tap Open all at (650, 645)
                                elif p_stage == "MYSTERY_BOX":
                                    log("🎁 [Macro Record] ตรวจพบหน้า Mystery Box -> กำลังกดปุ่ม Open all (เปิดกล่อง)...", "success")
                                    accept_mystery_box()
                                    time.sleep(1.2)
                                    # Tap to confirm loot
                                    safe_device_tap(target, t_port, ACCEPT_MYSTERY_BOX_BUTTON[0], ACCEPT_MYSTERY_BOX_BUTTON[1])
                                    time.sleep(0.8)

                                elif p_stage == "CONGRATULATIONS":
                                    log("🎉 [Macro Record] ปิดป๊อปอัป Congratulations...", "info")
                                    accept_congratulations()
                                    time.sleep(0.8)

                                elif p_stage in ["LEVEL_UP", "DAILY_CHECKIN", "DAILY_NEW", "DAILY_TREASURE", "RELIC_COMPLETE", "SET_REWARD"]:
                                    safe_device_tap(target, t_port, 640, 600)
                                    time.sleep(0.8)

                                else:
                                    safe_device_tap(target, t_port, 640, 565)
                                    time.sleep(0.8)

                            log("✅ [Macro Record] จัดการหน้า OK และเปิดกล่อง Mystery Box ให้เรียบร้อยแล้ว", "success")
                        except Exception as err:
                            log(f"⚠️ [Macro Record] เกิดข้อผิดพลาดในการจัดการหน้าผลลัพธ์: {err}", "warning")

                        break
            except Exception:
                pass

            time.sleep(0.5)

    def trigger_in_game_start(self) -> bool:
        """Called by BotEngine as soon as the in-game running screen is detected."""
        with self._lock:
            if self.status != "ARMED":
                return False
            self.status = "RECORDING"
            self.start_perf = time.perf_counter()
            self.actions = []
            self.active_slide_start = None
            self.last_jump_t = None
            self.last_jump_index = None
            self._last_call_perf = 0.0

        # Start OS-level global keyboard listener thread (LDPlayer capture)
        self._start_key_listener()
        return True

    def _start_key_listener(self):
        # 1. Primary: Windows Global Low-Level Keyboard Hook via keyboard module
        try:
            import keyboard
            if self._key_hook_ref is None:
                self._key_hook_ref = keyboard.hook(self._on_key_event)
                if self._log_fn:
                    self._log_fn("🎹 [Macro Record] ติดตั้ง Windows Global Key Hook สำเร็จ (ดักจับ Space/Z/X/S/ลูกศร ได้ทุกหน้าต่าง)", "info")
                return
        except Exception as e:
            if self._log_fn:
                self._log_fn(f"⚠️ [Macro Record] ไม่สามารถติดตั้ง keyboard.hook: {e} -> ใช้ GetAsyncKeyState สำรอง", "warning")

        # 2. Fallback: GetAsyncKeyState polling thread
        if not user32:
            return
        if self._key_listener_thread and self._key_listener_thread.is_alive():
            return
        self._key_listener_thread = threading.Thread(
            target=self._key_listener_loop,
            name=f"MacroKeyHook-{self.device_serial}",
            daemon=True,
        )
        self._key_listener_thread.start()

    def _on_key_event(self, e):
        if self.status != "RECORDING":
            return
        try:
            name = (getattr(e, "name", None) or "").lower()
            if not name:
                return

            event_type = getattr(e, "event_type", "")

            # Jump keys: Spacebar, Z, W, Up Arrow, Left Arrow, J (LDPlayer Jump), D
            if name in ("space", "z", "w", "up", "left", "j", "d"):
                if event_type == "down":
                    if not self._is_jump_key_down:
                        self._is_jump_key_down = True
                        act = self.record_jump()
                        if act and self._log_fn:
                            self._log_fn(f"🦘 [Macro Record] บันทึก {act.get('action')} ที่ t={act.get('t')}s (รวม {len(self.actions)} แอ็กชัน)", "info")
                elif event_type == "up":
                    self._is_jump_key_down = False

            # Slide keys: X, S (LDPlayer Slide), Down Arrow, Right Arrow, K, C, Shift, Ctrl
            elif name in ("x", "s", "down", "right", "k", "c", "shift", "left shift", "right shift", "ctrl", "left ctrl", "right ctrl"):
                if event_type == "down":
                    if not self._is_slide_key_down:
                        self._is_slide_key_down = True
                        self.record_slide_down()
                elif event_type == "up":
                    if self._is_slide_key_down:
                        self._is_slide_key_down = False
                        act = self.record_slide_up()
                        if act and self._log_fn:
                            self._log_fn(f"🛹 [Macro Record] บันทึก Slide ที่ t={act.get('t')}s นาน {act.get('duration')}s (รวม {len(self.actions)} แอ็กชัน)", "info")
        except Exception:
            pass

    def _stop_key_listener(self):
        if self._key_hook_ref is not None:
            try:
                import keyboard
                keyboard.unhook(self._key_hook_ref)
            except Exception:
                pass
            self._key_hook_ref = None
        self._is_jump_key_down = False
        self._is_slide_key_down = False

    def _key_listener_loop(self):
        """
        Fallback background listener polling physical keyboard state with GetAsyncKeyState.
        Captures Space / X / Z / Arrows directly while user is playing in LDPlayer.
        """
        if user32:
            try:
                user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
                user32.GetAsyncKeyState.restype = ctypes.c_short
            except Exception:
                pass

        was_jump_down = False
        was_slide_down = False

        # Drain initial state
        time.sleep(0.05)

        # Additional VK codes for LDPlayer mappings
        VK_J = 0x4A
        VK_S = 0x53
        VK_W = 0x57
        VK_UP = 0x26

        while self.status == "RECORDING":
            try:
                # Jump keys (Space, Z, Left, Up, W, J)
                is_space = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)
                is_z = bool(user32.GetAsyncKeyState(VK_Z) & 0x8000)
                is_left = bool(user32.GetAsyncKeyState(VK_LEFT) & 0x8000)
                is_up = bool(user32.GetAsyncKeyState(VK_UP) & 0x8000)
                is_w = bool(user32.GetAsyncKeyState(VK_W) & 0x8000)
                is_j = bool(user32.GetAsyncKeyState(VK_J) & 0x8000)
                is_jump_down = is_space or is_z or is_left or is_up or is_w or is_j

                # Slide keys (X, Down, Right, S)
                is_x = bool(user32.GetAsyncKeyState(VK_X) & 0x8000)
                is_down = bool(user32.GetAsyncKeyState(VK_DOWN) & 0x8000)
                is_right = bool(user32.GetAsyncKeyState(VK_RIGHT) & 0x8000)
                is_s = bool(user32.GetAsyncKeyState(VK_S) & 0x8000)
                is_slide_down = is_x or is_down or is_right or is_s

                # Jump transition (UP -> DOWN)
                if is_jump_down and not was_jump_down:
                    act = self.record_jump()
                    if act and self._log_fn:
                        self._log_fn(f"🦘 [Macro Record] บันทึก {act.get('action')} ที่ t={act.get('t')}s (รวม {len(self.actions)} แอ็กชัน)", "info")
                was_jump_down = is_jump_down

                # Slide transitions
                if is_slide_down and not was_slide_down:
                    self.record_slide_down()
                elif not is_slide_down and was_slide_down:
                    act = self.record_slide_up()
                    if act and self._log_fn:
                        self._log_fn(f"🛹 [Macro Record] บันทึก Slide ที่ t={act.get('t')}s นาน {act.get('duration')}s (รวม {len(self.actions)} แอ็กชัน)", "info")
                was_slide_down = is_slide_down

            except Exception:
                pass

            time.sleep(0.008)  # ~125 Hz polling, near zero CPU

    def record_jump(self) -> Dict[str, Any]:
        with self._lock:
            if self.status != "RECORDING":
                return {}

            now_perf = time.perf_counter()
            # 50ms debounce against key bounce / duplicate events from browser
            if (now_perf - self._last_call_perf) < 0.05:
                return {}
            self._last_call_perf = now_perf

            now_t = round(now_perf - self.start_perf, 2)
            if now_t < 0:
                now_t = 0.0

            # Check if this is a double jump (within 0.55s after previous jump while airborne)
            if self.last_jump_t is not None and (now_t - self.last_jump_t) <= 0.55 and self.last_jump_index is not None:
                air_time = round(now_t - self.last_jump_t, 2)
                prev_act = self.actions[self.last_jump_index]
                prev_act["action"] = "double_jump"
                # CookieRun engine takeoff lock is ~0.14-0.16s.
                # If pressed rapidly (< 0.16s), clamp air_time to 0.16s so the 2nd jump actually triggers in-game!
                prev_act["air_time"] = max(0.16, min(0.48, air_time))
                self.last_jump_t = None
                self.last_jump_index = None
                return prev_act

            entry = {"t": now_t, "action": "jump"}
            self.actions.append(entry)
            self.last_jump_t = now_t
            self.last_jump_index = len(self.actions) - 1
            return entry

    def record_slide_down(self):
        with self._lock:
            if self.status != "RECORDING":
                return
            if self.active_slide_start is None:
                self.active_slide_start = time.perf_counter()

    def record_slide_up(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self.status != "RECORDING" or self.active_slide_start is None:
                return None
            down_perf = self.active_slide_start
            self.active_slide_start = None
            now_perf = time.perf_counter()

            start_t = round(down_perf - self.start_perf, 2)
            if start_t < 0:
                start_t = 0.0
            duration = round(now_perf - down_perf, 2)
            duration = max(0.15, min(2.5, duration))

            entry = {"t": start_t, "action": "slide", "duration": duration}
            self.actions.append(entry)
            self.last_jump_t = None
            return entry

    def record_slide_instant(self, duration: float = 0.4) -> Dict[str, Any]:
        """Record a single slide action with known duration."""
        with self._lock:
            if self.status != "RECORDING":
                return {}
            now_t = round(time.perf_counter() - self.start_perf, 2)
            if now_t < 0:
                now_t = 0.0
            entry = {"t": now_t, "action": "slide", "duration": round(duration, 2)}
            self.actions.append(entry)
            self.last_jump_t = None
            return entry

    def stop_and_save(self, custom_name: str = "") -> Optional[Dict[str, Any]]:
        self._stop_key_listener()
        with self._lock:
            if self.status == "IDLE":
                return None

            # Finish any pending slide
            if self.active_slide_start is not None and self.start_perf > 0:
                now_perf = time.perf_counter()
                start_t = round(self.active_slide_start - self.start_perf, 2)
                duration = max(0.15, round(now_perf - self.active_slide_start, 2))
                self.actions.append({"t": max(0.0, start_t), "action": "slide", "duration": duration})
                self.active_slide_start = None

            elapsed = round(time.perf_counter() - self.start_perf, 1) if self.start_perf > 0 else 30.0
            self.status = "IDLE"

            name = custom_name.strip() or self.macro_name or f"มาโครบันทึกสด_{datetime.now().strftime('%d%m_%H%M')}"
            macro_id = f"rec_{int(time.time())}"

            # Sort actions by timestamp
            self.actions.sort(key=lambda x: x.get("t", 0.0))

            macro_data = {
                "id": macro_id,
                "name": name,
                "description": f"บันทึกจากการเล่นเกมสดเมื่อ {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "author": "Player (Recorded)",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": max(elapsed, (self.actions[-1]["t"] + 2.0) if self.actions else 30.0),
                "loop": False,
                "actions": self.actions,
            }

            ok, res_id = macro_manager.save_macro(macro_data)
            if ok:
                return macro_data
            return None

    def cancel(self):
        self._stop_key_listener()
        with self._lock:
            self.status = "IDLE"
            self.actions = []
            self.active_slide_start = None

    def __del__(self):
        self._stop_key_listener()

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            elapsed = 0.0
            if self.status == "RECORDING" and self.start_perf > 0:
                elapsed = round(time.perf_counter() - self.start_perf, 1)
            return {
                "device_serial": self.device_serial,
                "status": self.status,
                "macro_name": self.macro_name,
                "elapsed": elapsed,
                "action_count": len(self.actions),
                "recent_actions": self.actions[-5:],
            }


class MacroRecorderManager:
    """Manages recorders across devices."""

    def __init__(self):
        self._recorders: Dict[str, DeviceMacroRecorder] = {}
        self._lock = threading.Lock()

    def get_recorder(self, device_serial: str) -> DeviceMacroRecorder:
        clean = str(device_serial).strip()
        with self._lock:
            if clean not in self._recorders:
                self._recorders[clean] = DeviceMacroRecorder(clean)
            return self._recorders[clean]


macro_recorder_manager = MacroRecorderManager()
