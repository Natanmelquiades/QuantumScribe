# PRD — Implementação integral do Product Backlog

**Status:** aprovado para planejamento e execução por ondas
**Escopo:** QS-001 a QS-016
**Prioridade do programa:** estabilizar o fluxo principal antes de expandir
capacidades locais e, por último, validar a oferta cloud opcional.

## Objetivo

Entregar todos os itens do Product Backlog de forma incremental, mantendo a
transcrição local confiável em cada release. O programa não autoriza sacrificar
segurança de gravações, privacidade local, compatibilidade Windows ou qualidade
da interface para acelerar funcionalidades posteriores.

Cada QS continua sendo uma unidade independente de aceite. PRDs específicos já
existentes prevalecem em seus detalhes; este documento define a ordem, os
contratos entre frentes e os portões para avançar.

## Inventário e prioridade

| Prioridade | Itens | Resultado principal |
| --- | --- | --- |
| P1 | QS-001, QS-002, QS-003, QS-004, QS-006, QS-007, QS-011, QS-015, QS-016 | Fluxo de ditado, onboarding e recuperação confiáveis |
| P2 | QS-005, QS-009, QS-010, QS-012, QS-013, QS-014 | Melhorias de capacidade, recuperação e automação controlada |
| P3 | QS-008 | Personalização visual complementar |

## Princípios de execução

- Nenhuma gravação, texto ou item de fila pode ser perdido por transição de UI,
  cancelamento ou falha recuperável.
- A operação local e offline permanece disponível; cloud é opcional e exige
  consentimento explícito antes de enviar áudio ou texto.
- Alterações de estado assíncronas usam identidade de sessão/job para que eventos
  atrasados não afetem uma gravação, HUD ou entrega posterior.
- Recursos configuráveis devem declarar dependências, estado efetivo e fallback
  de modo claro na interface.
- Cada onda termina com testes automatizados relevantes, teste manual no pacote
  Windows e atualização de documentação de usuário quando houver mudança visível.

## Ondas de entrega

### Onda 0 — Base de qualidade e contrato de estados

**Itens envolvidos:** pré-requisito comum para QS-001, QS-004, QS-014, QS-015 e
QS-016.

1. Mapear os estados de gravação, transcrição, entrega, cancelamento e HUD.
2. Centralizar identificação de sessão/job e cancelamento seguro de callbacks.
3. Cobrir os fluxos críticos com testes de regressão: iniciar/finalizar rápido,
   cancelar, erro de microfone, falha de entrega e fechamento do app.

**Portão:** os testes provam que callbacks e sons tardios não alteram uma sessão
nova, e o aplicativo permanece utilizável após falhas comuns.

### Onda 1 — Confiabilidade do fluxo principal (P1)

| Ordem | Itens | Entrega |
| --- | --- | --- |
| 1 | QS-004, QS-016 | HUD estável e cancelamento intencional por `Esc` mantido |
| 2 | QS-015, QS-009 | Controles de som restaurados e controle de volume moderno acessível |
| 3 | QS-001 | Fila FIFO persistente de transcrições, com destinos e estados isolados |
| 4 | QS-014 | Entrega no destino original, foco atual ou clipboard, por escolha do usuário |
| 5 | QS-002, QS-003 | Perfil de transcrição exata e matriz de dependências de configurações |
| 6 | QS-006, QS-005 | Download resiliente, validação e reutilização segura de modelos existentes |
| 7 | QS-007 | Identidade de ícone unificada no app e pacote Windows |
| 8 | QS-011 | Busca textual local no histórico |

QS-009 é P2 no backlog, mas deve acompanhar QS-015 por compartilhar o controle
de efeitos; seu aceite próprio permanece obrigatório. QS-005 deve ser entregue
antes ou junto da etapa de seleção de modelo de QS-006, nunca como validação
superficial após o download.

**Portão:** numa instalação limpa e numa atualização, o usuário consegue baixar
ou reutilizar um modelo, gravar ditados consecutivos, cancelar apenas de forma
intencional, receber o texto no destino escolhido e pesquisar seu histórico sem
perder dados.

### Onda 2 — Histórico, pesquisa e personalização local

| Ordem | Itens | Entrega |
| --- | --- | --- |
| 1 | QS-010 | Histórico em tabela/lista local legível, preservando os Markdown |
| 2 | QS-011 | Integração visual completa da busca textual já entregue na Onda 1 |
| 3 | QS-012 | Busca semântica local opcional, com fallback textual obrigatório |
| 4 | QS-008 | Cor personalizada em superfícies que suportem atualização dinâmica |

QS-010 e QS-011 compartilham a fonte de dados, mas a busca textual não depende
do redesenho visual para existir. QS-012 só inicia após QS-011 manter índice e
reconstrução confiáveis.

**Portão:** o histórico antigo continua íntegro, uma busca textual funciona em
todos os arquivos e a busca semântica só aparece em máquinas compatíveis, sem
reduzir a capacidade local mínima.

### Onda 3 — Pesquisa e decisão do modo cloud

**Item:** QS-013.

Esta onda é uma pesquisa com protótipo técnico e avaliação de produto; não é
autorização para transmitir dados automaticamente nem lançar cobrança. Deve
produzir uma decisão documentada sobre provedores, custos, autenticação,
consentimento, LGPD, retenção, exclusão, limites, observabilidade e fallback
local. Caso aprovada, um PRD de produto/comercial próprio definirá o MVP cloud.

**Portão:** proposta viável, custo sustentável, fluxo de consentimento validado
e garantia de que recursos locais existentes não serão bloqueados por assinatura.

## Dependências críticas

```text
QS-004 ─┬─> QS-001 ─> QS-014
QS-016 ─┘
QS-015 ─> QS-009
QS-002 <─> QS-003
QS-005 ─> QS-006
QS-010 ─> QS-011 ─> QS-012 ─> QS-013
QS-007 ─> QS-008
```

- A implementação de QS-001 deve incorporar as proteções de sessão de QS-004 e
  QS-016, mas os critérios de aceite de cada item serão testados separadamente.
- QS-014 deve tratar destino por job, portanto depende da modelagem de fila em
  QS-001 quando coexistirem transcrições.
- QS-006 deve chamar QS-005 antes de transferir arquivos grandes.
- QS-012 não substitui QS-011: a pesquisa textual é o fallback universal.
- QS-008 não deve prometer atualizar o ícone estático da barra de tarefas quando
  o Windows exigir reinício, novo atalho ou invalidação de cache.

## Requisitos transversais

### Qualidade e testes

- Adicionar testes unitários para máquinas de estado, persistência, validação de
  modelos, índice e regras de configuração.
- Adicionar testes de integração para fila, entrega, download/interrupção e
  histórico de arquivos reais em diretório temporário.
- Fazer smoke test manual do executável Windows em instalação limpa e atualização
  para qualquer mudança em instalação, ícone, hotkey ou áudio.
- Registrar erros técnicos sem conteúdo ditado, chaves, tokens ou caminhos
  pessoais completos.

### Compatibilidade e migração

- Configurações antigas devem ter valores padrão seguros e migração explícita.
- Os arquivos Markdown do histórico são a fonte preservada até haver exportação
  equivalente e reversível.
- Dados de fila, índices e cache devem usar gravação atômica e recuperação de
  arquivos válidos após encerramento inesperado.

### Privacidade e segurança

- Modelos, áudio, transcrições, índices e diagnósticos permanecem locais por
  padrão.
- Qualquer modo remoto deve listar dados enviados, finalidade, fornecedor,
  retenção e ação para revogar consentimento antes da primeira transmissão.
- Não aceitar modelos, pacotes ou URLs arbitrárias; validar origem, formato e
  integridade antes de uso.

## Definição de concluído por item

Um item QS só passa para `Concluído` quando:

1. seus critérios de aceite próprios foram verificados;
2. os testes novos e a suíte existente passam;
3. fluxos P1 relacionados foram reexecutados quando houver mudança em estados,
   configuração, HUD, áudio, entrega ou persistência;
4. documentação, versão e notas de comportamento visível foram atualizadas;
5. não há regressão conhecida de dados, privacidade ou acessibilidade sem um
   bloqueio explicitamente registrado.

## Fora de escopo deste PRD

- Implementar todas as ondas em uma única release ou sem validação intermediária.
- Transformar a pesquisa QS-013 em produto pago sem decisão e PRD específicos.
- Remover o modo local para priorizar cloud.
- Considerar um item concluído apenas por ter código escrito, sem verificação.

## Referências

- [Product Backlog](PRODUCT_BACKLOG.md)
- [PRD QS-001 — Fila de transcrições](PRD_FILA_TRANSCRICOES.md)
- [PRD QS-002 — Transcrição Exata](PRD_QS002_TRANSCRICAO_EXATA.md)
- [PRD QS-003 — Configurações contextuais](PRD_QS003_CONFIGURACOES_CONTEXTUAIS.md)
- [PRD QS-004 — HUD em transições](PRD_QS004_HUD_ICONE_TRANSICOES.md)
- [PRD QS-006 — Download resiliente](PRD_QS006_DOWNLOAD_MODELO_RESILIENTE.md)
- [PRD QS-007 — Ícones oficiais](PRD_QS007_ICONES_OFICIAIS.md)
- [PRD QS-011 — Pesquisa textual](PRD_QS011_PESQUISA_TRANSCRICOES.md)
