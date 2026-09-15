import os
import sys

def get_project_root() -> str:
    """
    Get the root directory of the CookieRun Bot project.
    Works seamlessly both in development mode (running from source)
    and in compiled standalone mode (Nuitka / PyInstaller executable).
    """
    # 1. If running as compiled executable
    if getattr(sys, "frozen", False) or "__compiled__" in globals() or hasattr(sys, "__nuitka_version__"):
        return os.path.dirname(os.path.abspath(sys.executable))
    if sys.argv and sys.argv[0] and sys.argv[0].lower().endswith(".exe"):
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    # 2. Check if current file is in src/
    this_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(this_dir).lower() == "src":
        return os.path.dirname(this_dir)

    # 3. Check cwd or parent
    cwd = os.path.abspath(os.getcwd())
    if os.path.isfile(os.path.join(cwd, "frontend", "dist", "index.html")):
        return cwd
    if os.path.basename(cwd).lower() == "src":
        return os.path.dirname(cwd)

    return this_dir

def get_bin_dir() -> str:
    return os.path.join(get_project_root(), "bin")

def get_screenshots_dir() -> str:
    return os.path.join(get_project_root(), "screenshots")

def get_frontend_dist_dir() -> str:
    return os.path.join(get_project_root(), "frontend", "dist")

def get_settings_dir() -> str:
    settings_dir = os.path.join(get_project_root(), "settings")
    os.makedirs(settings_dir, exist_ok=True)
    return settings_dir

def get_macros_dir() -> str:
    macros_dir = os.path.join(get_project_root(), "macros")
    os.makedirs(macros_dir, exist_ok=True)
    return macros_dir

def get_history_dir() -> str:
    history_dir = os.path.join(get_project_root(), "history")
    os.makedirs(history_dir, exist_ok=True)
    return history_dir
