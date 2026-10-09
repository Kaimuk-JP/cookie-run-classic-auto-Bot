"""
Cloudflare quick tunnel for the Web Dashboard, shared by run_web.py (START_BOT.bat)
and gui_launcher.py (EXE / START_GUI.bat). Posts the public link to Discord once found.
"""

import atexit
import os
import re
import subprocess
import threading
import time
from typing import Optional

from path_utils import get_logs_dir, get_project_root

URL_PATTERN = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
URL_WAIT_TIMEOUT = 60.0

_tunnel_process: Optional[subprocess.Popen] = None
_tunnel_port: Optional[int] = None
_tunnel_url: Optional[str] = None
_lock = threading.Lock()


def _log(msg: str):
    """Print (console mode) and append to logs/tunnel.log (the EXE has no console)."""
    try:
        print(msg, flush=True)
    except Exception:
        pass  # console without UTF-8 (or none at all) must never break the tunnel
    try:
        with open(os.path.join(get_logs_dir(), "tunnel.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def find_cloudflared() -> Optional[str]:
    root_dir = get_project_root()
    candidates = [
        os.path.join(root_dir, "bin", "cloudflared.exe"),
        os.path.join(root_dir, "bin", "cloudflared-windows-amd64.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "cloudflared.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "cloudflared-windows-amd64.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def get_tunnel_url() -> Optional[str]:
    return _tunnel_url


def _send_to_discord(url: str, local_ip: str, port: int):
    try:
        from discord_notifier import discord_notifier
        discord_notifier.load_config()
        if not discord_notifier.webhook_url:
            _log("⚠️ [Tunnel] ไม่ได้ส่งลิงก์เข้า Discord: ยังไม่ได้ตั้งค่า Webhook URL")
            return
        if not discord_notifier.enabled:
            _log("⚠️ [Tunnel] ไม่ได้ส่งลิงก์เข้า Discord: ปิดการแจ้งเตือน Discord อยู่")
            return
        if discord_notifier.send_tunnel_started(url, local_ip, port):
            _log("📢 [Tunnel] ส่งลิงก์เข้า Discord เรียบร้อยแล้ว!")
        else:
            _log("❌ [Tunnel] ส่งลิงก์เข้า Discord ไม่สำเร็จ (Webhook ตอบกลับผิดพลาด / เน็ตมีปัญหา)")
    except Exception as e:
        _log(f"❌ [Tunnel] ส่งลิงก์เข้า Discord ไม่สำเร็จ: {e}")


def _monitor(proc: subprocess.Popen, local_ip: str, port: int):
    global _tunnel_url
    started = time.time()
    found = False
    # Keep draining stderr for the whole tunnel lifetime so cloudflared never blocks on a full pipe
    for line in iter(proc.stderr.readline, ""):
        if found:
            continue
        m = URL_PATTERN.search(line)
        if m:
            found = True
            _tunnel_url = m.group(0)
            _log("=" * 65)
            _log("  >>>  ลิงก์สำหรับดูผ่านมือถือ (Cloudflare Tunnel)  <<<")
            _log(f"    {_tunnel_url}  📱")
            _log("  * เปิดดูผ่าน Safari / Chrome บนมือถือได้ทันที (4G/5G/Wi-Fi)")
            _log("=" * 65)
            _send_to_discord(_tunnel_url, local_ip, port)
        elif time.time() - started > URL_WAIT_TIMEOUT:
            found = True
            _log(f"❌ [Tunnel] รอลิงก์ Cloudflare เกิน {int(URL_WAIT_TIMEOUT)} วินาที — ตรวจสอบอินเทอร์เน็ต/ไฟร์วอลล์")
    if not found:
        _log(f"❌ [Tunnel] cloudflared ปิดตัวก่อนได้ลิงก์ (exit code {proc.poll()})")


def start_cloudflared_tunnel(port: int, local_ip: str = "127.0.0.1") -> bool:
    """Start the tunnel once in the background. Returns False if cloudflared could not be started."""
    global _tunnel_process, _tunnel_port, _tunnel_url
    with _lock:
        if _tunnel_process is not None and _tunnel_process.poll() is None:
            if _tunnel_port == port:
                return True
            # Server moved to another port -> old tunnel points nowhere, start a fresh one
            try:
                _tunnel_process.terminate()
            except Exception:
                pass

        exe_path = find_cloudflared()
        if not exe_path:
            _log("⚠️ [Tunnel] ไม่พบ cloudflared.exe ในโฟลเดอร์ bin/ — ข้ามการสร้างลิงก์มือถือ")
            return False

        no_window = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        # Terminate any old orphan cloudflared instances
        for image in ("cloudflared.exe", "cloudflared-windows-amd64.exe"):
            try:
                subprocess.run(["taskkill", "/F", "/IM", image], stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=no_window)
            except Exception:
                pass

        cmd = [exe_path, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
        try:
            # stdin must be explicit: the windowed EXE has no valid console handles to inherit
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=no_window,
            )
        except Exception as e:
            _log(f"❌ [Tunnel] เริ่ม cloudflared ไม่สำเร็จ: {e}")
            return False
        _tunnel_process = proc
        _tunnel_port = port
        _tunnel_url = None

    _log(f"⏳ [Tunnel] กำลังสร้างลิงก์ Cloudflare สำหรับพอร์ต {port}...")
    threading.Thread(target=_monitor, args=(proc, local_ip, port), daemon=True, name="CloudflaredMonitor").start()
    return True


def stop_cloudflared_tunnel():
    global _tunnel_process
    with _lock:
        if _tunnel_process is not None:
            try:
                _tunnel_process.terminate()
            except Exception:
                pass
            _tunnel_process = None


atexit.register(stop_cloudflared_tunnel)
