#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -x ".venv-linux/bin/python" ]; then
    echo "Ambiente virtual .venv-linux não encontrado. Execute ./install_linux.sh primeiro."
    exit 1
fi

exec .venv-linux/bin/python main.py "$@"
