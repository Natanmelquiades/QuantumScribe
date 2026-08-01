#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/.venv-linux/bin/python"
APP_LOG="${XDG_DATA_HOME:-${HOME}/.local/share}/QuantumScribe/app.log"
PID_FILE="${XDG_DATA_HOME:-${HOME}/.local/share}/QuantumScribe/instance.pid"
SYSTEMD_UNIT="quantumscribe-code.service"

if [ ! -x "${PYTHON}" ]; then
    echo "Ambiente virtual .venv-linux não encontrado. Execute ./install_linux.sh primeiro."
    exit 1
fi

show_help() {
    cat <<'EOF'
QuantumScribe — execução direta do código no Linux

Uso:
  ./run_linux.sh               Inicia em segundo plano e libera o terminal
  ./run_linux.sh --logs        Inicia e acompanha o log ao vivo
  ./run_linux.sh --foreground  Mantém o processo ligado ao terminal (depuração)

No modo --logs, pressione Ctrl+C para fechar somente o painel de logs.
O QuantumScribe continuará funcionando em segundo plano.
EOF
}

MODE="background"
case "${1:-}" in
    --logs)
        MODE="logs"
        shift
        ;;
    --foreground)
        shift
        cd "${SCRIPT_DIR}"
        exec "${PYTHON}" main.py "$@"
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
esac

mkdir -p "$(dirname "${APP_LOG}")"
cd "${SCRIPT_DIR}"
APP_PID=""
if [ -f "${PID_FILE}" ]; then
    read -r SAVED_PID < "${PID_FILE}" || true
    if [[ "${SAVED_PID:-}" =~ ^[0-9]+$ ]] && kill -0 "${SAVED_PID}" 2>/dev/null; then
        APP_PID="${SAVED_PID}"
    fi
fi

if [ -z "${APP_PID}" ]; then
    if command -v systemd-run >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
        systemctl --user reset-failed "${SYSTEMD_UNIT}" >/dev/null 2>&1 || true
        systemd-run \
            --user \
            --unit="${SYSTEMD_UNIT%.service}" \
            --collect \
            --quiet \
            --property=Type=exec \
            --property="WorkingDirectory=${SCRIPT_DIR}" \
            --setenv="DISPLAY=${DISPLAY:-}" \
            --setenv="WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}" \
            --setenv="XAUTHORITY=${XAUTHORITY:-}" \
            --setenv="XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-}" \
            "${PYTHON}" main.py "$@"
        sleep 0.8
        APP_PID="$(systemctl --user show "${SYSTEMD_UNIT}" --property=MainPID --value)"
    else
        # Fallback para distribuições sem systemd --user. setsid remove o
        # processo da sessão do terminal e nohup ignora o fechamento da janela.
        nohup setsid "${PYTHON}" main.py "$@" </dev/null >/dev/null 2>&1 &
        APP_PID=$!
        sleep 0.8
    fi
else
    echo "QuantumScribe (Código) já estava ativo — PID ${APP_PID}."
fi

if [[ ! "${APP_PID}" =~ ^[0-9]+$ ]] || [ "${APP_PID}" -le 0 ] || ! kill -0 "${APP_PID}" 2>/dev/null; then
    echo "O QuantumScribe não permaneceu ativo. Confira o log em:"
    echo "${APP_LOG}"
    exit 1
fi

echo "QuantumScribe (Código) ativo em segundo plano — PID ${APP_PID}."
echo "Você já pode fechar este terminal."
echo "Log: ${APP_LOG}"

if [ "${MODE}" = "logs" ]; then
    echo
    echo "Acompanhando atividade (Ctrl+C fecha somente os logs):"
    echo "────────────────────────────────────────────────────────"
    touch "${APP_LOG}"
    tail -n 30 -F "${APP_LOG}"
fi
