# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

datas = [('localwhisper/assets/icon.png', 'localwhisper/assets')]
binaries = []
hiddenimports = ['silero_vad', 'torch', 'scipy', 'noisereduce', 'huggingface_hub']
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ctranslate2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('av')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# Runtime mínimo comprovado com faster-whisper/CTranslate2. Os pacotes NVIDIA
# também distribuem engines de treino/JIT que não participam da inferência e
# fariam o bundle ultrapassar o limite de 2 GB do compilador NSIS.
CUDA_RUNTIME_DLLS = {
    'cublas64_12.dll',
    'cublasLt64_12.dll',
    'cudnn64_9.dll',
    'cudnn_ops64_9.dll',
    'cudnn_cnn64_9.dll',
    'cudnn_graph64_9.dll',
    'cudnn_heuristic64_9.dll',
    'cudnn_engines_runtime_compiled64_9.dll',
    'cudnn_engines_tensor_ir64_9.dll',
    'cudnn_ext64_9.dll',
}
for package in ('nvidia.cublas', 'nvidia.cudnn'):
    binaries += [
        item for item in collect_dynamic_libs(package)
        if os.path.basename(item[0]) in CUDA_RUNTIME_DLLS
    ]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuantumScribe',
    icon='localwhisper/assets/icon.png',
    version='build/QuantumScribe.version.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuantumScribe',
)
