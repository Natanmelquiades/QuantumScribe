"""Gerenciador de Atalhos Globais no Linux (usando pynput)."""

from __future__ import annotations

import threading
import time
from typing import Callable

_MODIFIER_ALIASES = {
    "control": "ctrl",
    "windows": "cmd",
    "win": "cmd",
    "super": "cmd",
}
_MODIFIERS = {"ctrl", "alt", "shift", "cmd"}
_NAMED_KEYS = {"space", *(f"f{number}" for number in range(1, 13))}


def _hotkey_parts(hotkey: str) -> frozenset[str]:
    parts = [_MODIFIER_ALIASES.get(part.strip().lower(), part.strip().lower()) for part in hotkey.split("+")]
    if not parts or any(not part for part in parts):
        raise ValueError(f"Atalho '{hotkey}' possui uma sintaxe inválida.")

    unknown = [part for part in parts if part not in _MODIFIERS | _NAMED_KEYS and not (len(part) == 1 and part.isalnum())]
    if unknown:
        raise ValueError(f"Tecla desconhecida no atalho: '{unknown[0]}'")

    main_keys = [part for part in parts if part not in _MODIFIERS]
    if len(main_keys) != 1:
        raise ValueError(f"Atalho '{hotkey}' deve conter exatamente uma tecla principal válida.")
    if len(set(parts)) != len(parts):
        raise ValueError(f"Atalho '{hotkey}' contém teclas repetidas.")
    return frozenset(parts)


def _parse_hotkey(hotkey: str) -> tuple[int, int]:
    """Valida sintaxe de atalho (Ctrl+Space, etc.)."""
    _hotkey_parts(hotkey)
    return 0, 0


class GlobalHotkey:
    """Registra e gerencia uma hotkey global no Linux via pynput."""

    def __init__(self, hotkey: str, on_press: Callable[[], None] | None = None, on_release: Callable[[], None] | None = None) -> None:
        self.hotkey = hotkey
        self.on_press = on_press
        self.on_release = on_release
        self.listener = None
        self.ready = threading.Event()
        self.error: str | None = None
        self._required_keys = _hotkey_parts(hotkey)
        self._pressed_keys: set[str] = set()
        self._active = False
        self._release_pending = False
        self._state_lock = threading.Lock()

    def _press_token(self, token: str | None) -> None:
        if token is None:
            return
        should_notify = False
        with self._state_lock:
            self._pressed_keys.add(token)
            if not self._active and not self._release_pending and self._required_keys <= self._pressed_keys:
                self._active = True
                should_notify = True
        if should_notify and self.on_press:
            self.on_press()

    def _release_token(self, token: str | None) -> None:
        if token is None:
            return
        should_notify = False
        with self._state_lock:
            self._pressed_keys.discard(token)
            if self._active and not self._required_keys <= self._pressed_keys:
                self._active = False
                self._release_pending = True
            if self._release_pending and not self._required_keys & self._pressed_keys:
                self._release_pending = False
                should_notify = True
        if should_notify and self.on_release:
            self.on_release()

    @staticmethod
    def _event_token(key, keyboard) -> str | None:
        char = getattr(key, "char", None)
        if isinstance(char, str) and len(char) == 1:
            return char.lower()
        aliases = {
            keyboard.Key.ctrl: "ctrl",
            keyboard.Key.ctrl_l: "ctrl",
            keyboard.Key.ctrl_r: "ctrl",
            keyboard.Key.alt: "alt",
            keyboard.Key.alt_l: "alt",
            keyboard.Key.alt_r: "alt",
            keyboard.Key.shift: "shift",
            keyboard.Key.shift_l: "shift",
            keyboard.Key.shift_r: "shift",
            keyboard.Key.cmd: "cmd",
            keyboard.Key.cmd_l: "cmd",
            keyboard.Key.cmd_r: "cmd",
            keyboard.Key.space: "space",
        }
        for number in range(1, 13):
            aliases[getattr(keyboard.Key, f"f{number}")] = f"f{number}"
        return aliases.get(key)

    def start(self, readiness_timeout: float = 0.5) -> None:
        try:
            from pynput import keyboard

            self.listener = keyboard.Listener(
                on_press=lambda key: self._press_token(self._event_token(key, keyboard)),
                on_release=lambda key: self._release_token(self._event_token(key, keyboard)),
            )
            self.listener.start()
            self.ready.set()
        except Exception as err:
            self.error = f"Não foi possível registrar o atalho '{self.hotkey}': {err}"
            self.ready.set()
            raise RuntimeError(self.error) from err

    def stop(self) -> None:
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
        with self._state_lock:
            self._pressed_keys.clear()
            self._active = False
            self._release_pending = False


class EscapeHotkey:
    """Escuta pressionamento do Esc para cancelamento no Linux."""

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
        self.listener = None
        self._session_id: int | None = None
        self._press_time: float | None = None
        self._hold_timer: threading.Timer | None = None
        self._state_lock = threading.Lock()

    def _confirm_hold(self, session_id: int | None) -> None:
        with self._state_lock:
            if self._press_time is None or session_id != self._session_id:
                return
        if self.on_hold:
            self.on_hold(session_id)

    def register(self, session_id: int | None = None) -> None:
        self._session_id = session_id
        try:
            from pynput import keyboard

            def on_press_key(key):
                if key == keyboard.Key.esc:
                    with self._state_lock:
                        if self._press_time is not None:
                            return
                        self._press_time = time.monotonic()
                        session = self._session_id
                        self._hold_timer = threading.Timer(self.hold_seconds, self._confirm_hold, args=(session,))
                        self._hold_timer.daemon = True
                        self._hold_timer.start()
                    if self.on_press:
                        self.on_press(session)

            def on_release_key(key):
                if key == keyboard.Key.esc:
                    with self._state_lock:
                        if self._press_time is None:
                            return
                        session = self._session_id
                        self._press_time = None
                        timer = self._hold_timer
                        self._hold_timer = None
                    if timer:
                        timer.cancel()
                    if self.on_release:
                        self.on_release(session)

            self.listener = keyboard.Listener(on_press=on_press_key, on_release=on_release_key)
            self.listener.start()
        except Exception:
            pass

    def unregister(self, wait: bool = True) -> None:
        with self._state_lock:
            timer = self._hold_timer
            self._hold_timer = None
            self._press_time = None
        if timer:
            timer.cancel()
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
        self._session_id = None
