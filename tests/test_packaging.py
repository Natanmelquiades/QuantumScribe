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


def test_linux_packaging_sources_exist():
    expected = (
        ROOT / "QuantumScribe-Linux.spec",
        ROOT / "requirements-linux.txt",
        ROOT / "install_linux.sh",
        ROOT / "install_linux_shortcut.sh",
        ROOT / "run_linux.sh",
        ROOT / "build_linux.sh",
    )

    assert all(path.is_file() for path in expected)
    build_script = (ROOT / "build_linux.sh").read_text(encoding="utf-8")
    spec = (ROOT / "QuantumScribe-Linux.spec").read_text(encoding="utf-8")
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert 'pip install -r requirements-linux.txt' in build_script
    assert build_script.index('pip install -r requirements-linux.txt') > build_script.index('fi\n')
    assert "'PIL._tkinter_finder'" in spec
    assert "'gi.repository.AyatanaAppIndicator3'" in spec
    assert "install_linux_shortcut.sh" in release


def test_core_explicitly_excludes_heavy_optional_runtimes():
    spec = (ROOT / "QuantumScribe.spec").read_text(encoding="utf-8")

    assert "collect_dynamic_libs" not in spec
    assert "'torch'" in spec
    assert "'silero_vad'" in spec
    assert "'nvidia'" in spec
    assert "'onnxruntime'" in spec


def test_release_build_separates_core_and_optional_components():
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert r".\build.ps1 -Installer" in release
    assert "build_optional_components.ps1" in release
    assert "QuantumScribe-CUDA-" in release
    assert "QuantumScribe-SileroVAD-" in release
    assert "build-linux:" in release
    assert "QuantumScribe-Core-$version-Linux-x64.tar.gz" in release
    assert "Compress-Archive" not in release
    assert '"QuantumScribe-Core-$version-Windows-x64.zip",' not in release
    assert 'gh release download $tag --pattern "SHA256SUMS-Linux.txt"' in release
    assert 'gh release delete-asset $tag "SHA256SUMS-Linux.txt" --yes' in release
    assert "gh release edit $tag --draft=false --latest" in release


def test_backup_feature_is_not_shipped():
    assert not (ROOT / "localwhisper" / "backup.py").exists()
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")
    assert "Backup e Restauração" not in settings


def test_installer_has_fixed_safe_location_and_no_recursive_root_delete():
    installer = (ROOT / "installer" / "QuantumScribe.nsi").read_text(encoding="utf-8")

    assert "MUI_PAGE_DIRECTORY" not in installer
    assert 'InstallDir "$LOCALAPPDATA\\Programs\\${APP_NAME}"' in installer
    assert 'RMDir /r "$INSTDIR"' not in installer
    assert ".quantumscribe-install" in installer


def test_settings_save_does_not_depend_on_lazy_volume_widget():
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")

    assert "self.sound_volume_var = tk.DoubleVar" in settings
    assert "sound_volume=float(self.sound_volume_var.get())" in settings
    assert "sound_volume=float(self.volume_slider.get())" not in settings


def test_about_page_exposes_safe_application_updater():
    settings = (ROOT / "localwhisper" / "settings_ui.py").read_text(encoding="utf-8")
    updater = (ROOT / "localwhisper" / "updater.py").read_text(encoding="utf-8")

    assert '"Verificar atualização"' in settings
    assert "SHA256SUMS.txt" in updater
    assert "draft" in updater and "prerelease" in updater
    assert "Get-Process" in updater and "Start-Sleep" in updater
    assert "QuantumScribe-Setup-" in updater


def test_nsis_build_uses_utf8_input():
    build_script = (ROOT / "build.ps1").read_text(encoding="utf-8")

    assert '"/INPUTCHARSET" "UTF8"' in build_script
