import re
from pathlib import Path


def main():
    # Caminho absoluto para o __init__.py do projeto
    init_path = Path(__file__).parent / "localwhisper" / "__init__.py"
    if not init_path.exists():
        print("Arquivo __init__.py não encontrado.")
        return

    content = init_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        print("Constante __version__ não encontrada.")
        return

    old_version = match.group(1)
    parts = old_version.split(".")
    if len(parts) == 3:
        # Incrementa o último dígito (patch version)
        parts[2] = str(int(parts[2]) + 1)
        new_version = ".".join(parts)

        new_content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', content)
        init_path.write_text(new_content, encoding="utf-8")
        print(f"Versão incrementada com sucesso: {old_version} -> {new_version}")
    else:
        print(f"Formato de versão inválido: {old_version}")

if __name__ == "__main__":
    main()
