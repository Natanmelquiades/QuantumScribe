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

# Mapeamento de nomes de teclas para Virtual-Key codes
_VK_MAP: dict[str, int] = {
    "space": 0x20,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    _VK_MAP[_c.lower()] = ord(_c)


def _parse_hotkey(hotkey: str) -> tuple[int, int]:
    """Converte 'Ctrl+Space' em (modifiers, vk_code)."""
    parts = [p.strip().lower() for p in hotkey.split("+")]
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
    """Aguarde até que todas as teclas físicas do atalho associado sejam liberadas no Windows.

    Isso garante que a ação correspondente (iniciar/finalizar gravação) seja
    desencadeada somente no Keyup (quando o usuário retira a mão das teclas).
    """
    user32 = ctypes.windll.user32
    vks = [vk]

    # Mapeia modificadores para seus respectivos Virtual-Key codes físicos
    if mods & MOD_CONTROL:
        vks.append(0x11)  # VK_CONTROL
    if mods & MOD_ALT:
        vks.append(0x12)  # VK_MENU (Alt)
    if mods & MOD_SHIFT:
        vks.append(0x10)  # VK_SHIFT
    if mods & MOD_WIN:
        vks.extend([0x5B, 0x5C])  # VK_LWIN, VK_RWIN

    while True:
        any_pressed = False
        for k in vks:
            # 0x8000 indica que a tecla está pressionada fisicamente no momento
            if user32.GetAsyncKeyState(k) & 0x8000:
                any_pressed = True
                break
        if not any_pressed:
            break
        time.sleep(0.01)  # 10ms de suspensão para não ocupar a CPU

    # Folga adicional de 30ms para estabilização de estado do teclado no Windows
    time.sleep(0.03)


class GlobalHotkey:
    """Registra e gerencia uma hotkey global exclusiva no Windows (disparada no Keyup)."""

    def __init__(self, hotkey: str, on_press: Callable[[], None] | None = None, on_release: Callable[[], None] | None = None) -> None:
        self.hotkey = hotkey
        self.on_press = on_press
        self.on_release = on_release
        self.thread: threading.Thread | None = None
        self.thread_id: int | None = None
        self.ready = threading.Event()
        self.error: str | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self._message_loop, daemon=True)
        self.thread.start()
        self.ready.wait(timeout=3)
        if self.error:
            raise RuntimeError(self.error)

    def stop(self) -> None:
        if self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        if self.thread:
            self.thread.join(timeout=2)

    def _message_loop(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self.thread_id = kernel32.GetCurrentThreadId()

        try:
            mods, vk = _parse_hotkey(self.hotkey)
        except ValueError as exc:
            self.error = str(exc)
            self.ready.set()
            return

        # Registra a tecla de atalho exata (sem registrar variantes implícitas com Alt para evitar conflitos)
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
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                    if self.on_press:
                        self.on_press()

                    # Aguarda a liberação física de todas as teclas associadas
                    _wait_for_keys_release(mods, vk)

                    if self.on_release:
                        self.on_release()

                    # Limpa mensagens repetidas de atalho acumuladas na fila da thread
                    msg_junk = wintypes.MSG()
                    while user32.PeekMessageW(ctypes.byref(msg_junk), None, WM_HOTKEY, WM_HOTKEY, 1):
                        pass
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)


class EscapeHotkey:
    """Registra Esc como hotkey global temporariamente (durante gravação, disparando no Keyup)."""

    def __init__(self, on_press: Callable[[], None] | None = None, on_release: Callable[[], None] | None = None) -> None:
        self.on_press = on_press
        self.on_release = on_release
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()

    def register(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=1)

    def unregister(self) -> None:
        tid = self._thread_id
        if tid:
            ctypes.windll.user32.PostThreadMessageW(tid, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1)
        self._thread = None
        self._thread_id = None

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
                    if self.on_press:
                        self.on_press()
                    # Aguarda liberar a tecla Esc física antes de disparar
                    _wait_for_keys_release(0, VK_ESCAPE)
                    if self.on_release:
                        self.on_release()
        finally:
            user32.UnregisterHotKey(None, ESCAPE_HOTKEY_ID)
            self._thread_id = None
