"""Módulo de Cache Semântico Local para aceleração de expressões frequentes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict


def _get_cache_path() -> Path:
    from .config import model_dir
    # Salva o arquivo de cache no mesmo diretório de modelos/dados do usuário
    return model_dir() / "semantic_cache.json"


def _normalize_text(text: str) -> str:
    """Normaliza o texto para busca insensível a pontuação, acentuação e espaços extras."""
    # Transforma em minúsculas
    text = text.lower().strip()
    # Remove pontuação simples para o casamento semântico tolerar variações de pontuação do Whisper
    text = re.sub(r"[.,\/#!$%\^&\*;:{}=\-_`~()?\"]", "", text)
    # Remove múltiplos espaços em branco
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class NormalizedTextCache:
    """Cache de correspondência exata por texto normalizado.

    Armazena pares (texto_bruto_normalizado → texto_refinado) para reutilização
    rápida de expressões frequentes sem chamar o Mini-LLM novamente.

    Nota: a correspondência é por igualdade exata após normalização (lowercase,
    sem pontuação, sem espaços extras). Não há entendimento semântico real.
    """

    def __init__(self) -> None:
        self.path = _get_cache_path()
        self.cache: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        """Carrega o cache do disco."""
        if not self.path.exists():
            self.cache = {}
            return
        try:
            raw = self.path.read_text(encoding="utf-8")
            self.cache = json.loads(raw)
        except Exception:
            self.cache = {}

    def save(self) -> None:
        """Persiste o cache no disco."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get(self, raw_text: str) -> str | None:
        """Busca o texto polido no cache a partir da entrada bruta do Whisper."""
        normalized = _normalize_text(raw_text)
        return self.cache.get(normalized)

    def set(self, raw_text: str, refined_text: str) -> None:
        """Adiciona uma nova correspondência de reescrita no cache."""
        normalized = _normalize_text(raw_text)
        # Evita salvar se for vazio ou se forem exatamente iguais (sem ganho)
        if not normalized or normalized == _normalize_text(refined_text):
            return
        # Evita envenenar o cache com textos excessivamente longos (limite de 100 caracteres por frase)
        if len(raw_text) > 100 or len(refined_text) > 120:
            return

        self.cache[normalized] = refined_text.strip()
        self.save()


# Instância global compartilhada
global_cache = NormalizedTextCache()
