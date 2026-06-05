#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即时回放模块 - 基于循环缓冲区实现
参考: dxcam, pyfastscreencap, memoir-capture
"""

from __future__ import annotations

import subprocess
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from PIL import Image, ImageGrab

try:
    import dxcam
except ImportError:
    dxcam = None


class InstantReplay:
    """
    即时回放管理器
    
    实现原理：
    1. 使用循环缓冲区(deque)持续缓存最近N秒的画面
    2. 用户按键时，将缓冲区内容导出为视频
    3. 使用ffmpeg进行视频编码
    
    参考: https://github.com/ra1nty/DXcam
    参考: https://github.com/tezzary/pyfastscreencap
    """

    def __init__(self) -> None:
        self._camera = None
        self._buffer: deque = deque()
        self._max_buffer_size = 0
        self._target_fps = 10
        self._is_recording = False
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._output_folder = str(Path.home() / "Pictures" / "Screenshots" / "Replay")
        
        self._screen_width = 0
        self._screen_height = 0
        self._init_camera()

    def _init_camera(self):
        """初始化DXcam相机（如果可用）"""
        if dxcam is None:
            print("Warning: dxcam not available, will use fallback capture method")
            return
        
        try:
            self._camera = dxcam.create(output_color="RGB")
            if self._camera:
                test_frame = self._camera.grab()
                if test_frame is not None:
                    self._screen_height, self._screen_width = test_frame.shape[:2]
                    print(f"DXcam initialized: {self._screen_width}x{self._screen_height}")
        except Exception as e:
            print(f"Failed to initialize DXcam: {e}")
            self._camera = None

    def set_config(self, duration: int = 5, fps: int = 10, output_folder: str = ""):
        """
        设置即时回放参数
        
        :param duration: 回放时长（秒）
        :param fps: 帧率
        :param output_folder: 输出目录
        """
        self._target_fps = fps
        self._max_buffer_size = duration * fps
        self._buffer = deque(maxlen=self._max_buffer_size)
        
        if output_folder:
            self._output_folder = output_folder
        
        Path(self._output_folder).mkdir(parents=True, exist_ok=True)
        
        print(f"Replay config: {duration}s @ {fps}fps, buffer size: {self._max_buffer_size}")

    def _capture_frame(self):
        """捕获单帧画面"""
        if self._camera:
            try:
                frame = self._camera.grab()
                if frame is not None:
                    return frame
            except Exception as e:
                print(f"DXcam capture failed: {e}")
        
        return self._fallback_capture()

    def _fallback_capture(self):
        """备用截图方法 - 使用PIL"""
        try:
            return ImageGrab.grab()
        except Exception as e:
            print(f"Fallback capture failed: {e}")
            return None

    def start(self):
        """开始持续捕获（后台线程）"""
        if self._is_recording:
            return
        
        self._is_recording = True
        self._stop_event.clear()
        self._buffer.clear()
        
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self._capture_thread.start()
        
        print("Instant replay started")

    def stop(self):
        """停止捕获"""
        self._is_recording = False
        self._stop_event.set()
        
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        
        self._buffer.clear()
        print("Instant replay stopped")

    def _capture_loop(self):
        """后台捕获循环"""
        interval = 1.0 / self._target_fps
        
        while self._is_recording and not self._stop_event.is_set():
            start_time = time.perf_counter()
            
            frame = self._capture_frame()
            if frame is not None:
                self._buffer.append(frame)
            
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, interval - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)

    def is_recording(self) -> bool:
        """检查是否正在录制"""
        return self._is_recording

    def get_buffer_size(self) -> int:
        """获取当前缓冲区帧数"""
        return len(self._buffer)

    def save_replay(self, on_progress: Optional[Callable] = None) -> bool:
        """
        保存当前缓冲区内容为视频
        
        :param on_progress: 进度回调函数 (current, total)
        :return: 是否成功
        """
        if not self._buffer:
            print("Buffer is empty")
            return False
        
        buffer_list = list(self._buffer)
        total_frames = len(buffer_list)
        
        if total_frames < 2:
            print("Not enough frames in buffer")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(self._output_folder) / f"replay_{timestamp}.mp4"
        
        return self._encode_video(buffer_list, str(output_path), on_progress)

    def _encode_video(self, frames, output_path: str, on_progress=None) -> bool:
        """
        使用ffmpeg编码视频
        
        参考: https://github.com/tezzary/pyfastscreencap
        """
        if not frames:
            return False
        
        width, height = frames[0].size
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(self._target_fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-r", str(self._target_fps),
            output_path
        ]
        
        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            total_frames = len(frames)
            for i, frame in enumerate(frames):
                try:
                    if isinstance(frame, Image.Image):
                        frame_data = frame.convert('RGB').tobytes()
                    else:
                        # numpy array (dxcam)
                        frame_data = frame.tobytes()
                    process.stdin.write(frame_data)
                    
                    if on_progress and (i + 1) % 5 == 0:
                        on_progress(i + 1, total_frames)
                except Exception as e:
                    print(f"Error writing frame {i}: {e}")
                    process.stdin.close()
                    process.wait()
                    return False
            
            process.stdin.close()
            stdout, stderr = process.communicate(timeout=30)
            
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode('utf-8', errors='ignore')}")
                return False
            
            print(f"Replay saved to: {output_path}")
            return True
            
        except FileNotFoundError:
            print("Error: ffmpeg not found in PATH")
            return False
        except subprocess.TimeoutExpired:
            print("FFmpeg encoding timed out")
            return False
        except Exception as e:
            print(f"Encoding error: {e}")
            return False

    def __del__(self):
        """安全清理：仅设置标志位，不在GC中阻塞等待线程"""
        self._is_recording = False
        self._stop_event.set()