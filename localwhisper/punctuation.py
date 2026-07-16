"""Restauração conservadora de pontuação sem modificar palavras."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

_TERMINAL_PUNCTUATION = (".", "!", "?", "…", "...")

# Marcadores de pergunta de alta precisão no início da frase.
_QUESTION_START_RE = re.compile(
    r"^(?:"
    r"por\s+qu[eê]|pra\s+qu[eê]|para\s+qu[eê]|"
    r"quem|qual|quais|onde|quando|quanto|quantos|quantas|cad[eê]|"
    r"o\s+qu[eê]|ser[aá]\s+que|"
    r"como\s+(?:[eé]|est[aá]|t[aá]|foi|vai|fica|funciona|fa[cç]o|faz|fazer|podemos|posso|voc[eê]|voc[eê]s)"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)

# Perguntas coloquiais que também podem aparecer depois de uma oração e vírgula.
_QUESTION_CLAUSE_RE = re.compile(
    r"(?:^|[,;:]\s+)(?:"
    r"tem\s+como|d[aá]\s+(?:pra|para)|[eé]\s+poss[ií]vel|"
    r"como\s+[eé]\s+que|sabe\s+se|sabia\s+que|conhece|"
    r"vai\s+dar|posso|podemos|"
    r"voc[eê]s?\s+(?:consegue|conseguem|pode|podem|sabe|sabem|acha|acham)|"
    r"t[aá]\s+vendendo|est[aá]\s+vendendo"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)


def _looks_like_question(sentence: str) -> bool:
    """Detecta apenas construções interrogativas com baixa ambiguidade."""
    candidate = sentence.strip()
    if not candidate:
        return False

    # Remove somente o ponto final para analisar o conteúdo da frase.
    if candidate.endswith(".") and not candidate.endswith("..."):
        candidate = candidate[:-1].rstrip()

    return bool(
        _QUESTION_START_RE.search(candidate)
        or _QUESTION_CLAUSE_RE.search(candidate)
        or re.search(r"\bou\s+n[aã]o\s*$", candidate, re.IGNORECASE | re.UNICODE)
    )


def restore_question_marks(text: str) -> str:
    """Adiciona `?` a perguntas prováveis sem alterar nenhuma palavra."""
    if not text or not text.strip():
        return text

    # Mantém os separadores de espaço exatamente como foram recebidos.
    parts = re.split(r"(?<=[.!?…])(\s+)", text)
    for index in range(0, len(parts), 2):
        sentence = parts[index]
        stripped = sentence.rstrip()
        trailing = sentence[len(stripped):]
        if not stripped or stripped.endswith(("?", "!", "…", "...")):
            continue
        if not _looks_like_question(stripped):
            continue

        if stripped.endswith("."):
            stripped = stripped[:-1] + "?"
        else:
            stripped += "?"
        parts[index] = stripped + trailing

    return "".join(parts)


def ensure_terminal_punctuation(text: str) -> str:
    """Fecha um ditado completo com ponto quando não há sinal terminal."""
    if not text or not text.strip():
        return text
    stripped = text.rstrip()
    trailing = text[len(stripped):]
    if stripped.endswith(_TERMINAL_PUNCTUATION):
        return text
    if stripped.endswith((",", ";", ":")):
        stripped = stripped[:-1]
    return stripped + "." + trailing


def _close_statement(text: str) -> str:
    """Fecha um segmento em pausa longa modificando apenas pontuação."""
    stripped = text.rstrip()
    trailing = text[len(stripped):]
    if not stripped or stripped.endswith(_TERMINAL_PUNCTUATION):
        return text
    if stripped.endswith((",", ";", ":")):
        stripped = stripped[:-1] + "."
    else:
        stripped += "."
    return stripped + trailing


def join_whisper_segments(
    segments: Iterable[Any],
    *,
    pause_threshold_seconds: float = 0.65,
    detect_questions: bool = True,
) -> str:
    """Concatena segmentos usando pausas reais como limites de frase.

    Os objetos precisam expor ``text`` e podem expor ``start``/``end``. Na
    ausência de timestamps, o comportamento recua para a concatenação original.
    """
    collected: list[tuple[str, float | None, float | None]] = []
    for segment in segments:
        segment_text = str(getattr(segment, "text", "")).strip()
        if not segment_text:
            continue
        start = getattr(segment, "start", None)
        end = getattr(segment, "end", None)
        start_value = float(start) if isinstance(start, (int, float)) else None
        end_value = float(end) if isinstance(end, (int, float)) else None
        collected.append((segment_text, start_value, end_value))

    if not collected:
        return ""

    output: list[str] = [collected[0][0]]
    previous_end = collected[0][2]

    for segment_text, start, end in collected[1:]:
        if previous_end is not None and start is not None:
            pause = max(0.0, start - previous_end)
            if pause >= pause_threshold_seconds:
                output[-1] = _close_statement(output[-1])
        output.append(segment_text)
        previous_end = end

    result = " ".join(output).strip()
    if detect_questions:
        result = restore_question_marks(result)
    return ensure_terminal_punctuation(result)
