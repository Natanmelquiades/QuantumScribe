# Runbook — Recuperação Git não destrutiva

Este procedimento existe para o checkout com ownership divergente e objetos
ausentes. Ele não autoriza reparo automático nem limpeza ampla.

## Pré-condições e bloqueios

Parar imediatamente se não houver: identidade proprietária, caminho aprovado para
cópia preservada e remote conhecido/confiável. Sem esses três itens, registrar o
bloqueio e continuar apenas em arquivos de trabalho não-Git.

## Procedimento seguro

1. Registrar o caminho absoluto do checkout, usuário efetivo, branch, status,
   remotes, último commit acessível e lista de alterações não commitadas.
2. Criar uma cópia preservada em caminho explicitamente aprovado pelo proprietário.
   Não usar a pasta raiz do usuário como destino implícito e não sobrescrever uma
   cópia existente.
3. Identificar o remote canônico por confirmação do proprietário. Não inferir um
   remote a partir de uma URL não verificada.
4. Criar um clone novo fora do checkout de trabalho e validar conectividade,
   refs/branches e integridade. Executar `git fsck --full` somente no clone/cópia
   canônica, nunca no checkout original.
5. Comparar o clone com a cópia preservada usando diffs e hashes de arquivos. Copiar
   alterações somente depois de revisar cada caminho; não descartar arquivo do
   proprietário.
6. Se o clone canônico falhar, parar e registrar exatamente o erro. O resultado é
   **bloqueado**, não uma licença para executar `reset`, `prune`, `gc` ou reescrever
   objetos.

## Limpeza protegida

- `.pytest_cache`, `.pytest-tmp`, `build`, `dist` e temporários devem ser resolvidos
  por caminho absoluto e classificados antes de qualquer ação.
- A limpeza só ocorre quando a identidade proprietária tiver autorização e uma
  quarentena recuperável tiver sido criada.
- Não remover dados de usuário, configuração, modelos, histórico, diário, logs ou
  arquivos fora do diretório explicitamente aprovado.
- O agente pode documentar, inventariar e validar; a remoção material permanece
  condicionada ao proprietário/operador autorizado.

## Evidência obrigatória

Registrar data, identidade, caminhos, remote confirmado, hash/commit do clone,
resultado de `git fsck`, lista de arquivos preservados e decisão final. Não incluir
tokens, credenciais, áudio ou texto ditado.

**Referência:** ADR 0004 e `docs/prd/epic-1-quantumscribe-auditoria-estabilizacao.md`.
