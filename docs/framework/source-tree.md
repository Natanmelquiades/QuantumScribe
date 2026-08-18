# QuantumScribe — Árvore de origem

```text
QuantumScribe/
├── localwhisper/
│   ├── app.py                    # composição e fachada do desktop
│   ├── contracts.py              # contratos leves, sem dependências pesadas
│   ├── session_controller.py     # identidade/job e callbacks stale
│   ├── audio.py                  # captura e buffers
│   ├── transcriber.py             # transcrição clássica
│   ├── stream_transcriber.py      # streaming/VAD
│   ├── speech_cleaner.py          # limpeza determinística
│   ├── post_processor.py          # dicionário/pós-processamento
│   ├── rewriter.py                # reescrita opcional
│   ├── config.py                  # configuração e persistência atômica
│   ├── components.py              # catálogo/ativação de opcionais
│   ├── model_manager.py           # modelos e hardware
│   ├── updater.py                 # atualização segura
│   ├── ui.py/settings_ui.py/tray.py # apresentação e controles
│   └── platform/{windows,linux}/  # adaptadores por sistema operacional
├── tests/                         # unitários, integração controlada e packaging
├── scripts/                       # inventário, build e validações
├── docs/architecture.md           # arquitetura brownfield canônica
├── docs/architecture/             # mapas e decisões detalhadas
├── docs/framework/                # documentos carregados pelo AIOX
├── docs/guides/                   # procedimentos operacionais
├── QuantumScribe*.spec            # manifestos PyInstaller
├── requirements-*.txt/lock        # perfis e locks por finalidade
└── build.ps1/build_linux.sh       # reprodução de build
```

## Regras de localização

- Contratos e seams pequenos ficam em `localwhisper/` até haver evidência para um
  pacote coeso com mais de dois arquivos.
- Testes de contrato/seam ficam em `tests/test_<module>.py`; testes de plataforma,
  build e updater permanecem nos módulos já existentes.
- Documentação de decisão fica em `docs/architecture/project-decisions/`; guias
  operacionais ficam em `docs/guides/`.
- Artefatos de build não são fonte de código e devem permanecer fora da árvore
  versionada ou em diretórios de saída explicitamente ignorados.
