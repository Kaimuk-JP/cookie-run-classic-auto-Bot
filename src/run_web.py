import os
import sys

# Ensure UTF-8 output encoding on Windows
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

import socket
import threading
import time
import webbrowser
import uvicorn

def silence_windows_proactor_connection_lost():
    """Fix Windows asyncio Proactor [WinError 10054] bug when clients disconnect/refresh."""
    if sys.platform != "win32":
        return
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport

        _orig_call_conn_lost = _ProactorBasePipeTransport._call_connection_lost

        def _safe_call_connection_lost(self, exc):
            if self._called_connection_lost:
                return
            try:
                self._protocol.connection_lost(exc)
            finally:
                if hasattr(self, "_sock") and self._sock is not None:
                    if hasattr(self._sock, "shutdown") and self._sock.fileno() != -1:
                        try:
                            self._sock.shutdown(socket.SHUT_RDWR)
                        except (ConnectionResetError, OSError):
                            pass
                    try:
                        self._sock.close()
                    except (ConnectionResetError, OSError):
                        pass
                    self._sock = None
                server = getattr(self, "_server", None)
                if server is not None:
                    try:
                        server._detach(self)
                    except Exception:
                        pass
                    self._server = None
                self._called_connection_lost = True

        _ProactorBasePipeTransport._call_connection_lost = _safe_call_connection_lost
    except Exception:
        pass

silence_windows_proactor_connection_lost()

def find_free_port(start_port=8000, max_attempts=30):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

_tunnel_process = None

def start_cloudflared_tunnel(port, local_ip="127.0.0.1"):
    global _tunnel_process
    from path_utils import get_project_root
    root_dir = get_project_root()
    candidates = [
        os.path.join(root_dir, "bin", "cloudflared.exe"),
        os.path.join(root_dir, "bin", "cloudflared-windows-amd64.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "cloudflared.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "cloudflared-windows-amd64.exe"),
    ]
    exe_path = None
    for p in candidates:
        if os.path.exists(p):
            exe_path = p
            break

    if not exe_path:
        return

    import subprocess
    import re
    import atexit

    # Terminate any old orphan cloudflared instances
    try:
        subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["taskkill", "/F", "/IM", "cloudflared-windows-amd64.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    cmd = [exe_path, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        _tunnel_process = proc
    except Exception:
        return

    def kill_tunnel():
        global _tunnel_process
        if _tunnel_process:
            try:
                _tunnel_process.terminate()
            except Exception:
                pass
    atexit.register(kill_tunnel)

    def monitor_tunnel():
        url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
        url_sent = False
        while True:
            line = proc.stderr.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
                continue

            if not url_sent:
                m = url_pattern.search(line)
                if m:
                    url_sent = True
                    found_url = m.group(0)
                    print("\n" + "=" * 65, flush=True)
                    print("  >>>  ลิงก์สำหรับดูผ่านมือถือ (Cloudflare Tunnel)  <<<", flush=True)
                    print(f"\n    {found_url}  📱\n", flush=True)
                    print("  * เปิดดูผ่าน Safari / Chrome บนมือถือได้ทันที (4G/5G/Wi-Fi)", flush=True)
                    print("=" * 65 + "\n", flush=True)
                    try:
                        from discord_notifier import discord_notifier
                        discord_notifier.send_tunnel_started(found_url, local_ip, port)
                        print("📢 ส่งลิงก์เข้า Discord เรียบร้อยแล้ว!", flush=True)
                    except Exception:
                        pass

    threading.Thread(target=monitor_tunnel, daemon=True).start()

def open_browser(port):
    time.sleep(1.0)
    url = f"http://127.0.0.1:{port}"
    print(f"\n🌐 กำลังเปิดหน้าเว็บ Web Dashboard ที่ {url}...")
    try:
        os.system(f'start {url}')
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass

if __name__ == "__main__":
    port = find_free_port(8000)
    local_ip = get_local_ip()

    print("=" * 65)
    print("🍪 CookieRun Classic Bot - Web Dashboard (All-in-One)")
    print("=" * 65)
    print(f"🚀 คอมพิวเตอร์เครื่องนี้ (PC):     http://127.0.0.1:{port}")
    if local_ip and local_ip != "127.0.0.1":
        print(f"🏠 มือถือ (Wi-Fi บ้านเดียวกัน):    http://{local_ip}:{port}")
    print("=" * 65)

    # Start Cloudflare tunnel automatically in background if available
    start_cloudflared_tunnel(port, local_ip)

    # Launch browser automatically in background
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Run FastAPI app (reload=False to prevent background bots from being killed on file changes)
    try:
        from web_server import app
        uvicorn.run(app, host="0.0.0.0", port=port, reload=False, log_level="warning")
    except Exception as e:
        import traceback
        print("\n" + "=" * 65)
        print("❌ เกิดข้อผิดพลาดในการเริ่มเซิร์ฟเวอร์:")
        traceback.print_exc()
        print("=" * 65)
        try:
            input("\nกด Enter เพื่อปิดหน้าต่าง...")
        except Exception:
            pass

