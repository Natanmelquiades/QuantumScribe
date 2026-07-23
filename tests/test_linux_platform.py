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
