import asyncio
import io
import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

import cv2
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
)
from bot_engine import (
    BOOST_OPTIONS,
    BotEngine,
    bot_engine,
    engine_manager,
    get_device_settings_path,
)
from discord_notifier import discord_notifier
from scrcpy_streamer import stream_manager

# Heart Farmer (imported lazily to avoid circular deps)
try:
    from heart_farmer import HeartFarmer as _HeartFarmer
except ImportError:
    _HeartFarmer = None

try:
    from friend_cleaner import friend_cleaner_scheduler, clean_level1_friends
except ImportError:
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
    bot_engine.log(f"[FARMER] สั่งหยุดระบบปั้มหัวใจบนจอ {device}", "farmer")
    print(f"[WebServer] HeartFarmer stopping on {device}", flush=True)
    return {"success": True, "message": f"สั่งหยุดระบบปั้มหัวใจบนจอ {device} เรียบร้อยแล้ว"}

app = FastAPI(title="CookieRun Classic Bot Web Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates_path = os.path.join(os.path.dirname(__file__), "templates")
if os.path.isdir(templates_path):
    app.mount("/templates", StaticFiles(directory=templates_path), name="templates")

_bot_icon_path = os.path.join(os.path.dirname(__file__), "bot_icon.ico")

@app.get("/bot_icon.ico", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    if os.path.exists(_bot_icon_path):
        with open(_bot_icon_path, "rb") as f:
            return Response(content=f.read(), media_type="image/x-icon")
    return Response(status_code=404)


# Models
class StartBotRequest(BaseModel):
    device_serial: Optional[str] = None
    device_ip: str = "127.0.0.1"
    device_port: int = 7555
    use_hp_boost: bool = False
    use_item_extension: bool = False
    use_double_xp: bool = False
    use_fast_start: bool = False
    fast_start_min_stock: int = 10
    use_cookie_relay: bool = False
    cookie_relay_min_stock: int = 10
    use_desired_random_boost: bool = False
    desired_boost_id: str = "double_coins"
    detect_relic: bool = True
    send_friend_lives: bool = True
    heart_farmer_enabled: bool = False
    heart_farmer_device: str = "emulator-5562"
    heart_farmer_devices: List[str] = []
    heart_farmer_invite: str = "ใส่ลิงก์เชิญเพื่อนของคุณ"
    stop_goal_rounds_enabled: bool = False
    stop_goal_rounds_target: int = 50
    stop_goal_time_enabled: bool = False
    stop_goal_time_hours: float = 2.0


BotSettings = StartBotRequest


class StopBotRequest(BaseModel):
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


SETTINGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings"))
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
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save bot settings to {target_file}: {e}")


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    bot_engine.loop = loop
    for eng in engine_manager.get_all_engines().values():
        eng.loop = loop
    bot_engine.log(f"🌐 Web Server started. ADB path: {get_adb_path()}")


@app.on_event("shutdown")
async def shutdown_event():
    stream_manager.stop_all()


@app.get("/api/devices")
def get_devices():
    """Scans all ADB emulators/devices and returns status with running engine state."""
    scanned = scan_adb_devices()
    all_engines = engine_manager.get_all_engines()
    
    # Enrich scanned devices
    device_map = {}
    for d in scanned:
        serial = d["serial"]
        engine = all_engines.get(serial)
        d["is_running"] = engine.is_running if engine else False
        d["current_stage"] = engine.current_stage if engine else "IDLE"
        if engine:
            st = engine.get_status()
            d["rounds_played"] = st.get("rounds_played", 0)
            d["mystery_boxes"] = st.get("mystery_boxes", 0)
            d["uptime"] = st.get("uptime", "00:00:00")
            d["box_counts"] = st.get("box_counts", {})
            d["coin_stats"] = st.get("coin_stats", {})
            d["round_history"] = st.get("round_history", [])
        else:
            d["rounds_played"] = 0
            d["mystery_boxes"] = 0
            d["uptime"] = "00:00:00"
            d["box_counts"] = {"wood": 0, "silver": 0, "gold": 0, "rainbow": 0, "total": 0}
            d["coin_stats"] = {"session_earned": 0, "session_xp_earned": 0, "coins_per_hour": 0, "last_round": 0, "last_round_xp": 0}
            d["round_history"] = []
        device_map[serial] = d

    # Also include any active engine serials that may not be in scanned (only if currently running)
    for serial, eng in all_engines.items():
        if serial not in device_map and eng.is_running:
            st = eng.get_status()
            device_map[serial] = {
                "serial": serial,
                "name": f"จอ ({serial})",
                "model": "Device",
                "status": "online",
                "index": len(device_map) + 1,
                "is_running": eng.is_running,
                "current_stage": eng.current_stage,
                "rounds_played": st.get("rounds_played", 0),
                "mystery_boxes": st.get("mystery_boxes", 0),
                "uptime": st.get("uptime", "00:00:00"),
                "box_counts": st.get("box_counts", {}),
                "coin_stats": st.get("coin_stats", {}),
                "round_history": st.get("round_history", []),
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


@app.post("/api/settings/save")
def save_settings(settings: BotSettings, device: Optional[str] = None):
    dev = device.strip() if device and device.strip() else None
    save_bot_settings_to_file(settings.model_dump(), dev)
    return {"success": True, "message": "Settings saved"}


@app.post("/api/settings/reset")
def reset_settings(device: Optional[str] = None):
    dev = device.strip() if device and device.strip() else None
    target_file = get_device_settings_path(dev) if dev else SETTINGS_FILE
    if os.path.isfile(target_file):
        try:
            os.remove(target_file)
        except Exception:
            pass
    return {"success": True, "settings": load_bot_settings(dev)}


@app.post("/api/start")
def start_bot(req: BotSettings, device: Optional[str] = None):
    dev = (req.device_serial if req.device_serial else None) or device
    if not dev or not str(dev).strip():
        scanned = scan_adb_devices()
        if scanned:
            dev = scanned[0]["serial"]
        else:
            dev = f"{config.DEVICE_IP}:{config.DEVICE_PORT}"
    eng = get_engine_for_device(dev)
    eng.log(f"[BOT] สั่งเริ่มการทำงานบอทสำหรับจอ {dev}", "bot")
    res = eng.start(req.model_dump())
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])

    # --- Launch Heart Farmer thread if enabled ---
    if req.heart_farmer_enabled and _HeartFarmer is not None:
        farmer_invite = req.heart_farmer_invite.strip() or "ลิงก์เชิญเพื่อน"
        target_devs = [d.strip() for d in req.heart_farmer_devices if d and d.strip()] if req.heart_farmer_devices else ([req.heart_farmer_device.strip()] if req.heart_farmer_device else [dev])
        for fdev in target_devs:
            if fdev:
                _start_heart_farmer(fdev, farmer_invite)

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
    any_running = False
    for dev, t in list(_farmer_threads.items()):
        inst = _farmer_instances.get(dev)
        is_running = bool(t and t.is_alive() and inst and not inst.stopped)
        rounds = inst.rounds if inst else 0
        result[dev] = {
            "running": is_running,
            "rounds": rounds
        }
        if is_running:
            any_running = True
        total_rounds += rounds

    if device:
        dev = device.strip()
        d_stat = result.get(dev, {"running": False, "rounds": 0})
        return {
            "device": dev,
            "running": d_stat["running"],
            "rounds": d_stat["rounds"],
            "any_running": any_running,
            "total_rounds": total_rounds,
            "instances": result
        }
    return {
        "any_running": any_running,
        "total_rounds": total_rounds,
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


@app.post("/api/cleaner/stop")
def api_cleaner_stop():
    if friend_cleaner_scheduler is None:
        raise HTTPException(status_code=500, detail="FriendCleaner module not loaded")
    friend_cleaner_scheduler.stop()
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
            bot_engine.log(f"[CLEANER] กำลังเริ่มลบเพื่อนเวล 1 ทันทีบนจอ {dev}...", "cleaner")
            res = friend_cleaner.clean_level1_friends(dev, log_func=lambda m: bot_engine.log(m, "cleaner"))
            bot_engine.log(f"[CLEANER] {res.get('message', 'ลบเพื่อนเสร็จสิ้น')}", "cleaner")
        except Exception as e:
            bot_engine.log(f"[CLEANER] เกิดข้อผิดพลาด: {e}", "error")

    t = threading.Thread(target=_async_clean, daemon=True, name=f"CleanOnce-{dev}")
    t.start()
    return {"success": True, "message": f"ส่งคำสั่งลบเพื่อนเวล 1 ทันทีสำหรับจอ {dev} แล้ว"}



@app.post("/api/stop")
def stop_bot(req: Optional[StopBotRequest] = None, device: Optional[str] = None):
    dev = (req.device_serial if req and req.device_serial else None) or device
    if not dev or not str(dev).strip():
        running_engines = [e for e in engine_manager.get_all_engines().values() if e.is_running]
        if running_engines:
            for e in running_engines:
                e.stop()
            return {"success": True, "message": "สั่งหยุดบอททุกจอที่ทำงานอยู่แล้ว"}
        scanned = scan_adb_devices()
        if scanned:
            dev = scanned[0]["serial"]
        else:
            dev = f"{config.DEVICE_IP}:{config.DEVICE_PORT}"
    eng = get_engine_for_device(dev)
    eng.log(f"[BOT] สั่งหยุดการทำงานบอทสำหรับจอ {dev}", "bot")
    res = eng.stop()
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("message", "หยุดบอทไม่สำเร็จ"))
    return res


@app.post("/api/reset-stats")
def reset_stats(device: Optional[str] = None):
    eng = get_engine_for_device(device)
    eng.reset_stats()
    return {"success": True}


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
    dev = req.device_serial or (f"{req.device_ip}:{req.device_port}" if req.device_ip and req.device_port else None)
    eng = get_engine_for_device(dev)
    target = eng.device_serial or eng.device_ip
    try:
        device_tap(target, eng.device_port, req.x, req.y)
        eng.log(f"[ADB] Tap {req.x},{req.y}", "adb")
        return {"success": True, "x": req.x, "y": req.y}
    except Exception as e:
        eng.log(f"[ERROR] Tap failed at ({req.x},{req.y}): {e}", "error")
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


@app.post("/api/discord/save")
def save_discord_settings(req: DiscordSettingsRequest):
    discord_notifier.update_settings(req.dict())
    return {"success": True, "message": "บันทึกการตั้งค่า Discord สำเร็จ"}


@app.post("/api/discord/test")
def test_discord_webhook(req: DiscordTestRequest):
    success, msg = discord_notifier.test_webhook(req.webhook_url)
    return {"success": success, "message": msg}


def generate_placeholder_frame(text: str = "CookieRun Bot Idle") -> bytes:
    img = np.zeros((480, 854, 3), dtype=np.uint8)
    img[:] = (20, 24, 35)  # Dark slate background
    cv2.putText(img, "CookieRun Classic Bot", (240, 210), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 200, 100), 2, cv2.LINE_AA)
    cv2.putText(img, text, (240, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 190), 1, cv2.LINE_AA)
    cv2.putText(img, "Resolution: 1280x720 | Click Start to stream live screen", (190, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (120, 120, 130), 1, cv2.LINE_AA)
    _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buffer.tobytes()


@app.get("/api/stream")
async def video_feed(device: Optional[str] = None, fps: int = 60):
    fps = max(10, min(60, fps))
    eng = get_engine_for_device(device)
    target = eng.device_serial or eng.device_ip

    # Attempt high-speed hardware scrcpy stream
    streamer = stream_manager.get_streamer(target, max_fps=fps)
    streamer.max_fps = fps
    if streamer.start():
        async def scrcpy_generator():
            streamer.add_subscriber()
            interval = 1.0 / max(1, fps)
            try:
                while True:
                    jpeg = streamer.latest_jpeg
                    if jpeg is not None:
                        if streamer.latest_frame is not None:
                            eng.latest_frame = streamer.latest_frame
                            eng.latest_frame_jpeg = jpeg
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                        )
                    await asyncio.sleep(interval)
            except (GeneratorExit, asyncio.CancelledError, Exception):
                pass
            finally:
                streamer.remove_subscriber()

        return StreamingResponse(scrcpy_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

    # Graceful fallback to ADB screencap
    async def frame_generator():
        interval = 1.0 / max(5, min(20, fps))
        try:
            while True:
                now = time.time()
                frame_bytes = None
                if eng.is_running and eng.latest_frame_jpeg is not None:
                    frame_bytes = eng.latest_frame_jpeg
                else:
                    if now - eng.last_frame_time > 0.5:
                        eng.last_frame_time = now
                        try:
                            screen = await asyncio.to_thread(device_capture_screen, target, eng.device_port)
                            eng.update_frame(screen)
                        except Exception:
                            pass
                    frame_bytes = eng.latest_frame_jpeg or generate_placeholder_frame(f"Device {target} Ready")

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
                await asyncio.sleep(interval)
        except (GeneratorExit, asyncio.CancelledError, Exception):
            pass

    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/stream-stats")
def get_stream_stats(device: Optional[str] = None):
    eng = get_engine_for_device(device)
    target = eng.device_serial or eng.device_ip
    streamer = stream_manager.get_streamer(target)
    return {
        "device": target,
        "is_scrcpy": streamer.is_running,
        "fps": streamer.current_fps,
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
def get_round_screenshot(round_num: int, device: Optional[str] = None):
    eng = get_engine_for_device(device)
    jpeg_bytes = eng.round_screenshots.get(round_num)
    if jpeg_bytes is not None:
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    blank = np.zeros((480, 854, 3), dtype=np.uint8)
    blank[:] = (20, 24, 35)
    cv2.putText(blank, f"No screenshot for Round #{round_num}", (220, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 190), 2, cv2.LINE_AA)
    _, buf = cv2.imencode(".jpg", blank)
    return Response(content=buf.tobytes(), media_type="image/jpeg")


@app.get("/api/logs")
def get_logs(device: Optional[str] = None):
    if device == "all" or not device:
        return list(engine_manager.global_logs)
    eng = get_engine_for_device(device)
    return list(eng.logs)


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, device: Optional[str] = None):
    await websocket.accept()
    queue = asyncio.Queue()
    is_all = (device == "all" or not device)

    if is_all:
        engine_manager.loop = asyncio.get_running_loop()
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
        eng.loop = asyncio.get_running_loop()
        eng.ws_subscribers.append(queue)
        try:
            history = list(eng.logs)
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
def get_index():
    index_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Web Dashboard UI file not found in web/index.html</h1>"
