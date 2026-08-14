import sys
import types

from localwhisper.download_progress import (
    download_snapshot_with_progress,
    download_whisper_with_progress,
)


def _fake_hub(monkeypatch, captured):
    def snapshot_download(**kwargs):
        captured.update(kwargs)
        return "downloaded"

    module = types.ModuleType("huggingface_hub")
    module.snapshot_download = snapshot_download
    monkeypatch.setitem(sys.modules, "huggingface_hub", module)


def test_whisper_progress_download_keeps_requested_revision(tmp_path, monkeypatch):
    captured = {}
    _fake_hub(monkeypatch, captured)

    result = download_whisper_with_progress(
        "medium", tmp_path, revision="a" * 40
    )

    assert result == "downloaded"
    assert captured["repo_id"] == "Systran/faster-whisper-medium"
    assert captured["revision"] == "a" * 40


def test_snapshot_progress_download_keeps_requested_revision(tmp_path, monkeypatch):
    captured = {}
    _fake_hub(monkeypatch, captured)

    result = download_snapshot_with_progress(
        "approved/model", tmp_path, revision="b" * 40
    )

    assert result == "downloaded"
    assert captured["repo_id"] == "approved/model"
    assert captured["revision"] == "b" * 40
