# PRD QS-006 — Download resiliente do modelo Whisper

**Status:** proposta para validação
**Prioridade:** P1 — Alta
**Esforço preliminar:** G
**Relacionado a:** QS-005 — Reutilização de modelos existentes

## Contexto

O modelo Whisper é necessário para a função principal. O app já usa cache do
Hugging Face, retoma arquivos parciais quando a biblioteca permite, mostra
progresso agregado e valida a presença de arquivos essenciais. Mesmo assim, uma
falha hoje termina em mensagem genérica e nova tentativa manual, dependendo de
uma única fonte online.

## Problema

- Uma conexão instável pode bloquear completamente o onboarding.
- A mensagem atual não diferencia rede, disco, permissão, proxy, TLS ou snapshot
  corrompido.
- Não existe cadeia de tentativas controlada nem fallback operacional validado.
- Arquivos existentes são verificados por presença e tamanho, não por uma carga
  real antes de declarar o modelo pronto.

## Objetivo

Maximizar a conclusão do download sem intervenção técnica, preservar progresso
válido e sempre apresentar causa provável e próxima ação.

## Jornada proposta

1. Executar pré-verificações de espaço, escrita e conectividade.
2. Consultar QS-005 para reutilizar modelo compatível, quando disponível.
3. Baixar da fonte oficial primária com progresso e retomada.
4. Repetir falhas transitórias automaticamente com backoff.
5. Validar o snapshot e realizar teste leve de carga.
6. Se a fonte falhar, oferecer fallback aprovado ou pacote offline.
7. Nunca marcar como instalado antes de todas as validações.

## Estados de interface

`Preparando → Baixando → Verificando → Pronto`

Estados recuperáveis:

`Pausado`, `Sem conexão`, `Espaço insuficiente`, `Fonte indisponível`,
`Arquivos corrompidos` e `Ação necessária`.

Cada erro deve mostrar o que aconteceu, o que foi preservado e qual ação será
tentada em seguida.

## Política de tentativas

- Até três tentativas automáticas para falhas transitórias.
- Backoff com jitter, sem travar a interface.
- Não repetir automaticamente erros permanentes como falta de espaço ou acesso
  negado.
- Reutilizar blobs completos já presentes no cache.
- Permitir pausar, fechar e retomar depois.

## Fallbacks permitidos

1. Fonte oficial primária com revisão fixada.
2. Espelho secundário controlado pelo produto, com os mesmos artefatos e
   verificação de integridade.
3. Download manual de pacote assinado/verificado e importação pelo app.
4. Instalador offline opcional para ambientes sem acesso ao Hub.

Nunca baixar executáveis ou modelos de URLs arbitrárias sugeridas por mensagens
de erro.

## Requisitos funcionais

- **RF01:** verificar espaço necessário com margem antes de iniciar.
- **RF02:** validar permissão de escrita no destino.
- **RF03:** classificar erros em rede, DNS, proxy, TLS, autenticação/rate limit,
  disco, permissão, integridade e desconhecido.
- **RF04:** manter progresso real por bytes e estado do arquivo atual.
- **RF05:** preservar download parcial válido entre tentativas e reinícios.
- **RF06:** fixar repositório e revisão compatíveis por versão do app.
- **RF07:** validar arquivos obrigatórios, tamanho, metadados e carga mínima pelo
  CTranslate2/faster-whisper.
- **RF08:** promover snapshot para pronto somente de forma atômica.
- **RF09:** oferecer ações contextuais: tentar novamente, alterar pasta, usar
  modelo existente, importar pacote ou copiar diagnóstico.
- **RF10:** serializar downloads do mesmo modelo e impedir competição entre
  inicialização e tela de configurações.
- **RF11:** atualizar bandeja e configurações a partir de uma única máquina de
  estados.
- **RF12:** permitir cancelar sem apagar blobs válidos.

## Requisitos não funcionais

- Interface responsiva durante todo o processo.
- Diagnóstico sem chaves, nomes de usuário, textos ou caminhos pessoais completos.
- Downloads autenticados por TLS e artefatos validados.
- Compatibilidade com proxy corporativo suportado pelas bibliotecas oficiais.
- Testabilidade com fonte e filesystem simulados.

## Métricas de sucesso

- Taxa de instalação concluída por modelo e versão.
- Taxa de recuperação automática após falha transitória.
- Bytes evitados por retomada.
- Distribuição anônima de categorias de erro, somente com consentimento futuro.

## Critérios de aceite

1. Interromper o download em 25%, 50% e 90% permite retomada sem reiniciar arquivos
   completos.
2. Falhas transitórias disparam tentativas controladas e mantêm a UI responsiva.
3. Falta de espaço interrompe antes do download e informa o necessário.
4. Snapshot incompleto ou corrompido nunca aparece como instalado.
5. A conclusão inclui teste real de carga do modelo selecionado.
6. Fonte primária indisponível apresenta fallback seguro e utilizável.
7. Fechar e reabrir mantém progresso válido e estado coerente.
8. Dois gatilhos simultâneos resultam em apenas um download.
9. O usuário nunca fica num ciclo sem causa e próxima ação visíveis.

## Casos de teste mínimos

- instalação limpa por modelo suportado;
- queda de rede, DNS e timeout;
- proxy/TLS inválido;
- disco cheio e pasta sem permissão;
- arquivo truncado e cache parcialmente corrompido;
- rate limit e fonte indisponível;
- reinício do app e do computador;
- importação manual válida e inválida;
- concorrência entre auto-download e botão Baixar.

## Fora de escopo

- Criar a infraestrutura comercial cloud de QS-013.
- Reutilizar formatos incompatíveis de Whisper.
- Garantir disponibilidade eterna de um único provedor externo.

## Rollout

- Primeiro entregar classificação de erros, retomada e validação.
- Depois habilitar fonte secundária somente após pipeline de publicação,
  verificação e teste periódico.
- Validar em máquina Windows limpa e redes degradadas antes de cada release.
