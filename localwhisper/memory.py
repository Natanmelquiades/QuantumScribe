"""Módulo de Memória Adaptativa para Aprendizado Contínuo.

Analisa as transcrições anteriores (Diário) para extrair o vocabulário mais
utilizado pelo usuário, alimentando o contexto do Whisper para que ele
"aprenda" a escrever nomes próprios, siglas e gírias frequentes.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import List

from .diary import diary_dir

STOP_WORDS = {
    "como", "você", "para", "este", "esse", "isso", "aqui", "quem", "qual", "mais",
    "muito", "então", "sobre", "quando", "onde", "porque", "depois", "ainda",
    "fazer", "falar", "dizer", "estar", "sendo", "tudo", "nada", "pode", "quero",
    "vamos", "agora", "mesmo", "também", "assim", "apenas", "sempre", "quase",
    "novo", "nova", "novo", "fui", "foi", "tem", "ter", "está", "são", "vai", "vou",
    "seja", "pela", "pelo", "qualquer", "cada", "entre", "seus", "suas", "meus", "minhas",
    "nosso", "nossa", "nossos", "nossas", "teus", "tuas", "deles", "delas", "disso",
    "dessa", "desse", "neste", "nesta", "nisso", "naquilo", "daquilo", "naquele",
    "naquela", "daquele", "daquela", "outro", "outra", "outros", "outras", "algum",
    "alguma", "alguns", "algumas", "nenhum", "nenhuma", "pouco", "pouca", "poucos",
    "poucas", "tanto", "tanta", "tantos", "tantas", "todo", "toda", "todos", "todas"
}

_cached_vocabulary: str | None = None


def invalidate_cache() -> None:
    """Invalida o cache do vocabulário para forçar uma nova extração."""
    global _cached_vocabulary
    _cached_vocabulary = None


def get_active_vocabulary(limit: int = 20, days_lookback: int = 7) -> str:
    """Obtém o vocabulário ativo como uma string formatada para o prompt do Whisper.

    Usa um cache global na memória do processo para evitar ler o disco repetidamente.
    Para invalidar, chame invalidate_cache().
    """
    global _cached_vocabulary
    if _cached_vocabulary is not None:
        return _cached_vocabulary

    vocab = _extract_vocabulary_from_logs(limit, days_lookback)
    _cached_vocabulary = ", ".join(vocab) if vocab else ""
    return _cached_vocabulary


def _extract_vocabulary_from_logs(limit: int, days_lookback: int) -> List[str]:
    """Lê os últimos diários e encontra palavras frequentes ignorando stop-words."""
    target_dir = diary_dir()
    if not target_dir.exists():
        return []

    today = datetime.now().date()
    valid_dates = [today - timedelta(days=i) for i in range(days_lookback)]
    valid_filenames = {f"{d.strftime('%Y-%m-%d')}.md" for d in valid_dates}

    text_corpus = []

    # Busca apenas nos arquivos dos últimos N dias
    for file_path in target_dir.glob("*.md"):
        if file_path.name in valid_filenames:
            try:
                # O limite de caracteres evita ler arquivos gigantes por engano
                text_corpus.append(file_path.read_text(encoding="utf-8")[:100000])
            except Exception:
                pass

    if not text_corpus:
        return []

    full_text = " ".join(text_corpus)

    # Remove marcações de horário (ex: ## 14:30)
    full_text = re.sub(r'##\s\d{2}:\d{2}', ' ', full_text)

    # Extrai palavras com 4 letras ou mais (apenas letras, e ignora números e traços isolados)
    # Acentuação no regex: usamos o re.UNICODE implicitamente no Python 3
    words = re.findall(r'\b[A-Za-zÀ-ÿ]{4,}\b', full_text)

    counter = Counter()
    for word in words:
        w_lower = word.lower()
        if w_lower not in STOP_WORDS:
            # Preserva a capitalização original se foi falada com letra maiúscula na maioria das vezes,
            # mas vamos apenas somar e depois escolher a forma mais comum.
            counter[word] += 1

    if not counter:
        return []

    # Precisamos mesclar capitalizações (ex: "LocalWhisper" e "localwhisper").
    # Vamos agrupar as formas pelo termo em lower-case.
    merged: dict[str, dict[str, int]] = {}
    for word, count in counter.items():
        low = word.lower()
        if low not in merged:
            merged[low] = Counter()
        merged[low][word] += count

    # Para cada termo, pega a capitalização que apareceu mais vezes e o total global
    final_counter = Counter()
    for low, form_counter in merged.items():
        best_form = form_counter.most_common(1)[0][0]
        total_count = sum(form_counter.values())
        # Só pega palavras que aparecem mais de 1 vez para evitar ruído de palavras raras/erros
        if total_count >= 2:
            final_counter[best_form] = total_count

    top_words = [word for word, _count in final_counter.most_common(limit)]
    return top_words
