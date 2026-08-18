# Decision Log: Story 2.3

**Agent:** @dev (Dex)  
**Mode:** YOLO/deterministic  
**Story:** `docs/stories/2.3.story.md`  

## Decision

Expandir somente `[tool.ruff].exclude` no `pyproject.toml` para as raízes AIOX e
projeções de IDE/skills.

## Rationale

Os scripts externos distribuídos pelo AIOX não fazem parte do escopo Python do
QuantumScribe. Excluí-los do lint do produto elimina falsos positivos sem mascarar
erros em `localwhisper/`, `main.py` ou `tests/`.

## Alternatives Considered

- Reformatar scripts oficiais AIOX: rejeitado, pois altera conteúdo externo e amplia o escopo.
- Ignorar Ruff inteiro: rejeitado, pois removeria a proteção do código do produto.

## Verification

- Ruff: PASS.
- Compileall: PASS.
- Pytest: 111 passed, 1 skipped por plataforma Linux.
- Doctor: 16 PASS, 2 WARN, 0 FAIL.
