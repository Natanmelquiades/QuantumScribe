"""Módulo de Integração com APIs Linux (X11 / Wayland / Ubuntu 24 & 26)."""

from __future__ import annotations

import fcntl
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

_lock_file_handle = None


@dataclass(frozen=True, slots=True)
class WindowTarget:
    """Representa a janela de destino no Linux."""
    window: int
    focus: int = 0


def foreground_window() -> int:
    """Retorna o ID da janela em foco no Linux (via xdotool se disponível)."""
    if shutil.which("xdotool"):
        try:
            res = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except (subprocess.SubprocessError, OSError):
            pass
    return 0


def capture_input_target() -> WindowTarget:
    """Captura a janela ativa no Linux."""
    return WindowTarget(foreground_window())


def acquire_single_instance() -> bool:
    """Garante instância única no Linux usando lockfile."""
    global _lock_file_handle
    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir()))
    lock_path = runtime_dir / f"quantumscribe-{os.getuid()}.lock"
    try:
        _lock_file_handle = open(lock_path, "w")
        fcntl.flock(_lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_file_handle.write(str(os.getpid()))
        _lock_file_handle.flush()
        return True
    except (IOError, OSError):
        return False


def set_clipboard_text(text: str) -> None:
    """Escreve texto na área de transferência no Linux usando xclip ou wl-copy."""
    # Tenta Wayland (wl-copy) se WAYLAND_DISPLAY estiver definido
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        try:
            proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-8"), timeout=2)
            return
        except (subprocess.SubprocessError, OSError):
            pass

    # Fallback X11 (xclip)
    if shutil.which("xclip"):
        try:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-8"), timeout=2)
            return
        except (subprocess.SubprocessError, OSError):
            pass

    # Fallback xsel
    if shutil.which("xsel"):
        try:
            proc = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-8"), timeout=2)
            return
        except (subprocess.SubprocessError, OSError):
            pass

    raise OSError("Nenhum utilitário de clipboard (wl-copy, xclip ou xsel) foi encontrado.")


def type_into_window(target: WindowTarget, text: str) -> bool:
    """Cola texto na janela em foco no Linux (via xdotool / ydotool / Ctrl+V)."""
    try:
        set_clipboard_text(text)
    except OSError:
        return False
    time.sleep(0.05)

    if shutil.which("xdotool"):
        try:
            subprocess.run(["xdotool", "key", "--clearmods", "ctrl+v"], check=False, timeout=2)
            return True
        except (subprocess.SubprocessError, OSError):
            pass

    if shutil.which("ydotool"):
        try:
            # ydotool key 29:1 47:1 47:0 29:0 (Ctrl+V)
            subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=False, timeout=2)
            return True
        except (subprocess.SubprocessError, OSError):
            pass

    return False


def press_enter() -> None:
    """Simula o pressionamento da tecla Enter no Linux."""
    time.sleep(0.08)
    if shutil.which("xdotool"):
        try:
            subprocess.run(["xdotool", "key", "Return"], check=False, timeout=2)
            return
        except (subprocess.SubprocessError, OSError):
            pass

    if shutil.which("ydotool"):
        try:
            subprocess.run(["ydotool", "key", "28:1", "28:0"], check=False, timeout=2)
            return
        except (subprocess.SubprocessError, OSError):
            pass


def wait_for_process_exit(pid: int, timeout_ms: int = 15000) -> None:
    """Aguarda o encerramento do processo com o PID informado no Linux."""
    if pid <= 0:
        return
    start = time.monotonic()
    timeout_sec = timeout_ms / 1000.0
    while time.monotonic() - start < timeout_sec:
        try:
            os.kill(pid, 0)
            time.sleep(0.1)
        except OSError:
            break
