import asyncio
from collections import deque
from datetime import datetime
import json
import os
import random
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import cv2
import numpy as np

import config
from actions import (
    accept_congratulations,
    accept_daily_checkin,
    accept_daily_checkin_boost_set,
    accept_daily_new,
    accept_daily_treasure,
    accept_enter_league,
    accept_league_results,
    accept_level_up,
    accept_mystery_box,
    accept_overtake_break_score,
    accept_previous_rank_results,
    accept_previous_results,
    accept_relic_claim,
    accept_set_reward,
    accept_too_many_treasures,
    close_announcement_dialog,
    close_game_settings,
    close_party_run_mode,
    complete_finish,
    configure_top_row_items,
    exit_in_game_run,
    handle_anti_bot,
    handle_connection_lost,
    handle_inactive,
    handle_quick_receive_and_send_lives,
    handle_send_friend_life,
    open_relic_complete,
    perform_auto_jump,
    perform_auto_slide,
    play_game,
    purchase_cookie_relay,
    purchase_desired_random_boost,
    purchase_fast_start,
    start_game,
    using_cookie_relay,
    using_fast_start,
)
from adb import (
    device_capture_screen,
    device_check_connection,
    device_connect,
    device_reset_app,
    device_tap,
    get_adb_path,
    clear_system_memory,
)
from config import (
    BOOST_17P_BASE_SPEED_TEMPLATE,
    BOOST_15P_SCORE_BONUS_TEMPLATE,
    BOOST_20P_HP_FROM_POTIONS_TEMPLATE,
    BOOST_2PIT_LIFTS_TEMPLATE,
    BOOST_70P_CRUSH_CHANCE_TEMPLATE,
    BOOST_DOUBLE_COINS_TEMPLATE,
    BOOST_GOLD_COIN_MAGIC_TEMPLATE,
    BOOST_M15P_HP_DRAIN_TEMPLATE,
    BOOST_M30P_COLLISION_DAMAGE_TEMPLATE,
    BOOST_MAGNETIC_AURA_TEMPLATE,
    BOOST_REVIVE_ONCE_WITH_80HP_TEMPLATE,
    DETECTION_ALWAYS_STAGES,
    DETECTION_GROUPS,
    DETECTION_RECOVERY_SCAN_INTERVAL,
    SESSION_RESET_INTERVAL,
)
from detection import (
    detect_ingame_box_count,
    detect_result_screen_mystery_box,
    detect_mystery_box_grades,
    detect_stage,
    extract_item_stock,
    extract_result_coins,
    extract_result_score,
    extract_result_xp,
    load_templates,
)
from discord_notifier import discord_notifier
from error_logger import record_game_error


from path_utils import get_project_root
_project_root = get_project_root()

SETTINGS_DIR = os.path.join(_project_root, "settings")
os.makedirs(SETTINGS_DIR, exist_ok=True)
DEFAULT_SETTINGS_PATH = os.path.join(SETTINGS_DIR, "bot_settings.json")
LEGACY_SETTINGS_DIR = os.path.dirname(__file__)

HISTORY_DIR = os.path.join(_project_root, "history")
os.makedirs(HISTORY_DIR, exist_ok=True)


def get_device_settings_path(serial: Optional[str]) -> str:
    """Get device-specific settings file path inside settings/ directory."""
    safe_id = "".join(c if c.isalnum() else "_" for c in str(serial or "default"))
    return os.path.join(SETTINGS_DIR, f"bot_settings_{safe_id}.json")


def get_device_history_path(serial: Optional[str]) -> str:
    """Get device-specific round history JSON file path inside history/ directory."""
    safe_id = "".join(c if c.isalnum() else "_" for c in str(serial or "default"))
    return os.path.join(HISTORY_DIR, f"round_history_{safe_id}.json")


def get_device_history_csv_path(serial: Optional[str]) -> str:
    """Get device-specific play history CSV file path inside history/ directory."""
    safe_id = "".join(c if c.isalnum() else "_" for c in str(serial or "default"))
    return os.path.join(HISTORY_DIR, f"play_history_{safe_id}.csv")


def load_round_history_from_file(serial: Optional[str]) -> list:
    """Load saved round history from history/ directory."""
    path = get_device_history_path(serial)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def get_device_captcha_stats_path(serial: Optional[str]) -> str:
    """Get device-specific captcha stats JSON file path inside history/ directory."""
    safe_id = "".join(c if c.isalnum() else "_" for c in str(serial or "default"))
    return os.path.join(HISTORY_DIR, f"captcha_stats_{safe_id}.json")


def load_device_captcha_stats(serial: Optional[str]) -> dict:
    """Load saved captcha stats from history/ directory."""
    path = get_device_captcha_stats_path(serial)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {
        "total_attempts": 0,
        "success_count": 0,
        "fail_count": 0,
        "last_attempt_time": None,
        "last_result": None,
    }


def save_device_captcha_stats(serial: Optional[str], stats: dict):
    """Save captcha stats JSON inside history/ directory."""
    try:
        path = get_device_captcha_stats_path(serial)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CaptchaStats] Error saving: {e}")


def save_round_history_to_file(serial: Optional[str], history_list: list, new_entry: Optional[dict] = None):
    """Save round history list as JSON and append to CSV inside history/ directory."""
    try:
        json_path = get_device_history_path(serial)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)

        if new_entry:
            import csv
            today_str = datetime.now().strftime("%Y-%m-%d")
            csv_path = get_device_history_csv_path(serial)
            all_csv_path = os.path.join(HISTORY_DIR, "all_play_history.csv")

            boxes_str = ";".join(new_entry.get("boxes", [])) if isinstance(new_entry.get("boxes"), list) else str(new_entry.get("boxes", ""))
            current_round_str = str(new_entry.get("round", ""))
            row = [
                today_str,
                new_entry.get("time", ""),
                current_round_str,
                new_entry.get("duration", ""),
                str(new_entry.get("score", 0)),
                str(new_entry.get("coins", 0)),
                str(new_entry.get("xp", 0)),
                boxes_str,
                str(new_entry.get("box_count", 0)),
                new_entry.get("screenshot", ""),
            ]

            # Update or append to device CSV
            rows = []
            if os.path.isfile(csv_path):
                try:
                    with open(csv_path, "r", encoding="utf-8-sig") as f:
                        rows = list(csv.reader(f))
                except Exception:
                    rows = []
            if not rows:
                rows = [["Date", "Time", "Round", "Duration", "Score", "Coins", "XP", "Boxes", "BoxCount", "Screenshot"]]
            
            if len(rows) > 1 and len(rows[-1]) > 2 and rows[-1][2] == current_round_str:
                rows[-1] = row
            else:
                rows.append(row)

            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            # All devices CSV
            dev_tag = str(serial or "default")
            all_row = [today_str, new_entry.get("time", ""), dev_tag] + row[2:]
            all_rows = []
            if os.path.isfile(all_csv_path):
                try:
                    with open(all_csv_path, "r", encoding="utf-8-sig") as f:
                        all_rows = list(csv.reader(f))
                except Exception:
                    all_rows = []
            if not all_rows:
                all_rows = [["Date", "Time", "Device", "Round", "Duration", "Score", "Coins", "XP", "Boxes", "BoxCount", "Screenshot"]]
            
            if len(all_rows) > 1 and len(all_rows[-1]) > 3 and all_rows[-1][2] == dev_tag and all_rows[-1][3] == current_round_str:
                all_rows[-1] = all_row
            else:
                all_rows.append(all_row)

            with open(all_csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(all_rows)
    except Exception as e:
        print(f"[History] Error saving history: {e}")

BOOST_OPTIONS = [
    {"id": "double_coins", "name": "Double Coins (2x)", "template": BOOST_DOUBLE_COINS_TEMPLATE},
    {"id": "score_15", "name": "+15% Score Bonus", "template": BOOST_15P_SCORE_BONUS_TEMPLATE},
    {"id": "hp_drain_15", "name": "-15% HP Drain", "template": BOOST_M15P_HP_DRAIN_TEMPLATE},
    {"id": "revive_80", "name": "Revive Once with 80 HP", "template": BOOST_REVIVE_ONCE_WITH_80HP_TEMPLATE},
    {"id": "crush_70", "name": "70% Crush Chance", "template": BOOST_70P_CRUSH_CHANCE_TEMPLATE},
    {"id": "speed_17", "name": "+17% Base Speed", "template": BOOST_17P_BASE_SPEED_TEMPLATE},
    {"id": "coin_magic", "name": "Gold Coin Magic", "template": BOOST_GOLD_COIN_MAGIC_TEMPLATE},
    {"id": "damage_30", "name": "-30% Collision Damage", "template": BOOST_M30P_COLLISION_DAMAGE_TEMPLATE},
    {"id": "potions_20", "name": "+20% HP from Potions", "template": BOOST_20P_HP_FROM_POTIONS_TEMPLATE},
    {"id": "magnetic", "name": "Magnetic Aura", "template": BOOST_MAGNETIC_AURA_TEMPLATE},
    {"id": "pit_lifts_2", "name": "2 Pit Lifts", "template": BOOST_2PIT_LIFTS_TEMPLATE},
]


def get_detection_stage_names(group_name: str, exclude: Optional[set] = None) -> List[str]:
    stage_names = []
    if group_name != "IN_GAME":
        for stage_name in DETECTION_ALWAYS_STAGES:
            if stage_name not in stage_names:
                stage_names.append(stage_name)
    for stage_name in DETECTION_GROUPS[group_name]:
        if stage_name not in stage_names:
            stage_names.append(stage_name)
    if group_name == "IN_GAME":
        for stage_name in DETECTION_ALWAYS_STAGES:
            if stage_name not in stage_names:
                stage_names.append(stage_name)
    if exclude:
        stage_names = [s for s in stage_names if s not in exclude]
    return stage_names


_in_bot_log = threading.local()


class BotEngine:
    def __init__(self, device_serial: Optional[str] = None, device_ip: Optional[str] = None, device_port: Optional[int] = None):
        self.is_running = False
        self.should_stop = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Config state
        if device_serial:
            self.device_serial = str(device_serial).strip()
            if ":" in self.device_serial and not self.device_serial.startswith("emulator-"):
                parts = self.device_serial.split(":", 1)
                self.device_ip = parts[0]
                try:
                    self.device_port = int(parts[1])
                except Exception:
                    self.device_port = 5555
            else:
                self.device_ip = self.device_serial
                self.device_port = 5555
        else:
            self.device_ip = device_ip or config.DEVICE_IP
            self.device_port = device_port or config.DEVICE_PORT
            self.device_serial = f"{self.device_ip}:{self.device_port}"

        self.use_hp_boost = False
        self.use_item_extension = False
        self.use_double_xp = False
        self.use_fast_start = False
        self.fast_start_min_stock = 10
        self.use_cookie_relay = False
        self.cookie_relay_min_stock = 10
        self.use_desired_random_boost = False
        self.desired_boost_id = "double_coins"
        self.detect_relic = True
        self.send_friend_lives = True
        self.stop_goal_rounds_enabled: bool = False
        self.stop_goal_rounds_target: int = 50
        self.stop_goal_boxes_enabled: bool = False
        self.stop_goal_boxes_target: int = 20
        self.early_exit_boxes_enabled: bool = True
        self.early_exit_boxes_target: int = 2
        self.early_exit_triggered: bool = False
        self._last_box_check_time: float = 0.0
        self._box_target_consecutive_hits: int = 0
        self.stop_goal_time_enabled: bool = False
        self.stop_goal_time_hours: float = 2.0
        self.auto_action_enabled: bool = False
        self.auto_action_mode: str = "both"  # "jump_only", "slide_only", "both"
        self.auto_action_interval: float = 1.5
        self._last_auto_action_time: float = 0.0
        self._auto_action_toggle: bool = False
        self._mainmenu_play_fail_count: int = 0
        self._purchase_item_fail_count: int = 0

        # Load device-specific settings if present (check settings/ first, then legacy src/)
        dev_file = get_device_settings_path(self.device_serial)
        safe_id = "".join(c if c.isalnum() else "_" for c in str(self.device_serial or "default"))
        legacy_dev_file = os.path.join(LEGACY_SETTINGS_DIR, f"bot_settings_{safe_id}.json")
        def_file = DEFAULT_SETTINGS_PATH
        legacy_def_file = os.path.join(LEGACY_SETTINGS_DIR, "bot_settings.json")

        init_file = None
        for p in [dev_file, legacy_dev_file, def_file, legacy_def_file]:
            if os.path.isfile(p):
                init_file = p
                break

        if init_file:
            try:
                with open(init_file, "r", encoding="utf-8") as f:
                    init_cfg = json.load(f)
                self.use_hp_boost = bool(init_cfg.get("use_hp_boost", False))
                self.use_item_extension = bool(init_cfg.get("use_item_extension", False))
                self.use_double_xp = bool(init_cfg.get("use_double_xp", False))
                self.use_fast_start = bool(init_cfg.get("use_fast_start", False))
                self.fast_start_min_stock = int(init_cfg.get("fast_start_min_stock", 10))
                self.use_cookie_relay = bool(init_cfg.get("use_cookie_relay", False))
                self.cookie_relay_min_stock = int(init_cfg.get("cookie_relay_min_stock", 10))
                self.use_desired_random_boost = bool(init_cfg.get("use_desired_random_boost", False))
                self.desired_boost_id = init_cfg.get("desired_boost_id", "double_coins")
                self.detect_relic = bool(init_cfg.get("detect_relic", True))
                self.send_friend_lives = bool(init_cfg.get("send_friend_lives", True))
                self.stop_goal_rounds_enabled = bool(init_cfg.get("stop_goal_rounds_enabled", False))
                self.stop_goal_rounds_target = int(init_cfg.get("stop_goal_rounds_target", 50))
                self.stop_goal_boxes_enabled = bool(init_cfg.get("stop_goal_boxes_enabled", False))
                self.stop_goal_boxes_target = int(init_cfg.get("stop_goal_boxes_target", 20))
                self.early_exit_boxes_enabled = bool(init_cfg.get("early_exit_boxes_enabled", True))
                self.early_exit_boxes_target = int(init_cfg.get("early_exit_boxes_target", 2))
                self.stop_goal_time_enabled = bool(init_cfg.get("stop_goal_time_enabled", False))
                self.stop_goal_time_hours = float(init_cfg.get("stop_goal_time_hours", 2.0))
                self.auto_action_enabled = bool(init_cfg.get("auto_action_enabled", False))
                self.auto_action_mode = str(init_cfg.get("auto_action_mode", "both"))
                self.auto_action_interval = float(init_cfg.get("auto_action_interval", 1.5))
                self.enable_realtime_dodging = bool(init_cfg.get("enable_realtime_dodging", False))
                self.macro_enabled = bool(init_cfg.get("macro_enabled", False))
                self.selected_macro_id = str(init_cfg.get("selected_macro_id", "preset_basic_run"))
            except Exception:
                pass

        if not hasattr(self, "macro_enabled"):
            self.macro_enabled = False
        if not hasattr(self, "selected_macro_id"):
            self.selected_macro_id = "preset_basic_run"

        from macro_player import MacroPlayer
        self.macro_player = MacroPlayer(self.device_serial or self.device_ip)

        self.start_time: Optional[float] = None
        self.current_stage: str = "IDLE"
        self.rounds_played: int = 0
        self.mystery_boxes: int = 0

        self.box_counts: Dict[str, int] = {
            "wood": 0,
            "silver": 0,
            "gold": 0,
            "rainbow": 0,
            "total": 0,
        }
        self.box_history: deque = deque(maxlen=100)

        self.round_history: deque = deque(maxlen=50)
        self.round_screenshots: Dict[int, bytes] = {}
        self.current_round_start_time: float = 0
        self.current_round_recorded: bool = False
        self.current_round_boxes: List[str] = []
        self.current_round_mystery_box_handled: bool = False
        self.current_round_screen: Optional[np.ndarray] = None
        self.pending_round_summary: Optional[Dict[str, Any]] = None
        self.captcha_stats: Dict[str, Any] = load_device_captcha_stats(self.device_serial)

        self.lifetime_coins_earned: int = 0
        self.lifetime_xp_earned: int = 0
        self.session_coins_earned: int = 0
        self.last_round_coins: int = 0
        self.session_xp_earned: int = 0
        self.last_round_xp: int = 0
        self.accumulated_uptime_seconds: int = 0
        self.session_uptime_seconds: int = 0
        self.session_rounds_played: int = 0
        self.session_start_time: Optional[float] = None
        self.session_start_time_str: str = ""
        self.session_box_counts: Dict[str, int] = {
            "wood": 0,
            "silver": 0,
            "gold": 0,
            "rainbow": 0,
            "total": 0,
        }
        self.session_round_history: deque = deque(maxlen=50)

        past_history = load_round_history_from_file(self.device_serial)
        if past_history:
            self.round_history.extend(past_history[:50])
            for h in past_history:
                self.lifetime_coins_earned += int(h.get("coins", 0) or 0)
                self.lifetime_xp_earned += int(h.get("xp", 0) or 0)

                dur = str(h.get("duration", ""))
                m = re.search(r"(\d+)m", dur)
                s = re.search(r"(\d+)s", dur)
                sec = (int(m.group(1)) * 60 if m else 0) + (int(s.group(1)) if s else 0)
                self.accumulated_uptime_seconds += sec

                boxes = h.get("boxes", [])
                if isinstance(boxes, list):
                    for b in boxes:
                        if b in self.box_counts:
                            self.box_counts[b] += 1
                        self.box_counts["total"] += 1
            self.mystery_boxes = self.box_counts["total"]
            if self.round_history:
                self.rounds_played = max(int(h.get("round", 0) or 0) for h in self.round_history)

        # Frame buffer for live stream
        self.latest_frame_jpeg: Optional[bytes] = None
        self.latest_currency_crop_jpeg: Optional[bytes] = None
        self.last_frame_time: float = 0

        # Logs buffer
        self.logs: deque = deque(maxlen=200)
        self.ws_subscribers: List[asyncio.Queue] = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        target = self.device_serial or (f"{self.device_ip}:{self.device_port}" if self.device_ip else "")
        log_entry = {
            "time": timestamp,
            "timestamp": timestamp,
            "message": message,
            "level": level,
            "device": target,
            "target": target,
        }
        self.logs.append(log_entry)
        dev_tag = f"[{target}]" if target else ""
        _in_bot_log.active = True
        try:
            if dev_tag:
                print(f"[{timestamp}]  {dev_tag}\n{message}")
            else:
                print(f"[{timestamp}]\n{message}")
        finally:
            _in_bot_log.active = False

        mgr = globals().get("engine_manager")
        loop = self.loop or getattr(mgr, "loop", None)
        if loop and self.ws_subscribers:
            for q in list(self.ws_subscribers):
                try:
                    loop.call_soon_threadsafe(q.put_nowait, log_entry)
                except Exception:
                    pass

        if mgr:
            mgr.record_and_broadcast_log(log_entry)

    def interruptible_sleep(self, seconds: float) -> bool:
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self.should_stop:
                return True
            time.sleep(0.1)
        return False

    def update_frame(self, screen_bgr: np.ndarray):
        if screen_bgr is not None:
            try:
                target_w = 854
                target_h = 480
                resized = cv2.resize(screen_bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)
                _, buffer = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
                self.latest_frame_jpeg = buffer.tobytes()
                self.last_frame_time = time.time()

                h, w = screen_bgr.shape[:2]
                if h >= 100 and w >= 1200:
                    curr_crop = screen_bgr[10:72, 730:1220]
                    _, curr_buf = cv2.imencode(".jpg", curr_crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    self.latest_currency_crop_jpeg = curr_buf.tobytes()
            except Exception:
                pass

    def get_device_model_label(self) -> str:
        if getattr(self, "device_model", None):
            return self.device_model
        raw_target = self.device_serial or (f"{self.device_ip}:{self.device_port}" if self.device_ip else "")
        try:
            from adb import resolve_emulator_name, get_adb_path, _run_cmd, _format_target
            emu_name = resolve_emulator_name(raw_target)
            if emu_name:
                self.device_model = emu_name
                return emu_name

            target = _format_target(self.device_serial or self.device_ip, self.device_port)
            adb = get_adb_path()
            res = _run_cmd([adb, "-s", target, "shell", "getprop", "ro.product.model"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            model = res.stdout.strip()
            if model:
                self.device_model = model.replace("_", "-")
                return self.device_model
        except Exception:
            pass
        return raw_target or "CookieRun"

    def _flush_pending_round_summary(self):
        """ส่งข้อความสรุปผลรอบ Discord ที่รอตรวจสอบหน้า MYSTERY_BOX ไว้ (หากยังไม่ได้ส่ง)"""
        if self.pending_round_summary:
            p = self.pending_round_summary
            self.pending_round_summary = None
            try:
                discord_notifier.send_round_summary(
                    round_num=p["round_num"],
                    duration_str=p["duration_str"],
                    coins_earned=p["coins_earned"],
                    session_coins=p["session_coins"],
                    xp_earned=p["xp_earned"],
                    session_xp=p["session_xp"],
                    boxes=p.get("boxes") or [],
                    screen_img=p.get("screen_img"),
                    device_name=p.get("device_name") or self.get_device_model_label(),
                    duration_sec=p.get("duration_sec", 0),
                    session_rounds=p.get("session_rounds", self.session_rounds_played),
                    session_boxes=p.get("session_boxes") or dict(self.session_box_counts),
                )
            except Exception as e:
                self.log(f" ไม่สามารถส่งสรุปผลรอบ Discord: {e}", "warning")

    def start(self, user_config: Dict[str, Any]):
        with self.lock:
            if self.is_running:
                return {"success": False, "message": "Bot is already running"}

            dev_req = user_config.get("device_serial") or user_config.get("device") or self.device_serial
            if dev_req:
                self.device_serial = str(dev_req).strip()
                if ":" in self.device_serial and not self.device_serial.startswith("emulator-"):
                    parts = self.device_serial.split(":", 1)
                    self.device_ip = parts[0]
                    try:
                        self.device_port = int(parts[1])
                    except Exception:
                        self.device_port = 5555
                else:
                    self.device_ip = self.device_serial
                    self.device_port = 5555
            else:
                self.device_ip = user_config.get("device_ip", self.device_ip)
                self.device_port = int(user_config.get("device_port", self.device_port))
                self.device_serial = f"{self.device_ip}:{self.device_port}"

            self.use_hp_boost = bool(user_config.get("use_hp_boost", False))
            self.use_item_extension = bool(user_config.get("use_item_extension", False))
            self.use_double_xp = bool(user_config.get("use_double_xp", False))
            self.use_fast_start = bool(user_config.get("use_fast_start", False))
            self.fast_start_min_stock = int(user_config.get("fast_start_min_stock", 10))
            self.use_cookie_relay = bool(user_config.get("use_cookie_relay", False))
            self.cookie_relay_min_stock = int(user_config.get("cookie_relay_min_stock", 10))
            self.use_desired_random_boost = bool(user_config.get("use_desired_random_boost", False))
            self.desired_boost_id = user_config.get("desired_boost_id", "double_coins")
            self.detect_relic = bool(user_config.get("detect_relic", True))
            self.send_friend_lives = bool(user_config.get("send_friend_lives", True))
            self.stop_goal_rounds_enabled = bool(user_config.get("stop_goal_rounds_enabled", False))
            self.stop_goal_rounds_target = int(user_config.get("stop_goal_rounds_target", 50))
            self.stop_goal_boxes_enabled = bool(user_config.get("stop_goal_boxes_enabled", False))
            self.stop_goal_boxes_target = int(user_config.get("stop_goal_boxes_target", 20))
            self.early_exit_boxes_enabled = bool(user_config.get("early_exit_boxes_enabled", True))
            self.early_exit_boxes_target = int(user_config.get("early_exit_boxes_target", 2))
            self.early_exit_triggered = False
            self._box_target_consecutive_hits = 0
            self._mainmenu_play_fail_count = 0
            self._purchase_item_fail_count = 0
            self.stop_goal_time_enabled = bool(user_config.get("stop_goal_time_enabled", False))
            self.stop_goal_time_hours = float(user_config.get("stop_goal_time_hours", 2.0))
            self.macro_enabled = bool(user_config.get("macro_enabled", getattr(self, "macro_enabled", False)))
            self.selected_macro_id = str(user_config.get("selected_macro_id", getattr(self, "selected_macro_id", "preset_basic_run")))

            # Device context is set per-thread in _run_loop
            self.is_running = True
            self.should_stop = False
            self.start_time = time.time()
            self.session_start_time = self.start_time
            self.session_start_time_str = datetime.now().strftime("%H:%M:%S")
            self.session_coins_earned = 0
            self.session_xp_earned = 0
            self.session_rounds_played = 0
            self.session_uptime_seconds = 0
            self.session_box_counts = {
                "wood": 0,
                "silver": 0,
                "gold": 0,
                "rainbow": 0,
                "total": 0,
            }
            self.session_round_history.clear()
            self.current_round_start_time = time.time()
            self.current_round_recorded = False
            self.current_stage = "INITIALIZING"
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            self.log(f" Bot started (Device: {self.device_ip}:{self.device_port})", "success")
            discord_notifier.send_bot_start(self.device_ip, self.device_port, device_name=self.get_device_model_label())

        return {"success": True, "message": "Bot started successfully"}

    def stop(self):
        with self.lock:
            if not self.is_running:
                return {"success": True, "message": "บอทหยุดทำงานอยู่แล้ว"}

            self.should_stop = True
            self.current_stage = "STOPPING"
            self.log(" Stopping bot...", "warning")

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)

        if hasattr(self, "macro_player") and self.macro_player:
            self.macro_player.stop()

        self._flush_pending_round_summary()

        with self.lock:
            self.is_running = False
            self.current_stage = "IDLE"
            self.log(" Bot stopped", "info")
            session_sec = int(time.time() - self.start_time) if self.start_time else 0
            self.session_uptime_seconds = session_sec
            self.accumulated_uptime_seconds += session_sec
            self.start_time = None
            hours, remainder = divmod(session_sec, 3600)
            minutes, seconds = divmod(remainder, 60)
            session_uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            discord_notifier.send_bot_stop(
                uptime=session_uptime_str,
                rounds_played=self.rounds_played,
                total_boxes=self.mystery_boxes,
                coins_earned=self.session_coins_earned,
                session_xp=self.session_xp_earned,
                device_name=self.get_device_model_label(),
            )

        return {"success": True, "message": "Bot stopped successfully"}

    def reset_stats(self):
        self.rounds_played = 0
        self.session_rounds_played = 0
        self.mystery_boxes = 0
        self.box_counts = {
            "wood": 0,
            "silver": 0,
            "gold": 0,
            "rainbow": 0,
            "total": 0,
        }
        self.session_box_counts = {
            "wood": 0,
            "silver": 0,
            "gold": 0,
            "rainbow": 0,
            "total": 0,
        }
        self.lifetime_coins_earned = 0
        self.session_coins_earned = 0
        self.last_round_coins = 0
        self.lifetime_xp_earned = 0
        self.session_xp_earned = 0
        self.last_round_xp = 0
        self.accumulated_uptime_seconds = 0
        self.session_uptime_seconds = 0
        self.session_start_time = None
        self.session_start_time_str = ""
        self.round_history.clear()
        self.session_round_history.clear()
        self.round_screenshots.clear()
        self.box_history.clear()
        self.current_round_boxes = []
        self.current_round_mystery_box_handled = False
        self.pending_round_summary = None
        self.captcha_stats = {
            "total_attempts": 0,
            "success_count": 0,
            "fail_count": 0,
            "last_attempt_time": None,
            "last_result": None,
        }
        path_cap = get_device_captcha_stats_path(self.device_serial)
        if os.path.isfile(path_cap):
            try:
                os.remove(path_cap)
            except Exception:
                pass

        # Remove device-specific history files from disk
        path_json = get_device_history_path(self.device_serial)
        if os.path.isfile(path_json):
            try:
                os.remove(path_json)
            except Exception:
                pass
        path_csv = get_device_history_csv_path(self.device_serial)
        if os.path.isfile(path_csv):
            try:
                os.remove(path_csv)
            except Exception:
                pass

        self.log(" ล้างข้อมูลสถิติ กล่องปริศนา เหรียญ EXP และการแก้แคปซ่าทั้งหมดเป็น 0 แล้ว", "info")

    def clear_round_history(self):
        """Clear round history in memory and delete history files from disk."""
        with self.lock:
            self.round_history.clear()
            self.session_round_history.clear()
            self.round_screenshots.clear()
            self.pending_round_summary = None
            self.rounds_played = 0
            if "rounds_played" in self.stats:
                self.stats["rounds_played"] = 0
            path_json = get_device_history_path(self.device_serial)
            if os.path.isfile(path_json):
                try:
                    os.remove(path_json)
                except Exception:
                    pass
            path_csv = get_device_history_csv_path(self.device_serial)
            if os.path.isfile(path_csv):
                try:
                    os.remove(path_csv)
                except Exception:
                    pass
            self.log(" ล้างประวัติการเล่นเรียบร้อยแล้ว", "info")

    def get_status(self) -> Dict[str, Any]:
        session_sec = int(time.time() - self.start_time) if self.is_running and self.start_time else (self.session_uptime_seconds or 0)
        total_uptime_sec = self.accumulated_uptime_seconds + (session_sec if self.is_running else 0)
        hours, remainder = divmod(total_uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        sh, sremainder = divmod(session_sec, 3600)
        sm, ss = divmod(sremainder, 60)
        session_uptime_str = f"{sh:02d}:{sm:02d}:{ss:02d}"

        session_coins_per_hour = int(self.session_coins_earned / max(0.001, session_sec / 3600)) if (session_sec > 10) else 0
        lifetime_coins_per_hour = int(self.lifetime_coins_earned / max(0.001, total_uptime_sec / 3600)) if (total_uptime_sec > 10) else 0

        return {
            "is_running": self.is_running,
            "current_stage": self.current_stage,
            "uptime": uptime_str,
            "total_uptime": uptime_str,
            "uptime_seconds": total_uptime_sec,
            "session_uptime": session_uptime_str,
            "session_uptime_seconds": session_sec,
            "session_start_time": self.session_start_time_str,
            "session_rounds": self.session_rounds_played,
            "rounds_played": self.rounds_played,
            "session_mystery_boxes": self.session_box_counts.get("total", 0),
            "mystery_boxes": self.mystery_boxes,
            "session_box_counts": self.session_box_counts,
            "box_counts": self.box_counts,
            "captcha_stats": self.captcha_stats,
            "coin_stats": {
                "session_earned": self.session_coins_earned,
                "session_xp_earned": self.session_xp_earned,
                "lifetime_earned": self.lifetime_coins_earned,
                "lifetime_xp_earned": self.lifetime_xp_earned,
                "coins_per_hour": session_coins_per_hour,
                "lifetime_coins_per_hour": lifetime_coins_per_hour,
                "last_round": self.last_round_coins,
                "last_round_xp": self.last_round_xp,
            },
            "session_round_history": list(self.session_round_history),
            "round_history": list(self.round_history),
            "device_serial": self.device_serial,
            "device_ip": self.device_ip,
            "device_port": self.device_port,
            "use_hp_boost": self.use_hp_boost,
            "use_item_extension": self.use_item_extension,
            "use_double_xp": self.use_double_xp,
            "use_fast_start": self.use_fast_start,
            "fast_start_min_stock": self.fast_start_min_stock,
            "use_cookie_relay": self.use_cookie_relay,
            "cookie_relay_min_stock": self.cookie_relay_min_stock,
            "use_desired_random_boost": self.use_desired_random_boost,
            "desired_boost_id": self.desired_boost_id,
            "detect_relic": self.detect_relic,
            "send_friend_lives": self.send_friend_lives,
            "stop_goal_rounds_enabled": self.stop_goal_rounds_enabled,
            "stop_goal_rounds_target": self.stop_goal_rounds_target,
            "stop_goal_boxes_enabled": self.stop_goal_boxes_enabled,
            "stop_goal_boxes_target": self.stop_goal_boxes_target,
            "early_exit_boxes_enabled": self.early_exit_boxes_enabled,
            "early_exit_boxes_target": self.early_exit_boxes_target,
            "stop_goal_time_enabled": self.stop_goal_time_enabled,
            "stop_goal_time_hours": self.stop_goal_time_hours,
            "adb_path": get_adb_path(),
            "discord_settings": {
                "webhook_url": discord_notifier.webhook_url,
                "enabled": discord_notifier.enabled,
                "notify_boxes": discord_notifier.notify_boxes,
                "notify_antibot": discord_notifier.notify_antibot,
                "notify_status": discord_notifier.notify_status,
                "attach_screenshot": discord_notifier.attach_screenshot,
            }
        }

    def get_desired_boost_info(self):
        """Returns (template, display_name) for the currently selected desired_boost_id."""
        boost_item = next((b for b in BOOST_OPTIONS if b["id"] == self.desired_boost_id), BOOST_OPTIONS[0])
        return boost_item["template"], boost_item["name"]

    def get_relic_exclude(self):
        """Returns exclude set for stage detection based on detect_relic setting."""
        return None if self.detect_relic else {"RELIC_COMPLETE", "RELIC_CLAIM"}

    def check_and_apply_settings_update(self, new_config: Optional[dict] = None) -> list:
        """
        Check for configuration updates (either passed in or loaded from bot_settings.json),
        apply them to the running bot instance, and log any changes.
        Returns a list of human-readable changes detected.
        """
        if new_config is None:
            dev_path = get_device_settings_path(self.device_serial)
            settings_path = dev_path if os.path.exists(dev_path) else DEFAULT_SETTINGS_PATH
            if not os.path.exists(settings_path):
                legacy_path = os.path.join(LEGACY_SETTINGS_DIR, "bot_settings.json")
                if os.path.exists(legacy_path):
                    settings_path = legacy_path
                else:
                    return []
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    new_config = json.load(f)
            except Exception:
                return []

        if not isinstance(new_config, dict):
            return []

        changes = []

        def boost_name_by_id(bid):
            item = next((b for b in BOOST_OPTIONS if b["id"] == bid), None)
            return item["name"] if item else str(bid)

        fields_to_check = [
            ("use_hp_boost", "HP Extension (+30 HP)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("use_item_extension", "Item Extension (นาฬิกา)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("use_double_xp", "Double XP (EXP x2)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("use_fast_start", "Fast Start (ออกตัวเร็ว)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("fast_start_min_stock", "เกณฑ์ซื้อ Fast Start", int, lambda v: f"{v} ชิ้น"),
            ("use_cookie_relay", "Cookie Relay (ผลัดคุกกี้)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("cookie_relay_min_stock", "เกณฑ์ซื้อ Cookie Relay", int, lambda v: f"{v} ชิ้น"),
            ("use_desired_random_boost", "Random Boost (สุ่มหาบัฟ)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("desired_boost_id", "เป้าหมาย Random Boost", str, boost_name_by_id),
            ("detect_relic", "รับสมบัติโบราณ (Relic)", bool, lambda v: "เปิด" if v else "ปิด"),
            ("send_friend_lives", "ส่งหัวใจให้เพื่อน", bool, lambda v: "เปิด" if v else "ปิด"),
            ("stop_goal_rounds_enabled", "หยุดเมื่อครบจำนวนรอบ", bool, lambda v: "เปิด" if v else "ปิด"),
            ("stop_goal_rounds_target", "เป้าหมายจำนวนรอบ", int, lambda v: f"{v} รอบ"),
            ("stop_goal_boxes_enabled", "หยุดเมื่อครบจำนวนกล่อง", bool, lambda v: "เปิด" if v else "ปิด"),
            ("stop_goal_boxes_target", "เป้าหมายจำนวนกล่อง", int, lambda v: f"{v} กล่อง"),
            ("early_exit_boxes_enabled", "ออกจากห้องเมื่อได้กล่องครบ", bool, lambda v: "เปิด" if v else "ปิด"),
            ("early_exit_boxes_target", "เป้าหมายกล่องก่อนออก", int, lambda v: f"{v} กล่อง"),
            ("stop_goal_time_enabled", "หยุดเมื่อครบเวลา", bool, lambda v: "เปิด" if v else "ปิด"),
            ("stop_goal_time_hours", "เป้าหมายเวลา", float, lambda v: f"{v} ชม."),
            ("auto_action_enabled", "วิ่ง+กระโดด/สไลด์ อัตโนมัติ", bool, lambda v: "เปิด" if v else "ปิด"),
            ("auto_action_mode", "โหมดแอ็กชันขณะวิ่ง", str, lambda v: {"jump_only": "กระโดดอย่างเดียว", "slide_only": "สไลด์อย่างเดียว", "both": "กระโดด + สไลด์"}.get(v, v)),
            ("auto_action_interval", "เวลาหน่วงแอ็กชัน", float, lambda v: f"{v:g} วินาที"),
            ("macro_enabled", "โหมดเล่นตามมาโคร", bool, lambda v: "เปิด" if v else "ปิด"),
            ("selected_macro_id", "มาโครที่เลือก", str, lambda v: str(v)),
        ]

        with self.lock:
            for field, label, conv, formatter in fields_to_check:
                if field in new_config:
                    try:
                        new_val = conv(new_config[field])
                        old_val = getattr(self, field, None)
                        if old_val != new_val:
                            old_display = formatter(old_val) if old_val is not None else "ไม่มี"
                            new_display = formatter(new_val)
                            changes.append(f"{label}: {old_display} ➜ {new_display}")
                            setattr(self, field, new_val)
                            if field == "send_friend_lives" and new_val is True:
                                self._trigger_send_lives = True
                    except Exception:
                        pass

        if changes and self.is_running:
            self.log(" ตรวจพบการตั้งค่าใหม่ (Bot Settings Updated):", "info")
            for ch in changes:
                self.log(f"   • {ch}", "info")

        return changes

    def _run_loop(self):
        target = self.device_serial or self.device_ip
        from actions import set_device_context
        set_device_context(target, self.device_port)
        try:
            self.log(f"🔌 Connecting to device {target}...")
            device_connect(target, self.device_port)
            self.log(" ADB Connection established", "success")

            self.log(" Pre-warming OpenCV templates...")
            load_templates()
            self.log(" Templates loaded", "success")

            if self.use_desired_random_boost:
                _, initial_boost_name = self.get_desired_boost_info()
                self.log(f" Desired Random Boost: {initial_boost_name}")

            last_stage = None
            is_first_game = True
            detection_group = "PRE_GAME"
            last_detected_time = time.time()
            session_start_time = time.time()
            session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
            last_lives_time = time.time()
            lives_interval = random.uniform(25 * 60, 35 * 60)
            pending_send_friend_life = bool(self.send_friend_lives)
            in_game_last_stage_check = 0.0
            last_action_log_time = 0.0

            self.log("🏁 Main loop started. Waiting for game screen...")

            while not self.should_stop:
                # -------------------------------------------------------------
                # 1. SCREEN CAPTURE (ADB)
                # -------------------------------------------------------------
                try:
                    device_screen = device_capture_screen(target, self.device_port)
                    self.update_frame(device_screen)
                except Exception as e:
                    self.log(f" Screen capture error: {e}", "error")
                    if self.interruptible_sleep(1.0):
                        break
                    continue

                # -------------------------------------------------------------
                # 2. STAGE DETECTION & STATE MACHINE
                # -------------------------------------------------------------
                relic_exclude = self.get_relic_exclude()
                stage = detect_stage(device_screen, get_detection_stage_names(detection_group, exclude=relic_exclude))
                if stage is None:
                    if time.time() - last_detected_time >= DETECTION_RECOVERY_SCAN_INTERVAL[detection_group]:
                        stage = detect_stage(device_screen, exclude=relic_exclude)
                        if stage is not None:
                            last_detected_time = time.time()
                else:
                    last_detected_time = time.time()

                if stage is not None and stage != "CONNECTION_LOST":
                    self._connection_lost_retries = 0

                # 🚨 Auto-Recovery Watchdog: If game is stuck / unplayable / button not found (outside active run)
                if detection_group != "IN_GAME" and stage is None:
                    stuck_sec = time.time() - last_detected_time
                    # Soft Recovery: at 30 seconds, try closing any popup or news dialog (e.g. New Packages, Event, Announcement)
                    if stuck_sec >= 30.0 and stuck_sec < 35.0:
                        self.log(" ไม่พบปุ่มนำทางเกิน 30 วินาที — กำลังลองกดปิดป๊อปอัปแจ้งเตือน...", "warning")
                        close_announcement_dialog()
                    # Hard Recovery: only if truly stuck with no buttons for > 90 seconds
                    elif stuck_sec >= 90.0:
                        self.log("🚨 [Watchdog] ตรวจพบเกมติดค้างหาปุ่มไม่เจอเกิน 90 วินาที — กำลังบันทึกรูปและรีสตาร์ทแอป...", "error")
                        try:
                            record_game_error(
                                device_serial=target,
                                reason="เกมกดเล่นไม่ได้ หรือติดค้างหาปุ่มไม่เจอเกิน 90 วินาที",
                                details=f"ติดค้างอยู่ที่สถานะ {self.current_stage} ไม่สามารถเริ่มเกมหรือดำเนินการต่อได้",
                                screen_img=device_screen,
                                action_taken="บันทึกภาพหน้าจอลง logs_error/ และบังคับรีสตาร์ทแอปเกม CookieRun"
                            )
                        except Exception as err:
                            self.log(f" บันทึก error log ไม่สำเร็จ: {err}", "warning")

                        if hasattr(self, "macro_player") and self.macro_player.is_running:
                            self.macro_player.stop()
                        device_reset_app(target, self.device_port)
                        if self.interruptible_sleep(2.0):
                            break
                        close_announcement_dialog()
                        last_detected_time = time.time()
                        last_lives_time = time.time()
                        detection_group = "PRE_GAME"
                        last_stage = None
                        is_first_game = True
                        continue

                if stage:
                    self.current_stage = stage
                    # หากผ่านช่วงจบเกมมายังหน้าอื่นโดยไม่เจอหน้าเปิดกล่อง ให้ส่งสรุปรอบที่รอดำเนินการอยู่ทันที
                    if self.pending_round_summary and stage not in ("MYSTERY_BOX", "GAME_COMPLETE", "OVERTAKE_BREAK_SCORE"):
                        self._flush_pending_round_summary()
                elif self.current_stage not in ("STARTING", "STOPPING"):
                    self.current_stage = f"{detection_group} (Searching...)"

                # Safety timeout: หากรอนานเกิน 15 วินาทีแล้วยังไม่เข้า MYSTERY_BOX ให้ส่งสรุปรอบ
                if self.pending_round_summary and (time.time() - self.pending_round_summary.get("created_at", 0) > 15.0):
                    self._flush_pending_round_summary()

                #  Early Exit on Mystery Box Goal during active in-game running
                if detection_group == "IN_GAME" and self.early_exit_boxes_enabled and not self.early_exit_triggered and device_screen is not None:
                    now = time.time()
                    if now - self._last_box_check_time >= 0.35:
                        self._last_box_check_time = now
                        box_count = detect_ingame_box_count(device_screen)
                        effective_target = min(2, max(1, self.early_exit_boxes_target))
                        if box_count >= effective_target and box_count > 0:
                            self._box_target_consecutive_hits += 1
                            if self._box_target_consecutive_hits >= 2 or box_count >= 2:
                                self.early_exit_triggered = True
                                self._box_target_consecutive_hits = 0
                                self.log(
                                    f" [Box Farming] เก็บกล่องในรอบนี้ได้ {box_count} กล่อง (ครบเป้าหมาย {effective_target} กล่องแล้ว)! กำลังกด Pause เพื่อออกจากห้องและเริ่มรอบใหม่...",
                                    "success",
                                )
                                if hasattr(self, "macro_player") and self.macro_player.is_running:
                                    self.macro_player.stop()
                                exit_in_game_run(target, self.device_port, log_fn=self.log)
                                detection_group = "POST_GAME"
                                last_stage = None
                                last_detected_time = time.time()
                                continue
                        else:
                            self._box_target_consecutive_hits = 0

                #  Auto Jump / Slide or Macro playback during active in-game running
                if detection_group == "IN_GAME" and stage is None:
                    if self.macro_enabled and hasattr(self, "macro_player") and self.macro_player.is_running:
                        # Macro player is actively executing timeline in its dedicated thread
                        pass
                    elif self.auto_action_enabled:
                        now = time.time()
                        if now - self._last_auto_action_time >= max(0.2, self.auto_action_interval):
                            self._last_auto_action_time = now
                            if self.auto_action_mode == "jump_only":
                                perform_auto_jump()
                            elif self.auto_action_mode == "slide_only":
                                perform_auto_slide(250)
                            else:  # "both"
                                if not self._auto_action_toggle:
                                    perform_auto_jump()
                                else:
                                    perform_auto_slide(250)
                                self._auto_action_toggle = not self._auto_action_toggle

                if stage == last_stage:
                    if self.interruptible_sleep(0.1):
                        break
                    continue

                last_stage = stage

                if stage == "MAINMENU":
                    self.log(" Detected Stage: MAINMENU", "stage")

                    # ตรวจสอบการตั้งค่าใหม่ก่อนเริ่มรอบ
                    self.check_and_apply_settings_update()

                    if getattr(self, "_trigger_send_lives", False):
                        pending_send_friend_life = True
                        self._trigger_send_lives = False

                    if self.interruptible_sleep(1.0):
                        break

                    lives_elapsed = time.time() - last_lives_time
                    if self.send_friend_lives and (pending_send_friend_life or lives_elapsed >= lives_interval):
                        self.log(" ตรวจสอบและส่งหัวใจให้เพื่อน...", "stage")
                        try:
                            handle_quick_receive_and_send_lives()
                        except Exception as e:
                            self.log(f" รับส่งหัวใจกล่องจดหมาย: {e}", "warning")
                        try:
                            handle_send_friend_life()
                        except Exception as e:
                            self.log(f" ส่งหัวใจรายชื่อเพื่อน: {e}", "warning")
                        self.log(" ดำเนินการส่งหัวใจเสร็จสิ้น", "success")
                        pending_send_friend_life = False
                        last_lives_time = time.time()
                        lives_interval = random.uniform(25 * 60, 35 * 60)
                        last_stage = None
                        continue

                    elapsed = time.time() - session_start_time
                    if elapsed >= session_reset_interval:
                        self.log(f" Session reset triggered after {elapsed / 3600:.2f}h — restarting app...")
                        device_reset_app(target, self.device_port)
                        if self.interruptible_sleep(2.0):
                            break
                        close_announcement_dialog()
                        pending_send_friend_life = True
                        session_start_time = time.time()
                        session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
                        last_lives_time = time.time()
                        lives_interval = random.uniform(25 * 60, 35 * 60)
                        detection_group = "PRE_GAME"
                        last_stage = None
                        is_first_game = True
                        continue

                    # When returning to MAINMENU after a completed game, give the lobby time to stabilize
                    if detection_group == "POST_GAME":
                        detection_group = "PRE_GAME"
                        last_stage = None
                        if self.interruptible_sleep(2.5):
                            break
                        continue

                    # Check Auto-Stop Goals before starting next round
                    if self.stop_goal_rounds_enabled and self.session_rounds_played >= self.stop_goal_rounds_target:
                        goal_msg = f"วิ่งครบตามเป้าหมายเซสชัน {self.stop_goal_rounds_target} รอบ"
                        self.log(f"🎯 บรรลุเป้าหมาย: {goal_msg}! กำลังหยุดการทำงานบอทอัตโนมัติ...", "success")
                        uptime_sec = int(time.time() - self.start_time) if self.start_time else 0
                        hours, remainder = divmod(uptime_sec, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        discord_notifier.send_goal_reached(
                            goal_description=goal_msg,
                            uptime=uptime_str,
                            rounds_played=self.rounds_played,
                            total_boxes=self.mystery_boxes,
                            coins_earned=self.session_coins_earned,
                            session_xp=self.session_xp_earned,
                        )
                        break

                    session_boxes_count = self.session_box_counts.get("total", 0)
                    if self.stop_goal_boxes_enabled and session_boxes_count >= self.stop_goal_boxes_target:
                        goal_msg = f"เก็บกล่องปริศนาครบตามเป้าหมายเซสชัน {self.stop_goal_boxes_target} กล่อง"
                        self.log(f"🎯 บรรลุเป้าหมาย: {goal_msg}! กำลังหยุดการทำงานบอทอัตโนมัติ...", "success")
                        uptime_sec = int(time.time() - self.start_time) if self.start_time else 0
                        hours, remainder = divmod(uptime_sec, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        discord_notifier.send_goal_reached(
                            goal_description=goal_msg,
                            uptime=uptime_str,
                            rounds_played=self.rounds_played,
                            total_boxes=self.mystery_boxes,
                            coins_earned=self.session_coins_earned,
                            session_xp=self.session_xp_earned,
                        )
                        break


                    elapsed_hours = (time.time() - self.start_time) / 3600 if self.start_time else 0
                    if self.stop_goal_time_enabled and elapsed_hours >= self.stop_goal_time_hours:
                        goal_msg = f"ปล่อยบอทครบตามเป้าหมาย {self.stop_goal_time_hours:g} ชั่วโมง"
                        self.log(f"🎯 บรรลุเป้าหมาย: {goal_msg}! กำลังหยุดการทำงานบอทอัตโนมัติ...", "success")
                        uptime_sec = int(time.time() - self.start_time) if self.start_time else 0
                        hours, remainder = divmod(uptime_sec, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        discord_notifier.send_goal_reached(
                            goal_description=goal_msg,
                            uptime=uptime_str,
                            rounds_played=self.rounds_played,
                            total_boxes=self.mystery_boxes,
                            coins_earned=self.session_coins_earned,
                            session_xp=self.session_xp_earned,
                        )
                        break

                    is_first_game = False
                    start_game()
                    detection_group = "PRE_GAME"
                    # Wait 2.0s for transition animation from MAINMENU to PURCHASE_ITEM
                    if self.interruptible_sleep(2.0):
                        break

                    # Active verification: เช็คว่าหน้าจอเปลี่ยนหรือยัง ถ้ายังคงเป็น MAINMENU ให้จัดการลองกดซ้ำหรือรีเซ็ตแอป
                    verify_screen = device_capture_screen(target, self.device_port)
                    if verify_screen is not None:
                        current_check = detect_stage(verify_screen, ["MAINMENU", "PURCHASE_ITEM", "GAME_START", "IN_GAME"])
                        if current_check == "MAINMENU":
                            self._mainmenu_play_fail_count += 1
                            self.log(
                                f" หน้าจอยังไม่เปลี่ยนไปหน้าเตรียมตัว (กด Play ไม่ผ่านครั้งที่ {self._mainmenu_play_fail_count}) — กำลังลองแตะปิดป๊อปอัปและกด Play ซ้ำ...",
                                "warning",
                            )
                            try:
                                from actions import safe_device_tap, get_device_context, close_party_run_mode, close_game_settings
                                from config import CLOSE_ANNOUNCEMENT_DIALOG_BUTTON
                                safe_device_tap(*get_device_context(), CLOSE_ANNOUNCEMENT_DIALOG_BUTTON[0], CLOSE_ANNOUNCEMENT_DIALOG_BUTTON[1])
                                time.sleep(0.4)
                                chk_sc = device_capture_screen(target, self.device_port)
                                if chk_sc is not None:
                                    if detect_stage(chk_sc, ["PARTY_RUN"]) == "PARTY_RUN":
                                        close_party_run_mode()
                                    elif detect_stage(chk_sc, ["GAME_SETTINGS"]) == "GAME_SETTINGS":
                                        close_game_settings()
                            except Exception:
                                pass
                            time.sleep(0.5)
                            start_game()
                            if self.interruptible_sleep(1.5):
                                break

                            # Double-check after 2nd tap in this cycle
                            verify_screen2 = device_capture_screen(target, self.device_port)
                            if verify_screen2 is not None:
                                current_check2 = detect_stage(verify_screen2, ["MAINMENU", "PURCHASE_ITEM", "GAME_START", "IN_GAME"])
                                if current_check2 == "MAINMENU":
                                    self._mainmenu_play_fail_count += 1
                        else:
                            self._mainmenu_play_fail_count = 0

                    if self._mainmenu_play_fail_count >= 3:
                        self.log(
                            f" [Auto-Recovery] กดปุ่ม Play หน้าหลักไม่สำเร็จติดต่อกัน {self._mainmenu_play_fail_count} ครั้ง (เกมอาจค้างหรือปุ่มไม่ตอบสนอง) — กำลังบันทึกภาพและรีสตาร์ทแอปเปิดใหม่...",
                            "error",
                        )
                        try:
                            record_game_error(
                                device_serial=target,
                                reason="กดปุ่ม Play หน้าหลักหลายครั้งแล้วเกมไม่เริ่ม หรือหน้าจอค้าง",
                                details=f"กดปุ่ม Play ที่หน้า MAINMENU ไม่สำเร็จติดต่อกัน {self._mainmenu_play_fail_count} ครั้ง",
                                screen_img=verify_screen if verify_screen is not None else device_screen,
                                action_taken="บังคับรีสตาร์ทแอปเกม CookieRun และเปิดใหม่",
                            )
                        except Exception as e:
                            self.log(f" บันทึก error log ไม่สำเร็จ: {e}", "warning")

                        if hasattr(self, "macro_player") and self.macro_player.is_running:
                            self.macro_player.stop()
                        device_reset_app(target, self.device_port)
                        self._mainmenu_play_fail_count = 0
                        if self.interruptible_sleep(2.0):
                            break
                        close_announcement_dialog()
                        last_detected_time = time.time()
                        last_lives_time = time.time()
                        detection_group = "PRE_GAME"
                        last_stage = None
                        is_first_game = True
                        continue

                    last_stage = None

                elif stage == "PURCHASE_ITEM":
                    self._mainmenu_play_fail_count = 0
                    self.log(" Detected Stage: PURCHASE_ITEM", "stage")

                    # ตรวจสอบการตั้งค่าใหม่ก่อนกดซื้อ/เลือกไอเทม
                    self.check_and_apply_settings_update()

                    # Configure top-row items (HP Boost, Item Extension, Double XP)
                    configure_top_row_items(
                        device_screen,
                        use_hp=self.use_hp_boost,
                        use_extension=self.use_item_extension,
                        use_double_xp=self.use_double_xp,
                        log_fn=self.log
                    )

                    # Smart Fast Start check
                    if self.use_fast_start:
                        stock_fs = extract_item_stock(device_screen, "fast_start")
                        if stock_fs <= self.fast_start_min_stock:
                            self.log(f" Fast Start ในคลัง ({stock_fs} ชิ้น <= เกณฑ์ {self.fast_start_min_stock}) -> กำลังซื้อเพิ่ม...", "info")
                            purchase_fast_start()
                        else:
                            self.log(f" Fast Start ในคลังมี {stock_fs} ชิ้น (มากกว่าเกณฑ์ {self.fast_start_min_stock}) -> ข้ามการซื้อเพื่อประหยัดเหรียญ", "info")

                    # Smart Cookie Relay check
                    if self.use_cookie_relay:
                        stock_cr = extract_item_stock(device_screen, "cookie_relay")
                        if stock_cr <= self.cookie_relay_min_stock:
                            self.log(f" Cookie Relay ในคลัง ({stock_cr} ชิ้น <= เกณฑ์ {self.cookie_relay_min_stock}) -> กำลังซื้อเพิ่ม...", "info")
                            purchase_cookie_relay()
                        else:
                            self.log(f" Cookie Relay ในคลังมี {stock_cr} ชิ้น (มากกว่าเกณฑ์ {self.cookie_relay_min_stock}) -> ข้ามการซื้อเพื่อประหยัดเหรียญ", "info")

                    if self.use_desired_random_boost:
                        desired_boost_template, desired_boost_name = self.get_desired_boost_info()
                        if desired_boost_template:
                            self.log(f" Rolling boost for: {desired_boost_name}...")
                            purchase_desired_random_boost(desired_boost_template, desired_boost_name, self.desired_boost_id, log_fn=self.log)
                    play_game()
                    detection_group = "IN_GAME"
                    self._last_auto_action_time = time.time() + 1.0

                    self._flush_pending_round_summary()
                    self.rounds_played += 1
                    self.session_rounds_played += 1
                    self.current_round_start_time = time.time()
                    self.current_round_recorded = False
                    self.current_round_boxes = []
                    self.current_round_mystery_box_handled = False
                    self.current_round_screen = None
                    self.pending_round_summary = None
                    self.early_exit_triggered = False
                    self._last_box_check_time = 0.0
                    self._box_target_consecutive_hits = 0
                    self.log(f" Round {self.rounds_played} started!", "success")
                    if self.interruptible_sleep(0.2):
                        break
                    last_stage = None

                elif stage == "GAME_START":
                    self._mainmenu_play_fail_count = 0
                    self._purchase_item_fail_count = 0
                    self.log(" Detected Stage: GAME_START", "stage")
                    if self.use_fast_start:
                        using_fast_start()
                    detection_group = "IN_GAME"
                    self._last_auto_action_time = time.time() + 1.0

                    try:
                        from macro_recorder import macro_recorder_manager
                        rec = macro_recorder_manager.get_recorder(target)
                        if rec.status == "ARMED":
                            if rec.trigger_in_game_start():
                                self.log(" [Macro Record] เข้าสู่หน้าเกมวิ่งแล้ว! เริ่มจับเวลาและบันทึกมาโคร (t=0.00s)...", "success")
                    except Exception:
                        pass

                    if self.macro_enabled and self.selected_macro_id and not self.macro_player.is_running:
                        try:
                            from macro_manager import get_macro
                            mdata = get_macro(self.selected_macro_id)
                            if mdata:
                                time.sleep(1.0)  # Wait for START! banner to clear so cookie is running
                                self.log(f"[Macro] เริ่มเล่นตามมาโคร: {mdata.get('name', self.selected_macro_id)}", "info")
                                self.macro_player.start(mdata)
                        except Exception as e:
                            self.log(f" ไม่สามารถเริ่มมาโคร: {e}", "warning")

                elif stage == "GAME_RELAY":
                    self.log(" Detected Stage: GAME_RELAY (Cookie Relay Triggered)", "stage")
                    if self.use_cookie_relay:
                        using_cookie_relay()
                    detection_group = "IN_GAME"
                    self._last_auto_action_time = time.time() + 1.0
                    if self.macro_enabled and self.selected_macro_id:
                        try:
                            from macro_manager import get_macro
                            mdata = get_macro(self.selected_macro_id)
                            if mdata:
                                self.log(f" [Macro] ผลัดคุกกี้ - เล่นตามมาโครต่อ", "info")
                                self.macro_player.start(mdata)
                        except Exception as e:
                            pass

                elif stage == "GAME_COMPLETE":
                    if hasattr(self, "macro_player") and self.macro_player.is_running:
                        self.macro_player.stop()

                    # Auto save macro if recording was in progress
                    try:
                        from macro_recorder import macro_recorder_manager
                        rec = macro_recorder_manager.get_recorder(target)
                        if rec.status == "RECORDING":
                            saved = rec.stop_and_save()
                            if saved:
                                self.log(f" [Macro Record] จบเกมแล้ว! บันทึกมาโครลงไฟล์ JSON สำเร็จ: {saved.get('name')} ({len(saved.get('actions', []))} แอ็กชัน)", "success")
                    except Exception:
                        pass

                    self.log(" ตรวจพบหน้าจอสรุปผล (Result Screen) — กำลังรอตัวเลขคะแนนและเหรียญขึ้นครบ...", "stage")

                    # ตรวจสอบการตั้งค่าใหม่เมื่อจบรอบ
                    self.check_and_apply_settings_update()

                    # 1. รอแอนิเมชันหน้าจอสรุปผลเปิดสมบูรณ์ และแตะข้ามแอนิเมชันคะแนน/โบนัส
                    time.sleep(random.uniform(0.8, 1.2))
                    device_tap(target, self.device_port, 640, 260)
                    time.sleep(random.uniform(0.8, 1.2))
                    device_tap(target, self.device_port, 640, 260)
                    time.sleep(0.6)

                    # 2. จับภาพหน้าจอสรุปผลที่สมบูรณ์
                    device_screen = device_capture_screen(target, self.device_port)

                    # 3. สกัดคะแนน, เหรียญ, EXP และกล่องปริศนา
                    round_score = extract_result_score(device_screen) if device_screen is not None else 0
                    round_coins = extract_result_coins(device_screen) if device_screen is not None else 0
                    round_xp = extract_result_xp(device_screen) if device_screen is not None else 0
                    result_badge_boxes = detect_result_screen_mystery_box(device_screen) if device_screen is not None else []

                    # หากตัวเลขยังไม่ขึ้น ลองรออีกครั้งและแคปใหม่
                    if round_coins == 0 and device_screen is not None:
                        device_tap(target, self.device_port, 640, 260)
                        time.sleep(0.8)
                        fresh_screen = device_capture_screen(target, self.device_port)
                        if fresh_screen is not None:
                            device_screen = fresh_screen
                            round_score = extract_result_score(device_screen)
                            round_coins = extract_result_coins(device_screen)
                            round_xp = extract_result_xp(device_screen)
                            result_badge_boxes = detect_result_screen_mystery_box(device_screen)

                    # 4. [ขั้นตอนบันทึก - Save Screenshot] บันทึกไฟล์ภาพลง screenshots/ และ Web Dashboard
                    saved_img_path = None
                    if device_screen is not None:
                        self.current_round_screen = device_screen.copy()
                        try:
                            os.makedirs("screenshots", exist_ok=True)
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            saved_img_path = f"screenshots/round_{self.rounds_played}_{ts}.png"
                            cv2.imwrite(saved_img_path, device_screen)

                            _, buf = cv2.imencode(".jpg", device_screen, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            self.round_screenshots[self.rounds_played] = buf.tobytes()
                            if len(self.round_screenshots) > 50:
                                oldest_key = min(self.round_screenshots.keys())
                                del self.round_screenshots[oldest_key]
                        except Exception as err:
                            self.log(f" ไม่สามารถบันทึกภาพหน้าจอ: {err}", "warning")

                    # 5. [ขั้นตอนบันทึก - Record Stats] อัปเดตสถิติและประวัติการเล่น
                    if round_coins > 0:
                        self.session_coins_earned += round_coins
                        self.lifetime_coins_earned += round_coins
                        self.last_round_coins = round_coins
                    if round_xp > 0:
                        self.session_xp_earned += round_xp
                        self.lifetime_xp_earned += round_xp
                        self.last_round_xp = round_xp

                    # กำหนดกล่องปริศนาประจำรอบ
                    if self.current_round_boxes:
                        round_boxes = list(self.current_round_boxes)
                    elif result_badge_boxes:
                        round_boxes = ["wood"]
                        self.current_round_boxes = list(round_boxes)
                        if not self.current_round_mystery_box_handled:
                            for b in round_boxes:
                                self.box_counts[b] = self.box_counts.get(b, 0) + 1
                                self.session_box_counts[b] = self.session_box_counts.get(b, 0) + 1
                            self.box_counts["total"] += len(round_boxes)
                            self.session_box_counts["total"] += len(round_boxes)
                            self.mystery_boxes = self.box_counts["total"]
                    else:
                        round_boxes = []

                    dur_sec = int(time.time() - self.current_round_start_time) if self.current_round_start_time else 0
                    dur_str = f"{dur_sec // 60}m {dur_sec % 60}s" if dur_sec >= 60 else f"{dur_sec}s"

                    # อัปเดตหรือเพิ่มประวัติรอบ
                    if self.round_history and self.round_history[0].get("round") == self.rounds_played:
                        entry = self.round_history[0]
                        entry["score"] = round_score
                        entry["coins"] = round_coins
                        entry["xp"] = round_xp
                        entry["duration"] = dur_str
                        if round_boxes:
                            entry["boxes"] = round_boxes
                            entry["box_count"] = len(round_boxes)
                        if saved_img_path:
                            entry["screenshot"] = saved_img_path
                            entry["has_screenshot"] = True
                        self.current_round_recorded = True
                        save_round_history_to_file(self.device_serial, list(self.round_history), new_entry=entry)
                        if self.session_round_history and self.session_round_history[0].get("round") == self.rounds_played:
                            self.session_round_history[0].update(entry)
                    elif not self.current_round_recorded:
                        item = {
                            "round": self.rounds_played,
                            "session_round": self.session_rounds_played,
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "duration": dur_str,
                            "score": round_score,
                            "coins": round_coins,
                            "xp": round_xp,
                            "boxes": round_boxes,
                            "box_count": len(round_boxes),
                            "has_screenshot": True,
                            "screenshot": saved_img_path or "",
                        }
                        self.round_history.appendleft(item)
                        self.session_round_history.appendleft(item)
                        self.current_round_recorded = True
                        save_round_history_to_file(self.device_serial, list(self.round_history), new_entry=item)

                    score_log = f"คะแนน: {round_score:,} | " if round_score > 0 else ""
                    xp_log = f" | +{round_xp:,} EXP" if round_xp > 0 else ""
                    box_log = f" |  ได้รับ {len(round_boxes)} กล่อง" if round_boxes else ""
                    self.log(f" [บันทึกข้อมูลสำเร็จ] รอบที่ #{self.rounds_played}: {score_log}+{round_coins:,} 🪙{xp_log}{box_log}", "success")
                    if saved_img_path:
                        self.log(f"    บันทึกรูปภาพผลลัพธ์: {saved_img_path}", "info")
                    self.log(f"    บันทึกประวัติการเล่นลง: history/ (รอบที่ #{self.rounds_played})", "info")

                    # เตรียมข้อมูลสรุปรอบสำหรับ Discord ไว้ก่อน
                    # หน่วงเวลาส่งเพื่อรอตรวจจับหน้าต่าง MYSTERY_BOX (หน้าเปิดกล่องปริศนา) ในขั้นตอนถัดไป
                    # เพื่อให้ Discord ได้ข้อมูลเกรดกล่องจริงและรูปหน้าเปิดกล่องแบบเดียวกับหน้าเว็บ
                    self.pending_round_summary = {
                        "round_num": self.rounds_played,
                        "duration_str": dur_str,
                        "duration_sec": dur_sec,
                        "coins_earned": round_coins,
                        "session_coins": self.session_coins_earned,
                        "xp_earned": round_xp,
                        "session_xp": self.session_xp_earned,
                        "boxes": round_boxes,
                        "session_rounds": self.session_rounds_played,
                        "session_boxes": dict(self.session_box_counts),
                        "device_name": self.get_device_model_label(),
                        "screen_img": device_screen,
                        "created_at": time.time(),
                    }

                    # 6. หน่วงเวลาให้ผู้ใช้ได้ดูผลลัพธ์ทั้งหมด (Result Card) ให้ชัดเจนก่อนกด OK
                    self.log(" บันทึกผลลัพธ์เรียบร้อย — กำลังแสดงหน้า Result ให้ดูทั้งหมดก่อนกด OK...", "info")
                    if self.interruptible_sleep(random.uniform(2.5, 3.5)):
                        break

                    # 7. กดปุ่ม OK เพื่อดำเนินการต่อ
                    self.log(" กดปุ่ม OK เพื่อดำเนินการต่อ", "info")
                    complete_finish(device_screen)
                    detection_group = "POST_GAME"
                    last_stage = None

                    # 7. เคลียร์แรม (RAM) ทุกๆ รอบที่ทำเสร็จ
                    clear_system_memory(target, self.device_port, log_func=self.log)

                elif stage == "MYSTERY_BOX":
                    if self.current_round_mystery_box_handled:
                        # ได้ตรวจจับและนับเกรดกล่องในรอบนี้ไปแล้ว กดรับและข้ามการสแกนซ้ำ
                        accept_mystery_box()
                        if self.interruptible_sleep(1.0):
                            break
                        detection_group = "POST_GAME"
                        last_stage = None
                        continue

                    # รอแอนิเมชันเปิดกล่องนิ่ง
                    time.sleep(random.uniform(0.8, 1.2))
                    fresh_mb_screen = device_capture_screen(target, self.device_port)
                    if fresh_mb_screen is not None:
                        device_screen = fresh_mb_screen

                    # ตรวจจับเกรดกล่องที่แท้จริง
                    detected_grades = detect_mystery_box_grades(device_screen)
                    if not detected_grades:
                        # Fallback: หน้า MYSTERY_BOX มีกล่องอย่างน้อย 1 กล่อง
                        detected_grades = ["wood"]

                    box_names_th = {
                        "wood": " ไม้",
                        "silver": " เงิน",
                        "gold": " ทอง",
                        "rainbow": " รุ้ง",
                    }
                    grade_str = ", ".join([box_names_th.get(g, g) for g in detected_grades])

                    # หากก่อนหน้านี้ GAME_COMPLETE นับเป็น wood ไปก่อน ให้หักลบออกเพื่อไม่ให้ยอดเบิ้ล
                    if self.current_round_boxes and not self.current_round_mystery_box_handled:
                        for old_b in self.current_round_boxes:
                            if old_b in self.box_counts and self.box_counts[old_b] > 0:
                                self.box_counts[old_b] -= 1
                                self.box_counts["total"] = max(0, self.box_counts["total"] - 1)
                            if old_b in self.session_box_counts and self.session_box_counts[old_b] > 0:
                                self.session_box_counts[old_b] -= 1
                                self.session_box_counts["total"] = max(0, self.session_box_counts["total"] - 1)

                    self.current_round_boxes = list(detected_grades)
                    self.current_round_mystery_box_handled = True

                    for g in detected_grades:
                        self.box_counts[g] = self.box_counts.get(g, 0) + 1
                        self.session_box_counts[g] = self.session_box_counts.get(g, 0) + 1
                    self.box_counts["total"] += len(detected_grades)
                    self.session_box_counts["total"] += len(detected_grades)
                    self.mystery_boxes = self.box_counts["total"]

                    dur_sec = int(time.time() - self.current_round_start_time) if self.current_round_start_time else 0
                    dur_str = f"{dur_sec // 60}m {dur_sec % 60}s" if dur_sec >= 60 else f"{dur_sec}s"

                    if device_screen is not None:
                        try:
                            _, buf = cv2.imencode(".jpg", device_screen, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            self.round_screenshots[self.rounds_played] = buf.tobytes()
                            if len(self.round_screenshots) > 50:
                                oldest_key = min(self.round_screenshots.keys())
                                del self.round_screenshots[oldest_key]
                        except Exception:
                            pass

                    # อัปเดตข้อมูลกล่องในรอบปัจจุบัน
                    if self.round_history and self.round_history[0].get("round") == self.rounds_played:
                        self.round_history[0]["boxes"] = list(detected_grades)
                        self.round_history[0]["box_count"] = len(detected_grades)
                        save_round_history_to_file(self.device_serial, list(self.round_history), new_entry=self.round_history[0])
                        if self.session_round_history and self.session_round_history[0].get("round") == self.rounds_played:
                            self.session_round_history[0]["boxes"] = list(detected_grades)
                            self.session_round_history[0]["box_count"] = len(detected_grades)
                    else:
                        round_coins = extract_result_coins(device_screen) if device_screen is not None else 0
                        round_xp = extract_result_xp(device_screen) if device_screen is not None else 0
                        if round_coins > 0:
                            self.session_coins_earned += round_coins
                            self.lifetime_coins_earned += round_coins
                            self.last_round_coins = round_coins
                        if round_xp > 0:
                            self.session_xp_earned += round_xp
                            self.lifetime_xp_earned += round_xp
                            self.last_round_xp = round_xp

                        item = {
                            "round": self.rounds_played,
                            "session_round": self.session_rounds_played,
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "duration": dur_str,
                            "coins": round_coins,
                            "xp": round_xp,
                            "boxes": list(detected_grades),
                            "box_count": len(detected_grades),
                            "has_screenshot": True,
                            "screenshot": "",
                        }
                        self.round_history.appendleft(item)
                        self.session_round_history.appendleft(item)
                        self.current_round_recorded = True
                        save_round_history_to_file(self.device_serial, list(self.round_history), new_entry=item)

                    self.log(f" ได้รับกล่องปริศนา: [{grade_str}] (รวมทั้งหมด: {self.mystery_boxes} กล่อง)", "success")

                    # ส่งการแจ้งเตือนสรุปผลรอบเข้า Discord โดยใช้เกรดกล่องจริงและภาพหน้าเปิดกล่อง Mystery Box
                    if self.pending_round_summary:
                        self.pending_round_summary["boxes"] = list(detected_grades)
                        if device_screen is not None:
                            self.pending_round_summary["screen_img"] = device_screen
                        self._flush_pending_round_summary()
                    elif discord_notifier.notify_boxes:
                        discord_notifier.send_box_drop(
                            self.rounds_played,
                            detected_grades,
                            self.box_counts,
                            coins_earned=self.last_round_coins,
                            session_coins=self.session_coins_earned,
                            xp_earned=self.last_round_xp,
                            session_xp=self.session_xp_earned,
                            screen_img=device_screen
                        )

                    accept_mystery_box()
                    if self.interruptible_sleep(2.0):
                        break
                    detection_group = "POST_GAME"
                    last_stage = None

                elif stage == "CONGRATULATIONS":
                    self.log(" Detected Stage: CONGRATULATIONS", "stage")
                    accept_congratulations()
                    detection_group = "POST_GAME"
                    last_stage = None

                elif stage == "SET_REWARD":
                    self.log(" Detected Stage: SET_REWARD (You received a set reward!) — กดยืนยันรับรางวัล...", "success")
                    accept_set_reward()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "PREVIOUS_RESULTS":
                    self.log("Detected Stage: PREVIOUS_RESULTS (You have unreviewed game results) — กดยืนยันเพื่อไปหน้าสรุปคะแนน...", "info")
                    accept_previous_results()
                    detection_group = "POST_GAME"
                    last_stage = None

                elif stage == "LEVEL_UP":
                    self.log("⬆ Detected Stage: LEVEL_UP (Confirming immediately)", "success")
                    accept_level_up()
                    detection_group = "POST_GAME"
                    last_stage = None

                elif stage == "DAILY_CHECKIN":
                    self.log(" Detected Stage: DAILY_CHECKIN", "stage")
                    accept_daily_checkin()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "DAILY_CHECKIN_BOOST_SET":
                    self.log(" Detected Stage: DAILY_CHECKIN_BOOST_SET", "stage")
                    accept_daily_checkin_boost_set()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "DAILY_TREASURE":
                    self.log(" Detected Stage: DAILY_TREASURE", "stage")
                    accept_daily_treasure()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "DAILY_NEW":
                    self.log(" Detected Stage: DAILY_NEW", "stage")
                    accept_daily_new()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "ENTER_LEAGUE":
                    self.log(" Detected Stage: ENTER_LEAGUE", "stage")
                    accept_enter_league()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "LEAGUE_RESULTS":
                    self.log(" Detected Stage: LEAGUE_RESULTS", "stage")
                    accept_league_results()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "PREVIOUS_RANK_RESULTS":
                    self.log(" Detected Stage: PREVIOUS_RANK_RESULTS", "stage")
                    accept_previous_rank_results()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "OVERTAKE_BREAK_SCORE":
                    self.log(" Detected Stage: OVERTAKE_BREAK_SCORE", "stage")
                    accept_overtake_break_score()
                    detection_group = "POST_GAME"
                    last_stage = None

                elif stage == "TOO_MANY_TREASURES":
                    self.log(" Detected Stage: TOO_MANY_TREASURES", "warning")
                    accept_too_many_treasures()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "RELIC_COMPLETE":
                    self.log(" Detected Stage: RELIC_COMPLETE", "stage")
                    open_relic_complete()
                    detection_group = "PRE_GAME"

                elif stage == "RELIC_CLAIM":
                    self.log(" Detected Stage: RELIC_CLAIM", "stage")
                    accept_relic_claim()
                    detection_group = "PRE_GAME"

                elif stage == "GAME_SETTINGS":
                    self.log(" Detected Stage: GAME_SETTINGS — closing settings...", "stage")
                    close_game_settings()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "PARTY_RUN":
                    self.log(" Detected Stage: PARTY_RUN — closing party run mode...", "stage")
                    close_party_run_mode()
                    detection_group = "PRE_GAME"
                    last_stage = None

                elif stage == "ANTI_BOT":
                    self.log(" ตรวจพบหน้าจอ ANTI_BOT (กันบอท) — กำลังวิเคราะห์และแก้แคปซ่าอัตโนมัติ...", "warning")
                    discord_notifier.send_anti_bot_alert("ANTI_BOT", screen_img=device_screen)
                    handle_anti_bot(device_screen)

                    # ตรวจสอบผลลัพธ์ว่าแก้สำเร็จหรือไม่
                    time.sleep(2.5)
                    verify_screen = device_capture_screen(target, self.device_port)
                    still_anti_bot = False
                    if verify_screen is not None:
                        post_stage = detect_stage(verify_screen)
                        still_anti_bot = (post_stage == "ANTI_BOT")

                    now_str = datetime.now().strftime("%H:%M:%S")
                    self.captcha_stats["total_attempts"] += 1
                    self.captcha_stats["last_attempt_time"] = now_str

                    if not still_anti_bot:
                        self.captcha_stats["success_count"] += 1
                        self.captcha_stats["last_result"] = "success"
                        rate = (self.captcha_stats["success_count"] / self.captcha_stats["total_attempts"]) * 100
                        self.log(f" แก้ไขแคปซ่ากันบอทสำเร็จ! (อัตราสำเร็จ: {rate:.1f}% | {self.captcha_stats['success_count']}/{self.captcha_stats['total_attempts']} ครั้ง)", "success")
                    else:
                        self.captcha_stats["fail_count"] += 1
                        self.captcha_stats["last_result"] = "fail"
                        rate = (self.captcha_stats["success_count"] / self.captcha_stats["total_attempts"]) * 100
                        self.log(f" แก้ไขแคปซ่าไม่สำเร็จ (หน้าจอยังคงติดกันบอท) (อัตราสำเร็จ: {rate:.1f}% | {self.captcha_stats['success_count']}/{self.captcha_stats['total_attempts']} ครั้ง)", "error")

                    save_device_captcha_stats(self.device_serial, self.captcha_stats)
                    last_stage = None

                elif stage == "CONNECTION_LOST":
                    self._connection_lost_retries = getattr(self, "_connection_lost_retries", 0) + 1
                    if self._connection_lost_retries <= 2:
                        self.log(f" ตรวจพบหลุดการเชื่อมต่อ (CONNECTION_LOST) — กำลังกดลองใหม่ (Reconnect ครั้งที่ {self._connection_lost_retries}/2)...", "warning")
                        handle_connection_lost()
                        last_stage = None
                        if self.interruptible_sleep(1.0):
                            break
                    else:
                        self.log(" หลุดการเชื่อมต่อซ้ำซ้อนเกิน 2 ครั้ง — กำลังรีสตาร์ทแอปเกม...", "error")
                        discord_notifier.send_connection_lost(self.device_ip, self.device_port)
                        device_reset_app(target, self.device_port)
                        if self.interruptible_sleep(2.0):
                            break
                        close_announcement_dialog()
                        session_start_time = time.time()
                        session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
                        last_lives_time = time.time()
                        lives_interval = random.uniform(25 * 60, 35 * 60)
                        detection_group = "PRE_GAME"
                        last_stage = None
                        is_first_game = True
                        self._connection_lost_retries = 0

                elif stage == "INACTIVE":
                    self.log("💤 Detected Stage: INACTIVE — reconnecting...", "warning")
                    handle_inactive()
                    last_stage = None

                if self.interruptible_sleep(0.25):
                    break

        except Exception as e:
            self.log(f" Bot runtime error: {e}", "error")
        finally:
            with self.lock:
                self.is_running = False
                self.current_stage = "IDLE"
            self.log(" Bot execution ended", "info")


_log_file_lock = threading.Lock()

def write_log_to_file(log_entry: dict):
    try:
        from path_utils import get_logs_dir
        logs_dir = get_logs_dir()
        date_str = datetime.now().strftime("%Y-%m-%d")
        filepath = os.path.join(logs_dir, f"bot_log_{date_str}.txt")
        ts = log_entry.get("timestamp") or log_entry.get("time") or datetime.now().strftime("%H:%M:%S")
        lvl = str(log_entry.get("level") or "INFO").upper()
        target = log_entry.get("target") or log_entry.get("device") or ""
        dev_tag = f" [{target}]" if target else ""
        msg = str(log_entry.get("message") or "").strip()
        line = f"[{date_str} {ts}] [{lvl}]{dev_tag} {msg}\n"
        with _log_file_lock:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception:
        pass


class EngineManager:
    """Manages multiple BotEngine instances mapped to different devices/emulators."""
    def __init__(self):
        self.engines: Dict[str, BotEngine] = {}
        self.lock = threading.Lock()
        self.global_logs: deque = deque(maxlen=500)
        self.global_ws_subscribers: List[asyncio.Queue] = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def record_and_broadcast_log(self, log_entry: dict):
        with self.lock:
            self.global_logs.append(log_entry)
        write_log_to_file(log_entry)
        if self.loop and self.global_ws_subscribers:
            for q in list(self.global_ws_subscribers):
                try:
                    self.loop.call_soon_threadsafe(q.put_nowait, log_entry)
                except Exception:
                    pass

    def get_or_create_engine(self, serial: str) -> BotEngine:
        with self.lock:
            s = str(serial).strip()
            if s not in self.engines:
                eng = BotEngine(device_serial=s)
                eng.loop = self.loop
                self.engines[s] = eng
            else:
                if self.loop and not self.engines[s].loop:
                    self.engines[s].loop = self.loop
            return self.engines[s]

    def get_engine(self, serial: str) -> Optional[BotEngine]:
        with self.lock:
            return self.engines.get(str(serial).strip())

    def get_all_engines(self) -> Dict[str, BotEngine]:
        with self.lock:
            return dict(self.engines)

engine_manager = EngineManager()
# Global default instance for backwards compatibility
bot_engine = engine_manager.get_or_create_engine(f"{config.DEVICE_IP}:{config.DEVICE_PORT}")


def get_engine_for_device(device_serial: str) -> Optional[BotEngine]:
    return engine_manager.get_or_create_engine(device_serial)
