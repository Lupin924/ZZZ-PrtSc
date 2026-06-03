#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手柄管理器模块 - 使用 Windows 原生 API (winmm) 检测手柄
支持: PS5 DualSense, Xbox Series, Switch Pro 等主流手柄
无需额外依赖库
"""

from __future__ import annotations

import ctypes
import threading
import time
from ctypes import wintypes
from typing import Optional

# ─── winmm API ───────────────────────────────────────────────
_winmm = ctypes.windll.winmm

MAXPNAMELEN = 32
JOY_RETURNBUTTONS = 0x80
MMSYSERR_NOERROR = 0
JOYERR_NOERROR = 0

# XInput constants
XINPUT_USER_MAX = 4
XINPUT_GAMEPAD_SHARE = 0x2000  # Xbox Series Share button



class JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("dwXpos", wintypes.DWORD),
        ("dwYpos", wintypes.DWORD),
        ("dwZpos", wintypes.DWORD),
        ("dwRpos", wintypes.DWORD),
        ("dwUpos", wintypes.DWORD),
        ("dwVpos", wintypes.DWORD),
        ("dwButtons", wintypes.DWORD),
        ("dwButtonNumber", wintypes.DWORD),
        ("dwPOV", wintypes.DWORD),
        ("dwReserved1", wintypes.DWORD),
        ("dwReserved2", wintypes.DWORD),
    ]


class JOYCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("szPname", ctypes.c_char * MAXPNAMELEN),
        ("wXmin", wintypes.UINT),
        ("wXmax", wintypes.UINT),
        ("wYmin", wintypes.UINT),
        ("wYmax", wintypes.UINT),
        ("wZmin", wintypes.UINT),
        ("wZmax", wintypes.UINT),
        ("wNumButtons", wintypes.UINT),
        ("wPeriodMin", wintypes.UINT),
        ("wPeriodMax", wintypes.UINT),
        ("wRmin", wintypes.UINT),
        ("wRmax", wintypes.UINT),
        ("wUmin", wintypes.UINT),
        ("wUmax", wintypes.UINT),
        ("wVmin", wintypes.UINT),
        ("wVmax", wintypes.UINT),
        ("wCaps", wintypes.UINT),
        ("wMaxAxes", wintypes.UINT),
        ("wNumAxes", wintypes.UINT),
        ("wMaxButtons", wintypes.UINT),
        ("szRegKey", ctypes.c_char * 32),
        ("szOEMVxD", ctypes.c_char * 260),
    ]


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_byte),
        ("bRightTrigger", ctypes.c_byte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


# ─── API function signatures ─────────────────────────────────
_joy_get_num_devs = _winmm.joyGetNumDevs
_joy_get_num_devs.restype = wintypes.UINT

_joy_get_dev_caps = _winmm.joyGetDevCapsA
_joy_get_dev_caps.argtypes = [wintypes.UINT, ctypes.POINTER(JOYCAPS), wintypes.UINT]
_joy_get_dev_caps.restype = wintypes.UINT

_joy_get_pos_ex = _winmm.joyGetPosEx
_joy_get_pos_ex.argtypes = [wintypes.UINT, ctypes.POINTER(JOYINFOEX)]
_joy_get_pos_ex.restype = wintypes.UINT

# XInput - dynamically load
_xinput = None
_xinput_get_state = None
try:
    _xinput = ctypes.windll.xinput1_4
except OSError:
    try:
        _xinput = ctypes.windll.xinput1_3
    except OSError:
        _xinput = None

if _xinput:
    _xinput_get_state = _xinput.XInputGetState
    _xinput_get_state.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
    _xinput_get_state.restype = wintypes.DWORD


def _detect_controllers_winmm():
    """使用 winmm 检测传统 DirectInput 手柄"""
    controllers = []
    max_devs = _joy_get_num_devs()
    for dev_id in range(max_devs):
        caps = JOYCAPS()
        result = _joy_get_dev_caps(dev_id, ctypes.byref(caps), ctypes.sizeof(JOYCAPS))
        if result == MMSYSERR_NOERROR:
            name = caps.szPname.decode('gbk', errors='replace').strip('\x00').strip()
            if name:
                controllers.append({
                    'id': dev_id,
                    'name': name,
                    'num_buttons': caps.wNumButtons,
                    'max_buttons': caps.wMaxButtons,
                    'api': 'winmm',
                })
    return controllers


def _detect_controllers_xinput():
    """使用 XInput 检测 Xbox 手柄"""
    controllers = []
    if not _xinput_get_state:
        return controllers
    for user_id in range(XINPUT_USER_MAX):
        state = XINPUT_STATE()
        result = _xinput_get_state(user_id, ctypes.byref(state))
        if result == 0:
            controllers.append({
                'id': user_id,
                'name': f'Xbox Controller {user_id + 1}',
                'num_buttons': 16,
                'max_buttons': 16,
                'api': 'xinput',
            })
    return controllers


def _poll_buttons_winmm(dev_id: int) -> int:
    """通过 winmm 获取手柄按钮状态 (bitmask)"""
    info = JOYINFOEX()
    info.dwSize = ctypes.sizeof(JOYINFOEX)
    info.dwFlags = JOY_RETURNBUTTONS
    result = _joy_get_pos_ex(dev_id, ctypes.byref(info))
    if result == JOYERR_NOERROR:
        return info.dwButtons
    return 0


def _poll_buttons_xinput(user_id: int) -> int:
    """通过 XInput 获取 Xbox 手柄按钮状态 (bitmask)"""
    if not _xinput_get_state:
        return 0
    state = XINPUT_STATE()
    result = _xinput_get_state(user_id, ctypes.byref(state))
    if result == 0:
        return state.Gamepad.wButtons
    return 0


class GamepadManager:
    """手柄管理器 - 使用 Windows 原生 API 检测手柄输入"""

    DETECT_TIMEOUT = 2.0
    SCAN_INTERVAL = 0.1

    _XINPUT_BUTTON_BITS = [
        0x0001,  # A
        0x0002,  # B
        0x0004,  # X
        0x0008,  # Y
        0x0010,  # LEFT_BUMPER
        0x0020,  # RIGHT_BUMPER
        0x0040,  # LEFT_THUMB
        0x0080,  # RIGHT_THUMB
        0x0100,  # BACK
        0x0200,  # START
        0x1000,  # DPAD_UP
        0x2000,  # DPAD_DOWN
        0x4000,  # DPAD_LEFT
        0x8000,  # DPAD_RIGHT
    ]

    def __init__(self, signal_bridge) -> None:
        self.signal_bridge = signal_bridge
        self.is_running = False
        self.gamepad_type = None
        self.gamepad_name = "Unknown Controller"
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._connected = False
        self._api = None
        self._dev_id = 0
        self._last_button_states = []
        self._share_button_indices = [8, 10]
        self._scanning = False
        self._scan_complete = threading.Event()
        self._on_status_change = None

    def start(self, scan_on_start: bool = True) -> bool:
        """启动手柄管理器"""
        if self.is_running:
            return True

        try:
            self._stop_event.clear()

            if scan_on_start:
                self._detect_with_timeout()

            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="GamepadMonitor"
            )
            self._monitor_thread.start()
            self.is_running = True

            return True

        except Exception as e:
            print(f"手柄启动失败: {e}")
            return False

    def stop(self) -> None:
        """停止手柄管理器"""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()
        self._scan_complete.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

    def _detect_with_timeout(self) -> bool:
        """带超时的手柄检测"""
        self._scanning = True
        self._scan_complete.clear()

        start_time = time.time()
        detected = False

        while time.time() - start_time < self.DETECT_TIMEOUT:
            if self._detect_once():
                detected = True
                break
            time.sleep(self.SCAN_INTERVAL)

        self._scanning = False
        self._scan_complete.set()
        return detected

    def _detect_once(self) -> bool:
        """单次检测手柄"""
        try:
            # 先检测 XInput (Xbox 手柄)
            xinput_ctrls = _detect_controllers_xinput()
            for ctrl in xinput_ctrls:
                self._api = 'xinput'
                self._dev_id = ctrl['id']
                self._connected = True
                self.gamepad_name = ctrl['name']
                self.gamepad_type = 'xbox'
                self._share_button_indices = [10]
                self._last_button_states = self._init_xinput_button_states()
                return True

            # 再检测 winmm (PS5, Switch Pro 等)
            winmm_ctrls = _detect_controllers_winmm()
            for ctrl in winmm_ctrls:
                name = ctrl['name']
                self._api = 'winmm'
                self._dev_id = ctrl['id']
                self._connected = True
                self.gamepad_name = name

                if 'Sony' in name or 'DualSense' in name or 'PS5' in name:
                    self.gamepad_type = 'ps5'
                    self._share_button_indices = [8]
                elif 'Switch' in name or 'Pro' in name:
                    self.gamepad_type = 'switch'
                    self._share_button_indices = [8]
                else:
                    self.gamepad_type = 'generic'
                    self._share_button_indices = [8, 10]

                self._last_button_states = [False] * ctrl['num_buttons']
                return True

        except Exception as e:
            print(f"手柄单次检测异常: {e}")

        return False

    def _init_xinput_button_states(self) -> list:
        """初始化 XInput 按钮状态列表"""
        return [False] * len(self._XINPUT_BUTTON_BITS)

    def _monitor_loop(self) -> None:
        """监控循环 - 检测手柄连接状态和截图按钮"""
        check_count = 0
        check_interval = 50

        while not self._stop_event.is_set():
            try:
                if self._connected:
                    self._check_buttons()
                    check_count += 1
                    if check_count >= check_interval:
                        check_count = 0
                        if not self._is_controller_still_connected():
                            self._handle_disconnect()

                self._stop_event.wait(timeout=0.02)

            except Exception as e:
                print(f"手柄监控循环异常: {e}")
                self._connected = False
                self._notify_status_change()
                time.sleep(0.5)

    def _handle_disconnect(self):
        """处理手柄断开连接"""
        self._connected = False
        self.gamepad_type = None
        self.gamepad_name = "Unknown Controller"
        self._api = None
        self._last_button_states = []
        self._notify_status_change()

    def _notify_status_change(self):
        """通知UI状态变化"""
        if self._on_status_change:
            try:
                self._on_status_change()
            except Exception:
                pass

    def _is_controller_still_connected(self) -> bool:
        """检查手柄是否仍然连接"""
        try:
            if self._api == 'xinput':
                ctrls = _detect_controllers_xinput()
                return any(c['id'] == self._dev_id for c in ctrls)
            elif self._api == 'winmm':
                ctrls = _detect_controllers_winmm()
                return any(c['id'] == self._dev_id for c in ctrls)
        except Exception:
            pass
        return False

    def _check_buttons(self):
        """检查按钮状态"""
        try:
            button_bitmask = 0

            if self._api == 'xinput':
                button_bitmask = _poll_buttons_xinput(self._dev_id)
                self._check_xinput_buttons(button_bitmask)
            elif self._api == 'winmm':
                button_bitmask = _poll_buttons_winmm(self._dev_id)
                self._check_winmm_buttons(button_bitmask)

        except Exception as e:
            print(f"检查手柄按钮时出错: {e}")

    def _check_winmm_buttons(self, button_bitmask: int):
        """检测 winmm 手柄的按钮变化"""
        num_buttons = len(self._last_button_states)
        for i in range(num_buttons):
            current_state = bool(button_bitmask & (1 << i))
            if current_state != self._last_button_states[i]:
                self._last_button_states[i] = current_state
                if current_state and i in self._share_button_indices:
                    self._emit_screenshot()

    def _check_xinput_buttons(self, button_bitmask: int):
        """检测 XInput 手柄的按钮变化"""
        for i, bit in enumerate(self._XINPUT_BUTTON_BITS):
            if i >= len(self._last_button_states):
                break
            current_state = bool(button_bitmask & bit)
            if current_state != self._last_button_states[i]:
                self._last_button_states[i] = current_state
                if current_state and i in self._share_button_indices:
                    self._emit_screenshot()

    def _emit_screenshot(self) -> None:
        """触发截图"""
        if self.signal_bridge:
            self.signal_bridge.emit_screenshot()

    def get_connected_gamepad_info(self) -> dict:
        """获取手柄连接信息"""
        info = {
            'connected': self._connected,
            'type': self.gamepad_type,
            'name': self.gamepad_name if self._connected else None,
            'num_buttons': len(self._last_button_states) if self._connected else 0,
            'scanning': self._scanning,
        }
        return info

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def is_scanning(self) -> bool:
        """检查是否正在扫描"""
        return self._scanning

    def re_detect_joystick(self) -> bool:
        """手动重新检测手柄连接状态（带超时）"""
        if self._scanning:
            return False

        self._connected = False
        self._api = None
        self.gamepad_type = None
        self.gamepad_name = "Unknown Controller"
        self._last_button_states = []

        result = self._detect_with_timeout()
        self._notify_status_change()
        return result
