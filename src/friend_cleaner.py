"""
friend_cleaner.py - CookieRun Classic Level 1 Friend Cleaner
Automated friend management:
  1. Open Friends list (800, 305)
  2. Tap Manage (290, 669)
  3. Ensure Favorites is UNCHECKED
  4. Ensure Level sort is Ascending (Level ▲)
  5. Scan visible Level 1 badges, check each one until all on-screen are selected
  6. Scroll down and repeat until no more Level 1 friends exist
  7. Tap 'Clear selection' (954, 651) -> Tap 'Confirm' (792, 457)
  8. Tap 'X' (1008, 79) to return to Lobby
  9. Configurable interval timer & multi-device selection
"""

import os
import sys
import time
import random
import threading
from typing import Dict, List, Optional, Any

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import cv2
import numpy as np


try:
    from .adb import (
        _format_target,
        _run_cmd,
        get_adb_path,
        device_capture_screen,
        resolve_emulator_name,
        clear_system_memory,
    )
except ImportError:
    from adb import (
        _format_target,
        _run_cmd,
        get_adb_path,
        device_capture_screen,
        resolve_emulator_name,
        clear_system_memory,
    )

# Coordinates on 1280x720 (User-calibrated)
LOBBY_FRIENDS_BUTTON = (801, 302)      # แตะ: (801, 302) ปุ่มเพื่อน
LEVEL_SORT_BUTTON = (564, 148)         # แตะ: (564, 148) ปุ่มกรองเวล
MANAGE_BUTTON = (328, 654)             # แตะ: (328, 654) ปุ่ม manage
FRIEND_ROW_POINTS = [                  # แตะเพื่อนเวลหนึ่งสี่จุด
    (625, 236),
    (633, 358),
    (642, 449),
    (623, 536),
]
CLEAR_SELECTION_BUTTON = (956, 650)    # แตะ: (956, 650) ปุ่มเคลียร์สีแดง (Clear selection)
CONFIRM_REMOVE_BUTTON = (777, 455)     # แตะ: (777, 455) ปุ่มยืนยันลบสีเขียว (Confirm)
MANAGE_CLOSE_BUTTON = (1054, 52)       # แตะ: (1054, 52) ปุ่ม X ออกจากหน้า Manage (Select a friend to remove)
FRIENDS_CLOSE_BUTTON = (1009, 69)      # แตะ: (1009, 69) ปุ่ม X หน้ารายชื่อเพื่อนปกติ กลับสู่หน้าหลัก
GIFT_CLOSE_BUTTON = (1113, 109)        # แตะ: (1113, 109) ปุ่มปิดหน้า gift

# Mailbox & Receive Hearts coordinates (1280x720)
LOBBY_MAILBOX_BUTTON = (686, 677)      # ปุ่มกล่องจดหมายที่หน้าหลัก
MAILBOX_LIVES_TAB = (490, 180)         # แท็บ Lives
MAILBOX_QUICK_RECEIVE = (600, 615)     # ปุ่ม Quick Receive & Send Lives
MAILBOX_CLOSE_BUTTON = (1119, 93)      # ปุ่ม X ปิดกล่องจดหมาย (1119, 93)


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
LVL1_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "level1_badge.png")
NO_LIVES_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "no_lives_text.png")
FRIENDS_DIALOG_X_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "FRIENDS_DIALOG_X_BTN.png")
MANAGE_MODE_X_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "MANAGE_MODE_X_BTN.png")


def _adb_tap(device: str, x: int, y: int, jitter: int = 4, delay: float = 0.5):
    target = _format_target(device)
    adb = get_adb_path()
    jx = x + (random.randint(-jitter, jitter) if jitter > 0 else 0)
    jy = y + (random.randint(-jitter, jitter) if jitter > 0 else 0)
    _run_cmd([adb, "-s", target, "shell", "input", "tap", str(jx), str(jy)], timeout=10)
    if delay > 0:
        time.sleep(delay)


def _adb_swipe(device: str, x1: int, y1: int, x2: int, y2: int, duration: int = 350, delay: float = 0.8):
    target = _format_target(device)
    adb = get_adb_path()
    _run_cmd([adb, "-s", target, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)], timeout=10)
    if delay > 0:
        time.sleep(delay)


def _find_green_confirm_button(screen: Optional[np.ndarray]) -> Optional[Tuple[int, int]]:
    """
    Detects green Confirm button in center dialog popup area.
    Handles 'Send ... a free Life?', 'All Lives received and sent!', and 'No Lives to receive!'.
    """
    if screen is None:
        return None
    roi = screen[380:520, 450:850]
    green = (roi[:, :, 1] > 160) & (roi[:, :, 0] < 80) & (roi[:, :, 2] < 180)
    if green.sum() > 80:
        ys, xs = np.where(green)
        return (int(xs.mean()) + 450, int(ys.mean()) + 380)
    return None


def is_no_lives_to_receive(screen: Optional[np.ndarray], threshold: float = 0.80) -> bool:
    """
    Detects if the 'No Lives to receive!' dialog popup is visible on screen.
    When this appears, all lives have been claimed and the receiving routine should stop immediately.
    """
    if screen is None or not os.path.exists(NO_LIVES_TEMPLATE_PATH):
        return False
    templ = cv2.imread(NO_LIVES_TEMPLATE_PATH)
    if templ is None:
        return False
    roi = screen[250:400, 400:900]
    res = cv2.matchTemplate(roi, templ, cv2.TM_CCOEFF_NORMED)
    return float(np.max(res)) >= threshold


def is_at_lobby(screen: Optional[np.ndarray]) -> bool:
    """
    Check if game is currently at the Lobby (Home screen).
    1. Checks for the large vibrant green 'Play!' button at bottom-right (X=600..900, Y=620..700).
    2. Fallback: Checks for lobby templates (friends_lobby_btn.png, MAINMENU_1.png).
    """
    if screen is None:
        return False
    h, w = screen.shape[:2]
    if h >= 700 and w >= 900:
        roi = screen[620:700, 600:900]
        green = (roi[:, :, 1] > 180) & (roi[:, :, 0] < 80) & (roi[:, :, 2] < 150)
        if green.sum() > 2000:
            return True

    for tmpl_name in ["friends_lobby_btn.png", "MAINMENU_1.png"]:
        p = os.path.join(TEMPLATE_DIR, tmpl_name)
        if os.path.exists(p):
            t = cv2.imread(p)
            if t is not None and t.shape[0] <= screen.shape[0] and t.shape[1] <= screen.shape[1]:
                res = cv2.matchTemplate(screen, t, cv2.TM_CCOEFF_NORMED)
                if float(np.max(res)) >= 0.85:
                    return True
    return False


GAME_PACKAGE = "com.devsisters.crg"


def check_banner_or_news_popup(img: Optional[np.ndarray]) -> Optional[Tuple[int, int]]:
    """
    ตรวจจับหน้าต่างข่าวสาร/ประกาศ/แบนเนอร์/กิจกรรมทั้งหมด ที่มีปุ่ม X เทากลม
    อ้างอิงวิธีตรวจจับจาก heart_farmer.py:
      1. ตรวจจับตำแหน่งหลักที่ (1125, 72)
      2. ตรวจจับแบบพลวัตทั่วทั้งมุมขวาบน (x: 1050..1260, y: 15..130) สำหรับกิจกรรม Cookie Challenge ฯลฯ
    คืนค่าพิกัด (x, y) ของปุ่ม X หรือ None ถ้าไม่พบ
    """
    if img is None:
        return None
    h, w = img.shape[:2]
    if (w, h) != (1280, 720):
        img = cv2.resize(img, (1280, 720))

    # 1. ตรวจสอบพิกัดมาตรฐานจาก heart_farmer: (1125, 72)
    btn_roi = img[50:95, 1105:1145]
    grey = (np.abs(btn_roi[:, :, 0].astype(int) - btn_roi[:, :, 1].astype(int)) < 15) & \
           (np.abs(btn_roi[:, :, 1].astype(int) - btn_roi[:, :, 2].astype(int)) < 15) & \
           (btn_roi[:, :, 0] > 90) & (btn_roi[:, :, 0] < 170)
    white = (btn_roi[:, :, 0] > 200) & (btn_roi[:, :, 1] > 200) & (btn_roi[:, :, 2] > 200)
    if grey.sum() > 300 and white.sum() > 60:
        return (1125, 72)

    # 2. ตรวจสอบปุ่ม X เทากลมในบริเวณมุมขวาบนของหน้าต่างป็อปอัป (x: 1050..1260, y: 15..130)
    roi = img[15:130, 1050:1260]
    diff1 = np.abs(roi[:, :, 0].astype(int) - roi[:, :, 1].astype(int))
    diff2 = np.abs(roi[:, :, 1].astype(int) - roi[:, :, 2].astype(int))
    mask_grey = (diff1 < 20) & (diff2 < 20) & (roi[:, :, 0] > 100) & (roi[:, :, 0] < 185)
    mask_white = (roi[:, :, 0] > 210) & (roi[:, :, 1] > 210) & (roi[:, :, 2] > 210)

    n, _, stats, centroids = cv2.connectedComponentsWithStats(mask_grey.astype(np.uint8))
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if 250 < area < 3500:
            cx = int(centroids[i][0])
            cy = int(centroids[i][1])
            sub_w = mask_white[max(0, cy-15):min(roi.shape[0], cy+15), max(0, cx-15):min(roi.shape[1], cx+15)]
            if sub_w.sum() > 25:
                real_x = 1050 + cx
                real_y = 15 + cy
                return (real_x, real_y)

    return None


def check_select_mode_popup(img: Optional[np.ndarray]) -> bool:
    """
    ตรวจจับหน้าต่าง Select a Mode (X สีม่วง 1215, 95)
    อ้างอิงวิธีตรวจจับจาก heart_farmer.py
    """
    if img is None:
        return False
    h, w = img.shape[:2]
    if (w, h) != (1280, 720):
        img = cv2.resize(img, (1280, 720))
    roi = img[70:120, 1190:1240]
    purple = (roi[:, :, 0] > 100) & (roi[:, :, 2] > 100) & (roi[:, :, 1] < 80)
    roi_x = img[80:110, 1200:1230]
    white_x = (roi_x[:, :, 0] > 200) & (roi_x[:, :, 1] > 200) & (roi_x[:, :, 2] > 200)
    return bool(purple.sum() > 600 and white_x.sum() > 30)


def clear_all_lobby_popups(device: str, max_wait: float = 35.0, log_func=None) -> bool:
    """
    วนลูปตรวจจับและปิด Popup ทุกชนิด (ข่าวสาร/ประกาศ/แบนเนอร์/กิจกรรม, Select Mode, Confirm กลางจอ)
    จนกว่าหน้า Lobby จะสะอาดสมบูรณ์ 100% ตามแบบ heart_farmer
    """
    def _log(msg: str):
        if log_func:
            log_func(f"[PopupCleaner][{device}] {msg}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}][PopupCleaner][{device}] {msg}", flush=True)

    t_end = time.time() + max_wait
    while time.time() < t_end:
        screen = device_capture_screen(device)
        if screen is None:
            time.sleep(0.5)
            continue

        # 1. ตรวจสอบหน้าต่างข่าวสาร / ประกาศ / แบนเนอร์กิจกรรม (X เทากลม) ตามแบบ heart_farmer
        news_btn = check_banner_or_news_popup(screen)
        if news_btn is not None:
            _log(f"⚡ ตรวจพบหน้าต่างข่าวสาร/ประกาศ/กิจกรรม -> แตะปิดปุ่ม X ที่ {news_btn}...")
            _adb_tap(device, news_btn[0], news_btn[1], jitter=2, delay=1.2)
            continue

        # 2. ตรวจสอบหน้าต่าง Select a Mode (X สีม่วง 1215, 95)
        if check_select_mode_popup(screen):
            _log("⚡ ตรวจพบหน้าต่าง Select a Mode -> แตะปิดปุ่ม X ที่ (1215, 95)...")
            _adb_tap(device, 1215, 95, jitter=2, delay=1.2)
            continue

        # 3. ตรวจสอบปุ่ม Confirm สีเขียวกลางจอ (Pop-up รางวัล/ยินดีต้อนรับ)
        btn = _find_green_confirm_button(screen)
        if btn is not None:
            _log(f"⚡ ตรวจพบ Pop-up กลางจอ -> แตะ Confirm ที่ {btn}...")
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=1.2)
            continue

        # 4. ตรวจสอบว่าถึงหน้า Lobby สะอาดเรียบร้อยแล้ว
        if is_at_lobby(screen):
            time.sleep(1.0)
            chk = device_capture_screen(device)
            if chk is not None and check_banner_or_news_popup(chk) is None and not check_select_mode_popup(chk):
                _log("✅ ยืนยันหน้าล็อบบี้สะอาดเรียบร้อย 100%!")
                return True

        time.sleep(1.0)
    return False


def stop_game_app(device: str, log_func=None):
    """Force-stop CookieRun app on device."""
    target = _format_target(device)
    adb = get_adb_path()
    if log_func:
        log_func(f"🚪 สั่งปิดเกม Cookie Run ({GAME_PACKAGE}) บนจอ {device}...")
    else:
        print(f"[{time.strftime('%H:%M:%S')}][AppControl][{device}] 🚪 สั่งปิดเกม Cookie Run...", flush=True)
    _run_cmd([adb, "-s", target, "shell", "am", "force-stop", GAME_PACKAGE], timeout=10)
    time.sleep(1.5)


def start_game_app(device: str, log_func=None):
    """Launch CookieRun app on device."""
    target = _format_target(device)
    adb = get_adb_path()
    if log_func:
        log_func(f"📱 สั่งเปิดเกม Cookie Run บนจอ {device}...")
    else:
        print(f"[{time.strftime('%H:%M:%S')}][AppControl][{device}] 📱 สั่งเปิดเกม Cookie Run...", flush=True)
    _run_cmd([adb, "-s", target, "shell", "monkey", "-p", GAME_PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"], timeout=10)


def launch_game_and_wait_lobby(device: str, timeout: float = 60.0, log_func=None) -> bool:
    """
    เปิดเกม Cookie Run และรอจนกว่าจะโหลดเสร็จ พร้อมเคลียร์หน้าข่าว/แบนเนอร์/Pop-up อัตโนมัติ
    """
    start_game_app(device, log_func=log_func)
    time.sleep(5.0)
    return clear_all_lobby_popups(device, max_wait=timeout, log_func=log_func)


def wait_for_lobby(device: str, timeout: float = 15.0, log_func=None) -> bool:
    """
    Waits until the device screen is confirmed to be at the Lobby.
    If news/banner popups appear, clears them automatically.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        screen = device_capture_screen(device)
        if screen is not None:
            if check_banner_or_news_popup(screen) or check_select_mode_popup(screen):
                if log_func:
                    log_func("   ⚡ ตรวจพบหน้าข่าว/แบนเนอร์ กำลังกดปิด...")
                clear_all_lobby_popups(device, max_wait=10.0, log_func=log_func)
                continue
        if is_at_lobby(screen):
            return True
        if log_func:
            log_func("   [รอ] กำลังรอให้เกมแสดงผลหน้าล็อบบี้...")
        time.sleep(1.0)
    return False


def receive_mailbox_hearts(device: str, log_func=None) -> bool:
    """
    Open Mailbox, receive all lives/hearts and return lives to friends before deleting friends.
    ตรวจจอก่อนกด และตรวจจอหลังกดทุกขั้นตอน:
      - ตรวจสอบหน้าล็อบบี้ก่อนเปิดกล่องข้อความ
      - รับหัวใจจนกว่าจะขึ้น 'No Lives to receive!'
      - ตรวจสอบหน้าจอก่อนกดปิด และตรวจว่ากลับหน้าล็อบบี้หรือยังก่อนไปต่อ
    """
    def _log(msg: str):
        if log_func:
            log_func(f"[ReceiveHearts][{device}] {msg}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}][ReceiveHearts][{device}] {msg}", flush=True)

    # 1. ตรวจจอก่อนกด: ตรวจสอบว่าพร้อมที่หน้าล็อบบี้
    _log("💌 1. ตรวจสอบหน้าจอ: รอให้พร้อมที่หน้าล็อบบี้ก่อนเปิดกล่องข้อความ...")
    if not wait_for_lobby(device, timeout=8.0, log_func=_log):
        _log("   ⚠️ หน้าจออาจยังไม่ได้อยู่ล็อบบี้ แต่จะพยายามกดเข้ากล่องข้อความ...")

    _log(f"   แตะ: ({LOBBY_MAILBOX_BUTTON[0]}, {LOBBY_MAILBOX_BUTTON[1]}) ปุ่มกล่องข้อความ")
    _adb_tap(device, LOBBY_MAILBOX_BUTTON[0], LOBBY_MAILBOX_BUTTON[1], jitter=2, delay=1.5)

    _log("💌 2. กดแท็บ Lives...")
    _adb_tap(device, MAILBOX_LIVES_TAB[0], MAILBOX_LIVES_TAB[1], jitter=2, delay=1.0)

    # ตรวจจอทันที: ถ้าขึ้น 'No Lives to receive!' อยู่แล้ว
    screen = device_capture_screen(device)
    if is_no_lives_to_receive(screen):
        _log("   🛑 ตรวจพบ 'No Lives to receive!' -> รับหัวใจหมดแล้ว! กด Confirm แล้วหยุดรับทันที")
        btn = _find_green_confirm_button(screen)
        if btn is not None:
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=0.8)

        _log("💌 ปิดกล่องข้อความกลับสู่หน้าหลัก (ตรวจจอก่อนกด)...")
        screen_curr = device_capture_screen(device)
        if not is_at_lobby(screen_curr):
            _adb_tap(device, MAILBOX_CLOSE_BUTTON[0], MAILBOX_CLOSE_BUTTON[1], jitter=1, delay=1.2)
            wait_for_lobby(device, timeout=6.0, log_func=_log)
        return True

    _log("💌 3. เริ่มลูปกดรับหัวใจต่อเนื่องจนกว่าจะขึ้น 'No Lives to receive!'...")
    no_confirm_streak = 0
    total_confirmed = 0
    max_rounds = 40

    for round_num in range(1, max_rounds + 1):
        screen = device_capture_screen(device)

        # ตรวจจอก่อนกด: เช็ค No Lives to receive!
        if is_no_lives_to_receive(screen):
            _log("   🛑 ตรวจพบ 'No Lives to receive!' -> รับหมดแล้ว! กดยืนยันแล้วหยุดรับใจทันที")
            btn = _find_green_confirm_button(screen)
            if btn is not None:
                _adb_tap(device, btn[0], btn[1], jitter=2, delay=0.8)
            break

        btn = _find_green_confirm_button(screen)
        if btn is not None:
            _log(f"   👉 พบปุ่มยืนยัน Pop-up ที่ {btn} (รอบที่ {round_num}) -> กด Confirm...")
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=1.0)
            total_confirmed += 1
            no_confirm_streak = 0
            continue

        _log(f"   👉 กดปุ่ม 'Quick Receive & Send Lives' (รอบที่ {round_num})...")
        _adb_tap(device, MAILBOX_QUICK_RECEIVE[0], MAILBOX_QUICK_RECEIVE[1], jitter=3, delay=1.0)

        # ตรวจจอหลังกด
        time.sleep(0.8)
        screen = device_capture_screen(device)

        if is_no_lives_to_receive(screen):
            _log("   🛑 ตรวจพบ 'No Lives to receive!' -> รับหมดแล้ว! กดยืนยันแล้วหยุดรับใจทันที")
            btn = _find_green_confirm_button(screen)
            if btn is not None:
                _adb_tap(device, btn[0], btn[1], jitter=2, delay=0.8)
            break

        btn = _find_green_confirm_button(screen)
        if btn is not None:
            _log(f"   👉 มี Pop-up Confirm โผล่ขึ้นมาที่ {btn} -> กด Confirm...")
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=1.0)
            total_confirmed += 1
            no_confirm_streak = 0
        else:
            no_confirm_streak += 1
            if no_confirm_streak >= 2:
                _log("   ✨ ไม่มีปุ่มยืนยัน (Confirm) ขึ้นมาอีกแล้ว -> รับหัวใจทั้งหมดสำเร็จ 100%!")
                break

    # 4. ออกจากรับใจตรวจจอ: ตรวจจอก่อนแตะปิด และตรวจจอหลังแตะปิด
    _log(f"💌 4. ปิดกล่องข้อความกลับสู่หน้าหลัก (กดยืนยันไปทั้งหมด {total_confirmed} ครั้ง)...")
    screen_before_close = device_capture_screen(device)
    if is_at_lobby(screen_before_close):
        _log("   ✅ ตรวจจอพบว่าอยู่ที่หน้าล็อบบี้แล้ว ไม่ต้องแตะปุ่มปิดซ้ำ")
    else:
        _log(f"   แตะ: ({MAILBOX_CLOSE_BUTTON[0]}, {MAILBOX_CLOSE_BUTTON[1]}) ปุ่มปิดกล่องข้อความ")
        _adb_tap(device, MAILBOX_CLOSE_BUTTON[0], MAILBOX_CLOSE_BUTTON[1], jitter=1, delay=1.2)
        # ตรวจจอหลังกด: ยืนยันว่ากลับสู่หน้าล็อบบี้แล้ว
        if not wait_for_lobby(device, timeout=6.0, log_func=_log):
            _log("   [รอ] ยังไม่พบหน้าล็อบบี้ ตรวจสอบภาพหน้าจออีกครั้ง...")
            screen_retry = device_capture_screen(device)
            if not is_at_lobby(screen_retry):
                _adb_tap(device, MAILBOX_CLOSE_BUTTON[0], MAILBOX_CLOSE_BUTTON[1], jitter=1, delay=1.0)
                wait_for_lobby(device, timeout=5.0, log_func=_log)

    _log("✅ รับหัวใจครบถ้วน 100% เรียบร้อยแล้ว!")
    return True


def find_normal_friends_close_btn(screen: Optional[np.ndarray], threshold: float = 0.72) -> Optional[Tuple[int, int]]:
    """
    Detects 'X' close button of Friends dialog in NORMAL mode (with Friends/Find/Request tabs).
    Returns (1009, 69) if detected, otherwise None.
    """
    if screen is None or not os.path.exists(FRIENDS_DIALOG_X_TEMPLATE_PATH):
        return None
    tmpl = cv2.imread(FRIENDS_DIALOG_X_TEMPLATE_PATH)
    if tmpl is None:
        return None
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    roi = screen[30:140, 900:1120]
    res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val >= threshold:
        return FRIENDS_CLOSE_BUTTON
    return None


def find_manage_mode_close_btn(screen: Optional[np.ndarray], threshold: float = 0.80) -> Optional[Tuple[int, int]]:
    """
    Detects 'X' close button in MANAGE mode ('Select a friend to remove!').
    Returns (1054, 52) if detected, otherwise None.
    """
    if screen is None or not os.path.exists(MANAGE_MODE_X_TEMPLATE_PATH):
        return None
    tmpl = cv2.imread(MANAGE_MODE_X_TEMPLATE_PATH)
    if tmpl is None:
        return None
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    roi = screen[20:100, 1000:1120]
    res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val >= threshold:
        return MANAGE_CLOSE_BUTTON
    return None


def is_in_manage_friends_mode(screen: Optional[np.ndarray]) -> Optional[Tuple[int, int]]:
    """
    Checks if device is currently in Manage Friends mode ('Select a friend to remove!').
    Returns coordinate of 'Clear selection' button if detected, else None.
    """
    if screen is None:
        return None
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    # Red button at bottom right (600..715, 650..1100)
    roi = screen[600:715, 650:1100]
    red_mask = (roi[:, :, 2] > 160) & (roi[:, :, 1] < 80) & (roi[:, :, 0] < 80)
    if red_mask.sum() > 800:
        ys, xs = np.where(red_mask)
        return (int(xs.mean()) + 650, int(ys.mean()) + 600)
    # Check Manage mode X button
    if find_manage_mode_close_btn(screen) is not None:
        return CLEAR_SELECTION_BUTTON
    return None


def find_friends_dialog_close_btn(screen: Optional[np.ndarray]) -> Optional[Tuple[int, int]]:
    """
    Unified close button detector:
    - If in Manage mode: returns (1054, 52)
    - If in Normal mode: returns (1009, 69)
    """
    btn = find_manage_mode_close_btn(screen)
    if btn is not None:
        return btn
    return find_normal_friends_close_btn(screen)


def is_friends_dialog_open(screen: Optional[np.ndarray]) -> bool:
    """
    Check if Friends list popup is open on screen (either Normal or Manage mode).
    1. Checks if Manage mode is active.
    2. Checks if Normal close button is detected.
    3. Fallback: Checks for Favorites button in [140:220, 200:380].
    """
    if screen is None:
        return False
    if is_in_manage_friends_mode(screen) is not None:
        return True
    if find_normal_friends_close_btn(screen) is not None:
        return True
    roi = screen[140:220, 200:380]
    gold = (roi[:, :, 2] > 150) & (roi[:, :, 1] > 120) & (roi[:, :, 0] < 80)
    return bool(gold.sum() > 200)


def detect_level1_badges(screen_bgr: np.ndarray, threshold: float = 0.70) -> List[int]:
    """
    Search for Level 1 star badges in the friend list area.
    Returns sorted list of Y coordinates of Level 1 badges.
    """
    if screen_bgr is None:
        return []
    if not os.path.exists(LVL1_TEMPLATE_PATH):
        return []

    templ = cv2.imread(LVL1_TEMPLATE_PATH)
    if templ is None:
        return []

    # Search in badge column: X in 230..320, Y in 200..680
    h, w = screen_bgr.shape[:2]
    y_min, y_max = min(200, h - 50), min(680, h)
    x_min, x_max = min(230, w - 50), min(320, w)
    roi = screen_bgr[y_min:y_max, x_min:x_max]

    res = cv2.matchTemplate(roi, templ, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    pts = []
    for pt in zip(*loc[::-1]):
        y = y_min + pt[1]
        if not any(abs(y - p) < 40 for p in pts):
            pts.append(y)
    pts.sort()
    return pts


def is_row_selected(screen_bgr: np.ndarray, badge_y: int) -> bool:
    """
    Check if the friend row corresponding to badge_y is selected.
    Selected rows have a distinctive red/pink background at X=500.
    """
    try:
        h, w = screen_bgr.shape[:2]
        sample_y = min(badge_y + 20, h - 1)
        sample_x = min(500, w - 1)
        b, g, r = screen_bgr[sample_y, sample_x]
        return (int(r) - int(g) > 20) and (int(r) - int(b) > 20)
    except Exception:
        return False


def is_level_sort_ascending(screen_bgr: np.ndarray) -> bool:

    """
    Check if Level sort is active and ascending (Level ▲).
    We check the yellow/cyan arrow region or Level pill button.
    """
    try:
        # Sort button region (400..500, 130..170)
        roi = screen_bgr[130:170, 400:500]
        # Yellow arrow has R > 200, G > 200, B < 120
        yellow_mask = (roi[:, :, 2] > 200) & (roi[:, :, 1] > 200) & (roi[:, :, 0] < 120)
        if yellow_mask.sum() > 30:
            # Check arrow shape: upward triangle has peak at top (fewer pixels in top half)
            y_idx, _ = np.where(yellow_mask)
            mid = (y_idx.min() + y_idx.max()) / 2
            top_half = (y_idx < mid).sum()
            bottom_half = (y_idx >= mid).sum()
            return bottom_half > top_half  # Upward arrow has wide base at bottom
        return False
    except Exception:
        return False


def clean_level1_friends(device: str, log_func=None, restart_app: bool = False) -> Dict[str, Any]:
    """
    Executes the complete Level 1 friend deletion workflow:
      0. Receive hearts from Mailbox first (บอทต้องรับหัวใจก่อนลบเพื่อน)
      1. Open Friends list (811, 297)
      2. Tap Manage (324, 653)
      3. Ensure Level sort is Ascending (567, 138 - NO Favorites!)
      4. Scan visible Level 1 badges, check each one until all on-screen are selected
      5. Scroll up and repeat until no more Level 1 friends exist
      6. Tap 'Clear selection' (950, 661) -> Tap 'Confirm' (781, 460)
      7. Tap 'X' (1009, 69) to return to Lobby
      8. If restart_app is True, force-stops the game app after cleaning so it restarts on the next loop
    """
    def _log(msg: str):
        if log_func:
            log_func(f"[FriendCleaner][{device}] {msg}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}][FriendCleaner][{device}] {msg}", flush=True)

    _log("==========================================")
    _log("💖 ขั้นตอนที่ 1: รับหัวใจในกล่องข้อความก่อน...")
    _log("==========================================")
    try:
        receive_mailbox_hearts(device, log_func=_log)
    except Exception as e:
        _log(f"⚠️ มีข้อผิดพลาดในขั้นตอนรับหัวใจ: {e} -> ข้ามไปขั้นตอนลบเพื่อน")
    time.sleep(1.0)

    _log("==========================================")
    _log("🧹 ขั้นตอนที่ 2: เริ่มกระบวนการลบเพื่อนเวล 1...")
    _log("==========================================")

    # ตรวจสอบหน้าจอ: รอให้เกมกลับสู่หน้าล็อบบี้ก่อนเริ่ม
    _log("🔍 ตรวจสอบหน้าจอ: รอให้เกมแสดงผลหน้าล็อบบี้อย่างสมบูรณ์...")
    wait_for_lobby(device, timeout=10, log_func=_log)
    time.sleep(0.5)

    # 1. กดเข้าเพื่อน: (801, 302) ตรวจสอบหน้าจอก่อนกด
    friends_opened = False
    for attempt in range(5):
        screen = device_capture_screen(device)
        if is_friends_dialog_open(screen):
            _log("   ✅ ตรวจพบหน้าต่าง Friends เปิดอยู่แล้ว!")
            friends_opened = True
            break
        if not is_at_lobby(screen):
            _log("   ⚠️ หน้าจอไม่ได้อยู่ที่ล็อบบี้ กำลังรอหน้าล็อบบี้ก่อนแตะปุ่มเพื่อน...")
            wait_for_lobby(device, timeout=4, log_func=_log)
            continue

        _log(f"1. แตะ: ({LOBBY_FRIENDS_BUTTON[0]}, {LOBBY_FRIENDS_BUTTON[1]}) ปุ่มเพื่อน (รอบที่ {attempt + 1})")
        _adb_tap(device, LOBBY_FRIENDS_BUTTON[0], LOBBY_FRIENDS_BUTTON[1], jitter=1, delay=1.5)
        screen_after = device_capture_screen(device)
        if is_friends_dialog_open(screen_after):
            _log("   ✅ ตรวจพบหน้าต่าง Friends เปิดขึ้นมาแล้ว!")
            friends_opened = True
            break
        _log(f"   [รอ] รอหน้าต่าง Friends เปิด (รอบที่ {attempt + 1})...")
        time.sleep(1.0)

    if not friends_opened:
        _log("❌ ไม่สามารถเปิดหน้าต่าง Friends ได้ ยกเลิกการทำงานรอบนี้เพื่อความปลอดภัย")
        return {"success": False, "message": "Failed to open Friends dialog"}

    # ตรวจสอบว่าหน้าต่างเพื่อนยังเปิดอยู่ก่อนดำเนินการ
    screen = device_capture_screen(device)
    if not is_friends_dialog_open(screen):
        _log("❌ ตรวจไม่พบหน้าต่าง Friends ยกเลิกการทำงานเพื่อความปลอดภัย")
        return {"success": False, "message": "Friends dialog not visible"}

    # 2. ตรวจสอบหน้าจอว่ามีเพื่อนเวลหนึ่งไหม ค่อยกดกรองใหม่ (ตรวจจอก่อนกด กดแล้วตรวจจอ 4-5 ครั้ง)
    _log("2. ตรวจสอบหน้าจอว่ามีเพื่อนเวล 1 หรือไม่ เพื่อปรับการเรียงลำดับ (Sort)...")
    lvl1_found = False
    for sort_attempt in range(1, 6):
        screen = device_capture_screen(device)
        badges = detect_level1_badges(screen)
        if len(badges) > 0:
            _log(f"   ✅ [ตรวจจอก่อนกด: พบเวล 1] จำนวน {len(badges)} คนบนหน้าจอแล้ว! การเรียงลำดับถูกต้อง")
            lvl1_found = True
            break

        _log(f"   🔍 [รอบที่ {sort_attempt}/5: ยังไม่พบเวล 1] แตะปุ่มกรองเวล ({LEVEL_SORT_BUTTON[0]}, {LEVEL_SORT_BUTTON[1]})...")
        _adb_tap(device, LEVEL_SORT_BUTTON[0], LEVEL_SORT_BUTTON[1], jitter=1, delay=1.2)

        # ตรวจสอบหน้าจอหลังกดกรองทันที
        screen_after_sort = device_capture_screen(device)
        badges_after = detect_level1_badges(screen_after_sort)
        if len(badges_after) > 0:
            _log(f"   ✅ [ตรวจจอหลังกดกรอง: สำเร็จ] พบเพื่อนเวล 1 จำนวน {len(badges_after)} คนทันที!")
            lvl1_found = True
            break
        time.sleep(0.5)

    if not lvl1_found:
        _log("ℹ️ ตรวจสอบหน้าจอครบ 5 ครั้งแล้ว ไม่พบเพื่อนเลเวล 1 บนหน้าจอ (อาจไม่มีเพื่อนเวล 1 ในไอดีนี้)")

    # 3. กด manage: ตรวจจอก่อนกด
    screen = device_capture_screen(device)
    if not is_friends_dialog_open(screen):
        _log("❌ หน้าต่าง Friends ปิดไปแล้ว ไม่สามารถดำเนินการต่อได้")
        return {"success": False, "message": "Friends dialog closed unexpectedly"}

    _log(f"3. แตะ: ({MANAGE_BUTTON[0]}, {MANAGE_BUTTON[1]}) ปุ่ม manage")
    _adb_tap(device, MANAGE_BUTTON[0], MANAGE_BUTTON[1], jitter=1, delay=1.2)

    screen = device_capture_screen(device)
    if screen is None:
        _log("❌ ไม่สามารถจับภาพหน้าจอได้")
        return {"success": False, "message": "Failed to capture screen"}

    # 4. แตะเพื่อนเวลหนึ่ง: ตรวจจอก่อนแตะ แตะแล้วตรวจจอ ทุกครั้ง
    total_ticked = 0
    consecutive_empty_scrolls = 0
    max_scrolls = 40

    _log("4. เริ่มกระบวนการติ๊กเลือกเพื่อนเวล 1 (ตรวจจอก่อนแตะ และตรวจจอหลังแตะทุกรายการ)...")

    for scroll_idx in range(max_scrolls):
        screen = device_capture_screen(device)
        if screen is None:
            time.sleep(0.5)
            continue

        badges = detect_level1_badges(screen)

        if len(badges) == 0:
            consecutive_empty_scrolls += 1
            if consecutive_empty_scrolls >= 2:
                _log("   ✨ [ตรวจจอ: เลื่อนครบแล้ว] ไม่พบเพื่อนเวล 1 ติดต่อกัน 2 ครั้ง -> ติ๊กครบหมดแล้ว!")
                break
        else:
            consecutive_empty_scrolls = 0
            _log(f"   [รอบเลื่อนที่ {scroll_idx + 1}] พบเพื่อนเวล 1 บนหน้าจอ {len(badges)} คน")

            # แตะเพื่อนเวลหนึ่งตามจุด
            for pt in FRIEND_ROW_POINTS:
                px, py = pt[0], pt[1]
                has_lvl1 = any(abs(b_y - (py - 40)) < 65 for b_y in badges)
                if not has_lvl1:
                    continue

                # ตรวจจอก่อนกด: แถวนี้ถูกติ๊กเลือกแล้วหรือยัง
                b, g, r = screen[py, px]
                is_selected = (int(r) - int(g) > 25) and (int(r) - int(b) > 25)

                if not is_selected:
                    _log(f"   👉 [ตรวจจอก่อนกด: ยังไม่ติ๊ก] แตะเพื่อนเวล 1 ที่จุด ({px}, {py})")
                    _adb_tap(device, px, py, jitter=2, delay=0.3)

                    # ตรวจจอหลังกด: ยืนยันว่าแถวเปลี่ยนเป็นติ๊กเลือกแล้ว
                    screen_check = device_capture_screen(device)
                    if screen_check is not None:
                        cb, cg, cr = screen_check[py, px]
                        if (int(cr) - int(cg) > 20) and (int(cr) - int(cb) > 20):
                            _log(f"      ✅ [ตรวจจอหลังกด: สำเร็จ] แถวที่จุด ({px}, {py}) ติ๊กเลือกแล้ว")
                    total_ticked += 1

            # เก็บตกแถวที่ตรวจเจอแต่ไม่ตรงจุด 4 จุดหลัก
            screen_after = device_capture_screen(device)
            if screen_after is not None:
                badges_after = detect_level1_badges(screen_after)
                for b_y in badges_after:
                    if not is_row_selected(screen_after, b_y):
                        _log(f"   👉 [เก็บตก: ก่อนกด] แตะเพื่อนเวล 1 ที่ Y={b_y + 20}")
                        _adb_tap(device, 500, b_y + 20, jitter=2, delay=0.3)
                        total_ticked += 1

        # เลื่อนหน้าจอลงเพื่อตรวจคนถัดไป
        _log("   📜 เลื่อนหน้าจอลงเพื่อตรวจสอบเพื่อนคนถัดไป...")
        _adb_swipe(device, 500, 580, 500, 250, duration=350, delay=0.8)

    _log(f"✅ ติ๊กเลือกเพื่อนเลเวล 1 เสร็จสิ้น (ทั้งหมด ~{total_ticked} รายการ)")

    # 5. ลบให้หมด: ถ้ามีติ๊กไว้ ให้กดเคลียร์ -> ยืนยันลบ
    if total_ticked > 0:
        screen = device_capture_screen(device)
        manage_btn = is_in_manage_friends_mode(screen)
        if manage_btn is not None or is_friends_dialog_open(screen):
            btn_coord = manage_btn if manage_btn is not None else CLEAR_SELECTION_BUTTON
            _log(f"5. [ตรวจจอก่อนกด: พบหน้าจัดการเพื่อน] แตะ: ({btn_coord[0]}, {btn_coord[1]}) ปุ่มเคลียร์ (Clear selection)")
            _adb_tap(device, btn_coord[0], btn_coord[1], jitter=1, delay=1.2)

            # ตรวจหาปุ่มยืนยันลบ (สีเขียว Confirm)
            screen_confirm = device_capture_screen(device)
            conf_btn = _find_green_confirm_button(screen_confirm)
            conf_coord = conf_btn if conf_btn is not None else CONFIRM_REMOVE_BUTTON
            _log(f"   แตะ: ({conf_coord[0]}, {conf_coord[1]}) ปุ่มยืนยันลบ (Confirm)")
            _adb_tap(device, conf_coord[0], conf_coord[1], jitter=1, delay=2.5)

            # ตรวจจอหลังกดลบ: รอให้หน้าต่างยืนยันปิด และรายการเพื่อนอัปเดตเสร็จ
            for _ in range(6):
                screen_wait = device_capture_screen(device)
                if screen_wait is not None and _find_green_confirm_button(screen_wait) is None:
                    _log("   ✅ [ตรวจจอหลังกดยืนยัน: สำเร็จ] ลบเพื่อนเลเวล 1 ที่เลือกเรียบร้อยแล้ว!")
                    break
                time.sleep(0.5)
        else:
            _log("⚠️ ตรวจไม่พบหน้าต่างเพื่อน ข้ามขั้นตอนลบเพื่อความปลอดภัย")
    else:
        _log("ℹ️ ไม่มีเพื่อนเวล 1 ให้ลบในรอบนี้")

    # 6. ออกสู่หน้าหลัก (Lobby): ตรวจจับภาพและปิดตามลำดับ (ปิด Manage mode ก่อน แล้วปิดหน้าต่างหลัก)
    _log("6. เริ่มขั้นตอนออกจากหน้าต่างเพื่อนกลับสู่หน้าหลัก (Lobby)...")
    for attempt in range(1, 6):
        screen = device_capture_screen(device)

        # ตรวจจอก่อนกด: ถ้ากลับมาหน้าล็อบบี้แล้ว ห้ามกดปุ่มใดๆ อีกเด็ดขาด!
        if is_at_lobby(screen):
            _log("   ✅ [ตรวจจอก่อนกด: พบหน้าล็อบบี้แล้ว] กลับสู่หน้าหลักเรียบร้อย 100%!")
            break

        # เช็คว่ายังอยู่ใน Manage mode หรือไม่
        manage_x = find_manage_mode_close_btn(screen)
        if manage_x is not None:
            _log(f"   🎯 [ตรวจจอก่อนกด: อยู่ในโหมดจัดการ] แตะปุ่ม X ออกจากโหมดจัดการ ({manage_x[0]}, {manage_x[1]})...")
            _adb_tap(device, manage_x[0], manage_x[1], jitter=1, delay=1.2)
            continue

        # เช็คว่าอยู่ใน Normal Friends mode หรือไม่
        normal_x = find_normal_friends_close_btn(screen)
        if normal_x is not None:
            _log(f"   🎯 [ตรวจจอก่อนกด: อยู่ในหน้ารายชื่อเพื่อน] แตะปุ่ม X ปิดหน้าต่างเพื่อน ({normal_x[0]}, {normal_x[1]})...")
            _adb_tap(device, normal_x[0], normal_x[1], jitter=1, delay=1.5)

            # ตรวจจอหลังกดทันที
            screen_after = device_capture_screen(device)
            if is_at_lobby(screen_after):
                _log("   ✅ [ตรวจจอหลังกด: สำเร็จ] ยืนยันกลับสู่หน้าหลัก (Lobby) เรียบร้อยแล้ว 100%!")
                break
            continue

        _log("   ✨ [ตรวจจอ: ไม่พบหน้าต่างเพื่อนแล้ว] ปิดเรียบร้อย ไม่แตะซ้ำเด็ดขาด ป้องกันเข้าโหมดอื่น!")
        break

    final_screen = device_capture_screen(device)
    if is_at_lobby(final_screen):
        _log("🎉 กระบวนการเสร็จสมบูรณ์ 100% กลับสู่หน้าหลักเรียบร้อยแล้ว!")
    else:
        _log("ℹ️ สิ้นสุดการทำงาน ตรวจสอบหน้าจอเรียบร้อยแล้ว")

    # ปิดเกม Cookie Run ตามคำสั่งเพื่อรอเปิดใหม่ในรอบถัดไป
    if restart_app:
        _log("🚪 [ตั้งค่าให้ปิดเกมหลังทำงานเสร็จ] สั่งปิดเกม Cookie Run เพื่อรอเปิดใหม่ตามรอบลูป...")
        stop_game_app(device, log_func=_log)

    # เคลียร์แรม (RAM) ทุกๆ รอบที่ทำเสร็จ
    clear_system_memory(device, package=GAME_PACKAGE, log_func=_log)

    return {
        "success": True,
        "device": device,
        "total_ticked": total_ticked,
        "message": f"ลบเพื่อนเลเวล 1 บนจอ {device} เสร็จสิ้น (~{total_ticked} รายการ)"
    }


class FriendCleanerScheduler:
    """
    Manages background scheduled execution of Level 1 Friend Cleaning:
    - Interval timer (in minutes)
    - Target devices
    - Thread-safe execution
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.interval_minutes = 30
        self.target_devices: List[str] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_run_time: Optional[float] = None
        self.next_run_time: Optional[float] = None
        self.history: List[Dict[str, Any]] = []

    def start(self, devices: List[str], interval_minutes: int = 30, run_immediately: bool = True):
        with self.lock:
            self.target_devices = [d.strip() for d in devices if d and d.strip()]
            self.interval_minutes = max(1, interval_minutes)
            self.is_running = True
            self._stop_event.clear()

            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._worker_loop,
                    args=(run_immediately,),
                    name="FriendCleanerScheduler",
                    daemon=True
                )
                self._thread.start()

    def stop(self):
        with self.lock:
            self.is_running = False
            self._stop_event.set()

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            now = time.time()
            remaining_seconds = max(0, int(self.next_run_time - now)) if self.next_run_time else 0
            return {
                "is_running": self.is_running,
                "interval_minutes": self.interval_minutes,
                "target_devices": self.target_devices,
                "last_run": time.strftime("%H:%M:%S", time.localtime(self.last_run_time)) if self.last_run_time else None,
                "next_run_seconds": remaining_seconds,
                "next_run": time.strftime("%H:%M:%S", time.localtime(self.next_run_time)) if self.next_run_time else None,
                "history": self.history[-10:],
            }

    def _worker_loop(self, run_immediately: bool):
        first = True
        while not self._stop_event.is_set():
            if first:
                first = False
                if not run_immediately:
                    with self.lock:
                        self.next_run_time = time.time() + (self.interval_minutes * 60)
                    if self._stop_event.wait(self.interval_minutes * 60):
                        break

            # Execute run on all target devices
            with self.lock:
                devices_to_run = list(self.target_devices)
                self.last_run_time = time.time()
                self.next_run_time = self.last_run_time + (self.interval_minutes * 60)

            for dev in devices_to_run:
                if self._stop_event.is_set():
                    break
                try:
                    # ตรวจสอบและเปิดเกมพร้อมรอให้ถึงหน้า Lobby สะอาด
                    launch_game_and_wait_lobby(dev, timeout=45.0)
                    res = clean_level1_friends(dev, restart_app=True)
                    with self.lock:
                        self.history.append({
                            "time": time.strftime("%H:%M:%S"),
                            "device": dev,
                            "success": res.get("success", False),
                            "ticked": res.get("total_ticked", 0)
                        })
                except Exception as e:
                    print(f"[FriendCleaner] Error on {dev}: {e}", flush=True)
                finally:
                    clear_system_memory(dev, package=GAME_PACKAGE)

            # Wait for next interval
            if self._stop_event.wait(self.interval_minutes * 60):
                break

        with self.lock:
            self.is_running = False


# Global singleton
friend_cleaner_scheduler = FriendCleanerScheduler()


if __name__ == "__main__":
    try:
        from .adb import list_connected_devices
    except ImportError:
        from adb import list_connected_devices

    devs = list_connected_devices()
    if devs:
        target = devs[0]
        print(f"Starting Friend Cleaner flow on {target}...")
        clean_level1_friends(target)
    else:
        print("No connected devices found.")
