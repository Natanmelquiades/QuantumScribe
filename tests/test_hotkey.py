from types import SimpleNamespace

from localwhisper.app import ESC_HOLD_SECONDS, QuantumScribeApp
from localwhisper.hotkey import EscapeHotkey


class _FakeUser32:
    def __init__(self, pressed_states: list[bool]) -> None:
        self._pressed_states = iter(pressed_states)

    def GetAsyncKeyState(self, _key: int) -> int:
        return 0x8000 if next(self._pressed_states, False) else 0


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
    cancelled: list[bool] = []
    app.cancel_recording = lambda: cancelled.append(True)

    app._confirm_cancel_hold(12)

    assert cancelled == [True]
