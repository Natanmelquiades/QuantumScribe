# Como contribuir

Obrigado por considerar uma contribuição ao QuantumScribe.

## Preparação

Requisitos: Windows 10/11, Git, Python 3.11–3.13 e um microfone para testes manuais.

```powershell
git clone https://github.com/Natanmelquiades/QuantumScribe.git
cd QuantumScribe
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Antes de enviar um pull request

```powershell
.\.venv\Scripts\python.exe -m compileall -q main.py localwhisper tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check localwhisper tests
```

- mantenha mudanças pequenas e focadas;
- inclua testes para correções e novas regras de transcrição;
- não inclua modelos, builds, backups, áudios ou dados de usuário;
- preserve o modo literal: pontuação não pode trocar as palavras ditadas;
- descreva impacto, validação e eventuais limitações no pull request.

## Commits

Prefira mensagens objetivas no formato `tipo: resumo`, por exemplo:

- `fix: avoid model preload during startup`
- `feat: add conservative question detection`
- `docs: document CUDA installation`

Ao contribuir, você concorda que sua contribuição será licenciada sob a licença MIT
do projeto.
