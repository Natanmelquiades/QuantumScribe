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


def test_runtime_manifests_use_the_core_profile():
    for name in (
        "requirements-cpu.txt",
        "requirements-cuda.txt",
        "requirements-linux.txt",
    ):
        content = ROOT.joinpath(name).read_text(encoding="utf-8")
        assert "-r requirements-core.in" in content
        assert "-r requirements-common.txt" not in content


def test_core_manifest_does_not_declare_optional_runtimes():
    content = (ROOT / "requirements-core.in").read_text(encoding="utf-8").lower()

    for package in ("nvidia", "torch", "torchaudio", "silero", "onnxruntime", "scipy", "noisereduce"):
        assert package not in content


def test_generated_locks_are_hashed_and_have_required_profiles():
    for name in (
        "requirements-core.lock",
        "requirements-build.lock",
        "requirements-test.lock",
        "requirements-linux.lock",
        "requirements-build-linux.lock",
    ):
        path = ROOT / name
        assert path.is_file(), f"lock ausente: {name}"
        content = path.read_text(encoding="utf-8")
        assert "--hash=sha256:" in content, f"lock sem hashes: {name}"

    assert "-r requirements-core.lock" in (ROOT / "requirements-cpu.lock").read_text(encoding="utf-8")
