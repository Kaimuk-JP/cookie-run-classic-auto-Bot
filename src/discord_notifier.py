import io
import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional

import cv2
import requests


SETTINGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings"))
os.makedirs(SETTINGS_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(SETTINGS_DIR, "discord_config.json")
LEGACY_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "discord_config.json")

DEFAULT_CUSTOM_EMOJIS: Dict[str, str] = {
    "wood": "<:BOX_WOOD:1551086213329457224>",
    "silver": "<:BOX_SILVER:1551086179510915082>",
    "gold": "<:BOX_GOLD:1551086058303914115>",
    "rainbow": "<:BOX_RAINBOW:1551086131938852934>",
    "coins": "<:coins:1551093855892279306>",
    "xp": "<:starz:1551093812838006794>",
    "minigame": "<:minigame:1551093835306635284>",
    "allbox": "<:allboxs:1551095910719819816>",
    "time": "<:time:1551096036964171837>",
    "bill": "<:bill:1551096073886371971>",
    "total": "<:Total:1551097511329145013>",
}


class DiscordNotifier:
    def __init__(self):
        self.webhook_url: str = ""
        self.enabled: bool = False
        self.notify_boxes: bool = True
        self.notify_rounds: bool = True
        self.notify_antibot: bool = True
        self.notify_status: bool = True
        self.attach_screenshot: bool = True
        self.custom_emojis: Dict[str, str] = dict(DEFAULT_CUSTOM_EMOJIS)
        self.load_config()

    def load_config(self):
        cfg_path = CONFIG_FILE if os.path.isfile(CONFIG_FILE) else (LEGACY_CONFIG_FILE if os.path.isfile(LEGACY_CONFIG_FILE) else None)
        if cfg_path:
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.webhook_url = data.get("webhook_url", "")
                    self.enabled = bool(data.get("enabled", False))
                    self.notify_boxes = bool(data.get("notify_boxes", True))
                    self.notify_rounds = bool(data.get("notify_rounds", True))
                    self.notify_antibot = bool(data.get("notify_antibot", True))
                    self.notify_status = bool(data.get("notify_status", True))
                    self.attach_screenshot = bool(data.get("attach_screenshot", True))
                    loaded_emojis = data.get("custom_emojis")
                    if isinstance(loaded_emojis, dict):
                        self.custom_emojis = {**DEFAULT_CUSTOM_EMOJIS, **{k: v for k, v in loaded_emojis.items() if v}}
                    else:
                        self.custom_emojis = dict(DEFAULT_CUSTOM_EMOJIS)
            except Exception as e:
                print(f"[Discord] Error loading config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "webhook_url": self.webhook_url,
                    "enabled": self.enabled,
                    "notify_boxes": self.notify_boxes,
                    "notify_rounds": self.notify_rounds,
                    "notify_antibot": self.notify_antibot,
                    "notify_status": self.notify_status,
                    "attach_screenshot": self.attach_screenshot,
                    "custom_emojis": self.custom_emojis,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Discord] Error saving config: {e}")

    def update_settings(self, settings: dict):
        if "webhook_url" in settings:
            self.webhook_url = str(settings["webhook_url"]).strip()
        if "enabled" in settings:
            self.enabled = bool(settings["enabled"])
        if "notify_boxes" in settings:
            self.notify_boxes = bool(settings["notify_boxes"])
        if "notify_rounds" in settings:
            self.notify_rounds = bool(settings["notify_rounds"])
        if "notify_antibot" in settings:
            self.notify_antibot = bool(settings["notify_antibot"])
        if "notify_status" in settings:
            self.notify_status = bool(settings["notify_status"])
        if "attach_screenshot" in settings:
            self.attach_screenshot = bool(settings["attach_screenshot"])
        if "custom_emojis" in settings and isinstance(settings["custom_emojis"], dict):
            self.custom_emojis = settings["custom_emojis"]
        self.save_config()

    def _async_send(self, payload: dict, screen_img=None, box_thumb_img: Optional[str] = None, force_attach: bool = False):
        """Send webhook in a separate daemon thread so it never lags the bot loop."""
        threading.Thread(target=self._send_payload, args=(payload, screen_img, box_thumb_img, force_attach), daemon=True).start()

    def _send_payload(self, payload: dict, screen_img=None, box_thumb_img: Optional[str] = None, force_attach: bool = False):
        if not self.enabled or not self.webhook_url:
            return False

        try:
            files = {}
            file_idx = 0

            # 1. Attach box thumbnail icon if present
            if box_thumb_img and os.path.isfile(box_thumb_img):
                try:
                    with open(box_thumb_img, "rb") as bf:
                        thumb_bytes = bf.read()
                    files[f"files[{file_idx}]"] = ("thumb.png", io.BytesIO(thumb_bytes), "image/png")
                    file_idx += 1
                    if "embeds" in payload and payload["embeds"]:
                        payload["embeds"][0]["thumbnail"] = {"url": "attachment://thumb.png"}
                except Exception as e:
                    print(f"[Discord] Error attaching thumb: {e}")

            # 2. Attach screenshot image
            should_attach = (self.attach_screenshot or force_attach) and screen_img is not None
            if should_attach:
                encoded_bytes = None
                if isinstance(screen_img, bytes):
                    encoded_bytes = screen_img
                elif isinstance(screen_img, str) and os.path.isfile(screen_img):
                    try:
                        with open(screen_img, "rb") as f:
                            encoded_bytes = f.read()
                    except Exception:
                        pass
                elif hasattr(screen_img, "shape"):  # numpy ndarray
                    success, encoded_img = cv2.imencode(".jpg", screen_img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    if success:
                        encoded_bytes = encoded_img.tobytes()

                if encoded_bytes:
                    files[f"files[{file_idx}]"] = ("screen.jpg", io.BytesIO(encoded_bytes), "image/jpeg")
                    file_idx += 1
                    if "embeds" in payload and payload["embeds"]:
                        payload["embeds"][0]["image"] = {"url": "attachment://screen.jpg"}

            if files:
                data = {"payload_json": json.dumps(payload)}
                res = requests.post(self.webhook_url, data=data, files=files, timeout=15)
            else:
                res = requests.post(self.webhook_url, json=payload, timeout=15)

            return res.status_code in [200, 204]
        except Exception as e:
            print(f"[Discord] Webhook send error: {e}")
            return False

    def _format_duration_th(self, duration_sec: int = 0, duration_str: str = "") -> str:
        try:
            duration_sec = int(duration_sec or 0)
        except Exception:
            duration_sec = 0
        if duration_sec <= 0 and duration_str:
            import re
            m = re.search(r"(\d+)m", str(duration_str))
            s = re.search(r"(\d+)s", str(duration_str))
            duration_sec = (int(m.group(1)) * 60 if m else 0) + (int(s.group(1)) if s else 0)
        if duration_sec >= 60:
            m = duration_sec // 60
            s = duration_sec % 60
            return f"{m} นาที {s} วิ" if s > 0 else f"{m} นาที"
        elif duration_sec > 0:
            return f"{duration_sec} วิ"
        return str(duration_str) or "0 วิ"

    def _get_box_icons(self) -> Dict[str, str]:
        ce = self.custom_emojis or {}
        return {
            "wood": ce.get("wood") or DEFAULT_CUSTOM_EMOJIS.get("wood", "📦"),
            "silver": ce.get("silver") or DEFAULT_CUSTOM_EMOJIS.get("silver", "🥈"),
            "gold": ce.get("gold") or DEFAULT_CUSTOM_EMOJIS.get("gold", "🥇"),
            "rainbow": ce.get("rainbow") or DEFAULT_CUSTOM_EMOJIS.get("rainbow", "🌈"),
        }

    def _build_round_summary_embed(
        self,
        round_num: int,
        duration_str: str,
        coins_earned: int,
        session_coins: int,
        xp_earned: int,
        session_xp: int,
        boxes: List[str] = None,
        device_name: str = "",
        duration_sec: int = 0,
        session_rounds: int = 0,
        session_boxes: Dict[str, int] = None,
        minigame_count: int = 0,
        session_minigame_count: int = 0,
        opened_items: List[str] = None,
        is_test: bool = False,
    ) -> dict:
        boxes = boxes or []
        session_boxes = session_boxes or {}
        opened_items = opened_items or []
        if session_rounds <= 0:
            session_rounds = round_num

        dur_text = self._format_duration_th(duration_sec, duration_str)
        dev_label = device_name or "SM-G991B"
        box_icons = self._get_box_icons()

        from collections import Counter
        b_counts = Counter(boxes)
        box_grade_names = {
            "wood": "กล่องไม้",
            "silver": "กล่องเงิน",
            "gold": "กล่องทอง",
            "rainbow": "กล่องสายรุ้ง",
        }

        total_boxes_round = len(boxes)
        if total_boxes_round > 0:
            round_box_header = f"▎ **กล่องรอบนี้ · {total_boxes_round} ใบ**"
            box_lines = []
            for grade in ["wood", "silver", "gold", "rainbow"]:
                if b_counts[grade] > 0:
                    box_lines.append(f"{box_icons[grade]} {box_grade_names[grade]} `× {b_counts[grade]}`")
            round_box_text = round_box_header + "\n" + "\n".join(box_lines)
            if opened_items:
                items_fmt = "\n".join([f"  • {it}" for it in opened_items])
                round_box_text += f"\n\n▎ **ของที่ได้รับจากกล่อง ({len(opened_items)} ชิ้น)**\n{items_fmt}"
        elif opened_items:
            items_fmt = "\n".join([f"  • {it}" for it in opened_items])
            round_box_text = f"▎ **ของที่ได้รับจากกล่อง ({len(opened_items)} ชิ้น)**\n{items_fmt}"
        else:
            round_box_text = "▎ **กล่องรอบนี้ · 0 ใบ**\n*(ไม่ได้รับกล่อง)*"

        wood_sess = session_boxes.get("wood", 0)
        silver_sess = session_boxes.get("silver", 0)
        gold_sess = session_boxes.get("gold", 0)
        rainbow_sess = session_boxes.get("rainbow", 0)
        total_sess_boxes = session_boxes.get("total", wood_sess + silver_sess + gold_sess + rainbow_sess)

        # Dynamic left accent color matching reference
        color = 0xEE5253  # Warm Coral / Reddish Pink
        if "rainbow" in boxes:
            color = 0xC084FC  # Radiant Violet
        elif "gold" in boxes:
            color = 0xF59E0B  # Vibrant Gold
        elif "silver" in boxes:
            color = 0x94A3B8  # Silver

        ce = self.custom_emojis or {}
        ico_coins = ce.get("coins") or DEFAULT_CUSTOM_EMOJIS.get("coins", "🪙")
        ico_xp = ce.get("xp") or DEFAULT_CUSTOM_EMOJIS.get("xp", "⭐")
        ico_minigame = ce.get("minigame") or DEFAULT_CUSTOM_EMOJIS.get("minigame", "🎴")
        ico_allbox = ce.get("allbox") or DEFAULT_CUSTOM_EMOJIS.get("allbox", "🎁")
        ico_time = ce.get("time") or DEFAULT_CUSTOM_EMOJIS.get("time", "⏱️")
        ico_bill = ce.get("bill") or DEFAULT_CUSTOM_EMOJIS.get("bill", "🧾")
        ico_total = ce.get("total") or DEFAULT_CUSTOM_EMOJIS.get("total", "📒")

        description = (
            f"{ico_time} {dur_text}\n"
            f"----------------------------------------\n"
            f"▎ **ได้รอบนี้**\n"
            f"{ico_coins} เหรียญ `{coins_earned:,}`\n"
            f"{ico_xp} XP `{xp_earned:,}`\n"
            f"{ico_minigame} มินิเกม `{minigame_count}`\n"
            f"----------------------------------------\n"
            f"{round_box_text}\n\n"
            f"{ico_total} **สะสมรอบการทำงานนี้ · {session_rounds} ตา**\n"
            f"{box_icons['wood']} ไม้ `{wood_sess}` · {box_icons['silver']} เงิน `{silver_sess}`\n"
            f"{box_icons['gold']} ทอง `{gold_sess}` · {box_icons['rainbow']} รุ้ง `{rainbow_sess}`\n"
            f"{ico_allbox} รวมกล่อง `{total_sess_boxes}` ใบ\n"
            f"{ico_coins} `{session_coins:,}` · {ico_xp} `{session_xp:,}` · {ico_minigame} `{session_minigame_count}`"
        )

        title = f"{ico_bill} {dev_label} · จบรอบที่ {round_num}{' (ทดสอบ)' if is_test else ''}"

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return embed

    def _get_box_thumbnail_path(self, boxes: List[str]) -> Optional[str]:
        if not boxes:
            return None
        tmpl_dir = os.path.join(os.path.dirname(__file__), "templates")
        if "rainbow" in boxes:
            fn = "BOX_RAINBOW.png"
        elif "gold" in boxes:
            fn = "BOX_GOLD.png"
        elif "silver" in boxes:
            fn = "BOX_SILVER.png"
        elif "wood" in boxes:
            fn = "BOX_WOOD.png"
        else:
            return None
        path = os.path.join(tmpl_dir, fn)
        return path if os.path.isfile(path) else None

    def test_webhook(self, url: Optional[str] = None) -> tuple[bool, str]:
        """Test the webhook URL with the real styled summary embed preview and sample screenshot."""
        target_url = (url or self.webhook_url).strip()
        if not target_url:
            return False, "กรุณากรอก Discord Webhook URL"

        dev_name = "SM-g991b"
        screen_img = None
        try:
            from adb import scan_adb_devices, device_capture_screen
            devs = scan_adb_devices()
            if devs:
                dev_name = devs[0].get("emu_name") or devs[0].get("name") or dev_name
                target = devs[0].get("serial") or devs[0].get("name")
                if target:
                    screen_img = device_capture_screen(target, 5555)
        except Exception:
            pass

        # If no active device capture available, look for recent screenshot or generate a preview canvas
        if screen_img is None:
            try:
                sc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "screenshots"))
                if os.path.isdir(sc_dir):
                    sc_files = [os.path.join(sc_dir, f) for f in os.listdir(sc_dir) if f.endswith(('.png', '.jpg'))]
                    if sc_files:
                        latest_sc = max(sc_files, key=os.path.getmtime)
                        screen_img = cv2.imread(latest_sc)
            except Exception:
                pass

        if screen_img is None:
            try:
                import numpy as np
                preview = np.zeros((720, 1280, 3), dtype=np.uint8)
                preview[:] = (32, 28, 28)
                cv2.rectangle(preview, (30, 30), (1250, 690), (60, 50, 50), 2)
                cv2.putText(preview, "CookieRun Bot - Discord Preview", (60, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
                cv2.putText(preview, "Screenshot attachment is active and working!", (60, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (120, 220, 120), 2)
                cv2.putText(preview, f"Device: {dev_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", (60, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 180, 180), 1)

                box_path = os.path.join(os.path.dirname(__file__), "templates", "BOX_RAINBOW.png")
                if os.path.isfile(box_path):
                    box_im = cv2.imread(box_path, cv2.IMREAD_UNCHANGED)
                    if box_im is not None:
                        h, w = box_im.shape[:2]
                        y_off, x_off = 300, 560
                        if len(box_im.shape) == 3 and box_im.shape[2] == 4:
                            alpha = box_im[:, :, 3] / 255.0
                            for c in range(3):
                                preview[y_off:y_off+h, x_off:x_off+w, c] = (
                                    alpha * box_im[:, :, c] + (1.0 - alpha) * preview[y_off:y_off+h, x_off:x_off+w, c]
                                )
                        else:
                            preview[y_off:y_off+h, x_off:x_off+w] = box_im[:h, :w, :3]
                screen_img = preview
            except Exception:
                screen_img = None

        embed = self._build_round_summary_embed(
            round_num=22,
            duration_str="6m 17s",
            duration_sec=377,
            coins_earned=104768,
            session_coins=2314558,
            xp_earned=8655,
            session_xp=190912,
            boxes=["wood", "silver", "rainbow"],
            device_name=dev_name,
            session_rounds=22,
            session_boxes={"wood": 16, "silver": 25, "gold": 15, "rainbow": 9, "total": 65},
            opened_items=["Pastry Crumbs (Ingredient)", "Giant Dragonfly Wing (Ingredient)"],
            is_test=True,
        )

        box_thumb = self._get_box_thumbnail_path(["rainbow"])
        old_url = self.webhook_url
        old_enabled = self.enabled
        try:
            self.webhook_url = target_url
            self.enabled = True
            ok = self._send_payload(
                {"username": "CookieRun Bot", "embeds": [embed]},
                screen_img=screen_img,
                box_thumb_img=box_thumb,
                force_attach=True,
            )
            if ok:
                return True, "ส่งข้อความทดสอบสำเร็จ! โปรดตรวจสอบในห้อง Discord ของคุณ"
            return False, "ส่งข้อความไม่สำเร็จ โปรดตรวจสอบ Webhook URL"
        except Exception as e:
            return False, f"ส่งข้อความไม่สำเร็จ: {str(e)}"
        finally:
            self.webhook_url = old_url
            self.enabled = old_enabled

    def send_bot_start(self, device_ip: str, device_port: int, device_name: str = ""):
        if not self.notify_status or not self.enabled or not self.webhook_url:
            return

        dev_label = device_name or f"{device_ip}:{device_port}"
        embed = {
            "title": f"🟢 เริ่มต้นการทำงาน · {dev_label}",
            "description": (
                "🚀 **บอทฟาร์ม CookieRun Classic พร้อมทำงานแล้ว**\n"
                "----------------------------------------\n"
                f"📱 **อุปกรณ์:** `{dev_label}`\n"
                f"⏰ **เวลาเริ่ม:** `{datetime.now().strftime('%H:%M:%S')}`"
            ),
            "color": 0x22C55E,  # Green
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._async_send({"username": "CookieRun Bot", "embeds": [embed]})

    def send_bot_stop(self, uptime: str, rounds_played: int, total_boxes: int, coins_earned: int = 0, session_xp: int = 0, device_name: str = ""):
        if not self.notify_status or not self.enabled or not self.webhook_url:
            return

        dev_label = device_name or "CookieRun Bot"
        embed = {
            "title": f"🔴 หยุดการทำงาน · {dev_label}",
            "description": (
                "⏹️ **บอทได้หยุดการทำงานเรียบร้อยแล้ว**\n"
                "----------------------------------------\n"
                f"⏱️ **เวลาทำงานรวม:** `{uptime}`\n"
                f"🔄 **จำนวนรอบ:** `{rounds_played:,}` รอบ\n"
                f"🎁 **กล่องทั้งหมด:** `{total_boxes:,}` กล่อง\n"
                f"🪙 **เหรียญสะสม:** `+{coins_earned:,}` 🪙\n"
                f"⭐ **EXP สะสม:** `+{session_xp:,}` EXP\n"
                f"⏰ **เวลาหยุด:** `{datetime.now().strftime('%H:%M:%S')}`"
            ),
            "color": 0xEF4444,  # Red
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._async_send({"username": "CookieRun Bot", "embeds": [embed]})

    def send_box_drop(
        self,
        round_num: int,
        boxes: List[str],
        total_boxes: Dict[str, int],
        coins_earned: int = 0,
        session_coins: int = 0,
        xp_earned: int = 0,
        session_xp: int = 0,
        screen_img=None,
        device_name: str = "",
        duration_sec: int = 0,
        duration_str: str = "",
        session_rounds: int = 0,
        opened_items: List[str] = None,
        force_attach: bool = False,
    ):
        if not self.notify_boxes or not self.enabled or not self.webhook_url:
            return

        embed = self._build_round_summary_embed(
            round_num=round_num,
            duration_str=duration_str,
            coins_earned=coins_earned,
            session_coins=session_coins,
            xp_earned=xp_earned,
            session_xp=session_xp,
            boxes=boxes,
            device_name=device_name,
            duration_sec=duration_sec,
            session_rounds=session_rounds or round_num,
            session_boxes=total_boxes,
            opened_items=opened_items,
        )
        box_thumb = self._get_box_thumbnail_path(boxes)
        if opened_items:
            force_attach = True
        self._async_send(
            {"username": "CookieRun Bot", "embeds": [embed]},
            screen_img=screen_img,
            box_thumb_img=box_thumb,
            force_attach=force_attach,
        )

    def send_round_summary(
        self,
        round_num: int,
        duration_str: str,
        coins_earned: int,
        session_coins: int,
        xp_earned: int,
        session_xp: int,
        boxes: List[str] = None,
        screen_img=None,
        device_name: str = "",
        duration_sec: int = 0,
        session_rounds: int = 0,
        session_boxes: Dict[str, int] = None,
        minigame_count: int = 0,
        session_minigame_count: int = 0,
        opened_items: List[str] = None,
        force_attach: bool = False,
    ):
        if not self.notify_rounds or not self.enabled or not self.webhook_url:
            return

        embed = self._build_round_summary_embed(
            round_num=round_num,
            duration_str=duration_str,
            coins_earned=coins_earned,
            session_coins=session_coins,
            xp_earned=xp_earned,
            session_xp=session_xp,
            boxes=boxes,
            device_name=device_name,
            duration_sec=duration_sec,
            session_rounds=session_rounds,
            session_boxes=session_boxes,
            minigame_count=minigame_count,
            session_minigame_count=session_minigame_count,
            opened_items=opened_items,
        )
        box_thumb = self._get_box_thumbnail_path(boxes)
        if opened_items:
            force_attach = True
        self._async_send(
            {"username": "CookieRun Bot", "embeds": [embed]},
            screen_img=screen_img,
            box_thumb_img=box_thumb,
            force_attach=force_attach,
        )

    def send_anti_bot_alert(self, stage: str, details: str = "", screen_img=None):
        if not self.notify_antibot or not self.enabled or not self.webhook_url:
            return

        embed = {
            "title": "⚠️ ตรวจพบระบบป้องกันบอท (Anti-Bot Captcha)",
            "description": f"🤖 กำลังแก้ระบบป้องกันอัตโนมัติ...\n{details}",
            "color": 0xF97316,  # Orange
            "fields": [
                {"name": "⏰ เวลาที่พบ", "value": datetime.now().strftime("%H:%M:%S"), "inline": True},
            ],
            "footer": {"text": "CookieRun Classic Bot - Security Alert"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._async_send({"username": "CookieRun Bot Alert", "embeds": [embed]}, screen_img=screen_img, force_attach=True)

    def send_connection_lost(self, device_ip: str, device_port: int):
        if not self.notify_status or not self.enabled or not self.webhook_url:
            return

        embed = {
            "title": "🔌 การเชื่อมต่อขัดข้อง (Connection Lost)",
            "description": f"บอทกำลังรีเซ็ตและเปิดเกม CookieRun ใหม่อัตโนมัติ...",
            "color": 0xEF4444,  # Red
            "fields": [
                {"name": "อุปกรณ์", "value": f"`{device_ip}:{device_port}`", "inline": True},
                {"name": "⏰ เวลา", "value": datetime.now().strftime("%H:%M:%S"), "inline": True},
            ],
            "footer": {"text": "CookieRun Classic Bot"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._async_send({"username": "CookieRun Bot", "embeds": [embed]})

    def send_goal_reached(self, goal_description: str, uptime: str, rounds_played: int, total_boxes: int, coins_earned: int, session_xp: int):
        if not self.notify_status or not self.enabled or not self.webhook_url:
            return

        embed = {
            "title": "🎯 บรรลุเป้าหมายการฟาร์ม (Goal Reached)",
            "description": f"✨ **{goal_description}**\nบอทได้ทำการหยุดทำงานอัตโนมัติเรียบร้อยแล้ว",
            "color": 0xF59E0B,  # Amber / Gold
            "fields": [
                {"name": "🎯 เป้าหมายที่สำเร็จ", "value": goal_description, "inline": False},
                {"name": "⏱️ เวลาทำงานรวม", "value": uptime, "inline": True},
                {"name": "🔄 รอบที่เล่น", "value": f"{rounds_played} รอบ", "inline": True},
                {"name": "🎁 กล่องปริศนา", "value": f"{total_boxes} กล่อง", "inline": True},
                {"name": "💰 เหรียญสะสมทั้งหมด", "value": f"+{coins_earned:,} 🪙", "inline": True},
                {"name": "⭐ EXP สะสมทั้งหมด", "value": f"+{session_xp:,} EXP", "inline": True},
                {"name": "⏰ เวลาสิ้นสุด", "value": datetime.now().strftime("%H:%M:%S"), "inline": True},
            ],
            "footer": {"text": "CookieRun Classic Bot - Goal System"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._async_send({"username": "CookieRun Bot", "embeds": [embed]})

    def send_tunnel_started(self, tunnel_url: str, local_ip: str = "", port: int = 8000) -> bool:
        """Blocking send (call from a background thread); returns True when Discord accepted it."""
        self.load_config()
        if not self.webhook_url:
            return False

        embed = {
            "title": "🌐 ลิงก์ดูบอทผ่านมือถือ (Online Dashboard)",
            "description": f"เปิดบอทเรียบร้อยแล้ว! สามารถกดลิงก์ด้านล่างเพื่อเปิด Web Dashboard ผ่านมือถือได้ทันที:\n\n👉 **[คลิกเพื่อเปิด Web Dashboard บนมือถือ]({tunnel_url})**",
            "color": 0x10B981,  # Emerald Green
            "fields": [
                {"name": "Mobile Web Link", "value": f"[คลิกเปิดที่นี่]({tunnel_url})\n`{tunnel_url}`", "inline": False},
                {"name": "🏠 Wi-Fi ในบ้าน", "value": f"http://{local_ip}:{port}" if local_ip and local_ip != "127.0.0.1" else f"http://127.0.0.1:{port}", "inline": True},
                {"name": "💻 คอมพิวเตอร์ (PC)", "value": f"http://127.0.0.1:{port}", "inline": True},
                {"name": "⏰ เวลาเปิดบอท", "value": datetime.now().strftime("%H:%M:%S"), "inline": True},
            ],
            "footer": {"text": "CookieRun Classic Bot - Remote Mobile Control"},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        payload = {
            "username": "CookieRun Bot Monitor",
            "content": f"🚀 **บอทเปิดทำงานแล้ว! ลิงก์สำหรับดูผ่านมือถือ:** {tunnel_url}",
            "embeds": [embed]
        }
        return self._send_payload(payload)


discord_notifier = DiscordNotifier()
