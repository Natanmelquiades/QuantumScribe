import os
import tkinter as tk
from pathlib import Path
from unittest.mock import Mock

from PIL import Image

from localwhisper.config import AppConfig
from localwhisper.tray import TrayIcon, _force_png_suffix_for_appindicator, create_icon
from localwhisper.ui import Popup


def test_popup_tolerates_linux_tk_without_transparent_color(monkeypatch):
    window = Mock()

    def attributes(name, *_args):
        if name == "-transparentcolor":
            raise tk.TclError("unsupported")

    window.attributes.side_effect = attributes
    monkeypatch.setattr("localwhisper.ui.tk.Toplevel", lambda _root: window)
    monkeypatch.setattr("localwhisper.ui.tk.Canvas", lambda *_args, **_kwargs: Mock())
    monkeypatch.setattr(Popup, "_apply_noactivate", lambda _self: None)
    monkeypatch.setattr(Popup, "_render_pill", lambda _self, *_args: None)

    Popup(Mock(), AppConfig())

    window.attributes.assert_any_call("-alpha", 0.88)


def test_tray_title_is_x11_compatible(monkeypatch):
    captured: dict[str, str] = {}

    def fake_icon(_name, _image, title, **_kwargs):
        captured["title"] = title
        return Mock()

    fake_icon.HAS_MENU = True
    monkeypatch.setattr("localwhisper.tray.pystray.Icon", fake_icon)
    monkeypatch.setattr("localwhisper.tray.create_icon", Mock())

    TrayIcon(Mock(), Mock(), Mock())

    captured["title"].encode("latin-1")


def test_tray_default_action_opens_settings_instead_of_recording(monkeypatch):
    captured: dict[str, object] = {}

    def fake_icon(_name, _image, _title, **kwargs):
        captured["menu"] = kwargs["menu"]
        return Mock()

    fake_icon.HAS_MENU = False
    monkeypatch.setattr("localwhisper.tray.pystray.Icon", fake_icon)
    monkeypatch.setattr("localwhisper.tray.create_icon", Mock())

    TrayIcon(Mock(), Mock(), Mock())

    items = captured["menu"].items
    assert items[0].text == "Iniciar/parar ditado"
    assert items[0].default is False
    assert items[1].text == "Abrir configurações"
    assert items[1].default is True


def test_linux_tray_icon_has_transparent_antialiased_corners(monkeypatch):
    monkeypatch.setattr("localwhisper.tray.sys.platform", "linux")
    icon = create_icon()
    alpha = icon.getchannel("A")
    minimum, maximum = alpha.getextrema()

    assert icon.mode == "RGBA"
    assert icon.getpixel((0, 0))[3] == 0
    assert minimum == 0
    assert 200 <= maximum < 255
    assert any(0 < value < 255 for value in alpha.get_flattened_data())


def test_appindicator_uses_png_suffix_for_transparency(tmp_path, monkeypatch):
    class FakeAppIndicator:
        __module__ = "pystray._appindicator"

        def __init__(self):
            self.icon = Image.new("RGBA", (8, 8), (191, 90, 242, 128))
            self._icon_path = None
            self._icon_valid = False

    created = tmp_path / "quantumscribe-tray-test.png"

    def fake_mkstemp(**_kwargs):
        descriptor = os.open(created, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        return descriptor, str(created)

    monkeypatch.setattr("localwhisper.tray.tempfile.mkstemp", fake_mkstemp)
    indicator = FakeAppIndicator()

    assert _force_png_suffix_for_appindicator(indicator) is True
    indicator._update_fs_icon()

    assert Path(indicator._icon_path).suffix == ".png"
    with Image.open(indicator._icon_path) as written:
        assert written.mode == "RGBA"
        assert written.getpixel((0, 0))[3] == 128
