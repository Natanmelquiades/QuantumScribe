# EPIC-AIOX: Integridade e executabilidade do AIOX local

**Status:** Done
**Objetivo:** Corrigir a instalação local do AIOX para que o CLI, os agentes, os workflows e as validações funcionem de forma coerente no QuantumScribe.

## Contexto

A auditoria do framework encontrou uma instalação local baseada na versão 5.4.1, porém sem a raiz de distribuição do pacote e sem o módulo de métricas exigido pelo CLI. Também foram encontrados contratos inconsistentes em agentes e workflows.

## Escopo

- Restaurar componentes oficiais ausentes do AIOX sem substituir customizações do projeto.
- Corrigir contratos de agentes e referências de dependências que impedem validação ou execução.
- Tornar explícita a distinção entre workflows executáveis e templates de orquestração.
- Alinhar as instruções locais com a estrutura real do projeto.

## Fora de escopo

- Alterar o código funcional do QuantumScribe.
- Fazer push, criar PR ou publicar release.
- Substituir integralmente a instalação local por uma cópia não auditada do upstream.

## Story

- [x] AIOX local inicializa o CLI e responde a `--help`.
- [x] Agentes principais passam na validação estrutural.
- [x] Workflows executáveis passam no validador correspondente.
- [x] Templates de epic não são falsamente tratados como workflows lineares.
- [x] A documentação de comandos corresponde aos executáveis reais.

## Critérios de aceite

1. `node .aiox-core/cli/index.js --help` termina com sucesso.
2. O diagnóstico do CLI consegue ser carregado sem erro de módulo ausente.
3. O agente UX possui comandos no formato canônico de lista.
4. Nenhuma dependência obrigatória de agente aponta para arquivo inexistente.
5. O fluxo story→QA permanece preservado e validável.
6. As validações do aplicativo QuantumScribe continuam passando.

## Riscos e rollback

- Componentes oficiais devem ser restaurados somente nos caminhos ausentes ou comprovadamente quebrados.
- Alterações locais do usuário devem ser preservadas.
- Cada correção deve ser validada antes da próxima.

## Handoff

Implementação concluída e validada localmente. A publicação remota permanece fora desta epic e requer `@devops` com confirmação explícita.

<!-- [closure-key: 2.2:digest:working-tree-digest:4e0fd17e310a8ce4609b98298ed83715431c93ef53e14e8989050063719096c0] -->
<!-- [closure-key: 2.3:commit:02448f295ec435be09790642c584cfd565559fba] -->
