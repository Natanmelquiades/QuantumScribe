"""Cache de Vocabulário Pessoal — Aprende e corrige palavras do seu padrão de fala.

Este módulo gerencia um banco de palavras pessoal que:
    1. Permite adicionar manualmente correções (erro → correto)
    2. Aprende automaticamente vocabulário frequente dos diários (.md)
    3. Alimenta o initial_prompt do Whisper com os termos mais usados
    4. Aplica correções em zero latência via dict lookup + regex

Arquivo de dados: %LOCALAPPDATA%/LocalWhisper/vocab_personal.json

Estrutura do JSON:
    {
        "word_errada": {
            "correct": "wordCorreta",
            "hits": 42,
            "manual": true,
            "added": "2026-06-30"
        }
    }
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Dict


def _get_vocab_path() -> Path:
    from .config import app_data_dir
    return app_data_dir() / "vocab_personal.json"


# ---------------------------------------------------------------------------
# Correções padrão pré-populadas com base nos erros recorrentes identificados
# nos diários de uso do usuário (01/07 a 04/07/2026).
# Estas correções são injetadas na primeira execução se o vocab estiver vazio.
# ---------------------------------------------------------------------------
DEFAULT_CORRECTIONS: dict[str, str] = {
    # Erros de transcrição de produtos/marcas
    "chutarrinha": "chuteira",
    "chutesira": "chuteira",
    "chutesiras": "chuteiras",
    "chutaria": "chuteira",
    "canuxias": "Knul,X",
    "canuxis": "Knul,X",
    # Erros de vocabulário técnico
    "amaduras": "amadoras",
    "promptes": "prompts",
    "prontos": "prompts",      # quando claramente no contexto de prompts de IA
    "atalize": "atualize",
    "chrome job": "cron job",
    "chrome jobs": "cron jobs",
    "caracter sheet": "character sheet",
    "product shift": "product sheet",
    "produto de shift": "product sheet",
    "unidesk": "AnyDesk",
    # Coloquialismos frequentes que o Whisper distorce
    "sóque": "só que",
    # Termos de IA gerativa
    "nanobanana": "Nanobanana",
    "pintereste": "Pinterest",
}


class PersonalVocabCache:
    """Gerencia o vocabulário pessoal do usuário para correção automática de transcrições."""

    def __init__(self) -> None:
        self.path = _get_vocab_path()
        # Chave: palavra errada em minúsculas
        # Valor: dict com "correct", "hits", "manual", "added"
        self.corrections: Dict[str, dict] = {}
        self._compiled_pattern: re.Pattern | None = None
        self._dirty: bool = False  # Indica se precisa salvar
        self.load()
        self.seed_defaults()  # Injeta correções padrão se o vocab estiver vazio

    # ---- Persistência -----------------------------------------------------------

    def load(self) -> None:
        """Carrega o vocabulário pessoal do disco."""
        if not self.path.exists():
            self.corrections = {}
            return
        try:
            raw = self.path.read_text(encoding="utf-8")
            self.corrections = json.loads(raw)
            self._compiled_pattern = None  # Invalida cache de pattern

            # Migração: garante a grafia Knul,X no lugar de Canuxis
            migrated = False
            for key in ["canuxias", "canuxis"]:
                if key in self.corrections:
                    if self.corrections[key].get("correct") == "Canuxis":
                        self.corrections[key]["correct"] = "Knul,X"
                        migrated = True
            if migrated:
                self.save()
        except Exception:
            self.corrections = {}

    def save(self) -> None:
        """Persiste o vocabulário pessoal no disco."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.corrections, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._dirty = False
        except Exception:
            pass

    # ---- Gerenciamento de correções ---------------------------------------------

    def add_correction(self, wrong: str, correct: str) -> None:
        """Adiciona ou atualiza uma correção manual de palavra.

        Args:
            wrong: Palavra/expressão que o Whisper transcreve errado.
            correct: A forma correta que deve aparecer no texto final.
        """
        key = wrong.strip().lower()
        if not key or not correct.strip():
            return

        existing_hits = self.corrections.get(key, {}).get("hits", 0)
        self.corrections[key] = {
            "correct": correct.strip(),
            "hits": existing_hits,
            "manual": True,
            "added": str(date.today()),
        }
        self._compiled_pattern = None  # Invalida cache
        self.save()

    def remove_correction(self, wrong: str) -> None:
        """Remove uma correção do vocabulário.

        Args:
            wrong: A palavra errada a remover.
        """
        key = wrong.strip().lower()
        if key in self.corrections:
            del self.corrections[key]
            self._compiled_pattern = None
            self.save()

    def clear(self) -> None:
        """Remove todo o vocabulário pessoal."""
        self.corrections = {}
        self._compiled_pattern = None
        self.save()

    def seed_defaults(self) -> None:
        """Pré-popula o vocabulário com correções padrão se estiver vazio ou com chaves ausentes.

        Injeta qualquer correção padrão que ainda não exista no dicionário pessoal do usuário.
        Não sobrescreve correções manuais do usuário.
        Marca as entradas injetadas com ``manual=False`` para distingui-las.
        """
        modified = False
        for wrong, correct in DEFAULT_CORRECTIONS.items():
            key = wrong.strip().lower()
            if key and correct.strip() and key not in self.corrections:
                self.corrections[key] = {
                    "correct": correct.strip(),
                    "hits": 0,
                    "manual": False,
                    "added": str(date.today()),
                }
                modified = True

        if modified:
            self._compiled_pattern = None  # Invalida cache de pattern
            self.save()

    # ---- Aplicação de correções -------------------------------------------------

    def _get_pattern(self) -> re.Pattern | None:
        """Retorna (e compila se necessário) o padrão regex unificado para todas as correções."""
        if self._compiled_pattern is not None:
            return self._compiled_pattern

        if not self.corrections:
            return None

        # Ordena por comprimento decrescente para bigramas antes de palavras isoladas
        sorted_keys = sorted(self.corrections.keys(), key=len, reverse=True)
        escaped = [re.escape(k) for k in sorted_keys]

        # Word boundary para evitar substituir partes de palavras maiores
        pattern_str = r"\b(" + "|".join(escaped) + r")\b"
        self._compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
        return self._compiled_pattern

    def apply_corrections(self, text: str) -> str:
        """Aplica todas as correções conhecidas ao texto transcrito.

        A substituição é case-aware: se a palavra no texto começar com maiúscula,
        a correção também começará. Contabiliza hits para aprendizado de frequência.

        Args:
            text: Texto bruto ou semi-processado para corrigir.

        Returns:
            Texto com substituições aplicadas.
        """
        if not self.corrections or not text:
            return text

        pattern = self._get_pattern()
        if pattern is None:
            return text

        hit_counts: Dict[str, int] = {}

        def _replace(m: re.Match) -> str:
            matched = m.group(0)
            key = matched.lower()
            data = self.corrections.get(key)
            if not data:
                return matched

            correct = data.get("correct", matched)

            # Contabiliza hit
            hit_counts[key] = hit_counts.get(key, 0) + 1

            # Preserva capitalização: se a palavra no texto começa com maiúscula,
            # a correção também começa.
            if matched[0].isupper() and correct:
                return correct[0].upper() + correct[1:]
            return correct

        result = pattern.sub(_replace, text)

        # Atualiza hits no dicionário e salva de forma lazy
        if hit_counts:
            for key, count in hit_counts.items():
                if key in self.corrections:
                    self.corrections[key]["hits"] = self.corrections[key].get("hits", 0) + count
            self._dirty = True
            self.save()

        return result

    # ---- Integração com Whisper -------------------------------------------------

    def get_whisper_vocab_hint(self, max_words: int = 20) -> str:
        """Retorna string de vocabulário para o initial_prompt do Whisper.

        Inclui as palavras corrigidas mais frequentes para guiar o Whisper a
        reconhecê-las corretamente desde o início.

        Args:
            max_words: Número máximo de palavras a incluir.

        Returns:
            String formatada como "Palavra1, Palavra2, ..." ou "" se vazio.
        """
        if not self.corrections:
            return ""

        # Ordena pelas mais usadas (mais hits = mais importante para o Whisper)
        top = sorted(
            self.corrections.items(),
            key=lambda x: x[1].get("hits", 0),
            reverse=True,
        )[:max_words]

        words = [data["correct"] for _, data in top if data.get("correct")]
        return ", ".join(words) if words else ""

    # ---- Propriedades -----------------------------------------------------------

    @property
    def total_corrections(self) -> int:
        """Número total de correções no vocabulário."""
        return len(self.corrections)

    def get_all_sorted(self) -> list[dict]:
        """Retorna lista de todas as correções ordenadas por hits (decrescente).

        Útil para exibição na UI.

        Returns:
            Lista de dicts com keys: "wrong", "correct", "hits", "manual".
        """
        result = []
        for wrong, data in sorted(
            self.corrections.items(),
            key=lambda x: x[1].get("hits", 0),
            reverse=True,
        ):
            result.append({
                "wrong": wrong,
                "correct": data.get("correct", ""),
                "hits": data.get("hits", 0),
                "manual": data.get("manual", False),
            })
        return result


# ---- Instância global compartilhada ----------------------------------------

#: Instância global usada por todo o app. Carregada uma vez na inicialização.
personal_vocab = PersonalVocabCache()
