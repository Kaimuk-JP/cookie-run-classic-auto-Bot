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
from typing import Dict, List, Optional, Any, Tuple

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
LEVEL_SORT_BUTTON = (565, 150)         # แตะ: (565, 150) ปุ่มกรองเวล
MANAGE_BUTTON = (326, 651)             # แตะ: (326, 651) ปุ่ม manage
FRIEND_ROW_POINTS = [                  # แตะเพื่อนเวลหนึ่งสี่จุด (ที่ปุ่มดาวเลือก)
    (980, 236),
    (980, 340),
    (980, 445),
    (980, 550),
]
CLEAR_SELECTION_BUTTON = (956, 650)    # แตะ: (956, 650) ปุ่มเคลียร์สีแดง (Clear selection)
CONFIRM_REMOVE_BUTTON = (777, 455)     # แตะ: (777, 455) ปุ่มยืนยันลบสีเขียว (Confirm)
MANAGE_CLOSE_BUTTON = (1054, 52)       # แตะ: (1054, 52) ปุ่ม X ออกจากหน้า Manage (Select a friend to remove)
FRIENDS_CLOSE_BUTTON = (1009, 69)      # แตะ: (1009, 69) ปุ่ม X หน้ารายชื่อเพื่อนปกติ กลับสู่หน้าหลัก
GIFT_CLOSE_BUTTON = (1113, 109)        # แตะ: (1113, 109) ปุ่มปิดหน้า gift

# Mailbox & Receive Hearts coordinates (1280x720)
LOBBY_MAILBOX_BUTTON = (686, 677)      # ปุ่มกล่องจดหมายที่หน้าหลัก
MAILBOX_LIVES_TAB = (645, 175)         # แท็บ Lives
MAILBOX_QUICK_RECEIVE = (640, 601)     # ปุ่ม Quick Receive & Send Lives
MAILBOX_CLOSE_BUTTON = (1130, 88)      # ปุ่ม X ปิดกล่องจดหมาย (1130, 88)


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
LVL1_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "level1_badge.png")
NO_LIVES_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "no_lives_text.png")
MAILBOX_TITLE_TEMPLATE = os.path.join(TEMPLATE_DIR, "mailbox_title.png")
NO_LIVES_RECEIVED_TEMPLATE = os.path.join(TEMPLATE_DIR, "no_lives_received.png")
FRIENDS_DIALOG_X_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "FRIENDS_DIALOG_X_BTN.png")
MANAGE_MODE_X_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "MANAGE_MODE_X_BTN.png")

# Global stop event — ถูก set เมื่อกด Stop บน web dashboard
# ทุก loop ใน friend_cleaner จะ check ก่อน action ด้วย _should_stop()
_GLOBAL_STOP_EVENT = threading.Event()


def _should_stop() -> bool:
    """Returns True if user has requested bot to stop. ใช้ check ใน loop ยาวๆ ทุก function."""
    return _GLOBAL_STOP_EVENT.is_set()


def stop_all():
    """Signals all running cleaner loops to stop immediately."""
    _GLOBAL_STOP_EVENT.set()


def reset_stop():
    """Resets the stop signal so new tasks can run."""
    _GLOBAL_STOP_EVENT.clear()

def _adb_tap(device: str, x: int, y: int, jitter: int = 4, delay: float = 0.5):
    if _should_stop():
        return
    target = _format_target(device)
    adb = get_adb_path()
    jx = x + (random.randint(-jitter, jitter) if jitter > 0 else 0)
    jy = y + (random.randint(-jitter, jitter) if jitter > 0 else 0)
    _run_cmd([adb, "-s", target, "shell", "input", "tap", str(jx), str(jy)], timeout=10)
    if delay > 0 and not _should_stop():
        time.sleep(delay)


def _adb_swipe(device: str, x1: int, y1: int, x2: int, y2: int, duration: int = 350, delay: float = 0.8):
    if _should_stop():
        return
    target = _format_target(device)
    adb = get_adb_path()
    _run_cmd([adb, "-s", target, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)], timeout=10)
    if delay > 0 and not _should_stop():
        time.sleep(delay)


def is_all_lives_received_and_sent(screen: Optional[np.ndarray], threshold: float = 0.75) -> bool:
    """
    Detects if the 'All Lives received and sent!' dialog popup is visible on screen.
    """
    if screen is None:
        return False
    p = os.path.join(TEMPLATE_DIR, "ALL_LIVES_RECEIVED_AND_SENT_1.png")
    if not os.path.exists(p):
        return False
    tmpl = cv2.imread(p)
    if tmpl is None:
        return False
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    roi = screen[250:420, 400:880]
    res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
    return float(np.max(res)) >= threshold


def is_no_lives_to_receive(screen: Optional[np.ndarray], threshold: float = 0.75) -> bool:
    """
    Detects if the 'No Lives to receive!' dialog popup is visible on screen.
    When this appears, all lives have been claimed and the receiving routine should stop immediately.
    """
    if screen is None:
        return False
    p = os.path.join(TEMPLATE_DIR, "no_lives_text.png")
    if not os.path.exists(p):
        p = os.path.join(TEMPLATE_DIR, "NO_LIVES_TO_RECEIVE_1.png")
        if not os.path.exists(p):
            return False
    tmpl = cv2.imread(p)
    if tmpl is None:
        return False
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    roi = screen[250:420, 400:880]
    res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
    return float(np.max(res)) >= threshold


def _has_dialog_overlay(screen: np.ndarray) -> bool:
    """
    ตรวจว่าหน้าจอมี modal dialog popup (มีพื้นหลังมืด dimming จริงๆ).
    ใช้เฉพาะ dark corners เพื่อป้องกัน false positive กับ Friends dialog (ขาวแต่ไม่ dim)
    - Modal popup จริง: เกมจะ dim พื้นหลัง → corners มืดลง (< 80)
    - Friends dialog / Mailbox: ไม่ dim corners → corners ยังสว่าง
    """
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))

    # ตรวจ semi-transparent dark overlay: ขอบนอกจอ (corners) มืดกว่าปกติ
    # เมื่อมี modal popup เกมจะ dim พื้นหลัง → corners มืดลงชัดเจน
    corners = [
        screen[0:80, 0:120],        # top-left
        screen[0:80, 1160:1280],    # top-right
        screen[640:720, 0:120],     # bottom-left
        screen[640:720, 1160:1280], # bottom-right
    ]
    corner_brightness = [float(c.mean()) for c in corners]
    avg_corner = sum(corner_brightness) / len(corner_brightness)

    # เมื่อมี dim overlay มุมของจะมืดลง (< 80)
    # Friends dialog / Mailbox ไม่ dim corners → avg_corner จะสูงกว่า
    return avg_corner < 80



def is_turn_off_lives_warning(screen: Optional[np.ndarray]) -> bool:
    """
    ตรวจจับ dialog เตือน "If you turn this off, you won't receive messages from friends!"
    มีปุ่ม Cancel (สีเทา) ทางซ้าย และ Confirm (สีเขียว) ทางขวา
    บอตต้องกด Cancel เสมอ ไม่งั้นจะปิดการรับหัวใจจากเพื่อน!
    """
    if screen is None:
        return False
    h, w = screen.shape[:2]

    # 1. เช็คข้อความบน Pop-up ด้วย Template matching 'TURN_OFF_MSG_DIALOG.png' (multiscale)
    tmpl_msg_path = os.path.join(TEMPLATE_DIR, "TURN_OFF_MSG_DIALOG.png")
    if os.path.exists(tmpl_msg_path):
        tmpl_msg = cv2.imread(tmpl_msg_path)
        if tmpl_msg is not None:
            for s in [0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0, 1.05]:
                ts = cv2.resize(tmpl_msg, (0, 0), fx=s, fy=s)
                if ts.shape[0] <= screen.shape[0] and ts.shape[1] <= screen.shape[1]:
                    res = cv2.matchTemplate(screen, ts, cv2.TM_CCOEFF_NORMED)
                    if float(np.max(res)) >= 0.48:
                        return True

    # 2. ตรวจปุ่ม Cancel สีเทา ทางซ้าย และ Confirm สีเขียว ทางขวา (ในพิกัด 1280x720)
    if (w, h) != (1280, 720):
        screen_1280 = cv2.resize(screen, (1280, 720))
    else:
        screen_1280 = screen

    roi_cancel = screen_1280[425:485, 470:660]
    gray_cancel = (
        (roi_cancel[:, :, 0].astype(int) > 90) & (roi_cancel[:, :, 0].astype(int) < 210) &
        (np.abs(roi_cancel[:, :, 0].astype(int) - roi_cancel[:, :, 1].astype(int)) < 30) &
        (np.abs(roi_cancel[:, :, 1].astype(int) - roi_cancel[:, :, 2].astype(int)) < 30)
    )

    roi_confirm = screen_1280[425:485, 660:870]
    green_confirm = (
        (roi_confirm[:, :, 1] > 130) &
        (roi_confirm[:, :, 0] < 120) &
        (roi_confirm[:, :, 2] < 180)
    )

    # ต้องมีทั้ง Cancel เทา + Confirm เขียว
    if gray_cancel.sum() > 600 and green_confirm.sum() > 600:
        # แยก 'Send a free Life?' vs 'If you turn this off'
        # ถ้ามีข้อความ 'a free Life' แสดงว่าเป็นหน้าต่างส่งใจ ไม่ใช่ turn off warning
        p_free_life = os.path.join(TEMPLATE_DIR, "A_FREE_LIFE_TEXT.png")
        if os.path.exists(p_free_life):
            t_life = cv2.imread(p_free_life)
            if t_life is not None:
                res_life = cv2.matchTemplate(screen_1280[200:320, 420:700], t_life, cv2.TM_CCOEFF_NORMED)
                if float(np.max(res_life)) >= 0.70:
                    return False

        # ถ้ามีปุ่ม X วงกลมเทาที่มุมขวาบน dialog (X:600..680, Y:140..220) แสดงว่าเป็น Send Life dialog
        roi_round_x = screen_1280[140:220, 600:680]
        gray_circ = (roi_round_x[:, :, 0] > 90) & (roi_round_x[:, :, 0] < 180) & \
                    (np.abs(roi_round_x[:, :, 0].astype(int) - roi_round_x[:, :, 1].astype(int)) < 25) & \
                    (np.abs(roi_round_x[:, :, 1].astype(int) - roi_round_x[:, :, 2].astype(int)) < 25)
        white_x = (roi_round_x[:, :, 0] > 220) & (roi_round_x[:, :, 1] > 220) & (roi_round_x[:, :, 2] > 220)
        if gray_circ.sum() > 400 and white_x.sum() > 50:
            return False

        # ไม่มีทั้งปุ่ม X และไม่ใช่ Send Life -> เป็น Turn Off Warning จริง
        return True

    return False


def get_turn_off_lives_cancel_pos() -> Tuple[int, int]:
    """Returns Cancel button center position for 'If you turn this off' dialog."""
    return (560, 452)


def _find_green_confirm_button(screen: Optional[np.ndarray], require_overlay: bool = True) -> Optional[Tuple[int, int]]:
    """
    Detects green Confirm button in center dialog popup area.
    Handles 'Send ... a free Life?', 'All Lives received and sent!', and 'No Lives to receive!'.

    Args:
        require_overlay: True = ต้องมี dark overlay (ใช้ใน lobby context)
                         False = ไม่ต้องมี overlay (ใช้ใน mailbox context)
    """
    if screen is None:
        return None
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))

    # 0. ถ้าเจอ dialog เตือนปิดรับใจ ต้องไม่กด Confirm เด็ดขาด! (return None ทันที)
    if is_turn_off_lives_warning(screen):
        return None

    # 1. Template match CONFIRM_SEND_LIFE_1.png (2-button popup: Cancel / Confirm)
    p_send = os.path.join(TEMPLATE_DIR, "CONFIRM_SEND_LIFE_1.png")
    if os.path.exists(p_send):
        tmpl = cv2.imread(p_send)
        if tmpl is not None:
            res = cv2.matchTemplate(screen[300:580, 400:960], tmpl, cv2.TM_CCOEFF_NORMED)
            if float(np.max(res)) >= 0.72:
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                th, tw = tmpl.shape[:2]
                return (400 + max_loc[0] + tw // 2, 300 + max_loc[1] + th // 2)

    # 2. Template match CONFIRM_BUTTON_1.png (1-button popup)
    p_conf = os.path.join(TEMPLATE_DIR, "CONFIRM_BUTTON_1.png")
    if os.path.exists(p_conf):
        tmpl = cv2.imread(p_conf)
        if tmpl is not None:
            res = cv2.matchTemplate(screen[300:580, 380:900], tmpl, cv2.TM_CCOEFF_NORMED)
            if float(np.max(res)) >= 0.70:
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                th, tw = tmpl.shape[:2]
                return (380 + max_loc[0] + tw // 2, 300 + max_loc[1] + th // 2)

    # 3. Check if popup title is visible (No Lives or All Lives)
    if is_no_lives_to_receive(screen) or is_all_lives_received_and_sent(screen):
        return (640, 462)

    # 4. Color detection for green Confirm button
    #    require_overlay=True: ใช้ใน lobby — ต้องมี dark overlay ก่อน (ป้องกัน false positive)
    #    require_overlay=False: ใช้ใน mailbox — ไม่ต้องการ overlay (mailbox มี popup สีเขียวจริงเสมอ)
    if not require_overlay or _has_dialog_overlay(screen):
        # ค้นหาใน range ที่กว้างขึ้น เพื่อครอบ dialog ทั้งใน lobby และ mailbox
        roi_btn = screen[350:530, 440:870]
        green = (roi_btn[:, :, 1] > 150) & (roi_btn[:, :, 0] < 110) & (roi_btn[:, :, 2] < 180)
        if green.sum() > (1200 if not require_overlay else 2500):
            ys, xs = np.where(green)
            return (int(xs.mean()) + 440, int(ys.mean()) + 350)

    return None


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


def is_no_lives_received_screen(screen: Optional[np.ndarray]) -> bool:
    """Check if mailbox is on Lives tab and displays 'No Lives received!'"""
    if screen is None:
        return False
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    if os.path.exists(NO_LIVES_RECEIVED_TEMPLATE):
        t = cv2.imread(NO_LIVES_RECEIVED_TEMPLATE)
        if t is not None:
            res = cv2.matchTemplate(screen[400:600, 450:850], t, cv2.TM_CCOEFF_NORMED)
            if float(np.max(res)) >= 0.75:
                return True
    return False


def is_mailbox_open(screen: Optional[np.ndarray]) -> bool:
    """
    Check if the Mailbox dialog is currently open on screen.
    1. Must not be at Lobby.
    2. Check the teal header title 'Mailbox' (X: 480..750, Y: 60..150).
    3. Check the green 'Quick Receive & Send Lives' button area: (X: 400..880, Y: 580..620).
    4. If modal popup is active over mailbox (Confirm button present), returns True.
    5. If 'No Lives received!' empty text is displayed, returns True.
    """
    if screen is None or is_at_lobby(screen):
        return False
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))

    # 1. Check header title "Mailbox"
    if os.path.exists(MAILBOX_TITLE_TEMPLATE):
        t = cv2.imread(MAILBOX_TITLE_TEMPLATE)
        if t is not None and t.shape[0] <= screen.shape[0] and t.shape[1] <= screen.shape[1]:
            res = cv2.matchTemplate(screen[60:150, 480:750], t, cv2.TM_CCOEFF_NORMED)
            if float(np.max(res)) >= 0.75:
                return True

    # 2. Quick Receive button green
    roi = screen[580:620, 400:880]
    green = (roi[:, :, 1] > 130) & (roi[:, :, 0] < 110) & (roi[:, :, 2] < 160)
    if green.sum() > 1000:
        return True

    # 3. If Confirm dialog is open inside mailbox
    if _find_green_confirm_button(screen) is not None:
        return True

    # 4. Check "No Lives received!" empty state
    if is_no_lives_received_screen(screen):
        return True

    return False


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
    if screen is None or is_at_lobby(screen) or is_mailbox_open(screen):
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
    Must NOT be Lobby, and must NOT be Mailbox.
    """
    if screen is None or is_at_lobby(screen) or is_mailbox_open(screen):
        return False
    if is_in_manage_friends_mode(screen) is not None:
        return True
    if find_normal_friends_close_btn(screen) is not None:
        return True
    # Check for cyan Manage button at (326, 651) in normal friends dialog
    h, w = screen.shape[:2]
    if (w, h) != (1280, 720):
        screen = cv2.resize(screen, (1280, 720))
    manage_roi = screen[630:680, 240:370]
    cyan = (manage_roi[:, :, 0] > 130) & (manage_roi[:, :, 1] > 130) & (manage_roi[:, :, 2] < 100)
    if cyan.sum() > 2500:
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
    # อย่าแตะปิดถ้าหน้าต่างที่เปิดอยู่คือกล่องข้อความหรือหน้าต่างเพื่อน
    if is_mailbox_open(img) or is_friends_dialog_open(img):
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
        if _should_stop():
            _log("🛑 [Stop] ได้รับคำสั่งหยุด -> ออกจาก clear_all_lobby_popups")
            return False
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

        # 3. ตรวจ dialog เตือนปิดรับใจจากเพื่อน -> ต้องกด Cancel ก่อนทุกกรณี!
        if is_turn_off_lives_warning(screen):
            cancel_pos = get_turn_off_lives_cancel_pos()
            _log(f"⚠️⚠️⚠️ ตรวจพบ dialog 'ปิดรับใจจากเพื่อน' -> กด Cancel ที่ {cancel_pos} ห้ามกด Confirm!")
            _adb_tap(device, cancel_pos[0], cancel_pos[1], jitter=2, delay=1.5)
            continue

        # 4. ปิด Friends/Manage dialog ก่อน Confirm check เสมอ!
        #    เพื่อป้องกัน false positive กดปุ่ม toggle ส่งใจ/รับใจใน Friends list
        if is_in_manage_friends_mode(screen) is not None:
            _log("⚡ ตรวจพบหน้าจัดการเพื่อนค้างอยู่ -> แตะปิดที่ (1054, 52)...")
            _adb_tap(device, 1054, 52, jitter=1, delay=1.2)
            continue
        if is_friends_dialog_open(screen):
            _log("⚡ ตรวจพบหน้าต่างเพื่อนค้างอยู่ -> แตะปิดที่ (1009, 69)...")
            _adb_tap(device, 1009, 69, jitter=1, delay=1.2)
            continue

        # 5. ตรวจสอบว่าถึงหน้า Lobby สะอาดเรียบร้อยแล้ว (ตรวจก่อน Confirm check เพื่อป้องกันแตะโดนปุ่มในล็อบบี้)
        if is_at_lobby(screen):
            time.sleep(0.8)
            chk = device_capture_screen(device)
            if chk is not None and check_banner_or_news_popup(chk) is None and not check_select_mode_popup(chk):
                _log("✅ ยืนยันหน้าล็อบบี้สะอาดเรียบร้อย 100%!")
                return True

        # 6. ตรวจสอบปุ่ม Confirm สีเขียวกลางจอ (เฉพาะเมื่อมี Modal Pop-up เท่านั้น)
        btn = _find_green_confirm_button(screen, require_overlay=True)
        if btn is not None:
            _log(f"⚡ ตรวจพบ Pop-up กลางจอ -> แตะ Confirm ที่ {btn}...")
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=1.2)
            continue

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


def is_game_process_running(device: str) -> bool:
    """Check if CookieRun game process is currently running."""
    target = _format_target(device)
    adb = get_adb_path()
    for pkg in [GAME_PACKAGE, "com.devsisters.crg", "com.linecorp.LGCOOKIE"]:
        try:
            res = _run_cmd([adb, "-s", target, "shell", "pidof", pkg], capture_output=True, text=True, timeout=5)
            if res.stdout and res.stdout.strip():
                return True
        except Exception:
            pass
    return False


def start_game_app(device: str, log_func=None):
    """Launch CookieRun app on device."""
    target = _format_target(device)
    adb = get_adb_path()
    if log_func:
        log_func(f"สั่งเปิดเกม Cookie Run บนจอ {device}...")
    else:
        print(f"[{time.strftime('%H:%M:%S')}][AppControl][{device}] สั่งเปิดเกม Cookie Run...", flush=True)
    for pkg in [GAME_PACKAGE, "com.devsisters.crg", "com.linecorp.LGCOOKIE"]:
        try:
            res = _run_cmd([adb, "-s", target, "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True, timeout=10)
            if res.stdout and "Events injected: 1" in res.stdout:
                break
        except Exception:
            pass


def launch_game_and_wait_lobby(device: str, timeout: float = 60.0, log_func=None) -> bool:
    """
    เปิดเกม Cookie Run และรอจนกว่าจะโหลดเสร็จ พร้อมเคลียร์หน้าข่าว/แบนเนอร์/Pop-up อัตโนมัติ
    """
    start_game_app(device, log_func=log_func)
    for _ in range(50):
        if _should_stop():
            return False
        time.sleep(0.1)
    return clear_all_lobby_popups(device, max_wait=timeout, log_func=log_func)


def ensure_game_at_lobby(device: str, timeout: float = 60.0, log_func=None) -> bool:
    """
    ตรวจว่าเกมเปิดอยู่และอยู่ที่หน้าล็อบบี้พร้อมทำงานหรือไม่:
    - ถ้าอยู่ที่หน้าล็อบบี้แล้ว -> return True ทันที
    - ถ้าเกมยังไม่เปิด (หน้า Home) -> สั่งเปิดเกมทันทีและรอจนกว่าจะถึงหน้าล็อบบี้
    - ถ้าเกมเปิดอยู่แต่ติด popup/โหลด -> เคลียร์ popup จนถึงหน้าล็อบบี้
    """
    if _should_stop():
        return False

    def _l(msg: str):
        if log_func:
            log_func(msg)
        else:
            print(f"[{time.strftime('%H:%M:%S')}][AppControl][{device}] {msg}", flush=True)

    # 1. ตรวจสอบว่าหน้าจออยู่ที่ล็อบบี้อยู่แล้วหรือไม่
    screen = device_capture_screen(device)
    if screen is not None and is_at_lobby(screen):
        _l("   ✅ ตรวจพบหน้าจออยู่ที่ล็อบบี้เรียบร้อยแล้ว")
        return True

    # 2. ตรวจสอบว่าแอปเกมเปิดอยู่หรือไม่ (ถ้าอยู่หน้า Home / เกมปิด)
    if not is_game_process_running(device):
        _l("🚀 ตรวจพบหน้าจออยู่หน้าโฮม (เกมปิดอยู่) -> สั่งเปิดเกม Cookie Run ทันที...")
        return launch_game_and_wait_lobby(device, timeout=timeout, log_func=log_func)

    # 3. แอปเปิดอยู่แต่อาจติดหน้าข่าวสาร/แบนเนอร์/Popup
    _l("🔍 ตรวจพบเกมเปิดอยู่ กำลังเคลียร์ Pop-up และรอหน้าล็อบบี้...")
    if clear_all_lobby_popups(device, max_wait=15.0, log_func=log_func):
        chk = device_capture_screen(device)
        if chk is not None and is_at_lobby(chk):
            _l("   ✅ เข้าสู่หน้าล็อบบี้เรียบร้อยแล้ว!")
            return True

    # 4. ถ้ายังไม่ถึงล็อบบี้ ให้เปิดเกมใหม่
    _l("🔄 ยังไม่สามารถเข้าสู่หน้าล็อบบี้ได้ สั่งเปิดเกมใหม่...")
    return launch_game_and_wait_lobby(device, timeout=timeout, log_func=log_func)


def wait_for_lobby(device: str, timeout: float = 15.0, log_func=None) -> bool:
    """
    Waits until the device screen is confirmed to be at the Lobby.
    If news/banner popups appear, clears them automatically.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if _should_stop():
            return False
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
        for _ in range(10):
            if _should_stop():
                return False
            time.sleep(0.1)
    return False


def receive_mailbox_hearts(device: str, log_func=None) -> bool:
    """
    Open Mailbox, receive all lives/hearts and return lives to friends before deleting friends.
    ตรวจจอก่อนกด และตรวจจอหลังกดทุกขั้นตอน:
      - ตรวจสอบหน้าล็อบบี้ก่อนเปิดกล่องข้อความ
      - ยืนยันว่าหน้าต่าง Mailbox เปิดจริงก่อนกดปุ่มภายใน
      - แตะ Quick Receive & Send Lives
      - กดยืนยัน Pop-up ส่งใจให้เพื่อนต่อเนื่องจนหมด
      - ปิดกล่องข้อความและยืนยันกลับสู่หน้าล็อบบี้ 100%
    """
    def _log(msg: str):
        if log_func:
            log_func(f"[ReceiveHearts][{device}] {msg}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}][ReceiveHearts][{device}] {msg}", flush=True)

    if _should_stop():
        _log("🛑 [Stop] ได้รับคำสั่งหยุด -> ยกเลิกการรับหัวใจทันที")
        return False

    # 1. ตรวจจอก่อนกด: ตรวจสอบความพร้อมที่หน้าล็อบบี้ (ถ้าอยู่หน้าโฮมจะสั่งเปิดเกมทันที)
    _log("💌 1. ตรวจสอบหน้าจอ: ตรวจสอบความพร้อมที่หน้าล็อบบี้ก่อนเปิดกล่องข้อความ...")
    if not ensure_game_at_lobby(device, timeout=60.0, log_func=_log):
        if _should_stop():
            _log("🛑 [Stop] ได้รับคำสั่งหยุด -> ยกเลิกการทำงานทันที")
        else:
            _log("⚠️ ไม่สามารถเปิดเกมหรือเข้าหน้าล็อบบี้ได้ ยกเลิกขั้นตอนรับหัวใจเพื่อความปลอดภัย")
        return False

    if _should_stop():
        _log("🛑 [Stop] ได้รับคำสั่งหยุด -> ยกเลิกการเปิดกล่องข้อความ")
        return False

    mailbox_opened = False
    for attempt in range(5):
        if _should_stop():
            _log("🛑 [Stop] ได้รับคำสั่งหยุด ระหว่างเปิดกล่องข้อความ -> ยกเลิกทันที")
            return False
        screen = device_capture_screen(device)
        if is_mailbox_open(screen):
            _log("   ✅ ตรวจพบกล่องข้อความ (Mailbox) เปิดอยู่แล้ว!")
            mailbox_opened = True
            break
        _log(f"   แตะ: ({LOBBY_MAILBOX_BUTTON[0]}, {LOBBY_MAILBOX_BUTTON[1]}) ปุ่มกล่องข้อความ (รอบที่ {attempt + 1})...")
        _adb_tap(device, LOBBY_MAILBOX_BUTTON[0], LOBBY_MAILBOX_BUTTON[1], jitter=2, delay=1.5)
        if _should_stop():
            return False
        screen_chk = device_capture_screen(device)
        if is_mailbox_open(screen_chk):
            _log("   ✅ ตรวจพบกล่องข้อความ (Mailbox) เปิดขึ้นมาแล้ว!")
            mailbox_opened = True
            break
        for _ in range(8):
            if _should_stop():
                return False
            time.sleep(0.1)

    if not mailbox_opened:
        if _should_stop():
            _log("🛑 [Stop] ได้รับคำสั่งหยุด -> ยกเลิกขั้นตอนรับหัวใจ")
            return False
        _log("⚠️ ไม่สามารถเปิดกล่องข้อความได้ หรือหน้าจอไม่ตรง ข้ามขั้นตอนรับหัวใจเพื่อความปลอดภัย")
        return False

    _log("💌 2. กดแท็บ Lives...")
    _adb_tap(device, MAILBOX_LIVES_TAB[0], MAILBOX_LIVES_TAB[1], jitter=2, delay=1.0)

    # ตรวจจอทันที: ถ้าขึ้น 'No Lives to receive!' หรือ 'No Lives received!' อยู่แล้ว
    screen = device_capture_screen(device)
    if is_no_lives_to_receive(screen) or is_no_lives_received_screen(screen):
        _log("   🛑 ตรวจพบไม่มีหัวใจค้างในกล่องข้อความ (No Lives) -> ปิดกล่องข้อความทันที")
        btn = _find_green_confirm_button(screen, require_overlay=False)
        if btn is not None:
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=0.8)

        _log("💌 ปิดกล่องข้อความกลับสู่หน้าหลัก...")
        _adb_tap(device, MAILBOX_CLOSE_BUTTON[0], MAILBOX_CLOSE_BUTTON[1], jitter=1, delay=1.2)
        clear_all_lobby_popups(device, max_wait=5.0, log_func=_log)
        wait_for_lobby(device, timeout=6.0, log_func=_log)
        return True

    _log("💌 3. แตะปุ่ม Quick Receive & Send Lives และยืนยันรับ-ส่งใจ...")
    _adb_tap(device, MAILBOX_QUICK_RECEIVE[0], MAILBOX_QUICK_RECEIVE[1], jitter=2, delay=1.8)

    total_confirmed = 0
    no_confirm_streak = 0
    max_rounds = 60  # เพิ่มรอบสำรองกรณีมีเพื่อนเยอะ

    for round_num in range(1, max_rounds + 1):
        if _should_stop():
            _log("   🛑 [Stop] ได้รับคำสั่งหยุด -> ออกจาก receive loop")
            break
        screen = device_capture_screen(device)
        if is_at_lobby(screen):
            _log("   ✅ ตรวจพบว่าอยู่ที่หน้าล็อบบี้แล้ว")
            break

        # 0. ตรวจสอบ Pop-up เตือนปิดการรับใจ ("If you turn this off...") -> ต้องกด Cancel เสมอ! ห้ามกด Confirm!
        if is_turn_off_lives_warning(screen):
            cancel_pos = get_turn_off_lives_cancel_pos()
            _log(f"   🛑 ตรวจพบ Pop-up ประเภท: เตือนปิดรับใจ ('If you turn this off...') -> กด Cancel ที่ {cancel_pos} ทันที! (ไม่กด Confirm เพื่อรักษาการรับหัวใจ)")
            _adb_tap(device, cancel_pos[0], cancel_pos[1], jitter=2, delay=1.2)
            continue

        # 1. ตรวจสอบ Pop-up 'No Lives to receive!' หรือ 'All Lives received!'
        if is_no_lives_to_receive(screen) or is_all_lives_received_and_sent(screen):
            _log("   🛑 ตรวจพบ Pop-up ประเภท: สิ้นสุดการรับใจ (No Lives / All Lives received) -> กดยืนยันปิด")
            btn = _find_green_confirm_button(screen, require_overlay=False)
            if btn is not None:
                _adb_tap(device, btn[0], btn[1], jitter=2, delay=1.0)
            break

        # 2. ตรวจสอบปุ่มยืนยันสีเขียว (Confirm ส่งใจให้เพื่อนรายคน)
        btn = _find_green_confirm_button(screen, require_overlay=False)
        if btn is not None:
            _log(f"   👉 ตรวจพบ Pop-up ประเภท: ยืนยันส่งใจคืนเพื่อน ('Send a free Life?') -> กด Confirm ที่ {btn} (ครั้งที่ {total_confirmed + 1})...")
            _adb_tap(device, btn[0], btn[1], jitter=2, delay=1.2)
            total_confirmed += 1
            no_confirm_streak = 0
            continue

        # ถ้าไม่เจอปุ่มทันที ให้รอนานขึ้นเผื่อ animation Pop-up ถัดไป
        _log(f"   ⏳ ไม่พบ Confirm ทันที รอ animation... (streak={no_confirm_streak+1})")
        time.sleep(1.2)
        if _should_stop():
            _log("   🛑 [Stop] ได้รับคำสั่งหยุด -> ออกจาก receive loop")
            break
        screen_retry = device_capture_screen(device)

        # ตรวจอีกครั้ง: เตือนปิดรับใจ
        if is_turn_off_lives_warning(screen_retry):
            cancel_pos = get_turn_off_lives_cancel_pos()
            _log(f"   🛑 [retry] ตรวจพบ Pop-up ประเภท: เตือนปิดรับใจ -> กด Cancel ที่ {cancel_pos} ทันที!")
            _adb_tap(device, cancel_pos[0], cancel_pos[1], jitter=2, delay=1.2)
            continue

        # ตรวจอีกครั้ง: No Lives / All Lives received
        if is_no_lives_to_receive(screen_retry) or is_all_lives_received_and_sent(screen_retry):
            _log("   🛑 [retry] ตรวจพบ Pop-up ประเภท: สิ้นสุดการรับใจ -> กดยืนยันและออก")
            btn2 = _find_green_confirm_button(screen_retry, require_overlay=False)
            if btn2 is not None:
                _adb_tap(device, btn2[0], btn2[1], jitter=2, delay=1.0)
            break

        btn_retry = _find_green_confirm_button(screen_retry, require_overlay=False)
        if btn_retry is not None:
            _log(f"   👉 [retry] ตรวจพบ Pop-up ประเภท: ยืนยันส่งใจคืนเพื่อน -> กด Confirm ที่ {btn_retry} (ครั้งที่ {total_confirmed + 1})...")
            _adb_tap(device, btn_retry[0], btn_retry[1], jitter=2, delay=1.2)
            total_confirmed += 1
            no_confirm_streak = 0
            continue

        no_confirm_streak += 1
        # เพิ่ม threshold เป็น 5 เพื่อป้องกันออกก่อนเวลา (บางครั้ง popup ช้ามาก)
        if no_confirm_streak >= 5:
            _log(f"   ✨ ไม่มีปุ่มยืนยัน (Confirm) ขึ้นมาอีก {no_confirm_streak} รอบซ้อน -> รับหัวใจทั้งหมดสำเร็จ!")
            break

    # 3.5 Final sweep: รอ animation สุดท้ายแล้วตรวจอีกรอบก่อนปิด
    _log("💌 3.5 Final sweep: รอ animation สุดท้ายและตรวจ popup ที่เหลืออยู่...")
    time.sleep(1.5)
    for sweep_i in range(8):  # ตรวจสูงสุด 8 รอบ
        if _should_stop():
            break
        screen_sw = device_capture_screen(device)
        if screen_sw is None:
            break
        if is_at_lobby(screen_sw):
            break
        if is_turn_off_lives_warning(screen_sw):
            cancel_pos = get_turn_off_lives_cancel_pos()
            _log(f"   🛑 [Final sweep] ตรวจพบ Pop-up ประเภท: เตือนปิดรับใจ -> กด Cancel ที่ {cancel_pos}!")
            _adb_tap(device, cancel_pos[0], cancel_pos[1], jitter=2, delay=1.2)
            continue
        btn_sw = _find_green_confirm_button(screen_sw, require_overlay=False)
        if btn_sw is not None:
            _log(f"   🔁 [Final sweep {sweep_i+1}] พบ Confirm popup ที่ {btn_sw} -> กด")
            _adb_tap(device, btn_sw[0], btn_sw[1], jitter=2, delay=1.2)
            total_confirmed += 1
            time.sleep(1.2)  # รอ animation ถัดไป
        elif is_no_lives_to_receive(screen_sw) or is_all_lives_received_and_sent(screen_sw):
            _log("   🛑 [Final sweep] พบสัญญาณสิ้นสุด -> กดยืนยันและออก")
            btn_end = _find_green_confirm_button(screen_sw, require_overlay=False)
            if btn_end:
                _adb_tap(device, btn_end[0], btn_end[1], jitter=2, delay=1.0)
            break
        else:
            # ไม่มี popup แล้ว -> หยุด sweep
            break

    # 4. ออกจากรับใจตรวจจอ: ตรวจจอก่อนแตะปิด และตรวจจอหลังแตะปิด
    _log(f"💌 4. ปิดกล่องข้อความกลับสู่หน้าหลัก (กดยืนยันไปทั้งหมด {total_confirmed} ครั้ง)...")
    for close_attempt in range(8):
        if _should_stop():
            _log("   🛑 [Stop] ได้รับคำสั่งหยุด -> ออกจาก mailbox close loop")
            break
        screen_curr = device_capture_screen(device)
        if is_at_lobby(screen_curr):
            _log("   ✅ ตรวจจอพบว่าอยู่ที่หน้าล็อบบี้แล้ว 100%")
            break

        if is_turn_off_lives_warning(screen_curr):
            cancel_pos = get_turn_off_lives_cancel_pos()
            _log(f"   🛑 [Close Mailbox] ตรวจพบ Pop-up ประเภท: เตือนปิดรับใจ -> กด Cancel ที่ {cancel_pos}!")
            _adb_tap(device, cancel_pos[0], cancel_pos[1], jitter=2, delay=1.2)
            continue

        # ถ้ายังมี Confirm popup ค้างอยู่ ต้องกดยืนยันก่อนปิด Mailbox เสมอ!
        btn = _find_green_confirm_button(screen_curr, require_overlay=False)
        if btn is not None:
            _log(f"   👉 กดปุ่มยืนยัน Pop-up ที่ค้างอยู่: {btn} (close_attempt={close_attempt})")
            _adb_tap(device, btn[0], btn[1], jitter=1, delay=1.2)
            total_confirmed += 1
            time.sleep(1.0)  # รอดูว่ามี popup ถัดมาไหม
            continue

        if is_mailbox_open(screen_curr):
            _log(f"   แตะ: ({MAILBOX_CLOSE_BUTTON[0]}, {MAILBOX_CLOSE_BUTTON[1]}) ปุ่มปิดกล่องข้อความ (รอบ {close_attempt + 1})")
            _adb_tap(device, MAILBOX_CLOSE_BUTTON[0], MAILBOX_CLOSE_BUTTON[1], jitter=1, delay=1.5)
        else:
            # ถ้าเป็น Pop-up อื่นๆ ให้ปิด
            clear_all_lobby_popups(device, max_wait=3.0, log_func=_log)
        time.sleep(0.8)

    clear_all_lobby_popups(device, max_wait=4.0, log_func=_log)
    wait_for_lobby(device, timeout=6.0, log_func=_log)
    _log(f"✅ รับหัวใจจากกล่องข้อความเรียบร้อย 100%! (ยืนยันรวม {total_confirmed} ครั้ง)")
    return True

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
    _log("🧹 เริ่มกระบวนการรับหัวใจและลบเพื่อนเวล 1...")
    _log("==========================================")

    # ตรวจสอบสถานะเกม: มั่นใจว่าเกมเปิดอยู่และถึงหน้าล็อบบี้เรียบร้อยก่อนเริ่ม (ถ้าอยู่หน้าโฮมจะสั่งเปิดเกม)
    _log("🔍 ตรวจสอบสถานะเกม: รอให้เกมแสดงผลหน้าล็อบบี้ (ถ้าอยู่หน้าโฮมจะสั่งเปิดเกม)...")
    if not ensure_game_at_lobby(device, timeout=60.0, log_func=_log):
        if _should_stop():
            _log("🛑 [Stop] ได้รับคำสั่งหยุด -> ยกเลิกการทำงาน")
            return {"success": False, "total_ticked": 0, "stopped": True}
        _log("❌ ไม่สามารถเปิดเกมหรือเข้าสู่หน้าล็อบบี้ได้ ยกเลิกขั้นตอนลบเพื่อนเพื่อความปลอดภัย")
        return {"success": False, "message": "Failed to reach lobby"}
    time.sleep(0.5)

    # 0. รับหัวใจจากกล่องข้อความก่อนลบเพื่อน
    _log("0. [เตรียมตัว] เปิดกล่องข้อความเพื่อรับหัวใจและส่งหัวใจกลับให้เพื่อนก่อนลบ...")
    receive_mailbox_hearts(device, log_func=_log)
    time.sleep(0.8)

    if _should_stop():
        _log("🛑 [Stop] ได้รับคำสั่งหยุด หลังรับหัวใจเสร็จสิ้น -> ยกเลิกขั้นตอนลบเพื่อนทันที")
        return {"success": False, "total_ticked": 0, "stopped": True}

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

    # 2. กดเข้า Manage Friends mode
    _log("2. ตรวจสอบหน้าต่าง Friends และเข้าสู่โหมด Manage Friends...")
    manage_opened = False
    for manage_attempt in range(5):
        screen = device_capture_screen(device)
        if is_in_manage_friends_mode(screen) is not None:
            _log("   ✅ อยู่ในหน้า Manage Friends เรียบร้อยแล้ว!")
            manage_opened = True
            break

        # ตรวจสอบว่ามี Pop-up แจ้งเตือนขึ้นบังจอ (เช่น Search failed!) หรือไม่
        conf_btn = _find_green_confirm_button(screen)
        if conf_btn is not None:
            _log(f"   ⚡ พบหน้าต่างแจ้งเตือนกลางจอ แตะ Confirm ที่ {conf_btn}...")
            _adb_tap(device, conf_btn[0], conf_btn[1], jitter=1, delay=1.2)
            continue

        if not is_friends_dialog_open(screen):
            _log("   ⚠️ หน้าต่าง Friends ปิดไปแล้ว พยายามเปิดใหม่...")
            _adb_tap(device, LOBBY_FRIENDS_BUTTON[0], LOBBY_FRIENDS_BUTTON[1], jitter=1, delay=1.5)
            continue
        _log(f"   แตะ: ({MANAGE_BUTTON[0]}, {MANAGE_BUTTON[1]}) ปุ่ม Manage (รอบที่ {manage_attempt + 1})...")
        _adb_tap(device, MANAGE_BUTTON[0], MANAGE_BUTTON[1], jitter=1, delay=1.2)
        screen_after = device_capture_screen(device)
        if is_in_manage_friends_mode(screen_after) is not None:
            _log("   ✅ เข้าสู่หน้า Manage Friends เรียบร้อยแล้ว!")
            manage_opened = True
            break
        time.sleep(0.5)

    if not manage_opened:
        _log("❌ ไม่สามารถเข้าสู่หน้า Manage Friends ได้ ยกเลิกเพื่อความปลอดภัย ไม่แตะปุ่มใดๆ มั่วเด็ดขาด")
        close_btn = find_friends_dialog_close_btn(device_capture_screen(device))
        if close_btn:
            _adb_tap(device, close_btn[0], close_btn[1], jitter=1, delay=1.0)
        return {"success": False, "message": "Failed to enter Manage Friends mode"}

    # 3. ปรับการเรียงลำดับ (Sort by Level)
    _log("3. ตรวจสอบหน้าจอเพื่อปรับการเรียงลำดับเลเวล (Sort by Level)...")
    lvl1_found = False
    for sort_attempt in range(1, 6):
        screen = device_capture_screen(device)
        if is_in_manage_friends_mode(screen) is None:
            _log("⚠️ หลุดออกจากหน้า Manage Friends! หยุดขั้นตอนการกรอง")
            break
        badges = detect_level1_badges(screen)
        if len(badges) > 0:
            _log(f"   ✅ [ตรวจจอก่อนกด: พบเวล 1] จำนวน {len(badges)} คนบนหน้าจอแล้ว! การเรียงลำดับถูกต้อง")
            lvl1_found = True
            break

        _log(f"   🔍 [รอบที่ {sort_attempt}/5: ยังไม่พบเวล 1] แตะปุ่มกรองเวล ({LEVEL_SORT_BUTTON[0]}, {LEVEL_SORT_BUTTON[1]})...")
        _adb_tap(device, LEVEL_SORT_BUTTON[0], LEVEL_SORT_BUTTON[1], jitter=1, delay=1.2)

        screen_after_sort = device_capture_screen(device)
        badges_after = detect_level1_badges(screen_after_sort)
        if len(badges_after) > 0:
            _log(f"   ✅ [ตรวจจอหลังกดกรอง: สำเร็จ] พบเพื่อนเวล 1 จำนวน {len(badges_after)} คนทันที!")
            lvl1_found = True
            break
        time.sleep(0.5)

    if not lvl1_found:
        _log("ℹ️ ตรวจสอบหน้าจอครบ 5 ครั้งแล้ว ไม่พบเพื่อนเลเวล 1 บนหน้าจอ (อาจไม่มีเพื่อนเวล 1 ในไอดีนี้)")

    # 4. แตะติ๊กเลือกเพื่อนเวล 1
    total_ticked = 0
    consecutive_empty_scrolls = 0
    # 4. กระบวนการลบเพื่อนเวล 1 ทีละชุด (Batch Deletion):
    # เมื่อจัดเรียง Level ▲ เพื่อนเวล 1 จะอยู่ด้านบนสุดเสมอ
    # เมื่อเลือกลบแล้ว รายชื่อด้านล่างจะเลื่อนขึ้นมาแทนที่ด้านบนอัตโนมัติ
    # จึงเลือกลบทีละชุดทันที โดยไม่ต้องเลื่อนจอลงไปไกล ทำให้ไม่เลื่อนมั่วและลบได้หมดจด 100%
    total_deleted = 0
    max_batches = 75  # รองรับลบได้ถึง 75x4 = 300 คน
    consecutive_no_lvl1 = 0

    _log("4. เริ่มกระบวนการลบเพื่อนเวล 1 ทีละชุด (Batch Deletion)...")

    for batch_idx in range(1, max_batches + 1):
        if _should_stop():
            _log("🛑 [Stop] ได้รับคำสั่งหยุด ระหว่างขั้นตอนลบเพื่อน -> ออกจากลูปทันที")
            break
        screen = device_capture_screen(device)
        if screen is None:
            time.sleep(0.5)
            continue

        # CRITICAL GUARD: ต้องอยู่ในหน้า Manage Friends เท่านั้น ห้ามแตะหน้าอื่นเด็ดขาด!
        if is_in_manage_friends_mode(screen) is None:
            _log("⚠️ หน้าจอไม่ได้อยู่ในหน้า Manage Friends แล้ว! หยุดการทำงานทันทีเพื่อความปลอดภัย")
            break

        badges = detect_level1_badges(screen)

        if len(badges) == 0:
            consecutive_no_lvl1 += 1
            if consecutive_no_lvl1 >= 2:
                _log("   ✨ ตรวจสอบแล้วไม่พบเพื่อนเลเวล 1 บนหน้าจออีกต่อไป -> ลบครบหมดเกลี้ยง 100%!")
                break
            # เผื่อติดขอบเล็กน้อย ลองสะกิดเลื่อนขึ้นเบาๆ กลับมาบนสุด
            _adb_swipe(device, 500, 300, 500, 450, duration=250, delay=0.5)
            continue

        consecutive_no_lvl1 = 0
        _log(f"   [ชุดที่ {batch_idx}] ตรวจพบเพื่อนเวล 1 บนหน้าจอ {len(badges)} คน กำลังเลือก...")

        # แตะเลือกเพื่อนเลเวล 1 แต่ละแถว (แตะที่กึ่งกลางแถว X=500 เพื่อความแม่นยำ)
        selected_count = 0
        for pt in FRIEND_ROW_POINTS:
            px, py = pt[0], pt[1]
            has_lvl1 = any(abs(b_y - (py - 40)) < 65 for b_y in badges)
            if not has_lvl1:
                continue

            # ตรวจสอบสีพิกเซลก่อนกด ถ้ายังไม่เป็นสีชมพู/แดง (ยังไม่เลือก)
            b, g, r = screen[py, px]
            is_selected = (int(r) - int(g) > 25) and (int(r) - int(b) > 25)
            if not is_selected:
                _adb_tap(device, 500, py, jitter=2, delay=0.2)
                selected_count += 1

        # เก็บตกแถวที่ตรวจเจอ Level 1 badge แต่ไม่ตรงจุดหลัก 4 จุด
        screen_after_tap = device_capture_screen(device)
        if screen_after_tap is not None:
            badges_after = detect_level1_badges(screen_after_tap)
            for b_y in badges_after:
                if not is_row_selected(screen_after_tap, b_y):
                    _adb_tap(device, 500, b_y + 20, jitter=2, delay=0.2)
                    selected_count += 1

        # แตะปุ่ม Clear selection (956, 650) เพื่อสั่งลบชุดนี้
        _log(f"   👉 [ชุดที่ {batch_idx}] แตะปุ่มลบ (Clear selection)...")
        _adb_tap(device, CLEAR_SELECTION_BUTTON[0], CLEAR_SELECTION_BUTTON[1], jitter=1, delay=1.0)

        # ตรวจหาปุ่มยืนยัน Confirm สีเขียว
        screen_confirm = device_capture_screen(device)
        conf_btn = _find_green_confirm_button(screen_confirm)
        conf_coord = conf_btn if conf_btn is not None else CONFIRM_REMOVE_BUTTON
        _log(f"   👉 [ชุดที่ {batch_idx}] แตะยืนยัน Confirm...")
        _adb_tap(device, conf_coord[0], conf_coord[1], jitter=1, delay=2.0)

        total_deleted += selected_count
        _log(f"   ✅ [ชุดที่ {batch_idx}] ลบเพื่อนเลเวล 1 ชุดนี้เรียบร้อย (สะสม ~{total_deleted} คน)")
        time.sleep(0.6)

    _log(f"🎉 เสร็จสิ้นขั้นตอนลบเพื่อนเลเวล 1 ทั้งหมด (~{total_deleted} รายการ)")

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
        "total_ticked": total_deleted,
        "message": f"ลบเพื่อนเลเวล 1 บนจอ {device} เสร็จสิ้น (~{total_deleted} รายการ)"
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
        self.current_device: Optional[str] = None
        self.current_step: str = "พร้อมทำงาน"
        self.device_statuses: Dict[str, Dict[str, Any]] = {}

    def set_step(self, device: Optional[str], step: str):
        with self.lock:
            self.current_device = device
            self.current_step = step
            if device:
                self.device_statuses[device] = {
                    "device": device,
                    "status": "running",
                    "current_step": step,
                    "updated_at": time.strftime("%H:%M:%S")
                }

    def start(self, devices: List[str], interval_minutes: int = 30, run_immediately: bool = True):
        with self.lock:
            self.target_devices = [d.strip() for d in devices if d and d.strip()]
            self.interval_minutes = max(1, interval_minutes)
            self.is_running = True
            self.current_step = "กำลังเริ่มระบบวนลูป..."
            self._stop_event.clear()
        # Clear global stop event เมื่อเริ่มใหม่
        _GLOBAL_STOP_EVENT.clear()

        with self.lock:
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
            self.current_device = None
            self.current_step = "หยุดการทำงานแล้ว"
            for dev in self.device_statuses:
                self.device_statuses[dev]["status"] = "stopped"
                self.device_statuses[dev]["current_step"] = "หยุดการทำงานแล้ว"
        # ส่ง stop signal ไปยัง global event ทำให้ทุก loop หยุดทันที
        _GLOBAL_STOP_EVENT.set()

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            now = time.time()
            remaining_seconds = max(0, int(self.next_run_time - now)) if self.next_run_time else 0
            return {
                "is_running": self.is_running,
                "interval_minutes": self.interval_minutes,
                "target_devices": self.target_devices,
                "current_device": self.current_device,
                "current_step": self.current_step,
                "device_statuses": self.device_statuses,
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
                    next_str = time.strftime('%H:%M:%S', time.localtime(self.next_run_time))
                    self.set_step(None, f"รอเริ่มรอบแรกเวลา {next_str} (อีก {self.interval_minutes} นาที)")
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
                    self.set_step(dev, f"กำลังเปิดเกม Cookie Run บนจอ {dev}...")

                    def _scheduler_log(msg: str):
                        clean_msg = msg
                        # Extract friendly message from bracketed prefixes
                        if "]" in clean_msg:
                            clean_msg = clean_msg.split("]", 1)[-1].strip()
                        self.set_step(dev, clean_msg)
                        print(f"[{time.strftime('%H:%M:%S')}][Cleaner][{dev}] {clean_msg}", flush=True)

                    # ตรวจสอบและเปิดเกมพร้อมรอให้ถึงหน้า Lobby สะอาด
                    launch_game_and_wait_lobby(dev, timeout=45.0, log_func=_scheduler_log)
                    res = clean_level1_friends(dev, log_func=_scheduler_log, restart_app=True)
                    ticked = res.get("total_ticked", 0)
                    with self.lock:
                        self.history.append({
                            "time": time.strftime("%H:%M:%S"),
                            "device": dev,
                            "success": res.get("success", False),
                            "ticked": ticked
                        })
                        if dev in self.device_statuses:
                            self.device_statuses[dev]["status"] = "idle"
                            self.device_statuses[dev]["current_step"] = f"ลบเพื่อนเลเวล 1 สำเร็จ {ticked} รายการ"
                except Exception as e:
                    print(f"[FriendCleaner] Error on {dev}: {e}", flush=True)
                    self.set_step(dev, f"เกิดข้อผิดพลาด: {e}")
                finally:
                    clear_system_memory(dev, package=GAME_PACKAGE)

            # Wait for next interval
            next_str = time.strftime('%H:%M:%S', time.localtime(self.next_run_time)) if self.next_run_time else ""
            self.set_step(None, f"รอบล่าสุดเสร็จสิ้น • รอทำรอบถัดไปเวลา {next_str} (อีก {self.interval_minutes} นาที)")
            if self._stop_event.wait(self.interval_minutes * 60):
                break

        with self.lock:
            self.is_running = False
            self.current_device = None
            self.current_step = "หยุดการทำงานแล้ว"


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
