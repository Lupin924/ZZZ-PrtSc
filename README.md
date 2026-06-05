# ZZZ PrtSc - 游戏玩家专属截图工具

## 嗨，各位绳匠！

作为一个热爱《绝区零》的游戏玩家，我在多显示器环境下玩游戏时，一直找不到一个好用的截图工具。要么功能太复杂，要么不能用手柄快捷键截图。

于是我决定自己做一个！没错，我完全不懂编程，全靠 AI 帮忙写的代码。如果你也是玩家，希望这个工具能帮到你～

---

## 为什么做这个工具？

- 🎮 在 Windows 11 多屏环境下玩游戏，按 PrintScreen 会截到所有屏幕，太烦了！
- 📸 想捕捉游戏中的精彩瞬间，但普通截图工具反应太慢
- 🎯 想试试连拍模式，不错过任何一个帅气的战斗镜头
- 🎬 想要回放功能，记录下你刚刚打出的完美操作
- 🔌 PS5 手柄的 Create 键不用太浪费了！

---

## 工具特色

- **一键截图**：按键盘的 PrintScreen 键就能快速截图（BitBlt 硬件加速）
- **手柄支持**：PS5 / Xbox / Switch Pro 手柄都能用！
  - PS5 DualSense：按 Create 键
  - Xbox：按 Share（View/Back）键
  - Switch Pro：按 Capture 键
- **连拍模式**：连续捕捉多帧画面，精彩瞬间一个都跑不了
- **🎬 即时回放（新功能）**：基于循环缓冲区，按截图键即可将最近 N 秒的画面保存为视频
  - 支持自定义回放时长（1-60秒）和帧率（1-60 FPS）
  - 使用 ffmpeg 进行视频编码，输出 MP4 格式
  - DXcam 高性能屏幕捕获（可选，自动回退到 PIL）
- **安静运行**：启动后自动最小化到系统托盘，不打扰游戏
- **智能检测**：启动时自动检测手柄，不用手动设置
- **智能通知**：截图/连拍/回放完成后弹出通知，不重叠、不打扰

---

## 怎么用？

### 下载安装
1. 去 [Releases](https://github.com/Lupin924/ZZZ-PrtSc/releases) 页面下载最新版本
2. 解压后直接运行 `ZZZ_PrtSc.exe`，不用安装

### 基本操作
1. 运行程序后，右下角会出现一个小图标
2. 按 PrintScreen 键或者手柄上的截图键就能截图
3. 截图会自动保存到默认文件夹（可以在设置里改）

### 连拍模式
1. 点击「连拍模式」按钮或右键托盘图标选择
2. 在设置中调整连拍时长（1-10秒）和每秒拍几张（1-10张）
3. 按截图键开始，程序会自动连拍并保存

### 即时回放模式
1. 点击「🎬 即时回放」按钮或右键托盘图标选择
2. 在设置中调整回放时长（1-60秒）和帧率（1-60 FPS）
3. 按截图键将最近 N 秒的画面保存为视频
4. 需要安装 ffmpeg 才能使用视频编码

### 手柄连接
- 启动时会自动检测手柄，最多等2秒
- 如果没检测到，可以点击界面上的手柄图标重新扫描

---

## 截图示例

### 软件界面

这是工具的主界面，很简洁：

![主界面](screenshots/main_interface.jpg)

连拍模式的设置窗口：

![设置](screenshots/burst_settings.jpg)

### 游戏画面

下面这些都是用这个工具截的游戏画面：

![游戏截图1](screenshots/screenshot_20260603_230852_973258.png)

![游戏截图2](screenshots/screenshot_20260603_230924_079974.png)

![游戏截图3](screenshots/screenshot_20260603_230924_294566.png)

![游戏截图4](screenshots/screenshot_20260603_230955_326690.png)

![游戏截图5](screenshots/screenshot_20260601_212937_959518.png)

![游戏截图6](screenshots/screenshot_20260601_212938_160704.png)

![游戏截图7](screenshots/screenshot_20260601_212938_593810.png)

![游戏截图8](screenshots/screenshot_20260524_093913_6.png)

![游戏截图9](screenshots/screenshot_20260524_094821_1.png)

![游戏截图10](screenshots/screenshot_20260524_094821_2.png)

![游戏截图11](screenshots/screenshot_20260524_094822_4.png)

![游戏截图12](screenshots/screenshot_20260524_094935_1.png)

![游戏截图13](screenshots/screenshot_20260524_095812_2.png)

![游戏截图14](screenshots/screenshot_20260524_103124_4.png)

---

## 技术栈

- **UI 框架**：CustomTkinter
- **截图引擎**：Windows GDI BitBlt（硬件加速）
- **热键管理**：低级键盘钩子（WH_KEYBOARD_LL）
- **手柄检测**：XInput / winmm 原生 API
- **即时回放**：循环缓冲区 + ffmpeg 编码（可选 DXcam 加速）
- **系统托盘**：Win32 Shell_NotifyIcon 原生实现
- **打包工具**：PyInstaller
- **代码质量**：经过完整代码审查，修复了 10 个潜在问题，包括 Xbox 手柄按键映射、设置持久化、线程安全、通知弹窗、资源清理等

---

## 更新日志

### v1.0.3（最新）
- 🎬 新增即时回放模式（循环缓冲区 + ffmpeg 视频编码）
- 🔧 Xbox 手柄 Share 按键映射修正（从错误的 RB 按钮改为正确的 Share/View 按钮）
- 🔧 修复设置持久化问题：停止/关闭状态/模式切换时正确保存所有设置
- 🔧 修复通知弹窗重叠问题：新通知自动销毁旧通知
- 🔧 打开目录按钮智能切换：根据当前模式打开连拍/回放/截图目录
- 🔧 设置管理器增加线程安全锁
- 🔧 修复 `__del__` 析构函数在 GC 线程中的潜在崩溃风险
- 🔧 DXcam 从 PyInstaller 构建中排除（按需安装的可选依赖）
- 🔧 多处裸 `except:` 改为 `except Exception:`
- 📦 优化构建体积，排除不需要的模块（numpy、pyreadline3 等）

---

## 注意事项

- 目前只在 Windows 10/11 上测试过
- 手柄已测试 PS5 DualSense 和 Xbox Series 手柄
- 即时回放功能需要安装 ffmpeg（[下载](https://ffmpeg.org/download.html)）
- 设置文件保存在 `%APPDATA%\ZZZ PrtSc\settings.json`

---

## 免责声明

⚠️ **代码质量不保证**（毕竟我不会编程）
⚠️ **如果出问题了我可能修不了，但欢迎提建议！**

---

**愿每个绳匠都能捕捉到代理人的所有精彩瞬间！** 📸✨

---

## English Version

Click [here](README_en.md) to view the English version of this README.