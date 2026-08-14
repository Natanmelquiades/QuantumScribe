import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from localwhisper.app import QuantumScribeApp


class _ImmediateRoot:
    def after(self, _delay: int, callback):
        callback()


class _DeferredRoot:
    def __init__(self):
        self.callbacks = []

    def after(self, _delay: int, callback):
        self.callbacks.append(callback)

    def run_pending(self) -> None:
        while self.callbacks:
            self.callbacks.pop(0)()


class _ThreadStub:
    created: list["_ThreadStub"] = []

    def __init__(self, *, target, args, daemon: bool):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False
        self.created.append(self)

    def start(self) -> None:
        self.started = True


def test_cancelled_job_cannot_deliver_old_text(tmp_path, monkeypatch):
    app = object.__new__(QuantumScribeApp)
    app.config = SimpleNamespace(literal_mode=True, auto_paste=True)
    app.processing = True
    app._active_transcription_job = 1
    app._transcription_context = threading.local()
    app.root = _ImmediateRoot()
    app.popup = SimpleNamespace(show_processing_with_progress=Mock(), complete_progress=Mock())

    def transcribe_and_replace_job(*_args, **_kwargs):
        app._active_transcription_job = 2
        return "resultado antigo"

    app.transcriber = SimpleNamespace(is_loaded=lambda: True, transcribe=transcribe_and_replace_job)
    type_into_window = Mock()
    monkeypatch.setattr("localwhisper.app.type_into_window", type_into_window)
    audio_path = tmp_path / "old.wav"
    audio_path.write_bytes(b"audio")

    app._transcribe_and_deliver(audio_path, object(), 1.0, 1)

    type_into_window.assert_not_called()
    assert app.processing is True
    assert not audio_path.exists()


def test_completed_job_delivers_its_final_ui_message_before_being_retired(tmp_path, monkeypatch):
    app = object.__new__(QuantumScribeApp)
    app.config = SimpleNamespace(
        literal_mode=True,
        auto_paste=True,
        quantum_brain_also_paste=True,
        tone_style="Padrão",
        use_llm_rewriter=False,
    )
    app.processing = True
    app._active_transcription_job = 1
    app._transcription_context = threading.local()
    app.root = _DeferredRoot()
    app.popup = SimpleNamespace(show_processing_with_progress=Mock(), complete_progress=Mock())
    app.transcriber = SimpleNamespace(is_loaded=lambda: True, transcribe=lambda *_args, **_kwargs: "resultado")
    app._show_success = Mock()
    monkeypatch.setattr("localwhisper.app.type_into_window", Mock(return_value=True))
    monkeypatch.setattr("localwhisper.app.save_entry", Mock())
    monkeypatch.setattr("localwhisper.diary.save_comparison_log", Mock())
    audio_path = tmp_path / "done.wav"
    audio_path.write_bytes(b"audio")

    app._transcribe_and_deliver(audio_path, object(), 1.0, 1)

    assert app._active_transcription_job == 1
    assert app.processing is False
    app.root.run_pending()
    app._show_success.assert_called_once_with("Texto inserido")
    assert app._active_transcription_job is None


def test_finish_recording_allocates_a_distinct_wav_for_each_job(tmp_path, monkeypatch):
    app = object.__new__(QuantumScribeApp)
    app.config = SimpleNamespace(play_sounds=False)
    app.processing = False
    app._recording_session = 0
    app._next_transcription_job = 0
    app._active_transcription_job = None
    app._cancel_confirmation_pending_session = None
    app.popup = SimpleNamespace(clear_cancel_hold=Mock(), show_message=Mock())
    app.esc_hotkey = SimpleNamespace(unregister=Mock())
    app.target_window = object()
    app.recorder = SimpleNamespace(
        stop_and_save=lambda path: (Path(path).write_bytes(b"audio") or 1.0),
    )
    monkeypatch.setattr("localwhisper.app.tempfile.gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr("localwhisper.app.threading.Thread", _ThreadStub)
    monkeypatch.setattr("shutil.copy2", lambda *_args, **_kwargs: None)
    _ThreadStub.created.clear()

    app.finish_recording()
    app.processing = False
    app.finish_recording()

    first_path, second_path = (thread.args[0] for thread in _ThreadStub.created)
    assert first_path != second_path
    assert [thread.args[3] for thread in _ThreadStub.created] == [1, 2]
    for path in (first_path, second_path):
        path.unlink(missing_ok=True)
