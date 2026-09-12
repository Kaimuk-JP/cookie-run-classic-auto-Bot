"""
heart_farmer.py - CookieRun Classic Heart Farming Bot
Powered by Fast Flow (Dynamic Image Polling & Real-time Vision Detection)

Loop: clear data -> register Devplay -> add friend -> send heart -> repeat

Usage:
    python src/heart_farmer.py [device_serial] [max_rounds]
    python src/heart_farmer.py emulator-5562
    python src/heart_farmer.py 127.0.0.1:16480 50
"""

import sys
import os
import time
import random
import string
import traceback
from typing import Optional

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except Exception:
    pass

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
_ROOT = os.path.dirname(_SRC)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import cv2
import numpy as np

from adb import (
    _format_target,
    _run_cmd,
    get_adb_path,
    device_capture_screen,
    resolve_emulator_name,
    clear_system_memory,
    ensure_adb_root,
)
from error_logger import record_game_error

PACKAGE = "com.devsisters.crg"
INVITE_URL = "https://cookierunglobal.onelink.me/Xr0A/onm0jzbf"


# ===========================================================================
# LOW-LEVEL ADB HELPERS
# ===========================================================================

def _adb(device: str, *args, timeout: int = 15):
    adb = get_adb_path()
    target = _format_target(device)
    res = _run_cmd([adb, "-s", target] + list(args),
                   capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0 and ("device not found" in (res.stderr or "").lower() or "device offline" in (res.stderr or "").lower()):
        if ":" in str(target):
            _run_cmd([adb, "connect", target], timeout=5)
            time.sleep(0.5)
            res = _run_cmd([adb, "-s", target] + list(args),
                           capture_output=True, text=True, timeout=timeout)
    return res


def _tap(device: str, x: int, y: int, delay: float = 0.3):
    _adb(device, "shell", "input", "tap", str(x), str(y))
    if delay > 0:
        time.sleep(delay)


def _keyevent(device: str, code: int, delay: float = 0.2):
    _adb(device, "shell", "input", "keyevent", str(code))
    if delay > 0:
        time.sleep(delay)


def _type(device: str, text: str):
    _adb(device, "shell", "input", "text", text)


def _screen(device: str):
    return device_capture_screen(device)


# ===========================================================================
# IMAGE DETECTION FUNCTIONS (Fast Flow Real-Time Vision)
# ===========================================================================

def check_age_popup(img):
    if img is None or float(img.mean()) > 180:
        return False
    # ตรวจปุ่ม Confirm สีส้ม (x: 500..780, y: 360..450) และการ์ดสีขาว
    roi_btn = img[360:450, 500:780]
    mask_btn = (roi_btn[:, :, 2] > 200) & (roi_btn[:, :, 1] > 80) & (roi_btn[:, :, 1] < 150) & (roi_btn[:, :, 0] < 80)
    roi_card = img[260:350, 500:780]
    return mask_btn.sum() > 2000 and float(roi_card.mean()) > 220


def check_tos_popup(img):
    if img is None or float(img.mean()) > 180:
        return False
    roi_card = img[260:350, 500:780]
    roi_btn = img[360:450, 500:780]
    mask_orange = (roi_btn[:, :, 2] > 200) & (roi_btn[:, :, 1] > 80) & (roi_btn[:, :, 1] < 150) & (roi_btn[:, :, 0] < 80)
    return float(roi_card.mean()) > 220 and mask_orange.sum() < 500 and float(roi_btn.mean()) > 200


def check_devplay_login_btn(img):
    if img is None:
        return False
    # ตรวจปุ่ม DevPlay Login สีส้ม (x: 400..650, y: 580..660)
    roi = img[580:660, 400:650]
    mask = (roi[:, :, 2] > 180) & (roi[:, :, 1] > 70) & (roi[:, :, 1] < 160) & (roi[:, :, 0] < 80)
    return mask.sum() > 4000


def check_email_signin_btn(img):
    if img is None:
        return False
    # ตรวจปุ่ม 'Sign in with E-mail' สีส้ม (x: 650..950, y: 350..430)
    roi = img[350:430, 650:950]
    mask = (roi[:, :, 2] > 200) & (roi[:, :, 1] > 80) & (roi[:, :, 1] < 150) & (roi[:, :, 0] < 80)
    return mask.sum() > 2500


def check_email_input_page(img):
    if img is None:
        return False
    # ตรวจสอบว่าหน้าจอ WebView กรอกอีเมลโหลดเสร็จสมบูรณ์ 100%
    # 1. ข้อความหัวเรื่อง 'Please enter your e-mail address' (y: 110..150, x: 410..750)
    roi_title = img[110:150, 410:750]
    gray_title = cv2.cvtColor(roi_title, cv2.COLOR_BGR2GRAY)
    dark_title = int((gray_title < 100).sum())

    # 2. หัวเว็บ 'CookieRun' (y: 50..80, x: 580..700)
    roi_header = img[50:80, 580:700]
    gray_header = cv2.cvtColor(roi_header, cv2.COLOR_BGR2GRAY)
    dark_header = int((gray_header < 100).sum())

    return 300 < dark_title < 2500 and dark_header > 200


def check_password_input_page(img):
    if img is None:
        return False
    # หน้ากรอกรหัสผ่าน (มี 2 ช่อง + checkbox agree + Cloudflare)
    roi_title = img[100:160, 410:750]
    gray_title = cv2.cvtColor(roi_title, cv2.COLOR_BGR2GRAY)
    dark_title = int((gray_title < 100).sum())
    roi_box2 = img[240:290, 411:869]
    gray_box2 = cv2.cvtColor(roi_box2, cv2.COLOR_BGR2GRAY)
    box2_border = int(((gray_box2 < 210) & (gray_box2 > 150)).sum())
    return dark_title > 2500 or box2_border > 200


def check_cloudflare_green(img):
    # กล่อง checkbox Cloudflare ที่ (x: 410..460, y: 385..425)
    roi = img[385:425, 410:460]
    mask = (roi[:, :, 1] > 120) & (roi[:, :, 0] < 80) & (roi[:, :, 2] < 80)
    return mask.sum() > 50


def check_intro_video(img):
    if img is None:
        return False
    br = float(img.mean())
    return 20 < br < 170


def check_quit_watching_popup(img):
    if img is None:
        return False
    # ตรวจปุ่ม Confirm สีเขียวบนหน้าต่าง 'Quit watching?' อยู่ฝั่งขวา (x: 650..930, y: 410..510)
    roi_c = img[410:510, 650:930]
    hsv_c = cv2.cvtColor(roi_c, cv2.COLOR_BGR2HSV)
    mask_c = cv2.inRange(hsv_c, (35, 100, 100), (85, 255, 255))
    # ตรวจปุ่ม Cancel สีเทาบนหน้าต่าง 'Quit watching?' อยู่ฝั่งซ้าย (x: 350..550, y: 410..510)
    roi_cancel = img[410:510, 350:550]
    mask_cancel = (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 15) & \
                  (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 15) & \
                  (roi_cancel[:, :, 0] > 90) & (roi_cancel[:, :, 0] < 160)
    return bool(mask_c.sum() > 2000 and mask_cancel.sum() > 2000)


def check_hi_there_popup(img):
    if img is None:
        return False
    # ตรวจปุ่ม Confirm สีเขียวบนหน้าต่าง 'Hi there!' อยู่ตรงกลางจอ (x: 550..700, y: 430..510)
    roi = img[430:510, 550:700]
    mask = (roi[:, :, 1] > 130) & (roi[:, :, 0] < 90) & (roi[:, :, 1] > roi[:, :, 0] * 1.5)
    # ต้องไม่มีปุ่ม Cancel สีเทาฝั่งซ้าย (ไม่ใช่ Quit watching?)
    roi_cancel = img[410:510, 350:550]
    mask_cancel = (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 15) & \
                  (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 15) & \
                  (roi_cancel[:, :, 0] > 90) & (roi_cancel[:, :, 0] < 160)
    return bool(mask.sum() > 3000 and mask_cancel.sum() < 1000)


def check_in_tutorial_room(img):
    if img is None:
        return False
    if check_quit_watching_popup(img) or check_hi_there_popup(img):
        return False
    # ตรวจปุ่ม Jump (x: 50..230, y: 580..710)
    roi_jump = img[580:710, 50:230]
    return float(roi_jump.mean()) > 25


def is_tutorial_pause_menu(img):
    """ตรวจว่าเปิด Pause Menu ขึ้นมาจริงหรือยัง (Continue เขียวบน + Quit ฟ้าล่าง)"""
    if img is None:
        return False
    c_roi = img[380:460, 480:780]
    cyan = (c_roi[:, :, 0] > 120) & (c_roi[:, :, 1] > 120) & (c_roi[:, :, 2] < 70)
    g_roi = img[220:300, 480:780]
    green = (g_roi[:, :, 1] > 140) & (g_roi[:, :, 2] > 140) & (g_roi[:, :, 0] < 80)
    return cyan.sum() > 1000 and green.sum() > 1000


def is_tutorial_confirm_quit_dialog(img):
    """ตรวจว่าเปิดหน้าต่าง 'Quit the tutorial?' ขึ้นมาจริงหรือยัง (Quit ฟ้าบน + Cancel เทาล่าง)"""
    if img is None:
        return False
    c_roi = img[340:420, 480:780]
    cyan = (c_roi[:, :, 0] > 120) & (c_roi[:, :, 1] > 120) & (c_roi[:, :, 2] < 70)
    g_roi = img[490:560, 480:780]
    grey = (np.abs(g_roi[:, :, 0].astype(int) - g_roi[:, :, 1].astype(int)) < 15) & \
           (np.abs(g_roi[:, :, 1].astype(int) - g_roi[:, :, 2].astype(int)) < 15) & \
           (g_roi[:, :, 0] > 100) & (g_roi[:, :, 0] < 180)
    return cyan.sum() > 1000 and grey.sum() > 1000


def check_select_mode_popup(img):
    """ตรวจจับหน้าต่าง 'Select a Mode' (Party Run) ที่มีริบบิ้นม่วงบน และปุ่ม X เทากลมที่ (1215, 95)"""
    if img is None:
        return False
    roi_title = img[60:125, 400:880]
    purple = (roi_title[:, :, 0] > 110) & (roi_title[:, :, 2] > 90) & (roi_title[:, :, 1] < 70)
    roi_x = img[65:125, 1180:1250]
    white_x = (roi_x[:, :, 0] > 200) & (roi_x[:, :, 1] > 200) & (roi_x[:, :, 2] > 200)
    return purple.sum() > 600 and white_x.sum() > 30


def check_banner_or_news_popup(img):
    """ตรวจจับหน้าต่างข่าวสาร/ประกาศ/แนะนำฟีเจอร์ทั้งหมด ที่มีปุ่ม X เทากลมที่ (1125, 75)"""
    if img is None:
        return False
    btn_roi = img[50:95, 1105:1145]
    grey = (np.abs(btn_roi[:, :, 0].astype(int) - btn_roi[:, :, 1].astype(int)) < 15) & \
           (np.abs(btn_roi[:, :, 1].astype(int) - btn_roi[:, :, 2].astype(int)) < 15) & \
           (btn_roi[:, :, 0] > 90) & (btn_roi[:, :, 0] < 170)
    white = (btn_roi[:, :, 0] > 200) & (btn_roi[:, :, 1] > 200) & (btn_roi[:, :, 2] > 200)
    return bool(grey.sum() > 400 and white.sum() > 100)


def check_set_nickname_popup(img):
    if img is None:
        return False
    if check_quit_watching_popup(img) or check_hi_there_popup(img):
        return False

    # 1. เช็คแถบพิมพ์ Android IME บาร์สีขาวด้านบน (Enter your nickname!)
    top_bar = img[35:85, 20:1260]
    if top_bar.mean() > 180:
        return True

    # 2. เช็คตัวการ์ดหน้าต่าง Set Nickname กลางจอ (x: 450..830, y: 200..340)
    card = img[200:340, 450:830]
    b, g, r = card[:, :, 0], card[:, :, 1], card[:, :, 2]
    is_grey_card = (np.abs(b.astype(int) - g.astype(int)) < 20) & \
                   (np.abs(g.astype(int) - r.astype(int)) < 20) & \
                   (g > 70) & (g < 230)

    # 3. เช็คปุ่ม Confirm เดี่ยวตรงกลาง (x: 550..720, y: 440..530)
    btn = img[440:530, 550:720]
    btn_g = btn[:, :, 1]
    btn_b = btn[:, :, 0]
    is_btn = (btn_g.astype(int) - btn_b.astype(int) > 10)

    # 4. ต้องไม่มีปุ่ม Cancel สีเทาฝั่งซ้าย (ถ้ามีแสดงว่าเป็น Quit watching?)
    roi_cancel = img[440:530, 350:520]
    mask_cancel = (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 15) & \
                  (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 15) & \
                  (roi_cancel[:, :, 0] > 90) & (roi_cancel[:, :, 0] < 160)
    has_cancel = mask_cancel.sum() > 2000

    return bool(is_grey_card.sum() > 20000 and is_btn.sum() > 2000 and not has_cancel)


def check_inviting_player_popup(img):
    if img is None:
        return False
    # ปุ่ม Confirm สีเขียวบนหน้าต่าง Inviting player (x: 550..720, y: 480..580)
    roi = img[480:580, 550:720]
    mask = (roi[:, :, 1] > 150) & (roi[:, :, 0] < 70) & (roi[:, :, 2] > 100)
    return mask.sum() > 2500


def generate_random_nickname():
    """bot + ชื่อสุ่ม (คำหรือตัวอักษร 2-3 ตัว) + ตัวเลขสุ่ม 4-6 ตัว"""
    words = [
        "run", "fast", "dash", "star", "joy", "hero", "pro", "sky",
        "jump", "neo", "max", "ice", "cool", "luck", "ace", "pop",
        "fly", "fox", "cat", "sun", "red", "gem", "win", "bee"
    ]
    if random.random() < 0.7:
        rand_name = random.choice(words)
    else:
        rand_name = "".join(random.choices(string.ascii_lowercase, k=random.randint(2, 3)))

    digits = "".join(random.choices(string.digits, k=random.randint(4, 6)))
    nick = f"bot{rand_name}{digits}"
    if len(nick) > 12:
        nick = nick[:12]
    return nick


_rnd_nickname = generate_random_nickname


def _rnd_email():
    return f"user_{int(time.time())}_{random.randint(1000, 9999)}@gmail.com"


def _rnd_password():
    return f"kP9#mX2${random.randint(100, 999)}!qR5@"


_DEEPLINK_CACHE: dict = {}

def _resolve_deeplink(url: str) -> str:
    """แกะหา URL ปลายทางและ Custom Scheme จาก AppsFlyer OneLink (Fallback)"""
    if not url:
        return ""
    if url.startswith("devsisters-crg://"):
        return url
    if url in _DEEPLINK_CACHE:
        return _DEEPLINK_CACHE[url]
    try:
        import requests, re
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36"
        }
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=8)
        for m in re.finditer(r'(devsisters-crg://[^\'"\s<>]+)', r.text):
            link = m.group(1)
            if link.startswith("devsisters-crg://"):
                _DEEPLINK_CACHE[url] = link
                return link
        m2 = re.search(r"var (?:app_link|af_dp)\s*=\s*['\"]([^'\"]+)['\"]", r.text)
        if m2 and m2.group(1).startswith("devsisters-crg://"):
            _DEEPLINK_CACHE[url] = m2.group(1)
            return m2.group(1)
    except Exception:
        pass
    return ""


# ===========================================================================
# HEART FARMER CLASS (Full Fast Flow Integration)
# ===========================================================================

class HeartFarmer:
    """
    Automates heart farming loop using Fast Flow Real-Time Vision:
      clear data -> register Devplay -> add friend -> send heart -> repeat
    """

    def __init__(self, device: str, invite_url: str = INVITE_URL, max_rounds: int = 0):
        self.device = device
        self.emu_name = resolve_emulator_name(device) if "resolve_emulator_name" in globals() else ""
        self.invite_url = invite_url or INVITE_URL
        self.max_rounds = max_rounds   # 0 = infinite
        self.rounds = 0
        self.success_count = 0
        self.current_step = "เตรียมเริ่มทำงาน"
        self.start_time = time.time()
        self.stopped = False
        self.heart_sent = False

    def stop(self):
        self.stopped = True
        self.current_step = "หยุดการทำงานทันทีแล้ว"
        self._log("สั่งหยุดการทำงานทันที (Stopping requested...)")
        try:
            self.adb('shell', 'am', 'force-stop', PACKAGE, timeout=5)
        except Exception:
            pass

    def _log(self, msg: str):
        display_device = f"{self.emu_name} ({self.device})" if getattr(self, "emu_name", "") else self.device
        full_line = f"[{time.strftime('%H:%M:%S')}][HeartFarmer][{display_device}] {msg}"
        print(full_line, flush=True)

        try:
            from bot_engine import engine_manager
            eng = engine_manager.get_or_create_engine(self.device)
            timestamp = time.strftime("%H:%M:%S")
            level = "farmer"
            msg_lower = msg.lower()
            if any(x in msg for x in ("❌", "error", "fail", "ล้มเหลว", "ไม่สำเร็จ")):
                level = "error"
            elif any(x in msg for x in ("⚠️", "warning", "warn", "เตือน")):
                level = "warning"
            elif any(x in msg for x in ("✅", "success", "สำเร็จ", "🎉", "GREEN", "⚡")):
                level = "success"

            log_entry = {
                "time": timestamp,
                "timestamp": timestamp,
                "message": f"[HeartFarmer][{display_device}] {msg}",
                "level": level,
                "device": self.device,
                "target": self.device,
            }
            eng.logs.append(log_entry)

            loop = eng.loop or getattr(engine_manager, "loop", None)
            if loop and eng.ws_subscribers:
                for q in list(eng.ws_subscribers):
                    try:
                        loop.call_soon_threadsafe(q.put_nowait, log_entry)
                    except Exception:
                        pass

            if engine_manager:
                engine_manager.record_and_broadcast_log(log_entry)
        except Exception:
            pass

    def adb(self, *args, timeout: int = 15):
        return _adb(self.device, *args, timeout=timeout)

    def tap(self, x: int, y: int, delay: float = 0.3):
        _tap(self.device, x, y, delay=delay)

    def keyevent(self, code: int, delay: float = 0.2):
        _keyevent(self.device, code, delay=delay)

    def type_text(self, text: str):
        _type(self.device, text)

    def screenshot(self):
        return _screen(self.device)

    def wait_until(self, condition_fn, timeout: int = 30, interval: float = 0.35, desc: str = ""):
        """วนลูปตรวจสอบภาพหน้าจอแบบความเร็วสูง เจอแล้วทำต่อทันที"""
        if desc:
            self._log(f"  [รอ] {desc} (timeout {timeout}s)...")
        deadline = time.time() + timeout
        t0 = time.time()
        while time.time() < deadline:
            if self.stopped:
                return None, None
            img = self.screenshot()
            if img is not None:
                res = condition_fn(img)
                if res:
                    elapsed = time.time() - t0
                    self._log(f"  ⚡ เจอ {desc} ใน {elapsed:.1f}s!")
                    return res, img
            time.sleep(interval)
        self._log(f"  ⚠️ Timeout รอ {desc}")
        return None, None

    def clear_all_lobby_popups(self, max_wait: int = 35, desc: str = "Lobby") -> bool:
        """วนลูปตรวจจับและปิด Popup ทุกชนิด (Congratulations, Welcome Rewards, Banners, News, Select a Mode) จนกว่า Lobby จะสะอาดจริง 100%"""
        self._log(f"  -> เริ่มเคลียร์ Popup ทั้งหมด ({desc}) ตรวจจออย่างรัดกุม...")
        t_end = time.time() + max_wait
        while time.time() < t_end:
            if self.stopped:
                return False
            img = self.screenshot()
            if img is None:
                time.sleep(0.5)
                continue

            # 1. ตรวจสอบหน้าต่างข่าวสาร / แบนเนอร์ (X กลมสีเทา 1125, 72)
            if check_banner_or_news_popup(img):
                self._log("  ⚡ พบหน้าต่างข่าวสาร/ประกาศ -> กดปิด X (1125, 72)...")
                self.tap(1125, 72, delay=1.2)
                continue

            # 2. ตรวจสอบหน้าต่าง Select a Mode (X สีม่วง 1215, 95)
            if check_select_mode_popup(img):
                self._log("  ⚡ พบหน้าต่าง Select a Mode -> กดปิด X (1215, 95)...")
                self.tap(1215, 95, delay=1.2)
                continue

            # 3. ตรวจสอบปุ่ม Confirm สีเขียวกลางจอ (Congratulations / Daily Check-in / Welcome Rewards)
            roi_center = img[440:680, 480:710]
            mask_c = ((roi_center[:, :, 1] > 140) & (roi_center[:, :, 0] < 80) & (roi_center[:, :, 2] > 90)).astype(np.uint8)
            n_c, _, stats_c, centroids_c = cv2.connectedComponentsWithStats(mask_c)
            found_center = None
            for k in range(1, n_c):
                area = stats_c[k, cv2.CC_STAT_AREA]
                cx = int(centroids_c[k][0]) + 480
                cy = int(centroids_c[k][1]) + 440
                if area > 3000 and cx < 720:
                    found_center = (cx, cy)
                    break

            if found_center:
                self._log(f"  -> พบ Popup รางวัล/ยินดีต้อนรับ กลางจอ -> กด Confirm {found_center}...")
                self.tap(found_center[0], found_center[1], delay=1.2)
                continue

            # 4. ตรวจสอบว่าถึงหน้า Lobby มีปุ่ม Play! สีเขียวขวาล่าง
            roi_play = img[580:710, 750:950]
            mask_play = ((roi_play[:, :, 1] > 150) & (roi_play[:, :, 0] < 70) & (roi_play[:, :, 2] > 90)).astype(np.uint8)
            if mask_play.sum() > 3000:
                time.sleep(1.5)
                chk = self.screenshot()
                if chk is not None:
                    chk_news = check_banner_or_news_popup(chk)
                    chk_mode = check_select_mode_popup(chk)
                    chk_c = False
                    c_chk_roi = chk[440:680, 480:710]
                    c_chk_mask = ((c_chk_roi[:, :, 1] > 140) & (c_chk_roi[:, :, 0] < 80) & (c_chk_roi[:, :, 2] > 90)).astype(np.uint8)
                    n_chk, _, s_chk, cnts_chk = cv2.connectedComponentsWithStats(c_chk_mask)
                    for k in range(1, n_chk):
                        if s_chk[k, cv2.CC_STAT_AREA] > 3000 and (int(cnts_chk[k][0]) + 480 < 720):
                            chk_c = True
                            break
                    if not chk_news and not chk_mode and not chk_c:
                        self._log("  ⚡ ยืนยันหน้า Lobby เรียบร้อย สะอาด 100%!")
                        return True
            time.sleep(1.0)
        return False

    def handle_step_failure(self, step_name: str, details: str = ""):
        self.current_step = f"ล้มเหลว ({step_name}: {details})"
        self._log(f"❌ [ล้มเหลว] {step_name} ไม่สำเร็จ! รายละเอียด: {details}")
        try:
            img = self.screenshot()
            record_game_error(
                device_serial=self.device,
                reason=f"HeartFarmer: {step_name} ล้มเหลว",
                details=f"รอบที่ #{self.rounds} - {details}",
                screen_img=img,
                action_taken="เริ่มใหม่ตั้งแต่สเต็ปแรก (Step 0)"
            )
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # STEP METHODS (1:1 with fast_flow.py)
    # -----------------------------------------------------------------------

    def step0_clear_and_launch(self) -> bool:
        self._log("\n[STEP 0] ล้างข้อมูลล็อกอิน/แคช (เก็บแพตช์เกม) + ตรวจสิทธิ์ Root + เปิดเกม")
        self.adb('shell', 'am', 'force-stop', PACKAGE)
        time.sleep(0.5)

        # 1. ตรวจสอบและเปิดสิทธิ์ Root บน ADB ถ้ายังไม่ได้เป็น Root
        try:
            is_root = ensure_adb_root(self.device)
            if not is_root:
                self._log("  ⚠️ [Root Check] ไม่สามารถขอสิทธิ์ ADB Root ได้ จะพยายามใช้คำสั่ง su แทน")
        except Exception as e:
            self._log(f"  [Root Check] ข้อผิดพลาด: {e}")

        # 2. ปลดล็อกสิทธิ์ su ชั่วคราว (เผื่อเครื่องที่มี su โดน chmod 000 ซ่อนไว้)
        try:
            self.adb('shell', 'chmod', '755', '/system/xbin/su', timeout=2)
            self.adb('shell', 'chmod', '755', '/system/bin/su', timeout=2)
        except Exception:
            pass

        # 3. ล้างไฟล์ข้อมูลล็อกอินและแคช (เก็บโฟลเดอร์ files ซึ่งเป็นแพตช์เกมไว้)
        rm_cmd = (f"rm -rf /data/data/{PACKAGE}/shared_prefs "
                  f"/data/data/{PACKAGE}/databases "
                  f"/data/data/{PACKAGE}/cache "
                  f"/data/data/{PACKAGE}/code_cache "
                  f"/data/data/{PACKAGE}/app_webview "
                  f"/sdcard/Android/data/{PACKAGE}/cache")
        self.adb('shell', rm_cmd)
        self.adb('shell', 'su', '-c', f"'{rm_cmd}'")

        # 4. ตรวจสอบยืนยันว่าโฟลเดอร์ล็อกอิน (shared_prefs) ถูกลบออกจริงหรือไม่
        check_sp = self.adb('shell', f"ls -d /data/data/{PACKAGE}/shared_prefs 2>/dev/null")
        if check_sp and "shared_prefs" in (check_sp.stdout or ""):
            # พยายามลบเจาะจงไฟล์ข้างในโฟลเดอร์อีกรอบ
            self.adb('shell', f"rm -rf /data/data/{PACKAGE}/shared_prefs/* /data/data/{PACKAGE}/databases/*")
            self.adb('shell', 'su', '-c', f"'rm -rf /data/data/{PACKAGE}/shared_prefs/* /data/data/{PACKAGE}/databases/*'")
            recheck = self.adb('shell', f"ls /data/data/{PACKAGE}/shared_prefs 2>/dev/null")
            if recheck and recheck.stdout.strip():
                self._log("  ⚠️ [ล้างข้อมูล] พบไฟล์ใน shared_prefs ตกค้าง (กรุณาเปิดสิทธิ์ Root ในโปรแกรมจำลอง)")
            else:
                self._log("  ✅ [ล้างข้อมูล] ล้างไฟล์ข้อมูลล็อกอินสำเร็จเรียบร้อย")
        else:
            self._log("  ✅ [ล้างข้อมูล] ล้างข้อมูลล็อกอินสำเร็จสมบูรณ์ (shared_prefs ถูกลบเรียบร้อย)")

        # 5. ซ่อน su binary (ถ้ามี) ไม่ให้เกมตรวจจับ
        try:
            self.adb('shell', 'chmod', '000', '/system/xbin/su', timeout=2)
            self.adb('shell', 'chmod', '000', '/system/bin/su', timeout=2)
        except Exception:
            pass

        # 6. เปิดตัวเกม CookieRun Classic
        self.adb('shell', 'monkey', '-p', PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1')
        time.sleep(2.0)
        return True

    def step1_login_email(self) -> bool:
        # STEP 1a: Age Selection
        self._log("[STEP 1a] ตรวจจับหน้าต่าง Age Selection")
        ok, _ = self.wait_until(check_age_popup, timeout=25, desc="Age Popup")
        if ok:
            self.tap(770, 370, delay=0.4)
            self.tap(640, 406, delay=1.0)

        if self.stopped: return False

        # STEP 1b: TOS
        self._log("[STEP 1b] ตรวจจับหน้าต่าง Terms of Service")
        ok, _ = self.wait_until(check_tos_popup, timeout=12, desc="TOS Popup")
        if ok:
            self.tap(801, 443, delay=1.0)

        if self.stopped: return False

        # STEP 1c: DevPlay Login Button
        self._log("[STEP 1c] ตรวจจับปุ่ม DevPlay Login บน Title Screen")
        ok, _ = self.wait_until(check_devplay_login_btn, timeout=15, desc="DevPlay Login Button")
        if ok:
            self.tap(520, 622, delay=1.2)

        if self.stopped: return False

        # STEP 1d: Sign in with E-mail
        self._log("[STEP 1d] ตรวจจับปุ่ม Sign in with E-mail")
        ok, _ = self.wait_until(check_email_signin_btn, timeout=12, desc="Sign in with E-mail Button")
        if ok:
            self.tap(795, 391, delay=1.2)
            return True

        return True

    def step2_enter_email(self, email: Optional[str] = None) -> bool:
        self._log("[STEP 2] ตรวจจับหน้าจอกรอก Email (รอโหลดเสร็จ 100%) แล้วกรอก Email สุ่ม")
        email_deadline = time.time() + 35
        email_ready = False
        retries = 0
        while time.time() < email_deadline:
            if self.stopped: return False
            img = self.screenshot()
            if check_email_input_page(img):
                email_ready = True
                self._log("  ⚡ เจอหน้าจอกรอก Email โหลดเสร็จสมบูรณ์!")
                break
            retries += 1
            if retries % 6 == 0:
                if check_email_signin_btn(img):
                    self._log("  -> หน้าเว็บยังไม่ขึ้น ลองแตะ Sign in with E-mail ซ้ำ...")
                    self.tap(795, 391, delay=0.5)
                elif check_devplay_login_btn(img):
                    self._log("  -> หน้าเว็บยังไม่ขึ้น ลองแตะ DevPlay Login ซ้ำ...")
                    self.tap(520, 622, delay=0.5)
            time.sleep(0.5)

        if not email_ready:
            self._log("❌ ไม่สามารถโหลดหน้ากรอกอีเมลได้ภายในเวลา!")
            return False

        time.sleep(0.5)
        curr_email = email or _rnd_email()
        self._log(f"  -> หน้าจอกรอกอีเมลพร้อมแล้ว! สุ่ม Email: {curr_email}")
        self.tap(640, 210, delay=0.5)
        self.type_text(curr_email)
        self.keyevent(66, delay=0.3)
        self.keyevent(111, delay=0.3)
        time.sleep(0.3)
        self.tap(638, 662, delay=1.2)
        return True

    def step3_enter_password(self, password: Optional[str] = None) -> bool:
        self._log("[STEP 3] กรอก Password สุ่ม 2 ช่อง + ติ๊ก Agree")
        ok, _ = self.wait_until(check_password_input_page, timeout=12, desc="Password Input Page")
        if not ok and not check_password_input_page(self.screenshot()):
            self._log("❌ หน้ากรอกรหัสผ่านไม่ปรากฏ!")
            return False

        curr_pwd = password or _rnd_password()
        # ช่อง 1
        self.tap(521, 207, delay=0.3)
        self.type_text(curr_pwd)
        # ช่อง 2
        self.tap(521, 260, delay=0.3)
        self.type_text(curr_pwd)
        self.keyevent(111, delay=0.3)
        # ติ๊ก Agree
        self.tap(423, 328, delay=0.5)
        return True

    def step4_register(self) -> bool:
        self._log("[STEP 4] รอ Cloudflare เขียว + กด Register")
        cf_deadline = time.time() + 60
        taps = 0
        while time.time() < cf_deadline:
            if self.stopped: return False
            img = self.screenshot()
            if img is not None and check_cloudflare_green(img):
                self._log("  ⚡ Cloudflare = GREEN!")
                break
            taps += 1
            if taps % 4 == 0:
                self.tap(434, 404, delay=0.2)
            time.sleep(0.8)

        self.tap(638, 662, delay=1.0)
        return True

    def step5_handle_tutorial(self) -> bool:
        self._log("[STEP 5] ตรวจจับหน้าจอเพื่อข้ามวิดีโอ & คัตซีน (รอดูจอและเช็คจังหวะ ไม่กดเร็ว)")
        self._log("  -> รอหน้าเว็บ DevPlay ปิด และรอตัวเกมโหลดเข้าสู่อนิเมชั่นอินโทร (4 วินาที)...")
        time.sleep(4.0)

        video_deadline = time.time() + 60
        last_tap = 0
        while time.time() < video_deadline:
            if self.stopped: return False
            img = self.screenshot()
            if img is None:
                time.sleep(0.5)
                continue

            # 1. หน้าต่าง Quit watching? (ปุ่มเขียว Confirm อยู่ที่ 793, 456)
            if check_quit_watching_popup(img):
                self._log("  ⚡ เจอ Quit watching? -> กด Confirm (793, 456)...")
                self.tap(793, 456, delay=1.2)
                for _ in range(5):
                    time.sleep(1.2)
                    chk = self.screenshot()
                    if not check_quit_watching_popup(chk):
                        self._log("  ⚡ ปิดหน้าต่าง Quit watching? สำเร็จจริง 100%!")
                        break
                    self.tap(793, 456, delay=1.0)
                continue

            # 2. หน้าต่าง 'Hi there! New to the game?' (ปุ่มเขียว Confirm อยู่ที่ 640, 464)
            if check_hi_there_popup(img):
                self._log("  ⚡ เจอ Hi there! -> กด Confirm (640, 464)...")
                self.tap(640, 464, delay=1.5)
                for _ in range(5):
                    time.sleep(1.2)
                    chk = self.screenshot()
                    if not check_hi_there_popup(chk):
                        self._log("  ⚡ ปิดหน้าต่าง 'Hi there!' สำเร็จจริง 100%!")
                        break
                    self.tap(640, 464, delay=1.0)
                break

            # 3. ถึงห้อง Tutorial หรือเปิด Pause menu ขึ้นมาแล้ว
            if check_in_tutorial_room(img) or is_tutorial_pause_menu(img) or is_tutorial_confirm_quit_dialog(img):
                self._log("  ⚡ ถึงห้อง Tutorial เรียบร้อย!")
                break

            # 4. หากยังอยู่ในวิดีโอ -> แตะกลางจอทุก 2.5วิ
            now = time.time()
            if now - last_tap > 2.5:
                self._log("  -> อยู่ในอนิเมชั่น: แตะกลางจอ 1 ครั้งเพื่อเรียกหน้าต่าง Quit watching?...")
                self.tap(640, 360, delay=0.3)
                last_tap = now

            time.sleep(1.5)

        # STEP 5d: ออกจาก Tutorial
        self._log("[STEP 5d] ตรวจจับสถานะห้อง Tutorial ทุกๆ 1.2วิ -> ออกทันที พร้อมตรวจสอบว่าออกจริง")
        tut_deadline = time.time() + 45
        exited_tutorial = False
        last_pause_tap = 0
        while time.time() < tut_deadline:
            if self.stopped: return False
            img = self.screenshot()
            if img is None:
                time.sleep(0.5)
                continue

            if check_quit_watching_popup(img):
                self._log("  ⚡ ตรวจพบ Quit watching? -> กด Confirm (793, 456)...")
                self.tap(793, 456, delay=1.2)
                continue

            if check_hi_there_popup(img):
                self._log("  ⚡ ตรวจพบ Hi there! -> กด Confirm (640, 464)...")
                self.tap(640, 464, delay=1.2)
                continue

            # 1. ถึงหน้าต่างตั้งชื่อเล่นแล้ว
            if check_set_nickname_popup(img):
                self._log("  ⚡ ออกจากห้อง Tutorial สำเร็จ 100%! ถึงหน้าต่างตั้งชื่อเล่นแล้ว")
                exited_tutorial = True
                break

            # 2. Confirm Quit Dialog
            if is_tutorial_confirm_quit_dialog(img):
                self._log("  ⚡ ตรวจพบ Confirm Quit Dialog -> แตะปุ่ม Quit (631, 378)...")
                self.tap(631, 378, delay=0.8)
                for _ in range(5):
                    time.sleep(1.0)
                    chk = self.screenshot()
                    if not is_tutorial_confirm_quit_dialog(chk):
                        self._log("  ⚡ ออกจาก Tutorial สำเร็จจริง!")
                        break
                    self.tap(631, 378, delay=0.8)
                continue

            # 3. Pause Menu
            if is_tutorial_pause_menu(img):
                self._log("  ⚡ ตรวจพบ Pause Menu -> แตะปุ่ม Quit (631, 423)...")
                self.tap(631, 423, delay=0.8)
                for _ in range(5):
                    time.sleep(1.0)
                    chk = self.screenshot()
                    if is_tutorial_confirm_quit_dialog(chk) or check_set_nickname_popup(chk):
                        self._log("  ⚡ เปิดหน้าต่าง Confirm Quit สำเร็จจริง!")
                        break
                    self.tap(631, 423, delay=0.8)
                continue

            # 4. กำลังวิ่งอยู่ใน Tutorial -> แตะจอเคลียร์กล่อง + แตะ Pause
            now = time.time()
            if now - last_pause_tap > 1.5:
                self.tap(640, 360, delay=0.3)
                self.tap(1198, 38, delay=0.5)
                last_pause_tap = now

            time.sleep(1.2)

        if not exited_tutorial:
            self._log("  ❌ ออกจากห้อง Tutorial ไม่สำเร็จ!")
            return False
        return True

    def step6_set_nickname(self, nickname: Optional[str] = None) -> bool:
        self._log("[STEP 6] ตั้งชื่อเล่นสุ่ม 'bot' + ชื่อสุ่ม + ตัวเลข 4-6 หลัก")
        ok, _ = self.wait_until(check_set_nickname_popup, timeout=15, desc="Set Nickname Popup")
        nick = nickname or generate_random_nickname()
        self._log(f"  -> สุ่มชื่อ: {nick}")
        self.tap(638, 385, delay=0.8)
        for _ in range(15):
            self.keyevent(67, delay=0.04)
        self.type_text(nick)
        time.sleep(0.5)
        self.keyevent(66, delay=0.3)
        self.keyevent(111, delay=0.5)
        time.sleep(1.0)
        self._log("  -> แตะปุ่ม Confirm (639, 487) ตั้งชื่อ...")
        self.tap(639, 487, delay=1.2)
        for _ in range(6):
            time.sleep(1.0)
            chk = self.screenshot()
            if not check_set_nickname_popup(chk):
                self._log("  ⚡ ตั้งชื่อเล่นสำเร็จ หน้าต่างปิดเรียบร้อย 100%!")
                break
            self.tap(639, 487, delay=0.8)

        # STEP 6b: เคลียร์ Popup ทั้งหมดก่อนเปิด OneLink
        self._log("[STEP 6b] เคลียร์ Popup รางวัลและข่าวสารทั้งหมดจนถึง Lobby")
        self.clear_all_lobby_popups(max_wait=35, desc="Step 6b เคลียร์ก่อนเปิด OneLink")
        return True

    def step7_open_invite_link(self) -> bool:
        self._log(f"[STEP 7] เปิด OneLink ใน Browser -> รับเพื่อน ({self.invite_url})")
        res = self.adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', self.invite_url,
                       '-n', 'com.android.chromium/org.chromium.chrome.browser.ChromeTabbedActivity', timeout=10)
        if res and res.returncode != 0:
            self.adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', self.invite_url, timeout=10)
        time.sleep(1.5)
        self.adb('shell', 'am', 'start', '-n', f'{PACKAGE}/com.devsisters.CookieRunForKakao.OvenbreakX', timeout=10)
        return True

    def step8_confirm_friend_added(self) -> bool:
        self._log("[STEP 8] ยืนยันเพิ่มเพื่อน + เคลียร์ Welcome Rewards + เช็ค Friends ซิงก์ข้อมูล")
        ok, _ = self.wait_until(check_inviting_player_popup, timeout=8, desc="Inviting Player Popup")
        if ok:
            self._log("  ⚡ พบหน้าต่าง Inviting Player -> กด Confirm (639, 537)")
            self.tap(639, 537, delay=1.2)
        else:
            self._log("  ⚠️ ไม่พบหน้าต่าง Inviting Player (อาจตอบรับออโต้แล้ว)")

        # เคลียร์ Popup Welcome Rewards ทั้งหมดที่เด้งตามมา
        self.clear_all_lobby_popups(max_wait=20, desc="Step 8 เคลียร์ Welcome Rewards หลังรับเพื่อน")

        # ดีเลย์ 1 วิ แล้วกดเช็คเพื่อนทันทีตามคำสั่ง
        self._log("  -> ดีเลย์ 1 วิ แล้วแตะไอคอน Friends (800, 335) เพื่อเช็ค/ซิงก์เพื่อน...")
        time.sleep(1.0)
        self.tap(800, 335, delay=1.0)

        # รอหน้าต่าง Friends เปิดขึ้นมาจริง
        self._log("  [รอ] หน้าต่าง Friends เปิดขึ้นมาจริง...")
        for _ in range(12):
            if self.stopped: return False
            img_f = self.screenshot()
            if img_f is not None:
                roi_x = img_f[50:90, 990:1030]
                if float(roi_x.mean()) > 100:
                    self._log("  ⚡ หน้าต่าง Friends เปิดขึ้นมาเรียบร้อยแล้ว!")
                    break
            time.sleep(0.5)

        time.sleep(1.5)

        # ปิดหน้าต่าง Friends (1009, 69)
        self._log("  -> กดปิดหน้าต่าง Friends (1009, 69)...")
        self.tap(1009, 69, delay=1.0)

        # รอหน้าต่าง Friends ปิดสนิทจริง
        self._log("  [รอ] หน้าต่าง Friends ปิดสนิทและกลับสู่หน้า Lobby...")
        for _ in range(10):
            if self.stopped: return False
            img_l = self.screenshot()
            if img_l is not None:
                roi_x = img_l[50:90, 990:1030]
                if float(roi_x.mean()) < 80:
                    self._log("  ⚡ หน้าต่าง Friends ปิดเรียบร้อย กลับสู่หน้า Lobby จริง!")
                    break
            time.sleep(0.5)
        time.sleep(1.0)
        return True

    def step9_send_heart_and_exit(self) -> bool:
        self._log("[STEP 9] ส่งหัวใจให้เพื่อนอันดับ 1 (รอตรวจจับปุ่มจริง ไม่กดมั่ว)")
        heart_ready = False
        self._log("  [รอ] ตรวจสอบปุ่มส่งหัวใจ Rank 1 บนหน้า Lobby...")
        for _ in range(15):
            if self.stopped: return False
            img = self.screenshot()
            if img is None:
                time.sleep(0.5)
                continue

            roi_c = img[440:680, 480:710]
            mask_c = ((roi_c[:, :, 1] > 140) & (roi_c[:, :, 0] < 80) & (roi_c[:, :, 2] > 90)).astype(np.uint8)
            if cv2.countNonZero(mask_c) > 3000:
                self.tap(638, 563, delay=1.0)
                continue

            roi_rank1 = img[280:360, 610:700]
            hsv_r1 = cv2.cvtColor(roi_rank1, cv2.COLOR_BGR2HSV)
            mask_green = cv2.inRange(hsv_r1, (35, 100, 100), (85, 255, 255))
            mask_red = ((hsv_r1[:, :, 0] < 10) | (hsv_r1[:, :, 0] > 170)) & (hsv_r1[:, :, 1] > 150) & (hsv_r1[:, :, 2] > 150)

            if mask_green.sum() > 2000 and mask_red.sum() > 50:
                self._log("  ⚡ ตรวจพบปุ่มส่งหัวใจ Rank 1 (Active) บนหน้า Lobby!")
                heart_ready = True
                break
            elif mask_green.sum() > 2000 and mask_red.sum() <= 50:
                self._log("  ✅ ตรวจพบเครื่องหมายถูกสีเขียวที่ Rank 1 (หัวใจถูกส่งแล้ว)!")
                heart_ready = "already_sent"
                break

            time.sleep(0.8)

        if heart_ready is True:
            self._log("  -> แตะปุ่มส่งหัวใจ Rank 1 (655, 320)...")
            self.tap(655, 320, delay=1.0)

            # รอหน้าต่าง 'Send free Life?'
            self._log("  [รอ] หน้าต่าง 'Send free Life?'...")
            for _ in range(10):
                img_c = self.screenshot()
                if img_c is not None:
                    roi_cf = img_c[420:490, 720:860]
                    hsv_cf = cv2.cvtColor(roi_cf, cv2.COLOR_BGR2HSV)
                    mask_cf = cv2.inRange(hsv_cf, (35, 100, 100), (85, 255, 255))
                    if mask_cf.sum() > 2000:
                        self._log("  ⚡ พบหน้าต่าง 'Send free Life?' -> กด Confirm (793, 456)")
                        self.tap(793, 456, delay=1.2)
                        break
                time.sleep(0.4)

            # รอหน้าต่าง 'Message sent!'
            self._log("  [รอ] หน้าต่าง 'Message sent!'...")
            for _ in range(10):
                img_m = self.screenshot()
                if img_m is not None:
                    roi_msg = img_m[420:490, 560:720]
                    hsv_msg = cv2.cvtColor(roi_msg, cv2.COLOR_BGR2HSV)
                    mask_msg = cv2.inRange(hsv_msg, (35, 100, 100), (85, 255, 255))
                    if mask_msg.sum() > 2000:
                        self._log("  ⚡ พบหน้าต่าง 'Message sent!' -> กด Confirm (640, 456)")
                        self.tap(640, 456, delay=1.2)
                        break
                time.sleep(0.4)

            time.sleep(1.0)
            self._log("  🎉 ยืนยัน: ส่งหัวใจให้เพื่อนอันดับ 1 สำเร็จเสร็จสิ้น 100%!")
            self.heart_sent = True
        elif heart_ready == "already_sent":
            self._log("  🎉 ยืนยัน: หัวใจอันดับ 1 อยู่ในสถานะส่งเรียบร้อยแล้ว (เครื่องหมายถูกสีเขียว)!")
            self.heart_sent = True
        else:
            self._log("  ⚠️ ไม่พบบุ่มส่งหัวใจที่ Rank 1 ภายในเวลา")
            return False

        self._log("Force-stop game จบรอบ...")
        self.adb('shell', 'am', 'force-stop', PACKAGE, timeout=10)
        time.sleep(2.0)
        return True

    # -----------------------------------------------------------------------
    # RUN ROUND & MAIN LOOP
    # -----------------------------------------------------------------------

    def run_round(self) -> bool:
        if self.stopped: return False
        self.current_step = "ล้างแคช & เปิดเกมใหม่"
        if not self.step0_clear_and_launch():
            self.handle_step_failure("STEP 0", "ไม่สามารถล้างข้อมูลหรือเปิดเกมได้")
            return False

        if self.stopped: return False
        self.current_step = "ตรวจจับหน้าเข้าสู่ระบบ DevPlay"
        if not self.step1_login_email():
            self.handle_step_failure("STEP 1", "ไม่สามารถผ่านหน้าต่างเริ่มต้นหรือเปิดหน้ากรอกอีเมลได้")
            return False

        if self.stopped: return False
        self.current_step = "สร้างบัญชีสุ่ม & กรอกอีเมล"
        if not self.step2_enter_email():
            self.handle_step_failure("STEP 2", "กรอกอีเมลไม่สำเร็จ หรือไม่ได้หน้าสมัครที่มี 2 ช่อง")
            return False

        if self.stopped: return False
        self.current_step = "กรอกรหัสผ่าน & ยอมรับเงื่อนไข"
        if not self.step3_enter_password():
            self.handle_step_failure("STEP 3", "กรอกรหัสผ่าน 2 ช่องไม่สำเร็จ")
            return False

        if self.stopped: return False
        self.current_step = "ตรวจจับ Cloudflare & สมัครสมาชิก"
        if not self.step4_register():
            self.handle_step_failure("STEP 4", "กดยอมรับ/Cloudflare/Register ไม่สำเร็จ")
            return False

        if self.stopped: return False
        self.current_step = "ข้ามวิดีโอ & ข้ามด่านฝึกสอน"
        if not self.step5_handle_tutorial():
            self.handle_step_failure("STEP 5", "ข้ามหน้าต่าง Tutorial หรือออกจากด่านไม่สำเร็จ")
            return False

        if self.stopped: return False
        self.current_step = "ตั้งชื่อตัวละคร & รับของขวัญเริ่มต้น"
        if not self.step6_set_nickname():
            self.handle_step_failure("STEP 6", "ตั้งชื่อเล่นไม่สำเร็จ")
            return False

        if self.stopped: return False
        self.current_step = "เปิดลิงก์เชิญเพื่อน (Invite Link)"
        if not self.step7_open_invite_link():
            self.handle_step_failure("STEP 7", "เปิด Invite link ในเบราว์เซอร์ไม่สำเร็จ")
            return False

        if self.stopped: return False
        self.current_step = "ตรวจสอบยืนยันการเพิ่มเพื่อน"
        if not self.step8_confirm_friend_added():
            self.handle_step_failure("STEP 8", "ยืนยันการเพิ่มเพื่อนไม่สำเร็จ")
            return False

        if self.stopped: return False
        self.current_step = "ส่งหัวใจให้เพื่อนอันดับ 1 ❤️"
        if not self.step9_send_heart_and_exit():
            self.handle_step_failure("STEP 9", "ส่งหัวใจไม่สำเร็จ")
            return False

        self.current_step = "ส่งหัวใจสำเร็จเสร็จสิ้น 100%!"
        return True

    def run(self):
        self._log("=== HeartFarmer START (Fast Flow Mode) ===")
        self._log(f"Invite URL: {self.invite_url}")
        self._log(f"Max rounds: {self.max_rounds or 'infinite'}")

        while not self.stopped:
            if self.max_rounds and self.rounds >= self.max_rounds:
                self._log(f"ครบ {self.max_rounds} รอบ - หยุด")
                self.current_step = f"ครบ {self.max_rounds} รอบแล้ว (หยุดทำงาน)"
                break

            self.rounds += 1
            self.heart_sent = False
            self.current_step = f"เริ่มรอบที่ #{self.rounds}..."
            self._log(f"\n{'='*55}\n--- Round #{self.rounds} ---\n{'='*55}")

            try:
                ok = self.run_round()
                if ok:
                    self.success_count += 1
                    self.current_step = f"ส่งหัวใจสำเร็จ #{self.success_count} ดวง! (รอบ #{self.rounds})"
                    self._log(f"🎉 Round #{self.rounds} สำเร็จสมบูรณ์ 100% (DONE)!")
                else:
                    self.current_step = f"รอบ #{self.rounds} ล้มเหลว -> กำลังเริ่มรอบถัดไป..."
                    self._log(f"⚠️ Round #{self.rounds} ล้มเหลว -> เตรียมเริ่มรอบถัดไป...")
                    time.sleep(2.0)
            except KeyboardInterrupt:
                self._log("หยุดโดยผู้ใช้ (Ctrl+C)")
                self.current_step = "หยุดการทำงานแล้ว"
                break
            except Exception as exc:
                self.handle_step_failure("Exception", f"เกิดข้อผิดพลาด: {exc}")
                traceback.print_exc()
                time.sleep(3)
            finally:
                # เคลียร์แรม (RAM) ทุกๆ รอบที่ทำเสร็จ
                clear_system_memory(self.device, package=PACKAGE, log_func=self._log)

        self._log("=== HeartFarmer STOP ===")


if __name__ == "__main__":
    dev = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:16480"
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    HeartFarmer(device=dev, max_rounds=rounds).run()