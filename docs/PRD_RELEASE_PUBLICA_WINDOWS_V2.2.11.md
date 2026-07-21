# PRD — Release pública Windows v2.2.11

**Status:** em execução  
**Responsável:** Natan Melquiades  
**Data:** 21/07/2026  
**Release-alvo:** `v2.2.11`

## 1. Objetivo

Disponibilizar publicamente a versão atual do QuantumScribe para Windows como
um instalador `.exe`, com uma release verificável no GitHub e o código-fonte
correspondente publicado no repositório oficial.

## 2. Escopo

- Incrementar a versão patch centralizada para `2.2.11`.
- Validar o código antes da publicação.
- Gerar o instalador Windows x64 a partir do build reproduzível do projeto.
- Publicar a tag `v2.2.11`, o instalador e os artefatos complementares pela
  automação de release do GitHub.
- Manter a release pública, final (não rascunho e não pré-release) e associada
  ao commit publicado.

## 3. Fora do escopo

- Assinatura de código para Windows SmartScreen.
- Publicação em Microsoft Store.
- Inclusão de modelos de transcrição ou dados do usuário no repositório.
- Alterações funcionais além das já presentes na versão atual.

## 4. Requisitos

1. A versão deve permanecer idêntica em `localwhisper/__init__.py` e
   `pyproject.toml`.
2. O build deve usar `build.ps1 -Installer` e o instalador deve seguir o padrão
   `QuantumScribe-Setup-2.2.11-Windows-x64.exe`.
3. A publicação precisa executar a validação automatizada configurada no
   workflow de release: compilação Python, Ruff, testes e auditoria de
   dependências.
4. A release deve anexar, no mínimo, o instalador, o ZIP portátil Core, os
   componentes opcionais CUDA e Silero VAD e `SHA256SUMS.txt`.
5. Nenhuma credencial, transcrição, backup, modelo local ou dado pessoal pode
   ser publicado como parte dos arquivos da release.

## 5. Riscos e mitigação

| Risco | Mitigação |
| --- | --- |
| Falha de build em ambiente local | Usar o workflow Windows isolado e reproduzível do GitHub Actions. |
| Artefato incompatível ou corrompido | Publicar hashes SHA-256 para todos os arquivos distribuídos. |
| Publicação de conteúdo sensível | Manter builds, dados de usuário e configurações reais fora do Git e revisar o diff antes do push. |
| Aviso do SmartScreen | Informar que o instalador ainda não possui assinatura de código e preservar a origem verificável na release oficial. |

## 6. Critérios de aceite

- [ ] `2.2.11` está centralizada nos metadados do produto.
- [ ] As validações obrigatórias do workflow de release passaram.
- [ ] A tag `v2.2.11` aponta para o commit publicado no GitHub.
- [ ] A release `v2.2.11` está pública, sem rascunho e sem pré-release.
- [ ] O instalador `.exe` e os demais artefatos previstos estão disponíveis na release.
- [ ] Os hashes SHA-256 estão disponíveis para conferência pelo usuário.

