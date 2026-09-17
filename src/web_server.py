import asyncio
import collections
import io
import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

import cv2
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from pydantic import BaseModel

import config
from adb import (
    device_capture_screen,
    device_check_connection,
    device_reset_app,
    device_tap,
    get_adb_path,
    scan_adb_devices,
    clear_system_memory,
)
from bot_engine import (
    BOOST_OPTIONS,
    BotEngine,
    _in_bot_log,
    bot_engine,
    engine_manager,
    get_device_settings_path,
)
from discord_notifier import discord_notifier
from scrcpy_streamer import stream_manager
import sys
import re
from datetime import datetime
import socket

def silence_windows_proactor_connection_lost():
    """Fix Windows asyncio Proactor [WinError 10054] bug when clients disconnect/refresh."""
    if sys.platform != "win32":
        return
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport

        _orig_call_conn_lost = _ProactorBasePipeTransport._call_connection_lost

        def _safe_call_connection_lost(self, exc):
            if self._called_connection_lost:
                return
            try:
                self._protocol.connection_lost(exc)
            finally:
                if hasattr(self, "_sock") and self._sock is not None:
                    if hasattr(self._sock, "shutdown") and self._sock.fileno() != -1:
                        try:
                            self._sock.shutdown(socket.SHUT_RDWR)
                        except (ConnectionResetError, OSError):
                            pass
                    try:
                        self._sock.close()
                    except (ConnectionResetError, OSError):
                        pass
                    self._sock = None
                server = getattr(self, "_server", None)
                if server is not None:
                    try:
                        server._detach(self)
                    except Exception:
                        pass
                    self._server = None
                self._called_connection_lost = True

        _ProactorBasePipeTransport._call_connection_lost = _safe_call_connection_lost
    except Exception:
        pass

silence_windows_proactor_connection_lost()

# Heart Farmer (imported lazily to avoid circular deps)
try:
    from heart_farmer import HeartFarmer as _HeartFarmer
except Exception as _hf_err:
    print(f"[WebServer] Note: heart_farmer not loaded: {_hf_err}", flush=True)
    _HeartFarmer = None

try:
    from friend_cleaner import friend_cleaner_scheduler, clean_level1_friends
except Exception as _fc_err:
    print(f"[WebServer] Note: friend_cleaner not loaded: {_fc_err}", flush=True)
    friend_cleaner_scheduler = None
    clean_level1_friends = None


_farmer_threads: Dict[str, threading.Thread] = {}
_farmer_instances: Dict[str, Any] = {}


def _start_heart_farmer(device: str, invite_url: str) -> dict:
    global _HeartFarmer
    try:
        import heart_farmer
        import importlib
        importlib.reload(heart_farmer)
        _HeartFarmer = heart_farmer.HeartFarmer
    except Exception as e:
        print(f"[WebServer] Error reloading heart_farmer: {e}", flush=True)

    if _HeartFarmer is None:
        return {"success": False, "message": "HeartFarmer module is not available"}
    existing_t = _farmer_threads.get(device)
    existing_i = _farmer_instances.get(device)
    if existing_t and existing_t.is_alive() and existing_i and not existing_i.stopped:
        return {"success": False, "message": f"บอทปั้มหัวใจกำลังทำงานอยู่แล้วบนจอ {device}"}

    try:
        from adb import ensure_adb_root
        ensure_adb_root(device)
    except Exception:
        pass

    farmer = _HeartFarmer(device=device, invite_url=invite_url, max_rounds=0)
    t = threading.Thread(target=farmer.run, name=f"HeartFarmer-{device}", daemon=True)
    t.start()
    _farmer_threads[device] = t
    _farmer_instances[device] = farmer
    bot_engine.log(f"[FARMER] เริ่มระบบปั้มหัวใจบนจอ {device} (ลิงก์: {invite_url})", "farmer")
    print(f"[WebServer] HeartFarmer started on {device} (invite={invite_url})", flush=True)
    return {"success": True, "message": f"เริ่มระบบปั้มหัวใจบนจอ {device} เรียบร้อยแล้ว"}


def _stop_heart_farmer(device: str) -> dict:
    farmer = _farmer_instances.get(device)
    if farmer:
        farmer.stop()
    # Force stop game app immediately on emulator so actions halt right now
    try:
        from adb import get_adb_path
        import subprocess
        for pkg in ["com.devsisters.crg", "com.linecorp.LGCOOKIE"]:
            subprocess.run([adb_path, "-s", device, "shell", "am", "force-stop", pkg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except Exception:
        pass
    bot_engine.log(f"[FARMER] สั่งหยุดระบบปั้มหัวใจบนจอ {device} และปิดเกมทันที", "farmer")
    print(f"[WebServer] HeartFarmer stopped immediately on {device}", flush=True)
    return {"success": True, "message": f"สั่งหยุดระบบปั้มหัวใจบนจอ {device} ทันทีเรียบร้อยแล้ว"}

app = FastAPI(title="CookieRun Classic Bot Web Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from path_utils import get_project_root
_project_root = get_project_root()

templates_path = os.path.join(os.path.dirname(__file__), "templates")
if os.path.isdir(templates_path):
    app.mount("/templates", StaticFiles(directory=templates_path), name="templates")

screenshots_path = os.path.join(_project_root, "screenshots")
if os.path.isdir(screenshots_path):
    app.mount("/screenshots", StaticFiles(directory=screenshots_path), name="screenshots")

frontend_dist_path = os.path.join(_project_root, "frontend", "dist")
frontend_assets_path = os.path.join(frontend_dist_path, "assets")
if os.path.isdir(frontend_assets_path):
    app.mount("/assets", StaticFiles(directory=frontend_assets_path), name="assets")

frontend_illustrations_path = os.path.join(frontend_dist_path, "illustrations")
if os.path.isdir(frontend_illustrations_path):
    app.mount("/illustrations", StaticFiles(directory=frontend_illustrations_path), name="illustrations")

frontend_templates_path = os.path.join(frontend_dist_path, "templates")
if os.path.isdir(frontend_templates_path):
    app.mount("/templates", StaticFiles(directory=frontend_templates_path), name="templates")

_bot_icon_path = os.path.join(os.path.dirname(__file__), "bot_icon.ico")

@app.get("/bot_icon.ico", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    if os.path.exists(_bot_icon_path):
        with open(_bot_icon_path, "rb") as f:
            return Response(content=f.read(), media_type="image/x-icon")
    return Response(status_code=404)


class StartBotRequest(BaseModel):
    device: Optional[str] = None
    device_serial: Optional[str] = None
    device_ip: Optional[str] = None
    device_port: Optional[int] = None
    use_hp_boost: Optional[bool] = None
    use_item_extension: Optional[bool] = None
    use_double_xp: Optional[bool] = None
    use_fast_start: Optional[bool] = None
    fast_start_min_stock: Optional[int] = None
    use_cookie_relay: Optional[bool] = None
    cookie_relay_min_stock: Optional[int] = None
    use_desired_random_boost: Optional[bool] = None
    desired_boost_id: Optional[str] = None
    detect_relic: Optional[bool] = None
    send_friend_lives: Optional[bool] = None
    heart_farmer_enabled: Optional[bool] = None
    heart_farmer_device: Optional[str] = None
    heart_farmer_devices: Optional[List[str]] = None
    heart_farmer_invite: Optional[str] = None
    stop_goal_rounds_enabled: Optional[bool] = None
    stop_goal_rounds_target: Optional[int] = None
    early_exit_boxes_enabled: Optional[bool] = None
    early_exit_boxes_target: Optional[int] = None
    stop_goal_time_enabled: Optional[bool] = None
    stop_goal_time_hours: Optional[float] = None
    auto_action_enabled: Optional[bool] = None
    auto_action_mode: Optional[str] = None
    auto_action_interval: Optional[float] = None
    macro_enabled: Optional[bool] = None
    selected_macro_id: Optional[str] = None


BotSettings = StartBotRequest


class StopBotRequest(BaseModel):
    device: Optional[str] = None
    device_serial: Optional[str] = None


class FarmerStartRequest(BaseModel):
    device: Optional[str] = None
    devices: Optional[List[str]] = None
    invite_url: Optional[str] = "ใส่ลิงก์เชิญเพื่อนของคุณ"


class FarmerStopRequest(BaseModel):
    device: Optional[str] = None
    devices: Optional[List[str]] = None


class FriendCleanerStartRequest(BaseModel):
    device: Optional[str] = None
    devices: Optional[List[str]] = None
    interval_minutes: int = 30
    run_immediately: bool = True


class FriendCleanerRunOnceRequest(BaseModel):
    device: Optional[str] = None



class ConnectionTestRequest(BaseModel):
    device_serial: Optional[str] = None
    device_ip: str = "127.0.0.1"
    device_port: int = 7555


class TapRequest(BaseModel):
    x: int
    y: int
    device: Optional[str] = None
    device_serial: Optional[str] = None
    device_ip: Optional[str] = None
    device_port: Optional[int] = None


class DiscordSettingsRequest(BaseModel):
    webhook_url: str = ""
    enabled: bool = False
    notify_boxes: bool = True
    notify_rounds: bool = True
    notify_antibot: bool = True
    notify_status: bool = True
    attach_screenshot: bool = True


class DiscordTestRequest(BaseModel):
    webhook_url: str = ""


SETTINGS_DIR = os.path.join(_project_root, "settings")
os.makedirs(SETTINGS_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "bot_settings.json")
LEGACY_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "bot_settings.json")
DEFAULT_BOT_SETTINGS = {
    "device_serial": "127.0.0.1:7555",
    "device_ip": "127.0.0.1",
    "device_port": 7555,
    "use_hp_boost": False,
    "use_item_extension": False,
    "use_double_xp": False,
    "use_fast_start": False,
    "fast_start_min_stock": 10,
    "use_cookie_relay": False,
    "cookie_relay_min_stock": 10,
    "use_desired_random_boost": False,
    "desired_boost_id": "double_coins",
    "detect_relic": True,
    "send_friend_lives": True,
    "heart_farmer_enabled": False,
    "heart_farmer_device": "emulator-5562",
    "heart_farmer_invite": "ใส่ลิงก์เชิญเพื่อนของคุณ",
    "stop_goal_rounds_enabled": False,
    "stop_goal_rounds_target": 50,
    "stop_goal_time_enabled": False,
    "stop_goal_time_hours": 2.0,
    "early_exit_boxes_enabled": True,
    "early_exit_boxes_target": 2,
    "auto_action_enabled": False,
    "auto_action_mode": "both",
    "auto_action_interval": 1.5,
    "macro_enabled": False,
    "selected_macro_id": "preset_basic_run",
}


def get_engine_for_device(device_serial: Optional[str] = None) -> BotEngine:
    """Resolve or create the BotEngine instance for the requested device serial."""
    if device_serial and str(device_serial).strip():
        s = str(device_serial).strip()
        eng = engine_manager.get_or_create_engine(s)
        try:
            eng.loop = asyncio.get_event_loop()
        except Exception:
            pass
        return eng
    try:
        bot_engine.loop = asyncio.get_event_loop()
    except Exception:
        pass
    return bot_engine


def load_bot_settings(device_serial: Optional[str] = None) -> dict:
    """Load settings for a specific device from settings/ folder, falling back to legacy paths or defaults."""
    res = DEFAULT_BOT_SETTINGS.copy()
    if device_serial:
        dev_file = get_device_settings_path(device_serial)
        safe_id = "".join(c if c.isalnum() else "_" for c in str(device_serial or "default"))
        legacy_dev_file = os.path.join(os.path.dirname(__file__), f"bot_settings_{safe_id}.json")
        target_f = dev_file if os.path.isfile(dev_file) else (legacy_dev_file if os.path.isfile(legacy_dev_file) else None)
        if target_f:
            try:
                with open(target_f, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    res.update(data)
                    res["device_serial"] = device_serial
                    return res
            except Exception:
                pass

    def_target = SETTINGS_FILE if os.path.isfile(SETTINGS_FILE) else (LEGACY_SETTINGS_FILE if os.path.isfile(LEGACY_SETTINGS_FILE) else None)
    if def_target:
        try:
            with open(def_target, "r", encoding="utf-8") as f:
                data = json.load(f)
                res.update(data)
        except Exception:
            pass

    if device_serial:
        res["device_serial"] = device_serial
    return res


def save_bot_settings_to_file(settings: dict, device_serial: Optional[str] = None):
    """Save settings per device inside the settings/ directory."""
    target_file = get_device_settings_path(device_serial) if device_serial else SETTINGS_FILE
    try:
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        current = load_bot_settings(device_serial)
        clean_update = {k: v for k, v in settings.items() if v is not None}
        current.update(clean_update)
        if device_serial:
            current["device_serial"] = device_serial
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save bot settings to {target_file}: {e}")


class InterceptingStdout:
    """Intercepts sys.stdout so print statements from all functions and modules
    are automatically streamed in real-time to the Web Dashboard Live Logs console."""
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self._buffer = ""
        self._lock = threading.Lock()

    def write(self, s):
        if self.original_stdout:
            try:
                self.original_stdout.write(s)
            except Exception:
                pass

        if getattr(_in_bot_log, "active", False):
            return

        with self._lock:
            self._buffer += str(s)
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                # Filter out standard uvicorn log spam
                if line.startswith("INFO:") or line.startswith("WARNING:") or line.startswith("DEBUG:") or "GET /api/" in line or "GET /ws/" in line:
                    continue

                level = "info"
                line_lower = line.lower()
                if any(x in line for x in ("❌", "error", "fail", "ล้มเหลว", "ไม่สำเร็จ")):
                    level = "error"
                elif any(x in line for x in ("⚠️", "warning", "warn", "เตือน")):
                    level = "warning"
                elif any(x in line for x in ("✅", "success", "สำเร็จ", "🎉", "🎁")):
                    level = "success"
                elif "[farmer]" in line_lower or "heartfarmer" in line_lower or "หัวใจ" in line:
                    level = "farmer"
                elif "[cleaner]" in line_lower or "friendcleaner" in line_lower:
                    level = "cleaner"
                elif any(x in line_lower for x in ("detected stage", "stage:")):
                    level = "stage"

                now_str = datetime.now().strftime("%H:%M:%S")
                tm = re.match(r"^\[(\d{2}:\d{2}:\d{2})\]", line)
                time_str = tm.group(1) if tm else now_str

                # Accurately detect device serial anywhere in the line
                found_device = None
                known_serials = list(engine_manager.engines.keys()) + list(_farmer_instances.keys())
                for ser in known_serials:
                    if ser and ser in line:
                        found_device = ser
                        break
                if not found_device:
                    m_ser = re.search(r"(emulator-\d+|\d+\.\d+\.\d+\.\d+:\d+)", line)
                    if m_ser:
                        found_device = m_ser.group(1)

                log_entry = {
                    "time": time_str,
                    "timestamp": time_str,
                    "message": line,
                    "level": level,
                    "device": found_device,
                    "target": found_device,
                }
                engine_manager.record_and_broadcast_log(log_entry)

                if found_device:
                    eng = engine_manager.get_or_create_engine(found_device)
                    eng.logs.append(log_entry)
                    loop = eng.loop or getattr(engine_manager, "loop", None)
                    if loop and eng.ws_subscribers:
                        for q in list(eng.ws_subscribers):
                            try:
                                loop.call_soon_threadsafe(q.put_nowait, log_entry)
                            except Exception:
                                pass
                else:
                    # Broadcast system/adb logs to all engines as well
                    for eng in engine_manager.get_all_engines().values():
                        eng.logs.append(log_entry)
                        loop = eng.loop or getattr(engine_manager, "loop", None)
                        if loop and eng.ws_subscribers:
                            for q in list(eng.ws_subscribers):
                                try:
                                    loop.call_soon_threadsafe(q.put_nowait, log_entry)
                                except Exception:
                                    pass

    def flush(self):
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass

    def isatty(self):
        if self.original_stdout and hasattr(self.original_stdout, "isatty"):
            try:
                return self.original_stdout.isatty()
            except Exception:
                return False
        return False

    def fileno(self):
        if self.original_stdout and hasattr(self.original_stdout, "fileno"):
            try:
                return self.original_stdout.fileno()
            except Exception:
                pass
        raise OSError("fileno not available")

    @property
    def encoding(self):
        if self.original_stdout and hasattr(self.original_stdout, "encoding"):
            return self.original_stdout.encoding
        return "utf-8"

    @property
    def errors(self):
        if self.original_stdout and hasattr(self.original_stdout, "errors"):
            return self.original_stdout.errors
        return "replace"

    def __getattr__(self, name):
        if self.original_stdout:
            return getattr(self.original_stdout, name)
        raise AttributeError(f"'InterceptingStdout' object has no attribute '{name}'")


# Initialize stdout interception immediately so every module's print statements are captured
if not isinstance(sys.stdout, InterceptingStdout):
    sys.stdout = InterceptingStdout(sys.stdout)


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    engine_manager.loop = loop
    bot_engine.loop = loop
    for eng in engine_manager.get_all_engines().values():
        eng.loop = loop
    if not isinstance(sys.stdout, InterceptingStdout):
        sys.stdout = InterceptingStdout(sys.stdout)
    bot_engine.log(f"🌐 Web Server started. ADB path: {get_adb_path()}")
    # Auto-Resume check after update
    asyncio.create_task(_async_auto_resume_check())


async def _async_auto_resume_check():
    """Checks if an auto-resume request was queued by the updater before upgrading."""
    try:
        from updater import get_saved_running_state, execute_auto_resume
        state = get_saved_running_state()
        if not state or not state.get("should_resume"):
            return

        bot_engine.log("⏳ ตรวจพบคำสั่งกู้คืนการทำงานหลังอัปเดต (Auto-Resume) กำลังรอระบบเตรียมพร้อม...", "info")
        await asyncio.sleep(3.5)

        def _resume_bot(dev_serial):
            eng = get_engine_for_device(dev_serial)
            settings = load_bot_settings(dev_serial)
            settings["device_serial"] = dev_serial
            eng.start(settings)

        def _resume_farmer(dev_serial, invite_url):
            _start_heart_farmer(dev_serial, invite_url)

        def _notify(msg):
            bot_engine.log(msg, "success")
            try:
                discord_notifier.send_message(msg)
            except Exception:
                pass

        execute_auto_resume(
            start_bot_device_fn=_resume_bot,
            start_farmer_fn=_resume_farmer,
            notify_fn=_notify,
        )
    except Exception as e:
        print(f"[WebServer] Auto-resume error: {e}", flush=True)


@app.on_event("shutdown")
async def shutdown_event():
    stream_manager.stop_all()


@app.get("/api/system/version")
def api_get_system_version(check: bool = False):
    from version import CURRENT_VERSION
    from updater import check_for_updates
    data = {
        "version": CURRENT_VERSION,
        "update_info": None
    }
    if check:
        data["update_info"] = check_for_updates()
    return data


@app.post("/api/system/update")
def api_trigger_update():
    from updater import (
        check_for_updates,
        save_running_state_before_update,
        download_installer,
        launch_silent_installer_and_exit,
    )
    update_info = check_for_updates()
    if not update_info.get("has_update") or not update_info.get("download_url"):
        raise HTTPException(status_code=400, detail="ไม่พบเวอร์ชันใหม่ หรือลิงก์ดาวน์โหลดไม่ถูกต้อง")

    # 1. Collect running state
    active_bot_devs = [s for s, e in engine_manager.get_all_engines().items() if e.is_running]
    if bot_engine.is_running and "default" not in active_bot_devs:
        active_bot_devs.append("default")

    active_farmer_devs = []
    farmer_invites = {}
    for d, t in list(_farmer_threads.items()):
        inst = _farmer_instances.get(d)
        if t and t.is_alive() and inst and not inst.stopped:
            active_farmer_devs.append(d)
            farmer_invites[d] = getattr(inst, "invite_url", "")

    save_running_state_before_update(
        active_bot_devices=active_bot_devs,
        active_farmer_devices=active_farmer_devs,
        farmer_invites=farmer_invites
    )

    # 2. Stop running operations cleanly
    for s in active_bot_devs:
        try:
            get_engine_for_device(s).stop()
        except Exception:
            pass
    for d in active_farmer_devs:
        try:
            _stop_heart_farmer(d)
        except Exception:
            pass

    # 3. Download & Launch in detached thread
    def _do_update():
        bot_engine.log(f"📥 กำลังดาวน์โหลดไฟล์อัปเดต v{update_info.get('latest_version')}...", "info")
        installer_path = download_installer(update_info["download_url"])
        if installer_path and os.path.isfile(installer_path):
            bot_engine.log("🚀 ดาวน์โหลดสำเร็จ กำลังปิดระบบและรันการติดตั้งทับอัตโนมัติ...", "success")
            time.sleep(1.0)
            launch_silent_installer_and_exit(installer_path)
        else:
            bot_engine.log("❌ ดาวน์โหลดไฟล์อัปเดตไม่สำเร็จ", "error")

    threading.Thread(target=_do_update, daemon=True).start()
    return {
        "success": True,
        "message": f"กำลังดาวน์โหลด CookieRun Bot v{update_info.get('latest_version')} และจะเริ่มติดตั้งให้อัตโนมัติ"
    }


@app.get("/api/devices")
def get_devices():
    """Scans all ADB emulators/devices and returns status with running engine state."""
    scanned = scan_adb_devices()
    all_engines = engine_manager.get_all_engines()
    
    # Enrich scanned devices
    device_map = {}
    for d in scanned:
        serial = d["serial"]
        engine = engine_manager.get_or_create_engine(serial)
        
        # Check HeartFarmer status on this device
        farmer_inst = _farmer_instances.get(serial)
        farmer_thread = _farmer_threads.get(serial)
        is_farmer_running = bool(farmer_thread and farmer_thread.is_alive() and farmer_inst and not farmer_inst.stopped)
        
        heart_rounds = getattr(farmer_inst, "rounds", 0) if farmer_inst else 0
        heart_success = getattr(farmer_inst, "success_count", max(0, heart_rounds - 1 if is_farmer_running else heart_rounds)) if farmer_inst else 0
        heart_step = getattr(farmer_inst, "current_step", "กำลังปั้มหัวใจ" if is_farmer_running else "") if farmer_inst else ""

        heart_stats = {
            "running": is_farmer_running,
            "rounds": heart_rounds,
            "success_count": heart_success,
            "current_step": heart_step
        }
        d["heart_stats"] = heart_stats

        # Check Friend Cleaner Scheduler status
        is_cleaner_target = bool(friend_cleaner_scheduler and friend_cleaner_scheduler.is_running and serial in friend_cleaner_scheduler.target_devices)
        is_cleaner_busy = bool(is_cleaner_target and friend_cleaner_scheduler.current_device == serial)
        cleaner_stat = friend_cleaner_scheduler.get_status() if friend_cleaner_scheduler else {}
        cleaner_step = friend_cleaner_scheduler.current_step if is_cleaner_target else ""
        cleaner_next = cleaner_stat.get("next_run")
        cleaner_dev_status = (friend_cleaner_scheduler.device_statuses.get(serial, {}) if friend_cleaner_scheduler else {})
        cur_dev_step = cleaner_dev_status.get("current_step") or cleaner_step

        cleaner_stats = {
            "running": is_cleaner_target,
            "is_busy": is_cleaner_busy,
            "current_device": friend_cleaner_scheduler.current_device if friend_cleaner_scheduler else None,
            "current_step": cur_dev_step,
            "next_run": cleaner_next,
            "next_run_seconds": cleaner_stat.get("next_run_seconds", 0),
        }
        d["cleaner_stats"] = cleaner_stats

        if is_farmer_running:
            d["is_running"] = True
            d["active_mode"] = "heart_farmer"
            d["current_stage"] = "HEART_FARMER"
            d["activity_description"] = f"กำลังปั้มหัวใจ (รอบที่ {heart_rounds}) • {heart_step}"
            farmer_start = getattr(farmer_inst, "start_time", None)
            if farmer_start:
                secs = int(time.time() - farmer_start)
                m, s = divmod(secs, 60)
                h, m = divmod(m, 60)
                d["uptime"] = f"{h:02d}:{m:02d}:{s:02d}"
            else:
                d["uptime"] = "กำลังทำงาน"
        elif is_cleaner_target:
            d["is_running"] = True
            d["active_mode"] = "friend_cleaner"
            d["current_stage"] = "FRIEND_CLEANER"
            if is_cleaner_busy:
                d["activity_description"] = f"กำลังลบเพื่อนเวล 1 🧹 • {cur_dev_step}"
            else:
                d["activity_description"] = f"ระบบลบเพื่อนเวล 1 (รอบถัดไป {cleaner_next or 'เร็วๆ นี้'})"
            d["uptime"] = "กำลังทำงาน"
        elif engine.is_running:
            d["is_running"] = True
            d["active_mode"] = "bot_engine"
            d["current_stage"] = engine.current_stage
            d["activity_description"] = f"กำลังฟาร์มเหรียญ/กล่อง • {engine.current_stage}"
            d["uptime"] = engine.get_status().get("uptime", "00:00:00")
        else:
            d["is_running"] = False
            d["active_mode"] = "idle"
            d["current_stage"] = engine.current_stage
            d["activity_description"] = "พร้อมทำงาน (หยุดพัก)"
            d["uptime"] = engine.get_status().get("uptime", "00:00:00")

        st = engine.get_status()
        d["rounds_played"] = st.get("rounds_played", 0)
        d["session_rounds"] = st.get("session_rounds", 0)
        d["mystery_boxes"] = st.get("mystery_boxes", 0)
        d["session_mystery_boxes"] = st.get("session_mystery_boxes", 0)
        d["box_counts"] = st.get("box_counts", {})
        d["session_box_counts"] = st.get("session_box_counts", {})
        d["coin_stats"] = st.get("coin_stats", {})
        d["round_history"] = st.get("round_history", [])
        d["session_round_history"] = st.get("session_round_history", [])
        d["session_start_time"] = st.get("session_start_time", "")
        d["session_uptime"] = st.get("session_uptime", "00:00:00")
        d["total_uptime"] = st.get("total_uptime", st.get("uptime", "00:00:00"))
        d["captcha_stats"] = st.get("captcha_stats", {})
        device_map[serial] = d

    # Also include any active engine serials that may not be in scanned (only if currently running)
    for serial, eng in all_engines.items():
        if serial not in device_map and eng.is_running:
            st = eng.get_status()
            farmer_inst = _farmer_instances.get(serial)
            farmer_thread = _farmer_threads.get(serial)
            is_farmer_running = bool(farmer_thread and farmer_thread.is_alive() and farmer_inst and not farmer_inst.stopped)
            heart_rounds = getattr(farmer_inst, "rounds", 0) if farmer_inst else 0
            heart_success = getattr(farmer_inst, "success_count", max(0, heart_rounds - 1 if is_farmer_running else heart_rounds)) if farmer_inst else 0
            heart_step = getattr(farmer_inst, "current_step", "") if farmer_inst else ""

            device_map[serial] = {
                "serial": serial,
                "name": f"จอ ({serial})",
                "model": "Device",
                "status": "online",
                "index": len(device_map) + 1,
                "is_running": eng.is_running or is_farmer_running,
                "active_mode": "heart_farmer" if is_farmer_running else "bot_engine",
                "current_stage": "HEART_FARMER" if is_farmer_running else eng.current_stage,
                "activity_description": f"กำลังปั้มหัวใจ (รอบที่ {heart_rounds})" if is_farmer_running else f"กำลังฟาร์ม • {eng.current_stage}",
                "heart_stats": {
                    "running": is_farmer_running,
                    "rounds": heart_rounds,
                    "success_count": heart_success,
                    "current_step": heart_step
                },
                "rounds_played": st.get("rounds_played", 0),
                "session_rounds": st.get("session_rounds", 0),
                "mystery_boxes": st.get("mystery_boxes", 0),
                "session_mystery_boxes": st.get("session_mystery_boxes", 0),
                "uptime": st.get("uptime", "00:00:00"),
                "session_uptime": st.get("session_uptime", "00:00:00"),
                "total_uptime": st.get("total_uptime", st.get("uptime", "00:00:00")),
                "session_start_time": st.get("session_start_time", ""),
                "box_counts": st.get("box_counts", {}),
                "session_box_counts": st.get("session_box_counts", {}),
                "coin_stats": st.get("coin_stats", {}),
                "round_history": st.get("round_history", []),
                "session_round_history": st.get("session_round_history", []),
                "captcha_stats": st.get("captcha_stats", {}),
            }
    return list(device_map.values())


@app.get("/api/status")
def get_bot_status(device: Optional[str] = None):
    eng = get_engine_for_device(device)
    return eng.get_status()


@app.get("/api/settings")
def get_settings(device: Optional[str] = None):
    dev = device.strip() if device and device.strip() else None
    return load_bot_settings(dev)


@app.post("/api/settings")
@app.post("/api/settings/save")
def save_settings(settings: BotSettings, device: Optional[str] = None):
    dev = (device.strip() if device and device.strip() else None) or \
          (settings.device_serial.strip() if settings.device_serial and settings.device_serial.strip() else None) or \
          (settings.device.strip() if settings.device and settings.device.strip() else None)
    
    settings_dict = {k: v for k, v in settings.model_dump().items() if v is not None}
    save_bot_settings_to_file(settings_dict, dev)

    # Immediately hot-reload settings into engine if running or initialized
    try:
        if dev:
            eng = get_engine_for_device(dev)
            if eng:
                eng.check_and_apply_settings_update(settings_dict)
        else:
            bot_engine.check_and_apply_settings_update(settings_dict)
            for running_eng in engine_manager.get_all_engines().values():
                running_eng.check_and_apply_settings_update(settings_dict)
    except Exception as e:
        print(f"[WebServer] Hot reload settings error: {e}")

    return {"success": True, "message": "บันทึกการตั้งค่าเรียบร้อยแล้ว"}


@app.post("/api/settings/reset")
def reset_settings(device: Optional[str] = None):
    dev = device.strip() if device and device.strip() else None
    target_file = get_device_settings_path(dev) if dev else SETTINGS_FILE
    if os.path.isfile(target_file):
        try:
            os.remove(target_file)
        except Exception:
            pass
    def_settings = load_bot_settings(dev)
    try:
        eng = get_engine_for_device(dev) if dev else bot_engine
        if eng:
            eng.check_and_apply_settings_update(def_settings)
    except Exception as e:
        print(f"[WebServer] Hot reload reset settings error: {e}")

    return {"success": True, "message": "รีเซ็ตการตั้งค่าเรียบร้อยแล้ว", "settings": def_settings}


@app.post("/api/start")
def start_bot(req: BotSettings, device: Optional[str] = None):
    dev = (req.device_serial if req.device_serial else None) or (req.device if req.device else None) or device
    if not dev or not str(dev).strip():
        scanned = scan_adb_devices()
        if scanned:
            dev = scanned[0]["serial"]
        else:
            dev = f"{config.DEVICE_IP}:{config.DEVICE_PORT}"
    dev = str(dev).strip()
    eng = get_engine_for_device(dev)
    eng.log(f"[BOT] สั่งเริ่มการทำงานบอทสำหรับจอ {dev}", "bot")

    # Load saved settings for this specific device as base config
    merged_settings = load_bot_settings(dev)
    # Merge any non-None fields passed in the request
    req_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    merged_settings.update(req_dict)

    # CRITICAL: Always ensure device_serial explicitly points to the chosen device!
    merged_settings["device_serial"] = dev
    if ":" in dev and not dev.startswith("emulator-"):
        parts = dev.split(":", 1)
        merged_settings["device_ip"] = parts[0]
        try:
            merged_settings["device_port"] = int(parts[1])
        except Exception:
            merged_settings["device_port"] = 5555
    else:
        merged_settings["device_ip"] = dev
        merged_settings["device_port"] = 5555

    res = eng.start(merged_settings)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@app.post("/api/farmer/start")
def api_farmer_start(req: FarmerStartRequest):
    invite = req.invite_url.strip() if req.invite_url else "ใส่ลิงก์เชิญเพื่อนของคุณ"
    targets = []
    if req.devices:
        targets = [d.strip() for d in req.devices if d and d.strip()]
    elif req.device:
        targets = [req.device.strip()]

    if not targets:
        raise HTTPException(status_code=400, detail="กรุณาระบุจอที่ต้องการเริ่มปั้มหัวใจ")

    results = []
    for dev in targets:
        res = _start_heart_farmer(dev, invite)
        results.append({"device": dev, **res})

    all_success = any(r.get("success") for r in results)
    if not all_success:
        msg = "; ".join(r.get("message", "") for r in results)
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "results": results, "message": f"เริ่มระบบปั้มหัวใจ {len(targets)} จอเรียบร้อยแล้ว"}


@app.post("/api/farmer/stop")
def api_farmer_stop(req: Optional[FarmerStopRequest] = None, device: Optional[str] = None):
    targets = []
    if req and req.devices:
        targets = [d.strip() for d in req.devices if d and d.strip()]
    elif req and req.device:
        targets = [req.device.strip()]
    elif device:
        targets = [device.strip()]

    if not targets:
        for d in list(_farmer_instances.keys()):
            _stop_heart_farmer(d)
        return {"success": True, "message": "สั่งหยุดระบบปั้มหัวใจทั้งหมดแล้ว"}

    results = []
    for dev in targets:
        res = _stop_heart_farmer(dev)
        results.append({"device": dev, **res})
    return {"success": True, "results": results, "message": f"สั่งหยุดระบบปั้มหัวใจ {len(targets)} จอเรียบร้อยแล้ว"}


@app.get("/api/farmer/status")
def api_farmer_status(device: Optional[str] = None):
    result = {}
    total_rounds = 0
    total_success = 0
    any_running = False
    for dev, t in list(_farmer_threads.items()):
        inst = _farmer_instances.get(dev)
        is_running = bool(t and t.is_alive() and inst and not inst.stopped)
        rounds = getattr(inst, "rounds", 0) if inst else 0
        success_count = getattr(inst, "success_count", max(0, rounds - 1 if is_running else rounds)) if inst else 0
        current_step = getattr(inst, "current_step", "กำลังปั้มหัวใจ" if is_running else "") if inst else ""
        result[dev] = {
            "running": is_running,
            "rounds": rounds,
            "success_count": success_count,
            "current_step": current_step
        }
        if is_running:
            any_running = True
        total_rounds += rounds
        total_success += success_count

    if device:
        dev = device.strip()
        d_stat = result.get(dev, {"running": False, "rounds": 0, "success_count": 0, "current_step": ""})
        return {
            "device": dev,
            "running": d_stat["running"],
            "rounds": d_stat["rounds"],
            "success_count": d_stat["success_count"],
            "current_step": d_stat["current_step"],
            "any_running": any_running,
            "total_rounds": total_rounds,
            "total_success": total_success,
            "instances": result
        }
    return {
        "any_running": any_running,
        "total_rounds": total_rounds,
        "total_success": total_success,
        "instances": result
    }


# ===========================================================================
# FRIEND CLEANER (LEVEL 1) ENDPOINTS
# ===========================================================================

@app.post("/api/cleaner/start")
def api_cleaner_start(req: FriendCleanerStartRequest):
    if friend_cleaner_scheduler is None:
        raise HTTPException(status_code=500, detail="FriendCleaner module not loaded")

    targets = []
    if req.devices:
        targets = [d.strip() for d in req.devices if d and d.strip()]
    elif req.device:
        targets = [req.device.strip()]

    if not targets:
        scanned = scan_adb_devices()
        if scanned:
            targets = [scanned[0]["serial"]]
        else:
            targets = [f"{config.DEVICE_IP}:{config.DEVICE_PORT}"]

    friend_cleaner_scheduler.start(
        devices=targets,
        interval_minutes=req.interval_minutes,
        run_immediately=req.run_immediately
    )
    bot_engine.log(f"[CLEANER] เริ่มระบบลบเพื่อนเวล 1 อัตโนมัติ (ทำซ้ำทุก {req.interval_minutes} นาที, จอ: {', '.join(targets)})", "cleaner")
    return {"success": True, "message": f"เริ่มระบบลบเพื่อนเวล 1 อัตโนมัติแล้ว (ทำซ้ำทุก {req.interval_minutes} นาที)"}


def _stop_cleaner_system():
    """Stops friend cleaner scheduler and sets stop event on all loaded friend_cleaner instances."""
    try:
        import sys
        if 'friend_cleaner' in sys.modules:
            fc = sys.modules['friend_cleaner']
            if hasattr(fc, '_GLOBAL_STOP_EVENT'):
                fc._GLOBAL_STOP_EVENT.set()
            if hasattr(fc, 'stop_all'):
                fc.stop_all()
        import friend_cleaner
        if hasattr(friend_cleaner, '_GLOBAL_STOP_EVENT'):
            friend_cleaner._GLOBAL_STOP_EVENT.set()
        if hasattr(friend_cleaner, 'stop_all'):
            friend_cleaner.stop_all()
    except Exception:
        pass

    if friend_cleaner_scheduler:
        try:
            friend_cleaner_scheduler.stop()
        except Exception:
            pass


@app.post("/api/cleaner/stop")
def api_cleaner_stop():
    _stop_cleaner_system()
    bot_engine.log("[CLEANER] สั่งหยุดระบบลบเพื่อนเวล 1 อัตโนมัติ", "cleaner")
    return {"success": True, "message": "สั่งหยุดระบบลบเพื่อนเวล 1 เรียบร้อยแล้ว"}


@app.get("/api/cleaner/status")
def api_cleaner_status():
    if friend_cleaner_scheduler is None:
        return {"is_running": False, "error": "FriendCleaner not loaded"}
    return friend_cleaner_scheduler.get_status()


@app.post("/api/cleaner/run_once")
def api_cleaner_run_once(req: Optional[FriendCleanerRunOnceRequest] = None, device: Optional[str] = None):
    dev = (req.device if req and req.device else None) or device
    if not dev or not str(dev).strip():
        scanned = scan_adb_devices()
        if scanned:
            dev = scanned[0]["serial"]
        else:
            dev = f"{config.DEVICE_IP}:{config.DEVICE_PORT}"

    def _async_clean():
        try:
            import importlib
            import friend_cleaner
            importlib.reload(friend_cleaner)
            if friend_cleaner_scheduler:
                friend_cleaner_scheduler.set_step(dev, f"เริ่มลบเพื่อนเวล 1 ทันทีบนจอ {dev}...")
            bot_engine.log(f"[CLEANER] กำลังเริ่มลบเพื่อนเวล 1 ทันทีบนจอ {dev}...", "cleaner")

            def _run_once_log(m: str):
                if friend_cleaner_scheduler:
                    clean_msg = m.split("]", 1)[-1].strip() if "]" in m else m
                    friend_cleaner_scheduler.set_step(dev, clean_msg)
                bot_engine.log(m, "cleaner")

            res = friend_cleaner.clean_level1_friends(dev, log_func=_run_once_log)
            done_msg = res.get('message', 'ลบเพื่อนเสร็จสิ้น')
            bot_engine.log(f"[CLEANER] {done_msg}", "cleaner")
            if friend_cleaner_scheduler:
                friend_cleaner_scheduler.set_step(dev, done_msg)
                with friend_cleaner_scheduler.lock:
                    friend_cleaner_scheduler.history.append({
                        "time": time.strftime("%H:%M:%S"),
                        "device": dev,
                        "success": res.get("success", False),
                        "ticked": res.get("total_ticked", 0)
                    })
        except Exception as e:
            bot_engine.log(f"[CLEANER] เกิดข้อผิดพลาด: {e}", "error")
            if friend_cleaner_scheduler:
                friend_cleaner_scheduler.set_step(dev, f"เกิดข้อผิดพลาด: {e}")

    t = threading.Thread(target=_async_clean, daemon=True, name=f"CleanOnce-{dev}")
    t.start()
    return {"success": True, "message": f"ส่งคำสั่งลบเพื่อนเวล 1 ทันทีสำหรับจอ {dev} แล้ว"}



@app.post("/api/stop")
def stop_bot(req: Optional[StopBotRequest] = None, device: Optional[str] = None):
    dev = (req.device_serial if req and req.device_serial else None) or (req.device if req and req.device else None) or device
    if not dev or not str(dev).strip():
        return api_stop_all()

    dev = str(dev).strip()

    # 1. Stop Heart Farmer on this device if running
    _stop_heart_farmer(dev)

    # 2. Stop Friend Cleaner immediately
    _stop_cleaner_system()

    # 3. Stop Bot Engine
    eng = get_engine_for_device(dev)
    eng.log(f"[BOT] สั่งหยุดการทำงานบอทสำหรับจอ {dev}", "bot")
    res = eng.stop()

    # 4. Force stop game app immediately via ADB
    try:
        from adb import get_adb_path
        import subprocess
        for pkg in ["com.devsisters.crg", "com.linecorp.LGCOOKIE"]:
            subprocess.run([adb_path, "-s", dev, "shell", "am", "force-stop", pkg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except Exception:
        pass

    return {"success": True, "message": f"สั่งหยุดการทำงานจอ {dev} ทันทีเรียบร้อยแล้ว"}


@app.post("/api/start-all")
def api_start_all():
    """Start bot on all scanned online devices."""
    devices = scan_adb_devices()
    started = []
    errors = []
    for d in devices:
        serial = d.get("serial")
        if not serial:
            continue
        eng = get_engine_for_device(serial)
        if not eng.is_running:
            settings = load_bot_settings(serial)
            res = eng.start(settings)
            if res.get("success", False):
                started.append(serial)
            else:
                errors.append(f"{serial}: {res.get('message', 'Failed')}")
        else:
            started.append(serial)
    return {
        "success": len(errors) == 0,
        "started": started,
        "errors": errors,
        "message": f"เริ่มบอทแล้ว {len(started)} จอ" + (f" (พบปัญหา: {', '.join(errors)})" if errors else "")
    }


@app.post("/api/stop-all")
def api_stop_all():
    """Stop bot, heart farmer, and close game immediately on all devices."""
    stopped = []

    # 1. Stop all bot engines
    for serial, eng in engine_manager.get_all_engines().items():
        if eng.is_running:
            eng.stop()
            stopped.append(serial)
    if bot_engine.is_running:
        bot_engine.stop()
        if "default" not in stopped:
            stopped.append("default")

    # 2. Stop all heart farmers
    for d in list(_farmer_instances.keys()):
        _stop_heart_farmer(d)
        if d not in stopped:
            stopped.append(d)

    # 3. Stop cleaner
    _stop_cleaner_system()

    # 4. Force-stop game on all scanned devices immediately
    try:
        from adb import get_adb_path
        import subprocess
        adb_path = get_adb_path()
        devices = scan_adb_devices()
        for d in devices:
            serial = d.get("serial")
            if serial:
                for pkg in ["com.devsisters.crg", "com.linecorp.LGCOOKIE"]:
                    subprocess.Popen([adb_path, "-s", serial, "shell", "am", "force-stop", pkg],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    return {"success": True, "stopped": stopped, "message": f"สั่งหยุดบอทและปิดเกมทุกจอทันทีเรียบร้อยแล้ว ({len(stopped)} จอ)"}


@app.post("/api/clear-ram")
def api_clear_ram(device: Optional[str] = None):
    """Manually trigger 3-level RAM clearance."""
    dev = device.strip() if device and device.strip() else None
    eng = get_engine_for_device(dev)
    clear_system_memory(dev, log_func=eng.log)
    return {"success": True, "message": f"🧹 เคลียร์ RAM สำเร็จ ({dev or 'Host PC'})"}



@app.post("/api/reset-stats")
def reset_stats(device: Optional[str] = None):
    if not device or device == "all":
        for serial, eng in engine_manager.get_all_engines().items():
            eng.reset_stats()
        bot_engine.reset_stats()
        # Clean all history directory files
        if os.path.isdir(HISTORY_DIR):
            for f in os.listdir(HISTORY_DIR):
                fp = os.path.join(HISTORY_DIR, f)
                if os.path.isfile(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
        return {"success": True, "message": "ลบสถิติทั้งหมดของทุกจอเรียบร้อยแล้ว"}

    eng = get_engine_for_device(device)
    eng.reset_stats()
    return {"success": True, "message": f"ลบสถิติของจอ {device} เรียบร้อยแล้ว"}


@app.post("/api/test-connection")
def test_connection(req: ConnectionTestRequest):
    target = req.device_serial or req.device_ip
    success, msg = device_check_connection(target, req.device_port)
    return {
        "success": success,
        "message": msg,
        "adb_path": get_adb_path(),
    }


@app.post("/api/reset-app")
def trigger_reset_app(req: ConnectionTestRequest):
    target = req.device_serial or req.device_ip
    eng = get_engine_for_device(target)
    try:
        device_reset_app(target, req.device_port)
        eng.log(f"[SYS] สั่งรีเซ็ตแอปเกมบน {target}", "info")
        return {"success": True, "message": f"App reset command executed on {target}"}
    except Exception as e:
        eng.log(f"[ERROR] รีเซ็ตแอปเกมไม่สำเร็จบน {target}: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tap")
def manual_tap(req: TapRequest):
    dev = (req.device or req.device_serial or "").strip()
    if not dev and req.device_ip and req.device_port:
        dev = f"{req.device_ip}:{req.device_port}"
    dev = dev or None
    eng = get_engine_for_device(dev)
    target = dev or eng.device_serial or eng.device_ip
    port = eng.device_port if eng else 5555
    try:
        tapped = False
        streamer = stream_manager.get_streamer(target)
        if streamer and streamer.is_running:
            tapped = streamer.tap(req.x, req.y)

        if not tapped:
            device_tap(target, port, req.x, req.y)

        eng.log(f"[ADB] แตะจอที่ ({req.x}, {req.y}) บน {target}", "adb")
        return {"success": True, "target": target, "x": req.x, "y": req.y}
    except Exception as e:
        eng.log(f"[ERROR] แตะจอไม่สำเร็จบน {target} ({req.x},{req.y}): {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/discord")
def get_discord_settings():
    return {
        "webhook_url": discord_notifier.webhook_url,
        "enabled": discord_notifier.enabled,
        "notify_boxes": discord_notifier.notify_boxes,
        "notify_rounds": discord_notifier.notify_rounds,
        "notify_antibot": discord_notifier.notify_antibot,
        "notify_status": discord_notifier.notify_status,
        "attach_screenshot": discord_notifier.attach_screenshot,
    }


@app.post("/api/discord")
@app.post("/api/discord/save")
def save_discord_settings(req: DiscordSettingsRequest):
    data = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    discord_notifier.update_settings(data)
    return {"success": True, "message": "บันทึกการตั้งค่า Discord สำเร็จ"}


@app.post("/api/discord/test")
def test_discord_webhook(req: DiscordTestRequest):
    success, msg = discord_notifier.test_webhook(req.webhook_url)
    return {"success": success, "message": msg}


def generate_placeholder_frame(text: str = "CookieRun Bot Idle") -> bytes:
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    img[:] = (28, 20, 16)  # Warm dark chocolate background matching dashboard
    cv2.rectangle(img, (20, 20), (1260, 700), (70, 50, 40), 2)
    cv2.putText(img, "CookieRun Classic Bot Pro", (420, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 215, 0), 2, cv2.LINE_AA)
    cv2.putText(img, str(text), (440, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 240), 1, cv2.LINE_AA)
    cv2.putText(img, "Emulator screen will appear automatically when connected", (380, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 160, 170), 1, cv2.LINE_AA)
    _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buffer.tobytes()

_device_stream_fps: Dict[str, float] = {}


@app.get("/api/stream")
async def video_feed(device: Optional[str] = None, fps: int = 60):
    fps = max(10, min(60, fps))
    eng = get_engine_for_device(device)
    target = (eng.device_serial or eng.device_ip or (device if device else "")).strip()

    if not target:
        try:
            connected = scan_adb_devices()
            if connected:
                target = connected[0].get("serial", "").strip()
        except Exception:
            pass

    if not target:
        async def no_device_gen():
            frame = generate_placeholder_frame("Waiting for Emulator Connection...")
            while True:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                await asyncio.sleep(1.0)
        return StreamingResponse(no_device_gen(), media_type="multipart/x-mixed-replace; boundary=frame")

    # Start high-speed hardware scrcpy stream
    streamer = stream_manager.get_streamer(target, max_fps=fps)
    streamer.max_fps = fps
    try:
        streamer.start()
    except Exception:
        pass

    async def resilient_stream_generator():
        streamer.add_subscriber()
        interval = 1.0 / max(10, min(60, fps))
        last_jpeg = None
        last_fallback_time = 0.0
        fps_deque = collections.deque(maxlen=15)

        # 1. Immediately yield an initial frame to prevent black screen on connect
        init_jpeg = streamer.latest_jpeg or eng.latest_frame_jpeg
        if init_jpeg is None:
            try:
                port = eng.device_port or (int(target.split(":")[1]) if ":" in target else 5555)
                screen = await asyncio.to_thread(device_capture_screen, target, port)
                if screen is not None and screen.size > 0:
                    _, buf = cv2.imencode(".jpg", screen, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    init_jpeg = buf.tobytes()
                    eng.update_frame(screen)
            except Exception:
                pass
        if init_jpeg is None:
            init_jpeg = generate_placeholder_frame(f"Connecting to {target}...")

        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + init_jpeg + b"\r\n"
        last_jpeg = init_jpeg
        fps_deque.append(time.time())

        try:
            while True:
                now = time.time()
                jpeg = streamer.latest_jpeg

                # Path A: High-speed hardware Scrcpy frame (30-60 FPS)
                if jpeg is not None and jpeg is not last_jpeg:
                    last_jpeg = jpeg
                    if streamer.latest_frame is not None:
                        eng.latest_frame = streamer.latest_frame
                        eng.latest_frame_jpeg = jpeg
                    
                    fps_deque.append(now)
                    if len(fps_deque) > 1:
                        dur = fps_deque[-1] - fps_deque[0]
                        if dur > 0:
                            _device_stream_fps[target] = round((len(fps_deque) - 1) / dur, 1)

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                    )
                    await asyncio.sleep(interval)
                    continue

                # Path B: Scrcpy is still warming up or inactive -> Fallback to ADB screencap
                if now - last_fallback_time > 0.3:
                    last_fallback_time = now
                    frame_bytes = None
                    if eng.is_running and eng.latest_frame_jpeg is not None:
                        frame_bytes = eng.latest_frame_jpeg
                    else:
                        try:
                            port = eng.device_port or (int(target.split(":")[1]) if ":" in target else 5555)
                            screen = await asyncio.to_thread(device_capture_screen, target, port)
                            if screen is not None and screen.size > 0:
                                _, buf = cv2.imencode(".jpg", screen, [cv2.IMWRITE_JPEG_QUALITY, 70])
                                frame_bytes = buf.tobytes()
                                eng.update_frame(screen)
                        except Exception:
                            pass

                    if frame_bytes is None and last_jpeg is None:
                        frame_bytes = generate_placeholder_frame(f"Device {target} Ready")

                    if frame_bytes is not None and frame_bytes != last_jpeg:
                        last_jpeg = frame_bytes
                        fps_deque.append(now)
                        if len(fps_deque) > 1:
                            dur = fps_deque[-1] - fps_deque[0]
                            if dur > 0:
                                _device_stream_fps[target] = round((len(fps_deque) - 1) / dur, 1)

                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                        )

                await asyncio.sleep(interval)
        except (GeneratorExit, asyncio.CancelledError, Exception):
            pass
        finally:
            streamer.remove_subscriber()
            _device_stream_fps.pop(target, None)

    return StreamingResponse(resilient_stream_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/stream-stats")
def get_stream_stats(device: Optional[str] = None):
    eng = get_engine_for_device(device)
    target = (eng.device_serial or eng.device_ip or (device if device else "")).strip()
    streamer = stream_manager.get_streamer(target)

    # Priority 1: Scrcpy active frame rate
    calc_fps = streamer.current_fps if streamer.is_running and streamer.current_fps > 0 else 0.0
    # Priority 2: Stream generator real delivery frame rate
    if calc_fps <= 0:
        calc_fps = _device_stream_fps.get(target, 0.0)

    return {
        "device": target,
        "is_scrcpy": streamer.is_running,
        "fps": calc_fps,
        "max_fps": streamer.max_fps,
        "subscribers": streamer.subscribers,
    }


@app.get("/api/screenshot")
def get_screenshot(device: Optional[str] = None):
    eng = get_engine_for_device(device)
    target = eng.device_serial or eng.device_ip
    try:
        screen = device_capture_screen(target, eng.device_port)
        _, buffer = cv2.imencode(".png", screen)
        return Response(content=buffer.tobytes(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/round-screenshot/{round_num}")
def get_round_screenshot(round_num: int, device: Optional[str] = None, file: Optional[str] = None):
    eng = get_engine_for_device(device)

    # 1. Check in-memory buffer if available
    jpeg_bytes = getattr(eng, "round_screenshots", {}).get(round_num)
    if jpeg_bytes is not None:
        return Response(content=jpeg_bytes, media_type="image/jpeg")

    # 2. Check disk in all known screenshot directories
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    search_dirs = [
        os.path.join(os.path.dirname(__file__), "screenshots"),
        os.path.join(base_dir, "screenshots"),
        os.path.abspath("screenshots"),
        os.path.abspath("src/screenshots"),
    ]

    target_basename = None
    if file:
        target_basename = os.path.basename(file.strip())

    # If filename not given in param, check round_history JSON file
    if not target_basename:
        dev_name = str(device or getattr(eng, "device_serial", "") or "emulator-5562").replace(":", "_").replace("/", "_")
        history_file = os.path.join(base_dir, "history", f"round_history_{dev_name}.json")
        if os.path.isfile(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as hf:
                    hdata = json.load(hf)
                    for item in hdata:
                        if item.get("round") == round_num and item.get("screenshot"):
                            target_basename = os.path.basename(item["screenshot"])
                            break
            except Exception:
                pass

    found_path = None
    if target_basename:
        for sdir in search_dirs:
            candidate = os.path.join(sdir, target_basename)
            if os.path.isfile(candidate):
                found_path = candidate
                break

    # If still not found, search with glob for matching round number
    if not found_path:
        import glob
        all_matches = []
        for sdir in search_dirs:
            if os.path.isdir(sdir):
                all_matches.extend(glob.glob(os.path.join(sdir, f"round_{round_num}_*.png")))
                all_matches.extend(glob.glob(os.path.join(sdir, f"round_{round_num}_*.jpg")))
        if all_matches:
            # Sort newest first by file modification time
            all_matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            found_path = all_matches[0]

    if found_path and os.path.isfile(found_path):
        try:
            with open(found_path, "rb") as img_file:
                media = "image/jpeg" if found_path.lower().endswith(".jpg") else "image/png"
                return Response(content=img_file.read(), media_type=media)
        except Exception:
            pass

    # 3. Fallback placeholder image
    blank = np.zeros((480, 854, 3), dtype=np.uint8)
    blank[:] = (20, 24, 35)
    cv2.putText(blank, f"No screenshot for Round #{round_num}", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 190), 2, cv2.LINE_AA)
    _, buf = cv2.imencode(".jpg", blank)
    return Response(content=buf.tobytes(), media_type="image/jpeg")
# -------------------------------------------------------------
# MACRO SYSTEM API ENDPOINTS
# -------------------------------------------------------------
@app.get("/api/macros")
def api_get_macros():
    """List all available macro profiles."""
    import macro_manager
    return {"success": True, "macros": macro_manager.list_macros()}


@app.get("/api/macros/{macro_id}")
def api_get_macro(macro_id: str):
    """Get specific macro profile details."""
    import macro_manager
    data = macro_manager.get_macro(macro_id)
    if not data:
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์มาโครที่ระบุ")
    return {"success": True, "macro": data}


@app.post("/api/macros/save")
def api_save_macro(payload: Dict[str, Any] = Body(...)):
    """Create or update a macro profile."""
    import macro_manager
    ok, res = macro_manager.save_macro(payload)
    if not ok:
        raise HTTPException(status_code=400, detail=f"บันทึกไม่สำเร็จ: {res}")
    return {"success": True, "id": res, "message": "บันทึกมาโครสำเร็จ"}


@app.delete("/api/macros/{macro_id}")
def api_delete_macro(macro_id: str):
    """Delete a macro profile."""
    import macro_manager
    ok = macro_manager.delete_macro(macro_id)
    if not ok:
        raise HTTPException(status_code=400, detail="ไม่สามารถลบไฟล์มาโครได้")
    return {"success": True, "message": "ลบมาโครสำเร็จ"}


@app.post("/api/macros/select")
def api_select_macro(payload: Dict[str, Any] = Body(...)):
    """Select and activate a macro for a device with persistent settings save and hot-reload."""
    device = payload.get("device_serial") or payload.get("device") or "127.0.0.1:7555"
    macro_id = payload.get("macro_id", "")
    enabled = bool(payload.get("enabled", True))

    dev = str(device).strip()
    eng = get_engine_for_device(dev)

    # 1. Update settings file
    settings_dict = load_bot_settings(dev)
    settings_dict["macro_enabled"] = enabled
    if macro_id:
        settings_dict["selected_macro_id"] = str(macro_id)
    save_bot_settings_to_file(settings_dict, dev)

    # 2. Hot reload into engine
    eng.check_and_apply_settings_update({
        "macro_enabled": enabled,
        "selected_macro_id": str(macro_id) if macro_id else eng.selected_macro_id,
    })

    import macro_manager
    mdata = macro_manager.get_macro(macro_id) if macro_id else None
    mname = mdata.get("name") if mdata else macro_id
    eng.log(f"▶️ [Macro] {'เปิดใช้งาน' if enabled else 'ปิดใช้งาน'}มาโคร: {mname}", "success")

    # 3. If bot is currently in-game, start playing immediately!
    if enabled and mdata and eng.is_running and eng.current_stage in ["IN_GAME", "GAME_START", "STAGE_IN_GAME", "GAME_RELAY"]:
        if not eng.macro_player.is_running:
            eng.log(f"⚡ [Macro] กำลังวิ่งอยู่ในเกมพอดี! เริ่มรันสเต็ปมาโคร {mname} ทันที...", "info")
            eng.macro_player.start(mdata)

    return {"success": True, "macro_enabled": enabled, "selected_macro_id": macro_id, "name": mname}


@app.post("/api/macros/test")
def api_test_macro(payload: Dict[str, Any] = Body(...)):
    """Test-run a single macro or single action on a device."""
    device_serial = payload.get("device_serial") or payload.get("device") or "127.0.0.1:7555"
    action_type = payload.get("action", "jump")
    macro_id = payload.get("macro_id")

    eng = get_engine_for_device(device_serial)
    player = getattr(eng, "macro_player", None)
    if not player:
        from macro_player import MacroPlayer
        player = MacroPlayer(device_serial)

    if action_type == "jump":
        player.jump()
    elif action_type == "double_jump":
        player.double_jump(float(payload.get("air_time", 0.16)))
    elif action_type == "slide":
        player.slide(float(payload.get("duration", 0.40)))
    elif action_type == "stop":
        player.stop()
        eng.log("⏹️ [Macro] สั่งหยุดการรันมาโครแล้ว", "info")
        return {"success": True, "message": "หยุดการรันมาโครแล้ว"}
    elif action_type == "test_macro" and macro_id:
        import macro_manager
        mdata = macro_manager.get_macro(macro_id)
        if mdata:
            player.stop()
            eng.log(f"▶️ [Macro Run] เริ่มเตรียมเข้าห้องวิ่งและรันมาโคร: {mdata.get('name')} บนจอ {device_serial}", "info")
            player.start_with_navigation(mdata, device_serial, eng.device_port, log_fn=eng.log)
            return {"success": True, "message": f"กำลังเริ่มรันมาโคร {mdata.get('name')}"}
        else:
            raise HTTPException(status_code=404, detail="ไม่พบมาโคร")
    return {"success": True, "message": f"ทดสอบส่งแอ็กชัน {action_type} สำเร็จ"}


# -------------------------------------------------------------
# INTERACTIVE TAP & MACRO RECORDER API ENDPOINTS
# -------------------------------------------------------------
@app.post("/api/tap")
def api_tap_screen(payload: TapRequest):
    device = payload.device_serial or payload.device or "127.0.0.1:7555"
    eng = get_engine_for_device(device)
    target = eng.device_serial or eng.device_ip or device

    # Check if macro recording is active
    from macro_recorder import macro_recorder_manager
    rec = macro_recorder_manager.get_recorder(target)
    if rec.status == "RECORDING":
        if payload.x < 450 and payload.y > 450:
            rec.record_jump()
        elif payload.x > 750 and payload.y > 450:
            rec.record_slide_instant(0.4)
        else:
            rec.actions.append({
                "t": round(time.perf_counter() - rec.start_perf, 2) if rec.start_perf > 0 else 0.0,
                "action": "tap",
                "x": payload.x,
                "y": payload.y
            })

    # Try fast scrcpy tap first (< 1ms)
    try:
        streamer = stream_manager.get_streamer(target)
        if streamer and streamer.tap(payload.x, payload.y):
            return {"success": True, "method": "scrcpy"}
    except Exception:
        pass

    # Fallback to safe_device_tap
    try:
        from actions import safe_device_tap
        safe_device_tap(target, eng.device_port, payload.x, payload.y)
        return {"success": True, "method": "adb"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/macros/record/arm")
def api_record_arm(payload: Dict[str, Any] = Body(...)):
    """Arm the recorder to wait for the in-game running screen, auto-tapping Play from Lobby."""
    device = payload.get("device_serial") or payload.get("device") or "127.0.0.1:7555"
    name = payload.get("name", "")
    from macro_recorder import macro_recorder_manager
    rec = macro_recorder_manager.get_recorder(device)
    eng = get_engine_for_device(device)
    rec.set_log_fn(eng.log)
    rec.arm(name=name)

    eng.log("🟡 [Macro Record] เข้าสู่โหมดเตรียมบันทึก — กำลังตรวจจับหน้าจอและกด Play หน้าล็อบบี้เพื่อพาเข้าห้องวิ่งให้อัตโนมัติ...", "info")
    rec.start_auto_flow(device, eng.device_port, log_fn=eng.log)
    return {"success": True, "status": rec.status, "message": "เตรียมพร้อมบันทึก กำลังกดเริ่มเกมและรอเข้าห้องวิ่ง..."}


@app.post("/api/macros/record/trigger")
def api_record_trigger(payload: Dict[str, Any] = Body(...)):
    """Force start recording right now (t=0)."""
    device = payload.get("device_serial") or payload.get("device") or "127.0.0.1:7555"
    from macro_recorder import macro_recorder_manager
    rec = macro_recorder_manager.get_recorder(device)
    eng = get_engine_for_device(device)
    rec.set_log_fn(eng.log)
    rec.status = "ARMED"
    rec.trigger_in_game_start()

    eng.log("🟢 [Macro Record] เริ่มจับเวลาและบันทึกมาโครสดแล้ว (t=0.00s)", "success")
    return {"success": True, "status": rec.status}


@app.post("/api/macros/record/action")
def api_record_action(payload: Dict[str, Any] = Body(...)):
    """Record an action (jump, double_jump, slide_down, slide_up, slide)."""
    device = payload.get("device_serial") or payload.get("device") or "127.0.0.1:7555"
    action = payload.get("action", "jump")
    from macro_recorder import macro_recorder_manager
    rec = macro_recorder_manager.get_recorder(device)

    # Also send tap to real emulator so character actually jumps/slides!
    from macro_player import MacroPlayer
    player = MacroPlayer(device)

    result = {}
    if action == "jump":
        result = rec.record_jump()
        player.jump()
    elif action == "double_jump":
        air_time = float(payload.get("air_time", 0.15))
        result = {
            "t": round(time.perf_counter() - rec.start_perf, 2) if rec.start_perf > 0 else 0.0,
            "action": "double_jump",
            "air_time": air_time
        }
        rec.actions.append(result)
        player.double_jump(air_time)
    elif action == "slide_down":
        rec.record_slide_down()
        player._send_down(player.SLIDE_X, player.SLIDE_Y)
    elif action == "slide_up":
        result = rec.record_slide_up()
        player._send_up(player.SLIDE_X, player.SLIDE_Y)
    elif action == "slide":
        dur = float(payload.get("duration", 0.40))
        result = rec.record_slide_instant(dur)
        player.slide(dur)

    return {"success": True, "recorded": result, "status": rec.get_status()}


@app.post("/api/macros/record/stop")
def api_record_stop(payload: Dict[str, Any] = Body(...)):
    """Stop recording and save JSON profile."""
    device = payload.get("device_serial") or payload.get("device") or "127.0.0.1:7555"
    custom_name = payload.get("name", "")
    from macro_recorder import macro_recorder_manager
    rec = macro_recorder_manager.get_recorder(device)
    saved = rec.stop_and_save(custom_name)

    eng = get_engine_for_device(device)
    if saved:
        eng.log(f"💾 [Macro Record] บันทึกมาโครลงไฟล์ JSON สำเร็จ: {saved.get('name')} ({len(saved.get('actions', []))} แอ็กชัน)", "success")
        return {"success": True, "macro": saved, "message": "บันทึกมาโครลงไฟล์ JSON สำเร็จ"}
    return {"success": False, "message": "ไม่มีข้อมูลการบันทึก"}


@app.get("/api/macros/record/status")
def api_record_status(device: Optional[str] = None):
    """Check recorder status for device."""
    target = device or "127.0.0.1:7555"
    from macro_recorder import macro_recorder_manager
    rec = macro_recorder_manager.get_recorder(target)
    return rec.get_status()


@app.get("/api/logs")
def get_logs(device: Optional[str] = None):
    if device == "all" or not device:
        return list(engine_manager.global_logs)
    eng = get_engine_for_device(device)
    seen = set()
    combined = []
    for item in list(eng.logs):
        sig = (item.get("timestamp"), item.get("message"))
        if sig not in seen:
            seen.add(sig)
            combined.append(item)
    for item in list(engine_manager.global_logs):
        t_dev = item.get("device") or item.get("target")
        if not t_dev or t_dev == device:
            sig = (item.get("timestamp"), item.get("message"))
            if sig not in seen:
                seen.add(sig)
                combined.append(item)
    return combined


@app.get("/api/logs/export")
def export_logs(device: Optional[str] = None):
    """Export and download current logs as a formatted UTF-8 .txt file."""
    logs_data = get_logs(device=device)
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = [
        "=" * 60,
        "  CookieRun Classic Bot - Activity Logs Export",
        f"  Export Time : {date_now}",
        f"  Device Scope: {device if device else 'All Devices'}",
        f"  Total Rows  : {len(logs_data)}",
        "=" * 60,
        "",
    ]
    lines = list(header)
    for item in logs_data:
        ts = item.get("timestamp") or item.get("time") or ""
        lvl = str(item.get("level") or "INFO").upper()
        target = item.get("target") or item.get("device") or ""
        dev_str = f" [{target}]" if target else ""
        msg = str(item.get("message") or "").strip()
        lines.append(f"[{ts}] [{lvl}]{dev_str} {msg}")

    text_content = "\r\n".join(lines)
    ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cookierun_bot_logs_{ts_file}.txt"
    return Response(
        content=text_content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, device: Optional[str] = None):
    await websocket.accept()
    queue = asyncio.Queue()
    is_all = (device == "all" or not device)
    loop = asyncio.get_running_loop()

    if is_all:
        engine_manager.loop = loop
        engine_manager.global_ws_subscribers.append(queue)
        try:
            history = list(engine_manager.global_logs)
            await websocket.send_json({"type": "history", "logs": history})

            while True:
                log_entry = await queue.get()
                await websocket.send_json({"type": "log", "log": log_entry})
        except (WebSocketDisconnect, asyncio.CancelledError, Exception):
            pass
        finally:
            if queue in engine_manager.global_ws_subscribers:
                engine_manager.global_ws_subscribers.remove(queue)
    else:
        eng = get_engine_for_device(device)
        eng.loop = loop
        engine_manager.loop = loop
        eng.ws_subscribers.append(queue)
        try:
            seen = set()
            history = []
            for item in list(eng.logs):
                sig = (item.get("timestamp"), item.get("message"))
                if sig not in seen:
                    seen.add(sig)
                    history.append(item)
            for item in list(engine_manager.global_logs):
                t_dev = item.get("device") or item.get("target")
                if not t_dev or t_dev == device:
                    sig = (item.get("timestamp"), item.get("message"))
                    if sig not in seen:
                        seen.add(sig)
                        history.append(item)
            await websocket.send_json({"type": "history", "logs": history})

            while True:
                log_entry = await queue.get()
                await websocket.send_json({"type": "log", "log": log_entry})
        except (WebSocketDisconnect, asyncio.CancelledError, Exception):
            pass
        finally:
            if queue in eng.ws_subscribers:
                eng.ws_subscribers.remove(queue)


@app.get("/", response_class=HTMLResponse)
def get_index(ui: Optional[str] = None):
    legacy_index_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
    react_index_path = os.path.join(_project_root, "frontend", "dist", "index.html")

    if ui == "legacy" and os.path.isfile(legacy_index_path):
        with open(legacy_index_path, "r", encoding="utf-8") as f:
            return f.read()

    if os.path.isfile(react_index_path):
        with open(react_index_path, "r", encoding="utf-8") as f:
            return f.read()

    if os.path.isfile(legacy_index_path):
        with open(legacy_index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Web Dashboard UI file not found</h1>"


@app.get("/legacy", response_class=HTMLResponse)
def get_legacy_page():
    legacy_index_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.isfile(legacy_index_path):
        with open(legacy_index_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Legacy UI not found</h1>", status_code=404)
