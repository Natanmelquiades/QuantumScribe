"""Módulo de Gravação de Áudio via SoundDevice.

Este módulo lida com a captura de áudio mono a partir do microfone padrão
usando a biblioteca sounddevice. Ele acumula dados de som na memória e calcula
a amplitude do volume em tempo real para alimentar a animação do HUD.
"""

from __future__ import annotations

import threading
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import numpy as np

if TYPE_CHECKING:
    import sounddevice as sd

SAMPLE_RATE = 16_000  # Taxa de amostragem ideal exigida pelo modelo Whisper (16kHz)
CHANNELS = 1          # Captura apenas canal Mono


def get_input_devices() -> list[dict]:
    """Retorna uma lista de dicionários contendo informações sobre dispositivos de entrada de áudio,
    simplificada para exibir apenas dispositivos físicos reais e sem duplicatas.
    """
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()

        # Identifica a host API padrão do dispositivo de entrada padrão
        default_in_idx = sd.default.device[0]
        if default_in_idx >= 0:
            default_hostapi = devices[default_in_idx]['hostapi']
        else:
            default_hostapi = sd.default.hostapi

        input_devices = []
        seen_names = set()

        # Filtros de exclusão para mappers de som e drivers virtuais redundantes
        exclude_keywords = [
            "mapeador", "mapper", "primary sound", "captura de som prim",
            "microsoft sound mapper", "driver de captura"
        ]

        for d in devices:
            if d['max_input_channels'] > 0:
                name = d['name']
                name_lower = name.lower()

                # Pula mappers virtuais redundantes
                if any(kw in name_lower for kw in exclude_keywords):
                    continue

                # Filtra para manter apenas os dispositivos da Host API padrão do sistema.
                # Isso elimina a repetição do mesmo microfone em MME, WASAPI, DirectSound, etc.
                if d['hostapi'] != default_hostapi:
                    continue

                if name in seen_names:
                    continue
                seen_names.add(name)

                hostapi_name = hostapis[d['hostapi']]['name']
                input_devices.append({
                    'index': d['index'],
                    'name': name,
                    'hostapi_name': hostapi_name,
                    'display_name': name  # Exibe apenas o nome limpo
                })
        return input_devices
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[Audio] Falha ao consultar dispositivos de áudio: {e}", exc_info=True)
        return []


def get_device_index_by_name(display_name: str) -> int | None:
    """Busca o índice do dispositivo pelo nome de exibição (display_name).

    Retorna None se não encontrar ou se o nome for vazio/Padrão.
    """
    if not display_name or display_name == "Padrão do Sistema":
        return None

    # 1. Tenta correspondência exata na lista filtrada
    for d in get_input_devices():
        if d['display_name'] == display_name:
            return d['index']

    # 2. Fallback: busca por substring em qualquer dispositivo de entrada disponível
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        for d in devices:
            if d['max_input_channels'] > 0:
                if display_name.lower() in d['name'].lower():
                    return d['index']
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[Audio] Falha ao consultar dispositivo por nome: {e}", exc_info=True)

    return None


class AudioRecorder:
    """Controla o processo de gravação de áudio do microfone."""

    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._stream: "sd.InputStream" | None = None
        self._lock = threading.Lock()
        self._last_amplitude = 0.0
        self._max_seconds = 0.0
        self._recorded_seconds = 0.0
        self._on_limit_reached = None

    @property
    def is_recording(self) -> bool:
        """Indica se a gravação de áudio está ativa no momento."""
        return self._stream is not None

    def get_last_amplitude(self) -> float:
        """Retorna o último nível de amplitude de som (RMS) calculado.

        Usado pela interface gráfica para fazer as bolinhas ondularem.
        """
        with self._lock:
            return self._last_amplitude

    def start(
        self,
        device_index: int | None = None,
        max_seconds: float = 0.0,
        on_limit_reached: Callable[[], None] | None = None
    ) -> None:
        """Inicia o fluxo de entrada de áudio do microfone especificado de forma assíncrona.

        Limpa os chunks anteriores e redefine a medição de amplitude.
        """
        if self.is_recording:
            return
        with self._lock:
            self._chunks.clear()
            self._last_amplitude = 0.0
            self._max_seconds = max_seconds
            self._recorded_seconds = 0.0
            self._on_limit_reached = on_limit_reached

        import sounddevice as sd
        self._stream = sd.InputStream(
            device=device_index,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=self._callback,
        )
        self._stream.start()

    def stop_and_save(self, path: Path) -> float:
        """Interrompe a gravação e exporta as ondas acumuladas para um arquivo WAV de 16 bits.

        Args:
            path: Caminho local onde o arquivo .wav final será salvo.

        Returns:
            A duração em segundos da gravação de áudio efetuada.
        """
        stream = self._stream
        self._stream = None
        if stream:
            stream.stop()
            stream.close()

        with self._lock:
            if not self._chunks:
                raise RuntimeError("Nenhum áudio foi capturado.")
            # Junta todas as fatias de áudio armazenadas em um único vetor do numpy
            audio = np.concatenate(self._chunks, axis=0)
            self._chunks.clear()

        # Cria os diretórios necessários e salva o arquivo WAV estruturado
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as output:
            output.setnchannels(CHANNELS)
            output.setsampwidth(2)  # 16-bit
            output.setframerate(SAMPLE_RATE)
            output.writeframes(audio.tobytes())

        return len(audio) / SAMPLE_RATE

    def get_current_duration(self) -> float:
        """Retorna a duração atual do áudio gravado em segundos de forma thread-safe."""
        with self._lock:
            if not self._chunks:
                return 0.0
            total_frames = sum(len(c) for c in self._chunks)
            return total_frames / SAMPLE_RATE

    def get_audio_data_range(self, start_sec: float, end_sec: float) -> np.ndarray | None:
        """Une e extrai uma fatia temporal (segundos) dos dados de áudio em buffer na memória."""
        with self._lock:
            if not self._chunks:
                return None
            full_audio = np.concatenate(self._chunks, axis=0)

        start_frame = int(start_sec * SAMPLE_RATE)
        end_frame = int(end_sec * SAMPLE_RATE)

        if start_frame >= len(full_audio):
            return None
        end_frame = min(end_frame, len(full_audio))

        if start_frame >= end_frame:
            return None

        return full_audio[start_frame:end_frame]

    def cancel(self) -> None:
        """Descarta imediatamente a gravação em andamento, abortando o fluxo e limpando buffers."""
        stream = self._stream
        self._stream = None
        if stream:
            stream.abort()
            stream.close()
        with self._lock:
            self._chunks.clear()

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: "sd.CallbackFlags",
    ) -> None:
        """Função interna de callback do sounddevice, executada a cada novo bloco de som capturado.

        Processa os blocos de áudio de entrada e calcula o nível RMS (Root Mean Square)
        da onda sonora para medir a intensidade real da fala humana.
        """
        del time_info
        if status.input_overflow:
            return

        # Calcula a amplitude se o chunk contiver dados válidos
        if len(indata) > 0:
            rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))
            level = float(rms / 32768.0)  # Normaliza em relação ao range máximo do sinal 16-bit
            with self._lock:
                self._last_amplitude = level

        with self._lock:
            self._chunks.append(indata.copy())
            self._recorded_seconds += frames / SAMPLE_RATE

            if self._max_seconds > 0 and self._recorded_seconds >= self._max_seconds:
                # Aciona o callback em uma thread separada para evitar bloquear a thread de áudio
                if self._on_limit_reached:
                    threading.Thread(target=self._on_limit_reached, daemon=True).start()
                    # Zera o limite para que não dispare repetidamente
                    self._max_seconds = 0.0


def save_raw_to_wav(audio_data: np.ndarray, path: Path) -> None:
    """Salva um vetor numpy cru em formato WAV de 16-bit 16kHz Mono."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(CHANNELS)
        output.setsampwidth(2)  # 16-bit
        output.setframerate(SAMPLE_RATE)
        output.writeframes(audio_data.tobytes())
