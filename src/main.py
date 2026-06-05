#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
from pathlib import Path

import customtkinter as ctk
from PIL import Image

# CTkMessagebox 兼容性处理：新版 customtkinter 已分离为独立包
try:
    from CTkMessagebox import CTkMessagebox
except ImportError:
    CTkMessagebox = getattr(ctk, 'CTkMessagebox', None)
    if CTkMessagebox is None:
        from tkinter import messagebox
        CTkMessagebox = messagebox

from .hotkey_manager import HotkeyManager
from .screenshot_capture import ScreenshotCapture
from .settings_manager import SettingsManager, SettingsDialog
from .gamepad_manager import GamepadManager
from .tray_manager import Win32TrayManager
from .instant_replay import InstantReplay


class SignalBridge:
    def __init__(self):
        self.screenshot_callbacks = []
        self.exit_callbacks = []

    def connect_screenshot(self, callback):
        self.screenshot_callbacks.append(callback)

    def connect_exit(self, callback):
        self.exit_callbacks.append(callback)

    def emit_screenshot(self):
        for callback in self.screenshot_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"执行截图回调失败: {e}")

    def emit_exit(self):
        for callback in self.exit_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"执行退出回调失败: {e}")


class MainWindow:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.settings = SettingsManager()
        self.signal_bridge = SignalBridge()
        self.hotkey_manager = None
        self.screenshot_capture = ScreenshotCapture()
        self.gamepad_manager = None
        self.instant_replay = None
        self.is_running = True
        self.is_burst_mode = False
        self.is_replay_mode = False
        self.root = ctk.CTk()
        self._tray = None
        self._main_frame = None
        self._tooltip_frame = None
        self._tooltip_label = None
        self._notification_window = None

        self.burst_duration = self.settings.get("burst_duration", 3)
        self.burst_fps = self.settings.get("burst_fps", 3)
        self.burst_save_folder = self.settings.get(
            "burst_save_folder",
            str(Path.home() / "Pictures" / "Screenshots" / "Burst")
        )
        
        self.replay_duration = self.settings.get("replay_duration", 5)
        self.replay_fps = self.settings.get("replay_fps", 30)
        self.replay_save_folder = self.settings.get(
            "replay_save_folder",
            str(Path.home() / "Pictures" / "Screenshots" / "Replay")
        )

        self._init_ui()
        self._init_tray()
        self._init_hotkey()
        self._init_replay()
        self._connect_signals()
        self._start_capture()

        self._init_gamepad_async()

    def _init_ui(self):
        self.root.title("ZZZ PrtSc - 绝区零截图工具")
        self.root.geometry("475x410")
        self.root.resizable(False, False)
        self.root.configure(fg_color="#f5f5f5")

        try:
            icon_path = self._get_resource_path("app_icon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

        self._main_frame = ctk.CTkFrame(self.root, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#e8e8e8")
        self._main_frame.pack(fill=ctk.BOTH, expand=True, padx=18, pady=18)

        header_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        header_frame.pack(fill=ctk.X, padx=24, pady=(24, 18))

        self.mode_label = ctk.CTkLabel(
            header_frame,
            text="普通模式",
            font=("Microsoft YaHei", 22, "bold"),
            text_color="#2c2c2c"
        )
        self.mode_label.pack(side=ctk.LEFT)

        right_btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_btn_frame.pack(side=ctk.RIGHT)

        folder_btn = ctk.CTkButton(
            right_btn_frame,
            text="📂",
            command=self._open_save_folder,
            width=36,
            height=34,
            corner_radius=4,
            fg_color="#f0f0f0",
            text_color="#666666",
            hover_color="#e0e0e0",
            font=("Microsoft YaHei", 16),
            border_width=1,
            border_color="#e0e0e0"
        )
        folder_btn.pack(side=ctk.RIGHT, padx=(5, 0))
        self._add_button_tooltip(folder_btn, "打开目录")

        self.refresh_gamepad_btn = ctk.CTkButton(
            right_btn_frame,
            text="🎮",
            command=self._refresh_gamepad,
            width=36,
            height=34,
            corner_radius=4,
            fg_color="#f0f0f0",
            text_color="#666666",
            hover_color="#e0e0e0",
            font=("Microsoft YaHei", 16),
            border_width=1,
            border_color="#e0e0e0"
        )
        self.refresh_gamepad_btn.pack(side=ctk.RIGHT, padx=(5, 0))
        self._add_button_tooltip(self.refresh_gamepad_btn, "识别手柄")

        settings_btn = ctk.CTkButton(
            right_btn_frame,
            text="⚙️",
            command=self._show_settings,
            width=36,
            height=34,
            corner_radius=6,
            fg_color="#f5f5f5",
            text_color="#666666",
            hover_color="#e8e8e8",
            font=("Microsoft YaHei", 16),
            border_width=1,
            border_color="#e0e0e0"
        )
        settings_btn.pack(side=ctk.RIGHT)
        self._add_button_tooltip(settings_btn, "设置")

        status_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        status_frame.pack(fill=ctk.X, padx=24, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="● 运行中",
            font=("Microsoft YaHei", 14),
            text_color="#4CAF50"
        )
        self.status_label.pack(anchor="w")

        gamepad_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        gamepad_frame.pack(fill=ctk.X, padx=24, pady=(0, 18))

        self.gamepad_status_label = ctk.CTkLabel(
            gamepad_frame,
            text="🎮 未检测到手柄",
            font=("Microsoft YaHei", 13),
            text_color="#888888"
        )
        self.gamepad_status_label.pack(anchor="w")

        button_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, padx=24, pady=(0, 18))

        self.toggle_button = ctk.CTkButton(
            button_frame,
            text="停止",
            width=168,
            height=48,
            corner_radius=6,
            font=("Microsoft YaHei", 16, "bold"),
            fg_color="#E53935",
            hover_color="#C62828",
            text_color="#ffffff",
            command=self._toggle_capture
        )
        self.toggle_button.pack(side=ctk.LEFT, padx=5)

        self.burst_button = ctk.CTkButton(
            button_frame,
            text="连拍模式",
            width=168,
            height=48,
            corner_radius=6,
            font=("Microsoft YaHei", 16, "bold"),
            fg_color="#607D8B",
            hover_color="#546E7A",
            text_color="#ffffff",
            state=ctk.NORMAL,
            command=self._toggle_burst_mode
        )
        self.burst_button.pack(side=ctk.RIGHT, padx=5)

        replay_button_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        replay_button_frame.pack(fill=ctk.X, padx=24, pady=(0, 18))

        self.replay_button = ctk.CTkButton(
            replay_button_frame,
            text="🎬 即时回放",
            width=175,
            height=50,
            corner_radius=10,
            font=("Microsoft YaHei", 16, "bold"),
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
            text_color="#ffffff",
            state=ctk.NORMAL,
            command=self._toggle_replay_mode,
            border_width=0
        )
        self.replay_button.pack(padx=5)

        param_frame = ctk.CTkFrame(self._main_frame, fg_color="#f8f8f8", corner_radius=8)
        param_frame.pack(fill=ctk.X, padx=24, pady=(0, 18))

        param_inner = ctk.CTkFrame(param_frame, fg_color="transparent")
        param_inner.pack(fill=ctk.BOTH, expand=True, padx=18, pady=12)

        self.duration_label = ctk.CTkLabel(
            param_inner,
            text=f"连拍时长: {self.burst_duration}秒",
            font=("Microsoft YaHei", 13),
            text_color="#666666"
        )
        self.duration_label.pack(side=ctk.LEFT)

        self.fps_label = ctk.CTkLabel(
            param_inner,
            text=f"频率: {self.burst_fps}张/秒",
            font=("Microsoft YaHei", 13),
            text_color="#666666"
        )
        self.fps_label.pack(side=ctk.LEFT, padx=20)

        self.replay_label = ctk.CTkLabel(
            param_inner,
            text=f"回放: {self.replay_duration}秒/{self.replay_fps}fps",
            font=("Microsoft YaHei", 13),
            text_color="#666666"
        )
        self.replay_label.pack(side=ctk.RIGHT)

        footer_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        footer_frame.pack(fill=ctk.X, padx=24, pady=(0, 24))

        tip_label = ctk.CTkLabel(
            footer_frame,
            text="关闭后程序在系统托盘继续运行",
            font=("Microsoft YaHei", 11),
            text_color="#aaaaaa"
        )
        tip_label.pack(side=ctk.LEFT, anchor="w")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.protocol("WM_ICONIFY", self._on_minimize)

    def _init_tray(self):
        icon_image = self._create_default_icon()
        tooltip = "ZZZ PrtSc - 绝区零截图工具"
        menu_items = [
            ("显示主窗口", self._show_main_window),
            ("开启/停止", self._toggle_capture),
            ("连拍模式", self._toggle_burst_mode),
            ("⚙️ 设置", self._show_settings),
            ("退出", self._quit_app),
        ]

        self._tray = Win32TrayManager()
        success = self._tray.setup(
            icon_image=icon_image,
            tooltip=tooltip,
            menu_items=menu_items,
            on_double_click=self._show_main_window
        )
        if not success:
            print("托盘图标初始化失败")

    def _update_tray(self):
        if not self._tray:
            return

        icon_image = self._create_default_icon()
        
        if self.is_replay_mode:
            tooltip = "ZZZ PrtSc - 绝区零截图工具 (即时回放)"
        elif self.is_burst_mode:
            tooltip = "ZZZ PrtSc - 绝区零截图工具 (连拍)"
        else:
            tooltip = "ZZZ PrtSc - 绝区零截图工具"
        
        burst_mode_label = "退出连拍" if self.is_burst_mode else "连拍模式"
        replay_mode_label = "退出回放" if self.is_replay_mode else "即时回放"

        menu_items = [
            ("显示主窗口", self._show_main_window),
            ("开启/停止", self._toggle_capture),
            (burst_mode_label, self._toggle_burst_mode),
            (replay_mode_label, self._toggle_replay_mode),
            ("⚙️ 设置", self._show_settings),
            ("退出", self._quit_app),
        ]

        self._tray.update_icon(icon_image)
        self._tray.update_tooltip(tooltip)
        self._tray.update_menu(menu_items)

    def _create_default_icon(self):
        if self.is_replay_mode:
            bg_color = '#9C27B0'
            frame_color = '#FFFFFF'
        elif self.is_burst_mode:
            bg_color = '#E53935'
            frame_color = '#FFFFFF'
        elif self.is_running:
            bg_color = '#4CAF50'
            frame_color = '#FFFFFF'
        else:
            bg_color = '#9E9E9E'
            frame_color = '#FFFFFF'

        img = Image.new('RGBA', (64, 64), color=bg_color)
        pixels = img.load()
        frame_rgb = self._hex_to_rgb(frame_color)

        inset = 10
        border_width = 2

        for y in range(64):
            for x in range(64):
                if y >= inset and y < 64 - inset:
                    if x >= inset and x < inset + border_width:
                        pixels[x, y] = frame_rgb
                    if x >= 64 - inset - border_width and x < 64 - inset:
                        pixels[x, y] = frame_rgb

                if x >= inset and x < 64 - inset:
                    if y >= inset and y < inset + border_width:
                        pixels[x, y] = frame_rgb
                    if y >= 64 - inset - border_width and y < 64 - inset:
                        pixels[x, y] = frame_rgb

        corner_size = 8
        for i in range(corner_size):
            pixels[inset - 1, inset + i] = frame_rgb
            pixels[inset + i, inset - 1] = frame_rgb

            pixels[64 - inset, inset + i] = frame_rgb
            pixels[64 - inset - 1 - i, inset - 1] = frame_rgb

            pixels[inset - 1, 64 - inset - 1 - i] = frame_rgb
            pixels[inset + i, 64 - inset] = frame_rgb

            pixels[64 - inset, 64 - inset - 1 - i] = frame_rgb
            pixels[64 - inset - 1 - i, 64 - inset] = frame_rgb

        z_width = 10
        z_height = 14
        stroke_width = 3
        z_start_x = 15
        z_start_y = 25

        def draw_z(x, y):
            for i in range(z_width):
                for j in range(stroke_width):
                    if 0 <= x + i < 64 and 0 <= y + j < 64:
                        pixels[x + i, y + j] = frame_rgb
            
            for i in range(z_width):
                for j in range(stroke_width):
                    if 0 <= x + i < 64 and 0 <= y + z_height - stroke_width + j < 64:
                        pixels[x + i, y + z_height - stroke_width + j] = frame_rgb
            
            for i in range(stroke_width):
                for j in range(z_height):
                    if 0 <= x + i < 64 and 0 <= y + j < 64:
                        pixels[x + i, y + j] = frame_rgb
            
            for i in range(z_width):
                for j in range(stroke_width):
                    py = y + z_height - stroke_width - int((z_height - stroke_width) * (i / z_width))
                    if 0 <= x + i + stroke_width < 64 and 0 <= py + j < 64:
                        pixels[x + i + stroke_width, py + j] = frame_rgb

        draw_z(z_start_x, z_start_y)
        draw_z(z_start_x + z_width + 3, z_start_y)
        draw_z(z_start_x + z_width * 2 + 6, z_start_y)

        return img

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _init_hotkey(self):
        self.hotkey_manager = HotkeyManager(self.signal_bridge)

    def _init_gamepad_async(self):
        def gamepad_init_thread():
            try:
                self.gamepad_manager = GamepadManager(self.signal_bridge)
                self.gamepad_manager._on_status_change = self._on_gamepad_status_change
                if self.gamepad_manager.start():
                    self.root.after(0, self._update_gamepad_status)
                else:
                    self.root.after(0, lambda: self.gamepad_status_label.configure(text="🎮 未检测到手柄"))
            except Exception as e:
                print(f"初始化手柄管理器失败: {e}")
                self.root.after(0, lambda: self.gamepad_status_label.configure(text="🎮 手柄初始化失败"))

        thread = threading.Thread(target=gamepad_init_thread, daemon=True)
        thread.start()

    def _on_gamepad_status_change(self):
        """手柄状态变化回调（从监控线程调用）"""
        self.root.after(0, self._update_gamepad_status)

    def _update_gamepad_status(self):
        if self.gamepad_manager and self.gamepad_manager.is_running:
            info = self.gamepad_manager.get_connected_gamepad_info()
            gamepad_type = info.get('type')
            gamepad_name = info.get('name', '')
            scanning = info.get('scanning', False)

            status_text = self._get_gamepad_status_text(gamepad_type, gamepad_name, scanning)
            self.gamepad_status_label.configure(text=status_text)
        else:
            self.gamepad_status_label.configure(text="")

    def _get_gamepad_status_text(self, gamepad_type, gamepad_name, scanning):
        if scanning:
            return '🔍 正在扫描手柄...'
        
        if not gamepad_type:
            return '🎮 未检测到手柄，可使用 PrintScreen 键截图'
        
        gamepad_messages = {
            'ps5': '🎮 PS5 DualSense 已连接，按 [Create] 键截图',
            'xbox': '🎮 Xbox 手柄已连接，按 [Share] 键截图',
            'switch': '🎮 Switch Pro 已连接，按 [Capture] 键截图',
            'generic': '🎮 手柄已连接，按截图键截图',
        }

        if gamepad_type in gamepad_messages:
            return gamepad_messages[gamepad_type]
        elif gamepad_name:
            return f'🎮 {gamepad_name} 已连接'
        return ""

    def _refresh_gamepad(self):
        """手动重新检测手柄连接"""
        if self.gamepad_manager:
            self.gamepad_status_label.configure(text='🔍 正在扫描手柄...')
            self.root.update()
            
            def do_refresh():
                self.gamepad_manager.re_detect_joystick()
                self.root.after(0, self._update_gamepad_status)
            
            thread = threading.Thread(target=do_refresh, daemon=True)
            thread.start()

    def _init_replay(self):
        """初始化即时回放管理器"""
        self.instant_replay = InstantReplay()
        self.instant_replay.set_config(
            duration=self.replay_duration,
            fps=self.replay_fps,
            output_folder=self.replay_save_folder
        )

    def _connect_signals(self):
        self.signal_bridge.connect_screenshot(self._take_screenshot)
        self.signal_bridge.connect_exit(self._quit_app)

    def _update_ui_for_burst_mode(self):
        if self.is_burst_mode:
            self.mode_label.configure(text="连拍模式")
            self.burst_button.configure(
                text="退出连拍",
                fg_color="#e54d4d",
                hover_color="#d63d3d",
                text_color="#ffffff",
                state=ctk.NORMAL
            )
            bg_color = "#fef8f8"
        else:
            self.mode_label.configure(text="普通模式")
            if self.is_running:
                self.burst_button.configure(
                    text="连拍模式",
                    fg_color="#666666",
                    hover_color="#555555",
                    text_color="#ffffff",
                    state=ctk.NORMAL
                )
            else:
                self.burst_button.configure(
                    text="连拍模式",
                    fg_color="#cccccc",
                    hover_color="#cccccc",
                    text_color="#999999",
                    state=ctk.DISABLED
                )
            bg_color = "#fafafa"

        self.root.configure(fg_color=bg_color)
        if self._main_frame:
            self._main_frame.configure(fg_color=bg_color)

        self._update_tray()

    def _show_settings(self):
        dialog = SettingsDialog(self.root, {
            "burst_duration": self.burst_duration,
            "burst_fps": self.burst_fps,
            "burst_save_folder": self.burst_save_folder,
            "replay_duration": self.replay_duration,
            "replay_fps": self.replay_fps,
            "replay_save_folder": self.replay_save_folder
        })

        self.root.wait_window(dialog.dialog)
        result = dialog.result
        if result:
            self.burst_duration = result["burst_duration"]
            self.burst_fps = result["burst_fps"]
            self.burst_save_folder = result["burst_save_folder"]
            self.replay_duration = result["replay_duration"]
            self.replay_fps = result["replay_fps"]
            self.replay_save_folder = result["replay_save_folder"]

            self.settings.save({
                "burst_duration": self.burst_duration,
                "burst_fps": self.burst_fps,
                "burst_save_folder": self.burst_save_folder,
                "replay_duration": self.replay_duration,
                "replay_fps": self.replay_fps,
                "replay_save_folder": self.replay_save_folder
            })

            self.duration_label.configure(text=f"连拍时长: {self.burst_duration}秒")
            self.fps_label.configure(text=f"频率: {self.burst_fps}张/秒")
            self.replay_label.configure(text=f"回放: {self.replay_duration}秒/{self.replay_fps}fps")

    def _toggle_burst_mode(self):
        if not self.is_running:
            return
        
        if self.is_replay_mode:
            self._toggle_replay_mode()

        self.is_burst_mode = not self.is_burst_mode
        self.settings.save({"burst_mode_enabled": self.is_burst_mode})
        
        if self.is_burst_mode:
            max_count = self.settings.get("max_burst_count", 30)
            self.screenshot_capture.prepare_for_burst(max_count)
        
        self._update_ui_for_burst_mode()

    def _toggle_replay_mode(self):
        if not self.is_running:
            return
        
        if self.is_burst_mode:
            self.is_burst_mode = False
            self.settings.save({"burst_mode_enabled": False})
            self._update_ui_for_burst_mode()

        self.is_replay_mode = not self.is_replay_mode
        self.settings.save({"replay_mode_enabled": self.is_replay_mode})
        
        if self.is_replay_mode:
            self.instant_replay.set_config(
                duration=self.replay_duration,
                fps=self.replay_fps,
                output_folder=self.replay_save_folder
            )
            self.instant_replay.start()
        else:
            self.instant_replay.stop()
        
        self._update_ui_for_replay_mode()

    def _update_ui_for_replay_mode(self):
        if self.is_replay_mode:
            self.mode_label.configure(text="🎬 即时回放")
            self.replay_button.configure(
                text="⏹️ 退出回放",
                fg_color="#E54D4D",
                hover_color="#D63D3D",
                text_color="#ffffff",
                state=ctk.NORMAL
            )
            bg_color = "#f5f0fa"
        else:
            self.mode_label.configure(text="📷 普通模式")
            if self.is_running:
                self.replay_button.configure(
                    text="🎬 即时回放",
                    fg_color="#9C27B0",
                    hover_color="#7B1FA2",
                    text_color="#ffffff",
                    state=ctk.NORMAL
                )
            else:
                self.replay_button.configure(
                    text="🎬 即时回放",
                    fg_color="#e8e8e8",
                    hover_color="#e8e8e8",
                    text_color="#aaaaaa",
                    state=ctk.DISABLED
                )
            bg_color = "#fafafa"

        self.root.configure(fg_color=bg_color)
        if self._main_frame:
            self._main_frame.configure(fg_color=bg_color)
        
        self._update_tray()

    def _toggle_capture(self):
        if not self.is_running:
            self._start_capture()
        else:
            self._stop_capture()

    def _start_capture(self):
        print("尝试启动热键管理器...")
        if not self.hotkey_manager:
            print("错误：热键管理器未初始化")
            CTkMessagebox(title="错误", message="无法注册热键，请检查权限", icon="warning")
            return
        
        print("热键管理器已初始化，尝试启动...")
        success = self.hotkey_manager.start()
        print(f"热键启动结果: {success}")
        
        if not success:
            CTkMessagebox(title="错误", message="无法注册热键，请检查权限", icon="warning")
            return

        self.is_running = True
        self.toggle_button.configure(text="停止", fg_color="#E53935", hover_color="#C62828")

        if self.is_burst_mode:
            total = self.burst_duration * self.burst_fps
            self.status_label.configure(
                text=f"状态：运行中 (连拍 {self.burst_duration}秒/{self.burst_fps}张/秒，共{total}张)",
                text_color="#FF9800"
            )
        else:
            self.status_label.configure(text="状态：运行中", text_color="#4CAF50")
            self.burst_button.configure(
                text="连拍模式",
                fg_color="#666666",
                hover_color="#555555",
                text_color="#ffffff",
                state=ctk.NORMAL
            )

        self.settings.save({"enabled": True})
        self._update_tray()

    def _stop_capture(self):
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        
        if self.instant_replay:
            self.instant_replay.stop()

        self.is_running = False
        self.toggle_button.configure(text="开启", fg_color="#2196F3", hover_color="#1976D2")
        self.status_label.configure(text="状态：已停止", text_color="#999")

        save_updates = {"enabled": False}
        if self.is_burst_mode:
            self.is_burst_mode = False
            save_updates["burst_mode_enabled"] = False
        if self.is_replay_mode:
            self.is_replay_mode = False
            save_updates["replay_mode_enabled"] = False
        self.settings.save(save_updates)
        self._update_ui_for_burst_mode()
        self._update_ui_for_replay_mode()

    def _take_screenshot(self):
        if self.root.winfo_viewable():
            self.root.after(0, self._do_screenshot)
        else:
            self.root.after(10, self._do_screenshot)

    def _do_screenshot(self):
        try:
            if self.is_replay_mode:
                self._save_replay()
            elif self.is_burst_mode:
                if self.screenshot_capture.is_bursting():
                    return

                total = self.burst_duration * self.burst_fps

                def on_progress(current, total_count):
                    self.root.after(0, lambda: self.status_label.configure(
                        text=f"状态：正在连拍 {current}/{total_count}",
                        text_color="#FF9800"
                    ))
                    self.root.after(0, self._update_tray_bursting)

                def on_write_start():
                    self.root.after(0, lambda: self.status_label.configure(
                        text="状态：连拍文件正在写入磁盘",
                        text_color="#E53935"
                    ))
                    self.root.after(0, self._update_tray_bursting)

                def on_write_progress(current, total_count):
                    self.root.after(0, lambda: self.status_label.configure(
                        text=f"状态：连拍文件正在写入磁盘 {current}/{total_count}",
                        text_color="#E53935"
                    ))

                def on_complete(count):
                    self.root.after(0, lambda: self._on_burst_complete(count))

                max_count = self.settings.get("max_burst_count", 30)
                self.screenshot_capture.burst_capture_async(
                    self.burst_duration,
                    total,
                    self.burst_save_folder,
                    on_progress,
                    on_complete,
                    max_count,
                    self.burst_fps,
                    on_write_start,
                    on_write_progress
                )
            else:
                success = self.screenshot_capture.capture_primary_screen()
                if success:
                    self._show_notification("截图成功", "已复制到剪贴板")
        except Exception as e:
            print(f"截图失败: {e}")

    def _save_replay(self):
        """保存即时回放视频"""
        if not self.instant_replay or not self.instant_replay.is_recording():
            return
        
        self.status_label.configure(
            text="状态：正在保存回放视频...",
            text_color="#9C27B0"
        )
        
        def on_progress(current, total):
            self.root.after(0, lambda: self.status_label.configure(
                text=f"状态：正在编码视频 {current}/{total}",
                text_color="#9C27B0"
            ))
        
        def save_replay_async():
            success = self.instant_replay.save_replay(on_progress)
            self.root.after(0, lambda: self._on_replay_complete(success))
        
        thread = threading.Thread(target=save_replay_async, daemon=True)
        thread.start()

    def _on_replay_complete(self, success):
        if success:
            self.status_label.configure(text="状态：运行中", text_color="#4CAF50")
            self._show_notification("回放保存成功", f"已保存{self.replay_duration}秒视频")
        else:
            self.status_label.configure(text="状态：运行中", text_color="#4CAF50")
            self._show_notification("回放保存失败", "未能保存视频，请检查ffmpeg是否安装")

    def _update_tray_bursting(self):
        if self._tray:
            icon_image = self._create_default_icon()
            self._tray.update_icon(icon_image)

    def _on_burst_complete(self, count):
        self.status_label.configure(text="状态：运行中", text_color="#4CAF50")
        self._update_tray()
        if count > 0:
            self._show_notification("连拍完成", f"已保存{count}张截图")
        else:
            self._show_notification("连拍失败", "未能保存截图")

    def _show_notification(self, title, message):
        # 如果已有通知窗口在显示，先销毁旧的避免重叠
        if self._notification_window is not None:
            try:
                self._notification_window.destroy()
            except Exception:
                pass
            self._notification_window = None

        notification = ctk.CTkToplevel(self.root)
        self._notification_window = notification
        notification.overrideredirect(True)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 240
        window_height = 80
        margin = 10
        
        x_pos = screen_width - window_width - margin
        y_pos = screen_height - window_height - margin - 50
        
        notification.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        notification.configure(fg_color="#ffffff", border_width=1, border_color="#e0e0e0")

        title_label = ctk.CTkLabel(
            notification,
            text=title,
            font=("Microsoft YaHei", 12, "bold"),
            text_color="#1a1a1a"
        )
        title_label.pack(pady=(10, 0))

        msg_label = ctk.CTkLabel(
            notification,
            text=message,
            font=("Microsoft YaHei", 11),
            text_color="#666666"
        )
        msg_label.pack(pady=5)

        def _on_destroy():
            self._notification_window = None
            notification.destroy()

        notification.after(2000, _on_destroy)

    def _show_main_window(self):
        self.root.after(0, lambda: (self.root.deiconify(), self.root.lift()))

    def _open_save_folder(self):
        """根据当前模式打开对应的保存目录"""
        if self.is_replay_mode:
            folder_path = self.replay_save_folder
            folder_label = "回放"
        elif self.is_burst_mode:
            folder_path = self.burst_save_folder
            folder_label = "连拍"
        else:
            folder_path = self.burst_save_folder
            folder_label = "截图"
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            self._show_notification("提示", f"{folder_label}目录不存在")

    def _on_close(self):
        self.root.withdraw()
        self._show_notification("ZZZ PrtSc", "已最小化到系统托盘")

    def _on_minimize(self):
        self.root.iconify()

    def _quit_app(self):
        def do_quit():
            if self.hotkey_manager:
                self.hotkey_manager.stop()
            if self.gamepad_manager:
                self.gamepad_manager.stop()
            if self.instant_replay:
                self.instant_replay.stop()
            if self._tray:
                self._tray.stop()
            try:
                self.root.destroy()
            except Exception:
                pass
            sys.exit(0)
        self.root.after(0, do_quit)

    def _get_resource_path(self, filename):
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.resolve()
        return base_path / filename

    def run(self):
        self.root.mainloop()

    def _init_tooltip(self):
        if self._tooltip_frame is None:
            self._tooltip_frame = ctk.CTkFrame(self.root, fg_color="transparent")
            self._tooltip_label = ctk.CTkLabel(
                self._tooltip_frame,
                text="",
                font=("Microsoft YaHei", 12, "bold"),
                fg_color="#333333",
                text_color="#ffffff",
                corner_radius=4,
                padx=10,
                pady=5
            )
            self._tooltip_label.pack()
            self._tooltip_frame.pack_forget()

    def _show_tooltip(self, button, text):
        self._init_tooltip()
        self._tooltip_label.configure(text=text)
        self._tooltip_label.update_idletasks()
        
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        button_root_x = button.winfo_rootx()
        button_root_y = button.winfo_rooty()
        button_width = button.winfo_width()
        tooltip_width = self._tooltip_label.winfo_width()
        tooltip_height = self._tooltip_label.winfo_height()
        
        rel_x = button_root_x - root_x + button_width // 2 - tooltip_width // 2
        rel_y = button_root_y - root_y - tooltip_height - 8
        
        self._tooltip_frame.place(x=rel_x, y=rel_y)
        self._tooltip_frame.lift()

    def _hide_tooltip(self):
        if self._tooltip_frame is not None:
            self._tooltip_frame.place_forget()

    def _add_button_tooltip(self, button, text):
        def enter(event):
            self._show_tooltip(button, text)
        
        def leave(event):
            self._hide_tooltip()
        
        button.bind("<Enter>", enter, add="+")
        button.bind("<Leave>", leave, add="+")


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
