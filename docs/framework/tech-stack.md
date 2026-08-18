# QuantumScribe — Stack canônica

Este é o documento canônico de stack carregado pelo AIOX. Toda alteração de
dependência deve manter `pyproject.toml`, os manifestos por perfil e os locks
coerentes.

## Runtime

| Camada | Escolha | Regra |
| --- | --- | --- |
| Linguagem | Python `>=3.11,<3.14` | `pyproject.toml` é a fonte de metadados. |
| Transcrição | `faster-whisper`/CTranslate2 | Carregamento sob demanda; manter `auto` de device/compute. |
| Áudio | `sounddevice` e módulos locais | Hardware é acessado por adaptador e testes usam fakes. |
| Desktop | Tkinter/ttk, Pillow, pystray | UI não decide instalação nem importa engine para descobrir estado. |
| Persistência | Arquivos locais | Configuração, diário, histórico, cache e modelos permanecem locais. |
| Plataformas | Adaptadores `localwhisper/platform/{windows,linux}` | Diferenças de SO ficam atrás de módulos de plataforma. |

## Qualidade e distribuição

- Testes: Pytest; lint/imports: Ruff; compilação: `compileall`.
- Auditoria: `pip check`, `pip-audit` e inventário determinístico do bundle.
- Empacotamento: PyInstaller, PowerShell no Windows, shell no Linux e NSIS para o
  instalador Windows.
- Perfis: `requirements-core.lock` para Core CPU, locks de build/teste separados e
  locks de componentes opcionais. O Core não instala componentes via `pip` na
  máquina final.
- Builds de release devem usar `--require-hashes`, ambiente limpo e inventário com
  limite de 250 MB para o Core.

## Princípios de evolução

1. CLI e scripts são a fonte de execução; a UI apenas observa e apresenta estado.
2. O produto continua um monólito modular local, sem banco central ou API HTTP nova.
3. Dependências opcionais são carregadas sob demanda e permanecem fora do caminho
   de inicialização do Core.
4. Toda extração estrutural nasce com contrato, teste de caracterização e rollback
   isolado.

**Fontes:** `pyproject.toml`, `docs/architecture.md`,
`docs/prd/epic-1-quantumscribe-auditoria-estabilizacao.md` e os locks versionados.
