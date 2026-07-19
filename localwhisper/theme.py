"""Design System do Quantum Scribe — temas dinâmicos (escuro/claro) e cores de destaque.

Este módulo centraliza toda a paleta de cores da interface de configurações.
A partir de apenas dois parâmetros escolhidos pelo usuário — modo (dark/light)
e cor de destaque — ele deriva uma paleta completa e harmoniosa no estilo Apple,
garantindo contraste e consistência em todos os componentes.
"""

from __future__ import annotations

from dataclasses import dataclass

# Cor de destaque padrão do produto (violeta Quantum)
DEFAULT_ACCENT = "#BF5AF2"

# Presets de cores de destaque oferecidos na tela de Aparência.
# A primeira é sempre a identidade padrão do produto.
ACCENT_PRESETS: list[tuple[str, str]] = [
    ("Roxo", "#BF5AF2"),
    ("Laranja", "#FF6000"),
    ("Rosa", "#FF2D78"),
    ("Azul", "#0A84FF"),
    ("Verde", "#30D158"),
    ("Amarelo", "#FFD60A"),
]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converte '#RRGGBB' em tupla (r, g, b); tolerante a entradas inválidas."""
    value = hex_color.strip().lstrip("#")
    if len(value) != 6:
        return (191, 90, 242)
    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    except ValueError:
        return (191, 90, 242)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, c)) for c in rgb])


def darken(hex_color: str, factor: float = 0.82) -> str:
    """Escurece uma cor multiplicando seus canais pelo fator informado."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex((int(r * factor), int(g * factor), int(b * factor)))


def lighten(hex_color: str, factor: float = 1.18) -> str:
    """Clareia uma cor multiplicando seus canais pelo fator informado."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex((int(r * factor), int(g * factor), int(b * factor)))


def ideal_text_on(hex_color: str) -> str:
    """Retorna preto ou branco conforme a luminância da cor de fundo."""
    r, g, b = _hex_to_rgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#000000" if luminance > 0.62 else "#FFFFFF"


@dataclass(frozen=True, slots=True)
class Theme:
    """Paleta completa derivada do modo (dark/light) e da cor de destaque."""

    mode: str            # "dark" ou "light"
    accent: str          # Cor de destaque escolhida (#RRGGBB)
    accent_hover: str    # Variante de hover/pressionado do destaque
    accent_soft: str     # Destaque com baixa saturação para seleções sutis
    on_accent: str       # Cor de texto ideal sobre o destaque

    bg: str              # Fundo principal da janela
    sidebar_bg: str      # Fundo da barra lateral
    sidebar_active: str  # Fundo do item ativo na barra lateral
    card_bg: str         # Fundo dos cards/grupos
    input_bg: str        # Fundo de campos de entrada
    hover_bg: str        # Fundo de hover em linhas clicáveis
    border: str          # Bordas e divisórias
    text: str            # Texto principal
    muted: str           # Texto secundário/legendas
    danger: str          # Erros e ações destrutivas
    success: str         # Confirmações e estados ativos
    warning: str         # Avisos
    track: str           # Trilho de barras de progresso


def build_theme(mode: str = "dark", accent: str = DEFAULT_ACCENT) -> Theme:
    """Monta a paleta completa a partir do modo e da cor de destaque."""
    if mode not in ("dark", "light"):
        mode = "dark"
    if not accent or not accent.startswith("#"):
        accent = DEFAULT_ACCENT

    accent_hover = darken(accent, 0.8)
    on_accent = ideal_text_on(accent)

    if mode == "dark":
        return Theme(
            mode=mode,
            accent=accent,
            accent_hover=accent_hover,
            accent_soft=darken(accent, 0.32),
            on_accent=on_accent,
            bg="#0A0B0D",
            sidebar_bg="#101216",
            sidebar_active="#1E212A",
            card_bg="#14161B",
            input_bg="#1C1F26",
            hover_bg="#1A1D24",
            border="#2A2D35",
            text="#F0F2F5",
            muted="#8A8F9D",
            danger="#FF453A",
            success="#30D158",
            warning="#FFD60A",
            track="#26292F",
        )

    return Theme(
        mode=mode,
        accent=accent,
        accent_hover=accent_hover,
        accent_soft=lighten(accent, 2.6) if ideal_text_on(accent) == "#FFFFFF" else lighten(accent, 1.6),
        on_accent=on_accent,
        bg="#F2F2F7",
        sidebar_bg="#E9E9EE",
        sidebar_active="#DCDCE3",
        card_bg="#FFFFFF",
        input_bg="#ECECF1",
        hover_bg="#F4F4F8",
        border="#D3D3DB",
        text="#1C1C1E",
        muted="#6E6E73",
        danger="#FF3B30",
        success="#248A3D",
        warning="#B25000",
        track="#E2E2E8",
    )


def font_family(root=None) -> str:
    """Escolhe a melhor família tipográfica disponível (estilo Apple no Windows)."""
    preferred = ("Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", "Arial")
    try:
        from tkinter import font as tkfont
        families = set(tkfont.families(root)) if root is not None else set(tkfont.families())
        for name in preferred:
            if name in families:
                return name
    except Exception:
        pass
    return "Segoe UI"
