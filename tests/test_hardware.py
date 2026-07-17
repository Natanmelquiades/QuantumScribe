from localwhisper import hardware


def test_auto_prefers_cuda_when_runtime_is_available(monkeypatch):
    monkeypatch.setattr(hardware, "cuda_runtime_status", lambda: (True, "CUDA pronta"))

    selection = hardware.resolve_hardware("auto", "auto")

    assert selection.device == "cuda"
    assert selection.compute_type == "float16"
    assert selection.cuda_available is True


def test_auto_falls_back_to_cpu_before_loading_model(monkeypatch):
    monkeypatch.setattr(hardware, "cuda_runtime_status", lambda: (False, "cuBLAS ausente"))

    selection = hardware.resolve_hardware("auto", "auto")

    assert selection.device == "cpu"
    assert selection.compute_type == "int8"
    assert selection.cuda_available is False
    assert selection.detail == "cuBLAS ausente"


def test_explicit_cuda_is_a_preference_not_a_crash(monkeypatch):
    monkeypatch.setattr(hardware, "cuda_runtime_status", lambda: (False, "GPU incompatível"))

    selection = hardware.resolve_hardware("cuda", "int8")

    assert selection.device == "cpu"
    assert selection.compute_type == "int8"


def test_unsupported_cpu_float16_is_replaced_by_safe_int8():
    selection = hardware.resolve_hardware("cpu", "float16")

    assert selection.device == "cpu"
    assert selection.compute_type == "int8"


def test_cuda_setup_keeps_windows_dll_handles_alive(tmp_path, monkeypatch):
    nvidia_bin = tmp_path / "nvidia" / "cublas" / "bin"
    nvidia_bin.mkdir(parents=True)
    (nvidia_bin / "cublas64_12.dll").write_bytes(b"test")
    handle = object()

    monkeypatch.setattr(hardware.sys, "platform", "win32")
    monkeypatch.setattr(hardware.sys, "path", [str(tmp_path)])
    monkeypatch.setattr(hardware.os, "add_dll_directory", lambda path: handle)
    hardware._CUDA_DLL_HANDLES.clear()
    hardware._CUDA_DLL_DIRS.clear()

    registered = hardware.setup_cuda_dlls()

    assert str(nvidia_bin.resolve()) in registered
    assert handle in hardware._CUDA_DLL_HANDLES
