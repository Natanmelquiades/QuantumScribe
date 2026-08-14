from types import SimpleNamespace
from unittest.mock import Mock

from localwhisper.app import QuantumScribeApp


def _app_with_stream():
    app = object.__new__(QuantumScribeApp)
    app.config = SimpleNamespace(streaming_mode=True, play_sounds=False)
    app.processing = True
    app.starting = False
    app._recording_session = 9
    app._cancel_confirmation_pending_session = None
    app._stream_session_id = 9
    app._stream_stopping = False
    app._stream_accumulated = []
    app._stream_session = Mock()
    app.recorder = SimpleNamespace(is_recording=False)
    app.popup = SimpleNamespace(hide=Mock(), clear_cancel_hold=Mock(), set_text=Mock())
    app.esc_hotkey = SimpleNamespace(unregister=Mock())
    return app


def test_active_stream_stops_with_the_same_toggle():
    app = _app_with_stream()
    app._stop_streaming = Mock()

    app.toggle_recording()

    app._stop_streaming.assert_called_once_with(False)


def test_hud_cancel_stops_stream_capture_not_only_transcription():
    app = _app_with_stream()
    app.cancel_transcription = Mock()
    session = app._stream_session

    app._on_hud_cancel()

    session.cancel.assert_called_once_with()
    app.cancel_transcription.assert_not_called()
    assert app._stream_session is None
    assert app.processing is False


def test_escape_hold_cancels_an_active_stream():
    app = _app_with_stream()
    app.cancel_recording = Mock()

    app._confirm_cancel_hold(9)

    app.cancel_recording.assert_called_once_with()


def test_stale_stream_chunk_does_not_schedule_hud_update():
    app = _app_with_stream()
    app._stream_session_id = None
    app.root = SimpleNamespace(after=Mock())

    app._on_stream_chunk(9, "resultado antigo")

    app.root.after.assert_not_called()


def test_stream_completion_ignores_a_stale_session():
    app = _app_with_stream()
    app._show_success = Mock()

    app._finish_stream_success(Mock(), 8, "Texto inserido")

    assert app._stream_session is not None
    assert app.processing is True
    app._show_success.assert_not_called()
