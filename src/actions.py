import sys
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import random
import time
import threading
import cv2
import numpy as np
from typing import Optional, List, Dict, Any, Tuple

_device_context = threading.local()

def set_device_context(target_ip: str, target_port: int = 5555):
    """Set the active device target for the current thread."""
    _device_context.target_ip = target_ip
    _device_context.target_port = target_port

def get_device_context():
    """Get the active device target for the current thread."""
    ip = getattr(_device_context, "target_ip", None) or config.DEVICE_IP
    port = getattr(_device_context, "target_port", None) or config.DEVICE_PORT
    return ip, port

import config
from adb import safe_device_tap, safe_device_scroll, safe_device_hold, device_capture_screen
from config import (
    ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON,
    ACCEPT_CONGRATULATIONS_BUTTON,
    ACCEPT_SET_REWARD_BUTTON,
    ACCEPT_PREVIOUS_RESULTS_BUTTON,
    ACCEPT_DAILY_CHECKIN_BOOST_SET_BUTTON,
    ACCEPT_DAILY_CHECKIN_BUTTON,
    ACCEPT_DAILY_TREASURE_BUTTON,
    ACCEPT_DAILY_NEW_BUTTON,
    ACCEPT_ENTER_LEAGUE_BUTTON,
    ACCEPT_LEAGUE_RESULTS_BUTTON,
    ACCEPT_LEVEL_UP_BUTTON,
    ACCEPT_MYSTERY_BOX_BUTTON,
    ACCEPT_OVERTAKE_BREAK_SCORE_BUTTON,
    ACCEPT_PREVIOUS_RANK_RESULTS_BUTTON,
    ACCEPT_TOO_MANY_TREASURES_BUTTON,
    ALL_LIVES_RECEIVED_AND_SENT_REGION,
    ALL_LIVES_RECEIVED_AND_SENT_TEMPLATE,
    CLOSE_ANNOUNCEMENT_DIALOG_BUTTON,
    CLOSE_SEND_LIFE_DIALOG_BUTTON,
    COMPLETE_FINISH_BUTTON,
    REPLAY_BUTTON,
    CONFIRM_SEND_LIFE_BUTTON,
    CONFIRM_SEND_LIFE_REGION,
    CONFIRM_SEND_LIFE_TEMPLATE,
    COOKIE_RELAY_ITEM,
    COOKIE_RELAY_USE_BUTTON,
    EXIT_GAME_SETTINGS_BUTTON,
    EXIT_PARTY_RUN_MODE_BUTTON,
    FAST_START_ITEM,
    FAST_START_USE_BUTTON,
    FRIEND_BOTTOM_LEADERBOARD_REGION,
    FRIEND_BOTTOM_LEADERBOARD_TEMPLATE,
    FRIEND_SEND_LIFE_REGION,
    FRIEND_SEND_LIFE_TEMPLATE,
    FRIEND_TOP_LEADERBOARD_REGION,
    FRIEND_TOP_LEADERBOARD_TEMPLATE,
    INACTIVE_RELOAD_BUTTON,
    LEADERBOARD_BOTTOM_POSITION,
    LEADERBOARD_TOP_POSITION,
    MAIL_BOX_BUTTON,
    MAIL_BOX_LIVES_TAB_BUTTON,
    MAIL_BOX_CLOSE_BUTTON,
    MULTI_BUY_BUTTON,
    MULTI_PURCHASE_BUTTON,
    NO_LIVES_TO_RECEIVE_REGION,
    NO_LIVES_TO_RECEIVE_TEMPLATE,
    PICK_BOOST_CLOSE_BUTTON,
    PLAY_BUTTON,
    PURCHASE_BUTTON,
    QUICK_RECEIVE_AND_SEND_LIVES_BUTTON,
    RANDOM_BOOST_ITEM,
    RANDOM_BOOST_REGION,
    BOOST_DIALOG_ITEMS,
    BOOST_DIALOG_COORDS,
    HP_BOOST_ITEM,
    ITEM_EXTENSION_ITEM,
    DOUBLE_XP_ITEM,
    HP_BOOST_CHECKBOX,
    ITEM_EXTENSION_CHECKBOX,
    DOUBLE_XP_CHECKBOX,
    RELIC_CLAIM_BUTTON,
    RELIC_CLOSE_BUTTON,
    RELIC_COMPLETE_BUTTON,
    START_BUTTON,
    CONNECTION_LOST_RELOAD_BUTTON,
)
from detection import detect_templates, detect_anti_bot_odd_cards, detect_stage
from config import (
    ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
    ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
    ANTI_BOT_CARD_WIDTH, ANTI_BOT_CARD_HEIGHT,
)

def start_game():
    print("🏁 Starting the game...")
    safe_device_tap(*get_device_context(), START_BUTTON[0], START_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def play_game():
    print("🎮 Playing the game...")
    safe_device_tap(*get_device_context(), PLAY_BUTTON[0], PLAY_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def is_top_item_checked(screen, checkbox_coord):
    """
    Check if a top-row boost item is currently checked/active.
    When checked, the 11x11 box around the checkbox coordinate has bright green pixels (B < 40, G > 100, R < 40).
    """
    if screen is None:
        return False
    x, y = checkbox_coord
    h, w = screen.shape[:2]
    if y < 5 or y + 6 > h or x < 5 or x + 6 > w:
        return False
    patch = screen[y - 5 : y + 6, x - 5 : x + 6]
    green_pixels = ((patch[:, :, 1] > 100) & (patch[:, :, 0] < 40) & (patch[:, :, 2] < 40)).sum()
    return bool(green_pixels >= 40)


def configure_top_row_items(screen, use_hp=False, use_extension=False, use_double_xp=False, log_fn=None):
    """
    Configures top-row boost items (HP extension, item extension, double XP).
    Always unchecks any unneeded/disabled items FIRST, then checks the desired items.
    """
    items = [
        ("HP Extension (ขวดเลือด +30 HP)", HP_BOOST_ITEM, HP_BOOST_CHECKBOX, use_hp),
        ("Item Extension (นาฬิกายืดเวลา)", ITEM_EXTENSION_ITEM, ITEM_EXTENSION_CHECKBOX, use_extension),
        ("Double XP (EXP x2)", DOUBLE_XP_ITEM, DOUBLE_XP_CHECKBOX, use_double_xp),
    ]

    def emit_log(msg):
        if log_fn:
            log_fn(msg, "info")
        else:
            print(msg)

    # ขั้นตอนที่ 1: ติ๊กอันเดิมที่ไม่ต้องการออกก่อนทั้งหมด
    uncheck_performed = False
    for name, item_coord, checkbox_coord, desired in items:
        if not desired and is_top_item_checked(screen, checkbox_coord):
            emit_log(f"🛒 [Top Item] ติ๊กอันเดิมออกก่อน: ปิดใช้งาน {name}")
            safe_device_tap(*get_device_context(), item_coord[0], item_coord[1])
            time.sleep(random.uniform(0.3, 0.45))
            uncheck_performed = True

    # ตรวจจับหน้าจอล่าสุดหลังปลดออก
    if uncheck_performed:
        fresh_screen = device_capture_screen(*get_device_context())
        if fresh_screen is not None:
            screen = fresh_screen

    # ขั้นตอนที่ 2: ค่อยไปติ๊กเปิดส่วนที่เลือกไว้
    check_performed = False
    for name, item_coord, checkbox_coord, desired in items:
        if desired and not is_top_item_checked(screen, checkbox_coord):
            emit_log(f"🛒 [Top Item] ติ๊กเปิดส่วนที่เลือกไว้: {name}")
            safe_device_tap(*get_device_context(), item_coord[0], item_coord[1])
            time.sleep(random.uniform(0.3, 0.45))
            check_performed = True

    # ขั้นตอนที่ 3: ตรวจสอบความถูกต้องอีกครั้ง (Safety Confirmation)
    if uncheck_performed or check_performed:
        verify_screen = device_capture_screen(*get_device_context())
        if verify_screen is not None:
            for name, item_coord, checkbox_coord, desired in items:
                checked = is_top_item_checked(verify_screen, checkbox_coord)
                if desired and not checked:
                    emit_log(f"⚠️ [Top Item] แตะซ้ำเพื่อยืนยันการเปิด: {name}...")
                    safe_device_tap(*get_device_context(), item_coord[0], item_coord[1])
                    time.sleep(random.uniform(0.3, 0.4))
                elif not desired and checked:
                    emit_log(f"⚠️ [Top Item] แตะซ้ำเพื่อยืนยันการปิด: {name}...")
                    safe_device_tap(*get_device_context(), item_coord[0], item_coord[1])
                    time.sleep(random.uniform(0.3, 0.4))


def purchase_fast_start():
    print("🛒 Purchasing Fast Start...")
    safe_device_tap(*get_device_context(), FAST_START_ITEM[0], FAST_START_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(*get_device_context(), PURCHASE_BUTTON[0], PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))


def purchase_cookie_relay():
    print("🛒 Purchasing Cookie Relay...")
    safe_device_tap(*get_device_context(), COOKIE_RELAY_ITEM[0], COOKIE_RELAY_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(*get_device_context(), PURCHASE_BUTTON[0], PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))


def purchase_random_boost():
    print("🛒 Purchasing Random Boost...")
    safe_device_tap(*get_device_context(), RANDOM_BOOST_ITEM[0], RANDOM_BOOST_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(*get_device_context(), PURCHASE_BUTTON[0], PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))


def is_boost_dialog_option_checked(screen, check_coord):
    """Checks if a boost option in 'Pick desired Boosts!' dialog has a green checkmark."""
    if screen is None:
        return False
    cx, cy = check_coord
    h, w = screen.shape[:2]
    if cy < 13 or cy + 13 > h or cx < 13 or cx + 13 > w:
        return False
    patch = screen[cy - 12 : cy + 13, cx - 12 : cx + 13]
    return bool(((patch[:, :, 1] > 130) & (patch[:, :, 0] < 100)).sum() >= 15)


def sync_boost_dialog_selection(target_id: str, log_fn=None):
    """
    Ensures that in the 'Pick desired Boosts!' dialog, ONLY target_id is checked.
    Unchecks any previously checked boosts FIRST, then checks the desired boost.
    """
    def emit_log(msg):
        if log_fn:
            log_fn(msg, "info")
        else:
            print(msg)

    if target_id not in BOOST_DIALOG_ITEMS:
        emit_log(f"⚠️ Unknown target boost ID '{target_id}', falling back to double_coins")
        target_id = "double_coins"

    screen = device_capture_screen(*get_device_context())
    if screen is None:
        return

    # ขั้นตอนที่ 1: ติ๊กอันเดิมออกก่อนทั้งหมด (สำหรับทุกบัฟที่ไม่ใช่เป้าหมาย)
    uncheck_performed = False
    for bid, data in BOOST_DIALOG_ITEMS.items():
        if bid != target_id:
            if is_boost_dialog_option_checked(screen, data["check"]):
                emit_log(f"🔄 [Random Boost Dialog] ติ๊กอันเดิมออกก่อน: {data['name']}...")
                safe_device_tap(*get_device_context(), data["tap"][0], data["tap"][1])
                time.sleep(random.uniform(0.3, 0.45))
                uncheck_performed = True

    # ตรวจจับหน้าจอล่าสุดหลังปลดอันเดิมออก
    if uncheck_performed:
        fresh_screen = device_capture_screen(*get_device_context())
        if fresh_screen is not None:
            screen = fresh_screen

    # ขั้นตอนที่ 2: ค่อยไปติ๊กส่วนที่เลือกไว้ (target_id)
    target_data = BOOST_DIALOG_ITEMS[target_id]
    if not is_boost_dialog_option_checked(screen, target_data["check"]):
        emit_log(f"🎯 [Random Boost Dialog] ติ๊กเลือกส่วนที่เลือกไว้: {target_data['name']}...")
        safe_device_tap(*get_device_context(), target_data["tap"][0], target_data["tap"][1])
        time.sleep(random.uniform(0.35, 0.5))

    # ขั้นตอนที่ 3: ตรวจสอบความถูกต้องอีกครั้ง (Safety Confirmation)
    verify_screen = device_capture_screen(*get_device_context())
    if verify_screen is not None:
        # หากเป้าหมายยังไม่ติด ให้แตะซ้ำอีกครั้ง
        if not is_boost_dialog_option_checked(verify_screen, target_data["check"]):
            emit_log(f"⚠️ [Random Boost Dialog] แตะซ้ำเพื่อยืนยันการติ๊กถูก: {target_data['name']}...")
            safe_device_tap(*get_device_context(), target_data["tap"][0], target_data["tap"][1])
            time.sleep(random.uniform(0.3, 0.4))
        # หากยังมีตัวอื่นหลงเหลือติดอยู่ ให้ปลดออกซ้ำ
        for bid, data in BOOST_DIALOG_ITEMS.items():
            if bid != target_id:
                if is_boost_dialog_option_checked(verify_screen, data["check"]):
                    emit_log(f"⚠️ [Random Boost Dialog] ปลดอันเดิมที่ค้างอยู่ออกซ้ำ: {data['name']}...")
                    safe_device_tap(*get_device_context(), data["tap"][0], data["tap"][1])
                    time.sleep(random.uniform(0.3, 0.4))


def purchase_desired_random_boost(desired_template, desired_name, boost_id=None, log_fn=None):
    def emit_log(msg):
        if log_fn:
            log_fn(msg, "info")
        else:
            print(msg)

    emit_log(f"🛒 Checking Desired Random Boost: {desired_name} (ID: {boost_id})...")
    # 1. If already equipped on PURCHASE_ITEM screen, don't buy again
    screen = device_capture_screen(*get_device_context())
    if detect_templates(screen, desired_template, RANDOM_BOOST_REGION):
        emit_log(f"✨ Desired Boost '{desired_name}' is already equipped! Skipping purchase.")
        return

    # 2. Open item detail modal
    safe_device_tap(*get_device_context(), RANDOM_BOOST_ITEM[0], RANDOM_BOOST_ITEM[1])
    time.sleep(random.uniform(0.8, 1.2))

    # 3. Open "Pick desired Boosts!" dialog
    safe_device_tap(*get_device_context(), MULTI_PURCHASE_BUTTON[0], MULTI_PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1.0, 1.5))

    # 4. Resolve target boost ID
    target_id = boost_id
    if not target_id:
        name_lower = str(desired_name).lower()
        for bid in BOOST_DIALOG_ITEMS:
            if bid in name_lower or bid.replace("_", "") in name_lower.replace(" ", ""):
                target_id = bid
                break
        if not target_id:
            target_id = "double_coins"

    # 5. Synchronize boost selection: ติ๊กอันเดิมออกก่อน ➜ ค่อยติ๊กส่วนที่เลือกไว้!
    sync_boost_dialog_selection(target_id, log_fn=log_fn)

    # 6. Tap Multi-Buy button
    emit_log(f"🛒 Tapping Multi-Buy for target boost: {desired_name}...")
    safe_device_tap(*get_device_context(), MULTI_BUY_BUTTON[0], MULTI_BUY_BUTTON[1])
    time.sleep(random.uniform(1.5, 2.2))

    # 7. Wait for rolling to complete and desired boost to appear in RANDOM_BOOST_REGION
    emit_log(f"🔍 Waiting for desired boost to be detected: {desired_name}...")
    timeout = 30
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            emit_log(f"⏰ Timeout: Could not detect desired boost '{desired_name}' within {timeout} seconds.")
            emit_log("⚠️ Skipping Desired Random Boost. Closing any open dialogs...")
            # Tap close [X] so the popup does not block subsequent gameplay
            safe_device_tap(*get_device_context(), PICK_BOOST_CLOSE_BUTTON[0], PICK_BOOST_CLOSE_BUTTON[1])
            time.sleep(random.uniform(0.8, 1.2))
            return
        screen = device_capture_screen(*get_device_context())
        if detect_templates(screen, desired_template, RANDOM_BOOST_REGION):
            emit_log(f"✅ Desired Boost detected: {desired_name}!")
            break
        time.sleep(0.5)


def using_fast_start():
    print("⚡ Using Fast Start...")
    safe_device_tap(*get_device_context(), FAST_START_USE_BUTTON[0], FAST_START_USE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))


def using_cookie_relay():
    print("🍪 Using Cookie Relay...")
    safe_device_tap(*get_device_context(), COOKIE_RELAY_USE_BUTTON[0], COOKIE_RELAY_USE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))


def complete_finish(screen=None):
    print("🏆 Completing the game (Tapping Confirm/OK)...")
    target_x, target_y = COMPLETE_FINISH_BUTTON
    if screen is None:
        screen = device_capture_screen(*get_device_context())

    if screen is not None:
        # Check green button in bottom area y: 580..700
        # Automatically handles both 2-button screen (OK at ~460) and 1-button screen (Confirm at ~640)
        roi = screen[580:700, 300:900]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([35, 100, 100]), np.array([85, 255, 255]))
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            if cv2.contourArea(c) > 3000:
                bx, by, bw, bh = cv2.boundingRect(c)
                target_x, target_y = (300 + bx + bw // 2, 580 + by + bh // 2)
                break

    safe_device_tap(*get_device_context(), target_x, target_y)
    time.sleep(random.uniform(1.2, 1.8))


def replay_game():
    print("🔄 Replaying the game (Tapping Replay)...")
    safe_device_tap(*get_device_context(), REPLAY_BUTTON[0], REPLAY_BUTTON[1])
    time.sleep(random.uniform(1.0, 1.5))


def accept_mystery_box():
    print("🎁 Opening Mystery Boxes...")
    # 1. Tap Open All button
    safe_device_tap(*get_device_context(), ACCEPT_MYSTERY_BOX_BUTTON[0], ACCEPT_MYSTERY_BOX_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))
    # 2. Tap to confirm loot and return
    safe_device_tap(*get_device_context(), ACCEPT_MYSTERY_BOX_BUTTON[0], ACCEPT_MYSTERY_BOX_BUTTON[1])
    time.sleep(random.uniform(0.5, 0.8))


def accept_congratulations():
    print("🎉 Accepting Congratulations (Tapping Confirm)...")
    safe_device_tap(*get_device_context(), ACCEPT_CONGRATULATIONS_BUTTON[0], ACCEPT_CONGRATULATIONS_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_set_reward():
    print("🎁 Accepting Set Reward (Tapping Confirm)...")
    safe_device_tap(*get_device_context(), ACCEPT_SET_REWARD_BUTTON[0], ACCEPT_SET_REWARD_BUTTON[1])
    time.sleep(random.uniform(0.4, 0.6))


def accept_previous_results():
    print("📋 Accepting Previous Results (Tapping Confirm)...")
    safe_device_tap(*get_device_context(), ACCEPT_PREVIOUS_RESULTS_BUTTON[0], ACCEPT_PREVIOUS_RESULTS_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))


def accept_level_up():
    print("⬆️ Accepting Level Up (Tapping Confirm)...")
    safe_device_tap(*get_device_context(), ACCEPT_LEVEL_UP_BUTTON[0], ACCEPT_LEVEL_UP_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_daily_checkin():
    print("📅 Accepting Daily Check-in...")
    safe_device_tap(*get_device_context(), ACCEPT_DAILY_CHECKIN_BUTTON[0], ACCEPT_DAILY_CHECKIN_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_daily_checkin_boost_set():
    print("📅 Accepting Daily Check-in Boost Set...")
    safe_device_tap(*get_device_context(), ACCEPT_DAILY_CHECKIN_BOOST_SET_BUTTON[0], ACCEPT_DAILY_CHECKIN_BOOST_SET_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_daily_treasure():
    print("💎 Accepting Daily Treasure...")
    safe_device_tap(*get_device_context(), ACCEPT_DAILY_TREASURE_BUTTON[0], ACCEPT_DAILY_TREASURE_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_daily_new():
    print("📰 Accepting Daily New...")
    safe_device_tap(*get_device_context(), ACCEPT_DAILY_NEW_BUTTON[0], ACCEPT_DAILY_NEW_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_enter_league():
    print("🏆 Accepting Enter League...")
    safe_device_tap(*get_device_context(), ACCEPT_ENTER_LEAGUE_BUTTON[0], ACCEPT_ENTER_LEAGUE_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_league_results():
    print("🏆 Accepting League Results...")
    safe_device_tap(*get_device_context(), ACCEPT_LEAGUE_RESULTS_BUTTON[0], ACCEPT_LEAGUE_RESULTS_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_previous_rank_results():
    print("🏆 Accepting Previous Rank Results...")
    safe_device_tap(*get_device_context(), ACCEPT_PREVIOUS_RANK_RESULTS_BUTTON[0], ACCEPT_PREVIOUS_RANK_RESULTS_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_too_many_treasures():
    print("💎 Accepting Too Many Treasures...")
    safe_device_tap(*get_device_context(), ACCEPT_TOO_MANY_TREASURES_BUTTON[0], ACCEPT_TOO_MANY_TREASURES_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def accept_overtake_break_score():
    print("🏆 Accepting Overtake Break Score...")
    safe_device_tap(*get_device_context(), ACCEPT_OVERTAKE_BREAK_SCORE_BUTTON[0], ACCEPT_OVERTAKE_BREAK_SCORE_BUTTON[1])
    time.sleep(random.uniform(0.3, 0.5))


def open_relic_complete():
    print("🏺 Opening Relic Complete...")
    safe_device_tap(*get_device_context(), RELIC_COMPLETE_BUTTON[0], RELIC_COMPLETE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_relic_claim():
    print("🏺 Accepting Relic Claim...")
    safe_device_tap(*get_device_context(), RELIC_CLAIM_BUTTON[0], RELIC_CLAIM_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(*get_device_context(), RELIC_CLOSE_BUTTON[0], RELIC_CLOSE_BUTTON[1])
    time.sleep(random.uniform(10, 15))


def handle_anti_bot(screen):
    print("🤖 Solving Anti-Bot captcha...")
    card_coords = [
        ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
        ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
    ]

    odd_indices = detect_anti_bot_odd_cards(screen)
    card_nums = [i + 1 for i in odd_indices]
    print(f"🃏 Found odd cards: Card {card_nums[0]} and Card {card_nums[1]}")

    for idx in odd_indices:
        cx, cy = card_coords[idx]
        center_x = cx + ANTI_BOT_CARD_WIDTH // 2
        center_y = cy + ANTI_BOT_CARD_HEIGHT // 2
        tx = random.randint(center_x - 30, center_x + 30)
        ty = random.randint(center_y - 40, center_y + 40)
        print(f"  👆 Tapping Card {idx + 1} at ({tx}, {ty})")
        safe_device_tap(*get_device_context(), tx, ty)
        time.sleep(random.uniform(0.6, 1.0))

    print("✅ Anti-Bot captcha solved!")
    time.sleep(random.uniform(0.8, 1.4))


def handle_connection_lost():
    print("🔌 Handling Connection Lost (Tapping Reload)...")
    safe_device_tap(*get_device_context(), CONNECTION_LOST_RELOAD_BUTTON[0], CONNECTION_LOST_RELOAD_BUTTON[1])
    time.sleep(random.uniform(3.0, 5.0))


def handle_inactive():
    print("💤 Handling Inactive state...")
    safe_device_tap(*get_device_context(), INACTIVE_RELOAD_BUTTON[0], INACTIVE_RELOAD_BUTTON[1])
    time.sleep(random.uniform(10, 15))


def handle_send_friend_life():
    print("💌 Handling Send Friend Life on Leaderboard...")
    screen = device_capture_screen(*get_device_context())
    for _ in range(6):
        if detect_templates(screen, FRIEND_TOP_LEADERBOARD_TEMPLATE, FRIEND_TOP_LEADERBOARD_REGION):
            print("✅ Top of Friend Leaderboard reached.")
            break
        print("🔄 Scrolling up to find Send Friend Life...")
        safe_device_scroll(*get_device_context(), LEADERBOARD_BOTTOM_POSITION[0], LEADERBOARD_BOTTOM_POSITION[1], direction="down", distance=300, duration=150)
        time.sleep(random.uniform(0.6, 1.0))
        screen = device_capture_screen(*get_device_context())

    no_button_scroll_count = 0
    total_scrolls = 0
    while total_scrolls < 15:
        screen = device_capture_screen(*get_device_context())
        if detect_templates(screen, FRIEND_BOTTOM_LEADERBOARD_TEMPLATE, FRIEND_BOTTOM_LEADERBOARD_REGION):
            print("✅ Bottom of Friend Leaderboard reached. Done sending lives.")
            break
        send_life_button_coords = detect_templates(screen, FRIEND_SEND_LIFE_TEMPLATE, FRIEND_SEND_LIFE_REGION)
        if send_life_button_coords:
            no_button_scroll_count = 0
            for x, y, w, h in send_life_button_coords:
                print("💌 Sending life to friend...")
                safe_device_tap(*get_device_context(), x + w // 2, y + h // 2)
                time.sleep(random.uniform(0.6, 1.0))
                print("💌 Confirming send life...")
                safe_device_tap(*get_device_context(), CONFIRM_SEND_LIFE_BUTTON[0], CONFIRM_SEND_LIFE_BUTTON[1])
                time.sleep(random.uniform(0.6, 1.0))
                print("💌 Closing send life dialog...")
                safe_device_tap(*get_device_context(), CLOSE_SEND_LIFE_DIALOG_BUTTON[0], CLOSE_SEND_LIFE_DIALOG_BUTTON[1])
                time.sleep(random.uniform(0.5, 0.8))
        else:
            no_button_scroll_count += 1
            if no_button_scroll_count >= 5:
                print(f"ℹ️ No send life buttons found for 5 consecutive scrolls. Ending send lives.")
                break
            print(f"🔄 No send life buttons found, scrolling down... ({no_button_scroll_count}/5)")

        safe_device_scroll(*get_device_context(), LEADERBOARD_TOP_POSITION[0], LEADERBOARD_TOP_POSITION[1], direction="up", distance=120, duration=150)
        time.sleep(random.uniform(0.6, 1.0))
        total_scrolls += 1


def handle_quick_receive_and_send_lives():
    print("✉️ Handling Quick Receive and Send Lives...")
    time.sleep(random.uniform(0.8, 1.2))
    safe_device_tap(*get_device_context(), MAIL_BOX_BUTTON[0], MAIL_BOX_BUTTON[1])
    time.sleep(random.uniform(1.0, 1.5))
    safe_device_tap(*get_device_context(), MAIL_BOX_LIVES_TAB_BUTTON[0], MAIL_BOX_LIVES_TAB_BUTTON[1])
    time.sleep(random.uniform(1.0, 1.5))
    screen = device_capture_screen(*get_device_context())
    if detect_templates(screen, NO_LIVES_TO_RECEIVE_TEMPLATE, NO_LIVES_TO_RECEIVE_REGION):
        print("✉️ No lives to receive in mailbox. Closing mailbox...")
        safe_device_tap(*get_device_context(), MAIL_BOX_CLOSE_BUTTON[0], MAIL_BOX_CLOSE_BUTTON[1])
        time.sleep(random.uniform(0.8, 1.2))
        return

    print("✉️ Receiving all lives...")
    safe_device_tap(*get_device_context(), QUICK_RECEIVE_AND_SEND_LIVES_BUTTON[0], QUICK_RECEIVE_AND_SEND_LIVES_BUTTON[1])
    time.sleep(random.uniform(1.0, 1.5))
    for _ in range(10):
        screen = device_capture_screen(*get_device_context())
        all_lives_received_and_sent = detect_templates(screen, ALL_LIVES_RECEIVED_AND_SENT_TEMPLATE, ALL_LIVES_RECEIVED_AND_SENT_REGION)
        if all_lives_received_and_sent:
            print("✉️ All lives received and sent. Done!")
            safe_device_tap(*get_device_context(), ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON[0], ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON[1])
            time.sleep(random.uniform(0.8, 1.2))
            break
        confirm_send_life_button_coords = detect_templates(screen, CONFIRM_SEND_LIFE_TEMPLATE, CONFIRM_SEND_LIFE_REGION)
        if confirm_send_life_button_coords:
            print("✉️ Sending lives to friends...")
            safe_device_tap(*get_device_context(), CONFIRM_SEND_LIFE_BUTTON[0], CONFIRM_SEND_LIFE_BUTTON[1])
            time.sleep(random.uniform(0.8, 1.2))
            continue
        time.sleep(0.5)

    safe_device_tap(*get_device_context(), MAIL_BOX_CLOSE_BUTTON[0], MAIL_BOX_CLOSE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))
    print("✉️ Quick Receive and Send Lives completed.")


def close_announcement_dialog():
    print("🖱️ Closing announcement dialog...")
    screen = device_capture_screen(*get_device_context())
    if screen is not None and detect_stage(screen, ["MAINMENU", "PURCHASE_ITEM"]):
        print("✅ Already in menu, no dialog to close.")
        return

    for i in range(3):
        print(f"🖱️ Tapping close announcement dialog button {i+1}/3")
        safe_device_tap(*get_device_context(), CLOSE_ANNOUNCEMENT_DIALOG_BUTTON[0], CLOSE_ANNOUNCEMENT_DIALOG_BUTTON[1])
        time.sleep(random.uniform(0.3, 0.5))
        device_screen = device_capture_screen(*get_device_context())
        if detect_stage(device_screen, ["PARTY_RUN"]) == "PARTY_RUN":
            close_party_run_mode()
            break
        elif detect_stage(device_screen, ["GAME_SETTINGS"]) == "GAME_SETTINGS":
            close_game_settings()
            break
        elif detect_stage(device_screen, ["MAINMENU", "PURCHASE_ITEM"]):
            print("✅ Announcement closed, back to menu.")
            break


def close_party_run_mode():
    print(" Closing Party Run mode...")
    for _ in range(2):
        safe_device_tap(*get_device_context(), EXIT_PARTY_RUN_MODE_BUTTON[0], EXIT_PARTY_RUN_MODE_BUTTON[1])
        time.sleep(random.uniform(0.6, 1.0))
        screen = device_capture_screen(*get_device_context())
        if screen is None or detect_stage(screen, ["PARTY_RUN"]) != "PARTY_RUN":
            break


def close_game_settings():
    print(" Closing Game Settings...")
    for _ in range(2):
        safe_device_tap(*get_device_context(), EXIT_GAME_SETTINGS_BUTTON[0], EXIT_GAME_SETTINGS_BUTTON[1])
        time.sleep(random.uniform(0.6, 1.0))
        screen = device_capture_screen(*get_device_context())
        if screen is None or detect_stage(screen, ["GAME_SETTINGS"]) != "GAME_SETTINGS":
            break


def handle_clean_level1_friends(target_device: Optional[str] = None):
    """
    Automated Level 1 friend removal:
    Friends -> Manage -> ensure Level ▲ -> tick all Level 1 -> scroll until none left -> Clear selection -> Confirm -> X
    """
    dev = target_device or get_device_context()[0]
    try:
        from friend_cleaner import clean_level1_friends
        return clean_level1_friends(dev)
    except Exception as e:
        print(f"❌ Error in handle_clean_level1_friends: {e}", flush=True)
        return {"success": False, "message": str(e)}
 
 
def perform_auto_jump():
    """Execute single jump during in-game run."""
    safe_device_tap(*get_device_context(), config.JUMP_BUTTON[0], config.JUMP_BUTTON[1])


def perform_auto_slide(duration_ms: int = 250):
    """Execute slide/crouch during in-game run."""
    safe_device_hold(*get_device_context(), config.SLIDE_BUTTON[0], config.SLIDE_BUTTON[1], duration=duration_ms)


def exit_in_game_run(target_ip: Optional[str] = None, target_port: Optional[int] = None, log_fn=None):
    """
    Taps Pause -> Quit -> Confirm Quit to early exit the active run when target box count is reached.
    """
    ctx_ip, ctx_port = get_device_context()
    ip = target_ip or ctx_ip
    port = target_port or ctx_port

    def _log(m):
        if log_fn:
            log_fn(m, "info")
        else:
            print(m)

    _log("⏸️ [Early Exit] กำลังแตะปุ่ม Pause...")
    safe_device_tap(ip, port, config.PAUSE_BUTTON[0], config.PAUSE_BUTTON[1])
    time.sleep(random.uniform(0.6, 0.8))

    _log("🚪 [Early Exit] กำลังแตะปุ่ม Quit (ออกจากห้อง)...")
    safe_device_tap(ip, port, config.PAUSE_MENU_QUIT_BUTTON[0], config.PAUSE_MENU_QUIT_BUTTON[1])
    time.sleep(random.uniform(0.6, 0.8))

    _log("🚪 [Early Exit] กำลังแตะปุ่มยืนยันออกจากการวิ่ง...")
    safe_device_tap(ip, port, config.CONFIRM_QUIT_BUTTON[0], config.CONFIRM_QUIT_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))


