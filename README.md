<div align="center">
  <img src="localwhisper/assets/icon.png" width="112" alt="Ícone do QuantumScribe">
  <h1>QuantumScribe</h1>
  <p><strong>Ditado por voz local, rápido e fiel ao que você falou.</strong></p>
  <p>Windows · faster-whisper · CPU ou NVIDIA CUDA · Português do Brasil</p>

  [![Tests](https://github.com/Natanmelquiades/QuantumScribe/actions/workflows/tests.yml/badge.svg)](https://github.com/Natanmelquiades/QuantumScribe/actions/workflows/tests.yml)
  [![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f.svg)](LICENSE)
  [![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-blue.svg)](https://www.python.org/)
  [![Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)](https://www.microsoft.com/windows)

  [**Baixar para Windows**](https://github.com/Natanmelquiades/QuantumScribe/releases/latest)
  · [Ver formas de instalação](#baixar-e-instalar)
  · [Como usar](#como-usar)
</div>

---

O **QuantumScribe** transforma sua voz em texto diretamente no campo que estiver
focado. O reconhecimento roda no seu computador com
[faster-whisper](https://github.com/SYSTRAN/faster-whisper), preserva a fala em modo
literal e usa pausas e construções interrogativas para melhorar a pontuação sem
trocar palavras.

> **English:** QuantumScribe is a local-first Windows dictation app powered by
> faster-whisper. It offers global shortcuts, literal transcription, conservative
> punctuation, auto-paste, optional CUDA acceleration and an offline second brain.

![Painel principal de ditado e IA](docs/assets/screenshots/01-ditado-ia.png)

## Destaques

- **Local-first:** o áudio é transcrito localmente depois que o modelo é baixado.
- **Transcrição literal:** repetições, hesitações e palavras coloquiais podem ser
  preservadas sem uma LLM reescrever sua mensagem.
- **Pontuação conservadora:** detecta perguntas e pausas sem alterar o vocabulário.
- **Atalhos globais:** dite em navegadores, editores, chats e ferramentas de trabalho.
- **Auto-paste e autoenvio:** cola no cursor e, opcionalmente, pressiona Enter.
- **Tradução sob demanda:** produz texto em inglês usando o próprio Whisper.
- **CPU ou NVIDIA CUDA:** detecta automaticamente a GPU e usa CPU quando CUDA não estiver disponível.
- **Quantum Brain:** transforma ditados em notas Markdown locais e sínteses offline.
- **Configuração visual:** modelos, áudio, atalhos, HUD, backups e histórico em um só painel.

## Interface

<table>
  <tr>
    <td><img src="docs/assets/screenshots/01-ditado-ia.png" alt="Configurações de ditado, Whisper e pontuação"></td>
    <td><img src="docs/assets/screenshots/02-preferencias-atalhos.png" alt="Preferências, atalhos e aparência do HUD"></td>
  </tr>
  <tr>
    <td><img src="docs/assets/screenshots/03-sistema-notas-backups.png" alt="Configurações do Quantum Brain e backups"></td>
    <td><img src="docs/assets/screenshots/04-sobre.png" alt="Informações da versão e ambiente do QuantumScribe"></td>
  </tr>
</table>

<p align="center">
  <img src="docs/assets/screenshots/05-hud-gravando.png" width="31%" alt="HUD do QuantumScribe gravando">
  <img src="docs/assets/screenshots/06-hud-processando.png" width="31%" alt="HUD do QuantumScribe processando">
  <img src="docs/assets/screenshots/07-menu-bandeja.png" width="31%" alt="Menu do QuantumScribe na bandeja do Windows">
</p>

## Requisitos

- Windows 10 ou Windows 11;
- Python 3.11 a 3.13 para executar pelo código-fonte;
- microfone reconhecido pelo Windows;
- conexão à internet apenas para instalar dependências e baixar modelos;
- espaço livre para o ambiente Python e o modelo escolhido;
- GPU NVIDIA opcional para aceleração CUDA.

Modelos maiores normalmente oferecem mais qualidade, mas consomem mais disco, RAM,
VRAM e tempo de inicialização no primeiro ditado.

| Perfil | Modelo | Indicação |
|---|---|---|
| Super leve | `tiny` | máquinas simples e testes rápidos |
| Leve | `base` | ditado curto com baixo consumo |
| Equilibrado | `small` | alternativa mais leve para máquinas simples |
| Pro | `medium` | padrão; maior qualidade para uso diário e termos técnicos |
| Ultra | `large-v3` | máxima qualidade em hardware mais forte |

## Baixar e instalar

### Escolha a forma adequada

| Forma | Para quem | O que baixar |
|---|---|---|
| **Instalador Windows** — recomendada | quem quer instalar e abrir como um programa normal | `QuantumScribe-Setup-<versão>-Windows-x64.exe` na [release mais recente](https://github.com/Natanmelquiades/QuantumScribe/releases/latest) |
| **Versão portátil** | desenvolvedores e testes sem instalação | `QuantumScribe-Windows-x64.zip` na [release mais recente](https://github.com/Natanmelquiades/QuantumScribe/releases/latest) |
| **Código-fonte — CPU** | desenvolvimento e contribuição | clone com Git ou [baixe o código em ZIP](https://github.com/Natanmelquiades/QuantumScribe/archive/refs/heads/main.zip) |
| **Código-fonte — NVIDIA CUDA** | desenvolvimento com GPU NVIDIA compatível | o mesmo código-fonte, iniciado com o perfil CUDA |

> [!IMPORTANT]
> Os arquivos automáticos **Source code (zip)** e **Source code (tar.gz)** mostrados
> no fim de cada Release contêm somente o código-fonte. Eles não são o aplicativo
> pronto. Para instalar normalmente, escolha o arquivo que começa com
> `QuantumScribe-Setup-`.

### Opção 1 — instalador Windows, recomendada

1. Abra a [release mais recente](https://github.com/Natanmelquiades/QuantumScribe/releases/latest).
2. Na seção **Assets**, clique em
   `QuantumScribe-Setup-<versão>-Windows-x64.exe`.
3. Execute o arquivo baixado e avance pelo assistente.
4. Mantenha marcado **Atalho na área de trabalho** se quiser abrir pelo desktop.
5. Depois da instalação, abra **QuantumScribe** pelo menu Iniciar ou pelo atalho.

O instalador:

- instala somente para o usuário atual, sem exigir acesso de administrador;
- inclui aceleração NVIDIA CUDA, mas continua funcionando automaticamente em máquinas somente CPU;
- baixa automaticamente o modelo Pro (`medium`, cerca de 1,5 GB) na primeira execução e retoma o download se a conexão cair;
- adiciona o QuantumScribe ao menu Iniciar;
- oferece um atalho opcional na área de trabalho;
- aparece normalmente em **Configurações > Aplicativos instalados** para desinstalação.

> [!WARNING]
> Os builds atuais ainda não possuem assinatura digital comercial. O Windows
> SmartScreen pode exibir um aviso. Confirme que o arquivo veio da página oficial de
> Releases. Se necessário, clique em **Mais informações > Executar assim mesmo**.
> O hash pode ser conferido no `SHA256SUMS.txt` da mesma Release.

Modelos Whisper não são empacotados no instalador. Eles continuam sendo baixados sob
demanda e armazenados em `%LOCALAPPDATA%\QuantumScribe`.

### Opção 2 — versão portátil

1. Abra a [release mais recente](https://github.com/Natanmelquiades/QuantumScribe/releases/latest).
2. Em **Assets**, baixe `QuantumScribe-Windows-x64.zip`.
3. Clique com o botão direito no ZIP e selecione **Extrair tudo**.
4. Abra a pasta extraída e execute `QuantumScribe.exe`.

Não execute o programa diretamente de dentro do ZIP e não mova somente o `.exe`: a
pasta `_internal` contém bibliotecas necessárias para o aplicativo funcionar.

### Opção 3 — código-fonte para desenvolvimento

#### Com Git — perfil CPU recomendado

```powershell
git clone https://github.com/Natanmelquiades/QuantumScribe.git
cd QuantumScribe
.\run.ps1
```

Na primeira execução, o script cria `.venv`, instala o perfil CPU e inicia o app. Nas
execuções seguintes, ele abre diretamente sem reinstalar tudo.

#### Sem Git — código-fonte em ZIP

1. [Baixe o código-fonte da branch `main`](https://github.com/Natanmelquiades/QuantumScribe/archive/refs/heads/main.zip).
2. Extraia o ZIP.
3. Abra o PowerShell dentro da pasta extraída.
4. Execute:

```powershell
.\run.ps1
```

Essa opção requer Python 3.11, 3.12 ou 3.13 instalado no computador.

#### Perfil NVIDIA CUDA

```powershell
.\run.ps1 -Setup -Cuda
```

> [!IMPORTANT]
> O perfil CUDA instala pacotes grandes. Verifique espaço em disco e compatibilidade
> do driver NVIDIA. Se CUDA falhar, o transcritor tenta recuar para CPU.

Depois que o ambiente estiver preparado, `Iniciar.bat` continua disponível como um
atalho de conveniência para quem estiver trabalhando diretamente no código-fonte.

### Desinstalação

Remova o QuantumScribe pela tela de aplicativos instalados do Windows. Configurações,
modelos, notas e histórico em `%LOCALAPPDATA%\QuantumScribe` são preservados para
evitar perda acidental; apague essa pasta manualmente apenas se também quiser remover
seus dados locais.

## Como usar

1. Abra o QuantumScribe; ele ficará na bandeja do Windows.
2. Posicione o cursor no campo de texto desejado.
3. Pressione `Ctrl+Space` para começar a gravar.
4. Pressione `Ctrl+Space` novamente para concluir.
5. Aguarde a transcrição local e a inserção automática.

Na primeira execução, o modelo Pro é baixado em segundo plano. O modelo é carregado
na memória somente no primeiro ditado para que a bandeja e as configurações abram
rapidamente. O primeiro processamento da sessão pode demorar mais; os seguintes
reutilizam o modelo em memória.

### Atalhos padrão

| Atalho | Ação |
|---|---|
| `Ctrl+Space` | iniciar ou concluir ditado normal |
| `Ctrl+Alt+Space` | ditar e traduzir para inglês |
| `Ctrl+Shift+Space` | ditar, colar e enviar |
| `Ctrl+Shift+D` | salvar ditado no Quantum Brain |
| `Esc` | cancelar gravação/processamento |

Todos os atalhos principais podem ser alterados nas configurações.

## Privacidade

A transcrição normal acontece localmente. O aplicativo acessa o Hugging Face quando
você solicita o download de um modelo. Não há telemetria própria no código.

O QuantumScribe mantém configurações, modelos, diário, notas, caches e logs em:

```text
%LOCALAPPDATA%\QuantumScribe
```

Transcrições e backups podem conter informações pessoais. Não publique esses
arquivos em issues. Leia [PRIVACY.md](PRIVACY.md) para conhecer todos os dados locais
e as conexões de rede.

## Configuração

Use **Configurações** no menu da bandeja. O arquivo persistido fica em
`%LOCALAPPDATA%\QuantumScribe\config.json`. Um exemplo seguro está em
[config.example.json](config.example.json).

Opções importantes:

- `literal_mode`: preserva as palavras sem pós-reescrita;
- `punctuation_assist`: melhora sinais terminais e pausas;
- `preload_model`: se `false`, carrega o modelo no primeiro ditado;
- `auto_download_model`: baixa ou retoma automaticamente o modelo escolhido;
- `device`: `auto` (recomendado), `cpu` ou `cuda`; mesmo com preferência CUDA, o app recua preventivamente para CPU se necessário;
- `auto_paste`: insere o resultado no campo capturado;
- `use_llm_rewriter`: habilita reescrita opcional — desligada por padrão.

## Desenvolvimento

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check localwhisper tests
```

Os testes não precisam de microfone, GPU ou modelo Whisper baixado.

### Arquitetura resumida

```text
hotkeys/tray → app.py → audio.py → transcriber.py → punctuation/cleaner
                    ↘ HUD/UI               ↘ clipboard + auto-paste
                    ↘ diary / Quantum Brain / backups
```

Os módulos principais estão documentados no próprio código. Consulte
[CONTRIBUTING.md](CONTRIBUTING.md) antes de enviar mudanças.

## Build para Windows

```powershell
.\build.ps1                    # pasta portátil, perfil CPU
.\build.ps1 -Cuda              # pasta portátil adaptativa CPU/CUDA
.\build.ps1 -Cuda -Installer   # instalador universal recomendado para distribuição
.\build.ps1 -Installer         # instalador menor, somente CPU
```

O build usa os lockfiles reproduzíveis dentro de uma `.venv-build` isolada e gera
`dist\QuantumScribe\`. Distribua a pasta inteira compactada, não somente o `.exe`,
porque as DLLs e bibliotecas fazem parte do aplicativo. Para gerar o instalador também
é necessário ter o
[NSIS](https://nsis.sourceforge.io/) instalado.

Tags `v*` acionam o workflow de release, que testa o código, produz o ZIP portátil e o
instalador, calcula os hashes SHA-256 e anexa os três arquivos à GitHub Release.

## Solução de problemas

- **A bandeja não aparece:** confira o menu de ícones ocultos do Windows e o
  `%LOCALAPPDATA%\QuantumScribe\app.log`.
- **Atalho não responde:** verifique se outro programa registrou a mesma combinação.
- **Primeiro ditado demora:** aguarde o download inicial e a carga do modelo em RAM/VRAM; as próximas transcrições reutilizam o modelo.
- **CUDA falha:** atualize o driver ou selecione CPU com `compute_type=int8`.
- **Modelo não baixa:** confira conexão, cerca de 2 GB livres e permissões da pasta local; ao reabrir, o download continua de onde parou.
- **Texto não é colado:** confirme que o campo original ainda existe e que
  `auto_paste` está habilitado.

Ao relatar um bug, não anexe configurações, áudios ou transcrições pessoais. Consulte
[SECURITY.md](SECURITY.md).

## Roadmap

- assinatura digital dos executáveis e do instalador Windows;
- benchmarks reproduzíveis de modelos e hardware;
- mais testes de integração de áudio e hotkeys;
- internacionalização da interface;
- perfis de configuração exportáveis sem dados pessoais.

## Licença

Código disponibilizado sob a [licença MIT](LICENSE). Dependências e modelos têm
licenças próprias; consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

<div align="center">
  Feito por <a href="https://github.com/Natanmelquiades">Natan Melquiades</a>.
  Se o QuantumScribe for útil, deixe uma ⭐ no repositório.
</div>
