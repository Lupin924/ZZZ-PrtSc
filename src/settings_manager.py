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
from pathlib import Path
from typing import Any


class SettingsManager:
    """设置管理器 - 优化版本，使用 __slots__ 减少内存占用"""

    __slots__ = ("_settings_file", "_default_settings", "_cache", "_cache_valid")

    # 默认设置 - 类级别常量
    DEFAULT_SETTINGS: dict[str, Any] = {
        "enabled": False,
        "screenshot_folder": None,  # 延迟初始化
        "minimize_to_tray": True,
        "show_notification": True,
        "burst_mode_enabled": False,
        "burst_duration": 3,
        "burst_fps": 3,
        "burst_save_folder": None,
        "max_burst_count": 30,  # 最大连拍张数限制（基于8GB内存估算）
    }

    def __init__(self) -> None:
        """初始化设置管理器"""
        self._settings_file = self._get_settings_file_path()
        self._default_settings = self._init_default_settings()
        self._cache: dict[str, Any] | None = None
        self._cache_valid = False

    def _init_default_settings(self) -> dict[str, Any]:
        """初始化默认设置 - 延迟计算截图文件夹路径"""
        defaults = self.DEFAULT_SETTINGS.copy()
        defaults["screenshot_folder"] = str(Path.home() / "Pictures" / "Screenshots")
        defaults["burst_save_folder"] = str(Path.home() / "Pictures" / "Screenshots" / "Burst")
        return defaults

    def _get_settings_file_path(self) -> Path:
        """获取设置文件路径 - 确保设置能持久化"""
        # 对于打包后的程序，直接使用 AppData 目录
        # 因为 sys._MEIPASS 是临时目录，程序退出后会被删除
        if getattr(sys, "frozen", False):
            app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            app_folder = app_data / "ZZZ PrtSc"
            app_folder.mkdir(parents=True, exist_ok=True)
            return app_folder / "settings.json"
        
        # 开发模式下，优先使用当前工作目录
        base_dir = Path.cwd()
        settings_file = base_dir / "settings.json"
        
        # 检查是否可写
        try:
            test_file = settings_file.with_suffix(".test")
            test_file.write_text("test")
            test_file.unlink()
            return settings_file
        except (IOError, OSError):
            pass
        
        # 回退到AppData目录
        app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        app_folder = app_data / "ZZZ PrtSc"
        app_folder.mkdir(parents=True, exist_ok=True)
        return app_folder / "settings.json"

    def _load_from_file(self) -> dict[str, Any]:
        """从文件加载设置"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载设置失败: {e}")
        return {}

    def load(self) -> dict[str, Any]:
        """加载设置 - 使用缓存优化"""
        if self._cache_valid and self._cache is not None:
            return self._cache.copy()

        # 从文件加载并合并默认设置
        file_settings = self._load_from_file()
        merged = self._default_settings.copy()
        merged.update(file_settings)

        # 更新缓存
        self._cache = merged.copy()
        self._cache_valid = True

        return merged

    def save(self, settings: dict[str, Any]) -> bool:
        """保存设置 - 直接写入"""
        try:
            # 加载现有设置并更新
            current = self.load()
            current.update(settings)

            # 直接写入文件
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)

            # 使缓存失效
            self._cache_valid = False

            return True
        except (IOError, OSError) as e:
            print(f"保存设置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取特定设置项"""
        settings = self.load()
        return settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置特定设置项"""
        return self.save({key: value})

    def invalidate_cache(self) -> None:
        """使缓存失效 - 在设置被外部修改时调用"""
        self._cache_valid = False
        self._cache = None
