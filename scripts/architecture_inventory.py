"""Inventário determinístico de imports internos do QuantumScribe.

O script usa apenas a biblioteca padrão para manter a verificação disponível em
ambientes de build e revisão. Ele não importa o aplicativo: lê a árvore Python
com AST, resolve somente imports dentro do pacote informado e pode renderizar um
mapa Markdown estável para revisão arquitetural.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

OPTIONAL_ROOTS = frozenset(
    {
        "matplotlib",
        "noisereduce",
        "onnxruntime",
        "scipy",
        "silero_vad",
        "torch",
        "torchaudio",
    }
)


@dataclass(frozen=True)
class ModuleRecord:
    """Imports internos e opcionais observados em um módulo."""

    name: str
    internal_imports: tuple[str, ...]
    optional_imports: tuple[str, ...]


@dataclass(frozen=True)
class ImportInventory:
    """Resultado completo e ordenado do inventário."""

    package: str
    modules: tuple[ModuleRecord, ...]
    cycles: tuple[tuple[str, ...], ...]

    @property
    def module_names(self) -> frozenset[str]:
        return frozenset(record.name for record in self.modules)


def _module_name(package: str, package_root: Path, source: Path) -> str:
    relative = source.relative_to(package_root).with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join((package, *parts)) if parts else package


def _resolve_relative(module: str, level: int, imported: str, is_package: bool) -> str:
    parts = module.split(".")
    containing_package = parts if is_package else parts[:-1]
    # level=1 means the containing package; level=2 moves to its parent.
    base = containing_package[: max(1, len(containing_package) - level + 1)]
    return ".".join((*base, imported)) if imported else ".".join(base)


def _import_targets(module: str, node: ast.AST, is_package: bool) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        imported = node.module or ""
        if node.level:
            base = _resolve_relative(module, node.level, imported, is_package)
        else:
            base = imported
        candidates = [base]
        candidates.extend(f"{base}.{alias.name}" for alias in node.names if base)
        return tuple(candidates)
    return ()


def _root_name(import_name: str) -> str:
    return import_name.split(".", 1)[0]


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    rotations = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
    return min(rotations)


def _find_cycles(graph: dict[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    cycles: set[tuple[str, ...]] = set()
    visited: set[str] = set()
    active: list[str] = []
    active_index: dict[str, int] = {}

    def visit(module: str) -> None:
        visited.add(module)
        active_index[module] = len(active)
        active.append(module)
        for dependency in graph[module]:
            if dependency in active_index:
                cycle = tuple(active[active_index[dependency] :])
                cycles.add(_canonical_cycle(cycle))
            elif dependency not in visited:
                visit(dependency)
        active.pop()
        active_index.pop(module, None)

    for module in sorted(graph):
        if module not in visited:
            visit(module)
    return tuple(sorted(cycles))


def build_inventory(package_root: Path, package: str = "localwhisper") -> ImportInventory:
    """Lê uma árvore de pacote e retorna o grafo sem importar código do produto."""

    package_root = package_root.resolve()
    sources = sorted(package_root.rglob("*.py"))
    modules = {
        _module_name(package, package_root, source): source
        for source in sources
    }
    module_names = frozenset(modules)
    records: list[ModuleRecord] = []
    graph: dict[str, tuple[str, ...]] = {}

    for module, source in sorted(modules.items()):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        is_package = source.name == "__init__.py"
        targets = [
            target
            for node in ast.walk(tree)
            for target in _import_targets(module, node, is_package)
        ]
        internal = sorted({target for target in targets if target in module_names and target != module})
        optional = sorted({target for target in targets if _root_name(target) in OPTIONAL_ROOTS})
        records.append(ModuleRecord(module, tuple(internal), tuple(optional)))
        graph[module] = tuple(internal)

    return ImportInventory(package, tuple(records), _find_cycles(graph))


def render_markdown(inventory: ImportInventory) -> str:
    """Renderiza um relatório estável, sem timestamps ou caminhos absolutos."""

    fan_in = {record.name: 0 for record in inventory.modules}
    for record in inventory.modules:
        for dependency in record.internal_imports:
            fan_in[dependency] += 1

    lines = [
        f"# Mapa de dependências — `{inventory.package}`",
        "",
        "> Gerado por `scripts/architecture_inventory.py`; o conteúdo é determinístico.",
        "",
        f"Módulos analisados: **{len(inventory.modules)}**.",
        "",
        "## Grafo interno",
        "",
        "| Módulo | Dependências internas | Fan-out | Fan-in |",
        "| --- | --- | ---: | ---: |",
    ]
    for record in inventory.modules:
        dependencies = ", ".join(
            f"`{item.removeprefix(inventory.package + '.')}`" for item in record.internal_imports
        ) or "—"
        lines.append(
            f"| `{record.name}` | {dependencies} | {len(record.internal_imports)} | {fan_in[record.name]} |"
        )

    lines.extend(["", "## Ciclos internos", ""])
    if inventory.cycles:
        lines.extend(f"- `{' -> '.join((*cycle, cycle[0]))}`" for cycle in inventory.cycles)
    else:
        lines.append("- Nenhum ciclo interno detectado.")

    optional_records = [record for record in inventory.modules if record.optional_imports]
    lines.extend(["", "## Imports opcionais observados", ""])
    if optional_records:
        lines.extend(
            f"- `{record.name}`: {', '.join(f'`{item}`' for item in record.optional_imports)}"
            for record in optional_records
        )
    else:
        lines.append("- Nenhum import opcional conhecido detectado.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path("localwhisper"))
    parser.add_argument("--package", default="localwhisper")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    inventory = build_inventory(args.package_root, args.package)
    rendered = render_markdown(inventory)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
