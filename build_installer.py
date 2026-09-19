"""
Build script to compile CookieRun Bot Windows Installer Setup (.exe)
Uses Inno Setup Compiler (ISCC.exe).
"""

import os
import sys
import shutil
import subprocess

# Ensure UTF-8 console output on Windows
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def find_iscc() -> str:
    # 1. Check PATH
    iscc_path = shutil.which("iscc") or shutil.which("ISCC.exe")
    if iscc_path and os.path.isfile(iscc_path):
        return iscc_path

    # 2. Check known install locations
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p

    return ""

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(root_dir, "dist", "CookieRun_Bot")
    dist_exe = os.path.join(dist_dir, "CookieRunBot.exe")
    iss_file = os.path.join(root_dir, "installer.iss")

    print("=" * 70)
    print("  CookieRun Bot - Windows Installer (.exe) Builder")
    print("=" * 70)

    # 1. Find Inno Setup Compiler
    iscc = find_iscc()
    if not iscc:
        print("\n❌ Error: Inno Setup Compiler (ISCC.exe) not found!")
        print("Please run: winget install JRSoftware.InnoSetup -e")
        sys.exit(1)
    print(f"\n[1/3] Found Inno Setup Compiler: {iscc}")

    # 2. Check distribution folder
    force_rebuild = "--force-rebuild" in sys.argv or "-f" in sys.argv
    if force_rebuild or not os.path.isfile(dist_exe):
        print("\n📦 [2/3] Building native executable with build_exe.py...")
        build_cmd = [sys.executable, "build_exe.py"]
        if "--fast" in sys.argv:
            build_cmd.append("--fast")
        if "--pyinstaller" in sys.argv:
            build_cmd.append("--pyinstaller")
        res = subprocess.run(build_cmd, cwd=root_dir)
        if res.returncode != 0:
            print("❌ Failed to compile executable with build_exe.py!")
            sys.exit(1)
    else:
        print(f"\n✅ [2/3] Distribution folder ready: {dist_dir}")

    # 3. Compile Installer
    print("\n🔨 [3/3] Compiling Setup Installer with Inno Setup...")
    sys.path.insert(0, os.path.join(root_dir, "src"))
    try:
        from version import CURRENT_VERSION
    except Exception:
        CURRENT_VERSION = "2.0.1"

    res = subprocess.run([iscc, f"/DMyAppVersion={CURRENT_VERSION}", iss_file], cwd=root_dir)
    if res.returncode != 0:
        print("\n❌ Error compiling installer!")
        sys.exit(res.returncode)

    installer_output = os.path.join(root_dir, "dist_installer", f"CookieRunBot_Setup_v{CURRENT_VERSION}.exe")
    print("\n" + "=" * 70)
    print("🎉 INSTALLER CREATED SUCCESSFULLY! 🎉")
    print("=" * 70)
    print(f"📦 Installer File: {installer_output}")
    if os.path.isfile(installer_output):
        size_mb = os.path.getsize(installer_output) / (1024 * 1024)
        print(f"📊 File Size:     {size_mb:.2f} MB")
    print("\n✨ Ready to install on any Windows PC or distribute to users!")
    print("=" * 70)

if __name__ == "__main__":
    main()
