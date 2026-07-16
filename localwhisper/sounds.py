"""Módulo de Síntese e Reprodução de Efeitos Sonoros do LocalWhisper.

Este módulo gera formas de onda senoidais na memória via numpy e as
reproduz assincronamente através do sounddevice para evitar arquivos
de áudio externos.

Filosofia de design sonoro:
- play_start_sound  → "abertura": acorde ascendente suave, mesmo DNA harmônico do fim.
- play_end_sound    → "fechamento": acorde descendente com decaimento exponencial (som original aprovado).
- play_cancel_sound → "erro premium": batimento harmônico de duas notas próximas, suave e não agressivo.
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 16_000  # Frequência de amostragem padrão de 16kHz (mesma do Whisper)


def generate_beep(freq: float, duration: float, volume: float) -> np.ndarray:
    """Gera uma onda senoidal pura com rampa nas bordas para evitar estalos."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)

    # Rampa de fade-in e fade-out de 10ms (ou metade do tamanho da onda se for muito curta)
    fade_len = min(int(SAMPLE_RATE * 0.01), len(wave) // 2)
    if fade_len > 0:
        envelope = np.ones_like(wave)
        envelope[:fade_len] = np.linspace(0, 1, fade_len)
        envelope[-fade_len:] = np.linspace(1, 0, fade_len)
        wave = wave * envelope

    return wave * volume


def play_start_sound(volume: float = 0.5) -> None:
    """Toca o som de início da gravação.

    Usa o mesmo DNA harmônico do play_end_sound (130Hz / 195Hz / 260Hz),
    mas com envelope *crescente* — soa como a 'abertura' do par sonoro.
    Duração curta (0.20s) para não atrasar o início da gravação.
    """
    try:
        import sounddevice as sd
        duration = 0.20
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

        # Mesmo acorde do som de fim: Fundamental, Quinta e Oitava
        w1 = np.sin(2 * np.pi * 130.0 * t)
        w2 = np.sin(2 * np.pi * 195.0 * t)
        w3 = np.sin(2 * np.pi * 260.0 * t)

        # Mixagem normalizada (mesmas proporções do fim)
        wave = (w1 + 0.6 * w2 + 0.4 * w3) / 2.0

        # Envelope crescente (ataque logarítmico) — espelho do decaimento exponencial do fim
        envelope = np.zeros_like(t)
        fade_in = int(SAMPLE_RATE * 0.008)  # Ataque curtíssimo de 8ms para evitar estalo
        envelope[:fade_in] = np.linspace(0, 1, fade_in)
        # Crescimento suave com curva logarítmica invertida
        rise_t = t[fade_in:]
        envelope[fade_in:] = 1.0 - np.exp(-6.0 * (rise_t - rise_t[0]) / duration)

        # Fade-out nos últimos 20ms para evitar estalo no fim
        fade_out = int(SAMPLE_RATE * 0.02)
        envelope[-fade_out:] *= np.linspace(1, 0, fade_out)

        sound = wave * envelope * volume
        sd.play(sound, SAMPLE_RATE)
    except Exception:
        pass


def play_end_sound(volume: float = 0.5) -> None:
    """Toca o som de fim de transcrição (acorde harmônico grave e marcante)."""
    try:
        import sounddevice as sd
        duration = 0.45
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

        # Fundamental (130Hz), Quinta (195Hz) e Oitava (260Hz)
        w1 = np.sin(2 * np.pi * 130.0 * t)
        w2 = np.sin(2 * np.pi * 195.0 * t)
        w3 = np.sin(2 * np.pi * 260.0 * t)

        # Mixagem normalizada
        wave = (w1 + 0.6 * w2 + 0.4 * w3) / 2.0

        # Envelope de decaimento exponencial
        envelope = np.ones_like(t)
        fade_in = int(SAMPLE_RATE * 0.01)
        envelope[:fade_in] = np.linspace(0, 1, fade_in)
        decay_t = t[fade_in:] - 0.01
        envelope[fade_in:] = np.exp(-5.0 * decay_t / duration)

        sound = wave * envelope * volume
        sd.play(sound, SAMPLE_RATE)
    except Exception:
        pass


def play_cancel_sound(volume: float = 0.5) -> None:
    """Toca o som de cancelamento/erro.

    Usa duas notas ligeiramente dissonantes sobrepostas (160Hz e 180Hz)
    criando um batimento harmônico suave — transmite 'erro' sem ser agressivo.
    Envelope de decaimento rápido (0.25s) mantém o estilo premium e discreto.
    """
    try:
        import sounddevice as sd
        duration = 0.25
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

        # Duas notas próximas criam batimento audível (percepção de 'falha' suave)
        w1 = np.sin(2 * np.pi * 160.0 * t)
        w2 = np.sin(2 * np.pi * 210.0 * t)  # Terça menor — dissonância controlada

        # Sub-harmônico grave para dar peso ao som de erro
        w_sub = np.sin(2 * np.pi * 80.0 * t) * 0.4

        wave = (w1 + 0.7 * w2 + w_sub) / 2.1

        # Envelope: ataque imediato + decaimento exponencial médio
        envelope = np.ones_like(t)
        fade_in = int(SAMPLE_RATE * 0.006)
        envelope[:fade_in] = np.linspace(0, 1, fade_in)
        decay_t = t[fade_in:] - (fade_in / SAMPLE_RATE)
        envelope[fade_in:] = np.exp(-7.0 * decay_t / duration)

        sound = wave * envelope * volume
        sd.play(sound, SAMPLE_RATE)
    except Exception:
        pass
