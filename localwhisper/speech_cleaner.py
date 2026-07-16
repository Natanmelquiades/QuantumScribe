"""Módulo de Limpeza de Texto Pós-Transcrição.

Aplica regras determinísticas (sem LLM, zero latência adicional) para polir o
texto bruto do Whisper antes de entregá-lo ao usuário. Foco em:

    1. Detecção de alucinações conhecidas do Whisper → descarte do chunk
    2. Remoção de gageiras (repetições de palavras consecutivas)
    3. Correção gramatical de erros óbvios de transcrição (palavras inseridas fora de lugar)
    4. Remoção opcional de fillers (hmm, ãh, né, etc.)
    5. Normalização de capitalização de sentenças
    6. Limpeza de espaços e pontuação solta

Nenhuma dependência externa — tudo via regex Python nativo.
"""

from __future__ import annotations

import re
from typing import Set

# ---------------------------------------------------------------------------
# Alucinações conhecidas do Whisper
# Quando o áudio é muito curto, silencioso ou o modelo "trava", ele tende a
# gerar esses textos aleatoriamente. Chunks com qualquer um desses padrões
# são descartados inteiros.
# ---------------------------------------------------------------------------
_HALLUCINATION_LOWER = {
    "transcrição automática",
    "legendado por",
    "legendas por",
    "www.legendas",
    "obrigado por assistir",
    "thanks for watching",
    "please subscribe",
    "inscreva-se",
    "curta e compartilhe",
    "all rights reserved",
    "music:",
    "[música]",
    "[music]",
    "[aplausos]",
    "[silêncio]",
    "[inaudible]",
    "(inaudível)",
    "subtitles by",
    "subtitle by",
    "produced by",
}

# Padrões regex que indicam alucinação (compilados uma vez)
_HALLUCINATION_RE = re.compile(
    r"(©|™|®|\[música\]|\[music\]|\[aplausos\]|\[silêncio\])",
    re.IGNORECASE | re.UNICODE,
)

# ---------------------------------------------------------------------------
# Fillers padrão conservadores
# Removidos apenas se ativado pelo usuário. Por padrão, apenas sons sem
# conteúdo semântico claro são incluídos.
# ---------------------------------------------------------------------------
DEFAULT_FILLERS: Set[str] = {
    "hmm", "hm", "mm", "mmm",
    "ãh", "ãhh", "ah", "ahh",
    "éh", "éhh", "eh", "ehh",
    "uh", "uhh", "uhm",
    "mhm", "uhum",
}

# Padrão regex para detectar repetição de palavras (gageiras)
# Captura 2 a 4 ocorrências da mesma palavra consecutiva
_STUTTER_RE = re.compile(
    r"\b(\w{1,})((?:\s+\1){1,3})\b",
    re.IGNORECASE | re.UNICODE,
)

# ---------------------------------------------------------------------------
# Padrões de Correção Gramatical
# ---------------------------------------------------------------------------
# O Whisper frequentemente insere palavras no lugar errado, especialmente
# pronomes sujeito no meio de uma frase onde não fazem sentido gramatical.
#
# Cada entrada é uma tupla: (padrão_regex, substituição, descrição)
#
# Exemplos de erros que esses padrões corrigem:
#   "isso eu é certeza"  →  "isso é certeza"
#   "isso eu é claro"    →  "isso é claro"
#   "aquilo ela está certo" → "aquilo está certo"
#   "eu é assim"         →  "assim"
# ---------------------------------------------------------------------------

# Pronomes sujeito que o Whisper insere erroneamente
_PRONOUNS_PT = r"(?:eu|você|vc|ele|ela|eles|elas|nós|a gente|tu)"

# Verbos que geralmente seguem o sujeito correto
_VERBS_PT = r"(?:é|é|são|está|estão|estava|estavam|foi|foram|tem|têm|tinha|tinham|ser|estar|fica|ficam|ficou|ficaram|vira|viram|virou)"

# Demonstrativos e pronomes referenciais que normalmente precedem diretamente um verbo
_DEMONSTRATIVES_PT = r"(?:isso|isto|esse|essa|este|esta|aquilo|aquele|aquela|aqueles|aquelas|esses|essas|estes|estas)"

_GRAMMAR_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Padrão 1: Demonstrativo + Pronome inserido + Verbo
    # "isso eu é certeza" → "isso é certeza"
    # "isso ela está errado" → "isso está errado"
    (
        re.compile(
            rf"\b({_DEMONSTRATIVES_PT})\s+{_PRONOUNS_PT}\s+({_VERBS_PT})\b",
            re.IGNORECASE | re.UNICODE,
        ),
        r"\1 \2",
    ),
    # Padrão 2: Pronome sujeito de 1ª pessoa + verbo de 3ª pessoa ("eu é" é sempre errado)
    # "eu é assim" → "assim"  |  "e eu é isso" → "e isso"
    (
        re.compile(
            r"\beu\s+(é|está|foi|tem|tinha|estão|são)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        r"\1",  # Remove o "eu" malposto, preserva o verbo
    ),
    # Padrão 3: Artigo definido + pronome sujeito + verbo (insercão no meio de frase nominal)
    # "o eu é" → "oé" -> não aplicar, pois pode ser parte de outra frase
    # Por ora, padrões 1 e 2 já cobrem os casos mais comuns
]

# Padrão para múltiplos espaços
_MULTI_SPACE_RE = re.compile(r" {2,}")

# Padrão para capitalização após pontuação de fim de frase
_SENTENCE_START_RE = re.compile(
    r"([.!?]\s+)([a-záéíóúàâêôãõüç])",
    re.UNICODE,
)


def is_hallucination(text: str) -> bool:
    """Retorna True se o texto parece ser uma alucinação do Whisper.

    Um chunk detectado como alucinação deve ser completamente descartado,
    sem tentar salvar ou usar o texto.

    Args:
        text: Texto bruto retornado pelo Whisper.

    Returns:
        True se o texto deve ser descartado.
    """
    if not text:
        return True

    stripped = text.strip()

    # Texto muito curto (1-2 chars) ou apenas pontuação/espaços
    if len(stripped) <= 2:
        return True
    if re.fullmatch(r"[\s.,!?;:\-–—…\"'«»()\[\]]+", stripped):
        return True

    # Verifica padrões regex de alucinação
    if _HALLUCINATION_RE.search(stripped):
        return True

    # Verifica strings conhecidas de alucinação (case-insensitive)
    lower = stripped.lower()
    for pattern in _HALLUCINATION_LOWER:
        if pattern in lower:
            return True

    return False


def remove_stutters(text: str) -> str:
    """Remove repetições consecutivas de palavras (gageiras e tropeções de fala).

    Detecta padrões como:
        "eu eu eu quero"       → "eu quero"
        "vou vou fazer isso"   → "vou fazer isso"
        "o o o sistema"        → "o sistema"
        "mas mas mas"          → "mas"

    Preserva repetições intencionais de frases mais longas (não altera bigramas
    ou frases com mais de 1 palavra por repetição, para não cortar ênfases
    como "muito muito bom").

    Args:
        text: Texto de entrada com possíveis gageiras.

    Returns:
        Texto com gageiras removidas.
    """
    # Remove repetições: mantém apenas a primeira ocorrência
    result = _STUTTER_RE.sub(r"\1", text)

    # Limpa espaços duplos gerados pela remoção
    result = _MULTI_SPACE_RE.sub(" ", result)
    return result.strip()


def _build_filler_pattern(fillers: Set[str]) -> re.Pattern | None:
    """Compila padrão regex para os fillers fornecidos."""
    if not fillers:
        return None

    # Ordena por tamanho decrescente para bigramas antes de palavras
    sorted_f = sorted(fillers, key=len, reverse=True)
    escaped = [re.escape(f) for f in sorted_f]

    # Usa lookahead/lookbehind de borda de palavra não-letra para evitar
    # remover partes de palavras válidas (ex: "eh" não remove "ehm" inteiro)
    pattern_str = r"(?<![A-Za-zÀ-ÿ0-9])(" + "|".join(escaped) + r")(?![A-Za-zÀ-ÿ0-9])"
    return re.compile(pattern_str, re.IGNORECASE | re.UNICODE)


# Cache de padrão de fillers compilado
_filler_pattern_cache: dict[frozenset, re.Pattern | None] = {}


def remove_fillers(text: str, custom_fillers: Set[str] | None = None) -> str:
    """Remove palavras/sons de preenchimento do texto.

    Usa os fillers padrão (DEFAULT_FILLERS) se custom_fillers for None.
    Para desativar a remoção completamente, passe um set vazio: set().

    Args:
        text: Texto de entrada.
        custom_fillers: Set de fillers customizados. None = usa padrão.

    Returns:
        Texto com fillers removidos.
    """
    fillers = DEFAULT_FILLERS if custom_fillers is None else custom_fillers
    if not fillers:
        return text

    cache_key = frozenset(fillers)
    if cache_key not in _filler_pattern_cache:
        _filler_pattern_cache[cache_key] = _build_filler_pattern(fillers)

    pattern = _filler_pattern_cache[cache_key]
    if pattern is None:
        return text

    result = pattern.sub("", text)

    # Limpa pontuação que ficou sozinha no início e espaços extras
    result = re.sub(r"^[\s,;:.!?]+", "", result)
    result = _MULTI_SPACE_RE.sub(" ", result)
    return result.strip()


def capitalize_sentences(text: str) -> str:
    """Capitaliza a primeira letra de cada nova sentença.

    Aplica capitalização após . ! ? seguidos de espaço, e na primeira
    letra do texto.

    Args:
        text: Texto de entrada.

    Returns:
        Texto com sentenças capitalizadas.
    """
    if not text:
        return text

    # Capitaliza após pontuação de fim de sentença
    result = _SENTENCE_START_RE.sub(
        lambda m: m.group(1) + m.group(2).upper(),
        text,
    )

    # Capitaliza a primeira letra
    if result and result[0].islower():
        result = result[0].upper() + result[1:]

    return result


def fix_grammar_errors(text: str) -> str:
    """Corrige erros gramaticais óbvios causados por transcrição incorreta do Whisper.

    Aplica padrões regex para erros inequívocos em português, como pronomes sujeito
    inseridos no meio de uma frase onde não fazem nenhum sentido gramatical.

    Exemplos de correções automáticas:
        "isso eu é certeza"    →  "isso é certeza"
        "isso eu é claro"      →  "isso é claro"
        "isso ela está errado" →  "isso está errado"
        "eu é assim"           →  "assim"

    Args:
        text: Texto pós-remoção-de-gageiras para verificar e corrigir.

    Returns:
        Texto com erros gramaticais óbvios corrigidos.
    """
    result = text
    for pattern, replacement in _GRAMMAR_PATTERNS:
        result = pattern.sub(replacement, result)
    # Limpa espaços duplos que podem ter sobrado após a remoção de palavras
    result = _MULTI_SPACE_RE.sub(" ", result).strip()
    return result


def parse_custom_fillers(fillers_str: str) -> Set[str]:
    """Converte string de fillers separados por vírgula em set.

    Args:
        fillers_str: String como "hmm, ãh, né, sabe" ou "".

    Returns:
        Set de fillers. Set vazio se a string for vazia.
    """
    if not fillers_str or not fillers_str.strip():
        return set()
    parts = [f.strip().lower() for f in fillers_str.split(",")]
    return {f for f in parts if f}


def clean_transcription(
    text: str,
    remove_stutter: bool = False,
    remove_filler_words: bool = False,
    custom_fillers: Set[str] | None = None,
    literal_mode: bool = False,
) -> str | None:
    """Pipeline completo de limpeza do texto transcrito.

    Ordem de aplicação:
        1. Verifica alucinação → retorna None para descarte imediato
        2. Remove gageiras (se habilitado)
        3. Corrige erros gramaticais óbvios de transcrição (sempre ativo)
        4. Remove fillers (se habilitado)
        5. Normaliza espaços
        6. Capitaliza sentenças

    Args:
        text: Texto bruto do Whisper.
        remove_stutter: Remove repetições de palavras (gageiras).
        remove_filler_words: Remove fillers (hmm, ãh, etc.).
        custom_fillers: Set de fillers customizados. None = usa padrão.
        literal_mode: Se True, apenas rejeita alucinações conhecidas e
            preserva integralmente palavras, repetições, caixa e pontuação.

    Returns:
        Texto limpo pronto para entrega, ou None se o texto deve ser descartado.
    """
    if not text or not text.strip():
        return None

    # 1. Descarta alucinações conhecidas do Whisper
    if is_hallucination(text):
        return None

    result = text.strip()

    # No modo literal, qualquer "limpeza" linguística é uma alteração do
    # que o usuário falou. Mantemos inclusive repetições, hesitações,
    # capitalização e pontuação produzidas pelo Whisper.
    if literal_mode:
        return result

    # 2. Remove gageiras
    if remove_stutter:
        result = remove_stutters(result)

    # 3. Corrige erros gramaticais óbvios (sempre ativo — erros inequívocos)
    result = fix_grammar_errors(result)

    # 4. Remove fillers (conservador — desativado por padrão)
    if remove_filler_words:
        result = remove_fillers(result, custom_fillers)

    # 5. Normaliza espaços duplos e pontuação solta
    result = _MULTI_SPACE_RE.sub(" ", result).strip()

    # 6. Capitalização de sentenças
    result = capitalize_sentences(result)

    # Retorna None se após a limpeza ficou vazio ou muito curto
    if not result or len(result.strip()) <= 1:
        return None

    return result
