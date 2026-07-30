import sys

import pytest

if not sys.platform.startswith("linux"):
    pytest.skip("Testes específicos da integração Linux", allow_module_level=True)

from localwhisper.platform.linux import windows_api
from localwhisper.platform.linux.hotkey import GlobalHotkey, _parse_hotkey


def test_linux_hotkey_requires_exactly_one_main_key():
    for invalid in ("Ctrl", "Ctrl+Alt", "Ctrl+A+B", "Ctrl+Ctrl+Space"):
        try:
            _parse_hotkey(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Atalho inválido aceito: {invalid}")


def test_linux_hotkey_releases_only_after_the_whole_chord():
    events: list[str] = []
    hotkey = GlobalHotkey(
        "Ctrl+Space",
        on_press=lambda: events.append("press"),
        on_release=lambda: events.append("release"),
    )

    hotkey._press_token("ctrl")
    hotkey._press_token("space")
    assert events == ["press"]

    hotkey._release_token("space")
    assert events == ["press"]

    hotkey._release_token("ctrl")
    assert events == ["press", "release"]


def test_linux_hotkey_does_not_repeat_while_chord_is_held():
    events: list[str] = []
    hotkey = GlobalHotkey("Ctrl+Space", on_press=lambda: events.append("press"))

    hotkey._press_token("ctrl")
    hotkey._press_token("space")
    hotkey._press_token("space")

    assert events == ["press"]


def test_linux_autopaste_restores_captured_window_and_uses_valid_xdotool_option(monkeypatch):
    calls: list[list[str]] = []
    clipboard: list[str] = []

    class Result:
        returncode = 0

    monkeypatch.setattr(windows_api, "set_clipboard_text", clipboard.append)
    monkeypatch.setattr(windows_api.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        windows_api.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name == "xdotool" else None,
    )
    monkeypatch.setattr(
        windows_api.subprocess,
        "run",
        lambda command, **_kwargs: calls.append(command) or Result(),
    )

    target = windows_api.WindowTarget(window=4242)

    assert windows_api.type_into_window(target, "texto transcrito") is True
    assert clipboard == ["texto transcrito"]
    assert calls == [
        ["xdotool", "windowactivate", "--sync", "4242"],
        ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
    ]


def test_linux_autopaste_reports_failure_when_target_cannot_be_reactivated(monkeypatch):
    class Result:
        returncode = 1

    monkeypatch.setattr(windows_api, "set_clipboard_text", lambda _text: None)
    monkeypatch.setattr(windows_api.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(windows_api.shutil, "which", lambda name: name == "xdotool")
    monkeypatch.setattr(windows_api.subprocess, "run", lambda *_args, **_kwargs: Result())

    assert windows_api.type_into_window(windows_api.WindowTarget(window=99), "texto") is False
