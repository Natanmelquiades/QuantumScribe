import pytest

from localwhisper.config import AppConfig, is_model_downloaded, load_config, save_config


@pytest.fixture
def temp_appdata(tmp_path, monkeypatch):
    # Redireciona o LOCALAPPDATA para uma pasta temporária isolada
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path

def test_load_default_config(temp_appdata):
    # Sem arquivo existente, deve carregar o padrão
    config = load_config()
    assert isinstance(config, AppConfig)
    assert config.model == "medium"
    assert config.effective_model == "medium"
    assert config.language == "pt"
    assert config.device == "auto"
    assert config.compute_type == "auto"
    # ai_mode deve vir como False agora por padrão
    assert config.ai_mode is False

def test_save_and_reload(temp_appdata):
    config = load_config()
    config.language = "en"
    config.device = "cuda"
    save_config(config)

    # Recarrega para ver se persistiu
    reloaded = load_config()
    assert reloaded.language == "en"
    assert reloaded.device == "cuda"
    assert reloaded.effective_model == "medium"
    assert reloaded.auto_download_model is True

def test_missing_model_preserves_preference_for_automatic_download(temp_appdata):
    config = load_config()
    config.model = "medium"
    save_config(config)

    reloaded = load_config()
    # A preferência (model) deve continuar sendo "medium"
    assert reloaded.model == "medium"
    # Mesmo ausente, ele permanece efetivo para ser baixado/retomado automaticamente.
    assert reloaded.effective_model == "medium"


def test_corrupt_config_is_repaired_with_safe_defaults(temp_appdata):
    config_file = temp_appdata / "QuantumScribe" / "config.json"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("{inválido", encoding="utf-8")

    config = load_config()

    assert config.model == "medium"
    assert config.device == "auto"
    assert config.compute_type == "auto"
    assert '"model": "medium"' in config_file.read_text(encoding="utf-8")


def test_partial_model_snapshot_is_not_treated_as_downloaded(temp_appdata):
    snapshot = (
        temp_appdata / "QuantumScribe" / "models"
        / "models--Systran--faster-whisper-large-v3"
        / "snapshots" / "partial"
    )
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text("{}", encoding="utf-8")

    assert is_model_downloaded("large-v3") is False


def test_complete_model_snapshot_is_detected(temp_appdata):
    snapshot = (
        temp_appdata / "QuantumScribe" / "models"
        / "models--Systran--faster-whisper-small"
        / "snapshots" / "complete"
    )
    snapshot.mkdir(parents=True)
    for filename in ("config.json", "model.bin", "tokenizer.json"):
        (snapshot / filename).write_bytes(b"ready")

    assert is_model_downloaded("small") is True
