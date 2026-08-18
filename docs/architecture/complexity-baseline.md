# Baseline de complexidade e plano de decomposição

**Medição:** `radon 6.0.1`, `radon cc localwhisper -s -a`, 2026-08-18.  
**Resultado geral:** 503 blocos analisados; média **A (3,94)**.

## Pontos E/F conhecidos

| Local | Complexidade | Estado após Story 1.3 | Próximo passo |
| --- | ---: | --- | --- |
| `localwhisper/app.py::_transcribe_and_deliver` | F (48) | Ainda coordena transcrição, pós-processamento e entrega; identidade/stale-job foi isolada. | Extrair `delivery.py` somente com story própria e caracterização. |
| `localwhisper/ui.py::Popup._animate_atom` | E (40) | Fora do escopo; permanece em apresentação. | Decompor animação apenas com revisão de UI e teste visual/controlado. |
| `localwhisper/rewriter.py::rewrite_text` | E (35) | Fora do escopo; capacidade opcional preservada. | Separar etapas do rewriter sem puxar dependência para o Core. |
| `localwhisper/transcriber.py::LocalTranscriber.transcribe` | D (23) | Fora do primeiro seam. | Caracterizar fallback e cancelamento antes de decompor. |
| `localwhisper/stream_transcriber.py::StreamTranscriber._do_transcribe` | C (20) | Fora do primeiro seam. | Mapear streaming/VAD e stale session em story própria. |

## Decisão da Story 1.3

O `session_controller.py` removeu a coordenação de identidade monotônica, invalidação
e callbacks stale de `app.py`, mas não promete reduzir a complexidade ciclomática do
pipeline inteiro. Isso é intencional: mover pós-processamento e entrega na mesma
mudança aumentaria risco e violaria a migração por seam.

## Plano aprovado

1. **Entrega:** @architect define o contrato; @dev cria `delivery.py` em story
   própria; @qa mantém caracterização de clipboard, diário e resultado stale.
2. **Transcrição clássica:** @architect mapeia fallback/cancelamento; @dev extrai
   somente após o seam de entrega passar nos gates.
3. **Streaming/VAD:** @architect separa lifecycle de captura contínua e engine; a
   story deve cobrir cancelamento, sessão substituída e ausência de ONNX.
4. **UI:** a animação permanece isolada da lógica de domínio; qualquer decomposição
   exige validação visual/controlada e não pode importar engine pesado.

## Critério para avançar

Cada próxima story deve registrar complexidade antes/depois, manter a baseline de
testes, não criar E/F equivalente e deixar o módulo anterior como fachada até o
rollback ser demonstrado. Sem caracterização, o plano permanece aprovado mas a
extração fica bloqueada.
