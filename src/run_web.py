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

import argparse
import socket
import threading
import time
import webbrowser
import uvicorn

def find_free_port(start_port=8000, max_attempts=30):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def open_browser(port, device=None):
    time.sleep(1.0)
    dev_query = f"?device={device}" if device else ""
    url = f"http://127.0.0.1:{port}/{dev_query}"
    print(f"\n🌐 กำลังเปิดหน้าเว็บ Web Dashboard ที่ {url}...")
    try:
        os.system(f'start {url}')
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CookieRun Classic Bot - Web Dashboard")
    parser.add_argument("--port", type=int, default=None, help="Port to run Web Dashboard on (default: auto-detected 8000+)")
    parser.add_argument("--device", type=str, default=None, help="Target device serial (e.g. 127.0.0.1:16384)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    port = args.port if args.port else find_free_port(8000)
    device = args.device.strip() if args.device else None
    if device:
        os.environ["DEFAULT_DEVICE_SERIAL"] = device

    print("=" * 60)
    print("🍪 CookieRun Classic Bot - Web Dashboard")
    print("=" * 60)
    print(f"🚀 เซิร์ฟเวอร์เริ่มทำงานแล้วที่: http://127.0.0.1:{port}")
    if device:
        print(f"📱 ผูกการควบคุมจอหลักไว้ที่: {device}")
    print(f"💡 สามารถเปิดดูบนมือถือผ่าน Wi-Fi เดียวกันได้")
    print("=" * 60)

    # Launch browser automatically in background
    if not args.no_browser:
        threading.Thread(target=open_browser, args=(port, device), daemon=True).start()

    # Run FastAPI app (reload=False to prevent background bots from being killed on file changes)
    uvicorn.run("web_server:app", host="0.0.0.0", port=port, reload=False, log_level="warning")

