"""Seleção segura e adaptativa do hardware usado pelos modelos locais."""

from __future__ import annotations

import ctypes
import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_CUDA_DLL_HANDLES: list[object] = []
_CUDA_DLL_DIRS: set[str] = set()


@dataclass(frozen=True, slots=True)
class HardwareSelection:
    """Dispositivo e precisão efetivamente seguros para a sessão atual."""

    device: str
    compute_type: str
    cuda_available: bool
    detail: str


def setup_cuda_dlls() -> tuple[str, ...]:
    """Registra as DLLs NVIDIA tanto no Python local quanto no bundle instalado."""
    if sys.platform != "win32":
        return ()

    roots = [Path(path).resolve() for path in sys.path if path]
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        roots.append(Path(frozen_root).resolve())
    roots.append(Path(sys.executable).resolve().parent / "_internal")

    for root in dict.fromkeys(roots):
        nvidia_path = root / "nvidia"
        if not nvidia_path.is_dir():
            continue
        for dll in nvidia_path.rglob("*.dll"):
            dll_dir = str(dll.parent.resolve())
            if dll_dir in _CUDA_DLL_DIRS:
                continue
            try:
                _CUDA_DLL_HANDLES.append(os.add_dll_directory(dll_dir))
                _CUDA_DLL_DIRS.add(dll_dir)
            except (OSError, AttributeError):
                continue

    if _CUDA_DLL_DIRS:
        current_path = os.environ.get("PATH", "")
        prefix = ";".join(sorted(_CUDA_DLL_DIRS))
        if not current_path.startswith(prefix):
            os.environ["PATH"] = prefix + ";" + current_path
    return tuple(sorted(_CUDA_DLL_DIRS))


def _load_required_cuda_libraries() -> None:
    """Antecipa o carregamento que o CTranslate2 normalmente faz só no decode."""
    if sys.platform != "win32":
        return

    setup_cuda_dlls()

    # cuBLAS e cuDNN são dependências de runtime do faster-whisper em CUDA.
    # Carregá-las aqui evita descobrir uma instalação incompleta somente depois
    # que o modelo inteiro já foi alocado na GPU.
    ctypes.WinDLL("cublas64_12.dll")
    ctypes.WinDLL("cudnn64_9.dll")


@lru_cache(maxsize=1)
def cuda_runtime_status() -> tuple[bool, str]:
    """Informa se GPU NVIDIA e runtime CUDA estão realmente utilizáveis."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() < 1:
            return False, "nenhuma GPU NVIDIA compatível foi encontrada"

        _load_required_cuda_libraries()
        supported = ctranslate2.get_supported_compute_types("cuda")
        if not supported:
            return False, "o CTranslate2 não informou precisões CUDA compatíveis"
    except Exception as error:
        return False, f"runtime CUDA indisponível: {error}"

    return True, "GPU NVIDIA e runtime CUDA disponíveis"


def _safe_compute_type(device: str, requested: str) -> str:
    requested = (requested or "auto").strip().lower()
    try:
        import ctranslate2

        supported = set(ctranslate2.get_supported_compute_types(device))
    except Exception:
        supported = {"int8", "int8_float32", "float32"} if device == "cpu" else {"float16", "int8"}

    if requested != "auto" and requested in supported:
        return requested

    preferences = (
        ("float16", "int8_float16", "int8", "float32")
        if device == "cuda"
        else ("int8", "int8_float32", "int16", "float32")
    )
    return next((item for item in preferences if item in supported), "float32")


def resolve_hardware(requested_device: str, requested_compute_type: str) -> HardwareSelection:
    """Resolve a preferência do usuário para o hardware disponível de verdade."""
    requested = (requested_device or "auto").strip().lower()
    if requested not in {"auto", "cpu", "cuda"}:
        requested = "auto"

    if requested == "cpu":
        return HardwareSelection(
            device="cpu",
            compute_type=_safe_compute_type("cpu", requested_compute_type),
            cuda_available=False,
            detail="CPU selecionada nas configurações",
        )

    cuda_available, detail = cuda_runtime_status()
    device = "cuda" if cuda_available else "cpu"
    return HardwareSelection(
        device=device,
        compute_type=_safe_compute_type(device, requested_compute_type),
        cuda_available=cuda_available,
        detail=detail,
    )
