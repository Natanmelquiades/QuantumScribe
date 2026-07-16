"""Quantum Brain — Motor de Segundo Cérebro do Quantum Scribe.

Captura fragmentos de pensamento ditados, organiza em notas atômicas Markdown
e sintetiza periodicamente conexões, projetos e insights via LLM local.
"""

from __future__ import annotations

import datetime
import json
import threading
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .config import AppConfig

# Lock global para escrita concorrente
_brain_lock = threading.Lock()

# Singleton da instância do orquestrador
_orchestrator_instance: Optional["QuantumBrainOrchestrator"] = None
_orchestrator_lock = threading.Lock()


def quantum_brain_dir(config: "AppConfig") -> Path:
    """Retorna o diretório raiz do Quantum Brain."""
    from .config import app_data_dir
    path = app_data_dir() / "quantum_brain"
    path.mkdir(parents=True, exist_ok=True)
    return path


def raw_notes_dir(config: "AppConfig") -> Path:
    """Retorna o diretório de notas brutas do dia atual."""
    today = datetime.date.today().strftime("%Y-%m-%d")
    path = quantum_brain_dir(config) / "raw" / today
    path.mkdir(parents=True, exist_ok=True)
    return path


def projects_dir(config: "AppConfig") -> Path:
    """Retorna o diretório de projetos sintetizados."""
    path = quantum_brain_dir(config) / "projects"
    path.mkdir(parents=True, exist_ok=True)
    return path


def insights_dir(config: "AppConfig") -> Path:
    """Retorna o diretório de insights de síntese."""
    path = quantum_brain_dir(config) / "insights"
    path.mkdir(parents=True, exist_ok=True)
    return path


class QuantumBrainOrchestrator:
    """Coordena captura de notas brutas e agenda síntese periódica em background."""

    def __init__(self, config: "AppConfig") -> None:
        self.config = config
        self._unsynthesized_count = 0
        self._sync_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._start_background_sync()

    @classmethod
    def get_instance(cls, config: "AppConfig") -> "QuantumBrainOrchestrator":
        """Retorna a instância singleton do orquestrador (criando se necessário)."""
        global _orchestrator_instance
        with _orchestrator_lock:
            if _orchestrator_instance is None:
                _orchestrator_instance = cls(config)
            return _orchestrator_instance

    def add_entry(self, text: str) -> Path:
        """Salva uma nova nota bruta e verifica se deve disparar síntese.

        Returns:
            Caminho do arquivo de nota criado.
        """
        note_id = str(uuid.uuid4())[:8]
        now = datetime.datetime.now()

        # Frontmatter YAML simples (compatível com Obsidian)
        frontmatter = (
            f"---\n"
            f"id: {note_id}\n"
            f"timestamp: {now.isoformat()}\n"
            f"synthesized: false\n"
            f"---\n\n"
        )
        content = frontmatter + text.strip() + "\n"

        file_path = raw_notes_dir(self.config) / f"{note_id}.md"

        with _brain_lock:
            file_path.write_text(content, encoding="utf-8")
            self._unsynthesized_count += 1

        print(f"[Quantum Brain] Nota salva: {file_path.name} ({self._unsynthesized_count} pendentes)")

        # Dispara síntese imediata se atingiu o threshold
        threshold = getattr(self.config, "quantum_brain_sync_threshold", 5)
        if self._unsynthesized_count >= threshold:
            self._trigger_synthesis()

        return file_path

    def get_unsynthesized_notes(self) -> list[dict]:
        """Retorna todas as notas brutas marcadas como `synthesized: false`."""
        brain_dir = quantum_brain_dir(self.config)
        raw_dir = brain_dir / "raw"
        if not raw_dir.is_dir():
            return []

        notes = []
        for note_file in sorted(raw_dir.rglob("*.md")):
            try:
                content = note_file.read_text(encoding="utf-8")
                if "synthesized: false" in content:
                    # Extrai texto (tudo após o segundo ---)
                    parts = content.split("---\n", 2)
                    text = parts[2].strip() if len(parts) >= 3 else content
                    notes.append({
                        "file": note_file,
                        "content": content,
                        "text": text,
                    })
            except Exception:
                pass
        return notes

    def mark_as_synthesized(self, note_file: Path) -> None:
        """Atualiza o frontmatter da nota para `synthesized: true`."""
        try:
            content = note_file.read_text(encoding="utf-8")
            new_content = content.replace("synthesized: false", "synthesized: true", 1)
            note_file.write_text(new_content, encoding="utf-8")
        except Exception as e:
            print(f"[Quantum Brain] Erro ao marcar nota {note_file.name}: {e}")

    def _trigger_synthesis(self) -> None:
        """Dispara síntese em thread separada (não bloqueia o fluxo principal)."""
        def _run():
            try:
                synthesizer = BrainSynthesizer(self.config)
                synthesizer.run()
                self._unsynthesized_count = 0
            except Exception as e:
                print(f"[Quantum Brain] Erro na síntese: {e}")

        threading.Thread(target=_run, daemon=True, name="QBrainSynthesis").start()

    def _start_background_sync(self) -> None:
        """Inicia o timer periódico de síntese em background."""
        def _timer_loop():
            interval_min = getattr(self.config, "quantum_brain_sync_interval_min", 30)
            interval_sec = interval_min * 60
            while not self._stop_event.wait(interval_sec):
                notes = self.get_unsynthesized_notes()
                if notes:
                    print(f"[Quantum Brain] Síntese periódica: {len(notes)} notas pendentes")
                    self._trigger_synthesis()

        self._sync_thread = threading.Thread(
            target=_timer_loop, daemon=True, name="QBrainTimer"
        )
        self._sync_thread.start()

    def stop(self) -> None:
        """Para o timer de background."""
        self._stop_event.set()

    def get_stats(self) -> dict:
        """Retorna estatísticas do Quantum Brain para exibição na UI."""
        notes = self.get_unsynthesized_notes()
        brain_dir = quantum_brain_dir(self.config)

        # Conta projetos
        proj_dir = brain_dir / "projects"
        project_count = len(list(proj_dir.glob("*.md"))) if proj_dir.is_dir() else 0

        # Última síntese
        ins_dir = brain_dir / "insights"
        last_synthesis = None
        if ins_dir.is_dir():
            files = sorted(ins_dir.glob("*.md"), reverse=True)
            if files:
                last_synthesis = files[0].stat().st_mtime

        return {
            "unsynthesized": len(notes),
            "projects": project_count,
            "last_synthesis": last_synthesis,
            "brain_dir": str(brain_dir),
        }


class BrainSynthesizer:
    """Usa LLM local (Qwen2.5-3B via CTranslate2) para sintetizar notas brutas.

    Se o modelo não estiver disponível, usa síntese heurística simples
    (clustering por palavras-chave) como fallback robusto.
    """

    SYNTHESIS_PROMPT_TEMPLATE = """Você é um assistente de organização de pensamentos. Receberá fragmentos de pensamentos e ideias capturados por voz. Sua tarefa é:

1. Identificar os PROJETOS ou TEMAS presentes nos fragmentos
2. Agrupar os fragmentos por projeto/tema
3. Para cada grupo, criar um resumo coeso
4. Identificar conexões entre diferentes grupos
5. Sugerir próximos passos ou ações

Responda APENAS em JSON com a estrutura:
{{
  "projects": [
    {{
      "name": "Nome do Projeto",
      "summary": "Resumo do projeto",
      "fragments": ["fragmento 1", "fragmento 2"],
      "next_steps": ["ação 1", "ação 2"],
      "connections": ["Outro Projeto"]
    }}
  ],
  "general_insights": ["insight 1", "insight 2"]
}}

FRAGMENTOS:
{fragments}"""

    def __init__(self, config: "AppConfig") -> None:
        self.config = config
        self._orchestrator = QuantumBrainOrchestrator.get_instance(config)

    def run(self) -> None:
        """Executa um ciclo completo de síntese."""
        notes = self._orchestrator.get_unsynthesized_notes()
        if not notes:
            print("[Quantum Brain] Nenhuma nota pendente para síntese.")
            return

        print(f"[Quantum Brain] Sintetizando {len(notes)} notas...")

        # Tenta síntese via LLM; cai no heurístico se falhar
        try:
            synthesis = self._synthesize_with_llm(notes)
        except Exception as e:
            print(f"[Quantum Brain] LLM indisponível ({e}), usando síntese heurística.")
            synthesis = self._synthesize_heuristic(notes)

        if synthesis:
            self._save_synthesis(synthesis, notes)
            # Marca notas como sintetizadas
            for note in notes:
                self._orchestrator.mark_as_synthesized(note["file"])

    def _synthesize_with_llm(self, notes: list[dict]) -> dict | None:
        """Tenta usar o Qwen2.5-3B via CTranslate2 para síntese.

        Reutiliza a infraestrutura já existente no rewriter.py.
        O modelo precisa estar baixado na pasta models/rewriter/.
        """
        try:
            from .rewriter import _get_model_path, is_rewriter_downloaded
        except ImportError:
            raise RuntimeError("Módulo rewriter não disponível")

        brain_repo = getattr(self.config, "quantum_brain_llm_repo", "jncraton/Qwen2.5-3B-Instruct-ct2-int8")

        # Não baixa automaticamente em background para evitar downloads surpresa lentos
        if not is_rewriter_downloaded(brain_repo):
            raise RuntimeError(
                f"Modelo {brain_repo} não está baixado localmente. "
                "Configure ou baixe o modelo nas configurações do Quantum Scribe."
            )

        import ctranslate2
        from transformers import AutoTokenizer

        model_path = _get_model_path(brain_repo)

        # Carrega o gerador e o tokenizer
        generator = ctranslate2.Generator(str(model_path), device="cpu", compute_type="int8")
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))

        fragments_text = "\n---\n".join([f"[{i+1}] {n['text']}" for i, n in enumerate(notes)])
        prompt = self.SYNTHESIS_PROMPT_TEMPLATE.format(fragments=fragments_text)

        messages = [{"role": "user", "content": prompt}]
        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text_input))

        results = generator.generate_batch(
            [tokens],
            max_length=1024,
            sampling_temperature=0.3,
            sampling_topk=40,
        )

        output = tokenizer.decode(results[0].sequences_ids[0])

        # Extrai JSON da resposta
        import re
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None

    def _synthesize_heuristic(self, notes: list[dict]) -> dict:
        """Síntese baseada em frequência de palavras-chave (sem LLM).

        Agrupa notas por palavras mais frequentes para criar clusters temáticos.
        """
        import re
        from collections import Counter

        stop_words = {
            "que", "não", "uma", "por", "com", "mas", "isso", "para", "como",
            "mais", "tem", "ser", "foi", "está", "quando", "então", "muito",
            "esse", "este", "esta", "essa", "aqui", "agora", "também", "para",
            "pelo", "pela", "seus", "suas", "como", "mais", "tudo"
        }

        # Extrai palavras-chave de cada nota
        note_keywords = []
        for note in notes:
            words = re.findall(r'\b[A-Za-zÀ-ÿ]{4,}\b', note["text"].lower())
            keywords = [w for w in words if w not in stop_words]
            note_keywords.append(keywords)

        # Conta frequência global
        all_words = [w for kw in note_keywords for w in kw]
        top_themes = [w for w, _ in Counter(all_words).most_common(5)]

        return {
            "projects": [
                {
                    "name": f"Tema: {theme.capitalize()}",
                    "summary": f"Fragmentos relacionados ao tema '{theme}'",
                    "fragments": [
                        n["text"] for i, n in enumerate(notes)
                        if theme in note_keywords[i]
                    ][:5],
                    "next_steps": [],
                    "connections": [],
                }
                for theme in top_themes
                if any(theme in kw for kw in note_keywords)
            ],
            "general_insights": [
                f"Total de {len(notes)} fragmentos capturados",
                f"Temas identificados: {', '.join(top_themes)}",
            ]
        }

    def _save_synthesis(self, synthesis: dict, notes: list[dict]) -> None:
        """Salva a síntese nos arquivos de projetos e insights."""
        now = datetime.datetime.now()

        # 1. Atualiza ou cria arquivos de projetos
        for project in synthesis.get("projects", []):
            proj_name = project.get("name", "Sem Nome").replace("/", "-").replace("\\", "-")
            proj_file = projects_dir(self.config) / f"{proj_name}.md"

            # Lê conteúdo existente ou cria novo
            if proj_file.exists():
                existing = proj_file.read_text(encoding="utf-8")
                new_content = existing + f"\n\n## Atualização {now.strftime('%Y-%m-%d %H:%M')}\n\n"
            else:
                new_content = f"# {proj_name}\n\n"
                new_content += f"*Criado automaticamente pelo Quantum Brain em {now.strftime('%Y-%m-%d')}*\n\n"

            new_content += f"**Resumo:** {project.get('summary', '')}\n\n"

            if project.get("fragments"):
                new_content += "### Fragmentos\n\n"
                for frag in project["fragments"]:
                    new_content += f"- {frag}\n"
                new_content += "\n"

            if project.get("next_steps"):
                new_content += "### Próximos Passos\n\n"
                for step in project["next_steps"]:
                    new_content += f"- [ ] {step}\n"
                new_content += "\n"

            if project.get("connections"):
                new_content += "### Conexões\n\n"
                for conn in project["connections"]:
                    new_content += f"- [[{conn}]]\n"
                new_content += "\n"

            proj_file.write_text(new_content, encoding="utf-8")

        # 2. Salva relatório de síntese em insights/
        timestamp_str = now.strftime("%Y-%m-%d_%H-%M")
        insight_file = insights_dir(self.config) / f"{timestamp_str}_synthesis.md"

        insight_content = f"# Síntese do Quantum Brain — {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        insight_content += f"*{len(notes)} notas processadas*\n\n"

        if synthesis.get("general_insights"):
            insight_content += "## Insights Gerais\n\n"
            for insight in synthesis["general_insights"]:
                insight_content += f"- {insight}\n"
            insight_content += "\n"

        insight_content += "## Projetos Identificados\n\n"
        for project in synthesis.get("projects", []):
            insight_content += f"- **{project.get('name')}**: {project.get('summary', '')}\n"

        insight_file.write_text(insight_content, encoding="utf-8")

        # 3. Atualiza index.md (mapa mental geral)
        self._update_index(synthesis)

        print(f"[Quantum Brain] Síntese salva: {insight_file.name}")

    def _update_index(self, synthesis: dict) -> None:
        """Atualiza o arquivo index.md com o mapa de projetos atual."""
        brain_dir = quantum_brain_dir(self.config)
        index_file = brain_dir / "index.md"
        now = datetime.datetime.now()

        content = "# 🧠 Quantum Brain — Mapa Mental\n\n"
        content += f"*Última atualização: {now.strftime('%Y-%m-%d %H:%M')}*\n\n"
        content += "## Projetos Ativos\n\n"

        # Lista todos os projetos existentes
        proj_dir = projects_dir(self.config)
        for proj_file in sorted(proj_dir.glob("*.md")):
            proj_name = proj_file.stem
            content += f"- [[projects/{proj_name}]]\n"

        if synthesis.get("general_insights"):
            content += "\n## Insights Recentes\n\n"
            for insight in synthesis["general_insights"]:
                content += f"- {insight}\n"

        index_file.write_text(content, encoding="utf-8")
