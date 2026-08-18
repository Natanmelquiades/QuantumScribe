# ADR 0001 — Manter monólito modular local

- **Status:** Aceita
- **Data:** 2026-08-18
- **Contexto:** O QuantumScribe é um desktop local/offline com um orquestrador
  amplo, adaptadores de plataforma, UI, pipeline de transcrição e persistência em
  arquivos. Microserviços, banco remoto ou API HTTP aumentariam a superfície e não
  resolvem o problema identificado.
- **Decisão:** Evoluir como monólito modular local, com contratos pequenos, direção
  de dependências explícita e extração incremental por seam.
- **Consequências:** Builds e testes continuam simples; `app.py` pode permanecer
  fachada durante a migração; cada módulo deve ter responsabilidade observável e
  rollback isolado. O custo é manter disciplina de imports e documentação.
- **Rejeitado:** Reescrita ampla, microserviços e troca do framework visual.

**Fontes:** `docs/architecture.md#1-introduction` e
`docs/prd/epic-1-quantumscribe-auditoria-estabilizacao.md#qs-audit-003`.
