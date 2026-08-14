import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from localwhisper.app import ESC_HOLD_SECONDS, QuantumScribeApp
from localwhisper.hotkey import EscapeHotkey
from localwhisper.settings_ui import hotkey_conflict


class _FakeUser32:
    def __init__(self, pressed_states: list[bool]) -> None:
        self._pressed_states = iter(pressed_states)

    def GetAsyncKeyState(self, _key: int) -> int:
        return 0x8000 if next(self._pressed_states, False) else 0


@pytest.mark.skipif(sys.platform != "win32", reason="Exercita o polling GetAsyncKeyState do Windows")
def test_escape_hold_confirms_only_after_configured_duration(monkeypatch):
    events: list[tuple[str, int | None]] = []
    hotkey = EscapeHotkey(
        on_hold=lambda session_id: events.append(("confirmed", session_id)),
        on_release=lambda session_id: events.append(("released", session_id)),
        hold_seconds=1.5,
    )
    monotonic_values = iter((0.0, 0.5, 1.6))
    monkeypatch.setattr("localwhisper.hotkey.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("localwhisper.hotkey.time.sleep", lambda _seconds: None)

    hotkey._wait_for_confirmation(_FakeUser32([True, True, False]), 42)

    assert events == [("confirmed", 42), ("released", 42)]


@pytest.mark.skipif(sys.platform != "win32", reason="Exercita o polling GetAsyncKeyState do Windows")
def test_escape_tap_releases_without_confirmation(monkeypatch):
    events: list[tuple[str, int | None]] = []
    hotkey = EscapeHotkey(
        on_hold=lambda session_id: events.append(("confirmed", session_id)),
        on_release=lambda session_id: events.append(("released", session_id)),
        hold_seconds=1.5,
    )
    monotonic_values = iter((0.0, 0.3))
    monkeypatch.setattr("localwhisper.hotkey.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("localwhisper.hotkey.time.sleep", lambda _seconds: None)

    hotkey._wait_for_confirmation(_FakeUser32([True, False]), 7)

    assert events == [("released", 7)]


def test_app_uses_half_second_escape_confirmation():
    assert ESC_HOLD_SECONDS == 0.5


def test_completed_escape_hold_cancels_without_feedback_delay():
    app = object.__new__(QuantumScribeApp)
    app._recording_session = 12
    app._cancel_confirmation_pending_session = None
    app.recorder = SimpleNamespace(is_recording=True)
    app._stream_session = None
    cancelled: list[bool] = []
    app.cancel_recording = lambda: cancelled.append(True)

    app._confirm_cancel_hold(12)

    assert cancelled == [True]


@pytest.mark.parametrize("hotkey", ("Ctrl+Ctrl+Space", "Ctrl+Space+F2", "Ctrl++Space"))
def test_hotkey_parser_rejects_ambiguous_combinations(hotkey):
    from localwhisper.hotkey import _parse_hotkey

    with pytest.raises(ValueError):
        _parse_hotkey(hotkey)


def test_hotkey_conflict_detects_equivalent_modifier_order():
    config = SimpleNamespace(
        hotkey="Ctrl+Space",
        hotkey_translate="Ctrl+Alt+Space",
        hotkey_auto_send="Ctrl+Shift+Space",
        hotkey_quantum_brain="Ctrl+Shift+D",
    )

    assert hotkey_conflict(config, "hotkey", "Shift+Ctrl+Space") == "Ditado + Enviar"


@pytest.mark.skipif(sys.platform != "win32", reason="Ciclo de vida específico do listener Windows")
def test_escape_listener_alive_accepts_the_new_session_without_reregistering():
    hotkey = EscapeHotkey()
    hotkey._thread = SimpleNamespace(is_alive=lambda: True)
    hotkey._session_id = 1

    hotkey.register(2)

    assert hotkey._session_id == 2


@pytest.mark.skipif(sys.platform != "win32", reason="Ciclo de vida específico do listener Windows")
def test_escape_unregister_without_wait_keeps_listener_available():
    hotkey = EscapeHotkey()
    hotkey._thread = SimpleNamespace(is_alive=lambda: True)
    hotkey._thread_id = 42
    hotkey._session_id = 4

    hotkey.unregister(wait=False)

    assert hotkey._session_id is None
    assert hotkey._thread_id == 42


@pytest.mark.skipif(sys.platform != "win32", reason="Registro específico da API Windows")
def test_global_hotkey_reports_a_registration_timeout(monkeypatch):
    from localwhisper.platform.windows.hotkey import GlobalHotkey

    class _ThreadThatNeverSignals:
        def __init__(self, *, target, daemon: bool):
            self.target = target
            self.daemon = daemon

        def start(self) -> None:
            pass

        def join(self, timeout: float) -> None:
            del timeout

        def is_alive(self) -> bool:
            return False

    hotkey = GlobalHotkey("Ctrl+Space")
    stop = Mock()
    monkeypatch.setattr("localwhisper.platform.windows.hotkey.threading.Thread", _ThreadThatNeverSignals)
    monkeypatch.setattr(hotkey, "stop", stop)

    with pytest.raises(RuntimeError, match="não confirmou"):
        hotkey.start(readiness_timeout=0)

    stop.assert_called_once_with()
