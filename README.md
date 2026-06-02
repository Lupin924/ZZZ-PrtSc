# ZZZ PrtSc

A high-performance screenshot tool designed for gamers

## About This Tool

This tool was originally developed to better capture exciting moments in the game Zenless Zone Zero. The game is filled with high-speed action and stunning character skills, making it difficult to capture the perfect shot with ordinary screenshot methods.

We aim to provide a simple and fast way for players to easily preserve those unforgettable gaming moments.

## Key Features

- **One-Click Screenshot**: Press the PrintScreen key to quickly capture the current screen
- **Burst Mode**: Capture multiple frames in succession, never miss any exciting moment
- **Controller Support**: Works with screenshot/share buttons on major game controllers (PS5 DualSense, Xbox, Switch Pro)
- **Smart Scanning**: Automatically scans for controllers on startup with 2-second timeout to avoid resource consumption
- **Manual Scan**: Provides a button to manually scan for controllers
- **Status Indication**: Real-time display of controller connection status and operation hints
- **Quiet Operation**: Minimizes to system tray, won't interrupt your gaming experience
- **Persistent Settings**: Settings are automatically saved and restored on restart

## System Requirements

- Windows 10 or Windows 11
- x64 architecture supported

## Usage

### Installation

Simply download the latest executable file and run it, no additional dependencies required.

### Basic Operations

1. **Launch the Program**: After running ZZZ PrtSc, it will run quietly in the system tray
2. **Normal Screenshot**: Press the `PrintScreen` key on your keyboard to capture the current screen
3. **Controller Screenshot**: Press the screenshot/share button on your controller
   - PS5 DualSense: Press Create button
   - Xbox: Press Share button
   - Switch Pro: Press Capture button

### Burst Capture Function

1. Left-click the system tray icon and select "Burst Mode"
2. Set the burst duration and capture frequency
3. Press the screenshot button to start burst capture, the program will automatically complete and save

### Controller Scanning

1. **Auto Scan**: The program automatically scans for connected controllers on startup (max 2 seconds)
2. **Manual Scan**: Click the 🎮 button on the main interface to re-scan for controllers
3. **Status Display**: The main interface shows current controller status
   - 🔍 Scanning for controller...
   - 🎮 No controller detected, use PrintScreen for screenshots
   - 🎮 PS5 DualSense connected, press [Create] to screenshot
   - 🎮 Xbox controller connected, press [Share] to screenshot
   - 🎮 Switch Pro connected, press [Capture] to screenshot

### Settings

- Customizable burst duration (1-10 seconds)
- Adjustable capture frequency (1-10 frames/second)
- Customizable screenshot save folder location

## Notes

- This tool is for personal screenshot and sharing purposes only
- Please comply with the user agreements of related games
- For best results, use in fullscreen mode
- Settings are saved to `%APPDATA%\ZZZ PrtSc\settings.json`

## License

MIT License

This tool is built based on open source software, all third-party libraries follow their respective open source licenses.

***

**May every Proxy catch all the amazing moments of their Agents!**

---

## Technical Details

### Built With

- **Python 3.11** - Programming language
- **CustomTkinter** - Modern GUI framework
- **Win32 API** - System tray and hotkey handling
- **Pillow** - Image processing
- **PyInstaller** - Application packaging

### Project Structure

```
ZZZ PrtSc/
├── src/
│   ├── main.py          # Main application entry
│   ├── hotkey_manager.py # PrintScreen hotkey handling
│   ├── gamepad_manager.py # Controller input handling
│   ├── screenshot_capture.py # Screenshot capture logic
│   ├── settings_manager.py # Settings persistence
│   └── tray_manager.py   # System tray integration
├── main.py              # Application entry point
├── app_icon.png         # Application icon (PNG)
├── app_icon.ico         # Application icon (ICO)
├── make_ico.py          # ICO generation script
├── build.py             # Build script
├── final_build.py       # Alternative build script
├── requirements.txt     # Dependencies
├── LICENSE              # MIT License
├── README.md            # English documentation
└── README_zh.md         # Chinese documentation
```

### Building from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
python build.py

# Or use PyInstaller directly
python -m PyInstaller --name ZZZ_PrtSc --onefile --windowed --icon app_icon.ico main.py
```

### Controller Button Mapping

| Controller | Screenshot Button | Button Index |
|------------|-------------------|--------------|
| PS5 DualSense | Create | 8 |
| Xbox Series | Share | 10 |
| Switch Pro | Capture | 8 |

The application uses Windows native APIs (XInput and WinMM) for controller detection, ensuring minimal overhead and reliable button detection.
