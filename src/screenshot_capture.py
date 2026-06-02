#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高性能截图捕获模块 - BitBlt API
使用Windows GDI BitBlt进行硬件加速截屏
"""

from __future__ import annotations

import ctypes
import threading
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

import win32clipboard
from PIL import Image


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', ctypes.c_uint32),
        ('biWidth', ctypes.c_long),
        ('biHeight', ctypes.c_long),
        ('biPlanes', ctypes.c_short),
        ('biBitCount', ctypes.c_short),
        ('biCompression', ctypes.c_uint32),
        ('biSizeImage', ctypes.c_uint32),
        ('biXPelsPerMeter', ctypes.c_long),
        ('biYPelsPerMeter', ctypes.c_long),
        ('biClrUsed', ctypes.c_uint32),
        ('biClrImportant', ctypes.c_uint32),
    ]


class BitBltScreenshot:
    """BitBlt高速截图器 - 优化版"""

    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32
        self._gdi32 = ctypes.windll.gdi32
        self._screen_width = 0
        self._screen_height = 0
        self._row_size = 0
        self._pixel_buffer = None
        self._pixel_array = None
        self._bmi = None
        self._bmi_buffer = None
        self._init_screen_info()

    def _init_screen_info(self):
        """初始化屏幕信息，避免重复获取"""
        self._screen_width = self._user32.GetSystemMetrics(0)
        self._screen_height = self._user32.GetSystemMetrics(1)
        self._row_size = (self._screen_width * 3 + 3) & ~3
        
        buffer_size = self._row_size * self._screen_height
        self._pixel_buffer = bytearray(buffer_size)
        self._pixel_array = (ctypes.c_ubyte * buffer_size).from_buffer(self._pixel_buffer)
        
        self._bmi = BITMAPINFOHEADER()
        self._bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        self._bmi.biWidth = self._screen_width
        self._bmi.biHeight = -self._screen_height
        self._bmi.biPlanes = 1
        self._bmi.biBitCount = 24
        self._bmi.biCompression = 0
        self._bmi_buffer = ctypes.byref(self._bmi)

    def capture(self) -> Optional[Image.Image]:
        """执行BitBlt截图 - 优化版"""
        hdc = self._user32.GetDC(0)
        if not hdc:
            return None

        hdc_mem = self._gdi32.CreateCompatibleDC(hdc)
        if not hdc_mem:
            self._user32.ReleaseDC(0, hdc)
            return None

        hbitmap = self._gdi32.CreateCompatibleBitmap(hdc, self._screen_width, self._screen_height)
        if not hbitmap:
            self._gdi32.DeleteDC(hdc_mem)
            self._user32.ReleaseDC(0, hdc)
            return None

        self._gdi32.SelectObject(hdc_mem, hbitmap)

        result = self._gdi32.BitBlt(
            hdc_mem, 0, 0,
            self._screen_width, self._screen_height,
            hdc, 0, 0,
            0x00CC0020
        )

        if not result:
            self._gdi32.DeleteObject(hbitmap)
            self._gdi32.DeleteDC(hdc_mem)
            self._user32.ReleaseDC(0, hdc)
            return None

        scan_result = self._gdi32.GetDIBits(
            hdc_mem,
            hbitmap,
            0,
            self._screen_height,
            ctypes.byref(self._pixel_array),
            self._bmi_buffer,
            0
        )

        self._gdi32.DeleteObject(hbitmap)
        self._gdi32.DeleteDC(hdc_mem)
        self._user32.ReleaseDC(0, hdc)

        if not scan_result:
            return None

        try:
            return Image.frombytes('RGB', (self._screen_width, self._screen_height), bytes(self._pixel_buffer), 'raw', 'BGR', self._row_size)
        except Exception:
            return None

    def get_screen_size(self):
        """获取屏幕尺寸"""
        return (
            self._user32.GetSystemMetrics(0),
            self._user32.GetSystemMetrics(1)
        )


class ScreenshotCapture:
    """截图捕获器 - BitBlt高性能版"""

    __slots__ = ("_blt", "_burst_thread", "_save_thread", "_is_bursting", "_max_fps", "_lock",
                 "_burst_cache", "_screen_width", "_screen_height")

    def __init__(self) -> None:
        self._blt = BitBltScreenshot()
        self._burst_thread: Optional[threading.Thread] = None
        self._save_thread: Optional[threading.Thread] = None
        self._is_bursting = False
        self._max_fps = 10
        self._lock = threading.Lock()
        
        self._burst_cache = []
        screen_size = self._blt.get_screen_size()
        self._screen_width = screen_size[0]
        self._screen_height = screen_size[1]
        
        self._prepare_default_save_folder()

    def _prepare_default_save_folder(self):
        """预先创建默认保存目录"""
        default_folder = Path.home() / "Pictures" / "Screenshots" / "Burst"
        default_folder.mkdir(parents=True, exist_ok=True)

    def prepare_for_burst(self, max_expected_frames: int = 30) -> None:
        """预先为连拍模式准备资源"""
        if self._burst_cache:
            self._burst_cache.clear()
        
        self._burst_cache = [None] * max_expected_frames

    def capture_primary_screen(self) -> bool:
        """截取主屏幕并复制到剪贴板"""
        with self._lock:
            try:
                screenshot = self._blt.capture()

                if screenshot is None:
                    print("截图失败：capture() 返回 None")
                    return False

                output = BytesIO()
                screenshot.save(output, format='BMP')
                data = output.getvalue()[14:]
                output.close()

                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                    win32clipboard.CloseClipboard()
                    return True
                except Exception as e:
                    print(f"剪贴板操作失败: {e}")
                    return False

            except Exception as e:
                print(f"截图失败: {e}")
                import traceback
                traceback.print_exc()
                return False

    def get_max_fps(self) -> int:
        """获取最大帧率"""
        return self._max_fps

    def is_bursting(self) -> bool:
        """检查是否正在进行连拍"""
        return self._is_bursting

    def burst_capture_async(self, duration: float, total: int,
                           save_folder: str,
                           on_progress: Optional[Callable] = None,
                           on_complete: Optional[Callable] = None,
                           max_count: int = 30,
                           fps: int = 3,
                           on_write_start: Optional[Callable] = None,
                           on_write_progress: Optional[Callable] = None) -> None:
        """异步连拍"""
        if self._burst_thread and self._burst_thread.is_alive():
            return

        total = min(total, max_count)
        
        if total <= 0:
            if on_complete:
                on_complete(0)
            return

        self._is_bursting = True
        self._burst_thread = threading.Thread(
            target=self._burst_capture_worker,
            args=(duration, total, save_folder, on_progress, on_complete, fps, on_write_start, on_write_progress),
            daemon=True
        )
        self._burst_thread.start()

    def _burst_capture_worker(self, duration: float, total: int,
                             save_folder: str,
                             on_progress: Optional[Callable],
                             on_complete: Optional[Callable],
                             fps: int = 3,
                             on_write_start: Optional[Callable] = None,
                             on_write_progress: Optional[Callable] = None) -> None:
        """连拍工作线程 - 内存缓存模式"""
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        
        if total <= 0:
            if on_complete:
                on_complete(0)
            return
            
        if total == 1:
            target_interval = duration
        else:
            target_interval = duration / (total - 1) if total > 1 else duration
        
        cache = self._burst_cache if len(self._burst_cache) >= total else []
        cache_size = 0
        start_time = time.perf_counter()
        
        for frame_idx in range(total):
            if not self._is_bursting:
                break

            screenshot = self._blt.capture()
            
            if screenshot:
                if cache:
                    cache[cache_size] = screenshot
                else:
                    cache.append(screenshot)
                cache_size += 1

            if on_progress:
                on_progress(cache_size, total)

            if frame_idx < total - 1:
                current_time = time.perf_counter()
                target_next_time = start_time + (frame_idx + 1) * target_interval
                sleep_time = max(0, target_next_time - current_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)

        self._is_bursting = False

        if cache_size > 0:
            actual_cache = cache[:cache_size] if isinstance(cache, list) else cache
            self._save_thread = threading.Thread(
                target=self._save_cache_to_disk,
                args=(actual_cache, save_folder, on_write_start, on_write_progress, on_complete),
                daemon=True
            )
            self._save_thread.start()
        elif on_complete:
            on_complete(0)

    def is_saving(self) -> bool:
        """检查是否正在保存到磁盘"""
        return hasattr(self, '_save_thread') and self._save_thread and self._save_thread.is_alive()

    def _save_cache_to_disk(self, cache, save_folder, on_write_start, on_write_progress, on_complete):
        """后台线程将缓存写入磁盘"""
        if on_write_start:
            on_write_start()
        
        saved = 0
        for i, screenshot in enumerate(cache):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = Path(save_folder) / f"screenshot_{timestamp}.png"
                screenshot.save(str(filename))
                saved += 1
                
                if on_write_progress:
                    on_write_progress(saved, len(cache))
            except Exception as e:
                print(f"保存截图失败: {e}")
        
        if on_complete:
            on_complete(saved)

    def __del__(self):
        if self._burst_thread and self._burst_thread.is_alive():
            self._is_bursting = False
            self._burst_thread.join(timeout=1.0)
