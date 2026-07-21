from localwhisper.ui import Popup


def test_stale_hud_callbacks_do_not_hide_current_generation():
    popup = object.__new__(Popup)
    popup._visual_generation = 9

    Popup.hide(popup, generation=8)

    assert popup._visual_generation == 9


def test_stale_hud_animation_returns_without_touching_current_state():
    popup = object.__new__(Popup)
    popup._visual_generation = 4
    popup.animating = True

    Popup._animate(popup, generation=3)

    assert popup._visual_generation == 4
