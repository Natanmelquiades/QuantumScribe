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

    def start(self, readiness_timeout: float = 0.05) -> None:
        self.thread = threading.Thread(target=self._message_loop, daemon=True)
        self.thread.start()
        # O app continua iniciando mesmo se o Windows demorar a registrar um
        # atalho. Falhas imediatas ainda são exibidas ao usuário; não somamos
        # vários timeouts de 3 s antes de a bandeja ficar disponível.
        self.ready.wait(timeout=readiness_timeout)
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
    """Confirma o cancelamento apenas quando Esc permanece pressionado.

    O Windows entrega ``WM_HOTKEY`` no início do pressionamento. A confirmação é
    feita na própria thread da hotkey para não bloquear a interface, enquanto os
    callbacks de UI continuam sendo encaminhados para a thread principal pelo
    aplicativo. ``session_id`` impede que um evento atrasado afete outra gravação.
    """

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
            return
        self._session_id = session_id
        self._ready.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=1)

    def unregister(self, wait: bool = True) -> None:
        """Solicita a remoção do atalho, opcionalmente sem bloquear a UI."""
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
        """Aguarda a tecla liberar e confirma uma única vez ao atingir o limite."""
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
