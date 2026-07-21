# PRD QS-017 — Estabilidade do HUD, cancelamento e inicialização

**Status:** proposta de correção baseada em auditoria de código  
**Prioridade:** P1 — Alta  
**Esforço preliminar:** M  
**Relacionado a:** QS-004, QS-007 e QS-016

## Contexto e impacto

O fluxo principal depende de sinais visuais curtos: o usuário precisa ver que o
app iniciou, que a gravação está ativa e que um cancelamento foi ou não aceito.
Relatos recentes indicam que esses sinais são intermitentes: o ícone/HUD demora
para surgir ou desaparece, e o aro do `Esc` some antes de ser possível confirmar
visualmente o resultado.

Como o cancelamento descarta áudio ainda não transcrito, a ambiguidade é um risco
direto de perda de trabalho percebida pelo usuário.

## Evidências da auditoria

### Confirmadas no código

1. `Popup.show_recording`, `show_processing_with_progress`, `show_loading_model`
   e `show_message` podem chamar `_animate()` repetidamente. Cada chamada agenda
   outro `root.after`, mas não há identificador de animação nem cancelamento de
   callbacks anteriores. Mais de um loop pode atualizar e ocultar o mesmo HUD.
2. O app agenda `popup.hide` após sucesso, erro e outras mensagens sem associar o
   callback à sessão que o criou. Um callback antigo pode atingir uma sessão que
   já voltou a gravar.
3. Ao atingir o limite de `Esc`, `_confirm_cancel_hold` limpa o aro e chama
   `cancel_recording` imediatamente. O próximo frame de animação nunca é
   obrigado a desenhar 100%, portanto a confirmação pode parecer interrompida.
4. A inicialização registra quatro hotkeys globais de forma síncrona. Cada uma
   espera até 3 s por prontidão. Se o Windows atrasar o registro, a percepção de
   início pode chegar a múltiplos segundos antes de a bandeja estar pronta.
5. A bandeja cria um ícone de barras por conta própria, em vez de reutilizar o
   asset oficial usado pelas janelas. Isso amplia o risco de superfícies visuais
   divergentes e dificulta diagnosticar qual ícone desapareceu.

### Hipóteses a reproduzir no Windows

- `pystray` pode demorar a sinalizar a criação real do ícone mesmo depois de sua
  thread iniciar;
- uma falha de `RegisterHotKey` para `Esc` não é hoje comunicada ao usuário;
- cache de ícones do Windows pode contribuir para ícone ausente/desatualizado,
  mas não é necessário para explicar o sumiço do HUD.

## Objetivo

Garantir que cada transição visual tenha uma sessão identificável e que somente
o callback atual possa alterar seu HUD. O cancelamento por `Esc` deve chegar ao
limite sem retenção adicional e ocultar o HUD imediatamente. A bandeja deve
ter prontidão observável e usar o asset oficial.

## Solução proposta

### 1. Controlador de sessão visual

Criar um controlador único no `Popup` com um contador monotônico de geração.
Toda chamada que exibe, atualiza, explode ou oculta o HUD recebe/captura a geração
atual. Callbacks `after` verificam a geração antes de executar; callbacks antigos
se tornam no-ops.

- Manter no máximo um loop de animação ativo por geração.
- Armazenar e cancelar IDs de `after` quando a geração for encerrada, quando
  possível; a validação de geração continua obrigatória como proteção extra.
- Centralizar as transições em estados explícitos: `idle`, `recording`,
  `confirming_cancel`, `cancelled`, `loading`, `transcribing`, `success` e
  `error`.
- `hide` somente pode encerrar a geração que o solicitou. Não deve limpar uma
  gravação em curso ou uma nova mensagem.

### 2. Confirmação de cancelamento verificável

- Ao pressionar `Esc`, iniciar `confirming_cancel` para a sessão de gravação
  atual e desenhar o aro vermelho usando relógio monotônico.
- Ao atingir 100% em 0,5 segundo, cancelar a gravação, tocar o som e ocultar o
  HUD no mesmo callback, liberando imediatamente um novo ditado.
- Ao soltar antes do limite, retornar a `recording` e remover o aro; não cancelar
  áudio, não pausar a captura e não reiniciar a animação.
- Exibir uma confirmação breve de cancelamento quando o tema permitir; para o
  HUD minimalista, a permanência do aro completo é o feedback obrigatório.
- O token de gravação deve ser propagado pelos callbacks da hotkey e validado
  novamente antes de cancelar.

### 3. Inicialização e bandeja observáveis

- Iniciar a bandeja antes de tarefas opcionais e esperar uma confirmação curta de
  prontidão do backend antes de declarar o app disponível.
- Não bloquear a construção da interface pela soma dos timeouts de hotkeys;
  registrar em paralelo ou usar um timeout total limitado, mantendo diagnóstico
  individual por atalho.
- Exibir status não intrusivo na bandeja: `Iniciando…`, `Pronto para ditar` ou
  `Atalho indisponível` com ação de abrir configurações.
- Reutilizar um único asset oficial para bandeja, janelas e empacotamento;
  manter fallback local apenas se o asset não puder ser carregado.
- Registrar no log técnico tempos de início da bandeja, hotkeys e HUD, sem texto
  ditado nem dados pessoais.

## Plano de implementação

1. **Instrumentar e reproduzir:** adicionar log estruturado de geração, estado,
   origem da transição e atraso de inicialização; criar testes unitários do
   controlador de geração com scheduler falso.
2. **Estabilizar o Popup:** introduzir o controlador de sessão, garantir uma única
   animação e converter todos os `after` de animação/ocultação para callbacks
   protegidos por geração.
3. **Corrigir o `Esc`:** usar limite de 0,5 segundo, cancelar no instante em que
   o aro chega ao fim e testar toque curto, hold completo, soltar no limite e
   sessão seguinte.
4. **Corrigir início e bandeja:** criar sinal de prontidão, reduzir espera
   bloqueante dos hotkeys e unificar o asset de ícone.
5. **Validar no pacote Windows:** testar instalação limpa, atualização, inicialização
   repetida, conflito de atalho, hibernação/retorno e 100 ciclos rápidos de
   gravação/finalização/cancelamento.

## Critérios de aceite

1. Após 100 ciclos rápidos de mostrar/ocultar/transcrever/gravar, o HUD ativo
   permanece visível e coerente; nenhum callback de uma geração anterior o fecha.
2. Pressionar e soltar `Esc` antes do limite preserva a gravação e remove o aro.
3. Manter `Esc` por 0,5 segundo cancela exatamente uma vez no término do aro;
   o HUD some e uma nova gravação pode começar sem atraso adicional.
4. Uma confirmação de `Esc` anterior nunca cancela nem esconde uma nova gravação.
5. Em inicialização normal, a bandeja informa prontidão sem aguardar tarefas de
   modelo; atrasos ou conflitos de hotkey são diagnosticáveis e visíveis.
6. Bandeja, janela e executável usam o mesmo asset oficial ou informam fallback
   explícito em log.
7. A suíte automatizada, os novos testes de estado e o smoke test do executável
   Windows passam.

## Fora de escopo

- Reprojetar a fila de transcrições (QS-001).
- Alterar o comportamento de entrega de texto (QS-014).
- Tratar cache de ícones do Windows como única causa sem reproduzir a falha de
  runtime.

## Riscos e mitigação

| Risco | Mitigação |
| --- | --- |
| Cancelar timers válidos e deixar o HUD preso | geração + transição explícita + testes de cada estado |
| Atrasar demais o cancelamento | limite de 0,5 s; sem retenção após o aro completar |
| Hotkey indisponível silenciosamente | sinal de erro e ação de configuração |
| Alterar bandeja em Windows com cache antigo | asset único e verificação em instalação limpa/atualização |
