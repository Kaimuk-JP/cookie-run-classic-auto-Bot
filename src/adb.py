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

import json
import os
import random
import shutil
import socket
import subprocess
import time
import gc
try:
    import ctypes
except ImportError:
    ctypes = None
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional

import cv2
import numpy as np

NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

def _run_cmd(cmd_list, **kwargs):
    if "creationflags" not in kwargs and NO_WINDOW_FLAGS:
        kwargs["creationflags"] = NO_WINDOW_FLAGS
    return subprocess.run(cmd_list, **kwargs)


def get_adb_path() -> str:
    """Find adb executable in system PATH or common emulator install locations."""
    if "ADB_PATH" in os.environ and os.path.isfile(os.environ["ADB_PATH"]):
        return os.environ["ADB_PATH"]

    which_adb = shutil.which("adb")
    if which_adb:
        return which_adb

    candidates = [
        os.path.join(os.path.dirname(__file__), "adb.exe"),
        r"C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\adb.exe",
        r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe",
        r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"C:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe",
        r"C:\LDPlayer\LDPlayer9\adb.exe",
        r"C:\Program Files\LDPlayer\LDPlayer9\adb.exe",
        r"C:\leidian\LDPlayer9\adb.exe",
        r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
        r"C:\Program Files\Nox\bin\nox_adb.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    return "adb"


def _format_target(ip_or_serial: str, port: Optional[int | str] = None) -> str:
    """
    Format target device for ADB. Handles both IP:port and direct serials like emulator-5562.
    """
    target = str(ip_or_serial).strip()
    if ":" in target or target.startswith("emulator-"):
        return target
    if port is not None and str(port).strip() and str(port).strip() not in ("0", "None", ""):
        return f"{target}:{port}"
    return target


def ensure_adb_root(device: str) -> bool:
    """
    Ensure the ADB daemon on the target device is running as root (uid=0).
    Many emulators (MuMu 12/15, LDPlayer 9, etc.) start adbd as unprivileged shell (uid=2000)
    over network connections until 'adb root' is explicitly requested.
    """
    adb = get_adb_path()
    target = _format_target(device)
    try:
        res = _run_cmd([adb, "-s", target, "shell", "id"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if "uid=0" in (res.stdout or ""):
            return True

        # Attempt adb root
        _run_cmd([adb, "-s", target, "root"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=4)
        time.sleep(0.8)
        if ":" in str(target):
            _run_cmd([adb, "connect", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        _run_cmd([adb, "-s", target, "wait-for-device"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=4)

        res2 = _run_cmd([adb, "-s", target, "shell", "id"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        return "uid=0" in (res2.stdout or "")
    except Exception:
        return False


_EMU_NAME_CACHE: Dict[str, Tuple[float, str]] = {}
_PORT_PID_CACHE: Tuple[float, Dict[int, int]] = (0.0, {})

def _get_port_pid_map() -> Dict[int, int]:
    """Retrieve mapping of local listening TCP ports to process PIDs on Windows."""
    global _PORT_PID_CACHE
    now = time.time()
    if now - _PORT_PID_CACHE[0] < 5.0:
        return _PORT_PID_CACHE[1]

    mapping = {}
    if os.name != "nt":
        return mapping

    try:
        res = _run_cmd(["netstat", "-ano", "-p", "tcp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        for line in res.stdout.splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    addr, pid = parts[1], parts[4]
                    if ":" in addr:
                        try:
                            port = int(addr.rsplit(":", 1)[1])
                            mapping[port] = int(pid)
                        except ValueError:
                            pass
    except Exception:
        pass

    _PORT_PID_CACHE = (now, mapping)
    return mapping


def resolve_emulator_name(serial: str) -> str:
    """
    Attempt to find the user-defined emulator name (e.g. 'อัพ-3', 'LDPlayer-1')
    supporting MuMu Player, LDPlayer, Nox, and MEmu.
    """
    global _EMU_NAME_CACHE
    now = time.time()
    if serial in _EMU_NAME_CACHE:
        cache_time, cached_name = _EMU_NAME_CACHE[serial]
        if now - cache_time < 30.0 and cached_name:
            return cached_name

    ports = []
    if serial.startswith("emulator-"):
        try:
            p = int(serial.split("-")[1])
            ports = [p, p + 1]
        except Exception:
            pass
    elif ":" in serial:
        try:
            ports = [int(serial.rsplit(":", 1)[1])]
        except Exception:
            pass

    port_map = _get_port_pid_map()
    pids = [port_map[p] for p in ports if p in port_map]

    # 1. MuMu Player (MuMuManager.exe info -v all)
    mumu_candidates = [
        r"C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe",
        r"C:\Program Files\Netease\MuMuPlayer-12.0\nx_main\MuMuManager.exe",
    ]
    for exe in mumu_candidates:
        if os.path.isfile(exe):
            try:
                res = _run_cmd([exe, "info", "-v", "all"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace", timeout=2)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    for k, v in data.items():
                        v_pid = v.get("pid")
                        v_port = v.get("adb_port")
                        if (v_pid and v_pid in pids) or (v_port and v_port in ports):
                            name = v.get("name")
                            if name:
                                _EMU_NAME_CACHE[serial] = (now, name)
                                return name
            except Exception:
                pass

    # 2. LDPlayer (ldconsole.exe list2 / dnconsole.exe list2)
    ld_candidates = [
        r"C:\LDPlayer\LDPlayer9\ldconsole.exe",
        r"C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe",
        r"C:\leidian\LDPlayer9\ldconsole.exe",
        r"C:\LDPlayer\LDPlayer4\ldconsole.exe",
        r"C:\Program Files\dnplayerext2\dnconsole.exe",
    ]
    for exe in ld_candidates:
        if os.path.isfile(exe):
            try:
                res = _run_cmd([exe, "list2"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace", timeout=2)
                for line in res.stdout.splitlines():
                    parts = line.strip().split(",")
                    if len(parts) >= 7:
                        idx_str, title, _, _, _, pid_str, vbox_pid_str = parts[:7]
                        try:
                            l_pid = int(pid_str)
                            l_vbox = int(vbox_pid_str)
                            l_idx = int(idx_str)
                        except ValueError:
                            continue
                        ld_port = 5555 + l_idx * 2
                        if (l_pid in pids) or (l_vbox in pids) or (ld_port in ports):
                            if title:
                                _EMU_NAME_CACHE[serial] = (now, title)
                                return title
            except Exception:
                pass

    # 3. Nox (noxconsole.exe list)
    nox_candidates = [
        r"C:\Program Files\Nox\bin\noxconsole.exe",
        r"C:\Program Files (x86)\Nox\bin\noxconsole.exe",
    ]
    for exe in nox_candidates:
        if os.path.isfile(exe):
            try:
                res = _run_cmd([exe, "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace", timeout=2)
                for line in res.stdout.splitlines():
                    parts = line.strip().split(",")
                    if len(parts) >= 6:
                        title, pid_str = parts[1], parts[5]
                        try:
                            n_pid = int(pid_str)
                        except ValueError:
                            continue
                        if n_pid in pids:
                            if title:
                                _EMU_NAME_CACHE[serial] = (now, title)
                                return title
            except Exception:
                pass

    return ""


def scan_adb_devices() -> List[Dict]:
    """
    Scan for available emulators and devices:
    1. Probe standard emulator ports concurrently and connect.
    2. Query 'adb devices -l' and parse all connected devices.
    3. Return a list of dicts:
       [{"serial": "127.0.0.1:7555", "name": "จอที่ 1 (127.0.0.1:7555) [SM_G9980]", "model": "SM_G9980", "status": "device", "index": 1}, ...]
    """
    adb = get_adb_path()
    attached_serials = set()
    try:
        res = _run_cmd([adb, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        for line in res.stdout.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2:
                attached_serials.add(parts[0])
    except Exception:
        pass

    candidate_ports = [
        5555, 5557, 5559, 5561, 5563, 5565, 5567, 5569, 5571, 5573, 5575,
        7555, 16384, 16385, 16386, 16387, 16388,
        62001, 62025, 62026, 62027,
        21503, 21513, 21523
    ]

    def probe_port(p):
        if f"127.0.0.1:{p}" in attached_serials:
            return None
        # Avoid connecting duplicate socket if emulator-xxxx already corresponds to port p
        for s in attached_serials:
            if s.startswith("emulator-"):
                try:
                    num = int(s.split("-")[1])
                    if p == num + 1 or p == num:
                        return None
                except Exception:
                    pass
        try:
            s = socket.create_connection(("127.0.0.1", p), timeout=0.06)
            s.close()
            return p
        except Exception:
            return None

    try:
        with ThreadPoolExecutor(max_workers=20) as ex:
            open_ports = [p for p in ex.map(probe_port, candidate_ports) if p is not None]

        for p in open_ports:
            _run_cmd([adb, "connect", f"127.0.0.1:{p}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
    except Exception:
        pass

    devices = []
    try:
        out = _run_cmd([adb, "devices", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5).stdout
        lines = out.strip().splitlines()
        raw_devices = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]
                model = ""
                product = ""
                for p in parts[2:]:
                    if p.startswith("model:"):
                        model = p.split("model:")[1]
                    elif p.startswith("product:"):
                        product = p.split("product:")[1]
                raw_devices.append({
                    "serial": serial,
                    "status": status,
                    "model": model or product or "Device",
                })

        # Query Android kernel boot_id for deduplication
        def fetch_boot_id(dev):
            s = dev["serial"]
            if dev["status"] != "device":
                return s, None
            try:
                r = _run_cmd([adb, "-s", s, "shell", "cat", "/proc/sys/kernel/random/boot_id"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.5)
                v = r.stdout.strip()
                if len(v) >= 16 and " " not in v and "\n" not in v:
                    return s, v
            except Exception:
                pass
            return s, None

        boot_ids = {}
        if raw_devices:
            with ThreadPoolExecutor(max_workers=min(10, len(raw_devices))) as ex:
                for s, bid in ex.map(fetch_boot_id, raw_devices):
                    boot_ids[s] = bid

        groups = {}
        for dev in raw_devices:
            s = dev["serial"]
            bid = boot_ids.get(s)
            key = bid if bid else f"unknown_{s}"
            groups.setdefault(key, []).append(dev)

        final_devices = []
        for key, dev_list in groups.items():
            if len(dev_list) == 1:
                final_devices.append(dev_list[0])
            else:
                # Multiple connections sharing the same kernel boot_id (e.g. 127.0.0.1:7555 and emulator-5562)
                emulators = [d for d in dev_list if d["serial"].startswith("emulator-")]
                chosen = emulators[0] if emulators else dev_list[0]
                final_devices.append(chosen)
                # Disconnect redundant IP:port connections
                for d in dev_list:
                    if d["serial"] != chosen["serial"] and ":" in d["serial"]:
                        _run_cmd([adb, "disconnect", d["serial"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)

        idx = 1
        for dev in final_devices:
            serial = dev["serial"]
            status = dev["status"]
            model = dev["model"]
            emu_name = resolve_emulator_name(serial)
            if emu_name:
                display_label = f"{emu_name} ({serial})"
            else:
                display_label = f"จอที่ {idx} ({serial})"
                if model and model != "Device":
                    display_label += f" [{model}]"

            devices.append({
                "serial": serial,
                "name": emu_name or display_label,
                "display_name": display_label,
                "emu_name": emu_name or f"จอที่ {idx}",
                "model": model,
                "status": status,
                "index": idx
            })
            idx += 1
    except Exception as e:
        print(f"Error scanning ADB devices: {e}")

    return devices


def device_check_connection(ip: str, port: int = 5555) -> Tuple[bool, str]:
    """Test connection to the ADB device without raising exceptions."""
    target = _format_target(ip, port)
    adb = get_adb_path()
    try:
        if target.startswith("emulator-"):
            result = _run_cmd([adb, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            for line in result.stdout.splitlines():
                if target in line and "device" in line:
                    return True, f"Device {target} is online"
            return False, f"Device {target} not found or offline"

        result = _run_cmd(
            [adb, "connect", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        out = (result.stdout + result.stderr).strip()
        if "connected" in out.lower() or "already connected" in out.lower():
            return True, f"Connected to {target}"
        return False, out or f"Failed to connect to {target}"
    except Exception as e:
        return False, str(e)


def device_connect(ip: str, port: int = 5555):
    target = _format_target(ip, port)
    adb = get_adb_path()
    if target.startswith("emulator-"):
        result = _run_cmd([adb, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        for line in result.stdout.splitlines():
            if target in line and "device" in line:
                print(f"🔌 Device {target} connected and ready")
                return
        print(f"⚠️ Emulator {target} not listed as ready in adb devices, proceeding anyway")
        return

    result = _run_cmd(
        [adb, "connect", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"🔌 {result.stdout.strip().capitalize()}")
    if "connected" not in result.stdout.lower() and "already connected" not in result.stdout.lower():
        raise Exception(f"❌ Failed to connect to {target}\n{result.stderr.strip()}")


def device_capture_screen(ip: str, port: int = 5555):
    target = _format_target(ip, port)
    adb = get_adb_path()
    for attempt in range(3):
        try:
            result = _run_cmd(
                [adb, "-s", target, "exec-out", "screencap", "-p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=10,
            )
            if result.stdout and len(result.stdout) > 100:
                img = np.frombuffer(result.stdout, dtype=np.uint8)
                decoded = cv2.imdecode(img, cv2.IMREAD_COLOR)
                if decoded is not None:
                    return decoded
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(0.4)
    raise RuntimeError(f"Failed to capture screen from {target}")


def device_tap(ip: str, port: int = 5555, x: int = 0, y: int = 0):
    target = _format_target(ip, port)
    adb = get_adb_path()
    _run_cmd(
        [adb, "-s", target, "shell", "input", "tap", str(x), str(y)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def safe_device_tap(ip: str, port: int = 5555, x: int = 0, y: int = 0):
    jitter_x = x + random.randint(-15, 15)
    jitter_y = y + random.randint(-15, 15)
    target = _format_target(ip, port)
    adb = get_adb_path()
    _run_cmd(
        [adb, "-s", target, "shell", "input", "tap", str(jitter_x), str(jitter_y)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def safe_device_scroll(ip: str, port: int = 5555, x: int = 0, y: int = 0, direction: str = "up", distance: int = 500, duration: int = 300):
    jx = x + random.randint(-15, 15)
    jy = y + random.randint(-15, 15)
    direction_map = {
        "up":    (jx, jy + distance, jx, jy - distance),
        "down":  (jx, jy - distance, jx, jy + distance),
        "left":  (jx + distance, jy, jx - distance, jy),
        "right": (jx - distance, jy, jx + distance, jy),
    }
    if direction not in direction_map:
        raise ValueError(f"Invalid direction '{direction}'. Use: up, down, left, right.")
    x1, y1, x2, y2 = direction_map[direction]
    target = _format_target(ip, port)
    adb = get_adb_path()
    _run_cmd(
        [adb, "-s", target, "shell", "input", "swipe",
         str(x1), str(y1), str(x2), str(y2), str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def safe_device_hold(ip: str, port: int = 5555, x: int = 0, y: int = 0, duration: int = 250):
    """Hold a touch position for duration ms (used for slide/crouch in game)."""
    jx = x + random.randint(-10, 10)
    jy = y + random.randint(-10, 10)
    target = _format_target(ip, port)
    adb = get_adb_path()
    _run_cmd(
        [adb, "-s", target, "shell", "input", "swipe",
         str(jx), str(jy), str(jx), str(jy), str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def device_is_app_running(ip: str, port: int = 5555, package: str = "com.devsisters.crg") -> bool:
    target = _format_target(ip, port)
    adb = get_adb_path()
    result = _run_cmd(
        [adb, "-s", target, "shell", "pidof", package],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(result.stdout.strip())


def device_reset_app(ip: str, port: int = 5555, package: str = "com.devsisters.crg", max_retries: int = 5):
    target = _format_target(ip, port)
    adb = get_adb_path()
    print(f"🔄 Resetting app {package} on device {target}...")
    _run_cmd(
        [adb, "-s", target, "shell", "cmd", "activity", "force-stop", package],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"⏳ Waiting 2 seconds for app {package} to stop...")
    time.sleep(2)

    for attempt in range(1, max_retries + 1):
        print(f"Restarting app {package} on device {target} (attempt {attempt}/{max_retries})...")
        _run_cmd(
            [adb, "-s", target, "shell", "monkey", "-p", package, "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"⏳ Waiting 3 seconds to check if app started...")
        time.sleep(3)

        if device_is_app_running(target, package=package):
            print(f"📊 App {package} is running, verifying stability...")
            stable = True
            for check in range(1, 4):
                time.sleep(1.0)
                if not device_is_app_running(target, package=package):
                    print(f"💥 App {package} crashed during stability check ({check}/3).")
                    stable = False
                    break
                print(f"✅ Stability check {check}/3 passed.")
            if stable:
                print(f"✅ App {package} is stable.")
                return

        print(f"💥 App {package} appears to have crashed after launch.")
        if attempt < max_retries:
            print(f"🔁 Retrying in 2 seconds...")
            time.sleep(2)

    raise Exception(f"❌ Failed to start {package} after {max_retries} attempts.")


def clear_system_memory(
    ip_or_serial: Optional[str] = None,
    port: Optional[int | str] = None,
    package: Optional[str] = "com.devsisters.crg",
    log_func=None
):
    """
    เคลียร์ RAM ทุกๆ รอบที่ทำเสร็จ:
    1. Python Garbage Collection (gc.collect())
    2. Windows Working Set Minimization (คืน RAM ของ Python Process ให้ OS ทันที)
    3. Android / Emulator RAM Cache Clear (sync, drop_caches, am kill-all, am trim-memory)
    """
    freed_parts = []

    # 1. Python GC
    try:
        gc.collect()
        freed_parts.append("Python GC")
    except Exception:
        pass

    # 2. Windows RAM Working Set Trim
    if os.name == "nt" and ctypes is not None:
        try:
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
            psapi.EmptyWorkingSet.restype = ctypes.c_int
            h = kernel32.GetCurrentProcess()
            if psapi.EmptyWorkingSet(h):
                freed_parts.append("Windows RAM")
        except Exception:
            pass

    # 3. Android / Emulator RAM Clean
    if ip_or_serial:
        try:
            target = _format_target(ip_or_serial, port)
            adb = get_adb_path()
            # Sync buffers & drop Linux OS caches (pagecache, dentries, and inodes)
            drop_cmd = "su -c 'sync; echo 3 > /proc/sys/vm/drop_caches' || su 0 'sync; echo 3 > /proc/sys/vm/drop_caches' || sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'"
            _run_cmd([adb, "-s", target, "shell", drop_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)

            # Reclaim memory from cached background processes
            _run_cmd([adb, "-s", target, "shell", "am", "kill-all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)

            # Trim package memory if specified
            if package:
                _run_cmd([adb, "-s", target, "shell", "am", "trim-memory", package, "COMPLETE"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)

            freed_parts.append(f"Device RAM ({target})")
        except Exception:
            pass

    info_str = f"🧹 [เคลียร์ RAM] คืนหน่วยความจำเรียบร้อยแล้ว ({', '.join(freed_parts)})"

    def _safe_print(text):
        try:
            print(text, flush=True)
        except Exception:
            try:
                print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)
            except Exception:
                pass

    if log_func:
        try:
            import inspect
            sig = inspect.signature(log_func)
            if len(sig.parameters) >= 2:
                log_func(info_str, "info")
            else:
                log_func(info_str)
        except Exception:
            try:
                log_func(info_str)
            except Exception:
                _safe_print(info_str)
    else:
        _safe_print(info_str)
