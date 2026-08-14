"""Gerenciador de Atalhos Globais no Windows."""

from __future__ import annotations

import ctypes
import threading
import time
from ctypes import wintypes
from typing import Callable

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 0xC0DE
ESCAPE_HOTKEY_ID = 0xC0DF
VK_ESCAPE = 0x1B

_VK_MAP: dict[str, int] = {
    "space": 0x20,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    _VK_MAP[_c.lower()] = ord(_c)

_MODIFIER_ALIASES = {
    "control": "ctrl",
    "windows": "win",
    "super": "win",
    "cmd": "win",
}
_MODIFIERS = {"ctrl", "alt", "shift", "win"}


def _parse_hotkey(hotkey: str) -> tuple[int, int]:
    parts = [
        _MODIFIER_ALIASES.get(part.strip().lower(), part.strip().lower())
        for part in hotkey.split("+")
    ]
    if not parts or any(not part for part in parts):
        raise ValueError(f"Atalho '{hotkey}' possui uma sintaxe inválida.")
    if len(set(parts)) != len(parts):
        raise ValueError(f"Atalho '{hotkey}' contém teclas repetidas.")

    main_keys = [part for part in parts if part not in _MODIFIERS]
    if len(main_keys) != 1:
        raise ValueError(f"Atalho '{hotkey}' deve conter exatamente uma tecla principal válida.")

    mods = 0
    vk = 0
    for part in parts:
        if part == "ctrl":
            mods |= MOD_CONTROL
        elif part == "alt":
            mods |= MOD_ALT
        elif part == "shift":
            mods |= MOD_SHIFT
        elif part in ("win", "windows"):
            mods |= MOD_WIN
        elif part in _VK_MAP:
            vk = _VK_MAP[part]
        else:
            raise ValueError(f"Tecla desconhecida no atalho: '{part}'")
    if not vk:
        raise ValueError(f"Atalho '{hotkey}' não contém uma tecla principal válida.")
    return mods, vk


def _wait_for_keys_release(mods: int, vk: int) -> None:
    user32 = ctypes.windll.user32
    vks = [vk]
    if mods & MOD_CONTROL:
        vks.append(0x11)
    if mods & MOD_ALT:
        vks.append(0x12)
    if mods & MOD_SHIFT:
        vks.append(0x10)
    if mods & MOD_WIN:
        vks.extend([0x5B, 0x5C])

    while True:
        any_pressed = False
        for k in vks:
            if user32.GetAsyncKeyState(k) & 0x8000:
                any_pressed = True
                break
        if not any_pressed:
            break
        time.sleep(0.01)

    time.sleep(0.03)


class GlobalHotkey:
    """Registra e gerencia uma hotkey global no Windows."""

    def __init__(self, hotkey: str, on_press: Callable[[], None] | None = None, on_release: Callable[[], None] | None = None) -> None:
        self.hotkey = hotkey
        self.on_press = on_press
        self.on_release = on_release
        self.thread: threading.Thread | None = None
        self.thread_id: int | None = None
        self.ready = threading.Event()
        self.error: str | None = None
        self._stop_requested = threading.Event()

    def start(self, readiness_timeout: float = 0.75) -> None:
        self.ready.clear()
        self.error = None
        self.thread_id = None
        self._stop_requested.clear()
        self.thread = threading.Thread(target=self._message_loop, daemon=True)
        self.thread.start()
        if not self.ready.wait(timeout=readiness_timeout):
            self.stop()
            raise RuntimeError(
                f"O sistema não confirmou o registro do atalho '{self.hotkey}' a tempo. "
                "Tente novamente ou escolha outra combinação."
            )
        if self.error:
            self.stop()
            raise RuntimeError(self.error)

    def stop(self) -> None:
        self._stop_requested.set()
        if self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        if self.thread:
            self.thread.join(timeout=2)
            if not self.thread.is_alive():
                self.thread = None
                self.thread_id = None

    def _message_loop(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self.thread_id = kernel32.GetCurrentThreadId()

        if self._stop_requested.is_set():
            self.ready.set()
            return

        try:
            mods, vk = _parse_hotkey(self.hotkey)
        except ValueError as exc:
            self.error = str(exc)
            self.ready.set()
            return

        if not user32.RegisterHotKey(None, HOTKEY_ID, mods | MOD_NOREPEAT, vk):
            self.error = (
                f"'{self.hotkey}' já está sendo usado por outro aplicativo. "
                "Feche o aplicativo conflitante ou altere o atalho nas Configurações."
            )
            self.ready.set()
            return

        self.ready.set()
        message = wintypes.MSG()
        try:
            if self._stop_requested.is_set():
                return
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                    if self.on_press:
                        self.on_press()

                    _wait_for_keys_release(mods, vk)

                    if self.on_release:
                        self.on_release()

                    msg_junk = wintypes.MSG()
                    while user32.PeekMessageW(ctypes.byref(msg_junk), None, WM_HOTKEY, WM_HOTKEY, 1):
                        pass
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)


class EscapeHotkey:
    """Confirma o cancelamento quando Esc permanece pressionado."""

    def __init__(
        self,
        on_press: Callable[[int | None], None] | None = None,
        on_hold: Callable[[int | None], None] | None = None,
        on_release: Callable[[int | None], None] | None = None,
        hold_seconds: float = 0.5,
    ) -> None:
        self.on_press = on_press
        self.on_hold = on_hold
        self.on_release = on_release
        self.hold_seconds = max(0.1, hold_seconds)
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()
        self._session_id: int | None = None

    def register(self, session_id: int | None = None) -> None:
        if self._thread and self._thread.is_alive():
            # Após cancelamento rápido, o WM_QUIT pode ainda estar na fila da
            # sessão anterior. Reusar o listener vivo e trocar seu token evita
            # que a nova gravação fique temporariamente sem Esc.
            self._session_id = session_id
            return
        self._session_id = session_id
        self._ready.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=1)

    def unregister(self, wait: bool = True) -> None:
        if not wait:
            # Preserva o listener até a próxima sessão para não disputar seu
            # ciclo de vida com um registro imediato. Sem sessão, callbacks
            # atrasados são descartados pelo app.
            self._session_id = None
            return
        tid = self._thread_id
        if tid:
            ctypes.windll.user32.PostThreadMessageW(tid, WM_QUIT, 0, 0)
        if wait and self._thread:
            self._thread.join(timeout=1)
        if not self._thread or not self._thread.is_alive():
            self._thread = None
            self._thread_id = None
        self._session_id = None

    def _wait_for_confirmation(self, user32: ctypes.WinDLL, session_id: int | None) -> None:
        started_at = time.monotonic()
        confirmed = False
        while user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
            if not confirmed and time.monotonic() - started_at >= self.hold_seconds:
                confirmed = True
                if self.on_hold:
                    self.on_hold(session_id)
            time.sleep(0.01)
        if self.on_release:
            self.on_release(session_id)

    def _loop(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()

        if not user32.RegisterHotKey(None, ESCAPE_HOTKEY_ID, MOD_NOREPEAT, VK_ESCAPE):
            self._ready.set()
            return

        self._ready.set()
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam == ESCAPE_HOTKEY_ID:
                    session_id = self._session_id
                    if self.on_press:
                        self.on_press(session_id)
                    self._wait_for_confirmation(user32, session_id)
        finally:
            user32.UnregisterHotKey(None, ESCAPE_HOTKEY_ID)
            self._thread_id = None
