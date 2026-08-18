# QuantumScribe — Padrões de código

## Convenções

- Python com funções/módulos em `snake_case`, tipos modernos quando já adotados e
  docstrings claras nos contratos e seams.
- Ruff é obrigatório; target Python `py311`, line length 110 e regras E/F/I/W
  conforme `pyproject.toml`.
- Preferir módulos planos enquanto não houver coesão real para um pacote; não criar
  camadas apenas para esconder uma dependência.
- Imports relativos podem permanecer dentro do mesmo módulo/feature; novos imports
  devem respeitar a direção registrada em `docs/architecture/module-boundaries.md`.

## Limites de dependência

- `contracts.py` e `session_controller.py` usam somente biblioteca padrão e não
  importam UI, Tkinter, Whisper, áudio físico ou componentes opcionais.
- Domínio/pipeline não importa widgets. Workers comunicam eventos ao thread de UI
  por callbacks seguros; não atualizam widgets diretamente.
- `app.py` compõe adaptadores e mantém fachadas durante a migração; não é permitido
  mover comportamento em massa sem story própria.
- Imports de `torch`, ONNX, SciPy, `noisereduce` e CUDA ficam em caminhos opcionais
  ou adaptadores já previstos e não podem ser puxados pelo Core ocioso.

## Segurança e persistência

- Persistência usa arquivo temporário no mesmo diretório, flush/fsync quando
  aplicável e `os.replace`.
- Caminhos de arquivo são resolvidos e validados antes de extrair, promover ou
  remover; nunca usar exclusão recursiva arbitrária.
- Logs técnicos não registram áudio, texto ditado, tokens, credenciais ou dados
  pessoais.
- Downloads permanecem atrás dos controles existentes de HTTPS, allowlist, staging,
  tamanho, hash e promoção atômica.

## Revisão

Antes de concluir uma story: conferir o mapa de imports, executar os gates definidos
na story, atualizar File List e registrar qualquer desvio em ADR. Não corrigir um
problema de arquitetura alterando simultaneamente comportamento e estrutura.
