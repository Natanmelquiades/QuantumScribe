from datetime import datetime, timezone

import pytest

from localwhisper.contracts import (
    RecordingSession,
    SessionEvent,
    SessionState,
    TranscriptionResult,
)


def test_contracts_are_small_and_independent_from_runtime_dependencies():
    session = RecordingSession("session-1", datetime.now(timezone.utc))
    result = TranscriptionResult("session-1", "olá", source_mode="streaming")
    event = SessionEvent("session-1", SessionState.RECORDING, progress=0.25)

    assert session.source == "microphone"
    assert result.text == "olá"
    assert result.source_mode == "streaming"
    assert event.state is SessionState.RECORDING
    assert event.progress == 0.25


@pytest.mark.parametrize(
    "factory",
    [
        lambda: RecordingSession("", datetime.now(timezone.utc)),
        lambda: TranscriptionResult(" ", "texto"),
        lambda: SessionEvent("\t", SessionState.IDLE),
    ],
)
def test_contracts_reject_empty_session_ids(factory):
    with pytest.raises(ValueError, match="session_id"):
        factory()


@pytest.mark.parametrize("progress", [-0.01, 1.01, float("inf"), float("-inf")])
def test_session_event_rejects_invalid_progress(progress):
    with pytest.raises(ValueError, match="progress"):
        SessionEvent("session-1", SessionState.PROCESSING, progress=progress)


def test_session_event_requires_a_known_state():
    with pytest.raises(TypeError, match="SessionState"):
        SessionEvent("session-1", "recording")


def test_transcription_result_rejects_unknown_source_mode():
    with pytest.raises(ValueError, match="source_mode"):
        TranscriptionResult("session-1", "texto", source_mode="batch")
