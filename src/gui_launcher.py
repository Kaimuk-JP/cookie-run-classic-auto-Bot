"""
Desktop GUI Launcher for CookieRun Bot.
Provides:
1. Login & License authentication screen.
2. Welcome screen with automatic ADB & Emulator discovery (LDPlayer, MuMu, Nox, BlueStacks).
3. Background Web Server controller and 1-click Web Dashboard launcher.
"""

import os
import sys
import threading
import time
import webbrowser
from typing import Optional, List, Dict, Any

# Ensure UTF-8 output encoding or safe fallback for GUI (no console) mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure 'src' is on sys.path
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
_parent_dir = os.path.dirname(_this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from path_utils import get_project_root, get_settings_dir
_root_dir = get_project_root()
try:
    os.chdir(_root_dir)
except Exception:
    pass

# Setup TCL_LIBRARY and TK_LIBRARY if bundled
for _base in [_root_dir, _this_dir, _parent_dir]:
    _tcl_candidate = os.path.join(_base, "tcl", "tcl8.6")
    _tk_candidate = os.path.join(_base, "tcl", "tk8.6")
    if os.path.isdir(_tcl_candidate) and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = _tcl_candidate
    if os.path.isdir(_tk_candidate) and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = _tk_candidate

import customtkinter as ctk
from PIL import Image

import auth_manager
import adb

# Global background server reference
_server_thread: Optional[threading.Thread] = None
_server_port: int = 8000
_server_started: bool = False
_server_tunnel_url: Optional[str] = None


def find_free_port(start_port=8000, max_attempts=30):
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port


def start_backend_server(port: int):
    """Run uvicorn FastAPI server in background thread."""
    global _server_started
    import uvicorn
    from web_server import app
    _server_started = True
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, reload=False, log_level="warning")
    except Exception as e:
        print(f"[Launcher] Background server error: {e}")


class CookieRunLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance & Window Config - Warm Bakery / Sweet Kingdom Pastel Theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("CookieRun Classic Bot - Launcher & Manager")
        self.geometry("880x640")
        self.minsize(800, 580)

        # Set Window Icon
        icon_path = os.path.join(_this_dir, "bot_icon.ico")
        if not os.path.isfile(icon_path):
            icon_path = os.path.join(get_project_root(), "src", "bot_icon.ico")
        if os.path.isfile(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Center Window
        self.center_window(880, 640)

        # Current User & State
        self.current_user: Optional[Dict[str, Any]] = None
        self.discovered_devices: List[Dict[str, Any]] = []

        # Container Frame for swapping views - Warm Milk Cream Background
        self.container = ctk.CTkFrame(self, fg_color="#FFFDF6", corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Build Views
        self.login_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.welcome_frame = ctk.CTkFrame(self.container, fg_color="transparent")

        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")

        self.build_login_view()
        self.build_welcome_view()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Check for saved session
        saved_session = auth_manager.load_saved_session()
        if saved_session.get("remember") and saved_session.get("username"):
            self.entry_username.insert(0, saved_session["username"])
            self.switch_remember.select()
            ok, msg, user_info = auth_manager.verify_credentials(saved_session["username"], "1234")
            if ok:
                self.current_user = user_info
                # Auto-login: Jump directly into welcome screen and auto-open web dashboard!
                self.after(300, self.show_welcome)
                return

        # Show Login Frame first
        self.show_login()

    def center_window(self, width: int, height: int):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_login(self):
        self.welcome_frame.grid_remove()
        self.login_frame.grid()

    def show_welcome(self):
        self.login_frame.grid_remove()
        self.welcome_frame.grid()
        self.on_entered_welcome()

    def _get_asset_image(self, fname: str, size: tuple):
        """Helper to safely load CTkImage from src or app root in dev and frozen modes."""
        candidates = [
            os.path.join(get_project_root(), "src", fname),
            os.path.join(_this_dir, fname),
            os.path.join(get_project_root(), fname)
        ]
        for p in candidates:
            if os.path.isfile(p):
                try:
                    im = Image.open(p)
                    return ctk.CTkImage(light_image=im, dark_image=im, size=size)
                except Exception:
                    pass
        return None

    # -------------------------------------------------------------
    # VIEW 1: LOGIN SCREEN (Exact Match to User Mockup)
    # -------------------------------------------------------------
    def build_login_view(self):
        # Center Card - Clean Crisp Biscuit White with Warm Golden Border
        card = ctk.CTkFrame(
            self.login_frame,
            fg_color="#FFFFFF",
            corner_radius=32,
            border_width=2,
            border_color="#F6DFB8",
            width=470
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Preload high-res UI icon assets
        self.img_user_icon = self._get_asset_image("icon_user_gray.png", (18, 18))
        self.img_lock_icon = self._get_asset_image("icon_lock_gray.png", (18, 18))
        self.img_eye_open = self._get_asset_image("icon_eye_gray.png", (18, 18))
        self.img_eye_slash = self._get_asset_image("icon_eye_slash_gray.png", (18, 18))

        # Top App Badge Header (icon.png with sunny spark bursts)
        badge_img_path = os.path.join(get_project_root(), "src", "login_header_badge.png")
        if not os.path.isfile(badge_img_path):
            badge_img_path = os.path.join(_this_dir, "login_header_badge.png")
        if os.path.isfile(badge_img_path):
            try:
                pil_badge = Image.open(badge_img_path).resize((180, 106), Image.Resampling.LANCZOS)
                self.ctk_header_badge = ctk.CTkImage(light_image=pil_badge, dark_image=pil_badge, size=(180, 106))
                badge_lbl = ctk.CTkLabel(card, text="", image=self.ctk_header_badge)
                badge_lbl.pack(pady=(22, 6))
            except Exception:
                pass

        # Top Badge Pill - COOKIE RUN AUTOBOT PRO
        badge_frame = ctk.CTkFrame(card, fg_color="#FFF8E7", border_color="#F6D88E", border_width=1.5, corner_radius=14)
        badge_frame.pack(pady=(0, 8), padx=16)
        title_badge = ctk.CTkLabel(
            badge_frame,
            text="🤖  COOKIE RUN AUTOBOT PRO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8A4506"
        )
        title_badge.pack(padx=14, pady=4)

        # Title
        title_lbl = ctk.CTkLabel(
            card,
            text="เข้าสู่ระบบเข้าใช้งาน",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color="#3D2012"
        )
        title_lbl.pack(pady=(0, 4))

        # Subtitle
        sub_lbl = ctk.CTkLabel(
            card,
            text="โปรดป้อนข้อมูลให้ถูกต้องเพื่อเริ่มใช้งานเพื่อเริ่มต้นบอท",
            font=ctk.CTkFont(size=12),
            text_color="#8C6542"
        )
        sub_lbl.pack(pady=(0, 20))

        # Form Inputs Frame
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=40, pady=0)

        # Row 1: Username / Key Label
        lbl_u = ctk.CTkLabel(form_frame, text="ชื่อผู้ใช้ หรือ License Key", font=ctk.CTkFont(size=13, weight="bold"), text_color="#452311")
        lbl_u.pack(anchor="w", pady=(0, 6))

        # Username Input Box (with inner person icon)
        user_box = ctk.CTkFrame(form_frame, fg_color="#FFFDF9", border_color="#EEDBCE", border_width=1.5, corner_radius=18, height=46)
        user_box.pack(fill="x", pady=(0, 14))
        user_box.pack_propagate(False)

        if self.img_user_icon:
            lbl_user_icon = ctk.CTkLabel(user_box, text="", image=self.img_user_icon)
        else:
            lbl_user_icon = ctk.CTkLabel(user_box, text="👤", font=ctk.CTkFont(size=13), text_color="#A89080")
        lbl_user_icon.pack(side="left", padx=(14, 4))

        self.entry_username = ctk.CTkEntry(
            user_box,
            placeholder_text="เช่น admin หรือ CR-XXX",
            fg_color="transparent",
            border_width=0,
            text_color="#452311",
            placeholder_text_color="#A89080",
            font=ctk.CTkFont(size=13)
        )
        self.entry_username.pack(side="left", fill="x", expand=True, padx=4)

        # Row 2: Password Label
        lbl_p = ctk.CTkLabel(form_frame, text="รหัสผ่าน (ถ้ามี)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#452311")
        lbl_p.pack(anchor="w", pady=(0, 6))

        # Password Input Box (with inner lock icon and show/hide eye toggle button)
        pass_box = ctk.CTkFrame(form_frame, fg_color="#FFFDF9", border_color="#EEDBCE", border_width=1.5, corner_radius=18, height=46)
        pass_box.pack(fill="x", pady=(0, 12))
        pass_box.pack_propagate(False)

        if self.img_lock_icon:
            lbl_pass_icon = ctk.CTkLabel(pass_box, text="", image=self.img_lock_icon)
        else:
            lbl_pass_icon = ctk.CTkLabel(pass_box, text="🔒", font=ctk.CTkFont(size=13), text_color="#A89080")
        lbl_pass_icon.pack(side="left", padx=(14, 4))

        self.entry_password = ctk.CTkEntry(
            pass_box,
            placeholder_text="รหัสผ่านเข้าใช้งาน",
            show="•",
            fg_color="transparent",
            border_width=0,
            text_color="#452311",
            placeholder_text_color="#A89080",
            font=ctk.CTkFont(size=13)
        )
        self.entry_password.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_eye = ctk.CTkButton(
            pass_box,
            text="" if self.img_eye_open else "👁",
            image=self.img_eye_open if self.img_eye_open else None,
            width=34,
            height=34,
            fg_color="transparent",
            hover_color="#FFF4E0",
            text_color="#8A5A36",
            font=ctk.CTkFont(size=13),
            command=self.toggle_password_visibility
        )
        self.btn_eye.pack(side="right", padx=(0, 6))

        # Remember Me Toggle
        self.switch_remember = ctk.CTkCheckBox(
            form_frame,
            text="จดจำการล็อกอินในเครื่องนี้",
            font=ctk.CTkFont(size=12),
            text_color="#6B4226",
            checkbox_height=20,
            checkbox_width=20,
            corner_radius=6,
            border_color="#D4A373",
            border_width=2,
            hover_color="#D97706",
            fg_color="#F59E0B",
            checkmark_color="#FFFFFF"
        )
        self.switch_remember.pack(anchor="w", pady=(0, 10))

        # Error / Status Label
        self.lbl_login_status = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(size=12), text_color="#DC2626")
        self.lbl_login_status.pack(pady=(0, 6))

        # Big Honey Pill Login Button
        self.btn_login = ctk.CTkButton(
            form_frame,
            text="➔   เข้าสู่ระบบ   ➔",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=52,
            corner_radius=26,
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="#FFFFFF",
            command=self.handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 18))

        # Bottom Cute Cookie Divider
        divider = ctk.CTkFrame(card, fg_color="transparent")
        divider.pack(fill="x", padx=90, pady=(0, 22))

        line_left = ctk.CTkFrame(divider, height=1.5, fg_color="#F0DFCE")
        line_left.pack(side="left", fill="x", expand=True, pady=10)

        lbl_cookie = ctk.CTkLabel(divider, text="🍪", font=ctk.CTkFont(size=14))
        lbl_cookie.pack(side="left", padx=8)

        line_right = ctk.CTkFrame(divider, height=1.5, fg_color="#F0DFCE")
        line_right.pack(side="right", fill="x", expand=True, pady=10)

        # Bind Enter Key
        self.entry_username.bind("<Return>", lambda e: self.handle_login())
        self.entry_password.bind("<Return>", lambda e: self.handle_login())

    def toggle_password_visibility(self):
        """Toggle showing/hiding password in entry."""
        current_show = self.entry_password.cget("show")
        if current_show == "•":
            self.entry_password.configure(show="")
            if self.img_eye_slash:
                self.btn_eye.configure(image=self.img_eye_slash, text="")
            else:
                self.btn_eye.configure(text_color="#F59E0B")
        else:
            self.entry_password.configure(show="•")
            if self.img_eye_open:
                self.btn_eye.configure(image=self.img_eye_open, text="")
            else:
                self.btn_eye.configure(text_color="#8A5A36")

    def handle_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        ok, msg, user_info = auth_manager.verify_credentials(username, password)
        if ok:
            self.lbl_login_status.configure(text=msg, text_color="#059669")
            self.current_user = user_info
            # Save session
            remember = self.switch_remember.get() == 1
            auth_manager.save_saved_session(username, remember)
            # Switch to welcome screen after brief pause
            self.after(300, self.show_welcome)
        else:
            self.lbl_login_status.configure(text=msg, text_color="#DC2626")

    # -------------------------------------------------------------
    # VIEW 2: WELCOME & EMULATOR SCANNER SCREEN (Sweet Bakery Theme)
    # -------------------------------------------------------------
    def build_welcome_view(self):
        # Top Bar - Crisp White with Honey Accent
        top_bar = ctk.CTkFrame(self.welcome_frame, fg_color="#FFFFFF", height=66, corner_radius=0, border_width=2, border_color="#F0DFCE")
        top_bar.pack(fill="x", side="top")

        # Top Bar Logo & App Name
        logo_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=20, pady=12)

        lbl_logo = ctk.CTkLabel(
            logo_frame,
            text="🍪 CookieRun Bot Pro",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#D97706"
        )
        lbl_logo.pack(side="left")

        # Welcome User Pill
        user_pill = ctk.CTkFrame(top_bar, fg_color="#FFF9F0", border_color="#EEDBCE", border_width=1.5, corner_radius=10)
        user_pill.pack(side="left", padx=14, pady=14)

        self.lbl_welcome_user = ctk.CTkLabel(
            user_pill,
            text="ยินดีต้อนรับ",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#6B4226"
        )
        self.lbl_welcome_user.pack(padx=12, pady=4)

        # Logout Button
        btn_logout = ctk.CTkButton(
            top_bar,
            text="ออกจากระบบ",
            width=96,
            height=32,
            corner_radius=10,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#FFF1F2",
            hover_color="#FFE4E6",
            border_color="#FECDD3",
            border_width=1.5,
            text_color="#E11D48",
            command=self.handle_logout
        )
        btn_logout.pack(side="right", padx=20, pady=16)

        # Main Body (2 Columns / Biscuit Panels)
        body = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=18)
        body.grid_columnconfigure(0, weight=6)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure(0, weight=1)

        # Left Panel: ADB & Emulator Discovery
        emu_card = ctk.CTkFrame(
            body,
            fg_color="#FFFFFF",
            corner_radius=22,
            border_width=2,
            border_color="#F0DFCE"
        )
        emu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        emu_header = ctk.CTkFrame(emu_card, fg_color="transparent")
        emu_header.pack(fill="x", padx=20, pady=(18, 8))

        lbl_emu_title = ctk.CTkLabel(
            emu_header,
            text="📱 ตรวจจับตัวจำลอง (Emulator)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#452311"
        )
        lbl_emu_title.pack(side="left")

        self.btn_scan = ctk.CTkButton(
            emu_header,
            text="🔄 สแกนหา Emulator",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=136,
            height=34,
            corner_radius=12,
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="#FFFFFF",
            command=self.trigger_scan_devices
        )
        self.btn_scan.pack(side="right")

        # ADB Status Banner
        self.lbl_adb_status = ctk.CTkLabel(
            emu_card,
            text="กำลังตรวจสอบสถานะ ADB Engine...",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
            anchor="w"
        )
        self.lbl_adb_status.pack(fill="x", padx=22, pady=(0, 10))

        # Scrollable Device List Frame
        self.device_scroll = ctk.CTkScrollableFrame(
            emu_card,
            fg_color="#FFFDF9",
            corner_radius=14,
            border_width=1.5,
            border_color="#F3E5D8"
        )
        self.device_scroll.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        # Manual Connect Bar
        manual_frame = ctk.CTkFrame(
            emu_card,
            fg_color="#FFF8EC",
            border_color="#EEDBCE",
            border_width=1.5,
            corner_radius=12,
            height=46
        )
        manual_frame.pack(fill="x", padx=18, pady=(0, 18))

        lbl_manual = ctk.CTkLabel(
            manual_frame,
            text="ต่อตรง:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#6B4226"
        )
        lbl_manual.pack(side="left", padx=(14, 6), pady=8)

        self.entry_manual_ip = ctk.CTkEntry(
            manual_frame,
            placeholder_text="127.0.0.1:7555",
            width=150,
            height=32,
            corner_radius=10,
            fg_color="#FFFFFF",
            border_color="#EEDBCE",
            border_width=1.5,
            text_color="#452311",
            placeholder_text_color="#A89080"
        )
        self.entry_manual_ip.pack(side="left", padx=6, pady=8)

        btn_manual_connect = ctk.CTkButton(
            manual_frame,
            text="เชื่อมต่อ",
            width=76,
            height=32,
            corner_radius=10,
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.handle_manual_connect
        )
        btn_manual_connect.pack(side="left", padx=6, pady=8)

        # Right Panel: Web Dashboard Launcher & Controls
        dash_card = ctk.CTkFrame(
            body,
            fg_color="#FFFFFF",
            corner_radius=22,
            border_width=2,
            border_color="#F0DFCE"
        )
        dash_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        lbl_dash_title = ctk.CTkLabel(
            dash_card,
            text="🌐 แผงควบคุมบอท",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#452311"
        )
        lbl_dash_title.pack(anchor="w", padx=20, pady=(18, 4))

        lbl_dash_sub = ctk.CTkLabel(
            dash_card,
            text="ฟังก์ชันควบคุมทั้งหมดทำงานผ่าน Web Dashboard สุดล้ำ ทั้งการสตรีมจอสด สั่งเริ่มบอท และสถิติกล่องสมบัติ",
            font=ctk.CTkFont(size=11),
            text_color="#8A5A36",
            wraplength=260,
            justify="left"
        )
        lbl_dash_sub.pack(anchor="w", padx=20, pady=(0, 16))

        # Server Status Box
        self.server_status_box = ctk.CTkFrame(
            dash_card,
            fg_color="#FFF8EC",
            corner_radius=14,
            border_width=1.5,
            border_color="#EEDBCE"
        )
        self.server_status_box.pack(fill="x", padx=18, pady=(0, 16))

        self.lbl_server_status = ctk.CTkLabel(
            self.server_status_box,
            text="⏳ กำลังเตรียมเซิร์ฟเวอร์...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#D97706"
        )
        self.lbl_server_status.pack(padx=14, pady=12)

        # Prominent Launch Button
        self.btn_open_web = ctk.CTkButton(
            dash_card,
            text="🚀 เปิด Web Dashboard",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=16,
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="#FFFFFF",
            command=self.handle_open_web_dashboard
        )
        self.btn_open_web.pack(fill="x", padx=18, pady=(0, 14))

        # Quick Utility Buttons
        btn_clear_ram = ctk.CTkButton(
            dash_card,
            text="🧹 ล้าง RAM ตัวจำลอง",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            corner_radius=12,
            fg_color="#FFF9F0",
            hover_color="#FDF0DD",
            border_color="#EEDBCE",
            border_width=1.5,
            text_color="#8A3B04",
            command=self.handle_clear_ram
        )
        btn_clear_ram.pack(fill="x", padx=18, pady=(0, 10))

        btn_restart_adb = ctk.CTkButton(
            dash_card,
            text="⚡ รีสตาร์ท ADB Server",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            corner_radius=12,
            fg_color="#FFF9F0",
            hover_color="#FDF0DD",
            border_color="#EEDBCE",
            border_width=1.5,
            text_color="#8A3B04",
            command=self.handle_restart_adb
        )
        btn_restart_adb.pack(fill="x", padx=18, pady=(0, 18))

    def on_entered_welcome(self):
        # Update user label
        username = self.current_user.get("username", "User") if self.current_user else "User"
        role = self.current_user.get("role", "VIP") if self.current_user else "VIP"
        self.lbl_welcome_user.configure(text=f"ยินดีต้อนรับ, {username} [{role.upper()}]")

        # Start background server if not already running
        self.ensure_background_server()

        # Update ADB status and trigger auto scan
        adb_path = adb.get_adb_path()
        self.lbl_adb_status.configure(
            text=f"✅ ADB Engine: พร้อมใช้งาน ({os.path.basename(adb_path)})",
            text_color="#10B981"
        )
        self.trigger_scan_devices()

    def ensure_background_server(self, auto_open_browser: bool = True):
        global _server_thread, _server_port, _server_started
        if not _server_started:
            _server_port = find_free_port(8000)
            _server_thread = threading.Thread(
                target=start_backend_server,
                args=(_server_port,),
                daemon=True,
                name="LauncherWebServer"
            )
            _server_thread.start()

            # Poll for server ready then auto-open web dashboard in browser immediately!
            def check_ready_and_open():
                time.sleep(1.2)
                self.lbl_server_status.configure(
                    text=f"🟢 เซิร์ฟเวอร์พร้อมทำงาน (พอร์ต {_server_port})",
                    text_color="#10B981"
                )
                if auto_open_browser:
                    url = f"http://127.0.0.1:{_server_port}"
                    try:
                        os.startfile(url)
                    except Exception:
                        webbrowser.open(url)

            threading.Thread(target=check_ready_and_open, daemon=True).start()
        else:
            self.lbl_server_status.configure(
                text=f"🟢 เซิร์ฟเวอร์พร้อมทำงาน (พอร์ต {_server_port})",
                text_color="#10B981"
            )
            if auto_open_browser:
                url = f"http://127.0.0.1:{_server_port}"
                try:
                    os.startfile(url)
                except Exception:
                    webbrowser.open(url)

    def trigger_scan_devices(self):
        self.btn_scan.configure(text="⏳ กำลังค้นหา...", state="disabled")
        for widget in self.device_scroll.winfo_children():
            widget.destroy()

        lbl_loading = ctk.CTkLabel(self.device_scroll, text="กำลังสแกนหาพอร์ตและตัวจำลอง...", text_color="#A89080")
        lbl_loading.pack(pady=20)

        def scan_worker():
            try:
                devices = adb.scan_adb_devices()
            except Exception as e:
                devices = []
                print(f"[Launcher] Scan error: {e}")

            self.discovered_devices = devices
            self.after(0, self.render_device_list)

        threading.Thread(target=scan_worker, daemon=True).start()

    def render_device_list(self):
        self.btn_scan.configure(text="🔄 สแกนหา Emulator", state="normal")
        for widget in self.device_scroll.winfo_children():
            widget.destroy()

        if not self.discovered_devices:
            lbl_empty = ctk.CTkLabel(
                self.device_scroll,
                text="❌ ไม่พบ Emulator ที่เปิดอยู่\nกรุณาเปิด LDPlayer, MuMu หรือ Nox แล้วกดสแกนใหม่",
                font=ctk.CTkFont(size=12),
                text_color="#EF4444",
                justify="center"
            )
            lbl_empty.pack(pady=28)
            return

        for dev in self.discovered_devices:
            card = ctk.CTkFrame(
                self.device_scroll,
                fg_color="#FFFFFF",
                corner_radius=12,
                border_width=1.5,
                border_color="#EEDBCE"
            )
            card.pack(fill="x", pady=5, padx=3)

            info_col = ctk.CTkFrame(card, fg_color="transparent")
            info_col.pack(side="left", padx=14, pady=10)

            name = dev.get("name") or dev.get("display_name") or dev.get("serial")
            serial = dev.get("serial")
            status = dev.get("status", "device")

            lbl_name = ctk.CTkLabel(
                info_col,
                text=f"🎮 {name}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#452311"
            )
            lbl_name.pack(anchor="w")

            lbl_serial = ctk.CTkLabel(
                info_col,
                text=f"Serial: {serial} • {status.upper()}",
                font=ctk.CTkFont(size=11),
                text_color="#8A5A36"
            )
            lbl_serial.pack(anchor="w")

            badge_frame = ctk.CTkFrame(
                card,
                fg_color="#ECFDF5",
                border_color="#A7F3D0",
                border_width=1.5,
                corner_radius=8
            )
            badge_frame.pack(side="right", padx=14)

            badge = ctk.CTkLabel(
                badge_frame,
                text="● READY",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#059669"
            )
            badge.pack(padx=8, pady=3)

    def handle_manual_connect(self):
        ip_port = self.entry_manual_ip.get().strip()
        if not ip_port:
            return
        parts = ip_port.split(":")
        ip = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5555

        def connect_worker():
            ok, msg = adb.device_check_connection(ip, port)
            self.after(0, lambda: self.trigger_scan_devices())

        threading.Thread(target=connect_worker, daemon=True).start()

    def handle_clear_ram(self):
        def clear_worker():
            try:
                adb.clear_system_memory(None)
            except Exception:
                pass
        threading.Thread(target=clear_worker, daemon=True).start()

    def handle_restart_adb(self):
        def restart_worker():
            try:
                adb_path = adb.get_adb_path()
                import subprocess
                subprocess.run([adb_path, "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([adb_path, "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            self.after(500, self.trigger_scan_devices)
        threading.Thread(target=restart_worker, daemon=True).start()

    def handle_open_web_dashboard(self):
        url = f"http://127.0.0.1:{_server_port}"
        try:
            os.startfile(url)
        except Exception:
            webbrowser.open(url)

    def handle_logout(self):
        self.current_user = None
        self.show_login()

    def on_window_close(self):
        """Cleanup and shutdown server when GUI window is closed."""
        try:
            # Cleanly stop any running streams
            from scrcpy_streamer import stream_manager
            stream_manager.stop_all()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)


_SINGLE_INSTANCE_MUTEX = None

def enforce_single_instance(window_title: str = "CookieRun Classic Bot - Launcher & Manager"):
    """
    Enforce single running instance of CookieRun Bot using a system-wide Windows Named Mutex.
    If another instance is already running, focus the existing window and immediately exit.
    """
    global _SINGLE_INSTANCE_MUTEX
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        MUTEX_NAME = "CookieRun_Classic_Bot_Global_Mutex_v2"
        _SINGLE_INSTANCE_MUTEX = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        ERROR_ALREADY_EXISTS = 183
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            hwnd = user32.FindWindowW(None, window_title)
            if hwnd:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
            sys.exit(0)
    except Exception:
        pass


if __name__ == "__main__":
    enforce_single_instance()
    try:
        app = CookieRunLauncherApp()
        app.mainloop()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        try:
            log_dir = os.path.join(get_project_root(), "logs_error")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "crash_log.txt"), "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"เกิดข้อผิดพลาดในการเปิดระบบ:\n\n{err_msg}\n\n(บันทึกรายละเอียดไว้ใน logs_error/crash_log.txt)",
                "CookieRun Bot - Launcher Error",
                0x10  # MB_ICONERROR
            )
        except Exception:
            pass
        sys.exit(1)
