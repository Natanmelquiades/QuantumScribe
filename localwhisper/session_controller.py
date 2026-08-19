"""Coordenação leve da identidade de jobs de transcrição.

O controller não conhece Tkinter, áudio, Whisper, clipboard ou componentes
opcionais. Ele apenas cria uma identidade monotônica, invalida jobs cancelados e
impede que callbacks de um job antigo alterem uma sessão mais nova.
"""

from __future__ import annotations

import threading
from collections.abc import Callable


class SessionController:
    """Guarda o job ativo e agenda callbacks somente enquanto ele permanece atual."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._next_job_id = 0
        self._active_job_id: int | None = None

    @property
    def active_job_id(self) -> int | None:
        with self._lock:
            return self._active_job_id

    @property
    def next_job_id(self) -> int:
        with self._lock:
            return self._next_job_id

    def start_job(self) -> int:
        """Cria e ativa um novo job, invalidando qualquer job anterior."""
        with self._lock:
            self._next_job_id += 1
            self._active_job_id = self._next_job_id
            return self._active_job_id

    def set_next_job_id(self, job_id: int) -> None:
        """Permite restaurar o contador em testes/compatibilidade interna."""
        if not isinstance(job_id, int) or job_id < 0:
            raise ValueError("job_id deve ser um inteiro não negativo")
        with self._lock:
            self._next_job_id = job_id

    def set_active_job(self, job_id: int | None) -> None:
        """Ajusta o job ativo para manter a fachada antiga compatível."""
        if job_id is not None and (not isinstance(job_id, int) or job_id < 1):
            raise ValueError("job_id ativo deve ser um inteiro positivo ou None")
        with self._lock:
            self._active_job_id = job_id

    def invalidate(self) -> None:
        """Invalida o job ativo sem interromper à força o worker nativo."""
        self.set_active_job(None)

    def is_active(self, job_id: int) -> bool:
        with self._lock:
            return self._active_job_id == job_id

    def schedule_if_active(
        self,
        job_id: int,
        schedule: Callable[[Callable[[], None]], object],
        callback: Callable[[], None],
    ) -> None:
        """Agenda callback e revalida o job no momento de executar."""

        def run_if_current() -> None:
            if self.is_active(job_id):
                callback()

        schedule(run_if_current)

    def finish_if_active(
        self,
        job_id: int,
        schedule: Callable[[Callable[[], None]], object],
        callback: Callable[[], None],
    ) -> None:
        """Executa o callback final uma vez e aposenta apenas o job observado."""

        def finish_if_current() -> None:
            if not self.is_active(job_id):
                return
            try:
                callback()
            finally:
                with self._lock:
                    if self._active_job_id == job_id:
                        self._active_job_id = None

        schedule(finish_if_current)
