import pytest

from localwhisper.cache import NormalizedTextCache


@pytest.fixture
def temp_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path

def test_cache_normalizes_punctuation(temp_appdata):
    cache = NormalizedTextCache()
    # Adiciona com pontuações variadas
    cache.set("Olá, tudo bem?", "Olá, tudo bem com você?")

    # Busca com outra pontuação/espaçamento
    assert cache.get("olá tudo bem") == "Olá, tudo bem com você?"
    assert cache.get("olá, tudo bem !!!") == "Olá, tudo bem com você?"

def test_cache_returns_none_for_unknown(temp_appdata):
    cache = NormalizedTextCache()
    assert cache.get("texto que nao existe no cache") is None

def test_cache_ignores_long_texts(temp_appdata):
    cache = NormalizedTextCache()
    # Texto de entrada com mais de 100 caracteres
    long_input = "a" * 101
    cache.set(long_input, "resposta curta")
    assert cache.get(long_input) is None

    # Texto de saída com mais de 120 caracteres
    long_output = "b" * 121
    cache.set("entrada curta", long_output)
    assert cache.get("entrada curta") is None
