"""Download confiável e validação dos modelos Whisper locais."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from .config import is_model_downloaded, model_dir

SUPPORTED_MODELS = frozenset({"tiny", "base", "small", "medium", "large-v3"})
MODEL_REVISIONS = {
    "tiny": "d90ca5fe260221311c53c58e660288d3deb8d356",
    "base": "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66",
    "small": "536b0662742c02347bc0e980a01041f333bce120",
    "medium": "08e178d48790749d25932bbc082711ddcfdfbc4f",
    "large-v3": "edaa852ec7e145841d8ffdb056a99866b5f0a478",
}
_download_lock = threading.Lock()


class ModelDownloadError(RuntimeError):
    """Erro de instalação do modelo com uma mensagem adequada para a interface."""


def ensure_model_downloaded(
    model_name: str,
    *,
    destination: Path | None = None,
    downloader: Callable[..., str] | None = None,
) -> Path:
    """Garante que *model_name* esteja completo, retomando downloads interrompidos.

    O ``cache_dir`` é intencional: é o mesmo formato usado por ``WhisperModel``.
    Usar ``output_dir`` gravaria arquivos soltos e faria a validação acreditar que o
    modelo ainda não existe.
    """
    if model_name not in SUPPORTED_MODELS:
        raise ModelDownloadError(f"Modelo Whisper desconhecido: {model_name!r}.")

    target = destination or model_dir()
    target.mkdir(parents=True, exist_ok=True)

    with _download_lock:
        if destination is None and is_model_downloaded(model_name):
            return target
        if destination is not None and _has_complete_snapshot(target, model_name):
            return target

        try:
            if downloader is None:
                from huggingface_hub import snapshot_download

                snapshot_download(
                    repo_id=f"Systran/faster-whisper-{model_name}",
                    revision=MODEL_REVISIONS[model_name],
                    cache_dir=str(target),
                    allow_patterns=(
                        "config.json",
                        "model.bin",
                        "tokenizer.json",
                        "vocabulary.*",
                        "preprocessor_config.json",
                    ),
                )
            else:
                downloader(model_name, cache_dir=str(target))
        except Exception as error:
            raise ModelDownloadError(
                "Não foi possível baixar o modelo. Verifique a internet e o espaço "
                f"livre e tente novamente; o download será retomado. Detalhes: {error}"
            ) from error

        complete = (
            is_model_downloaded(model_name)
            if destination is None
            else _has_complete_snapshot(target, model_name)
        )
        if not complete:
            raise ModelDownloadError(
                "O download terminou, mas os arquivos essenciais do modelo não estão completos. "
                "Reabra o aplicativo para retomar."
            )
        return target


def _has_complete_snapshot(models_path: Path, model_name: str) -> bool:
    """Validação isolada para testes e diretórios alternativos de diagnóstico."""
    snapshots = (
        models_path
        / f"models--Systran--faster-whisper-{model_name}"
        / "snapshots"
    )
    if not snapshots.is_dir():
        return False
    required = ("config.json", "model.bin", "tokenizer.json")
    try:
        return any(
            snapshot.is_dir()
            and all((snapshot / name).is_file() and (snapshot / name).stat().st_size > 0 for name in required)
            for snapshot in snapshots.iterdir()
        )
    except OSError:
        return False
