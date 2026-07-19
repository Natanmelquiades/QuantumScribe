# PRD QS-002 — Modo Transcrição Exata

**Status:** proposta para validação
**Prioridade:** P1 — Alta
**Esforço preliminar:** M
**Relacionado a:** QS-003 — Configurações contextuais

## Contexto

O Quantum Scribe oferece modo literal, pontuação assistida, remoção de
repetições, remoção de hesitações, dicionário, estilos e reescrita por LLM. Essas
opções atendem necessidades diferentes, mas combinações pouco claras podem fazer
o texto final divergir do que o usuário acredita ter configurado.

Hoje o pipeline já evita várias transformações quando `literal_mode` está ativo,
porém a interface não apresenta uma regra única de precedência nem explica quais
opções continuam efetivas.

## Problema

- O usuário não sabe rapidamente se palavras poderão ser removidas ou trocadas.
- Controles incompatíveis podem parecer ativos mesmo sem produzir efeito.
- Alterar configurações ao longo dos dias gera resultados difíceis de prever.
- “Literal” pode ser entendido como preservar palavras ou preservar toda a saída,
  inclusive pontuação; essa diferença não está explícita.

## Objetivo

Oferecer um modo inequívoco para preservar o conteúdo falado, com uma ação de
restauração segura, resumo do processamento efetivo e dependências atualizadas ao
vivo.

## Experiência proposta

### Controle principal

Exibir `Preservar exatamente as palavras` como controle principal da seção de
texto. Quando ativado, a interface informa `Nenhuma palavra será removida,
substituída ou reescrita`.

### Pontuação

Manter `Ajustar somente pontuação` como opção compatível e independente, pois não
deve alterar a sequência de palavras. A descrição precisa deixar claro que ela
pode adicionar ou corrigir sinais.

### Ação Transcrição Exata

Oferecer `Usar configuração mais fiel`, que ativa preservação de palavras e
desativa também a assistência de pontuação. Essa ação representa a saída com o
menor pós-processamento possível.

### Resumo efetivo

Mostrar um resumo persistente:

- `Transcrição exata — sem pós-processamento`;
- `Palavras preservadas — pontuação assistida`;
- `Transcrição aprimorada — 3 ajustes ativos`.

## Matriz de compatibilidade mínima

| Opção | Com preservação de palavras | Motivo |
| --- | --- | --- |
| Pontuação assistida | Permitida, escolha explícita | Altera sinais, não palavras |
| Remover repetições | Desabilitada | Remove palavras faladas |
| Remover hesitações | Desabilitada | Remove palavras ou sons reconhecidos |
| Dicionário/substituições | Desabilitada | Troca palavras |
| Estilo/tom | Desabilitada | Pode reescrever conteúdo |
| Mini-LLM rewriter | Desabilitada | Pode trocar, remover ou acrescentar texto |
| Aprendizado contínuo | Desabilitado no processamento | Pode influenciar reconhecimento futuro |
| Tradução | Usa fluxo próprio | Tradução não pode prometer literalidade lexical |

## Requisitos funcionais

- **RF01:** ativar preservação de palavras deve desabilitar ao vivo todos os
  controles incompatíveis.
- **RF02:** controles desabilitados devem permanecer visíveis e explicar a
  dependência.
- **RF03:** o estado efetivo salvo deve ser normalizado; não basta desabilitar
  visualmente o widget.
- **RF04:** configurações antigas contraditórias devem ser normalizadas ao abrir o
  app, com aviso único e não intrusivo.
- **RF05:** desligar a preservação não deve reativar automaticamente opções que o
  usuário não escolheu naquela sessão.
- **RF06:** o resumo efetivo deve refletir o pipeline realmente executado.
- **RF07:** `Usar configuração mais fiel` deve aplicar a combinação completa em
  uma única ação confirmada.
- **RF08:** modo clássico e streaming devem obedecer à mesma matriz.
- **RF09:** tradução deve mostrar que a promessa de preservação literal não se
  aplica ao resultado traduzido.
- **RF10:** deve existir `Restaurar padrões recomendados` sem apagar dicionários
  ou tons personalizados armazenados.

## Requisitos não funcionais

- Comportamento determinístico e testável sem rede.
- Nenhuma latência adicional de transcrição.
- Configuração persistida de forma atômica.
- Textos de interface compreensíveis sem conhecimento de IA.

## Métricas de sucesso

- Redução de relatos de “o app mudou o que eu falei”.
- Nenhuma combinação incompatível persistida após salvar.
- Correspondência de 100% entre resumo exibido e etapas executadas nos testes.

## Critérios de aceite

1. Ao ativar preservação, repetição, hesitação, dicionário, tom e rewriter ficam
   inativos e deixam de atuar no pipeline.
2. Pontuação permanece disponível, mas sua alteração é descrita explicitamente.
3. A ação mais fiel desativa também pontuação assistida.
4. Reiniciar o app preserva a combinação escolhida e o mesmo resumo.
5. Uma configuração legada contraditória é corrigida sem reativar opções ocultas.
6. Comparando entrada e saída sem sinais de pontuação, a sequência de palavras é
   idêntica no modo de preservação.
7. A suíte existente e novos testes de matriz passam.

## Casos de teste mínimos

- cada combinação da matriz;
- alternância rápida do controle principal;
- salvar, fechar e reabrir;
- configuração legada contraditória;
- clássico, streaming e tradução;
- dicionário e rewriter previamente configurados;
- restauração de padrões sem perda de dados personalizados.

## Fora de escopo

- Melhorar a precisão do modelo Whisper.
- Garantir que o modelo reconheça corretamente toda palavra pronunciada.
- Criar novos estilos ou modelos de reescrita.

## Dependências e rollout

- Implementar em conjunto ou depois do motor de dependências de QS-003.
- Cobrir a normalização com testes antes de habilitar para configurações reais.
- Manter migração reversível: valores personalizados continuam armazenados mesmo
  quando temporariamente incompatíveis.
