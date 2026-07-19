# PRD QS-011 — Pesquisa textual unificada em transcrições

**Status:** proposta para validação
**Prioridade:** P1 — Alta
**Esforço preliminar:** M
**Relacionado a:** QS-010 — Histórico moderno; QS-012 — Pesquisa semântica

## Contexto

As transcrições são salvas localmente em arquivos Markdown diários. Cada entrada
possui horário e texto, mas a tela atual lista apenas os arquivos e os abre no
aplicativo associado. Para encontrar algo antigo, o usuário precisa pesquisar
arquivo por arquivo.

## Problema

- Não há busca global por palavra ou frase.
- O usuário pode lembrar o conteúdo, mas não a data.
- Históricos grandes tornam a consulta manual impraticável.
- A futura busca semântica não pode ser requisito para computadores simples.

## Objetivo

Oferecer pesquisa textual rápida, totalmente local e disponível em qualquer
computador suportado, sem alterar nem migrar destrutivamente os Markdown.

## Escopo do MVP

- busca por uma ou mais palavras;
- busca por frase exata;
- normalização de maiúsculas/minúsculas e opção tolerante a acentos;
- filtros de data;
- resultados com data, hora, trecho e termo destacado;
- ação de copiar e abrir o arquivo de origem.

## Experiência proposta

Adicionar um campo `Pesquisar em todas as transcrições` no histórico. A busca
começa após pequeno debounce ou Enter. Cada resultado mostra:

- data e hora;
- trecho com contexto antes/depois;
- termos destacados;
- arquivo de origem;
- ações `Copiar`, `Abrir` e, quando QS-010 existir, `Ver no histórico`.

Estados necessários: inicial, buscando, resultados, nenhum resultado, índice
desatualizado e erro recuperável.

## Modelo de dados e indexação

- Markdown continua sendo a fonte de verdade.
- Um índice local derivado pode ser reconstruído a qualquer momento.
- Cada registro indexado deve conter ID estável, data, hora, texto, arquivo,
  posição aproximada e fingerprint da origem.
- A implementação pode usar SQLite/FTS local ou estrutura equivalente, desde que
  não exija serviço, rede ou modelo de IA.
- Arquivos criados, alterados ou removidos fora do app devem ser reconciliados.

## Regras de busca

- Padrão: todas as palavras, independente de caixa.
- Frase entre aspas ou modo explícito: correspondência da sequência exata.
- Alternância `Ignorar acentos`, ligada por padrão em português.
- Ordenação padrão por relevância, com opção de mais recentes.
- Filtros `Hoje`, `7 dias`, `30 dias` e intervalo personalizado.
- Limitar e paginar resultados para não bloquear a interface.

## Requisitos funcionais

- **RF01:** indexar todos os arquivos diários existentes sem alterar seu conteúdo.
- **RF02:** atualizar o índice após cada `save_entry`.
- **RF03:** detectar mudanças externas por fingerprint/mtime e reconciliar.
- **RF04:** permitir reconstruir ou apagar apenas o índice.
- **RF05:** destacar correspondências sem perder o texto original.
- **RF06:** abrir o arquivo e identificar a entrada quando tecnicamente possível.
- **RF07:** copiar somente a transcrição escolhida.
- **RF08:** funcionar com índice ausente ou corrompido, reconstruindo-o de forma
  segura.
- **RF09:** não incluir o log comparativo de debug por padrão.
- **RF10:** fornecer uma API local reutilizável por QS-012.

## Requisitos não funcionais

- Operação 100% offline.
- Nenhum conteúdo em logs técnicos.
- Busca percebida abaixo de 300 ms após índice pronto em um histórico de referência
  de 50 mil entradas.
- Indexação incremental sem congelar Tkinter.
- Índice gravado atomicamente e descartável.
- Consumo de disco proporcional e informado ao usuário.

## Privacidade e segurança

- Índice armazenado dentro do diretório de dados do Quantum Scribe.
- Mesmas permissões locais do histórico.
- Exclusão do histórico deve remover registros correspondentes do índice.
- Backups devem declarar se incluem ou não o índice; preferência é reconstruí-lo.

## Critérios de aceite

1. Palavra existente em qualquer dia retorna a entrada correta numa única busca.
2. Frase exata não retorna entradas com palavras em ordem diferente.
3. Busca tolerante a acentos encontra `transcrição` ao consultar `transcricao`.
4. Resultados exibem data, hora, contexto e origem.
5. Nova transcrição aparece sem reconstrução completa.
6. Alterar ou excluir um Markdown externamente é refletido após reconciliação.
7. Índice corrompido é reconstruído sem perder transcrições.
8. Histórico de referência atende à meta de latência e não congela a UI.
9. Busca funciona sem GPU, modelo Whisper carregado, embeddings ou internet.

## Casos de teste mínimos

- arquivo vazio, um dia e vários anos;
- caracteres acentuados, emojis, pontuação e quebras de linha;
- frase exata e múltiplas palavras;
- filtros de data e ordenação;
- arquivos externos alterados, removidos e malformados;
- índice ausente, antigo e corrompido;
- gravação concorrente enquanto uma busca está ativa;
- exclusão de todo o histórico.

## Fora de escopo

- Busca por significado, embeddings ou LLM; pertence a QS-012.
- Sincronização cloud; pertence a QS-013.
- Migração obrigatória dos Markdown para banco de dados.

## Rollout

- Construir primeiro parser e índice com testes sobre cópias temporárias.
- Liberar busca textual antes da pesquisa semântica.
- Manter abertura dos Markdown como fallback enquanto QS-010 não for entregue.
