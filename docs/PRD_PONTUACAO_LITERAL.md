# PRD — Pontuação Inteligente com Preservação Literal

## Contexto

O modo literal da versão 2.1.20 eliminou reescritas de palavras, mas expôs
limitações de pontuação do Whisper em ditados coloquiais e longos. O histórico
real apresenta perguntas sem `?` e pausas de frase representadas apenas por uma
nova palavra com inicial maiúscula.

## Problema

1. Perguntas coloquiais como “tem como corrigir isso” podem terminar sem `?`.
2. Pausas perceptíveis entre segmentos são descartadas quando os textos do
   Whisper são concatenados com um espaço simples.
3. Não é aceitável usar uma LLM que possa trocar, remover ou inventar palavras.

## Objetivo

Melhorar a legibilidade do português adicionando somente sinais de pontuação,
sem modificar a sequência de palavras reconhecida pelo Whisper.

## Requisitos funcionais

- RF01: preservar integralmente as palavras e sua ordem.
- RF02: usar os timestamps dos segmentos para inserir ponto em pausas longas.
- RF03: reconhecer construções interrogativas conservadoras do português e
  adicionar ou corrigir o ponto de interrogação final.
- RF04: nunca transformar frases que já terminam em `?`, `!` ou reticências.
- RF05: funcionar nos modos clássico e streaming.
- RF06: permitir desligar a assistência de pontuação nas configurações.
- RF07: não utilizar rede, LLM ou dependências adicionais.

## Requisitos não funcionais

- Latência desprezível, baseada apenas em regex e timestamps já disponíveis.
- Comportamento determinístico e coberto por testes automatizados.
- Falha segura: se não houver confiança, manter a pontuação original.

## Critérios de aceite

- “Tem como corrigir isso.” resulta em “Tem como corrigir isso?”.
- “Eu estou indo dormir” seguido de pausa longa e “Então...” recebe um ponto
  entre os segmentos.
- As palavras antes e depois do processamento permanecem idênticas quando os
  sinais de pontuação são removidos para comparação.
- Perguntas já corretas permanecem inalteradas.
- Toda a suíte de testes passa.

## Fora de escopo

- Correção gramatical, substituição de palavras ou reescrita estilística.
- Inferência emocional de exclamações.
- Promessa de reconstrução perfeita da prosódia sem acesso a um modelo dedicado.
