import sys
import urllib.request


def test_core_import_boundary_is_offline_and_keeps_optional_modules_lazy(monkeypatch):
    def fail_network(*_args, **_kwargs):
        raise AssertionError("import do Core não pode iniciar download")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    import localwhisper.app  # noqa: F401
    import localwhisper.model_manager  # noqa: F401

    forbidden = {"torch", "torchaudio", "onnxruntime", "scipy", "noisereduce", "silero_vad"}
    assert forbidden.isdisjoint(sys.modules)
