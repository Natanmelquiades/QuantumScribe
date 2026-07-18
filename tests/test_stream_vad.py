import numpy as np

from localwhisper.stream_transcriber import SAMPLE_RATE, VAD_FRAME_SAMPLES, _SileroVAD


class _FakeSession:
    def __init__(self, probabilities):
        self.probabilities = iter(probabilities)
        self.shapes = []

    def run(self, _outputs, inputs):
        self.shapes.append(inputs["input"].shape)
        probability = np.array([[next(self.probabilities)]], dtype=np.float32)
        return probability, inputs["state"]


def _vad_with_fake_model(probabilities, min_silence_ms=64):
    vad = _SileroVAD.__new__(_SileroVAD)
    vad._session = _FakeSession(probabilities)
    vad._threshold = 0.5
    vad._min_silence_samples = SAMPLE_RATE * min_silence_ms / 1000
    vad._speech_pad_samples = SAMPLE_RATE * 80 / 1000
    vad.reset()
    return vad


def test_silero_onnx_adapter_preserves_start_and_end_semantics():
    vad = _vad_with_fake_model([0.9, 0.1, 0.1, 0.1])
    frame = np.zeros(VAD_FRAME_SAMPLES, dtype=np.int16)

    start = vad.process_frame(frame)
    assert start == {"start": 0.0}
    assert vad.process_frame(frame) is None
    assert vad.process_frame(frame) is None
    end = vad.process_frame(frame)

    assert end is not None and "end" in end
    assert all(shape == (1, 576) for shape in vad._session.shapes)


def test_silero_rejects_wrong_frame_size():
    vad = _vad_with_fake_model([0.9])

    try:
        vad.process_frame(np.zeros(100, dtype=np.int16))
    except ValueError as error:
        assert "512" in str(error)
    else:
        raise AssertionError("frame inválido deveria ser rejeitado")
