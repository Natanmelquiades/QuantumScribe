from pathlib import Path

from localwhisper.backup import _safe_extract_path


def test_safe_extract_path_blocks_traversal(tmp_path):
    base_dir = tmp_path / "workspace"
    base_dir.mkdir()

    # Tentativa de traversal usando ..
    traversal_path = "../../outside.txt"
    assert _safe_extract_path(base_dir, traversal_path) is None

    # Outra tentativa de traversal usando caminho absoluto fora de base_dir
    # (Como o teste roda em Windows ou sistemas POSIX, colocamos alternativas coerentes)
    import sys
    if sys.platform == "win32":
        traversal_absolute = "C:/Windows/System32/cmd.exe"
    else:
        traversal_absolute = "/etc/passwd"

    assert _safe_extract_path(base_dir, traversal_absolute) is None

def test_safe_extract_path_allows_valid(tmp_path):
    base_dir = tmp_path / "workspace"
    base_dir.mkdir()

    # Caminho válido dentro de base_dir
    valid_path = "src/main.py"
    resolved = _safe_extract_path(base_dir, valid_path)
    assert resolved is not None
    # Deve resolver sob base_dir
    assert resolved.relative_to(base_dir) == Path("src/main.py")
