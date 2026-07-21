"""Atualização segura do aplicativo a partir das releases oficiais do GitHub."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__
from .config import app_data_dir

_LATEST_RELEASE_API = "https://api.github.com/repos/Natanmelquiades/QuantumScribe/releases/latest"
_REPOSITORY = "Natanmelquiades/QuantumScribe"
_ALLOWED_HOSTS = {
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}
_MAX_RELEASE_METADATA_BYTES = 1024 * 1024
_MAX_CHECKSUM_BYTES = 1024 * 1024
_MAX_INSTALLER_BYTES = 500 * 1024 * 1024
_VERSION_PATTERN = re.compile(r"^(?:v)?(\d+)\.(\d+)\.(\d+)$")


class UpdateError(RuntimeError):
    """Falha segura e apresentável ao usuário durante a atualização."""


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    name: str
    url: str
    size: int


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    version: str
    release_url: str
    installer: ReleaseAsset
    checksums: ReleaseAsset


def parse_version(value: str) -> tuple[int, int, int]:
    match = _VERSION_PATTERN.fullmatch(value.strip())
    if not match:
        raise UpdateError(f"Versão inválida recebida: {value}")
    return tuple(int(part) for part in match.groups())


def _validate_url(url: str, *, expected_host: str | None = None) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in _ALLOWED_HOSTS:
        raise UpdateError("A atualização apontou para um endereço não autorizado.")
    if expected_host and host != expected_host:
        raise UpdateError("A atualização não veio do serviço oficial esperado.")
    if parsed.username or parsed.password or parsed.fragment:
        raise UpdateError("A atualização contém um endereço inválido.")
    return parsed


def _request(url: str) -> urllib.request.Request:
    _validate_url(url)
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"QuantumScribe/{__version__}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def _read_url(url: str, max_bytes: int) -> bytes:
    try:
        with urllib.request.urlopen(_request(url), timeout=30) as response:
            _validate_url(response.geturl())
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise UpdateError("A resposta de atualização excede o tamanho permitido.")
            data = response.read(max_bytes + 1)
    except UpdateError:
        raise
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise UpdateError("Não foi possível acessar o GitHub. Verifique sua conexão e tente novamente.") from error
    if len(data) > max_bytes:
        raise UpdateError("A resposta de atualização excede o tamanho permitido.")
    return data


def _asset_from_release(assets: object, name: str, version: str) -> ReleaseAsset:
    if not isinstance(assets, list):
        raise UpdateError("A release oficial possui metadados de arquivos inválidos.")
    matches = [item for item in assets if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1:
        raise UpdateError(f"A release não contém exatamente um arquivo {name}.")
    item = matches[0]
    try:
        asset = ReleaseAsset(name=name, url=str(item["browser_download_url"]), size=int(item["size"]))
    except (KeyError, TypeError, ValueError) as error:
        raise UpdateError(f"Os metadados do arquivo {name} são inválidos.") from error
    parsed = _validate_url(asset.url, expected_host="github.com")
    expected_path = f"/{_REPOSITORY}/releases/download/v{version}/{name}"
    if parsed.path != expected_path:
        raise UpdateError(f"O arquivo {name} não pertence à release oficial esperada.")
    return asset


def check_for_update(current_version: str = __version__) -> UpdateInfo | None:
    """Retorna a release final mais recente somente quando ela for uma atualização."""
    try:
        payload = json.loads(_read_url(_LATEST_RELEASE_API, _MAX_RELEASE_METADATA_BYTES))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpdateError("O GitHub retornou dados de atualização inválidos.") from error
    if not isinstance(payload, dict) or payload.get("draft") or payload.get("prerelease"):
        raise UpdateError("A última release disponível não é uma versão pública final.")

    tag = str(payload.get("tag_name", ""))
    latest_tuple = parse_version(tag)
    if latest_tuple <= parse_version(current_version):
        return None
    version = ".".join(str(part) for part in latest_tuple)
    installer_name = f"QuantumScribe-Setup-{version}-Windows-x64.exe"
    installer = _asset_from_release(payload.get("assets"), installer_name, version)
    checksums = _asset_from_release(payload.get("assets"), "SHA256SUMS.txt", version)
    if not (1024 * 1024 <= installer.size <= _MAX_INSTALLER_BYTES):
        raise UpdateError("O tamanho declarado do instalador é inválido.")
    if not (1 <= checksums.size <= _MAX_CHECKSUM_BYTES):
        raise UpdateError("O tamanho declarado dos hashes é inválido.")

    release_url = str(payload.get("html_url", ""))
    parsed_release = _validate_url(release_url, expected_host="github.com")
    if parsed_release.path != f"/{_REPOSITORY}/releases/tag/v{version}":
        raise UpdateError("A página da release não corresponde à versão encontrada.")
    return UpdateInfo(version, release_url, installer, checksums)


def _expected_hash(checksums: bytes, asset_name: str) -> str:
    try:
        text = checksums.decode("ascii")
    except UnicodeDecodeError as error:
        raise UpdateError("O arquivo de verificação da release é inválido.") from error
    matches: list[str] = []
    for line in text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        digest, filename = parts[0].lower(), parts[1].lstrip("* ")
        if filename == asset_name and re.fullmatch(r"[0-9a-f]{64}", digest):
            matches.append(digest)
    if len(matches) != 1:
        raise UpdateError("A release não contém um hash SHA-256 único para o instalador.")
    return matches[0]


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest().lower() != expected.lower():
        raise UpdateError("O instalador baixado falhou na verificação de segurança SHA-256.")


def _download_installer(
    asset: ReleaseAsset,
    destination: Path,
    on_progress: Callable[[int, int], None] | None,
) -> None:
    received = 0
    try:
        with urllib.request.urlopen(_request(asset.url), timeout=30) as response:
            _validate_url(response.geturl())
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > _MAX_INSTALLER_BYTES:
                raise UpdateError("O instalador excede o tamanho máximo permitido.")
            with destination.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > _MAX_INSTALLER_BYTES:
                        raise UpdateError("O instalador excede o tamanho máximo permitido.")
                    output.write(chunk)
                    if on_progress:
                        on_progress(received, asset.size)
    except UpdateError:
        raise
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise UpdateError("O download do instalador foi interrompido. Tente novamente.") from error
    if received != asset.size:
        raise UpdateError("O tamanho baixado não corresponde ao arquivo publicado no GitHub.")


def download_update(
    info: UpdateInfo,
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[Path, str]:
    """Baixa e valida o instalador, sem executá-lo."""
    checksums = _read_url(info.checksums.url, _MAX_CHECKSUM_BYTES)
    expected = _expected_hash(checksums, info.installer.name)
    update_dir = app_data_dir() / "updates" / info.version
    update_dir.mkdir(parents=True, exist_ok=True)
    installer = update_dir / info.installer.name
    partial = installer.with_suffix(installer.suffix + ".part")
    try:
        if installer.is_file():
            try:
                verify_sha256(installer, expected)
                return installer, expected
            except UpdateError:
                installer.unlink(missing_ok=True)
        partial.unlink(missing_ok=True)
        _download_installer(info.installer, partial, on_progress)
        verify_sha256(partial, expected)
        os.replace(partial, installer)
        return installer, expected
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def schedule_update_after_exit(installer: Path, expected_hash: str, parent_pid: int) -> None:
    """Agenda instalação silenciosa somente depois que o processo atual encerrar."""
    installer = installer.resolve()
    if sys.platform != "win32":
        raise UpdateError("A atualização automática está disponível somente no Windows.")
    if not installer.is_file() or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        raise UpdateError("O instalador preparado para atualização é inválido.")
    verify_sha256(installer, expected_hash)

    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    powershell = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not powershell.is_file():
        raise UpdateError("O atualizador do Windows não foi encontrado.")
    installed_app = Path(os.environ.get("LOCALAPPDATA", app_data_dir().parent)) / "Programs" / "QuantumScribe" / "QuantumScribe.exe"
    status_file = installer.parent / "update-status.txt"

    def ps_literal(path: Path) -> str:
        return "'" + str(path).replace("'", "''") + "'"

    script = f"""
$ErrorActionPreference = 'Stop'
$status = {ps_literal(status_file)}
try {{
  $deadline = [DateTime]::UtcNow.AddSeconds(60)
  while ((Get-Process -Id {int(parent_pid)} -ErrorAction SilentlyContinue) -and [DateTime]::UtcNow -lt $deadline) {{
    Start-Sleep -Milliseconds 250
  }}
  if (Get-Process -Id {int(parent_pid)} -ErrorAction SilentlyContinue) {{ throw 'O aplicativo não encerrou a tempo.' }}
  $actual = (Get-FileHash -LiteralPath {ps_literal(installer)} -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne '{expected_hash.lower()}') {{ throw 'SHA-256 do instalador não corresponde à release.' }}
  $setup = Start-Process -FilePath {ps_literal(installer)} -ArgumentList '/S' -PassThru -Wait
  if ($setup.ExitCode -ne 0) {{ throw "Instalador encerrou com código $($setup.ExitCode)." }}
  'success' | Set-Content -LiteralPath $status -Encoding UTF8
  if (Test-Path -LiteralPath {ps_literal(installed_app)}) {{ Start-Process -FilePath {ps_literal(installed_app)} }}
}} catch {{
  $_.Exception.Message | Set-Content -LiteralPath $status -Encoding UTF8
  exit 1
}}
""".strip()
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    try:
        subprocess.Popen(
            [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creation_flags,
        )
    except OSError as error:
        raise UpdateError("Não foi possível iniciar o atualizador do Windows.") from error
