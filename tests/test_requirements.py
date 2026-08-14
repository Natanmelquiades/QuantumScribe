from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _included_files(path: Path) -> list[Path]:
    includes: list[Path] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("-r "):
            includes.append(path.parent / line.removeprefix("-r ").strip())
    return includes


def test_requirement_manifest_includes_exist():
    """Cada manifesto de instalação deve resolver seus includes localmente."""
    manifests = [ROOT / "requirements.txt", *sorted(ROOT.glob("requirements-*.txt"))]
    assert manifests

    for manifest in manifests:
        for included in _included_files(manifest):
            assert included.is_file(), f"{manifest.name} inclui arquivo ausente: {included.name}"


def test_runtime_manifests_share_the_common_dependency_set():
    for name in (
        "requirements-cpu.txt",
        "requirements-cuda.txt",
        "requirements-linux.txt",
        "requirements-windows.txt",
    ):
        assert ROOT.joinpath(name).read_text(encoding="utf-8").splitlines()[0] == "-r requirements-common.txt"
