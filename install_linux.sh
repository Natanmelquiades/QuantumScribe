#!/bin/bash
set -e

echo "=== Instalando dependências de sistema para QuantumScribe no Ubuntu (24 / 26) ==="

# Instala pacotes do sistema necessários para áudio, área de transferência e simulação de teclado
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip python3-tk portaudio19-dev xdotool xclip wl-clipboard
fi

echo "=== Criando ambiente virtual Python ==="
if [ ! -x ".venv-linux/bin/python" ]; then
    python3 -m venv .venv-linux
fi

echo "=== Instalando dependências Python ==="
.venv-linux/bin/pip install --upgrade pip
.venv-linux/bin/pip install -r requirements-linux.txt

echo "=== Instalação concluída com sucesso! ==="
echo "Para executar o QuantumScribe, use: ./run_linux.sh"
