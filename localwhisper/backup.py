import os
import re
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """Retorna o caminho absoluto da raiz do projeto LocalWhisper."""
    return Path(__file__).parent.parent.resolve()

def get_version() -> str:
    """Extrai a versão do sistema a partir do __init__.py sem importá-lo."""
    root = get_project_root()
    init_file = root / "localwhisper" / "__init__.py"
    if init_file.exists():
        try:
            content = init_file.read_text(encoding="utf-8")
            match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[Backup] Falha ao ler versão no init_file: {e}", exc_info=True)
    return "0.0.0"

def create_backup(code_only: bool = False) -> tuple[Path, float, int]:
    """Cria um backup completo e rápido do código do app e, opcionalmente, dos dados do usuário.

    Retorna uma tupla (zip_path, tempo_decorrido, tamanho_bytes).
    """
    from .config import app_data_dir

    start_time = time.perf_counter()

    project_root = get_project_root()
    user_data_path = app_data_dir().resolve()
    version = get_version()

    # Formato do nome do backup: backup_v{versão}_{timestamp}[_code].zip
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_code" if code_only else ""
    backup_filename = f"backup_v{version}_{timestamp}{suffix}.zip"

    backups_dir = project_root / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    zip_path = backups_dir / backup_filename

    # Pastas e arquivos a serem ignorados no código
    ignore_dirs = {".git", ".venv", "__pycache__", "build", "dist", "backups", "temp_test", ".idea", ".vscode"}
    ignore_files = {"localwhisper.err.log", "localwhisper.out.log"}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        # 1. Copiar código do aplicativo (app_code)
        for root, dirs, files in os.walk(project_root):
            # Filtra diretórios in-place para que o os.walk não entre neles
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                if file in ignore_files or file.endswith(".zip"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(project_root)
                z.write(file_path, arcname=Path("app_code") / rel_path)

        # 2. Copiar dados do usuário (user_data)
        if not code_only and user_data_path.exists():
            for root, dirs, files in os.walk(user_data_path):
                # Ignorar a pasta de modelos
                if "models" in dirs:
                    dirs.remove("models")

                for file in files:
                    # Ignorar arquivos temporários de áudio ou outros zips
                    if file.endswith(".wav") or file.endswith(".zip") or file.endswith(".tmp"):
                        continue
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(user_data_path)
                    z.write(file_path, arcname=Path("user_data") / rel_path)

    elapsed = time.perf_counter() - start_time
    file_size = zip_path.stat().st_size

    return zip_path, elapsed, file_size

def _safe_extract_path(base_dir: Path, rel_path: str) -> Path | None:
    """Retorna o caminho absoluto seguro ou None se houver path traversal."""
    try:
        target = (base_dir / rel_path).resolve()
        target.relative_to(base_dir.resolve())  # Lança ValueError se estiver fora
        return target
    except ValueError:
        return None  # Path traversal detectado

def restore_backup(zip_path: Path, code_only: bool = False) -> None:
    """Restaura o código e, opcionalmente, os dados do usuário a partir de um backup zip."""
    import logging

    from .config import app_data_dir

    project_root = get_project_root()
    user_data_path = app_data_dir().resolve()

    # Se o zip em si for código-apenas (termina com _code.zip), não restauramos user_data
    is_zip_code_only = zip_path.name.endswith("_code.zip")
    should_restore_user_data = not (code_only or is_zip_code_only)

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        has_app_code = any(name.startswith("app_code/") for name in names)
        has_user_data = any(name.startswith("user_data/") for name in names)

        if not (has_app_code or has_user_data):
            raise ValueError("Arquivo de backup inválido ou incompatível.")

        for member in z.infolist():
            if member.filename.startswith("app_code/"):
                rel_path = member.filename[len("app_code/"):]
                if not rel_path:  # Ignora pasta raiz app_code/
                    continue
                target_path = _safe_extract_path(project_root, rel_path)
                if target_path is None:
                    logging.getLogger(__name__).warning(
                        f"[Backup] Entrada ZIP suspeita bloqueada: {member.filename!r}"
                    )
                    continue
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if not member.is_dir():
                    with z.open(member) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)

            elif member.filename.startswith("user_data/") and should_restore_user_data:
                rel_path = member.filename[len("user_data/"):]
                if not rel_path:  # Ignora pasta raiz user_data/
                    continue
                target_path = _safe_extract_path(user_data_path, rel_path)
                if target_path is None:
                    logging.getLogger(__name__).warning(
                        f"[Backup] Entrada ZIP suspeita bloqueada: {member.filename!r}"
                    )
                    continue
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if not member.is_dir():
                    with z.open(member) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)

def list_backups() -> list[dict]:
    """Lista todos os backups disponíveis na pasta backups/."""
    project_root = get_project_root()
    backups_dir = project_root / "backups"

    if not backups_dir.exists():
        return []

    results = []
    for f in backups_dir.glob("backup_v*.zip"):
        filename = f.name
        match = re.match(r"backup_v([\d\.]+)_(\d{8})_(\d{6})(_code)?\.zip", filename)
        is_code_only = False
        if match:
            version = match.group(1)
            date_str = match.group(2)
            time_str = match.group(3)
            is_code_only = bool(match.group(4))

            try:
                dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                formatted_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                formatted_dt = "Desconhecido"
        else:
            version = "Desconhecido"
            mtime = os.path.getmtime(f)
            formatted_dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            if "_code" in filename:
                is_code_only = True

        stat = f.stat()
        size_kb = stat.st_size / 1024

        results.append({
            "path": f,
            "filename": filename,
            "version": version,
            "datetime": formatted_dt,
            "size_kb": size_kb,
            "code_only": is_code_only
        })

    # Ordena decrescente pela data de modificação
    results.sort(key=lambda x: x["path"].stat().st_mtime, reverse=True)
    return results

def delete_backup(zip_path: Path) -> None:
    """Exclui permanentemente um arquivo de backup."""
    if zip_path.exists():
        zip_path.unlink()
