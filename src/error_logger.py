import os
import time
import json
from datetime import datetime
from typing import Optional
import cv2
import numpy as np

LOGS_ERROR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs_error"))
os.makedirs(LOGS_ERROR_DIR, exist_ok=True)

ERROR_TXT_PATH = os.path.join(LOGS_ERROR_DIR, "error_log.txt")
ERROR_JSON_PATH = os.path.join(LOGS_ERROR_DIR, "error_history.json")


def record_game_error(
    device_serial: str,
    reason: str,
    details: str,
    screen_img: Optional[np.ndarray] = None,
    action_taken: str = "บังคับปิดเกมและเปิดใหม่ (Force Restart App)"
) -> dict:
    """
    Records game error events with explanation and full screenshot to logs_error/.
    Triggered when:
    - Game cannot start / button cannot be found (Searching... timeout)
    - Game gets stuck in unhandled popup or error state
    - Play button is unresponsive
    """
    os.makedirs(LOGS_ERROR_DIR, exist_ok=True)
    now_dt = datetime.now()
    time_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = now_dt.strftime("%Y%m%d_%H%M%S")
    safe_serial = "".join(c if c.isalnum() else "_" for c in str(device_serial or "default"))

    # 1. Save screenshot if available
    screenshot_rel_path = ""
    if screen_img is not None:
        filename = f"error_{safe_serial}_{timestamp_file}.png"
        full_path = os.path.join(LOGS_ERROR_DIR, filename)
        try:
            cv2.imwrite(full_path, screen_img)
            screenshot_rel_path = f"logs_error/{filename}"
        except Exception as e:
            print(f"Failed to save error screenshot: {e}")

    # 2. Append formatted readable log to error_log.txt
    entry_text = (
        f"\n{'='*70}\n"
        f"[{time_str}] อุปกรณ์: {device_serial}\n"
        f"⚠️ สาเหตุ: {reason}\n"
        f"🔍 รายละเอียด: {details}\n"
        f"📸 ภาพหน้าจอที่บันทึก: {screenshot_rel_path or 'ไม่มีภาพ'}\n"
        f"🔄 การแก้ไขอัตโนมัติ: {action_taken}\n"
        f"{'='*70}\n"
    )
    try:
        with open(ERROR_TXT_PATH, "a", encoding="utf-8") as f:
            f.write(entry_text)
    except Exception as e:
        print(f"Failed to append error log txt: {e}")

    # 3. Append to error_history.json
    error_record = {
        "timestamp": time_str,
        "device_serial": device_serial,
        "reason": reason,
        "details": details,
        "screenshot": screenshot_rel_path,
        "action_taken": action_taken,
    }
    try:
        records = []
        if os.path.isfile(ERROR_JSON_PATH):
            try:
                with open(ERROR_JSON_PATH, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []
        records.append(error_record)
        # Keep last 100 error entries
        if len(records) > 100:
            records = records[-100:]
        with open(ERROR_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to write error log json: {e}")

    return error_record
