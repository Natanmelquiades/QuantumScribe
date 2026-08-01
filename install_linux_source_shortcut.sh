#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APPLICATIONS_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
LAUNCHER="${BIN_DIR}/quantumscribe-code"
DESKTOP_FILE="${APPLICATIONS_DIR}/quantumscribe-code.desktop"
ICON="${SCRIPT_DIR}/localwhisper/assets/tray-icon.png"

mkdir -p "${BIN_DIR}" "${APPLICATIONS_DIR}"

printf '#!/usr/bin/env bash\nexec %q "$@"\n' "${SCRIPT_DIR}/run_linux.sh" > "${LAUNCHER}"
chmod +x "${LAUNCHER}"

cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=QuantumScribe (Código)
Comment=Executa diretamente o código-fonte para desenvolvimento
Exec=${LAUNCHER}
Icon=${ICON}
Terminal=false
Categories=Development;
StartupNotify=true
EOF
chmod +x "${DESKTOP_FILE}"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "${DESKTOP_FILE}"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APPLICATIONS_DIR}" >/dev/null 2>&1 || true
fi

echo "Atalho separado criado: QuantumScribe (Código)"
echo "Para executar pelo terminal: ${SCRIPT_DIR}/run_linux.sh"
