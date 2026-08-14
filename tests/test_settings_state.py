from types import SimpleNamespace
from unittest.mock import Mock

from localwhisper.settings_ui import SettingsWindow, hotkey_conflict


def test_uninstalled_model_is_not_made_active(monkeypatch):
    window = object.__new__(SettingsWindow)
    window._cfg = SimpleNamespace(model="medium")
    window._toast = Mock()
    window._set = Mock()
    window._rebuild_page = Mock()
    monkeypatch.setattr("localwhisper.settings_ui.is_model_downloaded", lambda _model: False)

    window._select_model("large-v3")

    assert window._cfg.model == "medium"
    window._set.assert_not_called()
    window._rebuild_page.assert_not_called()
    assert "Baixe o modelo" in window._toast.call_args.args[0]


def test_hotkey_conflict_ignores_order_and_known_aliases():
    config = SimpleNamespace(
        hotkey="Ctrl+Space",
        hotkey_translate="Ctrl+Alt+Space",
        hotkey_auto_send="Ctrl+Shift+Space",
        hotkey_quantum_brain="Ctrl+Shift+D",
    )

    assert hotkey_conflict(config, "hotkey", "Shift+Control+Space") == "Ditado + Enviar"
