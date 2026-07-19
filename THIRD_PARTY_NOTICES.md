# Avisos de software de terceiros

O QuantumScribe é distribuído sob a licença MIT. Ele depende de projetos de terceiros
com licenças próprias. Esta lista é informativa; os arquivos de licença fornecidos
por cada pacote continuam sendo a fonte oficial.

| Projeto | Uso | Licença declarada pelo pacote |
|---|---|---|
| faster-whisper | transcrição | MIT |
| CTranslate2 | inferência otimizada | MIT |
| NumPy | processamento numérico | BSD e licenças componentes |
| sounddevice | captura de áudio | MIT |
| pystray | ícone da bandeja | LGPLv3 |
| Pillow | imagens e ícones | HPND/MIT-CMU |
| PyInstaller | empacotamento | GPLv2+ com exceção para distribuição |
| NSIS | geração do instalador Windows | zlib/libpng e licenças de módulos |
| comtypes | integração Windows | MIT |
| uiautomation | automação Windows | Apache-2.0 |
| tokenizers | tokenização | Apache-2.0 |
| noisereduce | redução de ruído | MIT |
| SciPy | filtros de áudio | BSD-3-Clause |
| Silero VAD | detecção de fala | MIT |
| ONNX Runtime | inferência leve do Silero VAD | MIT |
| PyYAML | leitura YAML | MIT |
| NVIDIA cuBLAS/cuDNN | aceleração CUDA opcional | termos proprietários NVIDIA |

Os modelos Whisper e Mini-LLM baixados do Hugging Face não fazem parte deste
repositório. O componente opcional Silero contém somente o modelo ONNX oficial sob
MIT. Antes de redistribuir outros pesos, consulte a licença da página específica.
