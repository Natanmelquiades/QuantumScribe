"""Integração opcional com a inicialização do Windows.

O registro ``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`` não
exige privilégios de administrador e é limitado à conta do usuário atual. Em
outros sistemas a funcionalidade permanece explicitamente indisponível, sem
tentar criar arquivos de inicialização no sistema.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:  # ``winreg`` só existe no Windows; manter o módulo importável no Linux.
    import winreg  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - executado apenas fora do Windows
    winreg = None  # type: ignore[assignment]


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "QuantumScribe"


def supports_startup() -> bool:
    """Retorna se o registro de inicialização do Windows está disponível."""
    return sys.platform == "win32" and winreg is not None


def startup_command() -> str:
    """Monta o comando seguro usado pelo Windows para iniciar o aplicativo.

    Em uma distribuição PyInstaller, ``sys.executable`` é o executável do
    Quantum Scribe. Em desenvolvimento, aponta para ``main.py`` usando o
    interpretador atual (preferindo ``pythonw.exe`` para não abrir console).
    """
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([str(Path(sys.executable).resolve())])

    project_root = Path(__file__).resolve().parents[1]
    entrypoint = project_root / "main.py"
    python_executable = Path(sys.executable).resolve()
    if sys.platform == "win32" and python_executable.name.lower() == "python.exe":
        pythonw = python_executable.with_name("pythonw.exe")
        if pythonw.is_file():
            python_executable = pythonw
    return subprocess.list2cmdline([str(python_executable), str(entrypoint)])


def set_startup_enabled(enabled: bool) -> None:
    """Ativa ou desativa o início automático para o usuário atual.

    A função é deliberadamente transacional do ponto de vista do chamador:
    qualquer erro de acesso ao registro é propagado, permitindo que a UI
    reverta o estado do switch e não prometa algo que não foi aplicado.
    """
    if not supports_startup():
        raise OSError("A inicialização com o Windows está disponível somente no Windows.")

    key = winreg.CreateKeyEx(  # type: ignore[union-attr]
        winreg.HKEY_CURRENT_USER,  # type: ignore[union-attr]
        RUN_KEY,
        0,
        winreg.KEY_SET_VALUE,  # type: ignore[union-attr]
    )
    try:
        if enabled:
            winreg.SetValueEx(  # type: ignore[union-attr]
                key, RUN_VALUE_NAME, 0, winreg.REG_SZ, startup_command()
            )
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE_NAME)  # type: ignore[union-attr]
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)  # type: ignore[union-attr]


def is_startup_enabled() -> bool:
    """Consulta se a entrada do Quantum Scribe existe no registro do usuário."""
    if not supports_startup():
        return False

    try:
        key = winreg.OpenKey(  # type: ignore[union-attr]
            winreg.HKEY_CURRENT_USER,  # type: ignore[union-attr]
            RUN_KEY,
            0,
            winreg.KEY_READ,  # type: ignore[union-attr]
        )
    except FileNotFoundError:
        return False
    try:
        value, _value_type = winreg.QueryValueEx(key, RUN_VALUE_NAME)  # type: ignore[union-attr]
        return bool(str(value).strip())
    except FileNotFoundError:
        return False
    finally:
        winreg.CloseKey(key)  # type: ignore[union-attr]


__all__ = [
    "RUN_KEY",
    "RUN_VALUE_NAME",
    "is_startup_enabled",
    "set_startup_enabled",
    "startup_command",
    "supports_startup",
]
