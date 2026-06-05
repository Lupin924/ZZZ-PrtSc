# ZZZ PrtSc - Gamer's Screenshot Tool

## Hey Proxies!

As a big fan of Zenless Zone Zero, I struggled finding a good screenshot tool for my multi-monitor Windows 11 setup. Most tools were too complicated or didn't support controller shortcuts.

So I decided to make my own! Yep, I know nothing about coding - this was 100% built with AI help. If you're also a gamer, hope this tool helps you capture those epic moments!

---

## Why I Built This

- 🎮 Pressing PrintScreen on multi-monitor setup captures ALL screens - so annoying!
- 📸 Regular screenshot tools are too slow for fast-paced gaming action
- 🎯 Wanted burst capture mode to catch those perfect combat moments
- 🎬 Wanted replay mode to save your sick gameplay clips on demand
- 🔌 PS5 DualSense Create button was going to waste!

---

## Features

- **One-Click Screenshot**: Press PrintScreen key for instant screenshot (BitBlt hardware acceleration)
- **Controller Support**: Works with PS5 / Xbox / Switch Pro controllers!
  - PS5 DualSense: Press Create button
  - Xbox: Press Share (View/Back) button
  - Switch Pro: Press Capture button
- **Burst Mode**: Capture multiple frames in succession, never miss a moment
- **🎬 Instant Replay (NEW)**: Circular buffer captures your recent gameplay, saves as video on key press
  - Customizable duration (1-60s) and FPS (1-60)
  - ffmpeg video encoding, MP4 output
  - Optional DXcam high-performance screen capture with PIL fallback
- **Quiet Operation**: Minimizes to system tray, won't interrupt your game
- **Smart Detection**: Automatically detects controllers on startup
- **Smart Notifications**: Non-overlapping toast notifications for screenshot/burst/replay completion

---

## How to Use

### Download & Install
1. Go to the [Releases](https://github.com/Lupin924/ZZZ-PrtSc/releases) page
2. Download the latest version and run `ZZZ_PrtSc.exe` - no installation needed!

### Basic Operation
1. Launch the program - you'll see a small icon in the system tray
2. Press PrintScreen or your controller's screenshot button
3. Screenshots are saved automatically (you can change the folder in settings)

### Burst Mode
1. Click "Burst Mode" button or select from tray menu
2. Set duration (1-10 seconds) and frames per second (1-10) in settings
3. Press the screenshot button to start - it will auto-save all frames

### Instant Replay Mode
1. Click "🎬 Instant Replay" button or select from tray menu
2. Set replay duration (1-60s) and FPS (1-60) in settings
3. Press screenshot button to save the last N seconds as video
4. Requires ffmpeg for video encoding

### Controller Connection
- Auto-detects controllers on startup (max 2 second wait)
- Click the controller icon in the main window to re-scan

---

## Screenshots

### Application Interface

Simple and clean main interface:

![Main Interface](screenshots/main_interface.jpg)

Settings window:

![Settings](screenshots/burst_settings.jpg)

### In-Game Examples

Here are some actual in-game screenshots captured with ZZZ PrtSc:

![Game Screenshot 1](screenshots/screenshot_20260603_230852_973258.png)

![Game Screenshot 2](screenshots/screenshot_20260603_230924_079974.png)

![Game Screenshot 3](screenshots/screenshot_20260603_230924_294566.png)

![Game Screenshot 4](screenshots/screenshot_20260603_230955_326690.png)

![Game Screenshot 5](screenshots/screenshot_20260601_212937_959518.png)

![Game Screenshot 6](screenshots/screenshot_20260601_212938_160704.png)

![Game Screenshot 7](screenshots/screenshot_20260601_212938_593810.png)

![Game Screenshot 8](screenshots/screenshot_20260524_093913_6.png)

![Game Screenshot 9](screenshots/screenshot_20260524_094821_1.png)

![Game Screenshot 10](screenshots/screenshot_20260524_094821_2.png)

![Game Screenshot 11](screenshots/screenshot_20260524_094822_4.png)

![Game Screenshot 12](screenshots/screenshot_20260524_094935_1.png)

![Game Screenshot 13](screenshots/screenshot_20260524_095812_2.png)

![Game Screenshot 14](screenshots/screenshot_20260524_103124_4.png)

---

## Tech Stack

- **UI Framework**: CustomTkinter
- **Capture Engine**: Windows GDI BitBlt (hardware accelerated)
- **Hotkey Management**: Low-level keyboard hook (WH_KEYBOARD_LL)
- **Controller Detection**: XInput / winmm native API
- **Instant Replay**: Circular buffer + ffmpeg encoding (optional DXcam acceleration)
- **System Tray**: Win32 Shell_NotifyIcon native implementation
- **Packaging**: PyInstaller
- **Code Quality**: Full code review completed, 10 issues fixed including Xbox controller mapping, settings persistence, thread safety, notification overlap, resource cleanup, etc.

---

## Changelog

### v1.0.3 (Latest)
- 🎬 New: Instant Replay Mode (circular buffer + ffmpeg video encoding)
- 🔧 Fixed: Xbox controller Share button mapping (corrected from wrong RB to proper Share/View button)
- 🔧 Fixed: Settings persistence - all modes properly saved on stop/close/toggle
- 🔧 Fixed: Notification window overlap - new toast auto-destroys old one
- 🔧 Fixed: Smart folder button - opens correct directory based on current mode
- 🔧 Fixed: Settings manager thread safety with proper lock
- 🔧 Fixed: `__del__` destructor crash risk during GC
- 🔧 Fixed: DXcam excluded from PyInstaller build (optional dependency)
- 🔧 Fixed: Multiple bare `except:` replaced with `except Exception:`
- 📦 Optimized build size by excluding unnecessary modules (numpy, pyreadline3, etc.)

---

## Notes

- Only tested on Windows 10/11
- Tested with PS5 DualSense and Xbox Series controllers
- Instant replay requires ffmpeg ([download](https://ffmpeg.org/download.html))
- Settings saved to `%APPDATA%\ZZZ PrtSc\settings.json`

---

## Disclaimer

⚠️ **Code quality not guaranteed** - I don't know how to code!
⚠️ **May not fix bugs** - but feel free to suggest improvements!

---

**May every Proxy capture all the amazing moments of their Agents!** 📸✨

---

## 中文版本

Click [here](README.md) to view the Chinese version.