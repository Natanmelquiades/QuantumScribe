# ADR 0004 — Recuperação Git fora do checkout de trabalho

- **Status:** Condicional / bloqueada até cópia canônica
- **Data:** 2026-08-18
- **Contexto:** A auditoria encontrou ownership divergente e objetos Git ausentes.
  O checkout contém alterações não commitadas que pertencem ao proprietário.
- **Decisão:** Não executar `reset`, `prune`, `gc`, reescrita de refs, tomada de
  posse ou exclusão ampla no checkout atual. Preservar uma cópia aprovada, identificar
  remote confiável, criar clone canônico e executar `git fsck` somente nesse clone.
- **Consequências:** A recuperação pode ficar bloqueada até o proprietário fornecer
  identidade e remote confiável, mas nenhuma alteração de trabalho é perdida. O
  runbook registra o próximo passo e o critério de abortar.
- **Rollback:** Abandonar apenas a cópia/clone de recuperação; o checkout original
  permanece intocado e a cópia preservada é a fonte de comparação.

**Procedimento:** `docs/guides/git-recovery-runbook.md`.
