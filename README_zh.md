# ZZZ PrtSc

一款为游戏玩家打造的高性能截图工具

## 关于本工具

这个工具完全由一个不懂代码的游戏玩家开发，100%通过AI协助完成。

### 用途是什么？

我开发这个工具是因为在Windows 11多屏环境下玩绝区零和其他游戏时，需要一个方便快捷的方式来截图主显示器。同时也想试试连拍功能，捕捉游戏中的精彩瞬间。

### 后续计划

- 可能会上传一些实际截图效果来演示工具的使用
- 会找时间测试更多手柄的兼容性（不只是PS5）

### 免责声明

⚠️ **不保证代码质量** - 这是一个非程序员用AI构建的项目  
⚠️ **兼容性有限** - 目前只测试了PS5手柄，其他手柄会后续测试

## 使用截图

以下是使用 ZZZ PrtSc 捕获的游戏画面截图示例：

![截图示例 1](screenshots/screenshot_20260603_230852_973258.png)

![截图示例 2](screenshots/screenshot_20260603_230924_079974.png)

![截图示例 3](screenshots/screenshot_20260603_230924_294566.png)

![截图示例 4](screenshots/screenshot_20260603_230955_326690.png)

![截图示例 5](screenshots/screenshot_20260601_212937_959518.png)

![截图示例 6](screenshots/screenshot_20260601_212938_160704.png)

![截图示例 7](screenshots/screenshot_20260601_212938_593810.png)

![截图示例 8](screenshots/screenshot_20260524_093913_6.png)

![截图示例 9](screenshots/screenshot_20260524_094821_1.png)

![截图示例 10](screenshots/screenshot_20260524_094821_2.png)

## 主要特点

- **一键截图**：按下 PrintScreen 键即可快速捕获当前屏幕
- **连拍模式**：连续捕捉多帧画面，不错过任何精彩瞬间
- **手柄支持**：支持主流游戏手柄的截图按键（PS5 DualSense、Xbox、Switch Pro）
- **智能扫描**：启动时自动扫描手柄，2秒超时限制，避免资源占用
- **手动扫描**：提供扫描手柄按钮，方便后续连接手柄
- **状态提示**：实时显示手柄连接状态和操作提示
- **安静运行**：最小化到系统托盘，不打扰游戏体验
- **设置持久化**：设置会自动保存，重启后自动恢复

## 系统要求

- Windows 10 或 Windows 11
- 支持 x64 架构

## 使用方法

### 安装

直接下载最新版本的可执行文件即可使用，无需安装其他依赖。

### 基本操作

1. **启动程序**：运行 ZZZ PrtSc 后，程序会在系统托盘安静运行
2. **普通截图**：按下键盘上的 `PrintScreen` 键即可截取当前屏幕
3. **手柄截图**：在手柄上按下对应的截图/分享键
   - PS5 DualSense：按 Create 键
   - Xbox：按 Share 键
   - Switch Pro：按 Capture 键

### 连拍功能

1. 左键点击系统托盘图标，选择「连拍模式」
2. 设置连拍时长和拍摄频率
3. 按下截图键开始连拍，程序会自动完成捕获并保存

### 手柄扫描

1. **自动扫描**：程序启动时会自动扫描已连接的手柄（最多等待2秒）
2. **手动扫描**：点击主界面的 🎮 按钮重新扫描手柄连接
3. **状态显示**：主界面会显示当前手柄状态
   - 🔍 正在扫描手柄...
   - 🎮 未检测到手柄，可使用 PrintScreen 键截图
   - 🎮 PS5 DualSense 已连接，按 [Create] 键截图
   - 🎮 Xbox 手柄已连接，按 [Share] 键截图
   - 🎮 Switch Pro 已连接，按 [Capture] 键截图

### 设置

- 可以自定义连拍的时长（1-10秒）
- 可以调整拍摄频率（1-10张/秒）
- 可以设置截图保存的文件夹位置

## 注意事项

- 本工具仅用于个人截图和分享目的
- 请遵守相关游戏的用户协议
- 建议在游戏全屏模式下使用以获得最佳效果
- 设置保存在 `%APPDATA%\ZZZ PrtSc\settings.json`

## 许可证

MIT License

本工具基于开源软件构建，所有使用的第三方库均遵循其各自的开源许可证。

***

**愿每个绳匠都能捕捉到代理人的所有精彩瞬间！**

---

## 技术细节

### 技术栈

- **Python 3.11** - 编程语言
- **CustomTkinter** - 现代GUI框架
- **Win32 API** - 系统托盘和热键处理
- **Pillow** - 图像处理
- **PyInstaller** - 应用程序打包

### 项目结构

```
ZZZ PrtSc/
├── src/
│   ├── main.py          # 主应用入口
│   ├── hotkey_manager.py # PrintScreen热键处理
│   ├── gamepad_manager.py # 手柄输入处理
│   ├── screenshot_capture.py # 截图捕获逻辑
│   ├── settings_manager.py # 设置持久化
│   └── tray_manager.py   # 系统托盘集成
├── main.py              # 应用程序入口点
├── app_icon.png         # 应用图标 (PNG)
├── app_icon.ico         # 应用图标 (ICO)
├── make_ico.py          # ICO生成脚本
├── build.py             # 构建脚本
├── final_build.py       # 备用构建脚本
├── requirements.txt     # 依赖列表
├── LICENSE              # MIT许可证
├── README.md            # 英文文档
└── README_zh.md         # 中文文档
```

### 从源代码构建

```bash
# 安装依赖
pip install -r requirements.txt

# 构建可执行文件
python build.py

# 或直接使用PyInstaller
python -m PyInstaller --name ZZZ_PrtSc --onefile --windowed --icon app_icon.ico main.py
```

### 手柄按钮映射

| 手柄类型 | 截图按钮 | 按钮索引 |
|----------|----------|----------|
| PS5 DualSense | Create | 8 |
| Xbox Series | Share | 10 |
| Switch Pro | Capture | 8 |

应用程序使用 Windows 原生 API（XInput 和 WinMM）进行手柄检测，确保最小的性能开销和可靠的按键检测。
