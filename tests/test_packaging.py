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


def test_universal_package_collects_cuda_runtime():
    spec = (ROOT / "QuantumScribe.spec").read_text(encoding="utf-8")

    assert "collect_dynamic_libs" in spec
    assert "nvidia.cublas" in spec
    assert "nvidia.cudnn" in spec
    assert "CUDA_RUNTIME_DLLS" in spec
    assert "nvidia.cuda_nvrtc" not in spec


def test_release_build_is_adaptive_cpu_cuda():
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert r".\build.ps1 -Cuda -Installer" in release


def test_settings_save_does_not_depend_on_lazy_volume_widget():
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")

    assert "self.sound_volume_var = tk.DoubleVar" in settings
    assert "sound_volume=float(self.sound_volume_var.get())" in settings
    assert "sound_volume=float(self.volume_slider.get())" not in settings


def test_nsis_build_uses_utf8_input():
    build_script = (ROOT / "build.ps1").read_text(encoding="utf-8")

    assert '"/INPUTCHARSET" "UTF8"' in build_script
