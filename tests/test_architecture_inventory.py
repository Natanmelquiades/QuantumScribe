from pathlib import Path

from scripts.architecture_inventory import build_inventory, render_markdown

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_import_inventory_is_deterministic_and_covers_package():
    package_root = PROJECT_ROOT / "localwhisper"
    first = build_inventory(package_root)
    second = build_inventory(package_root)

    assert first == second
    assert len(first.modules) >= 20
    assert "localwhisper.app" in {record.name for record in first.modules}
    assert render_markdown(first) == render_markdown(second)


def test_contract_module_does_not_depend_on_ui_or_heavy_optional_modules():
    inventory = build_inventory(PROJECT_ROOT / "localwhisper")
    contracts = next(record for record in inventory.modules if record.name == "localwhisper.contracts")

    assert not contracts.internal_imports
    assert not contracts.optional_imports


def test_cycle_report_is_explicit_and_stable():
    inventory = build_inventory(PROJECT_ROOT / "localwhisper")

    assert inventory.cycles == tuple(sorted(inventory.cycles))
    assert all(len(cycle) >= 2 for cycle in inventory.cycles)
