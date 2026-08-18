# Mapa de dependências — `localwhisper`

> Gerado por `scripts/architecture_inventory.py`; o conteúdo é determinístico.

Módulos analisados: **40**.

## Grafo interno

| Módulo | Dependências internas | Fan-out | Fan-in |
| --- | --- | ---: | ---: |
| `localwhisper` | — | 0 | 3 |
| `localwhisper.app` | `audio`, `cache`, `components`, `config`, `diary`, `hardware`, `hotkey`, `model_manager`, `platform`, `post_processor`, `quantum_brain`, `rewriter`, `session_controller`, `settings_ui`, `sounds`, `speech_cleaner`, `startup`, `stream_transcriber`, `transcriber`, `tray`, `ui`, `updater`, `vocab_cache`, `windows` | 24 | 0 |
| `localwhisper.audio` | — | 0 | 2 |
| `localwhisper.audio_enhancer` | — | 0 | 1 |
| `localwhisper.cache` | `config` | 1 | 1 |
| `localwhisper.components` | `localwhisper`, `config` | 2 | 3 |
| `localwhisper.config` | — | 0 | 12 |
| `localwhisper.contracts` | — | 0 | 0 |
| `localwhisper.diary` | `config` | 1 | 3 |
| `localwhisper.download_progress` | — | 0 | 1 |
| `localwhisper.hardware` | `components` | 1 | 2 |
| `localwhisper.hotkey` | `platform` | 1 | 2 |
| `localwhisper.memory` | `diary` | 1 | 1 |
| `localwhisper.model_manager` | `config` | 1 | 2 |
| `localwhisper.platform` | `platform.linux.hotkey`, `platform.linux.ui_compat`, `platform.linux.windows_api`, `platform.windows.hotkey`, `platform.windows.ui_compat`, `platform.windows.windows_api` | 6 | 4 |
| `localwhisper.platform.linux` | — | 0 | 0 |
| `localwhisper.platform.linux.hotkey` | — | 0 | 1 |
| `localwhisper.platform.linux.ui_compat` | — | 0 | 1 |
| `localwhisper.platform.linux.windows_api` | — | 0 | 1 |
| `localwhisper.platform.windows` | — | 0 | 0 |
| `localwhisper.platform.windows.hotkey` | — | 0 | 1 |
| `localwhisper.platform.windows.ui_compat` | — | 0 | 1 |
| `localwhisper.platform.windows.windows_api` | — | 0 | 1 |
| `localwhisper.post_processor` | — | 0 | 1 |
| `localwhisper.punctuation` | — | 0 | 1 |
| `localwhisper.quantum_brain` | `config`, `rewriter` | 2 | 2 |
| `localwhisper.rewriter` | `config` | 1 | 3 |
| `localwhisper.session_controller` | — | 0 | 1 |
| `localwhisper.settings_ui` | `localwhisper`, `audio`, `config`, `diary`, `download_progress`, `hotkey`, `model_manager`, `quantum_brain`, `rewriter`, `startup`, `stream_transcriber`, `theme`, `updater` | 13 | 1 |
| `localwhisper.sounds` | — | 0 | 1 |
| `localwhisper.speech_cleaner` | — | 0 | 2 |
| `localwhisper.startup` | — | 0 | 2 |
| `localwhisper.stream_transcriber` | `audio_enhancer`, `components`, `speech_cleaner`, `vocab_cache` | 4 | 2 |
| `localwhisper.theme` | — | 0 | 1 |
| `localwhisper.transcriber` | `config`, `hardware`, `memory`, `punctuation`, `vocab_cache` | 5 | 1 |
| `localwhisper.tray` | — | 0 | 1 |
| `localwhisper.ui` | `config`, `platform` | 2 | 1 |
| `localwhisper.updater` | `localwhisper`, `config` | 2 | 2 |
| `localwhisper.vocab_cache` | `config` | 1 | 3 |
| `localwhisper.windows` | `platform` | 1 | 1 |

## Ciclos internos

- Nenhum ciclo interno detectado.

## Imports opcionais observados

- `localwhisper.audio_enhancer`: `noisereduce`, `scipy`, `scipy.signal`, `scipy.signal.butter`, `scipy.signal.filtfilt`
- `localwhisper.stream_transcriber`: `onnxruntime`
