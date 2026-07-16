"""Módulo de Interface Gráfica (HUD) para o LocalWhisper.

Este módulo implementa o popup flutuante em formato de pílula (pill-shape) que
aparece na tela para guiar o usuário durante as etapas de ditado de voz.

Destaques da Implementação:
1. Janela Não-Ativável (WS_EX_NOACTIVATE):
   Usa chamadas da WinAPI via ctypes para que a janela flutuante apareça na tela
   sem roubar o foco do aplicativo que o usuário está utilizando. O foco do cursor
   permanece intacto na janela alvo original.

2. Transparência de Vidro (Chroma-Key + RGBA + Limiarização):
   Utiliza a cor quase preta "#020202" como chroma-key, e o pill é renderizado
   com técnica RGBA no Pillow. Aplica limiarização binária no canal alpha da
   imagem de alta resolução final para garantir recorte de borda perfeitamente
   nítido no Windows, eliminando qualquer pixel escuro ou serrilhado. A opacidade
   de 88% do vidro é controlada globalmente pela janela de forma limpa.

3. Temas Visuais Dinâmicos:
   - "dots": 5 bolinhas em onda senoidal.
   - "atom": átomo clássico com órbitas inclinadas.
   - "atom_compact": novo tema compacto (180x38), perfeitamente oval (raio 19)
     e com átomo mais delicado, reduzindo espaços vazios.

4. Barra de Progresso Premium:
   Barra de carregamento animada exibida durante transcrição, adaptando-se
   automaticamente à largura do layout ativo.
"""

from __future__ import annotations

import ctypes
import math
import tkinter as tk
from collections.abc import Callable
from ctypes import wintypes

from PIL import Image, ImageDraw, ImageTk

from .config import AppConfig

# ---------- WinAPI para janela não-ativável (HUD flutuante) ----------

_user32 = ctypes.windll.user32
_user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.GetWindowLongW.restype = ctypes.c_long
_user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
_user32.SetWindowLongW.restype = ctypes.c_long

_GWL_EXSTYLE = -20
_WS_EX_NOACTIVATE = 0x08000000
_WS_EX_TOOLWINDOW = 0x00000080

# ---------- Cores e Configurações de Layout ----------

CHROMA = "#020202"  # Chroma-key
BG_FILL = (10, 11, 14)      # Fundo interno
BORDER_FILL = (55, 60, 72)  # Borda
TEXT_COLOR = "#EBEDF2"  # Texto principal
MUTED_COLOR = "#7E8491"  # Subtexto
DOT_COLOR = "#FF6000"  # Bolinhas
SUCCESS_COLOR = "#5CFC7C"
ERROR_COLOR = "#FF647C"
PROGRESS_BG = "#1e2026"
PROGRESS_FILL = "#FF6000"
DOT_COUNT = 5

# Parâmetros de animação do átomo
ATOM_ORBIT_POINTS = 64
ATOM_ORBIT_ROTATIONS = [0.0, math.pi / 3, -math.pi / 3]
ATOM_ORBIT_DIRS = [1, -1, 1]
ATOM_BASE_SPEED = 0.020
ATOM_MAX_SPEED  = 0.50
ATOM_DECAY      = 0.90

# Configurações de tamanho e posicionamento por layout
LAYOUTS = {
    "classic": {
        "width": 230,
        "height": 46,
        "radius": 22,
        "tx": 59,
        "ty_title": 11,
        "ty_sub": 23,
        "prog_x": 14,
        "prog_y": 34,
        "prog_w": 202,
        "prog_h": 3,
        "atom_cx": 20,
        "atom_cy": 18,
        "atom_a": 14,
        "atom_b": 5.5,
        "atom_nucleus_r": 2.5,
        "atom_electron_r": 1.8,
        "dot_x0": 14,
        "dot_gap": 7,
        "dot_r": 2,
    },
    "compact": {
        "width": 180,
        "height": 38,
        "radius": 19,  # Altura 38 / 2 = 19 (oval fofinho perfeito)
        "tx": 40,      # Espaçamento muito mais próximo
        "ty_title": 12,
        "ty_sub": 24,
        "prog_x": 12,
        "prog_y": 30,
        "prog_w": 156,
        "prog_h": 2,
        "atom_cx": 22,
        "atom_cy": 19,
        "atom_a": 10,
        "atom_b": 4.0,
        "atom_nucleus_r": 1.8,
        "atom_electron_r": 1.4,
        "dot_x0": 12,
        "dot_gap": 5.5,
        "dot_r": 1.5,
    },
    "atom_minimal": {
        "width": 46,
        "height": 46,
        "radius": 23,
        "tx": 0,
        "ty_title": 0,
        "ty_sub": 0,
        "prog_x": 0,
        "prog_y": 0,
        "prog_w": 0,
        "prog_h": 0,
        "atom_cx": 23,
        "atom_cy": 23,
        "atom_a": 14,
        "atom_b": 5.5,
        "atom_nucleus_r": 2.5,
        "atom_electron_r": 1.8,
        "dot_x0": 0,
        "dot_gap": 0,
        "dot_r": 0,
    }
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> str:
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _orbit_points(cx: float, cy: float, a: float, b: float, rot: float, n: int) -> list[float]:
    cos_r, sin_r = math.cos(rot), math.sin(rot)
    pts: list[float] = []
    for i in range(n + 1):
        theta = 2 * math.pi * i / n
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        x = cx + a * cos_t * cos_r - b * sin_t * sin_r
        y = cy + a * cos_t * sin_r + b * sin_t * cos_r
        pts.extend([x, y])
    return pts


def _electron_pos(cx: float, cy: float, a: float, b: float, rot: float, angle: float) -> tuple[float, float]:
    cos_r, sin_r = math.cos(rot), math.sin(rot)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    x = cx + a * cos_a * cos_r - b * sin_a * sin_r
    y = cy + a * cos_a * sin_r + b * sin_a * cos_r
    return x, y


class Popup:
    """HUD flutuante e semi-transparente que exibe o status do LocalWhisper.

    Suporta layouts e dimensões dinâmicas baseadas no tema ativo:
    - "dots": 5 bolinhas, layout clássico (230x46).
    - "atom": átomo clássico, layout clássico (230x46).
    - "atom_compact": átomo compacto, layout compacto (180x38).
    """

    def __init__(
        self,
        root: tk.Tk,
        on_cancel: Callable[[], None],
        get_amplitude: Callable[[], float] | None = None,
        config: AppConfig | None = None,
    ) -> None:
        """Inicializa a janela popup Tkinter e define seus estilos WinAPI."""
        self.root = root
        self.on_cancel = on_cancel
        self.get_amplitude = get_amplitude
        self.config = config
        self.phase = 0.0
        self.animating = False
        self.smooth_amp = 0.0
        self._active_theme = "dots"
        self._atom_color = "#FF6000"

        # Progresso
        self._progress_animating = False

        # Estado do átomo
        self._atom_angles = [0.0, math.pi * 2 / 3, math.pi * 4 / 3]
        self._atom_speed = 0.0
        self._atom_trail: list[list[tuple[float, float]]] = [[], [], []]
        self._is_condensing = False
        self._is_exploding = False
        self._explosion_progress = 0.0

        # Custom states for only_atom minimal HUD option
        self.hud_state = "idle"
        self._only_atom_scale = 1.0
        self._error_jitter_x = 0.0
        self._error_jitter_y = 0.0
        self._error_timer = 0

        # Layout ativo (inicializa com o padrão classic)
        self._active_layout = LAYOUTS["classic"]

        # ---- Janela flutuante ----
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=CHROMA)
        self.window.attributes("-transparentcolor", CHROMA)
        self.window.attributes("-alpha", 0.88)

        self.window.update_idletasks()
        self._apply_noactivate()

        # ---- Canvas (inicializa com tamanho clássico) ----
        self.canvas = tk.Canvas(
            self.window, width=230, height=46,
            bg=CHROMA, highlightthickness=0,
        )
        self.canvas.pack()

        # ---- Pill de fundo ----
        self._pill_photo: ImageTk.PhotoImage | None = None
        self._render_pill(230, 46, 22)
        self._bg_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self._pill_photo)

        # ---- Tema "dots": bolinhas ----
        self._dot_ids: list[int] = []
        for i in range(DOT_COUNT):
            did = self.canvas.create_oval(
                0, 0, 1, 1, fill=DOT_COLOR, outline="", state="hidden",
            )
            self._dot_ids.append(did)

        # ---- Tema "atom": núcleo, 3 órbitas, 3 elétrons, 3x2 pontos de trilha ----
        self._atom_nucleus_id = self.canvas.create_oval(
            0, 0, 1, 1, fill=self._atom_color, outline="", state="hidden",
        )

        self._atom_orbit_ids: list[int] = []
        for _ in range(3):
            oid = self.canvas.create_line(
                0, 0, 1, 1, fill="#3a3e48", width=1, smooth=True, state="hidden",
            )
            self._atom_orbit_ids.append(oid)

        self._atom_trail_ids: list[list[int]] = []
        for _ in range(3):
            ring: list[int] = []
            for _ in range(2):
                tid = self.canvas.create_oval(
                    0, 0, 1, 1, fill="#FF4000", outline="", state="hidden",
                )
                ring.append(tid)
            self._atom_trail_ids.append(ring)

        self._atom_electron_ids: list[int] = []
        for _ in range(3):
            eid = self.canvas.create_oval(
                0, 0, 1, 1, fill=self._atom_color, outline="", state="hidden",
            )
            self._atom_electron_ids.append(eid)

        # ---- Textos ----
        self._title_id = self.canvas.create_text(
            0, 0, anchor="w", text="",
            fill=TEXT_COLOR, font=("Segoe UI Semibold", 8),
        )
        self._sub_id = self.canvas.create_text(
            0, 0, anchor="w", text="",
            fill=MUTED_COLOR, font=("Segoe UI", 7),
        )
        self._pct_id = self.canvas.create_text(
            0, 0, anchor="e", text="",
            fill=PROGRESS_FILL, font=("Segoe UI Semibold", 7), state="hidden",
        )

        # ---- Barra de progresso ----
        self._prog_bg_id = self.canvas.create_rectangle(
            0, 0, 1, 1, fill=PROGRESS_BG, outline="", state="hidden",
        )
        self._prog_fill_id = self.canvas.create_rectangle(
            0, 0, 1, 1, fill=PROGRESS_FILL, outline="", state="hidden",
        )

    # ------------------------------------------------------------------ WinAPI

    def _apply_noactivate(self) -> None:
        hwnd = _user32.GetParent(self.window.winfo_id())
        ex = _user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        _user32.SetWindowLongW(
            hwnd, _GWL_EXSTYLE,
            ex | _WS_EX_NOACTIVATE | _WS_EX_TOOLWINDOW,
        )

    # ------------------------------------------------------------ Pill Render

    def _render_pill(self, w: int, h: int, r: int) -> None:
        """Renderiza o pill em super-resolução com limiarização binária do alpha.

        Isso cria um recorte binário cirúrgico nas bordas externas do pill contra a
        cor chroma-key, garantindo que não haverá gradientes semitransparentes
        nas extremidades (o que causa o serrilhado escuro no Windows).
        """
        scale = 4
        sw, sh, sr = w * scale, h * scale, r * scale
        chroma_rgb = (2, 2, 2)

        img_rgba = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img_rgba)

        # Camada da sombra suave interna ao limite
        sm = 3 * scale
        draw.rounded_rectangle(
            ((sm, sm + 2 * scale), (sw - 1 - sm, sh - 1 - sm + 2 * scale)),
            radius=sr, fill=(0, 0, 0, 50),
        )
        # Borda de vidro
        draw.rounded_rectangle(
            ((0, 0), (sw - 1, sh - 1)),
            radius=sr, fill=(*BORDER_FILL, 130),
        )
        # Preenchimento
        bp = 1 * scale
        draw.rounded_rectangle(
            ((bp, bp), (sw - 1 - bp, sh - 1 - bp)),
            radius=sr - bp, fill=(*BG_FILL, 245),
        )

        # Redimensiona para resolução final
        img_final = img_rgba.resize((w, h), Image.LANCZOS)

        # Limiarização binária no canal alpha para recorte cirúrgico
        pixels = img_final.load()
        for y in range(h):
            for x in range(w):
                r_val, g_val, b_val, a_val = pixels[x, y]
                if a_val < 140:
                    pixels[x, y] = (2, 2, 2, 255)  # Fundo chroma-key
                else:
                    pixels[x, y] = (r_val, g_val, b_val, 255)  # Pill opaco

        # Composição final
        img_bg = Image.new("RGB", (w, h), chroma_rgb)
        img_bg.paste(img_final, mask=img_final.split()[3])
        self._pill_photo = ImageTk.PhotoImage(img_bg)

    # ------------------------------------------------------------- APIs Públicas

    def show_recording(self, theme: str = "dots", color: str = "#FF6000") -> None:
        """Exibe o HUD no estado de gravação ativa, aplicando o layout do tema."""
        self._active_theme = theme
        self._atom_color = color
        self.smooth_amp = 0.0
        self._hide_progress()
        self._is_condensing = False
        self._is_exploding = False

        only_atom = (theme == "atom_centered")
        if only_atom:
            self.hud_state = "recording"
            self._only_atom_scale = 1.0
            self._error_jitter_x = 0.0
            self._error_jitter_y = 0.0
            self._error_timer = 0
            self.window.attributes("-alpha", 0.88)

        self._apply_layout(theme)
        if theme != "atom_minimal" and theme != "atom_centered":
            self._set_content("Ouvindo…", "Ctrl+Space para concluir")
        self._reset_indicators()
        self._position()
        self.window.deiconify()
        self.animating = True
        self._animate()

    def show_processing_with_progress(self, audio_duration: float, title_override: str = "Transcrevendo…") -> None:
        """Exibe o HUD no estado de processamento/transcrição local do Whisper."""
        self._apply_layout(self._active_theme)

        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            self.hud_state = "transcribing"
            self.animating = True
            self._reset_indicators()
            self._position()
            self.window.deiconify()
            self._animate()
            return

        if self._active_theme == "atom_minimal":
            self.animating = True
            self._is_condensing = True
        else:
            self.animating = False
            self._set_content(title_override, "Processamento local")

        self._reset_indicators()
        self._position()
        self.window.deiconify()

        self._prog_estimate = max(4.0, audio_duration * 6.0)
        import time
        self._prog_start = time.monotonic()

        if self._active_theme != "atom_minimal":
            self.canvas.itemconfigure(self._prog_bg_id, state="normal")
            self.canvas.itemconfigure(self._prog_fill_id, state="normal")
            self.canvas.itemconfigure(self._pct_id, text="0%", state="normal")
            self._progress_animating = True
            self._animate_real_progress()

    def complete_progress(self) -> None:
        """Finaliza o preenchimento da barra de progresso."""
        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            self.trigger_explosion()
            return

        if self._active_theme == "atom_minimal":
            self.trigger_explosion()
            return

        self._progress_animating = False
        lay = self._active_layout
        self.canvas.coords(self._prog_fill_id, lay["prog_x"], lay["prog_y"], lay["prog_x"] + lay["prog_w"], lay["prog_y"] + lay["prog_h"])
        self.canvas.itemconfigure(self._pct_id, text="100%", state="normal")

    def show_loading_model(self) -> None:
        """Exibe o HUD no estado de carregamento do modelo de IA."""
        self.animating = False
        self._apply_layout(self._active_theme)
        self._set_content("Carregando modelo…", "Inicializando IA")
        self._reset_indicators()
        self._position()
        self.window.deiconify()

        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            self.hud_state = "transcribing"
            self.animating = True
            self._animate()

    def show_message(self, title: str, subtitle: str = "", error: bool = False) -> None:
        """Exibe uma mensagem temporária de status ou erro no HUD."""
        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            if error:
                self.hud_state = "error"
                self.animating = True
                self._error_timer = 0
                self._error_jitter_x = 0.0
                self._error_jitter_y = 0.0
                self._reset_indicators()
                self._position()
                self.window.deiconify()
                self._animate()
            else:
                self.trigger_explosion()
            return

        if self._active_theme == "atom_minimal" and not error:
            # Em mensagens de sucesso com atom_minimal, já engatilhamos a explosão. Mantém rodando
            return

        self.animating = False
        self._hide_progress()
        self._is_condensing = False
        self._is_exploding = False
        self._apply_layout(self._active_theme)
        color = ERROR_COLOR if error else SUCCESS_COLOR
        self._set_content(title, subtitle, title_color=color)
        self._reset_indicators()
        self._position()
        self.window.deiconify()

    def trigger_explosion(self) -> None:
        """Dispara a animação final de explosão do átomo minimalista antes de fechar."""
        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            self.hud_state = "exploding"
            self.animating = True
            self._explosion_frame = 0
            return

        if self._active_theme == "atom_minimal":
            self._is_condensing = False
            self._is_exploding = True
            self._explosion_progress = 0.0

    def hide(self) -> None:
        self.animating = False
        self._progress_animating = False
        self._is_condensing = False
        self._is_exploding = False
        self.hud_state = "idle"
        self._only_atom_scale = 1.0
        self.window.attributes("-alpha", 0.88)
        self.window.withdraw()

    def _set_content(self, title: str, subtitle: str, title_color: str = TEXT_COLOR) -> None:
        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            self.canvas.itemconfigure(self._title_id, state="hidden")
            self.canvas.itemconfigure(self._sub_id, state="hidden")
            return

        if self._active_theme == "atom_minimal":
            return
        self.canvas.itemconfigure(self._title_id, text=title, fill=title_color)
        self.canvas.itemconfigure(self._sub_id, text=subtitle)

    def set_text(self, title: str, subtitle: str, error: bool = False) -> None:
        only_atom = (self._active_theme == "atom_centered")
        if only_atom:
            self.canvas.itemconfigure(self._title_id, state="hidden")
            self.canvas.itemconfigure(self._sub_id, state="hidden")
            return

        if self._active_theme == "atom_minimal":
            return
        color = ERROR_COLOR if error else TEXT_COLOR
        self.canvas.itemconfigure(self._title_id, text=title, fill=color)
        self.canvas.itemconfigure(self._sub_id, text=subtitle)

    # ---------------------------------------------------------------- Layout Dinâmico

    def _apply_layout(self, theme: str) -> None:
        """Aplica as configurações geométricas do tema ativo à janela e aos elementos."""
        is_compact = (theme == "atom_compact")
        lay_key = "compact" if is_compact else "classic"
        lay = LAYOUTS[lay_key]

        only_atom = (theme == "atom_centered")

        if only_atom:
            width, height, radius = 46, 46, 23
            cx, cy = 23, 23
        else:
            width, height, radius = lay['width'], lay['height'], lay['radius']
            cx, cy = lay['atom_cx'], lay['atom_cy']

        self._active_layout = lay.copy()
        self._active_layout['width'] = width
        self._active_layout['height'] = height
        self._active_layout['radius'] = radius
        self._active_layout['atom_cx'] = cx
        self._active_layout['atom_cy'] = cy

        # Redimensiona a janela e o Canvas
        self.window.geometry(f"{width}x{height}")
        self.canvas.configure(width=width, height=height)

        # Recria e aplica o pill de fundo
        self._render_pill(width, height, radius)
        self.canvas.itemconfig(self._bg_image_id, image=self._pill_photo)
        self.canvas.coords(self._bg_image_id, 0, 0)

        # Reposiciona elementos de texto
        self.canvas.coords(self._title_id, lay['tx'], lay['ty_title'])
        self.canvas.coords(self._sub_id, lay['tx'], lay['ty_sub'])
        self.canvas.coords(self._pct_id, width - 12, lay['ty_sub'])

        # Reposiciona a barra de progresso
        self.canvas.coords(self._prog_bg_id, lay['prog_x'], lay['prog_y'], lay['prog_x'] + lay['prog_w'], lay['prog_y'] + lay['prog_h'])
        self.canvas.coords(self._prog_fill_id, lay['prog_x'], lay['prog_y'], lay['prog_x'], lay['prog_y'] + lay['prog_h'])

        # Se for dots, reposiciona as bolinhas
        if theme == "dots":
            if only_atom:
                mid = DOT_COUNT // 2
                for i, did in enumerate(self._dot_ids):
                    if i == mid:
                        self.canvas.coords(did, cx - lay['dot_r'], cy - lay['dot_r'], cx + lay['dot_r'], cy + lay['dot_r'])
                        self.canvas.itemconfigure(did, state="normal")
                    else:
                        self.canvas.itemconfigure(did, state="hidden")
            else:
                cy_dot = height // 2
                for i, did in enumerate(self._dot_ids):
                    x = lay['dot_x0'] + i * lay['dot_gap']
                    self.canvas.coords(did, x - lay['dot_r'], cy_dot - lay['dot_r'], x + lay['dot_r'], cy_dot + lay['dot_r'])
                    self.canvas.itemconfigure(did, state="normal")

        # Se for atom, atualiza órbitas estáticas para as novas dimensões
        elif theme in ("atom", "atom_compact", "atom_centered"):
            self.canvas.coords(self._atom_nucleus_id, cx - lay['atom_nucleus_r'], cy - lay['atom_nucleus_r'], cx + lay['atom_nucleus_r'], cy + lay['atom_nucleus_r'])

            for i, rot in enumerate(ATOM_ORBIT_ROTATIONS):
                pts = _orbit_points(cx, cy, lay['atom_a'], lay['atom_b'], rot, ATOM_ORBIT_POINTS)
                self.canvas.coords(self._atom_orbit_ids[i], *pts)


    # ---------------------------------------------------------------- Progresso

    def _hide_progress(self) -> None:
        self._progress_animating = False
        self.canvas.itemconfigure(self._prog_bg_id, state="hidden")
        self.canvas.itemconfigure(self._prog_fill_id, state="hidden")
        self.canvas.itemconfigure(self._pct_id, state="hidden")

    def _animate_real_progress(self) -> None:
        if not self._progress_animating:
            return
        import time
        lay = self._active_layout
        elapsed = time.monotonic() - self._prog_start
        ratio = min(0.93, 1 - math.exp(-elapsed / (self._prog_estimate * 0.4)))
        fill_w = int(lay['prog_w'] * ratio)
        self.canvas.coords(self._prog_fill_id, lay['prog_x'], lay['prog_y'], lay['prog_x'] + fill_w, lay['prog_y'] + lay['prog_h'])
        self.canvas.itemconfigure(self._pct_id, text=f"{int(ratio * 100)}%", state="normal")
        self.root.after(80, self._animate_real_progress)

    # ---------------------------------------------------------------- Internos

    def _reset_indicators(self) -> None:
        """Oculta todos os indicadores e exibe apenas os do tema ativo."""
        for did in self._dot_ids:
            self.canvas.itemconfigure(did, state="hidden")
        self.canvas.itemconfigure(self._atom_nucleus_id, state="hidden")
        for oid in self._atom_orbit_ids:
            self.canvas.itemconfigure(oid, state="hidden")
        for ring in self._atom_trail_ids:
            for tid in ring:
                self.canvas.itemconfigure(tid, state="hidden")
        for eid in self._atom_electron_ids:
            self.canvas.itemconfigure(eid, state="hidden")

        theme = self._active_theme
        if theme in ("atom", "atom_compact", "atom_centered"):
            atom_rgb = _hex_to_rgb(self._atom_color)
            orbit_idle = _lerp_color((58, 62, 72), atom_rgb, 0.18)

            self.canvas.itemconfigure(self._atom_nucleus_id, fill=self._atom_color, state="normal")
            for oid in self._atom_orbit_ids:
                self.canvas.itemconfigure(oid, fill=orbit_idle, state="normal")
            for ring in self._atom_trail_ids:
                for tid in ring:
                    self.canvas.itemconfigure(tid, state="normal")
            for eid in self._atom_electron_ids:
                self.canvas.itemconfigure(eid, fill=self._atom_color, state="normal")

            self._atom_speed = 0.0
            self._atom_angles = [0.0, math.pi * 2 / 3, math.pi * 4 / 3]
            self._atom_trail = [[], [], []]
        else:
            only_atom = (self._active_theme == "atom_centered")
            if only_atom:
                mid = DOT_COUNT // 2
                for i, did in enumerate(self._dot_ids):
                    if i == mid:
                        self.canvas.itemconfigure(did, state="normal")
                    else:
                        self.canvas.itemconfigure(did, state="hidden")
            else:
                for did in self._dot_ids:
                    self.canvas.itemconfigure(did, state="normal")

    def _position(self) -> None:
        self.window.update_idletasks()
        lay = self._active_layout
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - lay['width']) // 2
        y = sh - lay['height'] - 80
        self.window.geometry(f"{lay['width']}x{lay['height']}+{x}+{y}")

    # ---------------------------------------------------------------- Animações

    def _animate(self) -> None:
        if not self.animating:
            return
        if self._active_theme in ("atom", "atom_compact", "atom_centered"):
            self._animate_atom()
        else:
            self._animate_dots()

    def _animate_dots(self) -> None:
        if not self.animating:
            return
        lay = self._active_layout
        only_atom = (self._active_theme == "atom_centered")

        if only_atom:
            # Animates a single centered dot
            cx = lay['atom_cx']
            cy = lay['atom_cy']

            # State transitions
            if self.hud_state == "transcribing":
                self._only_atom_scale = self._only_atom_scale * 0.93 + 0.25 * 0.07
            elif self.hud_state == "exploding":
                self._only_atom_scale += 0.06
                opacity = max(0.0, 1.0 - self._explosion_frame / 30.0)
                self._explosion_frame += 1
                self.window.attributes("-alpha", 0.88 * opacity)
                if opacity <= 0.0 or self._only_atom_scale >= 2.2:
                    self.hide()
                    return
            elif self.hud_state == "error":
                self._only_atom_scale = self._only_atom_scale * 0.90 + 0.4 * 0.10
                import random
                self._error_jitter_x = random.uniform(-2.0, 2.0)
                self._error_jitter_y = random.uniform(-2.0, 2.0)
                cx += self._error_jitter_x
                cy += self._error_jitter_y
                self._error_timer += 1
                if self._error_timer > 40:
                    self._error_timer = 0
                    self.hide()
                    return
            else:
                self._only_atom_scale = 0.80

            amp = self.get_amplitude() if self.get_amplitude else 0.0
            amp_clean = max(0.0, amp - 0.0015)
            target = min(1.0, amp_clean * 300.0)
            self.smooth_amp = self.smooth_amp * 0.7 + target * 0.3

            # Calculate radius
            if self.hud_state == "recording":
                r = lay['dot_r'] * (1.0 + self.smooth_amp * 2.5)
                dot_color = DOT_COLOR
            elif self.hud_state == "error":
                r = lay['dot_r'] * self._only_atom_scale
                dot_color = ERROR_COLOR
            else:
                r = lay['dot_r'] * self._only_atom_scale
                dot_color = DOT_COLOR

            # Update middle dot
            mid = DOT_COUNT // 2
            for i, did in enumerate(self._dot_ids):
                if i == mid:
                    self.canvas.coords(did, cx - r, cy - r, cx + r, cy + r)
                    self.canvas.itemconfigure(did, fill=dot_color, state="normal")
                else:
                    self.canvas.itemconfigure(did, state="hidden")

            self.root.after(30, self._animate)
            return

        cy = lay['height'] // 2
        amp = self.get_amplitude() if self.get_amplitude else 0.0
        amp_clean = max(0.0, amp - 0.0015)
        target = min(1.0, amp_clean * 300.0)
        self.smooth_amp = self.smooth_amp * 0.7 + target * 0.3

        for i, did in enumerate(self._dot_ids):
            wave = math.sin(self.phase + i * 1.0)
            offset = wave * self.smooth_amp * 5.0
            x = lay['dot_x0'] + i * lay['dot_gap']
            y = cy + offset
            self.canvas.coords(did, x - lay['dot_r'], y - lay['dot_r'], x + lay['dot_r'], y + lay['dot_r'])

        self.phase += 0.35
        self.root.after(40, self._animate)

    def _animate_atom(self) -> None:
        if not self.animating and not self._is_exploding and self.hud_state != "exploding":
            return

        lay = self._active_layout
        only_atom = (self._active_theme == "atom_centered")

        # State and scaling transitions
        if only_atom:
            if self.hud_state == "transcribing":
                self._only_atom_scale = self._only_atom_scale * 0.93 + 0.25 * 0.07
            elif self.hud_state == "exploding":
                self._only_atom_scale += 0.06
                opacity = max(0.0, 1.0 - self._explosion_frame / 30.0)
                self._explosion_frame += 1
                self.window.attributes("-alpha", 0.88 * opacity)
                if opacity <= 0.0 or self._only_atom_scale >= 2.2:
                    self.hide()
                    return
            elif self.hud_state == "error":
                self._only_atom_scale = self._only_atom_scale * 0.90 + 0.4 * 0.10
                import random
                self._error_jitter_x = random.uniform(-2.0, 2.0)
                self._error_jitter_y = random.uniform(-2.0, 2.0)
                self._error_timer += 1
                if self._error_timer > 40:
                    self._error_timer = 0
                    self.hide()
                    return
            else:
                self._only_atom_scale = 0.80
                self._error_jitter_x = 0.0
                self._error_jitter_y = 0.0
        else:
            self._only_atom_scale = 1.0
            self._error_jitter_x = 0.0
            self._error_jitter_y = 0.0

        scale = self._only_atom_scale
        cx = lay['atom_cx'] + getattr(self, '_error_jitter_x', 0.0)
        cy = lay['atom_cy'] + getattr(self, '_error_jitter_y', 0.0)
        a = lay['atom_a'] * scale
        b = lay['atom_b'] * scale
        er = lay['atom_electron_r'] * scale
        nr = lay['atom_nucleus_r'] * scale

        amp = self.get_amplitude() if self.get_amplitude else 0.0
        amp_clean = max(0.0, amp - 0.0015)
        target = min(1.0, amp_clean * 300.0)
        self.smooth_amp = self.smooth_amp * 0.72 + target * 0.28
        sa = self.smooth_amp

        # Determine angular speed and colors
        if only_atom and self.hud_state in ("transcribing", "exploding", "error"):
            self._atom_speed = 0.0
            if self.hud_state == "error":
                orbit_color = ERROR_COLOR
                electron_color = ERROR_COLOR
                nuc_color = ERROR_COLOR
            else:
                orbit_color = self._atom_color
                electron_color = self._atom_color
                nuc_color = self._atom_color
        else:
            # Fallback to the original agent's minimal theme transitions if not only_atom
            if self._is_exploding:
                self._explosion_progress += 0.15
                if self._explosion_progress > 1.2:
                    self.hide()
                    return

                scale = 1.0 + (self._explosion_progress ** 2) * 8.0
                a = lay['atom_a'] * scale
                b = lay['atom_b'] * scale
                nr = nr * (1.0 + self._explosion_progress * 4.0)
                er = er * (1.0 + self._explosion_progress * 3.0)
                sa = max(0.0, 1.0 - self._explosion_progress)
                self._atom_speed = ATOM_MAX_SPEED * max(0.0, 1.0 - self._explosion_progress)

            elif self._is_condensing:
                self.smooth_amp *= 0.8
                sa = self.smooth_amp
                self._atom_speed *= 0.85

                speed_ratio = min(1.0, self._atom_speed / ATOM_BASE_SPEED) if ATOM_BASE_SPEED > 0 else 0
                scale = 0.35 + (0.65 * speed_ratio)
                a = lay['atom_a'] * scale
                b = lay['atom_b'] * scale
                nr = nr * (0.6 + 0.4 * speed_ratio)
                er = er * (0.6 + 0.4 * speed_ratio)

            else:
                target_speed = ATOM_BASE_SPEED + sa * (ATOM_MAX_SPEED - ATOM_BASE_SPEED)
                if sa > 0.015:
                    self._atom_speed = self._atom_speed * 0.78 + target_speed * 0.22
                else:
                    self._atom_speed *= ATOM_DECAY
                    if self._atom_speed < 0.001:
                        self._atom_speed = 0.0

                a = lay['atom_a']
                b = lay['atom_b']

            atom_rgb = _hex_to_rgb(self._atom_color)
            white = (255, 255, 255)
            orbit_idle_rgb = (58, 62, 72)

            orbit_color = _lerp_color(
                _hex_to_rgb(_lerp_color(orbit_idle_rgb, atom_rgb, 0.25)),
                atom_rgb,
                sa,
            )
            electron_color = _lerp_color(atom_rgb, white, sa * 0.75)

            # Se estiver explodindo e o progresso > 0.5, começa a fazer fade para o fundo do vidro (limiar invisível)
            if self._is_exploding and self._explosion_progress > 0.5:
                fade_ratio = min(1.0, (self._explosion_progress - 0.5) * 2)
                electron_color = _lerp_color(_hex_to_rgb(electron_color), _hex_to_rgb(CHROMA), fade_ratio)
                orbit_color = _lerp_color(_hex_to_rgb(orbit_color), _hex_to_rgb(CHROMA), fade_ratio)
                nuc_color = _lerp_color(atom_rgb, _hex_to_rgb(CHROMA), fade_ratio)
            else:
                nuc_color = self._atom_color

        # Update static elements when scaling/position changes
        self.canvas.coords(self._atom_nucleus_id, cx - nr, cy - nr, cx + nr, cy + nr)
        self.canvas.itemconfigure(self._atom_nucleus_id, fill=nuc_color)

        for i, oid in enumerate(self._atom_orbit_ids):
            rot = ATOM_ORBIT_ROTATIONS[i]
            pts = _orbit_points(cx, cy, a, b, rot, ATOM_ORBIT_POINTS)
            self.canvas.coords(oid, *pts)
            self.canvas.itemconfigure(oid, fill=orbit_color)

        if self._atom_speed > 0.0:
            for i in range(3):
                self._atom_angles[i] += self._atom_speed * ATOM_ORBIT_DIRS[i]

        for i, rot in enumerate(ATOM_ORBIT_ROTATIONS):
            angle = self._atom_angles[i]
            ex, ey = _electron_pos(cx, cy, a, b, rot, angle)

            trail = self._atom_trail[i]
            if not only_atom or self._atom_speed > 0.0:
                trail.append((ex, ey))
                if len(trail) > 3:
                    trail.pop(0)
            else:
                trail.clear()

            trail_ids = self._atom_trail_ids[i]
            for t, tid in enumerate(trail_ids):
                if not trail or len(trail) == 0:
                    self.canvas.coords(tid, 0, 0, 0, 0)
                    continue
                hist_idx = len(trail) - 2 - t
                if hist_idx < 0:
                    self.canvas.coords(tid, 0, 0, 0, 0)
                    continue
                tx_h, ty_h = trail[hist_idx]
                age = (len(trail_ids) - t) / len(trail_ids)
                trail_r = max(0.3, er * age * 0.55 * sa)
                if not only_atom and self._is_exploding:
                    trail_r = er * age
                self.canvas.coords(tid,
                    tx_h - trail_r, ty_h - trail_r,
                    tx_h + trail_r, ty_h + trail_r)

                atom_rgb = _hex_to_rgb(self._atom_color)
                trail_color = _lerp_color((20, 20, 20), atom_rgb, age * sa * 0.7)
                if not only_atom and self._is_exploding and self._explosion_progress > 0.5:
                    fade_ratio = min(1.0, (self._explosion_progress - 0.5) * 2)
                    trail_color = _lerp_color(_hex_to_rgb(trail_color), _hex_to_rgb(CHROMA), fade_ratio)
                self.canvas.itemconfigure(tid, fill=trail_color)

            self.canvas.coords(
                self._atom_electron_ids[i],
                ex - er, ey - er, ex + er, ey + er,
            )
            self.canvas.itemconfigure(self._atom_electron_ids[i], fill=electron_color)

        self.root.after(25, self._animate)
