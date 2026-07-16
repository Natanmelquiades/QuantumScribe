from __future__ import annotations

import re
import unittest
from types import SimpleNamespace

from localwhisper.punctuation import (
    ensure_terminal_punctuation,
    join_whisper_segments,
    restore_question_marks,
)


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text, flags=re.UNICODE)


class QuestionRestorationTests(unittest.TestCase):
    def test_restores_colloquial_question_mark(self) -> None:
        self.assertEqual(
            restore_question_marks("Tem como corrigir isso."),
            "Tem como corrigir isso?",
        )

    def test_detects_question_clause_after_statement(self) -> None:
        text = "A pontuação ainda está ruim, tem como melhorar isso."
        self.assertEqual(
            restore_question_marks(text),
            "A pontuação ainda está ruim, tem como melhorar isso?",
        )

    def test_keeps_existing_question_unchanged(self) -> None:
        text = "Por que você não atualizou a versão?"
        self.assertEqual(restore_question_marks(text), text)

    def test_does_not_turn_declarative_como_into_question(self) -> None:
        text = "Como mais uma coisa que eu tentei e parei."
        self.assertEqual(restore_question_marks(text), text)

    def test_only_changes_punctuation_never_words(self) -> None:
        original = "Ficou melhor, mas tem como corrigir isso por favor."
        restored = restore_question_marks(original)
        self.assertEqual(_words(restored), _words(original))


class SegmentPauseTests(unittest.TestCase):
    def test_long_pause_creates_sentence_boundary(self) -> None:
        segments = [
            SimpleNamespace(text="Eu estou indo dormir", start=0.0, end=1.2),
            SimpleNamespace(text="Então já crie o PRD", start=2.0, end=3.0),
        ]

        self.assertEqual(
            join_whisper_segments(segments, pause_threshold_seconds=0.65),
            "Eu estou indo dormir. Então já crie o PRD.",
        )

    def test_short_pause_does_not_invent_boundary(self) -> None:
        segments = [
            SimpleNamespace(text="Eu quero criar", start=0.0, end=1.0),
            SimpleNamespace(text="uma ferramenta melhor", start=1.2, end=2.0),
        ]

        self.assertEqual(
            join_whisper_segments(segments, pause_threshold_seconds=0.65),
            "Eu quero criar uma ferramenta melhor.",
        )

    def test_pause_and_question_detection_work_together(self) -> None:
        segments = [
            SimpleNamespace(text="Tem como corrigir isso", start=0.0, end=1.0),
            SimpleNamespace(text="Eu quero melhorar", start=1.8, end=2.8),
        ]

        result = join_whisper_segments(segments, pause_threshold_seconds=0.65)

        self.assertEqual(result, "Tem como corrigir isso? Eu quero melhorar.")
        self.assertEqual(
            _words(result),
            ["Tem", "como", "corrigir", "isso", "Eu", "quero", "melhorar"],
        )


class TerminalPunctuationTests(unittest.TestCase):
    def test_adds_period_to_complete_utterance_without_terminal_mark(self) -> None:
        self.assertEqual(
            ensure_terminal_punctuation("Depois disso eu acredito em qualquer coisa"),
            "Depois disso eu acredito em qualquer coisa.",
        )

    def test_preserves_existing_terminal_mark(self) -> None:
        self.assertEqual(
            ensure_terminal_punctuation("Tá vendendo, tá fazendo grana?"),
            "Tá vendendo, tá fazendo grana?",
        )


if __name__ == "__main__":
    unittest.main()
