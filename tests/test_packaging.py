import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_versions_stay_in_sync():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    init_text = (ROOT / "localwhisper" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)

    assert match is not None
    assert metadata["project"]["version"] == match.group(1)


def test_windows_packaging_sources_exist():
    expected = (
        ROOT / "localwhisper" / "assets" / "icon.png",
        ROOT / "QuantumScribe.spec",
        ROOT / "installer" / "QuantumScribe.nsi",
    )

    assert all(path.is_file() for path in expected)


def test_nsis_build_uses_utf8_input():
    build_script = (ROOT / "build.ps1").read_text(encoding="utf-8")

    assert '"/INPUTCHARSET" "UTF8"' in build_script
