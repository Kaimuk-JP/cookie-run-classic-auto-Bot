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

from adb import device_capture_screen, device_connect, device_reset_app, device_tap, clear_system_memory
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
    accept_relic_claim,
    accept_too_many_treasures,
    close_announcement_dialog,
    complete_finish,
    configure_top_row_items,
    handle_anti_bot,
    handle_inactive,
    handle_quick_receive_and_send_lives,
    handle_send_friend_life,
    open_relic_complete,
    play_game,
    purchase_cookie_relay,
    purchase_desired_random_boost,
    purchase_fast_start,
    start_game,
    using_cookie_relay,
    using_fast_start,
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
    DEVICE_IP,
    DEVICE_PORT,
    SESSION_RESET_INTERVAL,
)
import os
import cv2
from datetime import datetime

from detection import (
    detect_stage,
    load_templates,
    extract_result_coins,
    extract_result_score,
    extract_result_xp,
    detect_result_screen_mystery_box,
)
from debug import save_debug_screen

# -------------------
# BOT OPTIONS
# -------------------
BOOST_CHOICES = [
    ("Double Coins",            BOOST_DOUBLE_COINS_TEMPLATE),
    ("+15% Score Bonus",        BOOST_15P_SCORE_BONUS_TEMPLATE),
    ("-15% HP Drain",           BOOST_M15P_HP_DRAIN_TEMPLATE),
    ("Revive Once with 80 HP",  BOOST_REVIVE_ONCE_WITH_80HP_TEMPLATE),
    ("70% Crush Chance",        BOOST_70P_CRUSH_CHANCE_TEMPLATE),
    ("+17% Base Speed",         BOOST_17P_BASE_SPEED_TEMPLATE),
    ("Gold Coin Magic",         BOOST_GOLD_COIN_MAGIC_TEMPLATE),
    ("-30% Collision Damage",   BOOST_M30P_COLLISION_DAMAGE_TEMPLATE),
    ("+20% HP from Potions",    BOOST_20P_HP_FROM_POTIONS_TEMPLATE),
    ("Magnetic Aura",           BOOST_MAGNETIC_AURA_TEMPLATE),
    ("2 Pit Lifts",             BOOST_2PIT_LIFTS_TEMPLATE),
]


def get_detection_stage_names(group_name, exclude=None):
    stage_names = []
    # For non-in-game groups, always stages have higher priority
    if group_name != "IN_GAME":
        for stage_name in DETECTION_ALWAYS_STAGES:
            if stage_name not in stage_names:
                stage_names.append(stage_name)
    # Add stages from the specified detection group
    for stage_name in DETECTION_GROUPS[group_name]:
        if stage_name not in stage_names:
            stage_names.append(stage_name)
    # For in-game, always stages are appended last (original behavior)
    if group_name == "IN_GAME":
        for stage_name in DETECTION_ALWAYS_STAGES:
            if stage_name not in stage_names:
                stage_names.append(stage_name)
    if exclude:
        stage_names = [s for s in stage_names if s not in exclude]
    return stage_names


def prompt_user_options():
    desired_boost_template = None

    print("⚙️ --- Bot Options ---")
    use_hp_boost = input("🧪 Use HP Extension (+30 HP)? [y/n]: ").strip().lower() == "y"
    use_item_extension = input("⏳ Use Item Extension (Pocket Watch)? [y/n]: ").strip().lower() == "y"
    use_double_xp = input("⭐ Use Double XP (2x Star)? [y/n]: ").strip().lower() == "y"
    use_fast_start = input("⚡ Use Fast Start (buy + use)? [y/n]: ").strip().lower() == "y"
    use_cookie_relay = input("🍪 Use Cookie Relay (buy + use)? [y/n]: ").strip().lower() == "y"
    use_desired_random_boost = input("🎲 Use Desired Random Boost (buy + use)? [y/n]: ").strip().lower() == "y"
    if use_desired_random_boost:
        print("  Select desired boost (must match the boost option configured in-game):")
        for i, (name, _) in enumerate(BOOST_CHOICES, 1):
            print(f"  {i:2}. {name}")
        while True:
            choice = input("  Enter number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(BOOST_CHOICES):
                desired_boost_template = BOOST_CHOICES[int(choice) - 1][1]
                desired_boost_name = BOOST_CHOICES[int(choice) - 1][0]
                print(f"  ✅ Selected: {desired_boost_name}")
                break
            print(f"  ⚠️ Please enter a number between 1 and {len(BOOST_CHOICES)}.")
    detect_relic = input("🏺 Detect Relic (open + claim)? [y/n]: ").strip().lower() == "y"
    print("---------------------")

    return {
        "use_hp_boost": use_hp_boost,
        "use_item_extension": use_item_extension,
        "use_double_xp": use_double_xp,
        "use_fast_start": use_fast_start,
        "use_cookie_relay": use_cookie_relay,
        "use_desired_random_boost": use_desired_random_boost,
        "desired_boost_template": desired_boost_template,
        "desired_boost_name": desired_boost_name if use_desired_random_boost else None,
        "detect_relic": detect_relic,
    }


# -------------------
# MAIN LOOP
# -------------------
def main():
    try:
        print("🚀 CookieRun Classic Bot Started")
        print("⚠️ Screen must be 1280x720 resolution for the bot to work properly.")
        print(f"Connecting to device at {DEVICE_IP}:{DEVICE_PORT}...")

        device_connect(DEVICE_IP, DEVICE_PORT)
        load_templates()

        # * for debugging *
        # device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        # save_debug_screen(device_screen)

        options = prompt_user_options()
        relic_exclude = None if options["detect_relic"] else {"RELIC_COMPLETE", "RELIC_CLAIM"}

        last_stage = None
        is_first_game = True
        detection_group = "PRE_GAME"
        last_detected_time = time.time()
        session_start_time = time.time()
        session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
        last_lives_time = time.time()
        lives_interval = random.uniform(25 * 60, 35 * 60)
        pending_send_friend_life = True

        while True:
            device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
            stage = detect_stage(device_screen, get_detection_stage_names(detection_group, exclude=relic_exclude))
            if stage is None:
                if time.time() - last_detected_time >= DETECTION_RECOVERY_SCAN_INTERVAL[detection_group]:
                    stage = detect_stage(device_screen, exclude=relic_exclude)
                    last_detected_time = time.time()
            else:
                last_detected_time = time.time()

            if stage == last_stage:
                time.sleep(0.1)
                continue

            last_stage = stage

            if stage == "MAINMENU":
                print("🎮 Detected Stage: MAINMENU")
                # Wait screen refresh
                print("⏳ Waiting 5 seconds for screen refresh...")
                time.sleep(5)
                lives_elapsed = time.time() - last_lives_time
                if pending_send_friend_life or lives_elapsed >= lives_interval:
                    print("💌 Checking and sending friend lives...")
                    try:
                        handle_quick_receive_and_send_lives()
                    except Exception as e:
                        print(f"⚠️ Quick receive and send error: {e}")
                    try:
                        handle_send_friend_life()
                    except Exception as e:
                        print(f"⚠️ Send friend life error: {e}")
                    pending_send_friend_life = False
                    last_lives_time = time.time()
                    lives_interval = random.uniform(25 * 60, 35 * 60)
                    last_stage = None
                    continue
                if detection_group == "POST_GAME":
                    detection_group = "PRE_GAME"
                    last_stage = None
                    continue
                is_first_game = False
                start_game()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "PURCHASE_ITEM":
                print("🛒 Detected Stage: PURCHASE_ITEM")
                configure_top_row_items(
                    device_screen,
                    use_hp=options.get("use_hp_boost", False),
                    use_extension=options.get("use_item_extension", False),
                    use_double_xp=options.get("use_double_xp", False),
                )
                if options["use_fast_start"]:
                    purchase_fast_start()
                if options["use_cookie_relay"]:
                    purchase_cookie_relay()
                if options["use_desired_random_boost"]:
                    purchase_desired_random_boost(options["desired_boost_template"], options["desired_boost_name"])
                play_game()
                detection_group = "IN_GAME"
                time.sleep(0.2)
                last_stage = None
            elif stage == "GAME_START":
                print("🏁 Detected Stage: GAME_START")
                if options["use_fast_start"]:
                    using_fast_start()
                detection_group = "IN_GAME"
            elif stage == "GAME_RELAY":
                print("🔄 Detected Stage: GAME_RELAY")
                if options["use_cookie_relay"]:
                    using_cookie_relay()
                detection_group = "IN_GAME"
            elif stage == "GAME_COMPLETE":
                print("✅ Detected Stage: GAME_COMPLETE")
                # 1. รอแอนิเมชันนับคะแนนและเหรียญขึ้นครบ
                time.sleep(random.uniform(0.8, 1.2))
                device_tap(DEVICE_IP, DEVICE_PORT, 640, 260)
                time.sleep(random.uniform(0.8, 1.2))
                device_tap(DEVICE_IP, DEVICE_PORT, 640, 260)
                time.sleep(0.6)

                # 2. จับภาพหน้าจอสรุปผลที่สมบูรณ์
                device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)

                # 3. สกัดคะแนน, เหรียญ, EXP และกล่องปริศนา
                round_score = extract_result_score(device_screen) if device_screen is not None else 0
                round_coins = extract_result_coins(device_screen) if device_screen is not None else 0
                round_xp = extract_result_xp(device_screen) if device_screen is not None else 0
                round_boxes = detect_result_screen_mystery_box(device_screen) if device_screen is not None else []

                if round_coins == 0 and device_screen is not None:
                    device_tap(DEVICE_IP, DEVICE_PORT, 640, 260)
                    time.sleep(0.8)
                    fresh_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
                    if fresh_screen is not None:
                        device_screen = fresh_screen
                        round_score = extract_result_score(device_screen)
                        round_coins = extract_result_coins(device_screen)
                        round_xp = extract_result_xp(device_screen)
                        round_boxes = detect_result_screen_mystery_box(device_screen)

                # 4. [ขั้นตอนบันทึก - Save Screenshot] บันทึกรูปลงโฟลเดอร์ screenshots/
                saved_img_path = None
                if device_screen is not None:
                    try:
                        os.makedirs("screenshots", exist_ok=True)
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        saved_img_path = f"screenshots/round_{ts}.png"
                        cv2.imwrite(saved_img_path, device_screen)
                    except Exception as err:
                        print(f"⚠️ ไม่สามารถบันทึกรูปภาพหน้าจอ: {err}")

                # 5. [ขั้นตอนบันทึก - Record Stats] แสดงข้อมูลสถิติที่บันทึก
                score_log = f"คะแนน: {round_score:,} | " if round_score > 0 else ""
                xp_log = f" | +{round_xp:,} EXP" if round_xp > 0 else ""
                box_log = f" | 📦 ได้รับ {len(round_boxes)} กล่อง" if round_boxes else ""
                print(f"💾 [บันทึกข้อมูลสำเร็จ] {score_log}+{round_coins:,} 🪙{xp_log}{box_log}")
                if saved_img_path:
                    print(f"   📸 บันทึกรูปภาพผลลัพธ์: {saved_img_path}")

                # บันทึกลง history/play_history.csv
                try:
                    import csv
                    history_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "history"))
                    os.makedirs(history_dir, exist_ok=True)
                    csv_path = os.path.join(history_dir, "play_history.csv")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    time_str = datetime.now().strftime("%H:%M:%S")
                    write_hdr = not os.path.isfile(csv_path)
                    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        if write_hdr:
                            writer.writerow(["Date", "Time", "Device", "Score", "Coins", "XP", "Boxes", "Screenshot"])
                        writer.writerow([today_str, time_str, f"{DEVICE_IP}:{DEVICE_PORT}", round_score, round_coins, round_xp, ";".join(round_boxes), saved_img_path or ""])
                    print("   📁 บันทึกประวัติการเล่นลง: history/play_history.csv")
                except Exception as err:
                    print(f"⚠️ ไม่สามารถบันทึกประวัติการเล่น: {err}")

                # 6. หน่วงเวลาให้ดูผลลัพธ์ทั้งหมด (Score, Coins, XP, Boxes) ชัดเจนก่อนกด OK
                print("⏳ บันทึกผลลัพธ์เรียบร้อย — กำลังแสดงหน้า Result ให้ดูทั้งหมดก่อนกด OK...")
                time.sleep(random.uniform(2.5, 3.5))

                # 7. กดปุ่ม OK เพื่อดำเนินการต่อ
                print("👉 กดปุ่ม OK เพื่อดำเนินการต่อ")
                complete_finish()
                detection_group = "POST_GAME"

                # 8. เคลียร์แรม (RAM) ทุกๆ รอบที่ทำเสร็จ
                clear_system_memory(DEVICE_IP, DEVICE_PORT)
            elif stage == "MYSTERY_BOX":
                print("🎁 Detected Stage: MYSTERY_BOX")
                accept_mystery_box()
                time.sleep(3)
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "CONGRATULATIONS":
                print("🎉 Detected Stage: CONGRATULATIONS")
                accept_congratulations()
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "LEVEL_UP":
                print("⬆️ Detected Stage: LEVEL_UP")
                accept_level_up()
                detection_group = "PRE_GAME"
            elif stage == "DAILY_CHECKIN":
                print("📅 Detected Stage: DAILY_CHECKIN")
                accept_daily_checkin()
                detection_group = "PRE_GAME"
            elif stage == "DAILY_CHECKIN_BOOST_SET":
                print("📅 Detected Stage: DAILY_CHECKIN_BOOST_SET")
                accept_daily_checkin_boost_set()
                detection_group = "PRE_GAME"
            elif stage == "DAILY_TREASURE":
                print("💎 Detected Stage: DAILY_TREASURE")
                accept_daily_treasure()
                detection_group = "PRE_GAME"
            elif stage == "DAILY_NEW":
                print("📰 Detected Stage: DAILY_NEW")
                accept_daily_new()
                detection_group = "PRE_GAME"
            elif stage == "ENTER_LEAGUE":
                print("🏆 Detected Stage: ENTER_LEAGUE")
                accept_enter_league()
                detection_group = "PRE_GAME"
            elif stage == "LEAGUE_RESULTS":
                print("🏆 Detected Stage: LEAGUE_RESULTS")
                accept_league_results()
                detection_group = "PRE_GAME"
            elif stage == "PREVIOUS_RANK_RESULTS":
                print("🏆 Detected Stage: PREVIOUS_RANK_RESULTS")
                accept_previous_rank_results()
                detection_group = "PRE_GAME"
            elif stage == "OVERTAKE_BREAK_SCORE":
                print("🏆 Detected Stage: OVERTAKE_BREAK_SCORE")
                accept_overtake_break_score()
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "TOO_MANY_TREASURES":
                print("💎 Detected Stage: TOO_MANY_TREASURES")
                accept_too_many_treasures()
                detection_group = "PRE_GAME"
            elif stage == "RELIC_COMPLETE":
                print("🏺 Detected Stage: RELIC_COMPLETE")
                open_relic_complete()
                detection_group = "PRE_GAME"
            elif stage == "RELIC_CLAIM":
                print("🏺 Detected Stage: RELIC_CLAIM")
                accept_relic_claim()
                detection_group = "PRE_GAME"
            elif stage == "ANTI_BOT":
                print("⚠️ Detected Stage: ANTI_BOT")
                handle_anti_bot(device_screen)
                last_stage = None
            elif stage == "CONNECTION_LOST":
                print("🔌 Detected Stage: CONNECTION_LOST")
                device_reset_app(DEVICE_IP, DEVICE_PORT)
                time.sleep(2)
                close_announcement_dialog()
                session_start_time = time.time()
                session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
                last_lives_time = time.time()
                lives_interval = random.uniform(25 * 60, 35 * 60)
                detection_group = "PRE_GAME"
                last_stage = None
                is_first_game = True
            elif stage == "INACTIVE":
                print("💤 Detected Stage: INACTIVE")
                handle_inactive()
                last_stage = None
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
