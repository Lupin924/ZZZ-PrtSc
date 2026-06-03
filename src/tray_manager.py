#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘管理器 - Win32原生API实现
"""

from __future__ import annotations

import ctypes
import threading
from typing import Callable, Optional, List, Tuple

from PIL import Image


class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint32),
        ('hWnd', ctypes.c_void_p),
        ('uID', ctypes.c_uint32),
        ('uFlags', ctypes.c_uint32),
        ('uCallbackMessage', ctypes.c_uint32),
        ('hIcon', ctypes.c_void_p),
        ('szTip', ctypes.c_wchar * 128),
    ]


class MENUITEMINFOW(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint32),
        ('fMask', ctypes.c_uint32),
        ('fType', ctypes.c_uint32),
        ('fState', ctypes.c_uint32),
        ('wID', ctypes.c_uint32),
        ('hSubMenu', ctypes.c_void_p),
        ('hbmpChecked', ctypes.c_void_p),
        ('hbmpUnchecked', ctypes.c_void_p),
        ('dwItemData', ctypes.c_ulonglong),
        ('dwTypeData', ctypes.c_wchar_p),
        ('cch', ctypes.c_uint32),
        ('hbmpItem', ctypes.c_void_p),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ('hwnd', ctypes.c_void_p),
        ('message', ctypes.c_uint),
        ('wParam', ctypes.c_void_p),
        ('lParam', ctypes.c_void_p),
        ('time', ctypes.c_uint32),
        ('pt', ctypes.c_long * 2),
    ]


LP_MSG = ctypes.POINTER(MSG)


NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
MIIM_TYPE = 0x00000010
MIIM_ID = 0x00000002
MIIM_STATE = 0x00000001
MFT_STRING = 0x00000000
MFS_ENABLED = 0x00000000
MFS_DISABLED = 0x00000003
TPM_LEFTALIGN = 0x0000
TPM_BOTTOMALIGN = 0x0020
TPM_RIGHTBUTTON = 0x0002
WM_TRAYICON = 0x8001
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203
WM_CLOSE = 0x0010
WM_COMMAND = 0x0111

MF_STRING = 0x00000000
MF_ENABLED = 0x00000000
MF_DISABLED = 0x00000002


def _create_simple_icon() -> int:
    """创建简单图标 - 使用系统图标作为基础"""
    _user32 = ctypes.windll.user32
    hicon = _user32.LoadIconW(None, 32512)  # IDI_APPLICATION
    if hicon:
        return hicon
    
    hicon = _user32.LoadIconW(None, 32513)  # IDI_HAND
    if hicon:
        return hicon
        
    hicon = _user32.LoadIconW(None, 32514)  # IDI_QUESTION
    if hicon:
        return hicon
        
    hicon = _user32.LoadIconW(None, 32515)  # IDI_EXCLAMATION
    if hicon:
        return hicon
        
    return None


class TrayMenuItem:
    __slots__ = ('text', 'callback', 'item_id', 'enabled')

    def __init__(self, text: str, callback: Optional[Callable] = None, item_id: int = 0, enabled: bool = True):
        self.text = text
        self.callback = callback
        self.item_id = item_id
        self.enabled = enabled


class Win32TrayManager:
    _MENU_ID_BASE = 1000

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._hwnd: Optional[int] = None
        self._hicon: Optional[int] = None
        self._notify_id: Optional[int] = None
        self._menu_items: List[TrayMenuItem] = []
        self._tooltip: str = ""
        self._ready_event = threading.Event()
        self._on_double_click: Optional[Callable] = None
        # 使用 WinDLL 加载 DLL（Windows API 使用 stdcall 调用约定）
        # 创建完全独立的实例，避免与其他模块的 argtypes 设置冲突
        self.user32 = ctypes.WinDLL('user32.dll')
        self.kernel32 = ctypes.WinDLL('kernel32.dll')
        self.shell32 = ctypes.WinDLL('shell32.dll')
        self.gdi32 = ctypes.WinDLL('gdi32.dll')

    def setup(self, icon_image: Image.Image, tooltip: str,
              menu_items: List[Tuple[str, Optional[Callable]]],
              on_double_click: Optional[Callable] = None) -> bool:
        self._tooltip = tooltip[:127]
        self._on_double_click = on_double_click

        self._menu_items = []
        for i, (text, callback) in enumerate(menu_items):
            self._menu_items.append(TrayMenuItem(
                text=text, callback=callback,
                item_id=self._MENU_ID_BASE + i, enabled=callback is not None))

        self._thread = threading.Thread(target=self._run, daemon=True, name="TrayManager")
        self._thread.start()
        return self._ready_event.wait(timeout=5.0)

    def update_icon(self, icon_image: Image.Image):
        """更新托盘图标"""
        if not self._hwnd or not self._notify_id:
            return

        hicon = self._image_to_hicon(icon_image)
        if not hicon:
            print("图标转换失败")
            return

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = self._notify_id
        nid.uFlags = NIF_ICON
        nid.hIcon = hicon
        
        if self.shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid)):
            if self._hicon and self._hicon != hicon:
                self.user32.DestroyIcon(self._hicon)
            self._hicon = hicon
        else:
            print(f"更新图标失败，错误码: {self.kernel32.GetLastError()}")
            self.user32.DestroyIcon(hicon)

    def _image_to_hicon(self, image: Image.Image) -> int:
        """将 PIL Image 转换为 Windows HICON"""
        try:
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            width, height = image.size
            pixels = image.tobytes()

            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ('biSize', ctypes.c_uint32),
                    ('biWidth', ctypes.c_int),
                    ('biHeight', ctypes.c_int),
                    ('biPlanes', ctypes.c_uint16),
                    ('biBitCount', ctypes.c_uint16),
                    ('biCompression', ctypes.c_uint32),
                    ('biSizeImage', ctypes.c_uint32),
                    ('biXPelsPerMeter', ctypes.c_int),
                    ('biYPelsPerMeter', ctypes.c_int),
                    ('biClrUsed', ctypes.c_uint32),
                    ('biClrImportant', ctypes.c_uint32),
                ]

            class ICONINFO(ctypes.Structure):
                _fields_ = [
                    ('fIcon', ctypes.c_bool),
                    ('xHotspot', ctypes.c_uint),
                    ('yHotspot', ctypes.c_uint),
                    ('hbmMask', ctypes.c_void_p),
                    ('hbmColor', ctypes.c_void_p),
                ]

            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = width
            bmi.biHeight = -height
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0

            hdc = self.user32.GetDC(None)
            hbitmap = self.gdi32.CreateDIBSection(
                hdc, ctypes.byref(bmi), 0, ctypes.c_void_p(), None, 0
            )
            
            if not hbitmap:
                self.user32.ReleaseDC(None, hdc)
                return None

            hdc_mem = self.gdi32.CreateCompatibleDC(hdc)
            old_bitmap = self.gdi32.SelectObject(hdc_mem, hbitmap)

            self.gdi32.SetDIBits(hdc, hbitmap, 0, height, pixels, ctypes.byref(bmi), 0)
            self.gdi32.SelectObject(hdc_mem, old_bitmap)
            self.gdi32.DeleteDC(hdc_mem)

            icon_info = ICONINFO()
            icon_info.fIcon = True
            icon_info.xHotspot = 0
            icon_info.yHotspot = 0
            icon_info.hbmMask = hbitmap
            icon_info.hbmColor = hbitmap

            hicon = self.user32.CreateIconIndirect(ctypes.byref(icon_info))
            self.gdi32.DeleteObject(hbitmap)
            self.user32.ReleaseDC(None, hdc)

            return hicon

        except Exception as e:
            print(f"图像转换失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_tooltip(self, tooltip: str):
        self._tooltip = tooltip[:127]
        if self._hwnd and self._notify_id:
            self._update_tooltip_internal()

    def update_menu(self, menu_items: List[Tuple[str, Optional[Callable]]]):
        self._menu_items = []
        for i, (text, callback) in enumerate(menu_items):
            self._menu_items.append(TrayMenuItem(
                text=text, callback=callback,
                item_id=self._MENU_ID_BASE + i, enabled=callback is not None))

    def stop(self):
        self._stop_event.set()
        if self._hwnd:
            self.user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)

    def _WndProc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            lparam_val = ctypes.c_longlong(lparam).value
            low = lparam_val & 0xFFFF
            
            if low == WM_RBUTTONUP:
                self._show_menu()
            elif low == WM_LBUTTONDBLCLK:
                if self._on_double_click:
                    try:
                        self._on_double_click()
                    except:
                        pass
            return 0
        elif msg == WM_COMMAND:
            menu_id = ctypes.c_longlong(wparam).value & 0xFFFF
            for item in self._menu_items:
                if item.item_id == menu_id and item.callback:
                    try:
                        item.callback()
                    except Exception:
                        pass
                    break
            return 0
        elif msg == WM_CLOSE:
            self.user32.PostQuitMessage(0)
            return 0
        try:
            return self.user32.DefWindowProcW(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(msg),
                ctypes.c_void_p(wparam),
                ctypes.c_void_p(lparam)
            )
        except:
            return 0

    def _run(self):
        h_instance = self.kernel32.GetModuleHandleW(None)

        WNDPROC_TYPE = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_void_p
        )
        # 保存为实例变量，防止被垃圾回收
        self._wndproc_func = WNDPROC_TYPE(self._WndProc)
        wndproc_func = self._wndproc_func

        class WNDCLASSEX(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.c_uint32),
                ('style', ctypes.c_uint32),
                ('lpfnWndProc', ctypes.c_void_p),
                ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int),
                ('hInstance', ctypes.c_void_p),
                ('hIcon', ctypes.c_void_p),
                ('hCursor', ctypes.c_void_p),
                ('hbrBackground', ctypes.c_void_p),
                ('lpszMenuName', ctypes.c_void_p),
                ('lpszClassName', ctypes.c_wchar_p),
                ('hIconSm', ctypes.c_void_p),
            ]

        class_name = "ZZZPrtScTray"

        wnd_class = WNDCLASSEX()
        wnd_class.cbSize = ctypes.sizeof(WNDCLASSEX)
        wnd_class.style = 0
        wnd_class.lpfnWndProc = ctypes.cast(wndproc_func, ctypes.c_void_p)
        wnd_class.cbClsExtra = 0
        wnd_class.cbWndExtra = 0
        wnd_class.hInstance = h_instance
        wnd_class.hIcon = None
        wnd_class.hCursor = None
        wnd_class.hbrBackground = None
        wnd_class.lpszMenuName = None
        wnd_class.lpszClassName = class_name
        wnd_class.hIconSm = None

        if not self.user32.RegisterClassExW(ctypes.byref(wnd_class)):
            print(f"窗口类注册失败: {self.kernel32.GetLastError()}")
            return

        self._hwnd = self.user32.CreateWindowExW(
            0, class_name, None, 0, 0, 0, 0, 0,
            None, None, h_instance, None)

        if not self._hwnd:
            print(f"窗口创建失败: {self.kernel32.GetLastError()}")
            return

        if not self._add_icon():
            print("托盘图标添加失败")
            return

        self._ready_event.set()

        msg = MSG()
        msg_ptr = ctypes.cast(ctypes.byref(msg), LP_MSG)
        while not self._stop_event.is_set():
            ret = self.user32.GetMessageW(msg_ptr, None, 0, 0)
            if ret == 0 or ret == -1:
                break
            self.user32.TranslateMessage(msg_ptr)
            self.user32.DispatchMessageW(msg_ptr)

        self._cleanup()
        if self._hwnd:
            self.user32.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _add_icon(self) -> bool:
        self._hicon = _create_simple_icon()

        if not self._hicon:
            print("图标加载失败")
            return False

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self._hicon
        nid.szTip = self._tooltip

        self._notify_id = 1
        return bool(self.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)))

    def _update_tooltip_internal(self):
        if not self._hwnd or not self._notify_id:
            return

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = self._notify_id
        nid.uFlags = NIF_TIP
        nid.szTip = self._tooltip
        self.shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def _cleanup(self):
        if self._hwnd and self._notify_id:
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd = self._hwnd
            nid.uID = self._notify_id
            self.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            self._notify_id = None
        if self._hicon:
            self.user32.DestroyIcon(self._hicon)
            self._hicon = None

    def _show_menu(self):
        """显示右键菜单"""
        hmenu = self.user32.CreatePopupMenu()
        if not hmenu:
            return

        for item in self._menu_items:
            flags = MF_STRING | (MF_ENABLED if item.enabled else MF_DISABLED)
            self.user32.AppendMenuW(hmenu, flags, item.item_id, ctypes.c_wchar_p(item.text))

        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        self.user32.SetForegroundWindow(self._hwnd)
        
        self.user32.TrackPopupMenu(
            hmenu, 
            TPM_LEFTALIGN | TPM_BOTTOMALIGN | TPM_RIGHTBUTTON, 
            pt.x, pt.y, 
            0, 
            self._hwnd, 
            None
        )
        
        self.user32.DestroyMenu(hmenu)
