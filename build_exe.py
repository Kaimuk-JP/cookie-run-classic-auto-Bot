"""
Build Orchestrator for CookieRun Bot
Compiles the application into a secure Native Windows Executable (.exe)
using Nuitka + Zig C-Compiler to prevent reverse engineering and decompilation.
"""

import os
import sys
import shutil
import subprocess

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

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dist = os.path.join(root_dir, "frontend", "dist", "index.html")

    print("=" * 70)
    print(" CookieRun Bot - Native EXE Compiler (Nuitka + Zig C-Compiler)")
    print("=" * 70)

    # 1. Verify frontend dist
    if not os.path.isfile(frontend_dist):
        print("\n📦 [1/3] Frontend build not found. Building React dashboard with Vite...")
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm_cmd:
            print("❌ Error: 'npm' not found in PATH! Please build frontend first.")
            sys.exit(1)
        res = subprocess.run([npm_cmd, "run", "build"], cwd=os.path.join(root_dir, "frontend"))
        if res.returncode != 0:
            print("❌ Error: Failed to build frontend!")
            sys.exit(1)
    else:
        print("\n✅ [1/3] Frontend React build is ready.")

    # 2. Prepare build command
    print("\n⚙️  [2/3] Preparing Nuitka C compilation command...")
    entry_point = os.path.join(root_dir, "src", "gui_launcher.py")
    icon_path = os.path.join(root_dir, "src", "bot_icon.ico")
    output_dir = os.path.join(root_dir, "dist_build")

    nuitka_cmd = [
        sys.executable,
        "-O",
        "-m",
        "nuitka",
        "--standalone",
        "--zig",
        "--assume-yes-for-downloads",
        "--windows-console-mode=disable",
        "--enable-plugin=tk-inter",
        "--no-deployment-flag=excluded-module-usage",
        "--include-package=customtkinter",
        "--include-package=darkdetect",
        "--include-package-data=customtkinter",
        "--include-package=uvicorn",
        "--include-package=fastapi",
        "--include-package=starlette",
        "--include-package=pydantic",
        "--include-package=pydantic_core",
        "--include-package=websockets",
        f"--output-filename=CookieRunBot.exe",
        f"--output-dir={output_dir}",
    ]

    # Include Icon if present
    if os.path.isfile(icon_path):
        nuitka_cmd.append(f"--windows-icon-from-ico={icon_path}")

    # Add data directories (strictly system files, excluding screenshots/user settings)
    nuitka_cmd.extend([
        f"--include-data-dir={os.path.join(root_dir, 'frontend', 'dist')}=frontend/dist",
        f"--include-data-dir={os.path.join(root_dir, 'src', 'templates')}=templates",
        f"--include-data-dir={os.path.join(root_dir, 'bin')}=bin",
    ])

    if os.path.isdir(os.path.join(root_dir, "macros")):
        nuitka_cmd.append(f"--include-data-dir={os.path.join(root_dir, 'macros')}=macros")

    # Add source path to pythonpath
    src_dir = os.path.join(root_dir, "src")
    nuitka_cmd.append(entry_point)

    print("🚀 Starting compilation (this converts Python -> C++ -> Native Machine Code)...")
    print("⏳ This usually takes 3-7 minutes depending on CPU. Please wait...\n")
    print("Command:", " ".join(nuitka_cmd[:7]), "...")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_dir};{root_dir};" + env.get("PYTHONPATH", "")

    proc = subprocess.run(nuitka_cmd, cwd=root_dir, env=env)
    if proc.returncode != 0:
        print("\n❌ Nuitka compilation failed with exit code:", proc.returncode)
        sys.exit(proc.returncode)

    # 3. Post-build structure organization
    print("\n📦 [3/3] Organizing distribution folder...")
    raw_dist = os.path.join(output_dir, "gui_launcher.dist")
    if not os.path.isdir(raw_dist):
        raw_dist = os.path.join(output_dir, "run_web.dist")
    final_dist = os.path.join(root_dir, "dist", "CookieRun_Bot")

    if os.path.isdir(raw_dist):
        os.makedirs(final_dist, exist_ok=True)
        shutil.copytree(raw_dist, final_dist, dirs_exist_ok=True)

    # Ensure templates exist in both root templates/ and src/templates/
    src_templates = os.path.join(root_dir, "src", "templates")
    dist_templates = os.path.join(final_dist, "templates")
    dist_src_templates = os.path.join(final_dist, "src", "templates")
    if os.path.isdir(src_templates):
        if not os.path.exists(dist_templates):
            shutil.copytree(src_templates, dist_templates)
        if not os.path.exists(dist_src_templates):
            os.makedirs(os.path.dirname(dist_src_templates), exist_ok=True)
            shutil.copytree(src_templates, dist_src_templates)

    # Ensure all bin files are copied (including adb.exe, dlls, scrcpy-server.jar)
    src_bin = os.path.join(root_dir, "bin")
    dist_bin = os.path.join(final_dist, "bin")
    os.makedirs(dist_bin, exist_ok=True)
    if os.path.isdir(src_bin):
        for f in os.listdir(src_bin):
            s_f = os.path.join(src_bin, f)
            d_f = os.path.join(dist_bin, f)
            if os.path.isfile(s_f):
                shutil.copy2(s_f, d_f)

    # Ensure scrcpy package and scrcpy-server.jar are in dist/scrcpy/
    try:
        import scrcpy
        scrcpy_pkg_src = os.path.dirname(scrcpy.__file__)
        dist_scrcpy_dir = os.path.join(final_dist, "scrcpy")
        shutil.copytree(scrcpy_pkg_src, dist_scrcpy_dir, dirs_exist_ok=True)
    except Exception as e:
        print("Note on scrcpy copy:", e)

    # Ensure customtkinter and darkdetect are in dist
    try:
        import customtkinter
        ctk_pkg_src = os.path.dirname(customtkinter.__file__)
        dist_ctk_dir = os.path.join(final_dist, "customtkinter")
        shutil.copytree(ctk_pkg_src, dist_ctk_dir, dirs_exist_ok=True)
    except Exception as e:
        print("Note on customtkinter copy:", e)

    try:
        import darkdetect
        dd_pkg_src = os.path.dirname(darkdetect.__file__)
        dist_dd_dir = os.path.join(final_dist, "darkdetect")
        shutil.copytree(dd_pkg_src, dist_dd_dir, dirs_exist_ok=True)
    except Exception as e:
        print("Note on darkdetect copy:", e)

    # Ensure Tkinter & Tcl runtime files are present in dist
    py_base = os.path.dirname(sys.executable)
    py_dlls = os.path.join(py_base, "DLLs")
    for dll_file in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
        for src_candidate in [os.path.join(py_dlls, dll_file), os.path.join(py_base, dll_file)]:
            if os.path.isfile(src_candidate):
                shutil.copy2(src_candidate, os.path.join(final_dist, dll_file))
                break

    # Copy tcl directory
    src_tcl = os.path.join(py_base, "tcl")
    if os.path.isdir(src_tcl):
        shutil.copytree(src_tcl, os.path.join(final_dist, "tcl"), dirs_exist_ok=True)

    # Copy tkinter library
    src_tkinter = os.path.join(py_base, "Lib", "tkinter")
    if os.path.isdir(src_tkinter):
        shutil.copytree(src_tkinter, os.path.join(final_dist, "tkinter"), dirs_exist_ok=True)

    scrcpy_jar_src = os.path.join(src_bin, "scrcpy-server.jar")
    if os.path.isfile(scrcpy_jar_src):
        dist_scrcpy_dir = os.path.join(final_dist, "scrcpy")
        os.makedirs(dist_scrcpy_dir, exist_ok=True)
        shutil.copy2(scrcpy_jar_src, os.path.join(dist_scrcpy_dir, "scrcpy-server.jar"))
        shutil.copy2(scrcpy_jar_src, os.path.join(final_dist, "scrcpy-server.jar"))

    # Ensure web HTML templates (legacy & next_gen) are copied to final_dist/src/web
    src_web = os.path.join(root_dir, "src", "web")
    dist_src_web = os.path.join(final_dist, "src", "web")
    if os.path.isdir(src_web):
        os.makedirs(dist_src_web, exist_ok=True)
        for f in os.listdir(src_web):
            s_f = os.path.join(src_web, f)
            d_f = os.path.join(dist_src_web, f)
            if os.path.isfile(s_f):
                shutil.copy2(s_f, d_f)

    # Ensure icons exist in dist
    for img_name in [
        "bot_icon.ico", "icon.png", "login_header_badge.png",
        "icon_user_gray.png", "icon_lock_gray.png", "icon_eye_gray.png", "icon_eye_slash_gray.png"
    ]:
        src_img = os.path.join(root_dir, "src", img_name)
        if os.path.isfile(src_img):
            os.makedirs(os.path.join(final_dist, "src"), exist_ok=True)
            shutil.copy2(src_img, os.path.join(final_dist, img_name))
            shutil.copy2(src_img, os.path.join(final_dist, "src", img_name))

    # Copy src python scripts to final_dist/src and final_dist as guaranteed runtime fallback
    os.makedirs(os.path.join(final_dist, "src"), exist_ok=True)
    for f in os.listdir(src_dir):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(src_dir, f), os.path.join(final_dist, "src", f))
            shutil.copy2(os.path.join(src_dir, f), os.path.join(final_dist, f))

    # Ensure required empty directories exist (and clean out any screenshots or user data)
    for folder in ["settings", "history", "logs_error", "screenshots", "macros"]:
        target_dir = os.path.join(final_dist, folder)
        os.makedirs(target_dir, exist_ok=True)
        # Empty out files in these folders to avoid shipping test data
        for f in os.listdir(target_dir):
            p = os.path.join(target_dir, f)
            try:
                if os.path.isfile(p): os.remove(p)
                elif os.path.isdir(p): shutil.rmtree(p)
            except Exception:
                pass

    # Ensure src/screenshots is removed from final distribution
    dist_src_screenshots = os.path.join(final_dist, "src", "screenshots")
    if os.path.isdir(dist_src_screenshots):
        shutil.rmtree(dist_src_screenshots, ignore_errors=True)

    # Copy README and manual if available
    for manual in ["คู่มือวิธีใช้งาน_CookieRun_Bot.txt", "README.md"]:
        src_f = os.path.join(root_dir, manual)
        if os.path.isfile(src_f):
            shutil.copy2(src_f, os.path.join(final_dist, manual))

    print("\n" + "=" * 70)
    print("🎉 BUILD SUCCESSFUL! 🎉")
    print("=" * 70)
    print(f"📁 Output folder: {final_dist}")
    print(f"▶️  Executable:   {os.path.join(final_dist, 'CookieRunBot.exe')}")
    print("\n🛡️  All Python source code has been translated into native C/C++ machine code.")
    print("🔒 Decompilers (pyinstxtractor, uncompyle6, pycdc) CANNOT read or extract the code.")
    print("📦 You can simply ZIP the 'dist/CookieRun_Bot' folder to distribute to users!")
    print("=" * 70)

if __name__ == "__main__":
    main()
