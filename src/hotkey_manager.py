#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局热键管理器
使用Windows API注册全局热键，拦截PrintScreen键（ZZZ PrtSc）
"""

from __future__ import annotations

import ctypes
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Windows API 常量
WM_QUIT = 0x0012
VK_SNAPSHOT = 0x2C
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
LLKHF_ALTDOWN = 0x20

# 超时设置
HOOK_INSTALL_TIMEOUT_S = 3.0


# 基本类型定义
DWORD = ctypes.c_ulong
BOOL = ctypes.c_int
UINT = ctypes.c_uint
INT = ctypes.c_int
WPARAM = ctypes.c_ulonglong  # 64位
LPARAM = ctypes.c_ulonglong  # 64位
LRESULT = ctypes.c_longlong  # 64位有符号
HHOOK = ctypes.c_void_p
HINSTANCE = ctypes.c_void_p
HWND = ctypes.c_void_p


class KBDLLHOOKSTRUCT(ctypes.Structure):
    """键盘钩子结构体"""
    _fields_ = [
        ("vkCode", DWORD),
        ("scanCode", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class MSG(ctypes.Structure):
    """Windows消息结构体"""
    _fields_ = [
        ("hwnd", HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", ctypes.c_long * 2),  # POINT结构简化
    ]


# 定义回调函数类型
HOOKPROC = ctypes.WINFUNCTYPE(
    LRESULT,   # 返回类型
    INT,       # nCode
    WPARAM,    # wParam
    LPARAM,    # lParam
)


class HotkeyManager:
    """全局热键管理器"""

    __slots__ = (
        "signal_bridge", "is_running", "hook_thread", "hHook",
        "_hook_installed_event", "_stop_event", "user32", "kernel32",
        "_hook_proc_ref", "_hook_thread_id"
    )

    def __init__(self, signal_bridge) -> None:
        """初始化热键管理器"""
        self.signal_bridge = signal_bridge
        self.is_running = False
        self.hook_thread: threading.Thread | None = None
        self.hHook = None

        # 同步事件
        self._hook_installed_event = threading.Event()
        self._stop_event = threading.Event()

        # Windows API DLL
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        # 设置API参数类型
        self._setup_api_types()

        # 回调函数引用保持
        self._hook_proc_ref = None
        self._hook_thread_id = 0

    def _setup_api_types(self) -> None:
        """设置Windows API函数参数类型"""
        # SetWindowsHookExW
        self.user32.SetWindowsHookExW.argtypes = [
            INT,        # idHook
            HOOKPROC,   # lpfn
            HINSTANCE,  # hMod
            DWORD,      # dwThreadId
        ]
        self.user32.SetWindowsHookExW.restype = HHOOK

        # UnhookWindowsHookEx
        self.user32.UnhookWindowsHookEx.argtypes = [HHOOK]
        self.user32.UnhookWindowsHookEx.restype = BOOL

        # CallNextHookEx
        self.user32.CallNextHookEx.argtypes = [
            HHOOK,   # hhk
            INT,     # nCode
            WPARAM,  # wParam
            LPARAM,  # lParam
        ]
        self.user32.CallNextHookEx.restype = LRESULT

        # PeekMessageW
        self.user32.PeekMessageW.argtypes = [
            ctypes.POINTER(MSG),
            HWND,
            UINT,
            UINT,
            UINT,
        ]
        self.user32.PeekMessageW.restype = BOOL

        # TranslateMessage
        self.user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
        self.user32.TranslateMessage.restype = BOOL

        # DispatchMessageW
        self.user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
        self.user32.DispatchMessageW.restype = LRESULT

        # WaitMessage
        self.user32.WaitMessage.argtypes = []
        self.user32.WaitMessage.restype = BOOL

        # GetLastError
        self.kernel32.GetLastError.argtypes = []
        self.kernel32.GetLastError.restype = DWORD

    def start(self) -> bool:
        """启动热键监听"""
        if self.is_running:
            return True

        try:
            self._hook_installed_event.clear()
            self._stop_event.clear()

            self.hook_thread = threading.Thread(target=self._hook_thread, daemon=True)
            self.hook_thread.start()

            if self._hook_installed_event.wait(timeout=HOOK_INSTALL_TIMEOUT_S):
                self.is_running = True
                return True
            else:
                return False

        except Exception:
            return False

    def stop(self) -> None:
        """停止热键监听"""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()

        if self.hHook:
            try:
                self.user32.UnhookWindowsHookEx(self.hHook)
                self.hHook = None
            except Exception:
                pass

        if self._hook_thread_id:
            self.user32.PostThreadMessageW(self._hook_thread_id, WM_QUIT, 0, 0)

        if self.hook_thread and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=2.0)

    def _hook_thread(self) -> None:
        """钩子线程"""

        # 创建回调函数
        @HOOKPROC
        def keyboard_proc(nCode, wParam, lParam):
            """键盘钩子回调函数"""
            # nCode < 0 时必须直接传递给下一个钩子
            if nCode < 0:
                return self.user32.CallNextHookEx(None, nCode, wParam, lParam)

            try:
                # 获取键盘数据
                kb_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

                # 只处理PrintScreen键
                if kb_struct.vkCode == VK_SNAPSHOT:
                    # 检查是否是按下事件
                    if wParam == WM_KEYDOWN or wParam == WM_SYSKEYDOWN:
                        # 检查是否按下了Alt键（Alt+PrintScreen是系统功能，不拦截）
                        is_alt_down = (kb_struct.flags & LLKHF_ALTDOWN) != 0

                        if not is_alt_down:
                            print("PrintScreen键被按下，ZZZ PrtSc执行截图")
                            self.signal_bridge.emit_screenshot()
                            return 1  # 拦截该按键
            except Exception as e:
                print(f"键盘钩子处理异常: {e}")

            # 传递给下一个钩子
            return self.user32.CallNextHookEx(None, nCode, wParam, lParam)

        # 保持回调函数引用
        self._hook_proc_ref = keyboard_proc

        # 安装低级键盘钩子
        self.hHook = self.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc_ref,
            None,  # hMod 必须为 NULL
            0      # 0 表示全局钩子
        )

        if not self.hHook:
            error_code = self.kernel32.GetLastError()
            print(f"安装键盘钩子失败，错误码: {error_code}")
            return

        print("键盘钩子安装成功")
        self._hook_installed_event.set()

        self._hook_thread_id = self.kernel32.GetCurrentThreadId()

        msg = MSG()
        PM_REMOVE = 0x0001

        while not self._stop_event.is_set():
            ret = self.user32.GetMessageW(
                ctypes.byref(msg),
                None,
                0,
                0,
            )
            if ret == 0 or ret == -1:
                break
            if self._stop_event.is_set():
                break
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        if self.hHook:
            self.user32.UnhookWindowsHookEx(self.hHook)
            self.hHook = None

        print("钩子线程结束")
