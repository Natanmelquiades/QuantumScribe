import sys
import threading
import time
import types

import pytest

from localwhisper.config import is_model_downloaded
from localwhisper.model_manager import MODEL_REVISIONS, ModelDownloadError, ensure_model_downloaded


@pytest.fixture
def isolated_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path / "QuantumScribe" / "models"


def _write_complete_snapshot(cache_dir, model_name="medium"):
    snapshot = (
        cache_dir
        / f"models--Systran--faster-whisper-{model_name}"
        / "snapshots"
        / "test-revision"
    )
    snapshot.mkdir(parents=True, exist_ok=True)
    for filename in ("config.json", "model.bin", "tokenizer.json"):
        (snapshot / filename).write_bytes(b"ready")


def test_clean_install_downloads_medium_into_whisper_cache(isolated_appdata):
    calls = []

    def fake_download(model_name, *, cache_dir):
        calls.append((model_name, cache_dir))
        _write_complete_snapshot(isolated_appdata, model_name)
        return str(isolated_appdata)

    ensure_model_downloaded("medium", downloader=fake_download)

    assert calls == [("medium", str(isolated_appdata))]
    assert is_model_downloaded("medium") is True


def test_official_model_download_is_pinned_to_reviewed_revision(isolated_appdata, monkeypatch):
    captured = {}

    def fake_snapshot_download(**kwargs):
        captured.update(kwargs)
        _write_complete_snapshot(isolated_appdata, "medium")
        return str(isolated_appdata)

    fake_hub = types.ModuleType("huggingface_hub")
    fake_hub.snapshot_download = fake_snapshot_download
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)

    ensure_model_downloaded("medium")

    assert captured["repo_id"] == "Systran/faster-whisper-medium"
    assert captured["revision"] == MODEL_REVISIONS["medium"]
    assert len(captured["revision"]) == 40


def test_interrupted_download_is_resumed(isolated_appdata):
    partial = (
        isolated_appdata
        / "models--Systran--faster-whisper-medium"
        / "snapshots"
        / "test-revision"
    )
    partial.mkdir(parents=True)
    (partial / "config.json").write_text("{}", encoding="utf-8")
    calls = 0

    def resume_download(model_name, *, cache_dir):
        nonlocal calls
        calls += 1
        _write_complete_snapshot(isolated_appdata, model_name)
        return cache_dir

    ensure_model_downloaded("medium", downloader=resume_download)

    assert calls == 1
    assert is_model_downloaded("medium") is True


def test_complete_model_skips_network(isolated_appdata):
    _write_complete_snapshot(isolated_appdata)

    def should_not_run(*args, **kwargs):
        raise AssertionError("download não deveria ser iniciado")

    ensure_model_downloaded("medium", downloader=should_not_run)


def test_download_failure_is_actionable_and_keeps_partial_state(isolated_appdata):
    def fail_download(*args, **kwargs):
        raise OSError("rede indisponível")

    with pytest.raises(ModelDownloadError, match="retomado"):
        ensure_model_downloaded("medium", downloader=fail_download)

    assert is_model_downloaded("medium") is False


def test_simultaneous_first_use_downloads_only_once(isolated_appdata):
    calls = 0
    errors = []

    def slow_download(model_name, *, cache_dir):
        nonlocal calls
        calls += 1
        time.sleep(0.05)
        _write_complete_snapshot(isolated_appdata, model_name)
        return cache_dir

    def worker():
        try:
            ensure_model_downloaded("medium", downloader=slow_download)
        except Exception as error:  # pragma: no cover - coletado para diagnóstico
            errors.append(error)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert calls == 1
