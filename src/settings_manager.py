#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理模块
管理应用程序设置 - 优化版本
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any


class SettingsManager:
    """设置管理器 - 优化版本，使用 __slots__ 减少内存占用"""

    __slots__ = ("_settings_file", "_default_settings", "_cache", "_cache_valid", "_lock")

    DEFAULT_SETTINGS: dict[str, Any] = {
        "enabled": False,
        "screenshot_folder": None,
        "minimize_to_tray": True,
        "show_notification": True,
        "burst_mode_enabled": False,
        "burst_duration": 3,
        "burst_fps": 3,
        "burst_save_folder": None,
        "max_burst_count": 30,
        "replay_mode_enabled": False,
        "replay_duration": 5,
        "replay_fps": 30,
        "replay_save_folder": None,
    }

    def __init__(self) -> None:
        self._settings_file = self._get_settings_file_path()
        self._default_settings = self._init_default_settings()
        self._cache: dict[str, Any] | None = None
        self._cache_valid = False
        self._lock = threading.Lock()

    def _init_default_settings(self) -> dict[str, Any]:
        defaults = self.DEFAULT_SETTINGS.copy()
        defaults["screenshot_folder"] = str(Path.home() / "Pictures" / "Screenshots")
        defaults["burst_save_folder"] = str(Path.home() / "Pictures" / "Screenshots" / "Burst")
        defaults["replay_save_folder"] = str(Path.home() / "Pictures" / "Screenshots" / "Replay")
        return defaults

    def _get_settings_file_path(self) -> Path:
        if getattr(sys, "frozen", False):
            app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            app_folder = app_data / "ZZZ PrtSc"
            app_folder.mkdir(parents=True, exist_ok=True)
            return app_folder / "settings.json"

        base_dir = Path.cwd()
        settings_file = base_dir / "settings.json"

        try:
            test_file = settings_file.with_suffix(".test")
            test_file.write_text("test")
            test_file.unlink()
            return settings_file
        except (IOError, OSError):
            pass

        app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        app_folder = app_data / "ZZZ PrtSc"
        app_folder.mkdir(parents=True, exist_ok=True)
        return app_folder / "settings.json"

    def _load_from_file(self) -> dict[str, Any]:
        try:
            if self._settings_file.exists():
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载设置失败: {e}")
        return {}

    def load(self) -> dict[str, Any]:
        with self._lock:
            if self._cache_valid and self._cache is not None:
                return self._cache.copy()

            file_settings = self._load_from_file()
            merged = self._default_settings.copy()
            merged.update(file_settings)

            self._cache = merged.copy()
            self._cache_valid = True

            return merged

    def save(self, settings: dict[str, Any]) -> bool:
        try:
            current = self.load()
            current.update(settings)

            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)

            self._cache_valid = False
            return True
        except (IOError, OSError) as e:
            print(f"保存设置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        settings = self.load()
        return settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        return self.save({key: value})

    def invalidate_cache(self) -> None:
        with self._lock:
            self._cache_valid = False
            self._cache = None


class SettingsDialog:
    """设置对话框 - 统一管理连拍与回放设置UI"""

    def __init__(self, parent, settings):
        import customtkinter as ctk
        self._ctk = ctk

        self.parent = parent
        self.burst_duration = settings.get("burst_duration", 3)
        self.burst_fps = settings.get("burst_fps", 3)
        self.burst_save_folder = settings.get(
            "burst_save_folder", str(Path.home() / "Pictures" / "Screenshots" / "Burst"))
        self.replay_duration = settings.get("replay_duration", 5)
        self.replay_fps = settings.get("replay_fps", 30)
        self.replay_save_folder = settings.get(
            "replay_save_folder", str(Path.home() / "Pictures" / "Screenshots" / "Replay"))
        self.result = None
        self._create_dialog()

    def _create_dialog(self):
        ctk = self._ctk

        # 创建Toplevel，先不设置尺寸
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("设置")
        self.dialog.configure(fg_color="#fafafa")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 所有变量
        self.burst_dur_var = ctk.StringVar(value=str(self.burst_duration))
        self.burst_fps_var = ctk.StringVar(value=str(self.burst_fps))
        self.burst_folder_var = ctk.StringVar(value=self.burst_save_folder)
        self.replay_dur_var = ctk.StringVar(value=str(self.replay_duration))
        self.replay_fps_var = ctk.StringVar(value=str(self.replay_fps))
        self.replay_folder_var = ctk.StringVar(value=self.replay_save_folder)

        # 主容器 - 使用grid布局
        container = ctk.CTkFrame(self.dialog, fg_color="#fafafa")
        container.pack(padx=20, pady=14, fill="both", expand=True)

        row = 0
        # 标题 - 与主界面一致，16号字体
        ctk.CTkLabel(container, text="⚙️ 设置", font=("Microsoft YaHei", 16, "bold"), text_color="#2c2c2c").grid(row=row, column=0, columnspan=5, sticky="w", pady=(0, 12))
        row += 1

        # 连拍区域
        # row1: 连拍时长 | 频率
        ctk.CTkLabel(container, text="📸 连拍时长", font=("Microsoft YaHei", 12), text_color="#666666", width=80).grid(row=row, column=0, sticky="w", padx=(0, 6))
        ctk.CTkEntry(container, textvariable=self.burst_dur_var, width=55, height=30, font=("Microsoft YaHei", 12), corner_radius=4, fg_color="#ffffff", border_width=1, border_color="#e0e0e0").grid(row=row, column=1, padx=(0, 6))
        ctk.CTkLabel(container, text="秒", font=("Microsoft YaHei", 12), text_color="#999999", width=24).grid(row=row, column=2, sticky="w")
        ctk.CTkLabel(container, text="频率", font=("Microsoft YaHei", 12), text_color="#666666", width=36).grid(row=row, column=3, sticky="w", padx=(12, 6))
        ctk.CTkEntry(container, textvariable=self.burst_fps_var, width=55, height=30, font=("Microsoft YaHei", 12), corner_radius=4, fg_color="#ffffff", border_width=1, border_color="#e0e0e0").grid(row=row, column=4, padx=(0, 6))
        ctk.CTkLabel(container, text="张/秒", font=("Microsoft YaHei", 12), text_color="#999999").grid(row=row, column=5, sticky="w")
        row += 1

        # row2: 连拍保存路径
        ctk.CTkLabel(container, text="保存路径", font=("Microsoft YaHei", 12), text_color="#666666", width=80).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=(6, 6))
        ctk.CTkEntry(container, textvariable=self.burst_folder_var, height=30, font=("Microsoft YaHei", 11), corner_radius=4, fg_color="#ffffff", border_width=1, border_color="#e0e0e0").grid(row=row, column=1, columnspan=4, sticky="ew", padx=(0, 6), pady=(6, 6))
        ctk.CTkButton(container, text="浏览", command=lambda: self._browse_folder("burst"), width=60, height=30, corner_radius=4, fg_color="#666666", hover_color="#555555", text_color="#ffffff", font=("Microsoft YaHei", 11)).grid(row=row, column=5, pady=(6, 6))
        row += 1

        # 分隔线
        ctk.CTkFrame(container, height=1, fg_color="#e8e8e8").grid(row=row, column=0, columnspan=6, sticky="ew", pady=10)
        row += 1

        # 回放区域
        # row4: 回放时长 | 帧率
        ctk.CTkLabel(container, text="🎬 回放时长", font=("Microsoft YaHei", 12), text_color="#666666", width=80).grid(row=row, column=0, sticky="w", padx=(0, 6))
        ctk.CTkOptionMenu(container, values=["3", "5", "10", "15"], variable=self.replay_dur_var, width=40, height=28, font=("Microsoft YaHei", 11), corner_radius=4, fg_color="#ffffff", button_color="#e0e0e0", button_hover_color="#cccccc", dropdown_fg_color="#ffffff", dropdown_hover_color="#f8f9fa", text_color="#333333").grid(row=row, column=1, padx=(0, 6))
        ctk.CTkLabel(container, text="秒", font=("Microsoft YaHei", 12), text_color="#999999", width=24).grid(row=row, column=2, sticky="w")
        ctk.CTkLabel(container, text="帧率", font=("Microsoft YaHei", 12), text_color="#666666", width=36).grid(row=row, column=3, sticky="w", padx=(12, 6))
        ctk.CTkOptionMenu(container, values=["24", "30", "60"], variable=self.replay_fps_var, width=40, height=28, font=("Microsoft YaHei", 11), corner_radius=4, fg_color="#ffffff", button_color="#e0e0e0", button_hover_color="#cccccc", dropdown_fg_color="#ffffff", dropdown_hover_color="#f8f9fa", text_color="#333333").grid(row=row, column=4, padx=(0, 6))
        ctk.CTkLabel(container, text="fps", font=("Microsoft YaHei", 12), text_color="#999999").grid(row=row, column=5, sticky="w")
        row += 1

        # row5: 回放保存路径
        ctk.CTkLabel(container, text="保存路径", font=("Microsoft YaHei", 12), text_color="#666666", width=80).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=(6, 6))
        ctk.CTkEntry(container, textvariable=self.replay_folder_var, height=30, font=("Microsoft YaHei", 11), corner_radius=4, fg_color="#ffffff", border_width=1, border_color="#e0e0e0").grid(row=row, column=1, columnspan=4, sticky="ew", padx=(0, 6), pady=(6, 6))
        ctk.CTkButton(container, text="浏览", command=lambda: self._browse_folder("replay"), width=60, height=30, corner_radius=4, fg_color="#666666", hover_color="#555555", text_color="#ffffff", font=("Microsoft YaHei", 11)).grid(row=row, column=5, pady=(6, 6))
        row += 1

        # 确定按钮 - 与主界面按钮一致
        ctk.CTkButton(container, text="确定", command=self._on_ok, width=200, height=44, corner_radius=6, fg_color="#9C27B0", hover_color="#7B1FA2", text_color="#ffffff", font=("Microsoft YaHei", 14, "bold")).grid(row=row, column=0, columnspan=6, pady=(12, 0))

        # 设置容器的列权重 - 只有中间间隔列可以拉伸，下拉框列保持固定宽度
        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=0)
        container.grid_columnconfigure(2, weight=0)
        container.grid_columnconfigure(3, weight=1)  # 中间间隔列拉伸
        container.grid_columnconfigure(4, weight=0)
        container.grid_columnconfigure(5, weight=0)

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_ok)

        # 更新布局计算，根据内容设置窗口大小
        self.dialog.update_idletasks()
        self.dialog.geometry("475x340")
        self.dialog.resizable(False, False)

    def _browse_folder(self, folder_type):
        ctk = self._ctk
        if folder_type == "burst":
            folder = ctk.filedialog.askdirectory(initialdir=self.burst_folder_var.get())
            if folder:
                self.burst_folder_var.set(folder)
                self.burst_save_folder = folder
        else:
            folder = ctk.filedialog.askdirectory(initialdir=self.replay_folder_var.get())
            if folder:
                self.replay_folder_var.set(folder)
                self.replay_save_folder = folder

    def _show_error(self, message):
        """统一错误提示"""
        try:
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="错误", message=message, icon="warning")
        except ImportError:
            print(f"错误：{message}")

    def _on_ok(self):
        ctk = self._ctk
        burst_duration_str = self.burst_dur_var.get().strip()
        burst_fps_str = self.burst_fps_var.get().strip()
        replay_duration_str = self.replay_dur_var.get().strip()

        if not burst_duration_str:
            self._show_error("请输入连拍时长")
            return
        if not burst_fps_str:
            self._show_error("请输入拍摄频率")
            return
        if not replay_duration_str:
            self._show_error("请输入回放时长")
            return

        try:
            burst_duration = int(burst_duration_str)
            burst_fps = int(burst_fps_str)
            replay_duration = int(replay_duration_str)
            replay_fps = int(self.replay_fps_var.get())

            if burst_duration <= 0:
                self._show_error("连拍时长必须大于0")
                return
            if burst_fps <= 0:
                self._show_error("拍摄频率必须大于0")
                return
            if replay_duration <= 0:
                self._show_error("回放时长必须大于0")
                return

            self.result = {
                "burst_duration": burst_duration,
                "burst_fps": burst_fps,
                "burst_save_folder": self.burst_folder_var.get(),
                "replay_duration": replay_duration,
                "replay_fps": replay_fps,
                "replay_save_folder": self.replay_folder_var.get(),
            }
        except ValueError:
            self._show_error("请输入有效的数字")
            return

        self.dialog.destroy()

    def show(self):
        self.parent.wait_window(self.dialog)
        return self.result
