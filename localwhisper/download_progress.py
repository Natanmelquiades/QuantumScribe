"""Progresso percentual real para downloads de modelos (Hugging Face Hub).

O faster-whisper e o huggingface_hub baixam cada arquivo com uma barra tqdm
independente. Este módulo agrega todas as barras em um único percentual global
(monotônico e gradual), permitindo que a interface exiba uma barra de progresso
que avança de forma contínua — 10%, 20%, 35%... — em vez da antiga animação
indeterminada que ficava "indo e voltando".
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path

ProgressCallback = Callable[[float, int, int], None]
"""Assinatura do callback: (percentual 0-100, bytes baixados, bytes totais)."""


class _ProgressSession:
    """Agrega o progresso de todos os arquivos de um snapshot em percentual único."""

    def __init__(self, on_progress: ProgressCallback | None) -> None:
        self._on_progress = on_progress
        self._lock = threading.Lock()
        self._bars: dict[int, list[float]] = {}  # id(tqdm) -> [baixado, total]
        self._last_emit = 0.0
        self._last_percent = -1.0

    def make_tqdm_class(self):
        """Retorna uma subclasse de tqdm conectada a esta sessão de progresso."""
        from tqdm import tqdm

        session = self

        class _AggregatedTqdm(tqdm):
            def __init__(self, *args, **kwargs):
                kwargs["disable"] = True  # Nunca desenhar no console; só medir.
                super().__init__(*args, **kwargs)
                with session._lock:
                    session._bars[id(self)] = [0.0, float(self.total or 0)]
                session._emit(force=True)

            def update(self, n=1):
                super().update(n)
                with session._lock:
                    bar = session._bars.get(id(self))
                    if bar is not None:
                        bar[0] = float(self.n)
                        if not bar[1] and self.total:
                            bar[1] = float(self.total)
                session._emit()

            def close(self):
                with session._lock:
                    bar = session._bars.get(id(self))
                    if bar is not None and bar[1]:
                        bar[0] = bar[1]  # Arquivo concluído conta como 100%.
                try:
                    super().close()
                finally:
                    session._emit(force=True)

        return _AggregatedTqdm

    def _emit(self, force: bool = False) -> None:
        if self._on_progress is None:
            return
        with self._lock:
            downloaded = sum(b[0] for b in self._bars.values())
            total = sum(b[1] for b in self._bars.values())
            percent = (downloaded / total * 100.0) if total > 0 else 0.0
            now = time.monotonic()
            # Limita a taxa de emissão para não inundar a fila de eventos da UI.
            if not force and (now - self._last_emit) < 0.1 and percent < 100.0:
                return
            # Garante barra monotônica: nunca anda para trás.
            percent = max(percent, self._last_percent)
            self._last_percent = percent
            self._last_emit = now
        try:
            self._on_progress(min(percent, 100.0), int(downloaded), int(total))
        except Exception:
            pass


def download_whisper_with_progress(
    model_name: str,
    cache_dir: str | Path,
    on_progress: ProgressCallback | None = None,
) -> str:
    """Baixa um modelo Whisper Systran reportando percentual global real.

    Espelha o comportamento de ``faster_whisper.download_model`` (mesmo repo,
    mesmos padrões de arquivo e mesmo cache_dir), mas com barras agregadas.
    """
    from huggingface_hub import snapshot_download

    session = _ProgressSession(on_progress)
    allow_patterns = [
        "config.json",
        "preprocessor_config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.*",
    ]
    return snapshot_download(
        repo_id=f"Systran/faster-whisper-{model_name}",
        allow_patterns=allow_patterns,
        cache_dir=str(cache_dir),
        tqdm_class=session.make_tqdm_class(),
    )


def download_snapshot_with_progress(
    repo_id: str,
    local_dir: str | Path,
    on_progress: ProgressCallback | None = None,
) -> str:
    """Baixa um repositório genérico do Hub (ex.: Mini-LLM) com percentual real."""
    from huggingface_hub import snapshot_download

    session = _ProgressSession(on_progress)
    return snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        tqdm_class=session.make_tqdm_class(),
    )


def format_bytes(num_bytes: int) -> str:
    """Formata bytes em texto amigável (ex.: '342 MB')."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.0f} {unit}" if value >= 100 else f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} GB"
