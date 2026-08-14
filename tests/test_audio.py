import sys
import time
from types import SimpleNamespace

import numpy as np

from localwhisper.audio import AudioRecorder, _prefer_wasapi_input


class _FakeWasapiSettings:
    def __init__(self, *, auto_convert: bool):
        self.auto_convert = auto_convert


def _fake_sounddevice():
    devices = [
        {"name": "Microfone (NVIDIA Broadcast)", "hostapi": 0, "max_input_channels": 2},
        {"name": "Microfone (NVIDIA Broadcast)", "hostapi": 1, "max_input_channels": 2},
    ]
    hostapis = [{"name": "Windows MME"}, {"name": "Windows WASAPI"}]
    return SimpleNamespace(
        default=SimpleNamespace(device=(0, 6)),
        WasapiSettings=_FakeWasapiSettings,
        query_devices=lambda: devices,
        query_hostapis=lambda: hostapis,
        check_input_settings=lambda **kwargs: None,
    )


def test_prefer_wasapi_selects_the_low_latency_duplicate(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "sounddevice", _fake_sounddevice())

    device, extra = _prefer_wasapi_input(0)

    assert device == 1
    assert extra.auto_convert is True


def test_audio_recorder_falls_back_when_wasapi_open_fails(monkeypatch):
    attempts = []

    class _Stream:
        def __init__(self, **kwargs):
            attempts.append(kwargs)
            self.kwargs = kwargs

        def start(self):
            if self.kwargs["device"] == 1:
                raise RuntimeError("driver recusou WASAPI")

        def close(self):
            pass

        def abort(self):
            pass

    fake_sd = _fake_sounddevice()
    fake_sd.InputStream = _Stream
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)
    monkeypatch.setattr("localwhisper.audio._prefer_wasapi_input", lambda _device: (1, object()))

    recorder = AudioRecorder()
    recorder.start(device_index=0)

    assert [attempt["device"] for attempt in attempts] == [1, 0]
    recorder.cancel()


def test_audio_recorder_discards_the_start_sound_guard_window():
    recorder = AudioRecorder()
    recorder._ignore_audio_until = time.monotonic() + 1.0

    recorder._callback(
        np.ones((128, 1), dtype=np.int16),
        128,
        None,
        SimpleNamespace(input_overflow=False),
    )

    assert recorder.get_current_duration() == 0.0
