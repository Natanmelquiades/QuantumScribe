"""Módulo de Reescrita Avançada utilizando Mini-LLMs locais via CTranslate2."""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Optional

# Evita dependência obrigatória se a opção estiver desativada,
# as importações pesadas devem ocorrer dentro das funções de inicialização.
_generator_instance = None
_tokenizer_instance = None
_current_repo_id = None
_current_device = None
_current_compute_type = None
_rewriter_lock = threading.Lock()
_is_downloading = False
_PINNED_REVISIONS = {
    "jncraton/Qwen2.5-0.5B-Instruct-ct2-int8": "4c6321ff9d93b9c0d838e4cfa1397eb75cea5ceb",
    "jncraton/Qwen2.5-3B-Instruct-ct2-int8": "973e5c34c669fe7c461bf2b6840338d16e2c5d8a",
}


def _get_model_path(repo_id: str) -> Path:
    from .config import model_dir
    # Converte o ID do repo (ex: michaelfeil/ct2fast-Qwen1.5-0.5B-Chat) em nome de pasta
    safe_name = repo_id.replace("/", "--")
    return model_dir() / "rewriter" / safe_name


def is_rewriter_downloaded(repo_id: str) -> bool:
    """Verifica se os arquivos do modelo já foram baixados."""
    model_path = _get_model_path(repo_id)
    if not model_path.exists():
        return False
    # Checa a existência dos arquivos principais
    if not (model_path / "model.bin").exists():
        return False
    if not (model_path / "tokenizer.json").exists():
        return False
    return True


def download_rewriter_model(repo_id: str, callback: Optional[callable] = None) -> bool:
    """Faz o download do modelo convertido para CTranslate2 do Hugging Face.

    Deve ser rodado em uma Thread separada se for chamado a partir da UI.
    """
    global _is_downloading
    if _is_downloading:
        return False

    with _rewriter_lock:
        try:
            _is_downloading = True
            model_path = _get_model_path(repo_id)

            if callback:
                callback(f"Iniciando download do modelo {repo_id}...")

            from huggingface_hub import snapshot_download

            revision = _PINNED_REVISIONS.get(repo_id)
            if revision is None:
                raise ValueError("Repositório de Mini-LLM não aprovado nesta versão do Quantum Scribe")

            snapshot_download(
                repo_id=repo_id,
                revision=revision,
                local_dir=str(model_path),
            )

            if callback:
                callback("Download concluído com sucesso!")
            return True
        except Exception as e:
            if callback:
                callback(f"Erro no download: {e}")
            return False
        finally:
            _is_downloading = False


def _load_rewriter(repo_id: str, device: str = "cpu", compute_type: str = "int8"):
    """Carrega o gerador e o tokenizer na memória."""
    global _generator_instance, _tokenizer_instance, _current_repo_id, _current_device, _current_compute_type

    if (_generator_instance is not None and
        _current_repo_id == repo_id and
        _current_device == device and
        _current_compute_type == compute_type):
        return

    # Libera o gerador anterior da memória se as configurações mudaram
    if _generator_instance is not None:
        del _generator_instance
        _generator_instance = None

    model_path = _get_model_path(repo_id)
    if not is_rewriter_downloaded(repo_id):
        raise RuntimeError("O modelo de reescrita ainda não foi baixado.")

    import ctranslate2
    from tokenizers import Tokenizer

    # Inicializa o tokenizer
    _tokenizer_instance = Tokenizer.from_file(str(model_path / "tokenizer.json"))

    # Inicializa o modelo
    _generator_instance = ctranslate2.Generator(
        str(model_path),
        device=device,
        compute_type=compute_type,
        inter_threads=2
    )
    _current_repo_id = repo_id
    _current_device = device
    _current_compute_type = compute_type


# ---------------------------------------------------------------------------
# Guard: decide se o LLM deve ou não processar o texto
# ---------------------------------------------------------------------------

#: Número mínimo de palavras para acionar o LLM.
#: Frases com menos palavras são devolvidas sem modificação.
_LLM_MIN_WORDS: int = 6

#: Fator máximo de crescimento: se o LLM retornar mais do que esse múltiplo
#: de palavras em relação ao input, o output é descartado (LLM alucinando).
_LLM_MAX_GROWTH_FACTOR: float = 1.4


def _should_skip_rewriter(text: str) -> bool:
    """Retorna True se o texto NÃO deve passar pelo Mini-LLM.

    Critérios de skip (retorno do texto original sem processamento):
        1. Texto tem menos de _LLM_MIN_WORDS palavras — frases curtas não
           precisam de reescrita e o LLM tende a alterar o sentido.
        2. Texto está vazio ou só tem espaços.

    Args:
        text: Texto bruto retornado pelo Whisper.

    Returns:
        True se o LLM deve ser ignorado para este texto.
    """
    if not text or not text.strip():
        return True
    word_count = len(text.strip().split())
    return word_count < _LLM_MIN_WORDS


def rewrite_text(text: str, tone_style: str, repo_id: str, device: str = "cpu", compute_type: str = "int8", is_translation: bool = False) -> str:
    """Reescreve o texto utilizando o Mini-LLM local no tom especificado.

    O modelo padrão assumido é baseado na família Qwen, suportando formato ChatML.
    """
    with _rewriter_lock:
        _load_rewriter(repo_id, device, compute_type)

        # Mapeamento do tom para a instrução
        style_instructions = {
            "natural": "Corrija ortografia, acentuação e pontuação básicas. Mantenha 100% das palavras originais, a estrutura e a coloquialidade do ditado.",
            "formal": "Reescreva com linguagem formal, profissional e vocabulário empresarial. Corrija a gramática e remova gírias.",
            "developer": "Mantenha os jargões de programação em inglês e corrija a estrutura do texto para ficar claro e técnico."
        }

        # Carrega o tom do config customizado, se existir (tem prioridade sobre padrões)
        from .config import load_config
        current_config = load_config()
        custom_instruction = None
        if hasattr(current_config, "llm_custom_tones") and tone_style in current_config.llm_custom_tones:
            custom_instruction = current_config.llm_custom_tones[tone_style].strip() or None

        if custom_instruction:
            # Tom com instrução customizada pelo usuário — usa essa diretriz para qualquer tom
            if is_translation:
                system_prompt = (
                    f"You are a rewriting assistant. Your task is to rewrite the user's English text.\n"
                    f"IMPORTANT: Output MUST remain in ENGLISH.\n"
                    f"Directive: {custom_instruction}\n"
                    f"Only output the rewritten text, without additional explanations."
                )
            else:
                system_prompt = (
                    f"Você é um assistente de reescrita em português brasileiro.\n"
                    f"Diretriz: {custom_instruction}\n"
                    f"Apenas devolva o texto reescrito, sem explicações adicionais."
                )
            user_prompt = f"Reescreva: {text}" if not is_translation else f"Rewrite: {text}"

        elif tone_style == "natural":
            if is_translation:
                system_prompt = (
                    "Correct punctuation and spelling errors in the provided English text.\n"
                    "RULES:\n"
                    "- Keep the exact same words and word order.\n"
                    "- Do NOT rewrite, alter, or summarize.\n"
                    "Return ONLY the corrected text, without quotes or explanations."
                )
                user_prompt = f'Text: "{text}"'
            else:
                system_prompt = (
                    "Corrija apenas pontuação, acentuação e erros ortográficos óbvios do texto fornecido em português brasileiro.\n"
                    "REGRAS:\n"
                    "- Mantenha exatamente as mesmas palavras e ordem original.\n"
                    "- NÃO altere o estilo, vocabulário ou use sinônimos.\n"
                    "- NÃO reescreva ou resuma.\n"
                    "Retorne APENAS o texto corrigido, sem explicações ou aspas."
                )
                user_prompt = f'Texto: "{text}"'
        else:
            instruction = style_instructions.get(tone_style, style_instructions["natural"])
            if is_translation:
                system_prompt = (
                    f"You are a rewriting assistant. Your task is to rewrite the user's English text.\n"
                    f"IMPORTANT: The user text is in ENGLISH. Your output MUST remain in ENGLISH.\n"
                    f"Style directive (apply this to the English text): {instruction}\n"
                    f"Only output the rewritten text, without additional explanations."
                )
                user_prompt = f"Reescreva isso: {text}"
            else:
                system_prompt = (
                    f"Você é um assistente de reescrita. Sua tarefa é reescrever o texto do usuário.\n"
                    f"Diretriz: {instruction}\n"
                    f"Apenas devolva o texto reescrito, sem explicações adicionais."
                )
                user_prompt = f"Reescreva isso: {text}"

        # Formato ChatML genérico
        prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        tokens = _tokenizer_instance.encode(prompt).tokens

        # Gera o texto
        step_results = _generator_instance.generate_batch(
            [tokens],
            max_length=1024,
            sampling_temperature=0.0 if tone_style == "natural" else 0.3,
            repetition_penalty=1.1,
            end_token=["<|im_end|>"],
            include_prompt_in_result=False
        )

        output_tokens = step_results[0].sequences[0]

        # Limpa o end token se tiver
        if "<|im_end|>" in output_tokens:
            output_tokens.remove("<|im_end|>")

        output_text = _tokenizer_instance.decode([_tokenizer_instance.token_to_id(t) for t in output_tokens]).strip()

        # Guard anti-alucinação:
        # 1. Se o output estiver vazio ou tiver menos de 50% das palavras do input (indica truncamento grave).
        # 2. Se o output tiver mais que 1.4x de palavras do input (indica alucinação/invenção de conteúdo).
        input_words = len(text.strip().split())
        output_words = len(output_text.strip().split()) if output_text.strip() else 0
        if output_words == 0 or output_words < input_words * 0.5 or output_words > input_words * _LLM_MAX_GROWTH_FACTOR:
            return text  # Retorna o texto original sem modificação

        # 3. Se for o modo "natural" (que deve apenas pontuar/corrigir sem reescrever):
        #    - O número de palavras não deve variar mais que 20%.
        #    - Pelo menos 80% das palavras únicas originais devem ser preservadas.
        if tone_style == "natural":
            if output_words < input_words * 0.80 or output_words > input_words * 1.20:
                return text  # Retorna o original por segurança

            # Compara a preservação do vocabulário original
            def clean_words(value: str) -> set[str]:
                return {
                    re.sub(r"[^\w\s]", "", word).lower()
                    for word in value.strip().split()
                    if word
                }

            in_set = clean_words(text)
            out_set = clean_words(output_text)
            if in_set:
                overlap = len(in_set.intersection(out_set)) / len(in_set)
                if overlap < 0.80:
                    return text  # Modificou termos demais, recua para o original

        # Se o modelo retornou o texto corrigido envolto em aspas, remove
        if output_text.startswith('"') and output_text.endswith('"'):
            output_text = output_text[1:-1].strip()
        elif output_text.startswith("'") and output_text.endswith("'"):
            output_text = output_text[1:-1].strip()
        elif output_text.startswith("«") and output_text.endswith("»"):
            output_text = output_text[1:-1].strip()

        # Limpeza robusta de introduções coloquiais comuns que o Mini-LLM gera mesmo contra regras do prompt
        patterns = [
            "aqui está a reescrita:",
            "aqui está o texto reescrito:",
            "aqui está o texto corrigido:",
            "aqui está a versão corrigida:",
            "aqui está:",
            "texto reescrito:",
            "texto corrigido:",
            "versão corrigida:",
            "reescrita:",
            "aqui está o resultado:",
            "resultado:"
        ]

        # 1. Limpeza se estiver inline (ex: "Aqui está a reescrita: texto...")
        lower_text = output_text.lower()
        for pat in patterns:
            if lower_text.startswith(pat):
                output_text = output_text[len(pat):].strip()
                break

        # 2. Limpeza se estiver em linha separada (ex: "Aqui está a reescrita:\n\ntexto...")
        lines = output_text.split("\n")
        if len(lines) > 1:
            first_line = lines[0].lower().strip()
            # Remove dois pontos finais se houver no padrão
            clean_patterns = [p.rstrip(":") for p in patterns]
            for pat in clean_patterns:
                if first_line == pat or first_line.startswith(pat):
                    output_text = "\n".join(lines[1:]).strip()
                    break

        return output_text.strip()
