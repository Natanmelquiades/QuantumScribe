"""Contratos leves para coordenar uma sessão de transcrição.

Este módulo contém apenas tipos da biblioteca padrão. Ele pode ser importado por
testes, orquestração e adaptadores sem inicializar Tkinter, Whisper, áudio físico
ou qualquer dependência opcional.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Mapping, Protocol


class SessionState(str, Enum):
    """Estados observáveis do ciclo de vida de uma sessão."""

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CancellationToken(Protocol):
    """Handle mínimo para cancelamento cooperativo."""

    def is_cancelled(self) -> bool:
        """Indica se o trabalho deve parar antes de produzir um resultado."""


@dataclass(frozen=True, slots=True)
class RecordingSession:
    """Identidade e metadados da gravação em andamento."""

    session_id: str
    started_at: datetime
    source: str = "microphone"
    target: str | None = None
    cancel_token: CancellationToken | None = None

    def __post_init__(self) -> None:
        _validate_session_id(self.session_id)


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    """Texto produzido por uma sessão e informações de diagnóstico."""

    session_id: str
    text: str
    source_mode: Literal["classic", "streaming"] = "classic"
    language: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_session_id(self.session_id)
        if self.source_mode not in {"classic", "streaming"}:
            raise ValueError("source_mode deve ser 'classic' ou 'streaming'")


@dataclass(frozen=True, slots=True)
class SessionEvent:
    """Evento de progresso consumido por HUD, bandeja e diagnósticos."""

    session_id: str
    state: SessionState
    progress: float | None = None
    recoverable: bool = False
    user_action: str | None = None

    def __post_init__(self) -> None:
        _validate_session_id(self.session_id)
        if not isinstance(self.state, SessionState):
            raise TypeError("state deve ser uma instância de SessionState")
        if self.progress is not None and (
            not math.isfinite(self.progress) or not 0.0 <= self.progress <= 1.0
        ):
            raise ValueError("progress deve estar entre 0.0 e 1.0")


class AudioSource(Protocol):
    """Fonte de áudio compatível com uma sessão de gravação."""

    def capture(self, session: RecordingSession) -> object:
        """Captura dados para a sessão informada."""


class Transcriber(Protocol):
    """Motor clássico ou streaming que produz um resultado tipado."""

    def transcribe(self, audio: object, session: RecordingSession) -> TranscriptionResult:
        """Transcreve o áudio associado à sessão."""


class Delivery(Protocol):
    """Destino que entrega um resultado já validado."""

    def deliver(self, result: TranscriptionResult) -> None:
        """Entrega o resultado ao destino ativo."""


class ConfigStore(Protocol):
    """Persistência de configuração sem acoplar o contrato à implementação."""

    def load(self) -> object:
        """Carrega a configuração atual."""

    def save(self, config: object) -> None:
        """Persiste a configuração recebida."""


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id deve ser uma string não vazia")
