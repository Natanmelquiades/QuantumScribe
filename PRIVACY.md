# Privacidade e dados locais

O QuantumScribe foi projetado para transcrever áudio localmente. Depois que os
modelos são baixados, a transcrição normal não precisa enviar o áudio para um serviço
de reconhecimento de voz na nuvem.

## Conexões de rede

O aplicativo pode acessar o Hugging Face quando o usuário solicita o download de um
modelo Whisper ou Mini-LLM. O código não incorpora telemetria própria.

## Dados armazenados no computador

Por padrão, dados ficam sob `%LOCALAPPDATA%\QuantumScribe`, incluindo:

- `config.json`: preferências e prompts;
- `models/`: modelos baixados;
- `diary/`: transcrições organizadas por data;
- `quantum_brain/`: notas e sínteses locais;
- caches de vocabulário e comparação;
- `app.log`: diagnóstico local;
- `emergency_audio.wav`: cópia temporária de recuperação durante o processamento.

Backups completos podem incluir configurações, logs, diário e notas. Guarde-os como
dados pessoais e não os anexe a issues públicas.

## Controle do usuário

Os dados podem ser revisados e removidos diretamente no diretório acima. Feche o
aplicativo antes de excluir arquivos em uso. Modelos são grandes e podem ser
baixados novamente quando necessário.
