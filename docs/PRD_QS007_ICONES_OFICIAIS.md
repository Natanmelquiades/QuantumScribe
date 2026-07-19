# PRD QS-007 — Ícone oficial unificado

**Status:** proposta para validação
**Prioridade:** P1 — Alta
**Esforço preliminar:** M
**Relacionado a:** QS-008 — Personalização de cor dos ícones

## Contexto

As janelas e a tela Sobre usam o asset de átomo/microfone carregado por
`load_or_generate_icon`. A bandeja cria por código outro ícone, composto por
barras de áudio. Build e instalador usam arquivos diferentes (`icon.png` e
`QuantumScribe.ico`), o que facilita divergência e cache antigo no Windows.

## Problema

- O produto apresenta identidades diferentes conforme a superfície.
- Barra de tarefas, bandeja, atalho e instalador podem usar versões desatualizadas.
- O cache de ícones do Windows pode manter o asset anterior após atualização.
- Não existe uma validação automática de que todos os artefatos vieram da mesma
  fonte.

## Objetivo

Estabelecer um asset mestre e um pipeline determinístico que gere e aplique a
mesma identidade em todas as superfícies do Windows.

## Superfícies obrigatórias

- executável e barra de tarefas;
- janela principal oculta e configurações;
- bandeja do sistema;
- tela Sobre e cabeçalho lateral;
- atalhos do menu Iniciar e desktop;
- instalador, desinstalador e lista de aplicativos instalados;
- documentação oficial e screenshots futuros.

## Requisitos do asset

- Fonte mestre com transparência e resolução suficiente.
- Variante simplificada para 16×16 e 20×20, sem detalhes ilegíveis.
- `.ico` multirresolução: 16, 20, 24, 32, 40, 48, 64, 128 e 256 px quando
  suportado.
- PNGs derivados para Tkinter/Pillow e bandeja.
- Margens e contraste adequados nos temas claro e escuro.

## Requisitos funcionais

- **RF01:** manter um único asset mestre versionado.
- **RF02:** gerar derivados por script de build, nunca por edição manual separada.
- **RF03:** substituir o ícone de barras da bandeja pela variante oficial.
- **RF04:** usar o `.ico` gerado no PyInstaller, NSIS, atalhos e metadados.
- **RF05:** manter referência forte às imagens Tkinter para evitar coleta de lixo.
- **RF06:** atualizar o ícone da bandeja sem precisar reiniciar quando somente seu
  estado visual mudar.
- **RF07:** falha ao carregar asset deve usar um único fallback oficial embutido.
- **RF08:** o build deve falhar se os derivados estiverem ausentes ou desatualizados.
- **RF09:** documentar estratégia para cache do Windows em upgrade.
- **RF10:** QS-008 poderá colorir variantes em runtime sem modificar o asset
  oficial do instalador.

## Requisitos não funcionais

- Nitidez em escalas de 100%, 125%, 150% e 200%.
- Sem halo, fundo opaco indesejado ou recorte irregular.
- Geração reproduzível em máquinas de build limpas.
- Aumento irrelevante no tamanho do instalador.

## Critérios de aceite

1. Instalação limpa exibe a mesma marca na barra, bandeja, janelas, atalhos,
   instalador e lista de aplicativos.
2. A variante da bandeja é reconhecível em 16×16 nos temas claro e escuro.
3. Atualizar uma instalação antiga não deixa o ícone de barras nas superfícies
   controladas pelo app.
4. Todos os tamanhos mantêm transparência e proporção corretas.
5. O pipeline detecta derivados antigos em relação ao asset mestre.
6. Ausência do arquivo externo usa o mesmo fallback, não um desenho diferente.

## Plano de testes

- comparar hashes/manifesto dos derivados gerados;
- inspecionar executável, instalador e atalhos em VM limpa;
- testar atualização sobre versão anterior;
- validar bandeja em tema claro/escuro e escalas de DPI;
- reiniciar Explorer e limpar cache apenas no ambiente de teste para diferenciar
  bug de empacotamento de cache do sistema;
- conferir propriedades do executável e painel de aplicativos instalados.

## Fora de escopo

- Redesenhar o logotipo.
- Aplicar cor personalizada a atalhos estáticos e instalador; isso pertence a
  QS-008.
- Criar animação no ícone da bandeja.

## Rollout e rollback

- Gerar assets e validar primeiro no bundle portátil.
- Depois validar instalador limpo e atualização.
- Preservar temporariamente os assets anteriores somente como rollback de build,
  sem expor duas identidades no produto final.
