# ADR 0003 — Extrair lifecycle por seam, sem reescrita

- **Status:** Aceita
- **Data:** 2026-08-18
- **Contexto:** `app.py` concentra gravação, transcrição, streaming, cancelamento,
  entrega e atualização de UI. O risco principal é um resultado stale alterar uma
  sessão mais nova ou uma extração mudar comportamento sem evidência.
- **Decisão:** A primeira extração é `localwhisper/session_controller.py`, limitada
  a identidade monotônica de job, invalidação, guarda de sessão ativa e callbacks
  finais. `app.py` continua fachada compatível; delivery e `settings_ui.py` ficam
  para stories futuras.
- **Consequências:** O seam pode ser testado sem Tkinter, Whisper ou hardware e a
  coordenação de stale result fica isolada. O monólito ainda mantém algum código de
  orquestração até que novas stories tenham caracterização própria.
- **Critério de saída:** nenhuma mudança observável nos fluxos existentes, suíte
  completa aprovada, sem ciclo novo e sem aumento equivalente de complexidade.

**Fontes:** `docs/architecture.md#5-component-architecture`,
`docs/architecture/module-boundaries.md` e Story 1.3.
