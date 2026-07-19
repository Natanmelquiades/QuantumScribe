# Instruções permanentes do Quantum Scribe

## Controle de versão

- Toda rodada que modificar o projeto deve incrementar a versão patch por meio
  de `.venv\Scripts\python.exe increment_version.py` antes da entrega.
- A versão deve permanecer centralizada e ser exibida corretamente no produto.

## Gestão do Product Backlog

- Quando a skill pessoal `quantum-scribe-backlog` estiver disponível, usá-la em
  todo pedido que mencione backlog ou registro de trabalho futuro neste projeto.
- O backlog mestre do produto fica em `docs/PRODUCT_BACKLOG.md`.
- Sempre que o usuário pedir para criar um backlog, adicionar algo ao backlog,
  registrar uma ideia futura, melhoria, feature, correção ou débito técnico, o
  item deve ser incluído nesse arquivo.
- Cada novo item recebe o próximo identificador sequencial `QS-###` e começa na
  Caixa de Entrada ou em Em refinamento, conforme o nível de detalhe fornecido.
- Itens independentes recebem IDs separados, mesmo quando surgirem na mesma
  conversa. Itens relacionados devem indicar essa relação.
- Um pedido de registro no backlog não autoriza a implementação. Primeiro
  registrar, classificar e refinar; implementar somente quando o usuário pedir.
- Criar um PRD separado em `docs/` quando a funcionalidade tiver regras, riscos
  ou critérios de aceite que não caibam claramente no resumo do backlog.
- Manter a tabela Visão geral e a seção de status correspondente sincronizadas.
