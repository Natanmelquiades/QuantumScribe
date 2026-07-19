# PRD QS-004 — Ícone central do HUD em transições rápidas

**Status:** proposta para validação
**Prioridade:** P1 — Alta
**Esforço preliminar:** M
**Tipo:** correção de bug
**Relacionado a:** QS-001 — Fila de transcrições consecutivas

## Contexto

O HUD alterna entre gravação, carregamento, transcrição, sucesso, erro e oculto.
Essas mudanças usam callbacks agendados do Tkinter e animações que também podem
chamar `hide()`. Em ciclos muito rápidos, o usuário observa ocasionalmente o
ícone central desaparecer, deixando dúvida sobre o estado do app.

A causa ainda deve ser confirmada. A principal hipótese é que um callback ou
frame de animação pertencente à sessão anterior altera ou oculta a sessão nova.

## Problema

- O feedback visual pode desaparecer enquanto o app ainda trabalha.
- O defeito é intermitente e mais provável ao finalizar e reiniciar rapidamente.
- Estados e callbacks não possuem hoje um identificador explícito de sessão.

## Objetivo

Garantir que apenas eventos pertencentes à sessão visual ativa possam atualizar
ou ocultar o HUD.

## Modelo de estado proposto

Estados válidos:

`oculto → gravando → carregando → transcrevendo → sucesso/erro → oculto`

Cada nova exibição recebe uma `hud_generation` monotônica. Callbacks, animações e
fechamentos agendados capturam essa geração e são ignorados se ela já não for a
atual.

## Requisitos funcionais

- **RF01:** toda nova gravação ou sessão de processamento deve iniciar uma nova
  geração visual.
- **RF02:** `hide`, conclusão, erro e frames de animação devem validar a geração.
- **RF03:** callbacks agendados conhecidos devem ser cancelados ao mudar de
  geração, além da validação defensiva.
- **RF04:** iniciar gravação deve restaurar explicitamente geometria, opacidade,
  elementos visíveis, indicadores, escala e flags do tema.
- **RF05:** cada tema suportado deve definir seu conjunto completo de elementos
  visíveis por estado.
- **RF06:** uma conclusão antiga não pode tocar animação final sobre uma gravação
  nova.
- **RF07:** o HUD deve continuar `WS_EX_NOACTIVATE` e não roubar foco.
- **RF08:** QS-001 deve reutilizar o mesmo mecanismo por ID de job/sessão.
- **RF09:** logs de diagnóstico devem registrar geração e transição, sem texto
  transcrito.

## Requisitos não funcionais

- Nenhum timer bloqueante na thread de UI.
- Animação fluida no mesmo patamar atual.
- Correção determinística, sem aumentar atrasos artificiais entre ditados.
- Ausência de crescimento de callbacks pendentes ao longo do uso.

## Critérios de aceite

1. Cinquenta ciclos automatizados de finalizar/iniciar com intervalos curtos não
   ocultam o ícone da sessão ativa.
2. Um `hide` atrasado da geração N não afeta a geração N+1.
3. Todos os temas restauram seus elementos após sucesso, erro e cancelamento.
4. O término da transcrição anterior durante uma nova gravação não altera o HUD
   da gravação.
5. A janela mantém opacidade e tamanho corretos depois de animação de explosão.
6. Não há callbacks crescentes ou exceções do Tkinter no teste de estresse.
7. A suíte existente continua passando.

## Plano de reprodução e testes

- Instrumentar temporariamente transições com geração e timestamp.
- Simular conclusão seguida de novo início em 0, 25, 50, 100 e 250 ms.
- Cobrir gravação, transcrição, sucesso, erro, cancelamento e carregamento.
- Repetir em todos os temas do HUD.
- Testar com sons ligados/desligados e modelo carregado/não carregado.
- Validar manualmente em múltiplas escalas de DPI.

## Fora de escopo

- Redesenhar a aparência do HUD.
- Implementar a fila completa QS-001.
- Alterar o mecanismo de transcrição.

## Rollout e rollback

- Entregar inicialmente com logs de transição em nível de debug.
- Manter a API pública atual do `Popup` durante a primeira correção.
- Se houver regressão, permitir desativar a proteção nova sem remover os testes de
  reprodução, até corrigir o estado incompatível.
