#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/quantumscribe"
BIN_DIR="$HOME/.local/bin"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
LAUNCHER="$BIN_DIR/quantumscribe"
DESKTOP_FILE="$APPLICATIONS_DIR/quantumscribe.desktop"

mkdir -p "$BIN_DIR" "$APPLICATIONS_DIR"

if [ "${1:-}" = "--source" ]; then
    EXECUTABLE="$SCRIPT_DIR/run_linux.sh"
    ICON="$SCRIPT_DIR/localwhisper/assets/icon.png"
    if [ ! -x "$EXECUTABLE" ]; then
        chmod +x "$EXECUTABLE"
    fi
elif [ -x "$SCRIPT_DIR/QuantumScribe/QuantumScribe" ]; then
    if [ -e "$APP_DIR" ] && [ ! -f "$APP_DIR/.quantumscribe-install" ]; then
        echo "Instalação existente sem marcador de segurança: $APP_DIR" >&2
        echo "Remova ou mova essa pasta manualmente antes de continuar." >&2
        exit 1
    fi
    rm -rf -- "$APP_DIR"
    mkdir -p "$(dirname "$APP_DIR")"
    cp -a "$SCRIPT_DIR/QuantumScribe" "$APP_DIR"
    touch "$APP_DIR/.quantumscribe-install"
    EXECUTABLE="$APP_DIR/QuantumScribe"
    ICON="$APP_DIR/_internal/localwhisper/assets/icon.png"
else
    echo "Executável do QuantumScribe não encontrado ao lado deste instalador." >&2
    exit 1
fi

printf '#!/bin/bash\nexec %q "$@"\n' "$EXECUTABLE" > "$LAUNCHER"
chmod +x "$LAUNCHER"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=QuantumScribe
Comment=Ditado por voz local com inteligência artificial
Exec="$LAUNCHER"
Icon=$ICON
Terminal=false
Categories=Utility;AudioVideo;Accessibility;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$DESKTOP_FILE"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

if command -v xdg-user-dir >/dev/null 2>&1; then
    DESKTOP_DIR="$(xdg-user-dir DESKTOP)"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP_DIR="$HOME/Desktop"
elif [ -d "$HOME/Área de Trabalho" ]; then
    DESKTOP_DIR="$HOME/Área de Trabalho"
else
    DESKTOP_DIR="$HOME/Desktop"
fi
if [ -z "$DESKTOP_DIR" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi
mkdir -p "$DESKTOP_DIR"

DESKTOP_SHORTCUT="$DESKTOP_DIR/QuantumScribe.desktop"
cp "$DESKTOP_FILE" "$DESKTOP_SHORTCUT"
chmod +x "$DESKTOP_SHORTCUT"
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_SHORTCUT" metadata::trusted true >/dev/null 2>&1 || true
fi

echo "QuantumScribe instalado no menu de aplicativos."
echo "Atalho criado em: $DESKTOP_SHORTCUT"
