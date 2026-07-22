"""Plataforma Abstração de SO para QuantumScribe."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.hotkey import EscapeHotkey, GlobalHotkey, _parse_hotkey
    from .windows.ui_compat import make_window_no_activate
    from .windows.windows_api import (
        WindowTarget,
        acquire_single_instance,
        capture_input_target,
        foreground_window,
        press_enter,
        set_clipboard_text,
        type_into_window,
        wait_for_process_exit,
    )
else:
    from .linux.hotkey import EscapeHotkey, GlobalHotkey, _parse_hotkey
    from .linux.ui_compat import make_window_no_activate
    from .linux.windows_api import (
        WindowTarget,
        acquire_single_instance,
        capture_input_target,
        foreground_window,
        press_enter,
        set_clipboard_text,
        type_into_window,
        wait_for_process_exit,
    )

__all__ = [
    "WindowTarget",
    "foreground_window",
    "capture_input_target",
    "acquire_single_instance",
    "set_clipboard_text",
    "type_into_window",
    "press_enter",
    "wait_for_process_exit",
    "GlobalHotkey",
    "EscapeHotkey",
    "_parse_hotkey",
    "make_window_no_activate",
]
