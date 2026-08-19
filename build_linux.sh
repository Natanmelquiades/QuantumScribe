#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -x ".venv-linux/bin/python" ]; then
    echo "Criando ambiente .venv-linux..."
    python3 -m venv --copies .venv-linux
fi

.venv-linux/bin/python -m pip install --require-hashes -r requirements-build-linux.lock
.venv-linux/bin/python -m pip check

echo "=== Gerando executável do QuantumScribe para Linux ==="
.venv-linux/bin/python -m PyInstaller --clean --noconfirm QuantumScribe-Linux.spec

.venv-linux/bin/python scripts/inventory_bundle.py dist/QuantumScribe \
    --output dist/QuantumScribe-inventory.json --max-bytes 262144000

echo ""
echo "Executável gerado com sucesso em: dist/QuantumScribe/QuantumScribe"
