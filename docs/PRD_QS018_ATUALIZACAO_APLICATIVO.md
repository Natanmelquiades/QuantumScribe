# PRD QS-018 — Verificação e atualização segura do aplicativo

**Status:** implementado na versão 2.2.13

**Prioridade preliminar:** P2 — Média

**Escopo da primeira versão:** aplicativo Windows instalado pelo pacote oficial.

## Objetivo

Permitir que a pessoa veja se existe uma versão mais recente do QuantumScribe e,
quando quiser, atualize somente o aplicativo de forma segura. Modelos, componentes
opcionais, configurações, transcrições e demais dados locais ficam fora do fluxo.

## Experiência proposta

- Exibir o botão `Verificar atualização` na página **Sobre** e, se aprovado no
  desenho, uma entrada equivalente no menu da bandeja.
- Consultar a última release pública final do repositório oficial em segundo
  plano, sem bloquear a interface.
- Quando a versão remota for maior que a instalada, informar versão e notas,
  oferecendo `Atualizar agora` e `Agora não`.
- Ao confirmar, baixar apenas o instalador Windows x64 correspondente, validar o
  SHA-256 publicado e iniciar a atualização após o fechamento controlado do app.
- Caso já esteja atualizado, mostrar uma confirmação simples, sem fazer download.

## Regras e segurança

1. Aceitar apenas releases públicas finais do repositório oficial; ignorar
   rascunhos e pré-releases.
2. Comparar versões numéricas compatíveis com o versionamento do produto; uma
   versão remota menor ou igual nunca deve ser instalada.
3. Baixar somente o asset
   `QuantumScribe-Setup-<versão>-Windows-x64.exe` por HTTPS de hosts permitidos.
4. Exigir um `SHA256SUMS.txt` da mesma release e interromper antes da execução
   se o hash não corresponder, faltar ou for inválido.
5. O processo de atualização deve encerrar o aplicativo antes de executar o
   instalador; não pode substituir arquivos em uso nem duplicar atualizações.
6. Nunca baixar, remover, atualizar ou migrar automaticamente modelos Whisper,
   componentes CUDA/Silero VAD, configurações, transcrições, backups ou dados
   do Quantum Brain.
7. Preservar o instalador baixado apenas durante a operação e informar erros de
   rede, integridade, permissão ou cancelamento com uma ação clara de retentativa.
8. A primeira versão não fará checagem silenciosa em segundo plano nem
   atualização sem confirmação explícita.

## Riscos e dependências

- O executável em uso não pode se substituir: será necessário um iniciador ou
  fluxo de encerramento confiável para executar o instalador depois da saída.
- A confiança depende da release e do checksum; assinatura Authenticode do
  instalador continua sendo uma melhoria complementar recomendada.
- Atualizações sobre versões antigas precisam de testes de preservação de dados
  e de recuperação quando o instalador falhar ou for cancelado.

## Critérios de aceite

- Com `2.2.11` instalada e uma release pública posterior, o botão informa a nova
  versão e oferece atualizar sem travar a janela.
- Após confirmação, somente o instalador da versão nova é baixado e seu SHA-256
  é validado antes da execução.
- Um hash incorreto, release ausente ou falha de rede não inicia nenhum arquivo
  e mostra um erro compreensível com possibilidade de tentar novamente.
- O instalador inicia somente após o app encerrar, e uma atualização preserva
  configurações, transcrições, modelos e componentes opcionais existentes.
- Sem atualização disponível, o aplicativo informa que já está na versão atual.
