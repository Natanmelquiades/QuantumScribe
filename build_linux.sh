#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -x ".venv-linux/bin/python" ]; then
    echo "Criando ambiente .venv-linux..."
    python3 -m venv .venv-linux
fi

.venv-linux/bin/pip install -r requirements-linux.txt
.venv-linux/bin/pip install "pyinstaller>=6.18,<7"

echo "=== Gerando executável do QuantumScribe para Linux ==="
.venv-linux/bin/python -m PyInstaller --clean --noconfirm QuantumScribe-Linux.spec

echo ""
echo "Executável gerado com sucesso em: dist/QuantumScribe/QuantumScribe"
