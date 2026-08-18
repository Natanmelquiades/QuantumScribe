# ADR 0002 — Fronteira entre Core e componentes opcionais

- **Status:** Aceita
- **Data:** 2026-08-18
- **Contexto:** O bundle inicial carregava dependências e artefatos de capacidades
  opcionais. A Story 1.2 criou perfis, locks, inventário e componentes fora do Core.
- **Decisão:** O Core CPU deve inicializar offline sem CUDA, Torch, ONNX, SciPy,
  modelos ou componentes opcionais embutidos. Capacidades opcionais ficam atrás de
  manifestos, staging, hash, tamanho e ação explícita do usuário.
- **Consequências:** O caminho de inicialização permanece leve e reproduzível; os
  módulos de domínio não podem importar UI ou componentes apenas para consultar
  disponibilidade. Componentes possuem ciclo de instalação/ativação próprio.
- **Rollback:** Preservar artefato anterior conhecido como bom e reativar um
  componente somente em release controlado.

**Fontes:** `docs/architecture.md#3-tech-stack-alignment`,
`docs/guides/release-procedure.md` e Story 1.2.
