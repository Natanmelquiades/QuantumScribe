import tkinter as tk
from unittest.mock import Mock

from localwhisper.config import AppConfig
from localwhisper.tray import TrayIcon
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

    monkeypatch.setattr("localwhisper.tray.pystray.Icon", fake_icon)
    monkeypatch.setattr("localwhisper.tray.create_icon", Mock())

    TrayIcon(Mock(), Mock(), Mock())

    captured["title"].encode("latin-1")
