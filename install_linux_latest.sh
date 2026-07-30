#!/usr/bin/env bash
set -euo pipefail

readonly QS_REPOSITORY="Natanmelquiades/QuantumScribe"
readonly QS_RELEASE_API_URL="${QS_RELEASE_API_URL:-https://api.github.com/repos/${QS_REPOSITORY}/releases/latest}"
readonly QS_USER_AGENT="QuantumScribe-Linux-Installer/1"
readonly QS_DATA_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}"
readonly QS_APP_DIR="${QS_DATA_ROOT}/quantumscribe"
readonly QS_USER_DATA_DIR="${QS_DATA_ROOT}/QuantumScribe"
readonly QS_LAUNCHER="$HOME/.local/bin/quantumscribe"
readonly QS_PID_FILE="${QS_USER_DATA_DIR}/instance.pid"

QS_TEMP_DIR=""

log() {
    printf '[QuantumScribe] %s\n' "$*"
}

fail() {
    printf '[QuantumScribe] ERRO: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Instala a release final mais recente do QuantumScribe no Linux x64.

Uso:
  bash install_linux_latest.sh

Variáveis opcionais:
  QS_SKIP_SYSTEM_DEPENDENCIES=1  não executa apt-get
  QS_NO_START=1                 não inicia o aplicativo após instalar
  QS_VERIFY_ONLY=1              baixa e valida sem instalar
EOF
}

cleanup() {
    local temp_root="${TMPDIR:-/tmp}"
    if [[ -n "$QS_TEMP_DIR" && "$QS_TEMP_DIR" == "${temp_root%/}"/quantumscribe-install.* ]]; then
        rm -rf -- "$QS_TEMP_DIR"
    fi
}
trap cleanup EXIT INT TERM

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    "")
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

case "$(uname -m)" in
    x86_64|amd64)
        ;;
    *)
        fail "Esta distribuição oficial exige Linux x64 (x86_64)."
        ;;
esac

install_system_dependencies() {
    if [[ "${QS_SKIP_SYSTEM_DEPENDENCIES:-0}" == "1" ]]; then
        log "Instalação automática das dependências foi ignorada."
        return
    fi

    if ! command -v apt-get >/dev/null 2>&1; then
        fail "A instalação automática das dependências suporta Ubuntu/Debian. Instale curl, python3, xdotool, xclip, wl-clipboard, AppIndicator e desktop-file-utils pelo gerenciador da sua distribuição e execute novamente com QS_SKIP_SYSTEM_DEPENDENCIES=1."
    fi

    local -a privilege=()
    if [[ "$EUID" -ne 0 ]]; then
        command -v sudo >/dev/null 2>&1 || fail "O comando sudo é necessário para instalar as dependências do sistema."
        privilege=(sudo)
    fi

    log "Instalando dependências do sistema (pode solicitar sua senha)..."
    "${privilege[@]}" apt-get update
    "${privilege[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y \
        ca-certificates curl python3 python3-tk portaudio19-dev \
        gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
        xdotool xclip wl-clipboard desktop-file-utils
}

require_commands() {
    local command_name
    for command_name in curl python3 sha256sum tar uname; do
        command -v "$command_name" >/dev/null 2>&1 || fail "Comando obrigatório não encontrado: $command_name"
    done
}

stop_existing_package() {
    [[ -f "$QS_PID_FILE" ]] || return

    local pid
    pid="$(tr -dc '0-9' < "$QS_PID_FILE")"
    [[ -n "$pid" ]] || return
    kill -0 "$pid" 2>/dev/null || return

    local expected_executable="$QS_APP_DIR/QuantumScribe"
    local running_executable
    running_executable="$(readlink -f "/proc/$pid/exe" 2>/dev/null || true)"
    if [[ -z "$running_executable" || "$running_executable" != "$(readlink -f "$expected_executable" 2>/dev/null || true)" ]]; then
        fail "Há uma instância ativa do QuantumScribe que não pertence ao pacote instalado. Feche-a e execute o instalador novamente."
    fi

    log "Encerrando a versão instalada antes da substituição..."
    kill -TERM "$pid"
    local attempt
    for attempt in {1..50}; do
        kill -0 "$pid" 2>/dev/null || return
        sleep 0.2
    done
    fail "O QuantumScribe não encerrou no tempo esperado. Feche-o manualmente e tente novamente."
}

install_system_dependencies
require_commands

temp_root="${TMPDIR:-/tmp}"
QS_TEMP_DIR="$(mktemp -d "${temp_root%/}/quantumscribe-install.XXXXXX")"
readonly QS_TEMP_DIR
readonly QS_RELEASE_JSON="$QS_TEMP_DIR/release.json"
readonly QS_RELEASE_METADATA="$QS_TEMP_DIR/release-metadata.txt"

log "Consultando a release final mais recente..."
curl --fail --silent --show-error --location \
    --retry 3 --retry-all-errors \
    --header "Accept: application/vnd.github+json" \
    --header "X-GitHub-Api-Version: 2022-11-28" \
    --user-agent "$QS_USER_AGENT" \
    "$QS_RELEASE_API_URL" \
    --output "$QS_RELEASE_JSON"

python3 - "$QS_RELEASE_JSON" "$QS_REPOSITORY" > "$QS_RELEASE_METADATA" <<'PY'
import json
import re
import sys
from pathlib import Path

release_path = Path(sys.argv[1])
repository = sys.argv[2]
release = json.loads(release_path.read_text(encoding="utf-8"))

if release.get("draft") or release.get("prerelease"):
    raise SystemExit("A API retornou uma release que não é final.")

tag = str(release.get("tag_name", ""))
if re.fullmatch(r"v\d+\.\d+\.\d+", tag) is None:
    raise SystemExit(f"Tag de release inválida: {tag!r}")

version = tag.removeprefix("v")
linux_name = f"QuantumScribe-Core-{version}-Linux-x64.tar.gz"
assets = release.get("assets") or []
by_name = {
    str(asset.get("name")): str(asset.get("browser_download_url"))
    for asset in assets
    if asset.get("name") and asset.get("browser_download_url")
}

required = (linux_name, "SHA256SUMS.txt")
missing = [name for name in required if name not in by_name]
if missing:
    raise SystemExit(f"Assets obrigatórios ausentes: {', '.join(missing)}")

expected_prefix = f"https://github.com/{repository}/releases/download/{tag}/"
for name in required:
    if not by_name[name].startswith(expected_prefix):
        raise SystemExit(f"URL de asset fora da release oficial: {name}")

print(tag)
print(linux_name)
print(by_name[linux_name])
print(by_name["SHA256SUMS.txt"])
PY

mapfile -t release_fields < "$QS_RELEASE_METADATA"
[[ "${#release_fields[@]}" -eq 4 ]] || fail "Metadados incompletos na release oficial."

readonly QS_RELEASE_TAG="${release_fields[0]}"
readonly QS_ARCHIVE_NAME="${release_fields[1]}"
readonly QS_ARCHIVE_URL="${release_fields[2]}"
readonly QS_CHECKSUM_URL="${release_fields[3]}"
readonly QS_ARCHIVE_PATH="$QS_TEMP_DIR/$QS_ARCHIVE_NAME"
readonly QS_CHECKSUM_PATH="$QS_TEMP_DIR/SHA256SUMS.txt"
readonly QS_EXTRACT_DIR="$QS_TEMP_DIR/extracted"

log "Baixando $QS_ARCHIVE_NAME..."
curl --fail --silent --show-error --location \
    --retry 3 --retry-all-errors \
    --user-agent "$QS_USER_AGENT" \
    "$QS_ARCHIVE_URL" \
    --output "$QS_ARCHIVE_PATH"
curl --fail --silent --show-error --location \
    --retry 3 --retry-all-errors \
    --user-agent "$QS_USER_AGENT" \
    "$QS_CHECKSUM_URL" \
    --output "$QS_CHECKSUM_PATH"

mapfile -t expected_hashes < <(
    awk -v filename="$QS_ARCHIVE_NAME" '{
        asset_name = $2
        sub(/\r$/, "", asset_name)
        if (asset_name == filename) {
            print tolower($1)
        }
    }' "$QS_CHECKSUM_PATH"
)
[[ "${#expected_hashes[@]}" -eq 1 ]] || fail "Checksum único do pacote Linux não encontrado."
readonly QS_EXPECTED_HASH="${expected_hashes[0]}"
[[ "$QS_EXPECTED_HASH" =~ ^[0-9a-f]{64}$ ]] || fail "Checksum SHA-256 inválido."

readonly QS_ACTUAL_HASH="$(sha256sum "$QS_ARCHIVE_PATH" | awk '{ print tolower($1) }')"
[[ "$QS_ACTUAL_HASH" == "$QS_EXPECTED_HASH" ]] || fail "O pacote baixado não passou na validação SHA-256."
log "Checksum SHA-256 validado."

mkdir -p "$QS_EXTRACT_DIR"
python3 - "$QS_ARCHIVE_PATH" "$QS_EXTRACT_DIR" <<'PY'
import pathlib
import tarfile
import sys

archive_path = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
allowed_roots = {"QuantumScribe", "install_linux_shortcut.sh"}
required_paths = {"QuantumScribe/QuantumScribe", "install_linux_shortcut.sh"}

with tarfile.open(archive_path, "r:gz") as archive:
    names = set()
    for member in archive.getmembers():
        path = pathlib.PurePosixPath(member.name)
        if not member.name or path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"Caminho inseguro no pacote: {member.name!r}")
        if path.parts[0] not in allowed_roots:
            raise SystemExit(f"Item inesperado no pacote: {member.name!r}")
        if member.isdev():
            raise SystemExit(f"Dispositivo não permitido no pacote: {member.name!r}")
        if member.issym():
            target = path.parent / member.linkname
            if target.is_absolute() or ".." in target.parts:
                raise SystemExit(f"Link simbólico inseguro: {member.name!r}")
        if member.islnk():
            target = pathlib.PurePosixPath(member.linkname)
            if target.is_absolute() or ".." in target.parts:
                raise SystemExit(f"Hard link inseguro: {member.name!r}")
        names.add(member.name.rstrip("/"))

    missing = required_paths - names
    if missing:
        raise SystemExit(f"Layout obrigatório ausente: {', '.join(sorted(missing))}")

    archive.extractall(destination, filter="data")
PY

readonly QS_INSTALLER="$QS_EXTRACT_DIR/install_linux_shortcut.sh"
readonly QS_PACKAGED_EXECUTABLE="$QS_EXTRACT_DIR/QuantumScribe/QuantumScribe"
[[ -f "$QS_INSTALLER" && ! -L "$QS_INSTALLER" ]] || fail "Instalador Linux inválido no pacote."
[[ -x "$QS_PACKAGED_EXECUTABLE" && ! -L "$QS_PACKAGED_EXECUTABLE" ]] || fail "Executável Linux inválido no pacote."

if [[ "${QS_VERIFY_ONLY:-0}" == "1" ]]; then
    log "$QS_RELEASE_TAG baixado, validado e extraído com segurança."
    exit 0
fi

stop_existing_package
log "Instalando $QS_RELEASE_TAG para o usuário atual..."
bash "$QS_INSTALLER"

if [[ "${QS_NO_START:-0}" != "1" && ( -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ) ]]; then
    log "Iniciando o QuantumScribe..."
    if command -v setsid >/dev/null 2>&1; then
        setsid -f "$QS_LAUNCHER"
    else
        nohup "$QS_LAUNCHER" >/dev/null 2>&1 &
    fi
fi

log "$QS_RELEASE_TAG instalado com sucesso."
log "Seus modelos e configurações permanecem em: $QS_USER_DATA_DIR"
