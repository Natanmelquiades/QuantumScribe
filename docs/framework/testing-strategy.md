# QuantumScribe — Estratégia de testes

## Camadas

1. **Unitário:** contratos, estado de sessão, configuração, filtros e validadores;
   usar fakes/mocks e não iniciar Tkinter, Whisper real, rede ou hardware.
2. **Integração controlada:** lifecycle clássico/streaming, cancelamento, resultado
   stale, entrega, updater e componentes com filesystem temporário.
3. **Packaging/release:** requirements/locks, compileall, `pip check`, `pip-audit`,
   build limpo, inventário e smoke import/offline.
4. **Manual por ambiente:** instalação limpa CPU, GPU/fallback quando disponível,
   primeiro uso offline, download interrompido e atualização/rollback.

## Gates mínimos

```text
pytest -q -p no:cacheprovider
ruff check .
compileall dos módulos Python
pip check
pip-audit
radon cc localwhisper -s -a
```

Os comandos podem ser adaptados ao ambiente, mas a evidência da story deve registrar
qualquer diferença. O `git fsck` só é permitido em cópia/clone canônico, nunca no
checkout de trabalho com ownership divergente.

## Regras de regressão

- A baseline protegida pelas Stories 1.1/1.2 não pode cair.
- Toda extração deve ter teste de caracterização antes e depois.
- Resultado de sessão substituída não pode tocar HUD, clipboard, histórico ou estado
  de uma nova sessão.
- Testes devem ser determinísticos, sem download silencioso e sem depender de
  dispositivo físico.
- Cobertura deve ser acompanhada nos arquivos tocados; a Story 1.3 não mascara uma
  regressão removendo testes.
