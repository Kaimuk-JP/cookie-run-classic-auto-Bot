import os
import sys
import re
import subprocess
import time

# Ensure UTF-8 output
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def find_cloudflared_path():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(root_dir, "bin", "cloudflared.exe"),
        os.path.join(root_dir, "bin", "cloudflared-windows-amd64.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "cloudflared-windows-amd64.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "cloudflared.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return "cloudflared"

def detect_bot_port():
    import socket
    for port in [8000, 8001, 8002, 8003]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                return port
    return 8000

def main():
    exe_path = find_cloudflared_path()
    if not os.path.exists(exe_path) and exe_path == "cloudflared":
        print("[!] ไม่พบไฟล์ cloudflared.exe ในโฟลเดอร์ bin/", flush=True)
        print("กรุณาดาวน์โหลดหรือตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์ bin/ หรือ Downloads", flush=True)
        input("\nกด Enter เพื่อออก...")
        return

    target_port = detect_bot_port()

    print("=" * 65, flush=True)
    print("   CookieRun Classic Bot - Mobile Cloudflare Tunnel", flush=True)
    print("=" * 65, flush=True)
    print(f"[*] พบเซิร์ฟเวอร์บอททำงานอยู่ที่พอร์ต: {target_port}", flush=True)
    print("[*] กำลังเชื่อมต่อ Cloudflare Tunnel... กรุณารอสักครู่ (ประมาณ 3-5 วินาที)", flush=True)
    print("[*] หมายเหตุ: ต้องเปิด START_BOT.bat ไว้ด้วยเพื่อให้บอททำงาน", flush=True)
    print("=" * 65, flush=True)

    cmd = [exe_path, "tunnel", "--url", f"http://localhost:{target_port}"]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
    except Exception as e:
        print(f"[!] ไม่สามารถเริ่ม cloudflared ได้: {e}", flush=True)
        input("\nกด Enter เพื่อออก...")
        return

    tunnel_url = None
    # Cloudflared outputs tunnel logs to stderr
    start_time = time.time()
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

    while time.time() - start_time < 30:
        line = proc.stderr.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                break

    if tunnel_url:
        print("\n" + "=" * 65, flush=True)
        print("  >>> เชื่อมต่อสำเร็จแล้ว! ลิงก์สำหรับเปิดดูผ่านมือถือ <<<", flush=True)
        print(f"\n   >>  {tunnel_url}  <<\n", flush=True)
        print("  * นำลิงก์ด้านบนไปเปิดใน Safari / Chrome บนมือถือได้ทันที (ใช้ได้ทั้ง 4G/5G/Wi-Fi)", flush=True)
        print("  * เปิดหน้าต่างนี้ทิ้งไว้เพื่อให้ลิงก์ยังคงใช้งานได้", flush=True)
        print("=" * 65 + "\n", flush=True)
    else:
        print("\n[!] ไม่สามารถดึงลิงก์ Tunnel อัตโนมัติได้ แต่ระบบกำลังทำงาน...", flush=True)
        print("ดูข้อความด้านล่างเพื่อหาลิงก์ที่ลงท้ายด้วย .trycloudflare.com:", flush=True)
        print("-" * 65, flush=True)

    # Stream remaining logs or keep alive
    try:
        while True:
            line = proc.stderr.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                m = url_pattern.search(line)
                if m and not tunnel_url:
                    tunnel_url = m.group(0)
                    print(f"\n🔗 ลิงก์ของคุณคือ: {tunnel_url}\n")
    except KeyboardInterrupt:
        pass
    finally:
        try:
            proc.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()
