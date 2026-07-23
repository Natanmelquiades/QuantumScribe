#!/bin/bash
set -e

echo "=== Instalando dependências de sistema para QuantumScribe no Ubuntu (24 / 26) ==="

# Instala pacotes do sistema necessários para áudio, área de transferência e simulação de teclado
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y \
        python3-venv python3-pip python3-tk python3-dev build-essential pkg-config \
        portaudio19-dev libcairo2-dev libgirepository-2.0-dev \
        gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
        xdotool xclip wl-clipboard desktop-file-utils
fi

echo "=== Criando ambiente virtual Python ==="
if [ ! -x ".venv-linux/bin/python" ]; then
    python3 -m venv .venv-linux
fi

echo "=== Instalando dependências Python ==="
.venv-linux/bin/pip install --upgrade pip
.venv-linux/bin/pip install -r requirements-linux.txt

echo "=== Registrando aplicativo e atalho ==="
bash ./install_linux_shortcut.sh --source

echo "=== Instalação concluída com sucesso! ==="
echo "Abra o QuantumScribe pelo menu de aplicativos ou pelo atalho da área de trabalho."
