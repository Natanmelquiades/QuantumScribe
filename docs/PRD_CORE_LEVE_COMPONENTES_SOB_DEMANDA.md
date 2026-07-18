# PRD — QuantumScribe Core Leve e Componentes Sob Demanda

**Status:** proposto — pronto para implementação

**Responsável pelo produto:** Natan Melquiades

**Versão-alvo:** 2.2.0

**Data:** 18/07/2026

## 1. Resumo executivo

O QuantumScribe 2.1.26 distribui um instalador universal CPU/CUDA de aproximadamente
757 MB. Depois de instalado, o bundle contém mais de 1 GB de runtime NVIDIA, cerca
de 361 MB de Torch e outras bibliotecas destinadas a recursos que nem todos os
usuários utilizam. Na primeira execução, o aplicativo também inicia automaticamente
o download do modelo Whisper padrão.

A versão 2.2.0 deve inverter esse modelo. O produto primário será um **Core CPU
mínimo**, sem CUDA, Torch, modelos de linguagem, redução neural de ruído ou outros
recursos pesados. A seleção de hardware continuará automática: uma GPU NVIDIA
compatível terá prioridade e CPU será o fallback transparente. O pacote CUDA só será
incluído no preparo quando a detecção confirmar que aquela máquina pode utilizá-lo.
Nenhum componente ou modelo será baixado sem uma ação explícita do usuário que
confirme o plano e o tamanho total. Recursos opcionais serão instalados por um
gerenciador interno de componentes, com finalidade e impacto informados antes do
download.

Quando um componente nativo exigir recarga do processo, a interface exibirá o botão
**“Reiniciar QuantumScribe agora”**. O Windows não deverá ser reiniciado: o aplicativo
não instalará drivers, serviços ou componentes de sistema. Modelos que possam ser
carregados dinamicamente não exigirão reinicialização.

A função de backup e restauração será removida integralmente do produto. A proteção
do código do desenvolvedor continuará sendo responsabilidade do Git, das tags, das
Releases e da estratégia externa de backup do proprietário, sem código ou interface
de backup no aplicativo entregue ao usuário.

## 2. Decisões de produto confirmadas

1. O instalador principal será CPU, pequeno e funcional.
2. `device="auto"` e `compute_type="auto"` serão os padrões.
3. GPU NVIDIA compatível terá prioridade; CPU será fallback automático.
4. Recursos pesados virão ausentes do Core e só serão preparados quando houver uso
   comprovado pelo hardware ou escolha funcional do usuário.
5. A detecção será automática, mas o plano de download será visível e confirmado.
6. O aplicativo mostrará o tamanho antes de baixar e o espaço ocupado depois.
7. Instalações sob demanda não usarão `pip` no computador do usuário.
8. Componentes serão pré-compilados, versionados, verificados por hash e compatíveis
   com a versão instalada do QuantumScribe.
9. Reinicialização, quando necessária, significa reiniciar o aplicativo, não o PC.
10. A função de backup/restauração será removida da aplicação pública.
11. O caminho padrão de instalação será fixo por usuário e a desinstalação nunca
    removerá recursivamente uma pasta arbitrária escolhida pelo usuário.

## 3. Problema

### 3.1 Distribuição excessivamente grande

O release universal inclui dependências para CPU, CUDA, streaming neural e melhoria
avançada de áudio no mesmo pacote. Usuários sem GPU NVIDIA recebem bibliotecas que
jamais serão carregadas. Usuários que não ativam streaming também recebem Torch e o
runtime do Silero VAD.

### 3.2 Downloads automáticos

O modelo padrão é baixado automaticamente na primeira execução. Embora o download
seja documentado, o usuário não escolhe previamente a relação entre tamanho,
velocidade e qualidade.

### 3.3 Dependências opcionais misturadas ao Core

Ferramentas de build e bibliotecas de funções opcionais estão declaradas junto das
dependências essenciais. Isso aumenta tempo de instalação, superfície de ataque,
volume do executável e dificuldade de auditoria.

### 3.4 Desinstalação ampla

O instalador atual permite escolher o diretório e o desinstalador remove `$INSTDIR`
recursivamente. No caminho padrão isso funciona, mas uma escolha inadequada pode
colocar arquivos não pertencentes ao produto dentro do alcance da remoção.

### 3.5 Backup sem valor para o usuário final

A tela de configurações expõe criação, listagem, restauração e exclusão de backups de
código e dados. Essa função aumenta a interface, o código sensível de filesystem e a
possibilidade de o usuário gerar ZIPs com conteúdo pessoal. Ela não faz parte do
valor central de um aplicativo de ditado.

### 3.6 Automação atual depende do bundle universal

O código 2.1.26 já usa `device="auto"` e `compute_type="auto"` por padrão. A resolução
atual consulta o CTranslate2, prioriza CUDA quando GPU e DLLs são utilizáveis, escolhe
uma precisão compatível e recua para CPU se a inicialização ou a decodificação falhar.

Esse comportamento está correto, mas o release universal o obtém levando o runtime
CUDA para todas as máquinas. A 2.2.0 deverá preservar a mesma automação e mudar apenas
a entrega: detectar primeiro o hardware e baixar o runtime CUDA somente onde ele será
utilizado.

## 4. Objetivos

- Entregar uma instalação inicial pequena, rápida e previsível.
- Manter seleção automática de hardware, com GPU compatível como primeira opção.
- Manter ditado CPU, gravação, transcrição, pontuação, atalhos, clipboard, bandeja e
  configurações essenciais funcionando no Core.
- Impedir qualquer download silencioso de modelo ou componente opcional.
- Baixar apenas o recurso escolhido e apenas uma vez.
- Permitir instalar, atualizar e remover componentes opcionais com segurança.
- Eliminar Torch do Core e preferencialmente de toda a distribuição.
- Separar dependências de execução, build, teste e componentes opcionais.
- Remover a função de backup/restauração do produto.
- Tornar instalação, atualização e desinstalação incapazes de apagar arquivos não
  pertencentes ao QuantumScribe.
- Endurecer a cadeia de build e publicação dos artefatos distribuídos.

## 5. Não objetivos

- Instalar ou atualizar drivers NVIDIA.
- Reiniciar automaticamente o Windows.
- Executar `pip install` na máquina do usuário final.
- Embutir modelos Whisper ou Mini-LLMs no instalador Core.
- Manter compatibilidade com backups criados pela interface antiga.
- Criar um sistema próprio de atualização de driver ou gerenciador genérico de
  pacotes.
- Remover notas, diário ou Quantum Brain sem uma decisão de produto separada.
- Oferecer nuvem, telemetria ou transcrição remota.

## 6. Experiência principal

### 6.1 Instalação

O instalador deve:

- instalar somente para o usuário atual;
- usar o caminho fixo `%LOCALAPPDATA%\Programs\QuantumScribe`;
- não solicitar privilégios administrativos;
- não instalar serviço, driver, tarefa agendada ou regra de firewall;
- não criar inicialização automática;
- conter apenas o Core CPU;
- informar o tamanho instalado antes da confirmação;
- abrir o aplicativo sem iniciar downloads em segundo plano.

A tela de seleção de diretório deverá ser removida. A simplicidade e a segurança do
caminho fixo têm prioridade sobre uma personalização de baixo valor.

### 6.2 Primeira execução

Sem um modelo instalado, o aplicativo abrirá um onboarding curto:

1. Explicar que o áudio permanece local.
2. Informar que um modelo é necessário para transcrever.
3. Apresentar modelos compatíveis com tamanho real de download, espaço em disco,
   velocidade estimada e indicação de qualidade.
4. Detectar automaticamente o hardware e apresentar uma linha de decisão:
   - **“NVIDIA compatível detectada — aceleração GPU será preparada”**; ou
   - **“Execução em CPU — nenhum pacote de GPU será baixado”**.
5. Incluir o runtime CUDA no tamanho total somente quando a máquina for elegível.
6. Marcar **Balanceado** como recomendação visual, sem iniciar o download.
7. Exigir o clique em **“Baixar e preparar”** para confirmar conjuntamente o modelo e,
   quando aplicável, o componente CUDA selecionado automaticamente.
8. Permitir fechar o onboarding e explorar as configurações sem baixar nada.

Os perfis apresentados serão:

| Perfil | Modelo inicial sugerido | Comportamento |
| --- | --- | --- |
| Mínimo | `tiny` ou `base` | menor download e menor uso de memória |
| Balanceado | `small` | recomendação padrão para a maioria |
| Pro | `medium` | maior qualidade, download substancial |
| Máximo | `large-v3` | somente mediante escolha explícita e hardware adequado |

Os tamanhos não serão codificados manualmente na interface. Eles virão do manifesto
de modelos e serão apresentados antes da confirmação.

### 6.3 Uso normal

Depois de baixar um modelo, o Core deverá oferecer:

- gravação por atalho global;
- transcrição local em CPU;
- modo literal e pontuação determinística;
- clipboard e colagem automática;
- tradução já suportada pelo modelo, quando aplicável;
- HUD, sons, bandeja e histórico já existentes;
- streaming básico com Energy VAD, se mantido no escopo funcional;
- atualização e troca explícita de modelo.

O hardware não deverá exigir escolha cotidiana. Em cada inicialização:

1. se o componente CUDA estiver instalado e uma GPU NVIDIA compatível estiver
   disponível, usar CUDA;
2. escolher automaticamente o melhor `compute_type` suportado;
3. se GPU, driver, DLL ou memória forem insuficientes, recuar para CPU;
4. registrar o motivo técnico sem impedir a transcrição;
5. manter um override CPU apenas na seção avançada para diagnóstico.

O aplicativo não fará conexões de rede enquanto estiver ocioso. Rede será usada
somente durante uma operação visível de download, atualização ou consulta de
manifesto iniciada pelo usuário.

## 7. Arquitetura de distribuição

### 7.1 Core CPU

O Core conterá apenas dependências realmente importadas pelo fluxo primário. A
implementação deverá produzir um relatório de dependências e justificar cada pacote
direto.

Devem permanecer no Core, após confirmação por testes de importação e empacotamento:

- `faster-whisper` e o runtime CPU necessário do CTranslate2;
- `numpy`;
- `sounddevice`;
- `Pillow` e `pystray`;
- bibliotecas Win32 efetivamente utilizadas;
- cliente mínimo do Hugging Face necessário para downloads consentidos;
- dependências transitivas comprovadamente necessárias.

Devem sair das dependências do Core:

- `pyinstaller` e ferramentas de build;
- `pytest`, `ruff`, `pip-audit` e ferramentas de desenvolvimento;
- `nvidia-cublas-cu12` e `nvidia-cudnn-cu12`;
- `torch` e `torchaudio`;
- `silero-vad` baseado em Torch;
- `noisereduce`, `scipy` e `matplotlib`, salvo se uma medição provar que alguma parte
  é indispensável ao fluxo primário;
- `comtypes` ou `uiautomation` se a auditoria de uso confirmar que não são necessários.

### 7.2 Perfis de dependência

Os arquivos deverão ser reorganizados em perfis inequívocos:

- `requirements-core.in`: dependências diretas mínimas do aplicativo;
- `requirements-core.lock`: resolução exata com hashes;
- `requirements-build.lock`: PyInstaller e ferramentas de empacotamento;
- `requirements-test.lock`: testes, lint e auditoria;
- manifestos próprios para componentes opcionais, sem instalação via `pip` no
  computador do usuário.

O ambiente de desenvolvimento pode combinar os perfis, mas o build de release deverá
começar em ambiente limpo e instalar apenas Core + build.

### 7.3 Componentes opcionais

#### A. Aceleração NVIDIA CUDA

- Desabilitada e ausente no Core.
- O modo padrão será sempre `auto`; não haverá toggle obrigatório CPU/GPU no fluxo
  principal.
- O aplicativo detectará GPU e driver compatíveis durante o onboarding.
- Em máquina elegível, CUDA será selecionado automaticamente e entrará no plano de
  preparo confirmado pelo usuário, sem exigir que ele conheça CUDA.
- Em máquina sem NVIDIA compatível, nenhum byte do componente será baixado.
- O pacote conterá somente DLLs comprovadamente necessárias para inferência.
- O aplicativo não instalará driver NVIDIA.
- Após instalação ou remoção, será necessário reiniciar o QuantumScribe para carregar
  ou liberar as DLLs.
- Após o reinício, a seleção automática validará o runtime e usará GPU sem nova ação.
- Se a GPU falhar ao carregar ou decodificar, CPU assumirá a mesma tarefa.
- A UI mostrará ganho esperado, tamanho, decisão automática e requisitos antes do
  download.

#### B. VAD neural avançado

- O Core usará Energy VAD ou alternativa leve.
- A solução preferencial será Silero VAD em ONNX usando um runtime já presente, sem
  Torch.
- Torch somente poderá existir como componente excepcional se benchmarks demonstrarem
  que ONNX não atende aos critérios de qualidade e latência.
- A simples ativação do streaming não poderá baixar Torch silenciosamente.

#### C. Redução avançada de ruído

- O Core manterá normalização e filtros leves implementados com dependências já
  existentes.
- `noisereduce`, SciPy e Matplotlib não farão parte da instalação inicial.
- Um componente avançado somente será criado se testes A/B demonstrarem melhoria
  perceptível superior ao custo de download e memória.
- Se não houver benefício claro, a função será removida em vez de modularizada.

#### D. Reescrita por Mini-LLM

- Permanecerá desabilitada por padrão.
- O modelo nunca será baixado ao habilitar uma caixa de seleção sem confirmação.
- A tela exibirá repositório, licença, tamanho e espaço necessário.
- O runtime existente será reutilizado; somente os pesos e arquivos estritamente
  necessários serão baixados.
- A ativação ocorrerá após validação do modelo; reinício só será solicitado se houver
  troca de runtime nativo.

#### E. Modelos Whisper adicionais

- Nenhum modelo será incluído no instalador.
- Apenas o modelo escolhido será baixado.
- Trocar de modelo não apagará automaticamente o anterior.
- A tela permitirá remover modelos não usados e informará quanto espaço será liberado.
- O modelo ativo nunca será removido sem confirmação e seleção de substituto.

## 8. Gerenciador de componentes

### 8.1 Interface

A seção **Recursos opcionais** apresentará um card por componente com:

- nome e benefício;
- estado: não instalado, baixando, instalado, atualização disponível ou erro;
- tamanho de download e tamanho instalado;
- requisito de hardware;
- versão compatível;
- indicação “requer reiniciar o aplicativo”, quando aplicável;
- botões instalar, cancelar, tentar novamente, remover e reiniciar.

Nenhum controle deverá parecer habilitado enquanto o componente ainda não estiver
pronto. Marcar uma opção abrirá a confirmação de download, não instalará imediatamente.

CUDA será uma exceção de interação: a decisão de usar ou não será automática, mas o
download continuará aparecendo no plano confirmado pelo usuário. A seção avançada
permitirá forçar CPU para diagnóstico; não será necessário selecionar GPU manualmente.

### 8.2 Fluxo de instalação

1. Buscar manifesto compatível com a versão do aplicativo.
2. Exibir tamanho, origem, licença e espaço necessário.
3. Solicitar confirmação.
4. Baixar para arquivo temporário `.part`, com progresso e cancelamento.
5. Validar tamanho e SHA-256 antes de abrir ou extrair.
6. Validar nomes e destinos para impedir path traversal.
7. Extrair para diretório temporário dentro da pasta de componentes.
8. Fazer troca atômica para a versão validada.
9. Registrar componente, versão, hashes e arquivos pertencentes a ele.
10. Marcar `pending_restart` somente quando o processo atual não puder carregar o
    componente com segurança.

Uma falha em qualquer etapa preservará o Core funcional e removerá apenas os arquivos
temporários pertencentes à tentativa.

### 8.3 Reinicialização do aplicativo

Quando necessária, a UI exibirá:

- **Reiniciar QuantumScribe agora**;
- **Reiniciar depois**.

O reinício deverá:

1. salvar configurações pendentes;
2. impedir nova gravação;
3. encerrar gravação, hotkeys, tray e workers;
4. iniciar a mesma instalação do QuantumScribe com um argumento interno seguro;
5. encerrar a instância antiga;
6. validar o componente na nova inicialização;
7. mostrar sucesso ou reverter para o Core em caso de falha.

Não haverá botão para reiniciar o Windows. Se um driver externo for necessário, o
aplicativo apenas explicará o requisito e manterá o recurso desabilitado.

### 8.4 Remoção

- Componentes e modelos opcionais poderão ser removidos individualmente.
- A remoção usará o manifesto de propriedade de arquivos, nunca uma exclusão ampla.
- DLLs carregadas serão removidas após reiniciar o aplicativo.
- O usuário verá o espaço a ser liberado antes de confirmar.
- O Core e o modelo ativo serão protegidos contra remoção acidental.

## 9. Remoção da função de backup

### 9.1 Código e interface

Devem ser removidos:

- `localwhisper/backup.py`;
- imports e chamadas de backup em `settings_ui.py`;
- card “Backup e Restauração”;
- tabela, botões e diálogos de criar, restaurar e excluir backups;
- testes exclusivos de backup;
- mocks de backup usados na captura de screenshots;
- textos de README, privacidade, segurança e interface que apresentam backup como
  função do produto.

A seção “Sistema, Notas & Backups” deverá ser renomeada para refletir apenas as
funções que permanecerem, por exemplo **“Sistema, Notas e Histórico”**.

### 9.2 Dados legados

- A atualização não apagará automaticamente ZIPs antigos do usuário.
- O aplicativo deixará de listar, criar ou restaurar esses arquivos.
- A documentação poderá explicar onde localizar e excluir manualmente backups antigos.
- Uma limpeza opcional só poderá ser adicionada depois, com caminho exato, tamanho
  calculado e confirmação explícita.

### 9.3 Backup do desenvolvedor

Backup de desenvolvimento não será uma função do aplicativo. O proprietário usará:

- commits e branches Git;
- tags e Releases;
- repositório remoto;
- backup externo da estação de trabalho.

A regra `backups/` poderá permanecer no `.gitignore` para impedir commits acidentais,
mas nenhum código de runtime criará ou consumirá essa pasta.

## 10. Segurança da instalação e desinstalação

### 10.1 Instalação

- Usar caminho fixo por usuário.
- Criar um marcador de instalação contendo ID e versão do produto.
- Manter manifesto dos arquivos instalados.
- Atualizações poderão substituir `_internal` apenas depois de validar que o caminho
  pertence ao QuantumScribe.
- Nunca executar scripts recebidos de um componente.
- Nunca adicionar a pasta de componentes ao `PATH` global.

### 10.2 Desinstalação

O desinstalador deverá:

- confirmar o caminho fixo e o marcador do produto;
- remover somente arquivos do manifesto do instalador;
- remover diretórios apenas quando estiverem vazios;
- preservar modelos, configurações, notas e histórico por padrão;
- oferecer remoção de dados pessoais em uma opção separada, desmarcada e explícita;
- abortar se o caminho resolvido for `%LOCALAPPDATA%`, o perfil do usuário, raiz de
  unidade ou qualquer diretório fora do namespace do QuantumScribe;
- possuir testes automatizados para caminhos adulterados e diretórios compartilhados.

O comando amplo `RMDir /r "$INSTDIR"` não será aceito como estratégia final.

## 11. Segurança da cadeia de suprimentos

- Locks de release deverão conter versões exatas e hashes.
- Instalações de release usarão verificação obrigatória de hashes.
- Dependências recém-publicadas respeitarão período de resfriamento, salvo atualização
  de segurança explicitamente revisada.
- GitHub Actions serão fixadas por SHA completo, não apenas por tags mutáveis.
- Permissões do workflow serão mínimas e o job de build não manterá permissão de
  publicação durante a instalação de dependências.
- Build e publicação serão jobs separados; publicação consumirá artefato já validado.
- Cada release terá SHA-256, SBOM e atestação de proveniência.
- Executável e instalador deverão receber assinatura Authenticode antes de a release
  ser marcada como recomendada.
- Componentes opcionais terão manifesto assinado ou atestado, hashes e compatibilidade
  exata com a versão do Core.
- O pipeline bloqueará publicação se `pip-audit`, CodeQL, testes, verificação de
  licença, Defender ou validação do bundle falharem.

## 12. Requisitos funcionais

- **RF-01:** instalar e abrir o Core sem rede e sem baixar modelos.
- **RF-02:** não conter CUDA, Torch ou modelos no instalador Core.
- **RF-03:** exigir consentimento antes de todo download de modelo ou componente.
- **RF-04:** exibir tamanho, origem, finalidade e espaço necessário antes do download.
- **RF-05:** permitir cancelar e retomar downloads sem corromper a instalação.
- **RF-06:** validar SHA-256 e compatibilidade antes de ativar conteúdo baixado.
- **RF-07:** manter o Core funcional após falha de download, extração ou ativação.
- **RF-08:** oferecer modelos Whisper por perfil e baixar somente o escolhido.
- **RF-09:** usar `device="auto"` e `compute_type="auto"` como padrões de instalação
  limpa.
- **RF-10:** priorizar automaticamente CUDA em hardware elegível e recuar para CPU em
  qualquer incompatibilidade.
- **RF-11:** incluir o pacote CUDA no preparo somente depois de detectar GPU compatível
  e mostrar seu tamanho no plano confirmado.
- **RF-12:** nunca baixar CUDA em máquina sem NVIDIA compatível.
- **RF-13:** permitir forçar CPU apenas como opção avançada de diagnóstico.
- **RF-14:** não instalar driver NVIDIA.
- **RF-15:** substituir Torch/Silero por solução leve ou componente opcional.
- **RF-16:** mostrar botão de reiniciar o QuantumScribe somente quando necessário.
- **RF-17:** aplicar componentes sem reiniciar o Windows.
- **RF-18:** permitir remover componentes e modelos opcionais com cálculo de espaço.
- **RF-19:** remover toda a função pública de backup e restauração.
- **RF-20:** preservar backups antigos sem continuar gerenciando-os.
- **RF-21:** desinstalar sem remover arquivos alheios ao produto.
- **RF-22:** funcionar em CPU quando nenhum componente opcional estiver instalado.
- **RF-23:** não manter conexão de rede em repouso nem enviar telemetria.
- **RF-24:** registrar localmente apenas eventos técnicos sem conteúdo de áudio ou
  transcrição, salvo funções já explicitamente escolhidas pelo usuário.

## 13. Requisitos não funcionais

### Desempenho e tamanho

- Instalador Core alvo: **até 250 MB**.
- Tamanho instalado do Core, sem modelos: **até 600 MB**.
- Redução mínima de 60% em relação ao instalador universal 2.1.26.
- Inicialização até a bandeja em até 3 segundos em máquina de referência, sem carregar
  modelo.
- Nenhum import de Torch, SciPy ou Matplotlib durante a inicialização do Core.

### Confiabilidade

- Downloads atômicos, retomáveis e verificáveis.
- Falha segura com retorno automático ao CPU.
- Configuração desconhecida ou componente incompatível não poderá impedir a abertura
  da tela de recuperação.
- A atualização nunca apagará modelos ou dados do usuário sem consentimento.

### Privacidade

- Áudio e transcrição permanecem locais.
- Sem telemetria própria.
- Rede somente para ações visíveis e consentidas.
- Logs não armazenam áudio, texto transcrito, tokens ou caminhos sensíveis completos.

### Acessibilidade e clareza

- Botões descrevem a ação concreta: baixar, instalar, remover ou reiniciar o app.
- Nenhum toggle pesado inicia download sem confirmação.
- Progresso, erro e espaço em disco usam linguagem simples em português brasileiro.

## 14. Métricas de sucesso

- Pelo menos 80% dos usuários CPU conseguem instalar sem baixar o pacote CUDA.
- Zero downloads automáticos antes do primeiro consentimento.
- 100% das instalações limpas usam modo `auto` por padrão.
- 100% das máquinas NVIDIA elegíveis priorizam GPU após o preparo.
- 100% das máquinas sem NVIDIA evitam o download do componente CUDA.
- Falha de CUDA recua para CPU sem perda da gravação em andamento sempre que a
  arquitetura do transcritor permitir repetição segura.
- Zero reinicializações do Windows solicitadas pelo QuantumScribe.
- Zero referências de backup na UI pública.
- Redução do instalador principal para no máximo 250 MB.
- Zero alertas abertos críticos/altos de dependências na publicação.
- Zero arquivos fora do manifesto removidos em testes de atualização/desinstalação.
- Taxa de recuperação de download interrompido de 100% nos testes automatizados.

## 15. Migração da 2.1.x

1. Preservar `config.json`, modelos, diário, notas, histórico e logs compatíveis.
2. Remover o bundle antigo `_internal` somente após validar o diretório de instalação.
3. Instalar o novo Core CPU.
4. Preservar overrides explícitos antigos; configurações novas e valores inválidos
   convergem para `auto`.
5. Detectar preferências antigas de CUDA, streaming neural e redução de ruído.
6. Se uma máquina elegível ainda não tiver o componente CUDA, incluí-lo no próximo
   plano de preparo confirmado; até lá, usar CPU.
7. Se outro componente correspondente não existir, manter a preferência desativada e
   explicar como instalá-lo; não baixar automaticamente.
8. Manter modelos Whisper já existentes e reconhecê-los sem novo download.
9. Ignorar backups antigos sem apagá-los.
10. Remover configurações obsoletas apenas depois de uma migração versionada e testada.

## 16. Plano de implementação

### Fase 1 — Core mínimo e remoção de backup

- remover código, UI, testes e documentação de backup;
- auditar imports e dependências diretas;
- separar build/teste/runtime;
- retirar CUDA, Torch, Silero, noisereduce e SciPy do Core;
- manter fallback CPU e Energy VAD;
- gerar e medir instalador Core.

### Fase 2 — Onboarding e modelos consentidos

- impedir download automático no primeiro start;
- criar seleção de perfil de modelo;
- exibir tamanhos a partir de manifesto;
- implementar download retomável e remoção segura de modelos;
- reutilizar modelos já presentes.

### Fase 3 — Gerenciador de componentes

- criar formato de manifesto e diretórios versionados;
- implementar download, hash, extração segura e ativação;
- criar cards de recursos opcionais;
- implementar reinício controlado do aplicativo;
- implementar remoção e rollback.

### Fase 4 — CUDA e recursos avançados

- publicar componente CUDA mínimo;
- validar fallback em PC sem NVIDIA;
- substituir Silero/Torch por ONNX ou retirar o recurso;
- avaliar redução de ruído por benchmark antes de criar componente;
- manter Mini-LLM dependente de ação explícita.

### Fase 5 — Instalador e desinstalador seguros

- fixar caminho por usuário;
- remover seleção de diretório;
- adicionar marcador e manifesto de propriedade;
- substituir remoção recursiva ampla;
- testar atualização, rollback e desinstalação adulterada.

### Fase 6 — Release endurecida

- gerar locks com hashes;
- fixar Actions por SHA;
- separar build de publicação;
- gerar SBOM e atestação;
- assinar executáveis;
- publicar primeiro o instalador Core e componentes separados.

## 17. Impacto esperado por arquivo

| Área | Alteração esperada |
| --- | --- |
| `localwhisper/backup.py` | remover |
| `localwhisper/settings_ui.py` | remover backup; adicionar onboarding e componentes |
| `localwhisper/config.py` | novas preferências de componentes e migração versionada |
| `localwhisper/model_manager.py` | consentimento, manifesto, progresso e remoção segura |
| `localwhisper/stream_transcriber.py` | fallback leve; eliminar dependência obrigatória de Torch |
| `localwhisper/audio_enhancer.py` | manter DSP leve; retirar dependências pesadas do Core |
| `localwhisper/hardware.py` | detectar componentes CUDA externos e compatíveis |
| `localwhisper/app.py` | orquestrar instalação, pending restart e reinício seguro |
| `QuantumScribe.spec` | coletar apenas Core; componentes fora do bundle principal |
| `requirements-*.txt/lock` | separar perfis e adicionar hashes |
| `build.ps1` | builds limpos e separados por artefato |
| `installer/QuantumScribe.nsi` | caminho fixo e desinstalação por manifesto |
| `.github/workflows/*.yml` | SHA completo, jobs separados, SBOM, atestação e assinatura |
| `README.md`, `PRIVACY.md`, `SECURITY.md` | refletir downloads consentidos e ausência de backup |
| `scripts/capture_docs_screenshots.py` | remover mocks e screenshot de backup |
| `tests/test_backup.py` | remover; substituir por testes de instalação/desinstalação |

## 18. Critérios de aceite

### Instalação limpa

- [ ] Instalador Core tem no máximo 250 MB.
- [ ] Instala sem administrador em caminho fixo por usuário.
- [ ] Abre offline sem erro e sem iniciar download.
- [ ] Não contém diretórios `nvidia`, `torch` ou modelos.
- [ ] Não cria serviço, tarefa agendada, firewall ou inicialização automática.

### Primeiro modelo

- [ ] Usuário vê opções e tamanhos antes de baixar.
- [ ] Nenhum modelo é pré-selecionado de forma que inicie download sozinho.
- [ ] Somente o modelo confirmado é baixado.
- [ ] Download interrompido é retomado e hash inválido é rejeitado.
- [ ] Modelo já instalado na 2.1.x é reutilizado.

### Componentes opcionais

- [ ] Instalação limpa salva `device=auto` e `compute_type=auto`.
- [ ] NVIDIA compatível é detectada sem escolha manual de GPU.
- [ ] O plano confirmado inclui CUDA e seu tamanho somente na máquina elegível.
- [ ] Máquina sem NVIDIA não faz requisição nem download do componente CUDA.
- [ ] Componente CUDA instalado faz a próxima inicialização escolher GPU.
- [ ] Falha no carregamento ou decode CUDA repete com CPU de forma segura.
- [ ] Override CPU permanece disponível apenas em configurações avançadas.
- [ ] CUDA não é oferecido em hardware inelegível.
- [ ] Habilitar recurso abre confirmação, não download silencioso.
- [ ] Componente inválido nunca é carregado.
- [ ] Falha mantém CPU funcional.
- [ ] Botão “Reiniciar QuantumScribe agora” aparece somente quando necessário.
- [ ] Reinício aplica ou reverte o componente sem reiniciar o Windows.
- [ ] Remoção informa e libera o espaço esperado.

### Backup

- [ ] Não existe menu, card, botão ou import de backup.
- [ ] `localwhisper/backup.py` e testes exclusivos foram removidos.
- [ ] Screenshots e documentação não apresentam backup como recurso.
- [ ] ZIPs legados não são apagados automaticamente.

### Desinstalação

- [ ] Caminho adulterado faz o desinstalador abortar.
- [ ] Arquivo alheio colocado na pasta não é removido sem regra explícita.
- [ ] Diretório compartilhado nunca é apagado recursivamente.
- [ ] Dados pessoais são preservados por padrão.

### Release

- [ ] Testes, lint, auditoria, CodeQL e varredura antimalware passam.
- [ ] Locks e componentes têm hashes verificados.
- [ ] Actions estão fixadas por SHA completo.
- [ ] Release contém SBOM, checksums e atestação.
- [ ] Instalador e executável possuem assinatura válida.

## 19. Riscos e mitigação

| Risco | Mitigação |
| --- | --- |
| Complexidade do gerenciador de componentes | formato pequeno, componentes fechados e versionados; sem gerenciador genérico |
| Falha após instalar DLL nativa | diretórios versionados, ativação após restart e rollback automático |
| CUDA incompatível | detecção prévia, matriz de compatibilidade e fallback CPU |
| Usuário interpretar toggle como ação imediata | confirmação com tamanho e botão explícito de download |
| Fragmentação de suporte | Core sempre suportado; componentes limitados e identificáveis em diagnóstico |
| Modelo ou componente comprometido | origem fixa, hash, assinatura/atestação e bloqueio por versão |
| Migração apagar dados | nenhuma limpeza automática; testes com instalação 2.1.x real |
| Redução de qualidade sem Torch/noisereduce | benchmark antes/depois e fallback leve documentado |

## 20. Resultado esperado

O QuantumScribe 2.2.0 será um aplicativo local de ditado que instala rápido, inicia
sem downloads surpresa e funciona em CPU com o mínimo de dependências. O usuário só
receberá CUDA, modelos maiores ou processamento avançado quando escolher claramente
o recurso e aceitar seu custo de download e disco.

O produto deixará de expor backup e restauração, reduzirá substancialmente a
superfície de ataque e evitará exclusões amplas durante a desinstalação. Recursos
opcionais poderão evoluir sem inflar o instalador principal nem comprometer a
estabilidade do Core.
