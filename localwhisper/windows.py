"""Módulo de Abstração e Compatibilidade de Janelas/SO.

Este módulo re-exporta as funções de plataforma de forma transparente.
"""

from __future__ import annotations

from .platform import (
    WindowTarget,
    acquire_single_instance,
    capture_input_target,
    foreground_window,
    press_enter,
    set_clipboard_text,
    type_into_window,
)

__all__ = [
    "WindowTarget",
    "foreground_window",
    "capture_input_target",
    "acquire_single_instance",
    "set_clipboard_text",
    "type_into_window",
    "press_enter",
]
