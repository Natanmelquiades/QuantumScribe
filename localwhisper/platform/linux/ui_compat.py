"""Compatibilidade de UI para Linux."""

from __future__ import annotations

import tkinter as tk


def make_window_no_activate(window: tk.Toplevel) -> None:
    """No Linux/X11/Wayland, configura dicas de gerenciador de janelas."""
    try:
        # Define tipo de janela utilitária / splash para minimizar roubo de foco
        window.wm_attributes("-type", "utility")
    except Exception:
        pass
