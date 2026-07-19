# PRD — Fila de transcrições consecutivas

**Status:** proposta para validação
**Prioridade sugerida:** alta
**Escopo inicial:** modo clássico de gravação

## Contexto

Hoje, depois que uma gravação termina, o Quantum Scribe bloqueia um novo ditado
enquanto o áudio anterior é transcrito e entregue. Isso interrompe o raciocínio
do usuário: se ele lembra de um complemento logo após soltar o atalho, precisa
esperar o processamento terminar para voltar a falar.

No código atual, esse bloqueio é representado principalmente pelo estado único
`processing`. A solução exige separar gravação, transcrição e espera em fila,
pois essas atividades podem coexistir.

## Problema

- O atalho é ignorado durante uma transcrição em andamento.
- Não há confirmação visual de que um novo ditado foi aceito.
- Um único nome de arquivo temporário não comporta vários áudios com segurança.
- Cada ditado pode pertencer a uma janela, modo e configuração diferentes; esses
  dados não podem ser herdados acidentalmente do item anterior.
- Falha ou cancelamento de um item não pode travar nem apagar o restante da fila.

## Objetivo

Permitir que o usuário grave novos ditados enquanto outro está sendo transcrito.
Os novos áudios devem entrar em uma fila FIFO, ser processados um por vez e
preservar individualmente seu destino e modo de entrega.

## Experiência recomendada

Usar um **HUD único com indicador compacto de fila**, complementado por uma
confirmação temporária quando um item for adicionado.

### Durante a transcrição, sem nova gravação

- Título: `Transcrevendo…`
- Progresso do item atual permanece visível.
- Indicador à direita ou no subtítulo: `Fila: 2`.
- Se não houver itens esperando, o indicador pode ficar oculto.

### Ao iniciar uma gravação enquanto outra transcreve

- O HUD muda para o estado prioritário `Ouvindo…`.
- Subtítulo: `1 processando • 2 na fila`.
- A transcrição anterior continua em segundo plano e não perde seu progresso.
- O som e a animação de início permanecem iguais aos da gravação normal.

### Ao finalizar essa nova gravação

- Mostrar por aproximadamente 1,5 segundo:
  - título: `Adicionado à fila`;
  - subtítulo: `Posição 3 • 8 s de áudio`;
  - representação visual: três pequenos pontos ou cartões, com o primeiro em
    animação e os demais sólidos.
- Tocar um som curto de confirmação diferente do som de transcrição concluída.
- Em seguida, voltar a mostrar o item em processamento e o contador da fila.

### Quando a fila atingir o limite

- Limite recomendado: **3 itens aguardando**, sem contar o item que já está em
  processamento.
- Não iniciar outra captura quando já existirem 3 itens aguardando.
- Mostrar `Fila cheia — aguarde um item terminar` por cerca de 2 segundos.
- Tocar um aviso discreto; nunca ignorar o atalho silenciosamente.

O limite deve ser configurável internamente, mas não precisa aparecer nas
configurações no MVP. Três itens é um equilíbrio entre fluxo rápido, uso de disco
e risco de o usuário perder a noção de onde cada texto será inserido.

## Alternativas de apresentação consideradas

| Alternativa | Vantagem | Desvantagem | Decisão |
| --- | --- | --- | --- |
| HUD único + contador + confirmação | Compacto e coerente com a interface atual | Não mostra detalhes de todos os itens | **Recomendada para o MVP** |
| Pilha vertical de minicartões | Torna cada item e estado explícitos | Ocupa tela e pode cobrir o conteúdo | Considerar numa versão avançada |
| Som e toast apenas | Implementação visual simples | A fila fica invisível depois do toast | Não usar isoladamente |
| Indicador somente na bandeja | Não interrompe o trabalho | Fácil de não perceber | Usar apenas como complemento futuro |

## Modelo de estados

Cada item deve atravessar os estados:

`gravando → aguardando → transcrevendo → entregando → concluído`

Também são terminais:

`cancelado` e `falhou`.

O aplicativo, por sua vez, pode ter simultaneamente:

- zero ou uma gravação ativa;
- zero ou uma transcrição ativa;
- de zero a três itens aguardando.

Gravação e transcrição podem ocorrer ao mesmo tempo. Duas transcrições nunca
devem rodar simultaneamente no MVP, evitando concorrência no modelo e disputa de
CPU, GPU e memória.

## Dados obrigatórios de cada item

Cada `TranscriptionJob` deve ser imutável depois de enfileirado e conter:

- identificador único;
- caminho WAV exclusivo;
- duração;
- instante de criação;
- janela de destino capturada no início daquela gravação;
- modo normal, tradução, autoenvio ou Quantum Brain;
- snapshot das opções que alteram transcrição e pós-processamento;
- número de tentativas e estado atual.

O destino e o modo nunca devem ser lidos de variáveis globais mutáveis quando o
item chegar à frente da fila.

## Requisitos funcionais

- **RF01:** aceitar uma nova gravação enquanto outra transcrição está ativa.
- **RF02:** processar os itens em ordem FIFO com apenas um worker de transcrição.
- **RF03:** exibir a quantidade aguardando durante gravação e processamento.
- **RF04:** confirmar visual e sonoramente a entrada de cada item na fila.
- **RF05:** limitar a fila a 3 itens aguardando e informar quando estiver cheia.
- **RF06:** capturar e preservar destino, modo e opções por item.
- **RF07:** criar um arquivo temporário exclusivo por gravação.
- **RF08:** remover o WAV somente depois de conclusão, cancelamento explícito ou
  descarte confirmado.
- **RF09:** se um item falhar, informar a falha e iniciar o próximo
  automaticamente.
- **RF10:** se a janela de destino não existir mais, copiar o resultado para a
  área de transferência e avisar, sem descartar o texto.
- **RF11:** a conclusão do item anterior durante uma nova gravação não pode
  interromper, ocultar nem cancelar o HUD da gravação atual.
- **RF12:** o modo autoenvio deve pressionar Enter somente na janela pertencente
  àquele item e apenas após inserção bem-sucedida.
- **RF13:** o diário deve receber exatamente uma entrada por item concluído.
- **RF14:** ao cancelar a gravação atual, preservar a transcrição ativa e os itens
  já aguardando.
- **RF15:** ao cancelar a transcrição ativa, avançar para o próximo item da fila.

## Persistência e recuperação

Para minimizar perda de ditados, usar uma pasta local de spool, por exemplo
`%LOCALAPPDATA%\QuantumScribe\transcription_queue\`, com um WAV e um pequeno
arquivo de metadados por item.

- Gravar o WAV e os metadados de forma atômica antes de confirmar `Adicionado à
  fila`.
- Remover ambos somente após entrega ou cancelamento explícito.
- Em encerramento inesperado, detectar itens remanescentes na próxima abertura e
  recolocá-los na fila.
- Dados continuam locais e seguem as mesmas regras de privacidade das demais
  transcrições.

No primeiro lançamento, a recuperação pode ser automática com a mensagem
`Recuperando 2 ditados pendentes…`.

## Regras de cancelamento

- `Esc` durante uma gravação cancela somente a gravação em primeiro plano.
- `Esc` quando não há gravação, mas há transcrição, cancela somente o item ativo.
- Cancelar um item ativo não limpa a fila.
- Uma ação futura `Limpar fila` pode existir no menu da bandeja, com confirmação;
  ela fica fora do MVP.

## Concorrência e segurança técnica

- Manter uma fila protegida por lock e um único consumidor.
- Toda atualização de Tkinter deve continuar passando pela thread principal.
- O worker deve obter o próximo item numa operação atômica.
- A sinalização de cancelamento deve pertencer ao job ativo; não pode permanecer
  acionada e cancelar o job seguinte.
- Eventos atrasados do HUD devem carregar o ID do job e ser ignorados quando já
  não corresponderem ao estado visual atual.
- Sons de conclusão e chamadas para ocultar o HUD não podem sobrepor o estado
  `Ouvindo…` de uma gravação simultânea.
- O encerramento do app deve parar novas capturas, finalizar gravações de arquivo
  em curso e preservar no spool os jobs ainda não entregues.

## Requisitos não funcionais

- Nenhum congelamento adicional da interface.
- Sobrecarga desprezível durante a captação de áudio.
- Consumo de memória limitado: os itens aguardam como arquivos, não como arrays
  completos de áudio em RAM.
- Operação totalmente local e offline.
- Logs técnicos devem usar IDs, estados e durações, nunca o texto transcrito.
- Comportamento determinístico e coberto por testes de concorrência e estados.

## Critérios de aceite

1. Iniciar um ditado B enquanto A transcreve grava B imediatamente.
2. Ao encerrar B, o HUD confirma sua posição e A continua processando.
3. B só começa a transcrever depois que A termina ou é cancelado.
4. A e B são inseridos nas respectivas janelas capturadas, na ordem correta.
5. Com 3 itens aguardando, uma nova tentativa é recusada com aviso visível e som.
6. Três WAVs consecutivos possuem caminhos distintos e nenhum sobrescreve outro.
7. Falha em A não remove B nem C; B passa a ser processado.
8. Cancelar uma gravação simultânea não cancela a transcrição ativa.
9. O término de A enquanto B está sendo gravado não fecha nem altera o HUD de B.
10. Se a janela de um item foi fechada, seu texto permanece disponível no
    clipboard e o usuário recebe aviso.
11. Após encerramento inesperado, os itens persistidos são recuperados.
12. Toda a suíte existente continua passando.

## Casos de teste mínimos

- fila vazia, um item e limite cheio;
- enfileiramento enquanto o modelo ainda está carregando;
- item atual termina durante uma nova gravação;
- cancelamento da gravação, do item ativo e do app;
- erro de microfone, erro de transcrição e janela de destino inválida;
- mistura de normal, tradução e autoenvio na mesma fila;
- alterações de configuração enquanto existem itens pendentes;
- recuperação de spool válido, incompleto e corrompido;
- disparos rápidos/repetidos do atalho;
- garantia de uma única entrega e uma única entrada no diário por job.

## Fora de escopo do MVP

- Transcrever dois áudios em paralelo.
- Reordenar itens manualmente.
- Editar ou reproduzir o áudio da fila.
- Uma janela completa de gerenciamento da fila.
- Aplicar a fila ao modo Streaming Contínuo; esse modo já possui ciclo próprio e
  deve manter o comportamento atual até uma especificação dedicada.

## Fases sugeridas

1. **Núcleo seguro:** modelo `TranscriptionJob`, arquivos únicos, fila FIFO,
   worker único e testes de estado.
2. **UX:** contador no HUD, confirmação de posição, fila cheia e sons.
3. **Resiliência:** spool persistente, recuperação após reinício e testes de
   falhas.
4. **Evolução opcional:** minicartões, ações na bandeja e gerenciamento da fila.
