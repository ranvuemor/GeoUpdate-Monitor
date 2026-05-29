from __future__ import annotations

import ctypes
import platform
import time
from ctypes import wintypes
from typing import Callable


def idle_minutes_to_seconds(minutes: float) -> float:
    if minutes < 0:
        raise ValueError("Idle minutes must be zero or greater.")
    return minutes * 60.0


def get_idle_seconds() -> float | None:
    if platform.system() != "Windows":
        return None
    return _get_windows_idle_seconds()


def wait_until_idle(
    idle_seconds_required: float,
    check_interval_seconds: float,
    get_idle_seconds_fn: Callable[[], float | None] = get_idle_seconds,
    sleep_fn: Callable[[float], None] = time.sleep,
    print_fn: Callable[[str], None] = print,
) -> None:
    if idle_seconds_required < 0:
        raise ValueError("Required idle seconds must be zero or greater.")
    if check_interval_seconds < 0:
        raise ValueError("Idle check interval must be zero or greater.")

    required_minutes = idle_seconds_required / 60.0
    print_fn(f"Waiting until system is idle for {required_minutes:g} minutes...")

    while True:
        idle_seconds = get_idle_seconds_fn()
        if idle_seconds is None:
            raise RuntimeError("System idle detection is not supported on this platform.")

        idle_minutes = idle_seconds / 60.0
        print_fn(f"Current idle time: {idle_minutes:.1f} minutes")
        if idle_seconds >= idle_seconds_required:
            print_fn("Idle threshold reached. Starting checks.")
            return

        sleep_fn(check_interval_seconds)


class _LastInputInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def _get_windows_idle_seconds() -> float:
    last_input_info = _LastInputInfo()
    last_input_info.cbSize = ctypes.sizeof(_LastInputInfo)

    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        raise ctypes.WinError()

    ctypes.windll.kernel32.GetTickCount64.restype = ctypes.c_ulonglong
    tick_count = ctypes.windll.kernel32.GetTickCount64()
    idle_milliseconds = tick_count - last_input_info.dwTime
    return max(0.0, idle_milliseconds / 1000.0)
