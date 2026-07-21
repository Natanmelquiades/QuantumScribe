"""Diário de transcrições — salva cada transcrição em um arquivo .md por dia."""

from __future__ import annotations

import datetime
import re
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .config import app_data_dir

# Lock global para evitar escritas concorrentes no mesmo arquivo físico
_diary_lock = threading.Lock()
_ENTRY_HEADER = re.compile(r"^## (\d{2}:\d{2})\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class DiaryEntry:
    """Uma entrada pesquisável do diário, preservando a origem em Markdown."""

    path: Path
    date: datetime.date
    time: str
    text: str

    @property
    def preview(self) -> str:
        compact = " ".join(self.text.split())
        return compact[:140] + ("…" if len(compact) > 140 else "")


def diary_dir() -> Path:
    """Retorna o diretório do diário onde as transcrições são salvas em arquivos Markdown."""
    path = app_data_dir() / "diary"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_entry(text: str) -> None:
    """Adiciona uma entrada de transcrição ao diário do dia de forma atômica e thread-safe.

    Usa abertura do arquivo em modo append ("a") para otimização de I/O
    e previne colisões concorrentes usando um Lock de sincronização.
    """
    now = datetime.datetime.now()
    file_path = diary_dir() / f"{now:%Y-%m-%d}.md"

    with _diary_lock:
        exists = file_path.exists()
        # Abre em modo de adição com codificação utf-8
        with open(file_path, "a", encoding="utf-8") as f:
            if not exists:
                # Se o arquivo está sendo criado agora, adiciona o título do dia
                f.write(f"# {now:%Y-%m-%d}\n\n")
            f.write(f"## {now:%H:%M}\n\n{text}\n\n")


def search_entries(
    query: str,
    *,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> list[DiaryEntry]:
    """Busca texto localmente em todos os diários por frase ou palavras.

    A comparação ignora maiúsculas, acentos e variações de espaços, sem alterar
    arquivos existentes nem criar índice externo. Isso mantém o Markdown como a
    fonte de verdade enquanto o histórico visual evolui.
    """
    normalized_query = _normalize_for_search(query)
    if not normalized_query:
        return []

    results: list[DiaryEntry] = []
    for path in sorted(diary_dir().glob("*.md"), reverse=True):
        try:
            day = datetime.date.fromisoformat(path.stem)
        except ValueError:
            continue
        if start_date and day < start_date:
            continue
        if end_date and day > end_date:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        headers = list(_ENTRY_HEADER.finditer(content))
        for index, header in enumerate(headers):
            body_start = header.end()
            body_end = headers[index + 1].start() if index + 1 < len(headers) else len(content)
            text = content[body_start:body_end].strip()
            if normalized_query in _normalize_for_search(text):
                results.append(DiaryEntry(path=path, date=day, time=header.group(1), text=text))

    return sorted(results, key=lambda entry: (entry.date, entry.time), reverse=True)


def _normalize_for_search(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return " ".join(without_accents.split())


def save_comparison_log(raw_text: str, processed_text: str, tone: str, rewriter_active: bool) -> None:
    """Salva um comparativo entre o texto bruto do Whisper e o texto processado/enviado."""
    now = datetime.datetime.now()
    log_path = app_data_dir() / "transcription_comparison.md"

    with _diary_lock:
        exists = log_path.exists()
        with open(log_path, "a", encoding="utf-8") as f:
            if not exists:
                f.write("# Histórico Comparativo de Transcrições (Debug)\n\n")
                f.write("Este arquivo registra a diferença entre o que o Whisper ouviu literalmente e o que a IA entregou após reescrita/limpeza.\n\n")
                f.write("| Data/Hora | Tom | Mini-LLM Ativo? | Transcrição Bruta (Whisper) | Texto Enviado (Final) |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")

            # Limpa quebras de linha para caber na linha da tabela Markdown
            raw_clean = raw_text.replace("\n", " ").replace("|", "\\|")
            proc_clean = processed_text.replace("\n", " ").replace("|", "\\|")
            rewriter_status = "Sim" if rewriter_active else "Não"

            f.write(f"| {now:%Y-%m-%d %H:%M:%S} | {tone} | {rewriter_status} | {raw_clean} | {proc_clean} |\n")
