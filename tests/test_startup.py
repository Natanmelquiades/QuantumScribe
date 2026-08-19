from types import SimpleNamespace

import pytest

from localwhisper import startup
from localwhisper.config import AppConfig, load_config, save_config


@pytest.fixture
def temp_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    return tmp_path


class _FakeRunKey:
    def __init__(self, values=None):
        self.values = values if values is not None else {}
        self.closed = False

    def SetValueEx(self, name, _reserved, _kind, value):
        self.values[name] = value

    def DeleteValue(self, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]

    def QueryValueEx(self, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], "REG_SZ"

    def Close(self):
        self.closed = True


class _FakeWinreg:
    HKEY_CURRENT_USER = object()
    KEY_SET_VALUE = 1
    KEY_READ = 2
    REG_SZ = 1

    def __init__(self):
        self.key = _FakeRunKey()

    def CreateKeyEx(self, _root, _path, _reserved, _access):
        return self.key

    def OpenKey(self, _root, _path, _reserved, _access):
        if not self.key.values:
            raise FileNotFoundError("run key")
        return self.key

    def SetValueEx(self, key, name, _reserved, _kind, value):
        key.SetValueEx(name, _reserved, _kind, value)

    def DeleteValue(self, key, name):
        key.DeleteValue(name)

    def QueryValueEx(self, key, name):
        return key.QueryValueEx(name)

    def CloseKey(self, key):
        key.Close()


def test_startup_toggle_writes_and_removes_current_user_entry(monkeypatch):
    fake = _FakeWinreg()
    monkeypatch.setattr(startup, "winreg", fake)
    monkeypatch.setattr(startup, "supports_startup", lambda: True)
    monkeypatch.setattr(startup, "startup_command", lambda: '"QuantumScribe.exe"')

    startup.set_startup_enabled(True)
    assert fake.key.values[startup.RUN_VALUE_NAME] == '"QuantumScribe.exe"'
    assert startup.is_startup_enabled() is True

    startup.set_startup_enabled(False)
    assert startup.is_startup_enabled() is False


def test_startup_is_explicitly_unsupported_outside_windows(monkeypatch):
    monkeypatch.setattr(startup, "supports_startup", lambda: False)

    with pytest.raises(OSError, match="somente no Windows"):
        startup.set_startup_enabled(True)

    assert startup.is_startup_enabled() is False


def test_startup_preference_persists_in_app_config(temp_appdata):
    config = load_config()
    assert config.start_with_windows is False

    config.start_with_windows = True
    save_config(config)

    assert load_config().start_with_windows is True


def test_settings_save_failure_can_be_rolled_back():
    from unittest.mock import Mock

    from localwhisper.settings_ui import SettingsWindow

    window = object.__new__(SettingsWindow)
    window._cfg = AppConfig(start_with_windows=False)
    window.on_save_callback = Mock(side_effect=OSError("registro indisponível"))
    window._toast = Mock()

    result = window._set("start_with_windows", True)

    assert result is False
    assert window._cfg.start_with_windows is False
    window._toast.assert_called_once()


def test_app_applies_startup_change_before_persisting(monkeypatch):
    from unittest.mock import Mock

    from localwhisper.app import QuantumScribeApp

    app = object.__new__(QuantumScribeApp)
    app.config = AppConfig(start_with_windows=False)
    app.popup = SimpleNamespace(config=None)
    app.transcriber = SimpleNamespace(reload_config=Mock())
    app._register_all_hotkeys = Mock()

    startup_calls = []
    monkeypatch.setattr("localwhisper.app.set_startup_enabled", startup_calls.append)
    monkeypatch.setattr("localwhisper.app.save_config", lambda _config: None)

    app.save_and_apply_config(AppConfig(start_with_windows=True))

    assert startup_calls == [True]
    assert app.config.start_with_windows is True
    app.transcriber.reload_config.assert_called_once()


def test_app_restores_startup_entry_if_config_persistence_fails(monkeypatch):
    from localwhisper.app import QuantumScribeApp

    app = object.__new__(QuantumScribeApp)
    app.config = AppConfig(start_with_windows=False)

    startup_calls = []
    monkeypatch.setattr("localwhisper.app.set_startup_enabled", startup_calls.append)

    def fail_save(_config):
        raise OSError("disco indisponível")

    monkeypatch.setattr("localwhisper.app.save_config", fail_save)

    with pytest.raises(OSError, match="disco indisponível"):
        app.save_and_apply_config(AppConfig(start_with_windows=True))

    assert startup_calls == [True, False]
