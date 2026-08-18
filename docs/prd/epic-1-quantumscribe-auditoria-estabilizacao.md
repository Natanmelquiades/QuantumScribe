# EPIC-QSAUDIT: QuantumScribe — Estabilização, leveza e governança de qualidade

**Status:** ✅ Done — implementação e QA concluídos; follow-ups operacionais registrados  
**Owner:** Natan Melquiades / Product Management  
**Created:** 2026-08-18  
**Tipo:** Brownfield — consolidação de auditoria técnica e operacional  
**Prioridade:** P1 — Alta  
**Estimativa preliminar:** 34 pontos  

---

## Objective

Transformar os achados da auditoria do QuantumScribe em um plano executável para
reduzir regressões, separar o Core das dependências opcionais, tornar o release
reproduzível e criar limites arquiteturais que permitam evoluir o aplicativo sem
aumentar continuamente sua complexidade. O comportamento principal deve continuar
local, offline quando não houver uma ação explícita de rede, compatível com CPU e
com fallback automático de GPU para CPU.

Este epic foi executado como plano de estabilização. As alterações da auditoria e
das três stories agora formam uma linha de base institucionalizada; os débitos que
restam estão registrados como follow-ups explícitos, sem bloquear o resultado deste
epic.

## Business Value

- Menos falhas silenciosas durante gravação, transcrição, streaming e salvamento de
  configurações.
- Instalação e release menores, mais rápidos e mais previsíveis, sem carregar
  recursos que o usuário não escolheu.
- Menor risco de quebra ao alterar módulos atualmente muito grandes.
- Builds auditáveis, com dependências e hashes conhecidos.
- Diagnóstico e manutenção mais baratos, porque os contratos do sistema passam a
  estar protegidos por testes e documentação.

## Stakeholders

- **Produto e decisão final:** Natan Melquiades.
- **PM responsável pelo epic:** @pm (Morgan).
- **Arquitetura e limites técnicos:** @architect.
- **Detalhamento das histórias:** @sm.
- **Implementação:** @dev e @devops conforme a história.
- **Qualidade:** @qa e os quality gates definidos em cada história.
- **Operação do repositório:** proprietário do projeto, especialmente para a
  recuperação segura do histórico Git.

## Contexto e evidências da auditoria

### Estado atual conhecido

| Área | Evidência observada | Consequência |
| --- | --- | --- |
| Produto | Aplicativo Python desktop para Windows e Linux, baseado em `faster-whisper`; versão `2.2.34`; Python `>=3.11,<3.14`. | A compatibilidade entre plataformas e o comportamento offline são restrições centrais. |
| Testes | Linha de base final: `119 passed, 1 skipped`; `ruff`, `compileall`, `pip check` e `pip-audit` passaram. | Há uma base saudável para refatorar, mas os gates precisam ser repetidos em ambiente limpo e nos sistemas suportados. |
| Cobertura | Aproximadamente 31% no levantamento inicial; lacunas relevantes em `settings_ui.py` (~15%), `app.py` (~28%), `stream_transcriber.py` (~28%), `transcriber.py` (~31%), `quantum_brain.py` (~15%) e `memory`/`vocab_cache` (0%). | Os fluxos críticos podem regredir sem serem detectados. A cobertura deve ser ampliada por risco, não apenas por volume. |
| Complexidade | `app.py` e `settings_ui.py` foram classificados como C; `_transcribe_and_deliver` em `app.py` como F(48); `_animate_atom` em `ui.py` como E(40); `rewrite_text` em `rewriter.py` como E(35); `transcribe` em `transcriber.py` como D(23). | Mudanças pequenas têm alto raio de impacto e exigem extração incremental com gates. |
| Empacotamento | Build PyInstaller temporário de aproximadamente 333,8 MB e 1.434 arquivos. Destaques: CTranslate2 ~56,6 MB, NumPy/SciPy/OpenBLAS ~40 MB, bibliotecas AV ~19 MB, ONNX Runtime ~36 MB e `hf_xet` ~9,5 MB. | Há espaço material para reduzir o Core sem reduzir a qualidade do fluxo principal. |
| Dependências | `requirements-common.txt` mistura dependências essenciais com `onnxruntime`, `scipy` e `noisereduce`, embora o código tenha caminhos opcionais/fallback. Windows usa lock em partes do fluxo, mas `run.ps1` e o caminho Linux ainda aceitam arquivos não fixados. | A instalação e o build podem carregar peso desnecessário e variar entre ambientes. |
| Segurança | `pip-audit` não encontrou vulnerabilidades conhecidas nos arquivos avaliados; o código de atualização possui allowlist HTTPS, SHA-256, staging, limites e extração segura. | A segurança existente deve ser preservada durante a modularização; não há motivo para reescrever o updater neste epic. |
| Higiene de dados | O diretório `temp_test`, com aproximadamente 507 MB de artefatos de modelo e screenshots, foi movido para `D:\EMPRESAS E PROJETOS\My Softwares And Sass\QuantumScribe-audit-quarantine-20260818\temp_test`. | O espaço foi retirado do projeto de forma recuperável; a quarentena só deve ser apagada após confirmação do proprietário. |
| Ambiente local | `.pytest_cache` e `.pytest-tmp` permaneceram porque o Windows negou acesso por outra identidade. | A limpeza final depende de uma ação operacional com a identidade proprietária; não se deve tomar posse nem remover recursivamente sem autorização. |
| Repositório | `git fsck --full --no-reflogs` apontou links quebrados e objetos ausentes; também houve divergência de ownership que impede algumas operações Git no checkout atual. | O histórico não deve ser “consertado” destrutivamente dentro deste checkout. A recuperação precisa de cópia/remote conhecido e clone limpo. |

### Correções seguras já aplicadas durante a auditoria

Estas mudanças já estão na árvore de trabalho e devem ser preservadas ao detalhar as
histórias:

- `localwhisper/audio_enhancer.py`: filtros de áudio agora retornam com segurança
  para buffers vazios ou curtos demais e tratam falhas de dependências opcionais sem
  derrubar o streaming.
- `localwhisper/config.py`: `save_config()` usa arquivo temporário, `fsync` e
  substituição atômica para evitar configuração parcialmente gravada.
- `tests/test_audio_enhancer.py`: foram adicionados testes para buffers curtos,
  vazios e normalização.
- A validação após as correções terminou com `119 passed, 1 skipped`, lint sem
  achados e compilação Python concluída.

Essas correções são uma linha de base de segurança, não justificam marcar o epic ou
qualquer história como concluídos.

## Scope

### In Scope

- Consolidar contratos de confiabilidade para configuração, áudio, transcrição,
  streaming, cancelamento e entrega do texto.
- Expandir testes nos módulos críticos e estabelecer um relatório de cobertura
  reproduzível.
- Separar dependências de runtime, build, teste e componentes opcionais.
- Reduzir o Core CPU e preservar o comportamento `device="auto"`,
  `compute_type="auto"` e fallback para CPU.
- Impedir downloads silenciosos de modelos ou componentes e tornar explícito o
  custo de cada recurso opcional.
- Tornar Windows e Linux capazes de produzir builds limpos a partir de versões e
  hashes fixados.
- Documentar os limites arquiteturais antes de extrair responsabilidades de
  `app.py`, `settings_ui.py`, `stream_transcriber.py`, `transcriber.py`,
  `rewriter.py` e `ui.py`.
- Atualizar a documentação mínima de stack, padrões de código, empacotamento e
  rollback que foi identificada como ausente ou incompleta.
- Definir uma recuperação segura para o histórico Git e concluir a limpeza de
  artefatos somente com uma identidade que tenha posse dos arquivos.

### Out of Scope

- Novas funcionalidades de produto como busca semântica, modo cloud, redesign do
  histórico, ícones ou fila de transcrições, salvo quando forem necessárias apenas
  para não quebrar contratos existentes.
- Reescrita completa do aplicativo em outro framework ou linguagem.
- Remoção automática de modelos, configurações, notas, histórico, backups legados
  ou dados pessoais do usuário.
- Reparar o banco de objetos Git com `reset`, reescrita de histórico, `prune` ou
  exclusão de objetos sem cópia e decisão explícita do proprietário.
- Reescrever o sistema de atualização segura, que passou nos testes de segurança da
  auditoria.
- Instalar drivers, reiniciar o Windows ou fazer `pip install` na máquina do usuário
  final.

## Stories

| ID | Título | Pontos | Prioridade | Status | Executor | Quality gate |
| --- | --- | ---: | --- | --- | --- | --- |
| QS-AUDIT-001 | Fortalecer contratos de execução e regressão | 8 | P1 | Done | @dev | @architect |
| QS-AUDIT-002 | Separar Core, componentes opcionais e release reproduzível | 13 | P1 | Done | @devops | @architect |
| QS-AUDIT-003 | Modularizar o núcleo e fechar a governança de manutenção | 13 | P1 | Done | @architect | @pm |

**Total:** 34 pontos preliminares  
**Concluído:** 34 pontos do epic  
**Dependência:** as histórias devem ser refinadas pelo @sm e executadas em ordem,
com apenas uma história em progresso por vez.

### QS-AUDIT-001 — Fortalecer contratos de execução e regressão

**Objetivo:** proteger os fluxos que já funcionam, registrar os contratos revelados
pela auditoria e aumentar a cobertura dos caminhos mais arriscados antes de grandes
refatorações.

**Escopo da história:**

- Preservar e ampliar os testes dos buffers curtos/vazios e da gravação atômica de
  configuração.
- Criar testes de regressão para inicialização, sessões de transcrição,
  cancelamento, streaming, entrega/clipboard e falhas controladas de dependências
  opcionais.
- Medir cobertura por módulo e registrar os caminhos críticos ainda sem proteção.
- Separar testes unitários de testes dependentes de dispositivo, rede, modelo ou
  ambiente Windows.
- Manter mensagens e fallback seguros sem introduzir uma mudança de UX não
  especificada.

**Critérios de aceite preliminares:**

- O conjunto existente e os novos testes passam sem reduzir a linha de base de
  `119 passed, 1 skipped`.
- Um buffer vazio ou menor que o mínimo de cada filtro não lança exceção nem produz
  NaN/Inf; uma falha opcional retorna ao caminho seguro documentado.
- Uma falha durante a escrita de configuração não substitui o arquivo válido por um
  arquivo parcial.
- Cada caminho crítico alterado na história tem teste determinístico ou justificativa
  explícita para um teste de integração/ambiente.
- O relatório de cobertura é reproduzível e não há queda de cobertura nos módulos
  tocados.
- `ruff`, compilação, `pip check` e a auditoria de dependências continuam passando.

**Executor:** @dev  
**Quality gate:** @architect  
**Quality gate tools:** `pytest`, `pytest-cov`, `ruff`, `compileall`, `pip check`,
`pip-audit`, testes de integração controlados e revisão de diffs.

**Dependências relacionadas:** PRD QS-017; backlog QS-017, QS-023, QS-024,
QS-025 e QS-026.

### QS-AUDIT-002 — Separar Core, componentes opcionais e release reproduzível

**Objetivo:** entregar um Core CPU mínimo e funcional, retirando do bundle inicial
dependências que só pertencem a GPU, streaming neural, melhoria avançada, build ou
testes, sem perder qualidade ou o fallback automático.

**Escopo da história:**

- Auditar imports reais e separar perfis de runtime, build, teste e componentes
  opcionais.
- Reavaliar `onnxruntime`, `scipy`, `noisereduce`, CUDA, Torch e demais bibliotecas
  pesadas segundo uso comprovado e benchmark, sem assumir que toda dependência
  declarada é essencial.
- Criar locks equivalentes e verificáveis para Windows e Linux, incluindo hashes
  nos caminhos de release.
- Fazer build em ambiente limpo, gerar inventário de arquivos/tamanhos e preservar
  o comportamento `auto` de hardware.
- Garantir que modelos e componentes opcionais só sejam baixados após ação explícita
  do usuário, com tamanho, origem, hash e espaço necessários visíveis.
- Manter o updater seguro e reutilizar seus controles de origem, staging e hash.

**Critérios de aceite preliminares:**

- O Core CPU atende ao alvo já definido no PRD de Core Leve: instalador/bundle de no
  máximo 250 MB, sem diretórios `nvidia`, `torch` ou modelos embutidos.
- A instalação limpa abre sem iniciar download de modelo ou componente e continua
  funcional offline até que o usuário solicite um recurso de rede.
- `device="auto"` e `compute_type="auto"` permanecem os padrões; GPU compatível é
  priorizada e falhas de GPU retornam para CPU sem impedir a transcrição.
- Dependências de build e teste não são carregadas no runtime do usuário e os
  componentes opcionais não são instalados via `pip` na máquina final.
- Build de Windows e Linux começa de ambiente limpo e usa locks/hashes auditáveis.
- O inventário do artefato demonstra a redução de peso e não introduz regressão de
  importação, transcrição, streaming básico ou inicialização.
- `pytest`, `ruff`, `pip check`, `pip-audit` e o smoke test do artefato passam.

**Executor:** @devops  
**Quality gate:** @architect  
**Quality gate tools:** `build.ps1`, `run.ps1`, `QuantumScribe.spec`, PyInstaller,
locks com `--require-hashes`, inventário do bundle, `pip-audit`, testes de instalação
limpa e smoke tests Windows/Linux.

**Dependências relacionadas:** `docs/PRD_CORE_LEVE_COMPONENTES_SOB_DEMANDA.md`,
backlog QS-019, QS-020, QS-021 e QS-026; QS-AUDIT-001.

### QS-AUDIT-003 — Modularizar o núcleo e fechar a governança de manutenção

**Objetivo:** reduzir o raio de impacto das mudanças, eliminar funções críticas com
complexidade extrema de forma incremental e deixar o projeto recuperável e
compreensível para os próximos ciclos.

**Escopo da história:**

- Produzir um mapa arquitetural focado nos fluxos de gravação, transcrição,
  streaming, configurações, entrega e empacotamento.
- Definir contratos e fronteiras antes de extrair responsabilidades dos monólitos:
  `app.py`, `settings_ui.py`, `stream_transcriber.py`, `transcriber.py`,
  `rewriter.py` e `ui.py`.
- Extrair primeiro seams com testes de caracterização; evitar uma reescrita ampla ou
  uma mudança simultânea de comportamento e estrutura.
- Criar ou atualizar a documentação de stack, padrões de código, decisões de
  arquitetura, build e rollback, hoje apontada como incompleta pelo AIOX.
- Definir um runbook não destrutivo para o problema de ownership e objetos ausentes
  do Git, incluindo cópia do checkout, identificação de remote conhecido e clone
  canônico limpo.
- Concluir a limpeza de caches protegidos somente com a identidade proprietária,
  sem assumir posse nem remover diretórios amplos.

**Critérios de aceite preliminares:**

- O mapa arquitetural e as decisões de fronteira são revisados pelo @architect antes
  da primeira extração.
- Cada extração mantém os testes da história QS-AUDIT-001 e não altera o contrato
  funcional sem uma história específica.
- As funções classificadas como E/F na auditoria deixam de ser o ponto central de
  coordenação ou têm um plano aprovado de decomposição; nenhuma complexidade nova
  equivalente é introduzida.
- O projeto tem documentação mínima de stack, padrões, arquitetura, testes,
  empacotamento e rollback em locais que o AIOX consiga referenciar.
- O histórico Git é validado em um clone/cópia canônica conhecido, ou há um runbook
  aprovado e um bloqueio explícito caso o remote não seja confiável; nenhum reparo
  destrutivo é feito no checkout de trabalho.
- `.pytest_cache`, `.pytest-tmp` e artefatos temporários não ficam misturados ao
  código-fonte quando a limpeza puder ser executada pela identidade correta.

**Executor:** @architect  
**Quality gate:** @pm  
**Quality gate tools:** `radon`, `pytest`, `ruff`, `rg`, revisão de dependências,
`git fsck` em clone canônico e inspeção dos documentos de arquitetura/rollback.

**Dependências relacionadas:** QS-AUDIT-001; QS-AUDIT-002 para não criar novas
fronteiras em torno de dependências que serão removidas; PRD QS-017, PRD QS-018 e
PRD de Core Leve.

## Sequenciamento e dependências

1. **QS-AUDIT-001:** primeiro, porque testes de caracterização e contratos reduzem
   o risco de mexer nos monólitos e no empacotamento.
2. **QS-AUDIT-002:** segundo, porque a separação de dependências precisa de um
   inventário confiável e deve ser medida em build limpo.
3. **QS-AUDIT-003:** terceiro, com arquitetura documentada; suas extrações devem
   respeitar os limites e os componentes definidos na história 2.

O @sm deve criar as histórias em `docs/stories`, detalhar cada arquivo e fluxo
afetado, dividir tarefas quando a estimativa deixar de ser confiável e confirmar
os critérios de aceite com o @pm e o @architect.

## Compatibility Requirements

- Preservar Windows e Linux dentro do intervalo Python já declarado em
  `pyproject.toml`.
- Preservar ditado local, modo CPU, seleção automática de hardware e fallback GPU →
  CPU.
- Não introduzir rede no caminho ocioso nem downloads silenciosos.
- Preservar configurações, histórico, modelos existentes e dados do usuário; toda
  migração deve ser aditiva, reversível e validada.
- Manter o fluxo de build PyInstaller e os scripts de execução até que seu substituto
  tenha paridade comprovada.
- Manter os controles de segurança do updater e os limites de extração/atualização.
- Compatibilidade com o trabalho não commitado existente: nenhuma história pode
  descartar ou sobrescrever mudanças prévias sem revisão do diff e decisão explícita.

## Success Criteria

- [x] A suíte de regressão passa no ambiente disponível, sem queda em relação à
  linha de base original de 119 testes aprovados e 1 ignorado; o estado final tem
  158 testes aprovados e 1 ignorado.
- [x] Os fluxos críticos de configuração, áudio, transcrição, streaming,
  cancelamento, entrega e atualização possuem cobertura proporcional ao risco e um
  relatório reproduzível.
- [x] O Core CPU atinge o limite de no máximo 250 MB definido no PRD de Core Leve,
  sem empacotar CUDA, Torch ou modelos que não sejam necessários ao Core.
- [x] Nenhum modelo ou componente opcional é baixado sem confirmação explícita e
  informação de tamanho/origem/integridade.
- [x] Builds de Windows e Linux podem ser recriados a partir de dependências
  versionadas e hashes verificáveis.
- [x] As áreas de complexidade E/F têm decomposição aprovada e não concentram novas
  responsabilidades críticas.
- [x] O projeto possui documentação mínima de stack, padrões, arquitetura, testes,
  release e rollback.
- [x] O estado Git tem bloqueio de recuperação formalmente registrado, com
  responsável e próximo passo, até existir clone canônico confiável.
- [x] A limpeza não remove dados do usuário e todo artefato removido permanece
  recuperável até a confirmação do proprietário.

## Technical Requirements

- Python `>=3.11,<3.14`; respeitar `pyproject.toml` como fonte de metadados do
  projeto.
- Manter `ruff` com a configuração existente e os gates de compilação e dependências.
- Separar arquivos `requirements-*.txt`/locks por finalidade, documentando a fonte
  de cada dependência direta.
- Produzir o bundle em ambiente limpo, com relatório de tamanho e lista dos maiores
  artefatos.
- Usar staging e promoção atômica para configurações, modelos, componentes e
  releases.
- Testar caminhos sem dependências opcionais, com buffers pequenos, sem rede, com
  falha de GPU e com cancelamento.
- Não usar exclusão recursiva de diretório arbitrário para limpeza, desinstalação ou
  recuperação.

## Risk Mitigation and Rollback

| Risco | Impacto | Mitigação | Rollback |
| --- | --- | --- | --- |
| Separar dependências reduz qualidade de áudio/transcrição | Alto | Benchmark CPU/GPU, testes de caracterização e fallback leve antes do release. | Manter o perfil anterior como artefato temporário e reativar o componente somente em release controlado. |
| Refatorar monólitos quebra foco, cancelamento ou entrega | Alto | Extração por seam, uma história por vez, testes antes/depois e feature flag quando necessário. | Reverter somente a extração da história, preservando os testes e os contratos. |
| Build menor omite um import dinâmico | Alto | Build limpo, inspeção de hidden imports, smoke test instalado e execução em máquina sem ambiente de desenvolvimento. | Publicar o artefato anterior conhecido como bom até corrigir o manifesto. |
| Dependências não fixadas reproduzem resultados diferentes | Médio | Locks com hashes para todos os alvos suportados e CI limpo. | Bloquear release sem lock válido; não “corrigir” instalando versões flutuantes. |
| Git tem objetos ausentes ou ownership inconsistente | Crítico | Cópia do checkout, remote confiável, clone canônico e validação `git fsck`; não usar reset/prune no original. | Abandonar o checkout corrompido após preservar alterações e continuar em clone limpo. |
| Limpeza remove artefatos ou dados do usuário | Alto | Quarentena recuperável, caminhos explícitos, confirmação do proprietário e testes de proteção. | Restaurar da quarentena; não apagar caches protegidos por outra identidade. |
| Falta de documentação gera decisões divergentes | Médio | @architect aprova mapa e ADR antes da extração; @pm valida escopo. | Pausar a implementação e retornar a uma história de documentação/refinamento. |

## QA Strategy

### Gates automatizados

- `pytest` com testes unitários e integração controlada.
- `pytest-cov` para acompanhar os módulos críticos e evitar regressão de cobertura.
- `ruff` e compilação Python.
- `pip check` e `pip-audit` para os perfis de dependência.
- `radon` para acompanhar a complexidade dos pontos de extração.
- Build PyInstaller em ambiente limpo, inventário de tamanho e inspeção de imports.
- `git fsck` somente em cópia/clone canônico para a saúde do repositório.

### Validação manual

- Instalação limpa em CPU e, quando disponível, máquina com GPU compatível.
- Primeiro uso sem rede: aplicativo abre sem download silencioso.
- Gravação, cancelamento, transcrição, streaming básico, entrega e reinicialização.
- Falha controlada de componente opcional com fallback para CPU.
- Atualização e desinstalação sem apagar configurações, modelos, histórico ou
  arquivos externos ao produto.

## Definition of Done

- [x] @sm criou e refinou as três histórias em `docs/stories`.
- [x] Cada história possui executor, quality gate, ferramentas, dependências,
  critérios de aceite e rollback.
- [x] Não há história em execução sem os testes de caracterização necessários.
- [x] As validações automatizadas aplicáveis passam; a validação Linux local fica
  pendente apenas por ausência de bash/WSL e já está coberta pelo workflow de release.
- [x] O tamanho, o conteúdo e a origem do bundle estão registrados.
- [x] Dependências de release estão fixadas e auditadas para Windows e Linux.
- [x] Documentação de arquitetura, stack, padrões, release e rollback está atualizada.
- [x] O trabalho não commitado existente foi revisado e nenhum arquivo do usuário foi
  descartado.
- [x] A situação do Git está formalmente bloqueada com plano seguro aprovado até
  existir clone canônico.
- [x] @architect aprovou as mudanças estruturais e @pm aprovou o resultado do epic.

## PO Validation Snapshot

| Categoria | Status | Observação |
| --- | --- | --- |
| Integração com sistema existente | Aprovado | Três stories concluídas; rollback por story e caracterização preservados. |
| Ambiente e dependências | Aprovado | Core, build, teste e componentes possuem perfis/locks separados. |
| Testes | Aprovado com follow-up | 158 testes passam e a cobertura de risco foi ampliada; módulos E/F permanecem planejados. |
| Segurança | Aprovado com preservação | Auditoria de dependências e updater passaram; a refatoração não deve reduzir controles. |
| Empacotamento/release | Aprovado com follow-up | Core Windows validado em 219,354 MB; smoke Linux depende de runner nativo. |
| Arquitetura/documentação | Aprovado | Mapas, boundaries, ADRs, stack, padrões, testes e rollback publicados. |
| Higiene do repositório | Bloqueado operacionalmente | Há objetos Git ausentes/links quebrados e divergência de ownership no checkout atual. |
| Escopo do MVP deste epic | Aprovado | Três stories macro concluídas; expansões futuras exigem PRD/arquitetura próprios. |

**Decisão:** APPROVED / DONE. O epic atingiu seus critérios com follow-ups
operacionais explícitos: executar smoke Linux em runner disponível, limpar lint
preexistente do framework em escopo separado, extrair `delivery.py` em nova story e
recuperar o Git somente com o proprietário.

## Handoff

Próximo responsável: **@sm**.

Solicitação: criar as histórias detalhadas a partir de QS-AUDIT-001, QS-AUDIT-002 e
QS-AUDIT-003, mantendo a ordem, vinculando os arquivos reais do projeto e separando
qualquer trabalho que ultrapasse o limite de três histórias. Antes de autorizar a
implementação estrutural, o @sm deve solicitar revisão do @architect. O @pm deve
validar as histórias finais, critérios de aceite e a decisão sobre a recuperação do
Git com o proprietário do repositório.

## Documentation

| Tipo | Local | Status |
| --- | --- | --- |
| Epic AIOX | `docs/prd/epic-1-quantumscribe-auditoria-estabilizacao.md` | Criado |
| PRD relacionado | `docs/PRD_CORE_LEVE_COMPONENTES_SOB_DEMANDA.md` | Existente e deve ser referência principal para peso/componentes |
| PRD relacionado | `docs/PRD_QS017_ESTABILIDADE_HUD_INICIALIZACAO.md` | Existente; alinhar contratos de sessão/HUD |
| PRD relacionado | `docs/PRD_QS018_ATUALIZACAO_APLICATIVO.md` | Existente; preservar segurança do updater |
| Backlog | `docs/PRODUCT_BACKLOG.md` | Atualizar vínculos quando as histórias forem criadas |
| Stories | `docs/stories/` | Stories 1.1, 1.2 e 1.3 `Done` com gates QA |
| Arquitetura | `docs/architecture/` | Publicada: mapa, boundaries, complexidade e ADRs |
| Stack/padrões | `docs/framework/` | Publicados e carregados pelo AIOX |
| Runbook Git | `docs/guides/git-recovery-runbook.md` | Publicado; recuperação permanece owner-gated |

## Change Log

| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2026-08-18 | 1.0 | Epic criado a partir da auditoria completa do QuantumScribe, incluindo baseline, correções seguras, riscos, escopo, histórias e handoff. | @pm (Morgan) |
| 2026-08-18 | 1.1 | Stories 1.1–1.3 concluídas; QA PASS; documentação, Core/release, boundaries e runbook registrados. | @pm (Morgan) |

---

**Generated by:** AIOX PM brownfield-create-epic workflow  
**Template basis:** AIOX `product/templates/epic.hbs` v1.0  
**Next command:** `@pm` → acompanhar follow-ups operacionais fora do escopo concluído
