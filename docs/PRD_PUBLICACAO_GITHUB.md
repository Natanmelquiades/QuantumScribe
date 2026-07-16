# PRD — Publicação segura do QuantumScribe no GitHub

**Status:** pronto para execução após aprovação dos gates de decisão

**Responsável pelo produto:** Natan Melquiades

**Conta GitHub confirmada:** `Natanmelquiades`

**Slug proposto:** `Natanmelquiades/QuantumScribe`

**Versão do PRD:** 2.1.23
**Data da auditoria:** 16/07/2026

## 1. Resumo executivo

O QuantumScribe ainda não é um repositório Git e não possui remoto. A conta
`Natanmelquiades` está autenticada no GitHub CLI com acesso suficiente para criar e
publicar repositórios. O nome `Natanmelquiades/QuantumScribe` não estava ocupado no
momento desta auditoria.

O código-fonte publicável é pequeno, mas a pasta de trabalho contém aproximadamente
3,56 GB de ambiente virtual, builds, testes temporários e artefatos locais. Esses
itens não podem entrar no histórico. O `.gitignore` atual cobre parte deles, mas é
insuficiente para uma publicação segura e também ignora todos os arquivos `.spec`,
inclusive o `QuantumScribe.spec` necessário para compilar o aplicativo.

Não foram encontradas credenciais reais gravadas diretamente no código auditado.
Existem campos destinados a receber chaves e os backups locais podem conter dados
do usuário. Portanto, backups, configurações reais, diários, logs, áudios, modelos e
dados de `%LOCALAPPDATA%\QuantumScribe` devem permanecer fora do Git.

Recomendação: criar o repositório inicialmente como **privado**, enviar somente um
manifesto revisado, conferir o resultado no GitHub e mudar para público apenas após
aprovação explícita da licença, da documentação e da política de distribuição.

## 2. Objetivo

Preparar e publicar um repositório profissional, seguro e reproduzível do
QuantumScribe, contendo:

- código-fonte e testes;
- documentação de instalação, uso, privacidade e desenvolvimento;
- descrição, tópicos, ícone e imagem social do projeto;
- capturas sanitizadas da interface, configurações, HUD e menu da bandeja;
- automação mínima de testes;
- processo de releases para distribuir o aplicativo sem versionar binários pesados;
- histórico inicial sem dados pessoais, modelos, builds ou segredos.

## 3. Fora do escopo

- enviar modelos Whisper, Torch, CUDA ou pesos de Mini-LLM ao repositório;
- publicar diários, transcrições, prompts pessoais, backups ou configurações reais;
- prometer suporte a macOS/Linux — o aplicativo atual depende de Win32;
- publicar instalador ou executável antes de validar o build em máquina limpa;
- tornar o repositório público sem uma decisão humana sobre licença.

## 4. Estado atual auditado

### 4.1 Pontos positivos

- 27 testes automatizados passando na versão auditada;
- código-fonte sem arquivos individuais grandes;
- configuração de exemplo sem chave preenchida;
- dependências separadas entre CPU e CUDA;
- changelog existente;
- ícone PNG existente em `localwhisper/assets/icon.png`;
- backup e restauração possuem teste contra path traversal;
- modelos e dados do usuário ficam fora da pasta principal do código em operação normal.

### 4.2 Bloqueadores obrigatórios

1. **`.gitignore` incompleto**
   - Não ignora `backups/`, `temp_test/`, `.pytest_cache/`, logs, `.env`, áudios,
     configurações reais, chaves, arquivos de IDE e caches adicionais.
   - A regra `*.spec` exclui também `QuantumScribe.spec`, que deve ser versionado.

2. **Licença ausente**
   - Sem `LICENSE`, o copyright padrão mantém todos os direitos e terceiros não têm
     autorização automática para copiar, modificar ou distribuir o código.
   - A escolha entre código proprietário, source-available ou open source é um gate.

3. **README desatualizado**
   - Ainda descreve a biblioteca `keyboard`, embora o projeto use hotkeys Win32.
   - A tela “Sobre” menciona PyAudio, enquanto a captura usa `sounddevice`.
   - Não documenta adequadamente modo literal, pontuação inteligente, Quantum Brain,
     atalhos adicionais, requisitos de disco, primeiro download e carregamento sob demanda.
   - A afirmação de privacidade precisa explicar downloads do Hugging Face e os dados
     locais persistidos, em vez de usar uma promessa absoluta.

4. **Reprodutibilidade insuficiente**
   - As dependências usam intervalos amplos e não existe lockfile.
   - PyInstaller está misturado às dependências de execução.
   - Não há metadados `pyproject.toml`, matriz de Python suportada nem requisitos
     mínimos de hardware formalizados.

5. **Documentos comunitários e de segurança ausentes**
   - Faltam `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` e templates de issue.

6. **Material visual ausente**
   - Existe somente o ícone; não há screenshots sanitizados nem social preview.

7. **Distribuição não definida**
   - `dist/` possui centenas de MB e não deve ir para o Git.
   - O build precisa ser compactado, testado e anexado a uma GitHub Release.

### 4.3 Riscos legais e de terceiros

- Definir a licença do QuantumScribe antes de abrir o código.
- Gerar `THIRD_PARTY_NOTICES.md` com as licenças das dependências diretas e validar as
  obrigações de redistribuição do bundle.
- Revisar especialmente `pystray` (LGPLv3), PyInstaller (GPL com exceção), pacotes
  NVIDIA proprietários e as licenças dos modelos distribuídos ou sugeridos.
- Modelos não devem ser incorporados ao repositório ou release sem revisão da licença.
- Revisar a frase “Inspirado no SuperWhisper” e evitar qualquer aparência de afiliação,
  endosso ou uso indevido de marca.

Este PRD não substitui aconselhamento jurídico.

## 5. Gates de decisão do proprietário

Nenhuma publicação pública deve acontecer antes destas quatro decisões:

| Gate | Decisão necessária | Recomendação |
|---|---|---|
| Visibilidade | privado ou público | privado no primeiro envio |
| Licença | proprietário, source-available ou open source | decidir após revisar dependências |
| Distribuição | somente código ou código + release Windows | código primeiro; release depois do smoke test |
| Nome | `QuantumScribe` ou variação | `QuantumScribe`, atualmente disponível |

## 6. Requisitos funcionais da publicação

### RF-01 — Manifesto seguro de arquivos

O primeiro commit deve incluir apenas arquivos explicitamente aprovados. O manifesto
esperado inclui código Python, testes, documentação, scripts de instalação/build,
requirements, `QuantumScribe.spec`, ícone e arquivos `.github`.

Devem ser ignorados:

```gitignore
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
build/
dist/
backups/
temp_test/
models/
*.log
*.wav
*.zip
.env
.env.*
!.env.example
config.json
**/config.json
!config.example.json
*.pem
*.pfx
*.key
.idea/
.vscode/
LocalWhisper.spec.bak
```

`QuantumScribe.spec` deve continuar versionado.

### RF-02 — Documentação principal

Reescrever o `README.md` com:

1. logo, título, proposta de valor e badges reais;
2. screenshot principal do painel de configurações;
3. recursos: ditado, modo literal, pontuação, tradução, autoenvio e Quantum Brain;
4. requisitos: Windows, Python suportado, microfone, RAM, disco e GPU opcional;
5. instalação rápida CPU e CUDA em caminhos separados;
6. tabela de modelos e consumo aproximado;
7. atalhos padrão;
8. explicação do primeiro download e do carregamento no primeiro ditado;
9. diretórios e dados gravados localmente;
10. privacidade e conexões de rede usadas para baixar modelos;
11. compilação, testes, troubleshooting e desinstalação;
12. link para changelog, segurança, contribuição, licença e releases.

### RF-03 — Descrição e metadados do GitHub

**Descrição proposta:**

> Ditado por voz local para Windows com faster-whisper, transcrição literal,
> pontuação inteligente, atalhos globais, auto-paste e segundo cérebro offline.

**Tópicos propostos:**

`speech-to-text`, `whisper`, `faster-whisper`, `windows`, `offline`, `dictation`,
`portuguese`, `cuda`, `tkinter`, `privacy`.

Configurar também:

- Website: deixar vazio até existir uma landing page oficial;
- Issues: habilitado;
- Discussions: opcional;
- Wiki: desabilitada inicialmente, mantendo documentação em `docs/`;
- Social preview: PNG de 1280 × 640 sem dados reais do usuário.

### RF-04 — Galeria de screenshots

Criar `docs/assets/screenshots/` com:

| Arquivo | Conteúdo | Cuidados |
|---|---|---|
| `01-ditado-ia.png` | painel Ditado & IA | prompt e dicionário fictícios |
| `02-preferencias-atalhos.png` | preferências e atalhos | nenhum nome de dispositivo pessoal |
| `03-sistema-notas-backups.png` | Quantum Brain e backups | lista de notas/backups fictícia ou vazia |
| `04-sobre.png` | versão e informações do app | corrigir referência a PyAudio antes |
| `05-hud-gravando.png` | HUD durante gravação | fundo neutro, sem outro app pessoal |
| `06-hud-processando.png` | HUD processando | nenhum texto ditado visível |
| `07-menu-bandeja.png` | menu do ícone da bandeja | ocultar relógio/notificações pessoais |

Padrão de captura:

- usar um `%LOCALAPPDATA%` temporário e configuração demonstrativa;
- não usar o `config.json`, diário ou backups reais;
- PNG, escala nativa, texto legível e preferencialmente menos de 1 MB por imagem;
- remover EXIF/metadados;
- fornecer texto alternativo descritivo no README;
- usar caminhos relativos, por exemplo
  `![Painel de ditado e IA](docs/assets/screenshots/01-ditado-ia.png)`.

### RF-05 — Segurança e privacidade

- Criar `SECURITY.md` com canal de relato privado e versões suportadas.
- Documentar que transcrições, cache, Quantum Brain, configurações e áudio emergencial
  são armazenados localmente.
- Explicar quando o áudio emergencial é criado e removido.
- Não incluir endereços pessoais de e-mail sem aprovação; preferir GitHub Issues ou
  Security Advisories.
- Executar varredura de segredos antes do primeiro commit e novamente no conteúdo staged.
- Nunca contornar alertas de push protection sem revisar o achado.
- Executar auditoria de dependências e registrar exceções justificadas.

### RF-06 — Qualidade e CI

Criar workflow Windows em `.github/workflows/tests.yml` porque o projeto usa Win32:

- runner `windows-latest`;
- versão de Python explicitamente suportada;
- instalação de dependências de teste mínimas;
- `python -m compileall`;
- `pytest -q`;
- lint após definir e fixar a ferramenta no ambiente de desenvolvimento.

Separar dependências em runtime, desenvolvimento/teste e build. Criar lockfile ou
processo reproduzível equivalente para CPU e documentar o perfil CUDA separadamente.

### RF-07 — Releases

- Não versionar `dist/` nem executáveis no Git.
- Criar tag compatível com a versão do aplicativo.
- Produzir ZIP da pasta completa do PyInstaller.
- Testar em máquina/usuário limpo antes da publicação.
- Gerar `SHA256SUMS.txt`.
- Anexar ZIP e checksums à GitHub Release.
- Publicar notas baseadas no `CHANGELOG.md`.
- Informar que builds sem assinatura podem gerar alertas do Windows/antivírus.

O GitHub bloqueia arquivos normais acima de 100 MiB. Releases aceitam assets de até
2 GiB por arquivo; portanto, o bundle deve ser distribuído como release, não como
arquivo rastreado no repositório.

## 7. Plano de execução

### Fase 0 — Preservação

1. Criar backup completo e validar o ZIP.
2. Registrar a versão e o resultado dos testes.
3. Não apagar artefatos locais; excluí-los apenas do manifesto Git.

### Fase 1 — Higiene do repositório

1. Corrigir `.gitignore`.
2. Remover do manifesto logs vazios, `.bak`, caches e bytecode.
3. Manter `QuantumScribe.spec` rastreável.
4. Revisar nomes antigos `LocalWhisper` que ainda sejam visíveis ao usuário.
5. Garantir que nenhum arquivo de `%LOCALAPPDATA%` seja copiado para o projeto.

### Fase 2 — Documentação e legal

1. Aprovar licença.
2. Criar `LICENSE` ou aviso explícito de direitos reservados.
3. Criar `THIRD_PARTY_NOTICES.md`.
4. Reescrever README e atualizar `config.example.json`.
5. Criar `SECURITY.md`, `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md`.
6. Corrigir referências técnicas obsoletas na interface e documentação.

### Fase 3 — Imagens

1. Criar perfil demonstrativo isolado.
2. Capturar os sete cenários.
3. Inspecionar visualmente cada imagem em resolução original.
4. Remover metadados e verificar ausência de informações pessoais.
5. Inserir galeria e textos alternativos no README.
6. Criar social preview separado.

### Fase 4 — Engenharia e validação

1. Definir versões de Python suportadas.
2. Separar dependências e criar lock/reprodutibilidade.
3. Adicionar workflow Windows.
4. Rodar compilação, testes, lint, auditoria de dependências e scan de segredos.
5. Executar smoke test: iniciar, bandeja, configurações, gravação, transcrição,
   auto-paste, cancelamento e encerramento.

### Fase 5 — Primeiro commit e envio privado

Runbook proposto, somente após os gates:

```powershell
git init -b main
git add .
git status --short
git diff --cached --stat
git diff --cached
git commit -m "chore: publish QuantumScribe source"
gh repo create QuantumScribe --private --source=. --remote=origin --push
```

Antes do commit, validar com `git ls-files` que não aparecem `.venv`, `backups`,
`dist`, `temp_test`, logs, configs reais, modelos, áudios ou ZIPs.

### Fase 6 — Validação remota e possível abertura pública

1. Clonar o repositório privado em pasta temporária.
2. Confirmar que instalação e testes funcionam a partir do clone limpo.
3. Revisar README renderizado, links, imagens, licença e Actions.
4. Conferir alertas de segurança e dependências.
5. Somente após aprovação humana, alterar visibilidade para público.
6. Configurar descrição, tópicos, social preview e proteção da branch principal.

### Fase 7 — Primeira release

Executar apenas se a distribuição binária for aprovada. O release deve ser separado
do primeiro push do código para permitir correções sem publicar um binário prematuro.

## 8. Critérios de aceitação

- [ ] Backup completo criado e validado.
- [ ] Nenhum segredo, dado pessoal ou arquivo de usuário no staged/remote.
- [ ] Nenhum arquivo acima de 50 MiB no histórico Git comum.
- [ ] `.venv`, modelos, backups, builds e temporários ignorados.
- [ ] `QuantumScribe.spec` presente no repositório.
- [ ] README tecnicamente correto e com galeria sanitizada.
- [ ] Licença e avisos de terceiros aprovados.
- [ ] Documentos de segurança e contribuição presentes.
- [ ] Testes e compileall passando no Windows.
- [ ] Workflow CI verde.
- [ ] Clone privado limpo reproduz a instalação e os testes.
- [ ] Visibilidade pública aprovada explicitamente pelo proprietário.
- [ ] Release, se houver, contém ZIP completo, checksum e notas.

## 9. Evidências e fontes oficiais

- O GitHub recomenda que o README explique utilidade, início rápido, suporte e
  manutenção, e suporta imagens por caminhos relativos:
  https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- O GitHub bloqueia arquivos acima de 100 MiB e recomenda releases para binários:
  https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- Releases permitem empacotar software e aceitam assets individuais abaixo de 2 GiB:
  https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- Sem licença, aplicam-se os direitos autorais padrão; uma licença define permissões:
  https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- Push protection bloqueia credenciais detectadas antes que entrem no repositório:
  https://docs.github.com/en/code-security/concepts/secret-security/push-protection
- O GitHub recomenda `setup-python` para CI de projetos Python:
  https://docs.github.com/en/actions/tutorials/build-and-test-code/python

## 10. Resultado esperado

Um repositório GitHub profissional, leve e seguro, que apresente corretamente o
QuantumScribe, permita instalação e contribuição reproduzíveis e distribua builds
Windows por Releases, sem expor dados pessoais nem transformar o histórico Git em
armazenamento de modelos ou binários.
