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
    assert config.model == "small"
    assert config.language == "pt"
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
    # effective_model deve ser recalculado (como o modelo cuda não existe, recua para small)
    assert reloaded.effective_model == "small"

def test_model_fallback_preserves_preference(temp_appdata):
    config = load_config()
    config.model = "medium"
    save_config(config)

    reloaded = load_config()
    # A preferência (model) deve continuar sendo "medium"
    assert reloaded.model == "medium"
    # Mas como o modelo "medium" não está baixado na pasta temporária, effective_model deve ser "small"
    assert reloaded.effective_model == "small"


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
