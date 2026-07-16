import os
import subprocess
import sys
import traceback
from pathlib import Path


def check_and_restart_in_venv():
    """Verifica se o script está rodando com o interpretador do ambiente virtual (.venv).
    Se não estiver, reinicia a si mesmo usando o pythonw.exe do .venv.
    """
    # O executável PyInstaller já contém seu próprio runtime. Procurar uma .venv
    # dentro do bundle só adiciona trabalho e pode causar comportamento inesperado.
    if getattr(sys, "frozen", False):
        return

    project_dir = Path(__file__).resolve().parent
    venv_dir = project_dir / ".venv"
    current_exe = Path(sys.executable).resolve()

    # Verifica se o executável atual está dentro da pasta .venv
    try:
        current_exe.relative_to(venv_dir)
        in_venv = True
    except ValueError:
        in_venv = False

    if not in_venv:
        # Localiza o executável pythonw.exe do .venv
        venv_python = venv_dir / "Scripts" / "pythonw.exe"
        if venv_python.is_file():
            args = [str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:]
            subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            sys.exit(0)

# Garante execução no ambiente virtual (.venv)
check_and_restart_in_venv()

def setup_logging():
    # Caminho do diretório de dados do app (%LOCALAPPDATA%\QuantumScribe)
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "QuantumScribe"
    base.mkdir(parents=True, exist_ok=True)
    log_path = base / "app.log"

    # Redireciona sys.stdout e sys.stderr para o arquivo com bufferização de linha
    try:
        sys.stdout = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stderr = sys.stdout
    except Exception:
        pass

    # Capturador de exceções globais não tratadas
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        sys.stderr.write("\n=== EXCEÇÃO NÃO TRATADA ===\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        sys.stderr.flush()

    sys.excepthook = handle_exception

def setup_cuda_dlls():
    """Mapeia os caminhos de instalação das DLLs do pacote nvidia e os expõe ao Windows."""
    if sys.platform != "win32":
        return

    cuda_paths = []
    # Busca a pasta 'nvidia' em todas as rotas do sys.path
    for path in sys.path:
        if not path:
            continue
        # Resolve para caminho absoluto
        nvidia_path = Path(path).resolve() / "nvidia"
        if nvidia_path.is_dir():
            # Mapeia subdiretórios com DLLs e registra no Windows
            registered = set()
            for root, dirs, files in os.walk(str(nvidia_path)):
                for file in files:
                    if file.lower().endswith(".dll"):
                        abs_root = os.path.abspath(root)
                        if abs_root not in registered:
                            try:
                                os.add_dll_directory(abs_root)
                                registered.add(abs_root)
                                cuda_paths.append(abs_root)
                            except Exception:
                                pass
                            break

    if cuda_paths:
        # Prende os caminhos de CUDA no topo do PATH do processo atual
        os.environ["PATH"] = ";".join(cuda_paths) + ";" + os.environ.get("PATH", "")

# Configura o sistema de logs antes de importar e iniciar o app
setup_logging()

# Configura caminhos das DLLs CUDA antes de iniciar
setup_cuda_dlls()

from localwhisper.app import main  # noqa: E402 (CUDA paths must be registered first)

if __name__ == "__main__":
    main()
