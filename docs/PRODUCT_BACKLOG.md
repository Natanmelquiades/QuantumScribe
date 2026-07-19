# Product Backlog — Quantum Scribe

Este é o inventário central de futuras features, melhorias, correções e débitos
técnicos do produto. Novas ideias podem entrar inicialmente na Caixa de Entrada,
mesmo sem prioridade ou especificação completa. Durante o refinamento, cada item
é classificado e preparado para desenvolvimento.

## Como usar

1. Registrar rapidamente qualquer ideia nova na **Caixa de Entrada**.
2. Refinar o item: esclarecer problema, resultado esperado e critérios de aceite.
3. Classificar prioridade, tipo, esforço e dependências.
4. Mover para **Pronto para priorização** quando houver informação suficiente.
5. Selecionar os próximos itens e movê-los para **Planejado**.
6. Atualizar o status durante o desenvolvimento até **Concluído**.

## Convenções

### Status

- `Ideia`: captura inicial, ainda não refinada.
- `Em refinamento`: sendo detalhada ou validada.
- `Pronto`: especificação suficiente para priorização.
- `Planejado`: selecionado para um próximo ciclo.
- `Em desenvolvimento`: implementação iniciada.
- `Bloqueado`: depende de decisão ou trabalho externo.
- `Concluído`: entregue e validado.
- `Descartado`: não será desenvolvido no momento.

### Prioridade

- `P0 — Crítica`: falha grave, perda de dados ou produto inutilizável.
- `P1 — Alta`: impacto frequente e relevante no fluxo principal.
- `P2 — Média`: melhoria importante, mas existe alternativa temporária.
- `P3 — Baixa`: conveniência, polimento ou oportunidade futura.
- `A definir`: ainda precisa passar pela triagem.

### Tipo

- `Feature`: nova capacidade para o usuário.
- `Melhoria`: evolução de algo que já existe.
- `Bug`: comportamento incorreto.
- `Débito técnico`: trabalho interno de qualidade ou manutenção.
- `Pesquisa`: descoberta necessária antes de decidir uma solução.

### Esforço preliminar

- `P`: pequeno.
- `M`: médio.
- `G`: grande.
- `A definir`: ainda não estimado.

## Visão geral

| ID | Item | Tipo | Status | Prioridade | Esforço | PRD |
| --- | --- | --- | --- | --- | --- | --- |
| QS-001 | Fila de transcrições consecutivas | Feature | Em refinamento | P1 — Alta | G | [Abrir PRD](PRD_FILA_TRANSCRICOES.md) |
| QS-002 | Modo Transcrição Exata e simplificação dos ajustes de texto | Melhoria | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS002_TRANSCRICAO_EXATA.md) |
| QS-003 | Configurações contextuais e dependências entre funções | Melhoria | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS003_CONFIGURACOES_CONTEXTUAIS.md) |
| QS-004 | Ícone central do HUD desaparece em transições rápidas | Bug | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS004_HUD_ICONE_TRANSICOES.md) |
| QS-005 | Detectar e reutilizar modelos Whisper compatíveis existentes | Feature | Em refinamento | P2 — Média | G | A criar |
| QS-006 | Download resiliente do modelo com retomada e fallback | Melhoria | Em refinamento | P1 — Alta | G | [Abrir PRD](PRD_QS006_DOWNLOAD_MODELO_RESILIENTE.md) |
| QS-007 | Unificar e atualizar o ícone oficial em todas as superfícies | Bug | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS007_ICONES_OFICIAIS.md) |
| QS-008 | Sincronizar a cor personalizada com os ícones do aplicativo | Melhoria | Em refinamento | P3 — Baixa | M | A criar |
| QS-009 | Modernizar o controle de volume dos efeitos | Melhoria | Em refinamento | P2 — Média | P | A criar |
| QS-010 | Redesenhar o histórico de transcrições como tabela moderna | Melhoria | Em refinamento | P2 — Média | M | A criar |
| QS-011 | Pesquisa textual unificada em todas as transcrições | Feature | Em refinamento | P1 — Alta | M | [Abrir PRD](PRD_QS011_PESQUISA_TRANSCRICOES.md) |
| QS-012 | Pesquisa semântica local e adaptativa no histórico | Feature | Em refinamento | P2 — Média | G | A criar |
| QS-013 | Modo cloud/API opcional para computadores fracos | Pesquisa | Em refinamento | P2 — Média | G | A criar |
| QS-014 | Controle de destino e mudança de foco ao entregar transcrições | Melhoria | Em refinamento | P2 — Média | M | A criar |

## Caixa de Entrada

Adicione ideias novas aqui sem se preocupar inicialmente com a solução.

<!-- Modelo rápido:
- **Título:**
  - Problema ou oportunidade:
  - Resultado desejado:
  - Contexto ou exemplo:
-->

_Nenhum item aguardando triagem._

## Em refinamento

### QS-001 — Fila de transcrições consecutivas

- **Tipo:** Feature
- **Prioridade preliminar:** P1 — Alta
- **Esforço preliminar:** G
- **Problema:** o usuário precisa esperar a transcrição atual terminar antes de
  começar outro ditado.
- **Resultado desejado:** permitir novas gravações enquanto um item é processado,
  mantendo uma fila visível, segura e limitada.
- **Próxima decisão:** validar a apresentação recomendada do HUD e confirmar o
  limite de três itens aguardando.
- **Especificação:** [PRD — Fila de transcrições consecutivas](PRD_FILA_TRANSCRICOES.md)

### QS-002 — Modo Transcrição Exata e simplificação dos ajustes de texto

- **Tipo:** Melhoria de experiência e previsibilidade.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Problema:** combinações de opções como modo literal, assistência de
  pontuação, remoção de repetições, remoção de hesitações, dicionário e reescrita
  podem fazer a saída variar sem deixar evidente quais etapas modificaram o
  texto reconhecido.
- **Resultado desejado:** oferecer uma ação simples e inequívoca para transcrever
  com a menor modificação possível e mostrar claramente quando algum
  pós-processamento estiver ativo.
- **Solução inicial a avaliar:** preset ou botão `Transcrição Exata`, que desative
  de uma vez todas as transformações de palavras e mantenha somente proteções
  técnicas indispensáveis. Exibir um resumo como `Sem alterações de texto` ou
  `2 ajustes podem modificar a transcrição`.
- **Regras preliminares:**
  - explicar em linguagem simples o efeito de cada opção;
  - impedir combinações contraditórias ou avisar sobre elas;
  - permitir restaurar os padrões seguros com um clique;
  - diferenciar pontuação conservadora de alterações de palavras;
  - indicar no HUD ou nas configurações o perfil efetivamente ativo;
  - preservar uma configuração escolhida entre reinicializações;
  - ao ativar `Transcrição Literal`, tratá-la como opção principal e desabilitar
    automaticamente todas as transformações incompatíveis, como reescrita por
    LLM, estilo/tom, remoção de repetições, remoção de hesitações, aprendizado e
    substituições automáticas que alterem palavras;
  - definir explicitamente se assistência de pontuação é compatível com o modo
    literal ou se deverá ser desligada para cumprir a promessa mais estrita;
  - atualizar os controles dependentes ao vivo, antes de salvar, mostrando por
    que ficaram inativos;
  - ao desligar o modo literal, não reativar silenciosamente transformações que
    o usuário não escolheu.
- **Próxima decisão:** definir se `Transcrição Exata` será um preset, um modo
  permanente ou o padrão inicial para novos usuários, além de aprovar uma matriz
  única de compatibilidade entre todas as opções de texto.
- **Especificação:** [PRD QS-002 — Modo Transcrição Exata](PRD_QS002_TRANSCRICAO_EXATA.md)

### QS-003 — Configurações contextuais e dependências entre funções

- **Tipo:** Melhoria de interface, desempenho e transparência.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-002.
- **Problema:** a tela mostra Silero VAD e controles de silêncio mesmo quando o
  Streaming Contínuo está desligado, dando a impressão de que continuam ativos.
  Além disso, o modo clássico possui um filtro VAD interno do faster-whisper que
  não está claramente diferenciado nem possui controle visível.
- **Constatação atual:** o Silero VAD é inicializado apenas quando o streaming é
  ativado, mas seu status aparece sempre na interface. O VAD do modo clássico é
  um mecanismo separado.
- **Resultado desejado:** mostrar, habilitar e carregar apenas opções aplicáveis
  ao modo atual, sem esconder filtros que ainda alterem o processamento. A mesma
  regra deve valer para toda a tela de configurações, não somente para VAD.
- **Regras preliminares:**
  - com Streaming Contínuo desligado, rebaixar visualmente ou recolher Silero VAD,
    tempo de chunk e silêncio para corte;
  - exibir o estado `Inativo — requer Streaming Contínuo`, em vez de um selo que
    pareça confirmar uso ativo;
  - não carregar modelo ou recursos do Silero enquanto o streaming estiver
    desligado;
  - ao ativar streaming, liberar os controles dependentes imediatamente;
  - nomear e explicar separadamente o filtro VAD clássico do faster-whisper;
  - avaliar um controle seguro para o VAD clássico, incluindo aviso sobre ruído,
    silêncio e possíveis cortes de fala;
  - garantir que instalações novas não ativem nem carreguem recursos opcionais
    que o usuário nunca habilitou;
  - auditar todos os controles e criar uma matriz `opção principal → opções
    dependentes → opções incompatíveis`;
  - aplicar habilitação, desabilitação, recolhimento e mensagens explicativas ao
    vivo enquanto o usuário altera a opção principal;
  - validar novamente as dependências ao salvar e também ao carregar configurações
    antigas ou inconsistentes;
  - nunca deixar um controle parecer ativo quando seu recurso não está sendo
    executado;
  - quando um recurso for independente, oferecer controle próprio e deixar essa
    independência clara na descrição.
- **Próxima decisão:** definir se controles inativos ficam visíveis e cinza ou se
  aparecem somente após expandir/ativar o modo correspondente. Preferência
  preliminar: visíveis e rebaixados, com o motivo, para ensinar a relação ao
  usuário.
- **Especificação:** [PRD QS-003 — Configurações contextuais](PRD_QS003_CONFIGURACOES_CONTEXTUAIS.md)

### QS-004 — Ícone central do HUD desaparece em transições rápidas

- **Tipo:** Bug de interface e feedback de estado.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-001 — Fila de transcrições consecutivas.
- **Problema:** o ícone/animação central do HUD desaparece ocasionalmente quando
  o usuário finaliza uma transcrição e inicia outra gravação muito rápido. Sem o
  indicador, não fica claro se o sistema continua gravando ou processando.
- **Frequência observada:** intermitente, mais provável em ações consecutivas e
  rápidas.
- **Resultado desejado:** o HUD deve sempre exibir um indicador visual coerente
  com o estado atual, inclusive em transições rápidas entre conclusão,
  processamento e nova gravação.
- **Regras preliminares:**
  - eventos atrasados de animação ou ocultação não podem apagar o HUD da sessão
    seguinte;
  - cada atualização visual deve validar a sessão ou geração de HUD à qual
    pertence;
  - iniciar uma gravação deve restaurar explicitamente todos os elementos do tema
    selecionado;
  - a correção da fila QS-001 pode compartilhar a solução de controle de estados,
    mas QS-004 só será concluído após validação própria;
  - adicionar teste de estresse para finalizar e reiniciar repetidamente com
    intervalos curtos.
- **Critério principal de aceite:** após múltiplos ciclos rápidos de
  finalizar/iniciar, o ícone central permanece visível e animado durante toda
  gravação ou processamento ativo.
- **Especificação:** [PRD QS-004 — Ícone central do HUD](PRD_QS004_HUD_ICONE_TRANSICOES.md)

### QS-005 — Detectar e reutilizar modelos Whisper compatíveis existentes

- **Tipo:** Feature de onboarding e gerenciamento de armazenamento.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-006 — Download resiliente do modelo.
- **Problema:** atualmente o Quantum Scribe verifica apenas seu próprio diretório
  de modelos. Um usuário pode já possuir o mesmo modelo em um cache conhecido ou
  instalado por outro projeto e ainda ser obrigado a baixar outra cópia.
- **Resultado desejado:** antes de iniciar um download grande, procurar modelos
  existentes em locais conhecidos, validar sua compatibilidade e informar ao
  usuário quando puderem ser reutilizados com segurança.
- **Regras preliminares:**
  - pesquisar primeiro o cache próprio, o cache padrão do Hugging Face e caminhos
    configurados por variáveis oficiais do ecossistema;
  - oferecer `Localizar modelo existente…` para seleção manual de uma pasta;
  - reconhecer que modelos OpenAI Whisper/PyTorch e modelos faster-whisper em
    CTranslate2 podem ter formatos incompatíveis;
  - validar nome, formato, arquivos essenciais, tamanho e capacidade de carga
    antes de aceitar um modelo encontrado;
  - nunca executar arquivos nem confiar somente no nome da pasta;
  - mostrar `Modelo compatível encontrado` com origem, variante e espaço que será
    economizado, pedindo confirmação antes de vinculá-lo;
  - preferir referência segura ao cache existente ou link de filesystem quando
    suportado; copiar apenas quando necessário;
  - se o modelo for incompatível, explicar o motivo e seguir para o fluxo de
    download sem quebrar a instalação;
  - não fazer varredura indiscriminada de todos os discos, evitando lentidão e
    acesso desnecessário a arquivos pessoais.
- **Critério principal de aceite:** numa máquina com snapshot CTranslate2 válido
  no cache global do Hugging Face, o app o detecta, valida e pode iniciar sem
  baixar uma segunda cópia.

### QS-006 — Download resiliente do modelo com retomada e fallback

- **Tipo:** Melhoria crítica de onboarding e confiabilidade.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-005 — Detecção de modelos existentes.
- **Problema:** falhas repetidas no download do modelo quase fizeram um novo
  usuário desistir da instalação. Sem modelo completo, a função principal do
  produto fica indisponível.
- **Resultado desejado:** concluir o download de forma confiável em conexões
  instáveis e oferecer caminhos de recuperação claros, sem exigir intervenção
  técnica ou ajuda de um agente.
- **Estratégia de fallback preliminar:**
  1. retomar o snapshot parcial da fonte oficial primária;
  2. repetir automaticamente arquivos que falharam, com backoff e limite seguro;
  3. alternar para uma fonte secundária previamente validada e confiável;
  4. oferecer download manual verificado ou instalador offline como última opção.
- **Regras preliminares:**
  - não depender de um único link permanente sem monitoramento;
  - fixar repositório/revisão compatível e validar arquivos essenciais após cada
    tentativa;
  - preservar partes válidas e retomar de onde parou, sem reiniciar gigabytes;
  - verificar espaço em disco, acesso à pasta, conectividade, proxy, certificado
    TLS e integridade antes de exibir um erro genérico;
  - usar staging e promoção atômica, nunca tratar snapshot parcial como instalado;
  - apresentar progresso real, arquivo atual, tentativas e ação seguinte;
  - oferecer `Tentar novamente`, `Alterar local`, `Usar modelo existente` e
    `Download manual`, conforme a causa;
  - manter a interface responsiva e permitir fechar/reabrir o app sem perder o
    progresso válido;
  - registrar diagnóstico técnico sem dados pessoais e permitir copiá-lo para
    suporte;
  - testar fonte primária e fallback periodicamente antes de cada release;
  - executar testes de instalação limpa, conexão interrompida, pouco espaço,
    proxy corporativo, snapshot corrompido e retomada após reinício.
- **Critérios principais de aceite:**
  - uma interrupção no meio do download é retomada sem baixar novamente os
    arquivos completos;
  - falha na fonte primária aciona uma alternativa segura ou uma instrução de
    recuperação utilizável;
  - o app só informa `Modelo instalado` depois de validar e carregar o snapshot;
  - nenhum usuário fica preso num ciclo de erro sem causa e próxima ação visíveis.
- **Especificação:** [PRD QS-006 — Download resiliente](PRD_QS006_DOWNLOAD_MODELO_RESILIENTE.md)

### QS-007 — Unificar e atualizar o ícone oficial em todas as superfícies

- **Tipo:** Bug de identidade visual e empacotamento.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Problema:** o ícone exibido na barra de tarefas e o ícone da bandeja do
  Windows estão desatualizados ou diferentes do ícone oficial mostrado na tela
  Sobre e nas janelas do aplicativo.
- **Constatação atual:** as janelas carregam o ícone de átomo/microfone, enquanto
  a bandeja gera por código um ícone distinto de barras de áudio.
- **Resultado desejado:** adotar uma única fonte oficial de ícone e gerar dela
  todas as variantes necessárias para janela, executável, barra de tarefas,
  bandeja, instalador, atalhos e tela Sobre.
- **Regras preliminares:**
  - manter um asset mestre em alta resolução e versões apropriadas para cada
    tamanho e densidade;
  - gerar `.ico` com múltiplas resoluções para o executável e atalhos do Windows;
  - garantir legibilidade da bandeja nos temas claro e escuro e em 100%–200% de
    escala;
  - substituir o gerador de barras de áudio da bandeja pelo ícone oficial;
  - atualizar metadados do build e instalador, considerando o cache de ícones do
    Windows em atualizações;
  - impedir que uma ausência de asset faça diferentes superfícies voltarem a
    logos divergentes.
- **Critério principal de aceite:** após instalação limpa e atualização, todas as
  superfícies exibem a mesma identidade visual, sem ícone antigo em cache.
- **Especificação:** [PRD QS-007 — Ícone oficial unificado](PRD_QS007_ICONES_OFICIAIS.md)

### QS-008 — Sincronizar a cor personalizada com os ícones do aplicativo

- **Tipo:** Melhoria de personalização visual.
- **Prioridade preliminar:** P3 — Baixa.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-007 — Ícone oficial unificado.
- **Problema:** a cor de destaque/átomo pode ser personalizada dentro do sistema,
  mas os ícones externos permanecem com a cor padrão.
- **Resultado desejado:** avaliar a aplicação da cor escolhida pelo usuário ao
  ícone da bandeja e às janelas, mantendo contraste e reconhecimento da marca.
- **Regras preliminares:**
  - atualizar imediatamente os ícones que aceitam imagem em tempo de execução;
  - manter fallback monocromático ou de alto contraste quando necessário;
  - não prometer alteração instantânea do ícone fixado na barra de tarefas caso o
    Windows dependa do ícone estático do executável e de cache;
  - separar personalização dinâmica dos assets oficiais usados pelo instalador;
  - oferecer `Usar cor do sistema` e `Usar cor oficial` como escolhas claras.
- **Próxima decisão:** decidir se a personalização deve atingir somente bandeja e
  janelas ou também atalhos/barra de tarefas após reinício.

### QS-009 — Modernizar o controle de volume dos efeitos

- **Tipo:** Melhoria visual e de interação.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** P.
- **Problema:** o controle atual usa o slider clássico do Tkinter e apresenta um
  cursor quadrado, visualmente antigo e inconsistente com o restante do painel.
- **Resultado desejado:** substituir por um slider moderno com trilho limpo,
  preenchimento na cor de destaque e marcador circular.
- **Regras preliminares:**
  - usar esfera/círculo como thumb, com estados normal, hover, pressionado e foco;
  - suportar clique no trilho, arraste suave, teclado e escala de DPI;
  - manter percentual visível e atualização ao vivo;
  - preservar acessibilidade, área de toque confortável e contraste nos temas
    claro e escuro;
  - usar componente reutilizável para futuros sliders do painel.
- **Critério principal de aceite:** o slider não exibe componentes nativos
  quadrados e continua operável por mouse e teclado em diferentes escalas.

### QS-010 — Redesenhar o histórico de transcrições como tabela moderna

- **Tipo:** Melhoria de experiência e organização.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-011 e QS-012.
- **Problema:** o histórico atual é um campo de texto com links roxos para
  arquivos diários, tem pouca hierarquia visual e não permite examinar as
  transcrições de forma confortável dentro do app.
- **Resultado desejado:** apresentar o histórico numa tabela/lista moderna,
  neutra e legível, com separação clara entre dias e entradas.
- **Regras preliminares:**
  - usar preto, cinzas e branco como base; reservar a cor de destaque para foco,
    seleção ou ação, sem colorir todos os nomes;
  - usar linhas alternadas em cinza mais claro/escuro ou divisores discretos;
  - considerar colunas `Data`, `Hora`, `Prévia`, `Quantidade` e `Ações`;
  - permitir expandir um dia e visualizar suas transcrições sem abrir o Markdown
    externamente;
  - oferecer ordenação, cópia, abertura do arquivo e navegação por teclado;
  - manter boa leitura com históricos grandes e scrollbar discreta;
  - preservar os arquivos Markdown atuais como fonte ou formato de exportação,
    evitando migração destrutiva.
- **Critério principal de aceite:** dias e entradas são distinguíveis sem depender
  de links coloridos, com data/hora e prévia consultáveis dentro do aplicativo.

### QS-011 — Pesquisa textual unificada em todas as transcrições

- **Tipo:** Feature de recuperação de informação.
- **Prioridade preliminar:** P1 — Alta.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-010 — Novo histórico; QS-012 — Pesquisa semântica.
- **Problema:** o usuário não consegue localizar uma palavra ou frase sem abrir e
  procurar manualmente em cada arquivo diário.
- **Resultado desejado:** pesquisar de uma vez em todos os arquivos e entradas do
  histórico, funcionando localmente em qualquer computador.
- **Regras preliminares:**
  - oferecer busca exata e por palavras, sem diferenciar maiúsculas/minúsculas e
    com tratamento adequado de acentos;
  - indexar data, hora, texto e origem de cada entrada;
  - destacar os termos encontrados e mostrar trecho de contexto;
  - permitir filtrar por intervalo de datas e ordenar por relevância ou recência;
  - atualizar o índice quando novas transcrições forem salvas ou arquivos forem
    alterados;
  - reconstruir o índice sem perder os Markdown originais;
  - responder rapidamente em históricos grandes e manter tudo offline.
- **Critério principal de aceite:** uma frase existente em qualquer arquivo diário
  é encontrada numa única busca, com link direto para a entrada correspondente.
- **Especificação:** [PRD QS-011 — Pesquisa textual](PRD_QS011_PESQUISA_TRANSCRICOES.md)

### QS-012 — Pesquisa semântica local e adaptativa no histórico

- **Tipo:** Feature avançada de recuperação de informação.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-011 — Busca textual; QS-013 — Modo cloud/API.
- **Problema:** uma busca apenas por palavras não encontra ideias relacionadas
  quando o usuário não lembra a formulação exata do que disse.
- **Resultado desejado:** permitir busca por significado usando chunks,
  embeddings e índice vetorial local sempre que o computador suportar, com
  adaptação automática ao ambiente.
- **Regras preliminares:**
  - manter a busca textual QS-011 como base universal e fallback obrigatório;
  - dividir entradas em chunks preservando data, hora, arquivo e posição;
  - selecionar modelo de embeddings pequeno, multilíngue e adequado ao português;
  - armazenar embeddings e metadados localmente, com reconstrução incremental;
  - detectar RAM, CPU/GPU, espaço e capacidades antes de oferecer ou ativar o
    recurso;
  - disponibilizar modo leve por CPU e ocultar/desabilitar semantic search quando
    o ambiente não atingir requisitos mínimos;
  - explicar consumo de disco, tempo de indexação e privacidade;
  - permitir apagar e reconstruir o índice sem apagar transcrições;
  - combinar relevância semântica, correspondência textual e recência;
  - avaliar resultados em português com um conjunto de consultas reais antes do
    lançamento.
- **Critério principal de aceite:** uma consulta conceitualmente relacionada,
  mesmo sem repetir as palavras originais, retorna a entrada correta entre os
  primeiros resultados num computador compatível.

### QS-013 — Modo cloud/API opcional para computadores fracos

- **Tipo:** Pesquisa de produto, arquitetura e monetização.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** G.
- **Relacionado a:** QS-006 — Download; QS-012 — Pesquisa semântica local.
- **Problema:** computadores fracos ou incompatíveis podem não executar com boa
  experiência transcrição, LLM e embeddings locais.
- **Oportunidade:** oferecer um plano pago opcional que execute esses recursos por
  API/cloud, mantendo o modo local como alternativa principal para quem possui
  hardware compatível.
- **Escopo de pesquisa:**
  - transcrição por API, pós-processamento por LLM e embeddings/busca semântica;
  - seleção automática ou manual entre `Local`, `Cloud` e `Híbrido` por recurso;
  - custos por minuto, tokens, armazenamento e indexação versus preço sustentável;
  - autenticação, cobrança, limites, observabilidade e suporte;
  - consentimento explícito antes de enviar áudio ou texto para terceiros;
  - criptografia, retenção mínima, exclusão, portabilidade e requisitos legais de
    privacidade/LGPD;
  - provedores alternativos e fallback para evitar dependência de uma única API;
  - degradação clara para busca textual/local quando assinatura ou rede falhar;
  - comunicação transparente de quais dados saem do computador em cada modo.
- **Princípio de produto:** recursos locais existentes não devem ser removidos ou
  bloqueados artificialmente para forçar assinatura.
- **Critério de saída da pesquisa:** proposta técnica e financeira com custos,
  riscos, experiência de consentimento, fornecedores possíveis e definição de um
  MVP pago para computadores fracos.

### QS-014 — Controle de destino e mudança de foco ao entregar transcrições

- **Tipo:** Melhoria de experiência e controle de automação.
- **Prioridade preliminar:** P2 — Média.
- **Esforço preliminar:** M.
- **Relacionado a:** QS-001 — Fila de transcrições consecutivas.
- **Problema:** o aplicativo captura a janela/campo que estava ativo no início do
  ditado e, ao concluir, força o foco de volta para esse destino antes de colar.
  Isso protege contra colagem no lugar errado, mas pode interromper quem já está
  trabalhando em outra página ou aplicativo.
- **Constatação atual:** a opção existente de colagem automática controla se o
  texto será colado ou apenas copiado; ela não permite escolher se o destino é a
  janela original ou o foco atual no momento da conclusão.
- **Resultado desejado:** permitir que cada usuário escolha como a transcrição
  será entregue quando o foco tiver mudado durante o processamento.
- **Modos preliminares:**
  - `Voltar ao campo original`: comportamento atual, restaura a janela capturada
    no início e cola no destino original;
  - `Colar onde eu estiver`: não troca de janela e cola no campo que estiver
    ativo quando a transcrição terminar;
  - `Somente copiar`: nunca muda o foco nem cola automaticamente;
  - avaliar `Perguntar quando o foco mudar`, com aviso não intrusivo e ações para
    escolher o destino.
- **Regras preliminares:**
  - apresentar a escolha nas configurações em linguagem clara, separada do toggle
    geral de colagem automática;
  - não mudar de página ou trazer uma janela para frente quando o usuário tiver
    desabilitado o retorno ao destino original;
  - preservar o texto no clipboard se o destino escolhido não aceitar a colagem;
  - mostrar confirmação indicando onde o texto foi inserido ou que ficou somente
    copiado;
  - no modo autoenvio, pressionar Enter apenas após inserção confirmada e nunca em
    uma janela diferente da escolhida;
  - definir comportamento individual por job quando a fila QS-001 existir;
  - manter o comportamento atual como opção disponível e documentar o padrão para
    instalações novas.
- **Próxima decisão:** escolher entre `Voltar ao campo original` e `Perguntar
  quando o foco mudar` como padrão mais seguro para novos usuários.
- **Critério principal de aceite:** com o retorno automático desabilitado, o
  usuário pode trocar de aplicativo durante a transcrição e nenhuma janela é
  aberta, restaurada ou trazida para frente contra sua vontade.

## Pronto para priorização

_Nenhum item._

## Planejado

_Nenhum item._

## Em desenvolvimento

_Nenhum item._

## Bloqueado

_Nenhum item._

## Concluído

_Nenhum item registrado neste backlog._

## Descartado

_Nenhum item._

## Roteiro de refinamento

Para cada item, responder:

- Qual problema real estamos resolvendo?
- Quem é afetado e com que frequência?
- Qual resultado indicará que a mudança funcionou?
- O que faz parte e o que não faz parte da primeira versão?
- Existem riscos de perda de dados, privacidade ou regressão?
- Há dependências técnicas ou decisões pendentes?
- Quais são os critérios mínimos de aceite?
- Qual é a prioridade relativa aos demais itens?
