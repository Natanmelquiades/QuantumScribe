"""Compatibilidade de UI para Windows (WS_EX_NOACTIVATE)."""

from __future__ import annotations

import ctypes
import tkinter as tk
from ctypes import wintypes

_user32 = ctypes.windll.user32
_user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongW.restype = ctypes.c_long
_user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
_user32.SetWindowLongW.restype = ctypes.c_long

_GWL_EXSTYLE = -20
_WS_EX_NOACTIVATE = 0x08000000
_WS_EX_TOOLWINDOW = 0x00000080


def make_window_no_activate(window: tk.Toplevel) -> None:
    """Configura a janela para não roubar o foco no Windows."""
    hwnd = _user32.GetParent(window.winfo_id())
    style = _user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
    style |= _WS_EX_NOACTIVATE | _WS_EX_TOOLWINDOW
    _user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, style)
