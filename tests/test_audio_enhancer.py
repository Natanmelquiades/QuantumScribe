import sys

import numpy as np
import pytest

from localwhisper.audio_enhancer import (
    apply_highpass_filter,
    apply_noise_reduction,
    apply_rms_normalization,
)


def test_audio_enhancer_preserves_empty_and_short_buffers():
    empty = np.array([], dtype=np.float32)
    short = np.ones(8, dtype=np.float32)

    assert apply_highpass_filter(short) is short
    assert apply_noise_reduction(short) is short
    assert apply_rms_normalization(empty) is empty


def test_audio_enhancer_handles_a_normal_buffer():
    audio = np.zeros(2048, dtype=np.float32)
    audio[256:768] = 0.1

    filtered = apply_highpass_filter(audio)
    reduced = apply_noise_reduction(audio)
    normalized = apply_rms_normalization(audio)

    assert filtered.shape == audio.shape
    assert reduced.shape == audio.shape
    assert normalized.shape == audio.shape
    assert np.isfinite(normalized).all()


@pytest.mark.parametrize("size", [0, 1, 15, 16])
def test_highpass_filter_short_boundaries_are_finite(size):
    audio = np.linspace(-0.1, 0.1, size, dtype=np.float32)

    filtered = apply_highpass_filter(audio)

    assert filtered.shape == audio.shape
    assert np.isfinite(filtered).all()
    if size <= 15:
        assert filtered is audio


@pytest.mark.parametrize("size", [0, 1, 511, 512])
def test_noise_reduction_short_boundaries_are_finite(size):
    audio = np.linspace(-0.1, 0.1, size, dtype=np.float32)

    reduced = apply_noise_reduction(audio)

    assert reduced.shape == audio.shape
    assert np.isfinite(reduced).all()
    if size < 512:
        assert reduced is audio


@pytest.mark.parametrize(
    ("module_name", "function"),
    [("scipy", apply_highpass_filter), ("noisereduce", apply_noise_reduction)],
)
def test_optional_audio_dependency_failure_returns_original(monkeypatch, module_name, function):
    monkeypatch.setitem(sys.modules, module_name, None)
    audio = np.ones(2048, dtype=np.float32)

    result = function(audio)

    assert result is audio
    assert np.isfinite(result).all()
