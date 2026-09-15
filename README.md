# cookie-run-classic-auto-Bot

CookieRun Classic Automated Bot with Modern Web Dashboard, Auto Friend Cleaner (Level 1), Auto Heart Farmer, and Real-Time ADB Screen Streaming.

## ✨ Features
- 🚀 **Full Gameplay Loop Automation:** Auto-play, stage detection (OpenCV template matching), mystery box extraction, score/coin/EXP logging.
- 🧹 **Level 1 Friend Cleaner:** Automatically cleans inactive Level 1 friends with automatic memory (RAM) trimming.
- 💖 **Heart Farmer (Fast Flow):** Automated high-speed account cycling, tutorial bypass, and heart sending.
- 🌐 **Modern Web Dashboard:** Real-time web control, emulator screen mirror, live log stream, and multi-device management via FastAPI & WebSockets.
- ⚡ **Auto RAM Cleaner:** Automatic 3-level memory clearing (Python GC + Windows Working Set + Android cache drop) after every completed round.
- 🔔 **Discord Webhook Notifications:** Rich summary embeds for rounds, rewards, and mystery boxes.

## 🛠️ Requirements
- Python 3.10+
- ADB (Android Debug Bridge)
- Android Emulator (LDPlayer, MuMu Player, Nox, BlueStacks) set to **1280×720** resolution

## 📦 Installation
Run `INSTALL.bat` or install requirements manually:
```bash
pip install -r src/requirements.txt
```

## 🎮 How to Run

### Method 1: Desktop GUI Launcher (Recommended)
Double-click `START_GUI.bat` to launch the Sweet Bakery Desktop Launcher with automatic emulator discovery, single-instance protection, and instant dashboard opening.

### Method 2: Command-Line / Direct Web Server
Double-click `START_BOT.bat` or run:
```bash
python src/run_web.py
```
Open your browser at `http://localhost:8000` to access the Web Dashboard.

## 📦 Build Installer (.exe)
Run `BUILD_INSTALLER.bat` to compile the application into a standalone native Windows Installer (`dist_installer/CookieRunBot_Setup_v2.0.0.exe`) that runs on any PC without requiring Python.
