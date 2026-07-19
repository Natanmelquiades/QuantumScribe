"""Gera exclusões explícitas para o NSIS; arquivos desconhecidos são preservados."""

from __future__ import annotations

from pathlib import Path


def _nsis_path(path: Path) -> str:
    return str(path).replace("/", "\\").replace("$", "$$").replace('"', '$\\"')


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    bundle = project_root / "dist" / "QuantumScribe"
    output = project_root / "installer" / "generated_uninstall_files.nsh"
    if not bundle.is_dir():
        raise SystemExit(f"Bundle não encontrado: {bundle}")

    files = sorted((path.relative_to(bundle) for path in bundle.rglob("*") if path.is_file()), reverse=True)
    directories = sorted(
        (path.relative_to(bundle) for path in bundle.rglob("*") if path.is_dir()),
        key=lambda path: (len(path.parts), str(path)),
        reverse=True,
    )
    lines = ["; Gerado automaticamente. Não editar."]
    lines.extend(f'Delete "$INSTDIR\\{_nsis_path(path)}"' for path in files)
    lines.extend(f'RMDir "$INSTDIR\\{_nsis_path(path)}"' for path in directories)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
