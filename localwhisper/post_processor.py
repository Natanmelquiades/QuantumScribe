"""Módulo de pós-processamento de texto (NLP leve) do LocalWhisper.

Este módulo aplica regras e substituições ao texto transcrito pelo Whisper
antes dele ser copiado para o clipboard ou colado na janela ativa.
Foca em corrigir alucinações e erros crônicos de vocabulário do modelo.
"""

import re


def apply_custom_dict(text: str, custom_dict: dict[str, str]) -> str:
    """Substitui ocorrências de palavras cadastradas no dicionário.

    A substituição é feita usando limites de palavra (word boundaries) e
    é case-insensitive para a busca, mas respeita a capitalização exata
    definida no valor do dicionário.

    Args:
        text: O texto original transcrito.
        custom_dict: Dicionário onde a chave é o erro e o valor é o acerto.
            Exemplo: {"gaguegando": "gaguejando", "ia": "IA"}

    Returns:
        O texto com as substituições aplicadas.
    """
    if not custom_dict or not text:
        return text

    processed_text = text

    # Ordena as chaves por tamanho em ordem decrescente.
    # Isso garante que frases maiores ("inteligência artificial") sejam
    # substituídas antes de palavras menores ("inteligência") se houver conflito.
    sorted_keys = sorted(custom_dict.keys(), key=len, reverse=True)

    for error_word in sorted_keys:
        correction = custom_dict[error_word]

        # Ignora chaves vazias por segurança
        if not error_word.strip():
            continue

        # (?i) = ignore case
        # \b = word boundary (limite de palavra), evita substituir pedaços de palavras
        # re.escape garante que caracteres especiais no dicionário não quebrem a regex
        pattern = r'(?i)\b' + re.escape(error_word) + r'\b'

        # Função para substituir mantendo a compatibilidade de escape de string
        # Usamos uma função lambda para retornar a string literal da correção.
        processed_text = re.sub(pattern, lambda _: correction, processed_text)

    return processed_text
