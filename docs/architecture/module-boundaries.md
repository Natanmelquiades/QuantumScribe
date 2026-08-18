# Limites dos módulos

## Direção arquitetural

```text
Entradas (hotkey/tray/UI)
          ↓
app.py — composição/fachada
          ↓
captura → transcrição clássica/streaming → pós-processamento → entrega
    ↓              ↓                                  ↓            ↓
configuração   hardware/componentes                 diário/cache  clipboard/target
          ↓
updater e componentes opcionais (staging/hash/promoção)
```

## Fronteiras atuais e alvo

| Módulo | Responsabilidade permitida | Pode depender de | Não deve depender de |
| --- | --- | --- | --- |
| `contracts.py` | Tipos, Protocols e invariantes leves | stdlib | UI, engine, áudio físico, opcionais |
| `session_controller.py` | Identidade de job, estado ativo, callbacks stale | stdlib | Tkinter, Whisper, clipboard, UI |
| `app.py` | Composição, lifecycle da fachada e roteamento de eventos | adaptadores e serviços | nova regra opcional espalhada |
| `audio.py` | Captura, buffer e dispositivo | plataforma/config | widgets e transcrição |
| `transcriber.py` | Engine clássico e fallback | hardware/config/model manager | UI direta |
| `stream_transcriber.py` | Sessão contínua/VAD | áudio, componentes, limpeza | widgets diretos |
| `speech_cleaner.py`/`post_processor.py` | Transformações determinísticas | stdlib/config quando necessário | captura/UI |
| `rewriter.py`/`quantum_brain.py` | Capacidades opcionais | config, cache e hardware | caminho Core ocioso |
| `config.py`/`diary.py`/`cache.py` | Persistência local | filesystem seguro | UI e engine pesado |
| `components.py`/`model_manager.py`/`updater.py` | Catálogo, modelos e atualização | downloads, config, manifests | instalação silenciosa |
| `ui.py`/`settings_ui.py`/`tray.py` | Apresentação e interação | contratos, callbacks, config | decisão de engine/download |
| `platform/*` | Adaptadores por SO | APIs do SO | regras de negócio |
| specs/build/scripts | Empacotamento e evidência | requirements/locks | imports de runtime no usuário |

## Regras de migração

- `app.py` permanece fachada até que cada seam tenha caracterização e rollback.
- Um módulo novo não pode aumentar a superfície do Core nem importar uma capacidade
  opcional para descobrir se ela existe.
- Círculos novos no grafo interno bloqueiam a story; um ciclo existente só pode ser
  mantido se estiver descrito no mapa e tiver plano de remoção.
- `delivery.py` e a decomposição de `settings_ui.py` ficam para stories próprias.

**Fontes:** `docs/architecture.md#5-component-architecture`,
`docs/architecture.md#8-source-tree-integration` e
`docs/prd/epic-1-quantumscribe-auditoria-estabilizacao.md#qs-audit-003`.
