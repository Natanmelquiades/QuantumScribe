"""Módulo de Aprimoramento de Áudio para Maximizar Qualidade de Transcrição.

Aplica pipeline de pré-processamento ao áudio bruto do microfone antes de
enviar ao Whisper, garantindo qualidade mesmo em microfones ruins ou ambientes
com ruído de fundo.

Pipeline (em ordem):
    1. Filtro passa-alta (80Hz)     — Remove ronco mecânico, vibração de mesa, ruído de cabo
    2. Supressão de ruído espectral — Limpa fundo de microfone barato e ruído estacionário
    3. Normalização RMS             — Garante volume adequado mesmo para voz baixa
    4. Ganho adaptativo com clip    — Amplifica sem distorcer

Requisitos opcionais:
    noisereduce>=3.0    (pip install noisereduce) — Supressão de ruído espectral
    scipy>=1.13         (pip install scipy)       — Filtros digitais
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 16_000

# Nível RMS alvo após normalização (~-22dBFS).
# O Whisper performa melhor neste range de volume.
TARGET_RMS: float = 0.08

# Limites do ganho adaptativo: [min_gain, max_gain]
# min_gain = ÷3 (~-10dB), max_gain = ×12 (~+22dB)
GAIN_MIN: float = 0.33
GAIN_MAX: float = 12.0


# ---- Conversão de tipos --------------------------------------------------------

def to_float32(audio_int16: np.ndarray) -> np.ndarray:
    """Normaliza array int16 para float32 em [-1.0, 1.0]."""
    return audio_int16.astype(np.float32) / 32768.0


def to_int16(audio_float32: np.ndarray) -> np.ndarray:
    """Converte float32 [-1.0, 1.0] de volta para int16 com saturação."""
    clipped = np.clip(audio_float32, -1.0, 1.0)
    return (clipped * 32767).astype(np.int16)


# ---- Estágios do pipeline ------------------------------------------------------

def apply_highpass_filter(audio: np.ndarray, cutoff_hz: float = 80.0) -> np.ndarray:
    """Filtro Butterworth passa-alta de 4ª ordem.

    Remove ronco mecânico de mesa, vibrações, ruído de cabo de microfone e qualquer
    componente de baixa frequência que confunde o Whisper sem carregar informação de voz.

    Args:
        audio: Array float32 mono.
        cutoff_hz: Frequência de corte em Hz (padrão 80 Hz é seguro para voz).

    Returns:
        Array float32 filtrado. Se scipy não estiver disponível, retorna intacto.
    """
    try:
        from scipy.signal import butter, filtfilt
        nyquist = SAMPLE_RATE / 2.0
        b, a = butter(4, cutoff_hz / nyquist, btype="high")
        return filtfilt(b, a, audio).astype(np.float32)
    except ImportError:
        return audio


def apply_noise_reduction(audio: np.ndarray) -> np.ndarray:
    """Supressão de ruído espectral via noisereduce (spectral gating).

    Estima o perfil de ruído e o subtrai do sinal de fala. Especialmente eficaz
    para ruídos estacionários como ventiladores, ar condicionado e fundo de
    microfone de baixo custo.

    Args:
        audio: Array float32 mono [-1, 1].

    Returns:
        Array float32 com ruído reduzido. Se noisereduce não estiver disponível,
        retorna intacto.
    """
    try:
        import noisereduce as nr
        reduced = nr.reduce_noise(
            y=audio,
            sr=SAMPLE_RATE,
            stationary=False,      # Suporta ruído não-estacionário (vozes de fundo)
            prop_decrease=0.75,    # Remove 75% do ruído estimado — conservador para voz
            n_fft=512,             # FFT menor = menos artefatos em chunks curtos
            win_length=512,
            hop_length=128,
        )
        return reduced.astype(np.float32)
    except ImportError:
        return audio


def apply_rms_normalization(audio: np.ndarray) -> np.ndarray:
    """Normaliza o volume do áudio para um nível RMS alvo.

    Garante que voz baixa seja amplificada ao nível ideal para o Whisper,
    sem distorcer voz alta. O ganho é limitado para evitar amplificar silêncio.

    Args:
        audio: Array float32 mono [-1, 1].

    Returns:
        Array float32 com volume normalizado.
    """
    rms = float(np.sqrt(np.mean(audio ** 2)))

    # Sinal de silêncio puro — não aplica ganho para evitar amplificar ruído de fundo
    if rms < 1e-8:
        return audio

    gain = TARGET_RMS / rms
    # Limita o ganho para não distorcer sinais já adequados ou amplificar demais
    gain = float(np.clip(gain, GAIN_MIN, GAIN_MAX))
    normalized = audio * gain
    return np.clip(normalized, -1.0, 1.0).astype(np.float32)


# ---- Funções públicas principais -----------------------------------------------

def enhance_audio_for_whisper(
    audio_int16: np.ndarray,
    profile: str | bool = "balanced",
) -> np.ndarray:
    """Pipeline completo de aprimoramento — retorna float32 pronto para o Whisper.

    Esta é a função principal usada pelo StreamTranscriber. Retorna float32
    normalizado em [-1, 1], que o faster-whisper aceita diretamente sem precisar
    de arquivo WAV intermediário.

    Args:
        audio_int16: Array int16 de áudio mono 16kHz capturado pelo microfone.
        profile: Perfil de aprimoramento ("fast", "balanced", "quality") ou bool para compatibilidade.

    Returns:
        Array float32 aprimorado, pronto para faster-whisper.transcribe(audio).
    """
    # Trata compatibilidade com boolean antigo
    if isinstance(profile, bool):
        profile = "quality" if profile else "balanced"

    if profile not in ("fast", "balanced", "quality"):
        profile = "balanced"

    # 1. Normaliza int16 → float32 [-1, 1]
    audio = to_float32(audio_int16)

    # 2. Filtro passa-alta — remove ronco
    if profile in ("balanced", "quality"):
        audio = apply_highpass_filter(audio, cutoff_hz=80.0)

    # 3. Supressão de ruído espectral
    if profile == "quality":
        audio = apply_noise_reduction(audio)

    # 4. Normalização de volume (voz baixa → amplifica; voz alta → atenua)
    audio = apply_rms_normalization(audio)

    # Garante range correto para o Whisper
    return np.clip(audio, -1.0, 1.0).astype(np.float32)


def enhance_audio_chunk(
    audio_int16: np.ndarray,
    profile: str | bool = "balanced",
) -> np.ndarray:
    """Aprimora o áudio e retorna int16 (para salvar em WAV ou no recorder clássico).

    Args:
        audio_int16: Array int16 de áudio mono 16kHz.
        profile: Perfil de aprimoramento ("fast", "balanced", "quality") ou bool para compatibilidade.

    Returns:
        Array int16 aprimorado.
    """
    audio_f = enhance_audio_for_whisper(audio_int16, profile)
    return to_int16(audio_f)


def is_noisereduce_available() -> bool:
    """Verifica se a biblioteca noisereduce está instalada."""
    try:
        import noisereduce  # noqa: F401
        return True
    except ImportError:
        return False


def is_scipy_available() -> bool:
    """Verifica se o scipy está instalado (necessário para o filtro passa-alta)."""
    try:
        import scipy  # noqa: F401
        return True
    except ImportError:
        return False
