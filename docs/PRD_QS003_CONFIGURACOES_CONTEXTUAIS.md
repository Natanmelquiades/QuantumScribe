# PRD QS-003 — Configurações contextuais e dependências entre funções

**Status:** proposta para validação
**Prioridade:** P1 — Alta
**Esforço preliminar:** M
**Relacionado a:** QS-002 — Modo Transcrição Exata

## Contexto

A tela de configurações contém opções principais e dependentes. O Streaming
Contínuo controla chunks, silêncio de corte e Silero VAD; efeitos sonoros controlam
volume; aprimoramento de áudio controla perfil; e o modo literal interfere em
várias transformações de texto.

Atualmente algumas dependências são apenas organizacionais. Por exemplo, o status
do Silero VAD aparece mesmo com streaming desligado, embora o modelo neural só
seja pré-carregado quando streaming está ativo. O modo clássico usa outro filtro
VAD do faster-whisper, hoje sem distinção clara na interface.

## Problema

- Um recurso pode parecer ativo quando não está sendo executado.
- Opções sem efeito continuam editáveis.
- Configurações contraditórias podem ser carregadas de versões anteriores.
- O usuário não consegue distinguir VAD de streaming do filtro de silêncio do
  modo clássico.

## Objetivo

Criar uma fonte única de regras de dependência que controle interface, estado
persistido e comportamento efetivo do app em tempo real.

## Princípios de UX

- Manter controles dependentes visíveis e rebaixados para ensinar sua relação.
- Sempre mostrar um motivo curto, como `Requer Streaming Contínuo`.
- Atualizar a tela imediatamente, sem exigir salvar ou reabrir.
- Nunca usar cor de sucesso para um recurso apenas instalado, mas inativo.
- Diferenciar `Disponível`, `Ativo`, `Inativo` e `Indisponível`.

## Matriz inicial de dependências

| Opção principal | Dependentes | Regra |
| --- | --- | --- |
| Streaming Contínuo | tamanho do chunk, silêncio para corte, Silero/Energy VAD | Inativos quando streaming está desligado |
| Aprimorar áudio | perfil de aprimoramento | Perfil inativo quando aprimoramento está desligado |
| Efeitos sonoros | volume | Volume inativo quando sons estão desligados |
| Remover hesitações | lista personalizada | Lista editável, mas marcada como não aplicada quando remoção está desligada |
| Mini-LLM | modelo, download e estilo | Ações contextuais ao estado do rewriter |
| Quantum Brain | atalhos e opções do Brain | Inativos quando o módulo está desligado |
| Preservar palavras | transformações de texto | Seguir matriz de QS-002 |

## Tratamento de VAD

### Streaming

- Com streaming desligado: mostrar `Inativo — requer Streaming Contínuo`.
- Não inicializar Silero, Torch ou worker de VAD por causa da tela de status.
- Ao ativar streaming: detectar o motor disponível e mostrar `Ativo: Silero` ou
  `Ativo: detecção por energia`.

### Modo clássico

Expor separadamente `Filtrar trechos sem fala no modo clássico`, explicando que
é o filtro interno do faster-whisper e não o Silero do streaming. A decisão de
permitir desligá-lo deve preservar um padrão seguro e alertar sobre ruído,
alucinações e maior tempo de processamento.

## Requisitos funcionais

- **RF01:** manter uma matriz central de dependências, sem regras divergentes
  espalhadas entre páginas.
- **RF02:** recalcular estados dos controles ao vivo após toda alteração relevante.
- **RF03:** validar novamente ao salvar, carregar e migrar configurações.
- **RF04:** impedir execução de recursos cujo controle principal esteja desligado.
- **RF05:** distinguir instalação de ativação nos textos de status.
- **RF06:** não descarregar modelos em uso; mudanças que exigirem reinício devem
  informar isso claramente.
- **RF07:** preservar preferências dependentes enquanto inativas, sem reativá-las
  silenciosamente.
- **RF08:** disponibilizar uma função de diagnóstico que descreva o estado efetivo
  sem expor dados pessoais.
- **RF09:** cobrir todas as páginas atuais numa auditoria de dependências.
- **RF10:** novos controles devem declarar suas dependências na mesma estrutura.

## Requisitos não funcionais

- Atualizações visuais abaixo de 100 ms.
- Nenhum carregamento pesado causado apenas por abrir configurações.
- Regras determinísticas e unitariamente testáveis sem Tkinter real quando
  possível.
- Compatibilidade com configurações existentes.

## Critérios de aceite

1. Com streaming desligado, chunk, silêncio e VAD aparecem inativos e não são
   carregados.
2. Ativar streaming libera os controles imediatamente e mostra o motor efetivo.
3. Desativar sons rebaixa o volume sem perder o valor salvo.
4. Configuração contraditória é normalizada antes de o pipeline usá-la.
5. A interface nunca informa `Silero ativo` apenas porque o pacote está instalado.
6. VAD clássico e VAD de streaming são apresentados como mecanismos diferentes.
7. A matriz de QS-002 funciona igualmente após reinício.
8. Auditoria automatizada cobre todas as dependências declaradas.

## Casos de teste mínimos

- ligar/desligar cada opção principal;
- múltiplas mudanças antes de fechar a tela;
- carregamento de JSON antigo, incompleto e contraditório;
- Silero disponível e indisponível;
- streaming ativo e clássico ativo;
- mudança enquanto uma transcrição está em andamento;
- temas claro e escuro e navegação por teclado.

## Fora de escopo

- Redesenhar toda a arquitetura visual das configurações.
- Instalar dependências automaticamente ao alternar um controle.
- Alterar algoritmos de VAD.

## Riscos e mitigação

- **Perda de preferência:** manter valor armazenado separado do valor efetivo.
- **Regra circular:** validar o grafo de dependências na inicialização/testes.
- **Mudança no meio do job:** aplicar a nova configuração somente ao próximo job
  quando o recurso não puder mudar com segurança.
