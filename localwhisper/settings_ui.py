"""Interface Gráfica do Painel de Configurações do Quantum Scribe (v2.1.9).

Este módulo implementa a janela interativa de configurações em Tkinter,
alinhada rigorosamente de acordo com o Design System do projeto,
com barra lateral de navegação premium perfeitamente alinhada à esquerda.
"""

from __future__ import annotations

import glob
import importlib.util
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font, messagebox, ttk
from typing import Callable

from PIL import Image, ImageDraw, ImageTk

from .backup import create_backup, delete_backup, get_project_root, list_backups, restore_backup
from .config import AppConfig, is_model_downloaded
from .diary import diary_dir
from .hotkey import _parse_hotkey


def load_or_generate_icon() -> Image.Image:
    """Carrega o ícone oficial em assets/icon.png ou desenha programaticamente se não existir."""
    # Define caminho
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    icon_path = assets_dir / "icon.png"

    if icon_path.exists():
        try:
            return Image.open(icon_path)
        except Exception:
            pass

    # Desenha o ícone programático premium
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Círculo de fundo preto profundo
    draw.ellipse((8, 8, 248, 248), fill=(10, 11, 14, 255), outline=None)

    # 2. Borda circular neon laranja
    draw.ellipse((8, 8, 248, 248), fill=None, outline=(255, 96, 0, 255), width=6)

    # 3. Desenho de órbitas de átomo em laranja suave
    orb_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    orb_draw = ImageDraw.Draw(orb_img)
    orb_draw.ellipse((40, 113, 216, 143), fill=None, outline=(255, 120, 40, 120), width=3)

    img.alpha_composite(orb_img)
    img.alpha_composite(orb_img.rotate(60, resample=Image.BICUBIC))
    img.alpha_composite(orb_img.rotate(-60, resample=Image.BICUBIC))

    # 4. Desenha microfone estilizado no centro
    draw.rounded_rectangle((108, 70, 148, 140), radius=15, fill=(255, 96, 0, 255))
    draw.rounded_rectangle((114, 76, 142, 100), radius=6, fill=(55, 60, 72, 255))
    draw.arc((96, 95, 160, 155), start=0, end=180, fill=(255, 96, 0, 255), width=4)
    draw.line((128, 155, 128, 185), fill=(255, 96, 0, 255), width=5)
    draw.line((100, 185, 156, 185), fill=(255, 96, 0, 255), width=5)

    # 5. Bolinhas dos elétrons
    draw.ellipse((190, 95, 202, 107), fill=(255, 238, 128, 255), outline=None)
    draw.ellipse((54, 95, 66, 107), fill=(255, 238, 128, 255), outline=None)
    draw.ellipse((122, 210, 134, 222), fill=(255, 238, 128, 255), outline=None)

    try:
        img.save(icon_path, "PNG")
    except Exception:
        pass

    return img


# DESIGN SYSTEM: Paleta de Cores (Tema Preto, Laranja e Cinza Espacial)
BG_COLOR = "#0a0b0d"        # Fundo principal (Preto profundo)
SIDEBAR_BG = "#13151a"      # Fundo da barra lateral
CARD_BG = "#111317"         # Fundo de grupos/cards
INPUT_BG = "#181a21"        # Fundo dos campos de entrada
BORDER_COLOR = "#2c2f36"    # Borda dos campos e divisórias
TEXT_COLOR = "#f0f2f5"      # Texto principal
MUTED_COLOR = "#8a8f9d"     # Texto secundário/status
ACCENT_COLOR = "#ff6000"    # Cor de destaque (Laranja neon)
ACCENT_HOVER = "#d65000"    # Cor de hover
DANGER_COLOR = "#ff4d4d"    # Cor de erro/alerta
CANCEL_BG = "#1e2026"       # Fundo do botão cancelar
CANCEL_HOVER = "#272a33"    # Hover do botão cancelar
SUCCESS_COLOR = "#30d158"   # Verde ativo estilo Apple
SIDEBAR_ACTIVE = "#20232b"  # Cor do item ativo na sidebar


# Mapeamento de Modelos Whisper
MODELS_MAP = {
    "tiny": {
        "id": "tiny",
        "name": "Super Leve (Tiny)",
        "desc": "Transcreve muito rápido, mas pode errar pontuações e termos complexos (~75MB)",
    },
    "base": {
        "id": "base",
        "name": "Leve (Base)",
        "desc": "Bom equilíbrio entre velocidade e precisão básica (~145MB)",
    },
    "small": {
        "id": "small",
        "name": "Equilibrado (Small)",
        "desc": "Recomendado! Ótima precisão e velocidade para uso diário (~460MB)",
    },
    "medium": {
        "id": "medium",
        "name": "Alto Desempenho / Pro (Medium)",
        "desc": "Excelente precisão, ideal para termos técnicos (~1.5GB)",
    },
    "large-v3": {
        "id": "large-v3",
        "name": "Ultra / Máximo (Large-v3)",
        "desc": "Precisão máxima absoluta, consome mais memória GPU/RAM (~3.0GB)",
    }
}


class ModernDropdown(tk.Frame):
    """Dropdown nativo moderno com largura padronizada de 22 caracteres."""
    def __init__(self, parent, variable, values, width=22, command=None, *args, **kwargs):
        super().__init__(parent, bg=INPUT_BG, highlightthickness=1, highlightbackground=BORDER_COLOR, *args, **kwargs)
        self.variable = variable
        self.values = values
        self.command = command

        self.btn = tk.Button(
            self, textvariable=self.variable, bg=INPUT_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR,
            font=("Segoe UI", 9), relief="flat", bd=0, width=width,
            anchor="w", padx=8, pady=4, cursor="hand2", command=self._show_menu
        )
        self.btn.pack(side="left", fill="both", expand=True)

        icon_lbl = tk.Label(self, text="▼", font=("Segoe UI", 7), bg=INPUT_BG, fg=MUTED_COLOR)
        icon_lbl.pack(side="right", padx=(0, 8))
        icon_lbl.bind("<Button-1>", lambda e: self._show_menu())

        self.menu = tk.Menu(self, tearoff=0, bg=CARD_BG, fg=TEXT_COLOR, activebackground=ACCENT_COLOR, activeforeground="#ffffff", font=("Segoe UI", 9), bd=0)
        self._update_menu()

    def _update_menu(self):
        self.menu.delete(0, "end")
        for val in self.values:
            self.menu.add_command(label=val, command=lambda v=val: self._on_select(v))

    def _on_select(self, val):
        self.variable.set(val)
        if self.command:
            self.command()

    def _show_menu(self):
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.menu.tk_popup(x, y)

    def configure_values(self, values):
        self.values = values
        self._update_menu()


class ScrollableFrame(tk.Frame):
    """Um contêiner rolável usando Canvas do Tkinter e Scrollbar minimalista do ttk."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg=BG_COLOR, *args, **kwargs)

        self.canvas = tk.Canvas(self, bg=BG_COLOR, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")

        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_COLOR, padx=25, pady=20)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        try:
            widget_class = event.widget.winfo_class()
            if widget_class in ("Text", "Treeview"):
                return
        except Exception:
            pass

        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass


class AppleSwitch(tk.Label):
    """Interruptor Liga/Desliga dinâmico estilo Apple."""
    def __init__(self, parent, variable: tk.BooleanVar, on_img: ImageTk.PhotoImage, off_img: ImageTk.PhotoImage, command=None, *args, **kwargs):
        bg_color = kwargs.get("bg", CARD_BG)
        super().__init__(parent, image=off_img, bg=bg_color, cursor="hand2")
        self.variable = variable
        self.on_img = on_img
        self.off_img = off_img
        self.command = command

        self.bind("<Button-1>", lambda e: self.toggle())
        self.update_visual()

    def toggle(self):
        new_val = not self.variable.get()
        self.variable.set(new_val)
        self.update_visual()
        if self.command:
            self.command()

    def update_visual(self):
        if self.variable.get():
            self.configure(image=self.on_img)
        else:
            self.configure(image=self.off_img)


class SettingsWindow(tk.Toplevel):
    """Janela de configurações moderna estilo Apple com navegação lateral unificada."""

    def __init__(self, parent: tk.Tk, current_config: AppConfig, on_save: Callable[[AppConfig], None]) -> None:
        super().__init__(parent)
        self.current_config = current_config
        self.on_save_callback = on_save

        self._test_stream = None
        self._test_stream_active = False
        self._smooth_level = 0.0
        self._test_amplitude = 0.0
        self._listed_files: list[str] = []

        # Atributos de widgets
        self.hotkey_normal_entry = None
        self.hotkey_translate_entry = None
        self.hotkey_auto_send_entry = None
        self.hotkey_quantum_brain_entry = None
        self.prompt_text = None
        self.dict_tree = None
        self.custom_fillers_entry = None

        # Inicialização das variáveis do Design System
        self._atom_color_val = getattr(self.current_config, "atom_color", "#FF6000")
        self.code_only_var = tk.BooleanVar(value=True)

        # Variáveis Tkinter
        self.paste_var = tk.BooleanVar(value=self.current_config.auto_paste)
        self.sounds_var = tk.BooleanVar(value=self.current_config.play_sounds)
        self.sound_volume_var = tk.DoubleVar(value=self.current_config.sound_volume)

        self._theme_id_map = {
            "Bolinhas (padrão)": "dots",
            "Átomo clássico": "atom",
            "Átomo compacto": "atom_compact",
            "Átomo minimalista": "atom_minimal",
            "Apenas Átomo no Centro": "atom_centered",
        }
        self._theme_name_map = {v: k for k, v in self._theme_id_map.items()}
        current_theme_name = self._theme_name_map.get(getattr(self.current_config, "hud_theme", "dots"), "Bolinhas (padrão)")
        self.hud_theme_var = tk.StringVar(value=current_theme_name)

        self.tone_var = tk.StringVar(value=getattr(self.current_config, "tone_style", "natural"))
        self.literal_mode_var = tk.BooleanVar(value=getattr(self.current_config, "literal_mode", True))
        self.punctuation_assist_var = tk.BooleanVar(value=getattr(self.current_config, "punctuation_assist", True))
        self.learning_var = tk.BooleanVar(value=getattr(self.current_config, "continuous_learning", False))
        self.rewriter_var = tk.BooleanVar(value=getattr(self.current_config, "use_llm_rewriter", False))
        self.ai_mode_var = tk.BooleanVar(value=getattr(self.current_config, "ai_mode", True))

        self.friendly_to_id = {model["name"]: model_id for model_id, model in MODELS_MAP.items()}
        self.id_to_friendly = {model_id: model["name"] for model_id, model in MODELS_MAP.items()}
        current_friendly = self.id_to_friendly.get(self.current_config.model, "Alto Desempenho / Pro (Medium)")
        self.model_name_var = tk.StringVar(value=current_friendly)

        self._lang_friendly_map = {
            "Detecção Automática": "auto",
            "Português (Brasil)": "pt",
            "Português (Portugal)": "pt",
            "Inglês": "en",
            "Espanhol": "es",
            "Francês": "fr",
            "Alemão": "de",
            "Italiano": "it"
        }
        self._lang_code_map = {
            "auto": "Detecção Automática",
            "pt": "Português (Brasil)",
            "en": "Inglês",
            "es": "Espanhol",
            "fr": "Francês",
            "de": "Alemão",
            "it": "Italiano"
        }
        current_lang_code = self.current_config.language or "auto"
        current_friendly_lang = self._lang_code_map.get(current_lang_code, "Detecção Automática")
        self.lang_friendly_var = tk.StringVar(value=current_friendly_lang)

        self.device_var = tk.StringVar(value=self.current_config.device)
        self.compute_var = tk.StringVar(value=self.current_config.compute_type)

        current_mic = self.current_config.audio_device or "Padrão do Sistema"
        self.mic_var = tk.StringVar(value=current_mic)

        self.streaming_var = tk.BooleanVar(value=getattr(self.current_config, "streaming_mode", False))
        self.min_silence_var = tk.IntVar(value=getattr(self.current_config, "stream_min_silence_ms", 350))
        self.audio_enhance_var = tk.BooleanVar(value=getattr(self.current_config, "audio_enhance", True))
        self._profile_id_map = {
            "Rápido (apenas volume)": "fast",
            "Equilibrado (recomendado)": "balanced",
            "Máxima Qualidade (redução de ruído)": "quality"
        }
        self._profile_name_map = {v: k for k, v in self._profile_id_map.items()}
        current_profile_name = self._profile_name_map.get(
            getattr(self.current_config, "audio_enhance_profile", "balanced"),
            "Equilibrado (recomendado)"
        )
        self.audio_enhance_profile_var = tk.StringVar(value=current_profile_name)
        self.remove_stutters_var = tk.BooleanVar(value=getattr(self.current_config, "remove_stutters", False))
        self.remove_fillers_var = tk.BooleanVar(value=getattr(self.current_config, "remove_fillers", False))

        self.quantum_brain_enabled_var = tk.BooleanVar(value=getattr(self.current_config, "quantum_brain_enabled", True))
        self.quantum_brain_also_paste_var = tk.BooleanVar(value=getattr(self.current_config, "quantum_brain_also_paste", True))
        self.quantum_brain_sync_interval_var = tk.IntVar(value=getattr(self.current_config, "quantum_brain_sync_interval_min", 30))
        self.quantum_brain_sync_threshold_var = tk.IntVar(value=getattr(self.current_config, "quantum_brain_sync_threshold", 5))

        try:
            self._icon_img = load_or_generate_icon()
            self._icon_photo = ImageTk.PhotoImage(self._icon_img)
            self.iconphoto(False, self._icon_photo)
        except Exception:
            pass

        self._generate_switch_images()

        self.title("Quantum Scribe — Configurações")
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        width = 780
        height = 540
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.withdraw()

        self._setup_styles()

        self.main_container = tk.Frame(self, bg=BG_COLOR)
        self.main_container.pack(fill="both", expand=True)

        self.sidebar_frame = tk.Frame(self.main_container, bg=SIDEBAR_BG, width=200)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Content frame sem padding para que a scrollbar encoste no canto direito
        self.content_frame = tk.Frame(self.main_container, bg=BG_COLOR)
        self.content_frame.pack(side="right", fill="both", expand=True)

        self._panels: dict[str, tk.Frame] = {}
        self._sidebar_btns: dict[str, dict[str, tk.Widget]] = {}

        self._build_sidebar()
        self._build_footer()

        self.scrollable_container = ScrollableFrame(self.content_frame)
        self.scrollable_container.pack(side="top", fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._show_section("dictation_ai")

        self.update_idletasks()
        self.deiconify()
        self.focus_set()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        # Estilização da Scrollbar Minimalista Premium (clam)
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=INPUT_BG,
            troughcolor=BG_COLOR,
            bordercolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
            darkcolor=BORDER_COLOR,
            arrowsize=0  # Esconde setas clássicas
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)],
        )

        style.configure(
            "TCombobox",
            fieldbackground=INPUT_BG,
            background=BORDER_COLOR,
            foreground=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            arrowcolor=TEXT_COLOR,
            lightcolor=BORDER_COLOR,
            darkcolor=BORDER_COLOR,
            padding=(8, 5),
            font=("Segoe UI Variable", 9) if "Segoe UI Variable" in font.families() else ("Segoe UI", 9),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", INPUT_BG)],
            foreground=[("readonly", TEXT_COLOR)],
            focusfill=[("readonly", INPUT_BG)],
            selectbackground=[("readonly", INPUT_BG)],
            selectforeground=[("readonly", TEXT_COLOR)],
        )

        self.option_add("*TCombobox*Listbox.background", INPUT_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT_COLOR)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT_COLOR)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))
        self.option_add("*TCombobox*Listbox.borderWidth", 1)
        self.option_add("*TCombobox*Listbox.relief", "flat")

        style.configure(
            "Treeview",
            background=INPUT_BG,
            foreground=TEXT_COLOR,
            fieldbackground=INPUT_BG,
            bordercolor=BORDER_COLOR,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading",
            background=CARD_BG,
            foreground=MUTED_COLOR,
            relief="flat",
            font=("Segoe UI Semibold", 9)
        )
        style.map("Treeview", background=[("selected", ACCENT_COLOR)])
        style.map("Treeview.Heading", background=[("active", CARD_BG)])

    def _generate_switch_images(self) -> None:
        """Gera as imagens para os switches estilo Apple em memória."""
        w, h = 40, 22

        img_on = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_on = ImageDraw.Draw(img_on)
        draw_on.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(48, 209, 88, 255))
        draw_on.ellipse((w - h + 2, 2, w - 2, h - 2), fill=(255, 255, 255, 255))

        img_off = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_off = ImageDraw.Draw(img_off)
        draw_off.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(62, 62, 66, 255))
        draw_off.ellipse((2, 2, h - 2, h - 2), fill=(255, 255, 255, 255))

        self._switch_on_photo = ImageTk.PhotoImage(img_on)
        self._switch_off_photo = ImageTk.PhotoImage(img_off)

    def _create_toggle(self, parent: tk.Widget, variable: tk.BooleanVar, command=None) -> AppleSwitch:
        """Cria uma chave liga/desliga estilo Apple alinhada à direita via Grid."""
        switch = AppleSwitch(parent, variable, self._switch_on_photo, self._switch_off_photo, command=command, bg=CARD_BG)
        switch.grid(row=0, column=1, sticky="e", padx=10)
        return switch

    def _create_card(self, parent: tk.Widget, title: str | None = None) -> tk.Frame:
        """Cria um frame estilo Card com fundo contrastante e borda sutil."""
        card_frame = tk.Frame(
            parent, bg=CARD_BG, highlightthickness=1,
            highlightbackground=BORDER_COLOR, bd=0
        )
        card_frame.pack(fill="x", pady=(0, 15), padx=5)

        if title:
            title_lbl = tk.Label(
                card_frame, text=title.upper(),
                font=("Segoe UI Bold", 8), fg=ACCENT_COLOR, bg=CARD_BG,
                anchor="w", padx=15, pady=5
            )
            title_lbl.pack(fill="x", pady=(10, 2))

        return card_frame

    def _create_card_row(self, card: tk.Frame, label_text: str, desc_text: str | None = None) -> tk.Frame:
        """Cria uma linha de opção alinhada dentro de um Card usando Grid para simetria visual."""
        existing_children = card.winfo_children()
        if len(existing_children) > 0:
            last_child = existing_children[-1]
            if not (isinstance(last_child, tk.Label) and last_child.cget("text") and last_child.cget("text").isupper()):
                sep = tk.Frame(card, bg=BORDER_COLOR, height=1)
                sep.pack(fill="x", padx=15)

        row = tk.Frame(card, bg=CARD_BG, padx=15, pady=10)
        row.pack(fill="x")

        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=0)

        text_container = tk.Frame(row, bg=CARD_BG)
        text_container.grid(row=0, column=0, sticky="w")

        lbl = tk.Label(
            text_container, text=label_text,
            font=("Segoe UI Semibold", 9), fg=TEXT_COLOR, bg=CARD_BG,
            anchor="w"
        )
        lbl.pack(fill="x", anchor="w")

        if desc_text:
            desc_lbl = tk.Label(
                text_container, text=desc_text,
                font=("Segoe UI", 8), fg=MUTED_COLOR, bg=CARD_BG,
                anchor="w", justify="left"
            )
            desc_lbl.pack(fill="x", anchor="w", pady=(2, 0))

        return row

    def _build_sidebar_button(self, parent: tk.Widget, sid: str, icon: str, text: str) -> tk.Frame:
        """Constrói um botão de navegação premium para a barra lateral com alinhamento pixel-perfect."""
        btn_frame = tk.Frame(parent, bg=SIDEBAR_BG, cursor="hand2")
        btn_frame.pack(fill="x", pady=2, padx=10)

        # Label para o ícone (com largura fixa no Tkinter para alinhar os textos perfeitamente)
        icon_lbl = tk.Label(
            btn_frame, text=icon, font=("Segoe UI Symbol", 11),
            fg=MUTED_COLOR, bg=SIDEBAR_BG, width=3, anchor="center"
        )
        icon_lbl.pack(side="left", padx=(10, 5), pady=8)

        # Label para o texto (alinhado estritamente à esquerda 'w')
        text_lbl = tk.Label(
            btn_frame, text=text, font=("Segoe UI", 10),
            fg=TEXT_COLOR, bg=SIDEBAR_BG, anchor="w", justify="left"
        )
        text_lbl.pack(side="left", fill="both", expand=True, pady=8)

        # Armazena referências para reconfigurar os estados visuais
        self._sidebar_btns[sid] = {
            "frame": btn_frame,
            "icon": icon_lbl,
            "text": text_lbl
        }

        # Faz bind dos cliques e do hover em todos os subwidgets para que o botão inteiro seja interativo
        for w in (btn_frame, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda e, s=sid: self._show_section(s))
            w.bind("<Enter>", lambda e, s=sid: self._on_sidebar_hover(s, True))
            w.bind("<Leave>", lambda e, s=sid: self._on_sidebar_hover(s, False))

        return btn_frame

    def _build_sidebar(self) -> None:
        tk.Label(
            self.sidebar_frame,
            text="Quantum Scribe",
            font=("Segoe UI Semibold", 14),
            fg=ACCENT_COLOR,
            bg=SIDEBAR_BG,
            pady=20,
            padx=20,
            anchor="w"
        ).pack(fill="x")

        sections = [
            ("dictation_ai", "🎙", "Ditado & IA"),
            ("preferences", "⚙", "Preferências"),
            ("system_notes", "🧠", "Sistema & Notas"),
            ("about", "ℹ", "Sobre")
        ]

        for sid, icon, text in sections:
            self._build_sidebar_button(self.sidebar_frame, sid, icon, text)

        self._current_section = ""

    def _on_sidebar_hover(self, section_id: str, is_enter: bool) -> None:
        if self._current_section == section_id:
            return
        btn = self._sidebar_btns[section_id]
        bg_color = SIDEBAR_ACTIVE if is_enter else SIDEBAR_BG
        btn["frame"].configure(bg=bg_color)
        btn["icon"].configure(bg=bg_color)
        btn["text"].configure(bg=bg_color)

    def _show_section(self, section_id: str) -> None:
        if self._current_section == section_id:
            return

        if self._current_section:
            old_btn = self._sidebar_btns[self._current_section]
            old_btn["frame"].configure(bg=SIDEBAR_BG)
            old_btn["icon"].configure(bg=SIDEBAR_BG, fg=MUTED_COLOR)
            old_btn["text"].configure(bg=SIDEBAR_BG, fg=TEXT_COLOR, font=("Segoe UI", 10), anchor="w")
            if self._current_section in self._panels:
                self._panels[self._current_section].pack_forget()

        self._current_section = section_id
        new_btn = self._sidebar_btns[section_id]
        new_btn["frame"].configure(bg=SIDEBAR_ACTIVE)
        new_btn["icon"].configure(bg=SIDEBAR_ACTIVE, fg=ACCENT_COLOR)
        new_btn["text"].configure(bg=SIDEBAR_ACTIVE, fg=TEXT_COLOR, font=("Segoe UI Semibold", 10), anchor="w")

        if section_id not in self._panels:
            parent_frame = self.scrollable_container.scrollable_frame
            if section_id == "dictation_ai":
                self._panels["dictation_ai"] = self._build_dictation_ai_panel(parent_frame)
            elif section_id == "preferences":
                self._panels["preferences"] = self._build_preferences_panel(parent_frame)
            elif section_id == "system_notes":
                self._panels["system_notes"] = self._build_system_notes_panel(parent_frame)
            elif section_id == "about":
                self._panels["about"] = self._build_about_panel(parent_frame)

        self._panels[section_id].pack(fill="both", expand=True)

        try:
            self.scrollable_container.canvas.yview_moveto(0)
        except Exception:
            pass

        if section_id == "system_notes":
            self._refresh_transcriptions_list()
            self._refresh_backups_list()
            self._update_quantum_brain_stats()

    def _build_header(self, parent: tk.Frame, title: str, desc: str) -> None:
        header = tk.Frame(parent, bg=BG_COLOR)
        header.pack(fill="x", pady=(0, 20))
        tk.Label(header, text=title, font=("Segoe UI Semibold", 16), fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor="w")
        tk.Label(header, text=desc, font=("Segoe UI", 9), fg=MUTED_COLOR, bg=BG_COLOR).pack(anchor="w")

    def _create_styled_entry(self, parent: tk.Widget, initial_value: str) -> tk.Entry:
        entry = tk.Entry(
            parent, bg=INPUT_BG, fg=TEXT_COLOR, font=("Segoe UI", 9),
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR,
            insertbackground=TEXT_COLOR, width=22
        )
        entry.insert(0, initial_value)
        return entry

    # ------------------ PAINEL 1: DITADO & IA ------------------
    def _build_dictation_ai_panel(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=BG_COLOR)
        self._build_header(frame, "Ditado & Inteligência Artificial", "Configure o motor de reconhecimento de voz e estilo de pós-processamento.")

        # --- Card 1: Motor Whisper ---
        card_whisper = self._create_card(frame, "Reconhecimento de Voz (Whisper)")

        row_model = self._create_card_row(card_whisper, "Modelo da IA", "Tamanho do modelo Whisper (tiny, base, small, medium, large).")
        self.model_combo = ModernDropdown(row_model, variable=self.model_name_var, values=list(self.friendly_to_id.keys()), width=22, command=self._on_model_changed)
        self.model_combo.grid(row=0, column=1, sticky="e", padx=10)

        # Status / Progresso download Whisper
        self.download_status_frame = tk.Frame(card_whisper, bg=CARD_BG)
        self.download_status_frame.pack(fill="x", padx=15, pady=(5, 10))

        self.download_status_label = tk.Label(self.download_status_frame, text="", font=("Segoe UI Semibold", 8), bg=CARD_BG, fg=MUTED_COLOR, anchor="w")
        self.download_status_label.pack(anchor="w", pady=(0, 2))

        self.download_progress_var = tk.DoubleVar(value=0.0)
        self.download_progress_bar = ttk.Progressbar(
            self.download_status_frame, orient="horizontal",
            variable=self.download_progress_var, length=250, mode="determinate"
        )
        self.download_progress_bar.pack_forget()

        self.download_btn = tk.Button(
            self.download_status_frame, text="Baixar Modelo Whisper", bg=ACCENT_COLOR, fg="#ffffff",
            activebackground=ACCENT_HOVER, activeforeground="#ffffff", font=("Segoe UI Bold", 8),
            relief="flat", bd=0, padx=10, pady=2, cursor="hand2", command=self._download_selected_model
        )
        self.download_btn.pack(side="left", pady=(5, 0))

        row_lang = self._create_card_row(card_whisper, "Idioma", "Idioma padrão de transcrição (ou detecção automática).")
        self.lang_combo = ModernDropdown(row_lang, variable=self.lang_friendly_var, values=list(self._lang_friendly_map.keys()), width=22)
        self.lang_combo.grid(row=0, column=1, sticky="e", padx=10)

        row_device = self._create_card_row(card_whisper, "Hardware", "Processador utilizado para rodar a transcrição (CPU ou GPU CUDA).")
        self.device_combo = ModernDropdown(row_device, variable=self.device_var, values=["cpu", "cuda", "auto"], width=15)
        self.device_combo.grid(row=0, column=1, sticky="e", padx=10)

        row_compute = self._create_card_row(card_whisper, "Precisão (Quantização)", "Tipo de precisão matemática das operações.")
        self.compute_combo = ModernDropdown(row_compute, variable=self.compute_var, values=["int8", "float16", "auto"], width=15)
        self.compute_combo.grid(row=0, column=1, sticky="e", padx=10)

        # Prompt Auxiliar Fixo
        sep = tk.Frame(card_whisper, bg=BORDER_COLOR, height=1)
        sep.pack(fill="x", padx=15)

        prompt_title_frame = tk.Frame(card_whisper, bg=CARD_BG, padx=15, pady=5)
        prompt_title_frame.pack(fill="x", pady=(5, 2))
        tk.Label(prompt_title_frame, text="Prompt Auxiliar Fixo", font=("Segoe UI Semibold", 9), fg=TEXT_COLOR, bg=CARD_BG).pack(anchor="w")
        tk.Label(prompt_title_frame, text="Ensina vocabulário específico, termos técnicos ou regras de formatação adicionais.", font=("Segoe UI", 8), fg=MUTED_COLOR, bg=CARD_BG).pack(anchor="w")

        self.prompt_text = tk.Text(card_whisper, height=3, bg=INPUT_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), relief="flat", highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR, insertbackground=TEXT_COLOR)
        self.prompt_text.pack(fill="x", padx=15, pady=(5, 15))
        self.prompt_text.insert("1.0", getattr(self.current_config, "initial_prompt", "") or "")

        # --- Card 2: Pós-Processamento & Estilos ---
        card_ai = self._create_card(frame, "Pós-Processamento & Estilos")

        row_tone = self._create_card_row(card_ai, "Estilo da Transcrição", "Tom de voz e formatação do ditado final pós-reescrita.")

        default_tones = ["natural", "formal", "developer"]
        custom_tones_keys = list(getattr(self.current_config, "custom_tones", {}).keys())
        all_tones = default_tones + custom_tones_keys
        if self.tone_var.get() not in all_tones:
            all_tones.append(self.tone_var.get())

        tone_control_frame = tk.Frame(row_tone, bg=CARD_BG)
        tone_control_frame.grid(row=0, column=1, sticky="e", padx=10)

        self.tone_combo = ModernDropdown(tone_control_frame, variable=self.tone_var, values=all_tones, width=15)
        self.tone_combo.pack(side="left", padx=(0, 5))

        edit_btn = tk.Button(tone_control_frame, text="✏️ Editar Estilos", bg=INPUT_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
            relief="flat", bd=0, padx=10, pady=2, cursor="hand2", command=self._open_styles_editor)
        edit_btn.pack(side="left")

        self.tone_desc_label = tk.Label(card_ai, text="", font=("Segoe UI Italic", 8), fg=MUTED_COLOR, bg=CARD_BG, justify="left", anchor="w", padx=15, pady=5)
        self.tone_desc_label.pack(fill="x", pady=(0, 5))

        def update_tone_desc(*args):
            tone = self.tone_var.get()
            desc_map = {
                "natural": "Tom Natural: Corrige erros ortográficos/gramaticais mantendo a coloquialidade original.",
                "formal": "Tom Formal: Reescreve formalmente o ditado, ideal para e-mails e documentos profissionais.",
                "developer": "Tom Desenvolvedor: Mantém jargões de código e termos técnicos em inglês intactos."
            }
            desc = desc_map.get(tone, f"Tom Customizado '{tone}': Utiliza as suas regras personalizadas de reescrita.")
            self.tone_desc_label.configure(text=desc)

        self.tone_var.trace_add("write", update_tone_desc)
        update_tone_desc()

        row_rewriter = self._create_card_row(card_ai, "Pós-Processamento Inteligente", "Aplica o estilo de tom reescrevendo o texto via LLM offline local.")
        self._create_toggle(row_rewriter, self.rewriter_var, command=self._on_rewriter_toggled)

        self.llm_status_frame = tk.Frame(card_ai, bg=CARD_BG)
        self.llm_status_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.llm_status_label = tk.Label(self.llm_status_frame, text="", font=("Segoe UI Semibold", 8), bg=CARD_BG, anchor="w")
        self.llm_status_label.pack(side="left")

        self.download_llm_btn = tk.Button(
            self.llm_status_frame, text="Baixar Mini-LLM (~400MB)", bg=ACCENT_COLOR, fg="#ffffff",
            activebackground=ACCENT_HOVER, activeforeground="#ffffff", font=("Segoe UI Bold", 8),
            relief="flat", bd=0, padx=10, pady=2, cursor="hand2", command=self._download_llm_model
        )

        # row_aimode = self._create_card_row(card_ai, "Modo Agente IA", "Executa o ditado interpretando-o como comandos ou ações para a IA.")
        # self._create_toggle(row_aimode, self.ai_mode_var)

        row_learn = self._create_card_row(card_ai, "Aprendizado Contínuo", "Aprende e prioriza o vocabulário das suas notas diárias salvas.")
        self._create_toggle(row_learn, self.learning_var)

        # --- Card 3: Microfone & Áudio ---
        card_audio = self._create_card(frame, "Microfone & Captação")

        row_mic = self._create_card_row(card_audio, "Microfone Padrão", "Dispositivo de áudio utilizado para capturar sua voz.")
        current_mic = self.current_config.audio_device or "Padrão do Sistema"
        devices = ["Padrão do Sistema"]
        if current_mic != "Padrão do Sistema":
            devices.append(current_mic)
        self.mic_combo = ModernDropdown(row_mic, variable=self.mic_var, values=devices, width=22)
        self.mic_combo.grid(row=0, column=1, sticky="e", padx=10)

        # Busca microfones em segundo plano
        def load_devices():
            try:
                import sounddevice as sd
                found_devices = ["Padrão do Sistema"]
                for d in sd.query_devices():
                    if d.get('max_input_channels', 0) > 0:
                        name = d['name']
                        if name not in found_devices:
                            found_devices.append(name)
                if current_mic not in found_devices:
                    found_devices.append(current_mic)
                self.after(0, lambda: self.mic_combo.configure_values(found_devices))
            except Exception:
                pass
        threading.Thread(target=load_devices, daemon=True).start()

        # Teste do microfone
        row_test = self._create_card_row(card_audio, "Teste do Microfone", "Verifique o volume do sinal de entrada captado em tempo real.")

        test_control_frame = tk.Frame(row_test, bg=CARD_BG)
        test_control_frame.grid(row=0, column=1, sticky="e", padx=10)

        self.meter_canvas = tk.Canvas(test_control_frame, width=160, height=18, bg=INPUT_BG, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.meter_canvas.pack(side="left", padx=(0, 10))
        self.meter_bar = self.meter_canvas.create_rectangle(1, 1, 1, 17, fill=ACCENT_COLOR, outline="")

        self.test_btn = tk.Button(
            test_control_frame, text="Iniciar Teste", bg=CANCEL_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI Semibold", 9),
            relief="flat", bd=0, padx=12, pady=4, cursor="hand2", command=self._toggle_test_stream
        )
        self.test_btn.pack(side="left")

        row_enhance = self._create_card_row(card_audio, "Aprimorar Áudio", "Aplica redução de ruídos espectral e normalização de voz.")
        self._create_toggle(row_enhance, self.audio_enhance_var)

        row_profile = self._create_card_row(card_audio, "Perfil de Aprimoramento", "Nível de pré-processamento (Rápido, Equilibrado, Máxima Qualidade).")
        self.profile_combo = ModernDropdown(
            row_profile,
            variable=self.audio_enhance_profile_var,
            values=list(self._profile_id_map.keys()),
            width=25
        )
        self.profile_combo.grid(row=0, column=1, sticky="e", padx=10)

        # Verificar disponibilidade sem importar Torch/SciPy. Esses imports custam
        # vários segundos e faziam o clique no menu da bandeja parecer travado.
        nr_ok = (
            importlib.util.find_spec("noisereduce") is not None
            and importlib.util.find_spec("scipy") is not None
        )
        status_text = "   ✓ Filtros inteligentes de ruído ativados" if nr_ok else "   ⚠ noisereduce não instalado. Execute: pip install noisereduce scipy"
        status_color = SUCCESS_COLOR if nr_ok else "#f0a500"
        lbl_status = tk.Label(card_audio, text=status_text, font=("Segoe UI Italic", 8), fg=status_color, bg=CARD_BG, anchor="w", padx=15, pady=5)
        lbl_status.pack(fill="x", pady=(0, 10))

        row_vad = self._create_card_row(card_audio, "Detecção de Fala (VAD)", "Identifica pausas naturais na voz para segmentar chunks de fala.")
        silero_ok = (
            importlib.util.find_spec("torch") is not None
            and importlib.util.find_spec("silero_vad") is not None
        )
        vad_text = "✓ Silero VAD (alta qualidade)" if silero_ok else "⚠ Energy VAD (fallback básico)"
        vad_color = SUCCESS_COLOR if silero_ok else "#f0a500"
        tk.Label(row_vad, text=vad_text, font=("Segoe UI Bold", 8), fg=vad_color, bg=CARD_BG).grid(row=0, column=1, sticky="e", padx=10)

        row_silence = self._create_card_row(card_audio, "Silêncio para Corte", "Tempo necessário de silêncio para a IA separar blocos de ditado.")
        self._silence_combo = ModernDropdown(
            row_silence,
            variable=tk.StringVar(value=str(self.min_silence_var.get()) + "ms"),
            values=["250ms", "350ms", "500ms", "700ms"],
            width=12,
        )
        self._silence_combo.grid(row=0, column=1, sticky="e", padx=10)
        self._silence_combo.bind("<<ComboboxSelected>>",
            lambda e: self.min_silence_var.set(int(self._silence_combo.get().replace("ms", ""))))

        row_stream = self._create_card_row(card_audio, "Modo Streaming Contínuo", "Transcreve chunks menores em tempo real conforme você dita.")
        self._create_toggle(row_stream, self.streaming_var)

        row_literal = self._create_card_row(card_audio, "Transcrição Literal", "Preserva palavras, repetições e hesitações sem reescrita automática.")
        self._create_toggle(row_literal, self.literal_mode_var)

        row_punctuation = self._create_card_row(card_audio, "Pontuação Inteligente", "Usa perguntas e pausas da fala para pontuar sem trocar palavras.")
        self._create_toggle(row_punctuation, self.punctuation_assist_var)

        row_stutters = self._create_card_row(card_audio, "Remover Repetições", "Limpa gagueiras e palavras duplicadas consecutivas.")
        self._create_toggle(row_stutters, self.remove_stutters_var)

        row_fillers = self._create_card_row(card_audio, "Remover Hesitações (Fillers)", "Remove automaticamente sons como 'hmm', 'ãh', 'eh'.")
        self._create_toggle(row_fillers, self.remove_fillers_var)

        row_cf = self._create_card_row(card_audio, "Hesitações Personalizadas", "Termos separados por vírgula para remoção automática.")
        self.custom_fillers_entry = self._create_styled_entry(row_cf, "")
        self.custom_fillers_entry.grid(row=0, column=1, sticky="e", padx=10)
        custom_fillers_val = getattr(self.current_config, "custom_fillers", "")
        self.custom_fillers_entry.delete(0, "end")
        self.custom_fillers_entry.insert(0, custom_fillers_val)

        self._on_model_changed()
        self._on_rewriter_toggled()

        return frame

    # ------------------ PAINEL 2: PREFERÊNCIAS & ATALHOS ------------------
    def _build_preferences_panel(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=BG_COLOR)
        self._build_header(frame, "Preferências & Atalhos", "Ajustes de atalhos globais de teclado, sons e estilo visual da interface.")

        self._atom_color_val = getattr(self.current_config, "atom_color", "#FF6000")

        # --- Card 1: Atalhos Globais ---
        card_hotkeys = self._create_card(frame, "Atalhos Globais do Teclado")

        row_normal = self._create_card_row(card_hotkeys, "Ditado Normal", "Inicia a gravação e insere o texto diretamente no cursor do sistema.")
        self.hotkey_normal_entry = self._create_styled_entry(row_normal, self.current_config.hotkey)
        self.hotkey_normal_entry.grid(row=0, column=1, sticky="e", padx=10)

        row_trans = self._create_card_row(card_hotkeys, "Ditado + Traduzir", "Inicia gravação, traduz a fala para o inglês e cola o resultado.")
        hk_tr = getattr(self.current_config, "hotkey_translate", "Ctrl+Alt+Space")
        self.hotkey_translate_entry = self._create_styled_entry(row_trans, hk_tr)
        self.hotkey_translate_entry.grid(row=0, column=1, sticky="e", padx=10)

        row_send = self._create_card_row(card_hotkeys, "Ditado + Enviar", "Cola o texto ditado e pressiona a tecla Enter automaticamente.")
        hk_as = getattr(self.current_config, "hotkey_auto_send", "Ctrl+Shift+Space")
        self.hotkey_auto_send_entry = self._create_styled_entry(row_send, hk_as)
        self.hotkey_auto_send_entry.grid(row=0, column=1, sticky="e", padx=10)

        row_brain = self._create_card_row(card_hotkeys, "Ditado + Quantum Brain", "Grava o áudio e envia diretamente para o banco de notas do Quantum Brain.")
        hk_qb = getattr(self.current_config, "hotkey_quantum_brain", "Ctrl+Shift+D")
        self.hotkey_quantum_brain_entry = self._create_styled_entry(row_brain, hk_qb)
        self.hotkey_quantum_brain_entry.grid(row=0, column=1, sticky="e", padx=10)

        note_frame = tk.Frame(card_hotkeys, bg=CARD_BG, padx=15, pady=5)
        note_frame.pack(fill="x", pady=(0, 7))
        tk.Label(note_frame, text="💡 Atalho Fixo: Tecla ESC cancela a gravação e fecha o HUD imediatamente.", font=("Segoe UI Italic", 8), fg=MUTED_COLOR, bg=CARD_BG, anchor="w").pack(fill="x")

        # --- Card 2: Interface & HUD ---
        card_hud = self._create_card(frame, "Interface & HUD")

        row_paste = self._create_card_row(card_hud, "Colar Automatically", "Digita o texto no cursor do sistema logo após terminar o ditado.")
        self._create_toggle(row_paste, self.paste_var)

        row_theme = self._create_card_row(card_hud, "Animação do HUD", "Estilo visual que indica que a gravação está ativa.")
        theme_combo = ttk.Combobox(
            row_theme, textvariable=self.hud_theme_var,
            values=list(self._theme_id_map.keys()),
            state="readonly", width=22
        )
        theme_combo.grid(row=0, column=1, sticky="e", padx=10)

        self._atom_color_row = self._create_card_row(card_hud, "Cor do Átomo", "Selecione a cor de destaque da animação do átomo.")

        color_control_frame = tk.Frame(self._atom_color_row, bg=CARD_BG)
        color_control_frame.grid(row=0, column=1, sticky="e", padx=10)

        self._atom_color_preview = tk.Label(
            color_control_frame, text="  ",
            bg=self._atom_color_val, width=3, relief="flat", cursor="hand2"
        )
        self._atom_color_preview.pack(side="left", padx=(0, 5))

        self._atom_color_label = tk.Label(
            color_control_frame, text=self._atom_color_val.upper(),
            font=("Segoe UI", 9), fg=MUTED_COLOR, bg=CARD_BG, cursor="hand2"
        )
        self._atom_color_label.pack(side="left")

        self._atom_color_preview.bind("<Button-1>", lambda _: self._pick_atom_color())
        self._atom_color_label.bind("<Button-1>", lambda _: self._pick_atom_color())

        theme_combo.bind("<<ComboboxSelected>>", lambda _: self._toggle_atom_color_row())
        self._toggle_atom_color_row()

        # --- Card 3: Efeitos Sonoros ---
        card_sounds = self._create_card(frame, "Efeitos Sonoros")

        row_sounds = self._create_card_row(card_sounds, "Efeitos Sonoros", "Tocar bip sonoro ao iniciar e pausar o ditado.")
        self._create_toggle(row_sounds, self.sounds_var, command=self._toggle_volume_slider)

        self.volume_row = self._create_card_row(card_sounds, "Volume dos Efeitos", "Ajuste a intensidade do som de notificação.")

        self.volume_slider = tk.Scale(
            self.volume_row, from_=0.0, to=1.0, resolution=0.05, orient="horizontal",
            variable=self.sound_volume_var,
            bg=CARD_BG, fg=TEXT_COLOR, troughcolor=INPUT_BG, activebackground=ACCENT_COLOR,
            highlightthickness=0, bd=0, showvalue=True, length=180, font=("Segoe UI", 8)
        )
        self.volume_slider.grid(row=0, column=1, sticky="e", padx=10)

        self.volume_label = tk.Label(self.volume_row, text="", font=("Segoe UI", 1), bg=CARD_BG) # Ref oculta
        self._toggle_volume_slider()

        return frame

    # ------------------ PAINEL 3: SISTEMA & NOTAS ------------------
    def _build_system_notes_panel(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=BG_COLOR)
        self._build_header(frame, "Sistema, Notas & Backups", "Ajustes do Quantum Brain, backups de segurança e histórico de transcrições.")

        self.code_only_var = tk.BooleanVar(value=True)

        # --- Card 1: Quantum Brain ---
        card_brain = self._create_card(frame, "Segundo Cérebro (Quantum Brain)")

        row_brain_on = self._create_card_row(card_brain, "Habilitar Quantum Brain", "Captura pensamentos ditados e os compila periodicamente.")
        self._create_toggle(row_brain_on, self.quantum_brain_enabled_var)

        row_brain_paste = self._create_card_row(card_brain, "Também Colar no Cursor", "Insere a transcrição no cursor imediatamente após criar a nota.")
        self._create_toggle(row_brain_paste, self.quantum_brain_also_paste_var)

        row_interval = self._create_card_row(card_brain, "Intervalo de Síntese", "Tempo máximo (em minutos) para condensar notas ativas.")
        self.sync_interval_spin = tk.Spinbox(
            row_interval, from_=15, to=240, increment=5, textvariable=self.quantum_brain_sync_interval_var,
            bg=INPUT_BG, fg=TEXT_COLOR, buttonbackground=INPUT_BG, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR,
            insertbackground=TEXT_COLOR, font=("Segoe UI", 9), width=10
        )
        self.sync_interval_spin.grid(row=0, column=1, sticky="e", padx=10)

        row_threshold = self._create_card_row(card_brain, "Quantidade Limite de Notas", "Quantidade de notas pendentes necessárias para gerar uma síntese.")
        self.sync_threshold_spin = tk.Spinbox(
            row_threshold, from_=3, to=50, increment=1, textvariable=self.quantum_brain_sync_threshold_var,
            bg=INPUT_BG, fg=TEXT_COLOR, buttonbackground=INPUT_BG, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR,
            insertbackground=TEXT_COLOR, font=("Segoe UI", 9), width=10
        )
        self.sync_threshold_spin.grid(row=0, column=1, sticky="e", padx=10)

        stats_frame = tk.Frame(card_brain, bg=CARD_BG, padx=15, pady=8)
        stats_frame.pack(fill="x")
        self.stats_label = tk.Label(
            stats_frame, text="Carregando estatísticas...",
            font=("Segoe UI", 9), fg=TEXT_COLOR, bg=CARD_BG, justify="left", anchor="w"
        )
        self.stats_label.pack(anchor="w", fill="x")

        row_brain_actions = self._create_card_row(card_brain, "Ferramentas do Banco", "Gerencie o diretório de notas ou inicie a consolidação manual.")

        brain_actions_frame = tk.Frame(row_brain_actions, bg=CARD_BG)
        brain_actions_frame.grid(row=0, column=1, sticky="e", padx=10)

        open_folder_btn = tk.Button(
            brain_actions_frame, text="🔍 Abrir Pasta", bg=INPUT_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=self._open_quantum_brain_folder
        )
        open_folder_btn.pack(side="left", padx=(0, 5))

        synthesize_btn = tk.Button(
            brain_actions_frame, text="⚡ Sintetizar Agora", bg=ACCENT_COLOR, fg="#ffffff",
            activebackground=ACCENT_HOVER, activeforeground="#ffffff", font=("Segoe UI Semibold", 9),
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=self._trigger_manual_synthesis
        )
        synthesize_btn.pack(side="left")

        # --- Card 2: Histórico de Transcrições ---
        card_logs = self._create_card(frame, "Histórico de Transcrições")

        row_logs_dir = self._create_card_row(card_logs, "Logs de Transcrição", f"Caminho absoluto: {diary_dir()}")

        open_logs_btn = tk.Button(
            row_logs_dir, text="Abrir Pasta 📂", bg=INPUT_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI", 8),
            relief="flat", bd=0, padx=10, cursor="hand2", command=lambda: os.startfile(diary_dir())
        )
        open_logs_btn.grid(row=0, column=1, sticky="e", padx=10)

        log_view_frame = tk.Frame(card_logs, bg=INPUT_BG, highlightthickness=1, highlightbackground=BORDER_COLOR, bd=0)
        log_view_frame.pack(fill="x", padx=15, pady=(5, 10))

        self.logs_text = tk.Text(log_view_frame, height=5, bg=INPUT_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), relief="flat", bd=0, state="disabled")
        scrollbar = ttk.Scrollbar(log_view_frame, command=self.logs_text.yview)
        self.logs_text.configure(yscrollcommand=scrollbar.set)

        self.logs_text.tag_config("link", foreground=ACCENT_COLOR, underline=True)
        self.logs_text.tag_bind("link", "<Enter>", lambda _: self.logs_text.config(cursor="hand2"))
        self.logs_text.tag_bind("link", "<Leave>", lambda _: self.logs_text.config(cursor=""))
        self.logs_text.tag_bind("link", "<Button-1>", self._on_transcription_clicked)

        self.logs_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        row_del_logs = self._create_card_row(card_logs, "Apagar Logs", "Apagar todos os históricos salvos permanentemente.")

        delete_logs_btn = tk.Button(
            row_del_logs, text="🗑 Apagar Todas as Transcrições", bg=CANCEL_BG, fg=DANGER_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=DANGER_COLOR, font=("Segoe UI Semibold", 9),
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=self._delete_all_transcriptions
        )
        delete_logs_btn.grid(row=0, column=1, sticky="e", padx=10)

        # --- Card 3: Backup & Restauração ---
        card_backup = self._create_card(frame, "Backup e Restauração")

        row_backup_actions = self._create_card_row(card_backup, "Ferramentas de Backup", "Gere novos backups zip ou selecione arquivos locais.")

        backup_ctrl_frame = tk.Frame(row_backup_actions, bg=CARD_BG)
        backup_ctrl_frame.grid(row=0, column=1, sticky="e", padx=10)

        self.chk_code_only = tk.Checkbutton(
            backup_ctrl_frame, text="Apenas Código",
            variable=self.code_only_var, bg=CARD_BG, fg=TEXT_COLOR,
            activebackground=CARD_BG, activeforeground=TEXT_COLOR,
            selectcolor=INPUT_BG, font=("Segoe UI", 9)
        )
        self.chk_code_only.pack(side="left", padx=(0, 10))

        self.btn_create_backup = tk.Button(
            backup_ctrl_frame, text="Criar Backup 💾", bg=ACCENT_COLOR, fg="#ffffff",
            activebackground=ACCENT_HOVER, activeforeground="#ffffff", font=("Segoe UI Bold", 9),
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=self._on_create_backup_clicked
        )
        self.btn_create_backup.pack(side="left", padx=(0, 5))

        self.btn_restore_file = tk.Button(
            backup_ctrl_frame, text="Restaurar de Arquivo... 📂", bg=CANCEL_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI Semibold", 9),
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2", command=self._on_restore_file_clicked
        )
        self.btn_restore_file.pack(side="left")

        table_frame = tk.Frame(card_backup, bg=INPUT_BG, highlightthickness=1, highlightbackground=BORDER_COLOR)
        table_frame.pack(fill="x", padx=15, pady=(5, 10))

        columns = ("filename", "type", "version", "datetime", "size")
        self.backup_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=4)
        self.backup_tree.heading("filename", text="Arquivo")
        self.backup_tree.heading("type", text="Tipo")
        self.backup_tree.heading("version", text="Versão")
        self.backup_tree.heading("datetime", text="Data/Hora")
        self.backup_tree.heading("size", text="Tamanho")

        self.backup_tree.column("filename", width=150, minwidth=100)
        self.backup_tree.column("type", width=90, minwidth=70, anchor="center")
        self.backup_tree.column("version", width=60, minwidth=40, anchor="center")
        self.backup_tree.column("datetime", width=120, minwidth=90, anchor="center")
        self.backup_tree.column("size", width=70, minwidth=50, anchor="e")

        scrollbar_bk = ttk.Scrollbar(table_frame, orient="vertical", command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar_bk.set)

        self.backup_tree.pack(side="left", fill="both", expand=True)
        scrollbar_bk.pack(side="right", fill="y")

        row_backup_table_ctrl = self._create_card_row(card_backup, "Ações de Backup Selecionado", "Gerencie o backup atualmente selecionado na tabela acima.")

        backup_table_ctrl_frame = tk.Frame(row_backup_table_ctrl, bg=CARD_BG)
        backup_table_ctrl_frame.grid(row=0, column=1, sticky="e", padx=10)

        self.btn_restore_selected = tk.Button(
            backup_table_ctrl_frame, text="Restaurar Selecionado 🔄", bg=CANCEL_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI Semibold", 8),
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=self._on_restore_selected_clicked
        )
        self.btn_restore_selected.pack(side="left", padx=(0, 5))

        self.btn_delete_selected = tk.Button(
            backup_table_ctrl_frame, text="Excluir Selecionado 🗑", bg=CANCEL_BG, fg=DANGER_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=DANGER_COLOR, font=("Segoe UI Semibold", 8),
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=self._on_delete_selected_clicked
        )
        self.btn_delete_selected.pack(side="left")
        self._backup_items_map = {}

        return frame

    # ------------------ PAINEL 4: SOBRE ------------------
    def _build_about_panel(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg=BG_COLOR)
        self._build_header(frame, "Sobre o Quantum Scribe", "Informações da versão e recursos adicionais da aplicação.")

        # --- Card 1: Identidade do Aplicativo ---
        card_identity = self._create_card(frame)

        # Grid para logo e textos principais do Sobre
        row_id = tk.Frame(card_identity, bg=CARD_BG, padx=15, pady=15)
        row_id.pack(fill="x")
        row_id.columnconfigure(0, weight=0)
        row_id.columnconfigure(1, weight=1)

        # Pequeno canvas para desenhar logo reescalado do átomo
        logo_canvas = tk.Canvas(row_id, width=64, height=64, bg=CARD_BG, bd=0, highlightthickness=0)
        logo_canvas.grid(row=0, column=0, sticky="nw", padx=(0, 15))

        # Carrega e redimensiona ícone em cache
        self._logo_photo_small = ImageTk.PhotoImage(self._icon_img.resize((64, 64), Image.Resampling.LANCZOS))
        logo_canvas.create_image(32, 32, image=self._logo_photo_small)

        text_block = tk.Frame(row_id, bg=CARD_BG)
        text_block.grid(row=0, column=1, sticky="nw")

        from . import __version__
        tk.Label(text_block, text="Quantum Scribe", font=("Segoe UI Bold", 16), fg=TEXT_COLOR, bg=CARD_BG).pack(anchor="w")
        tk.Label(text_block, text=f"Versão Oficial {__version__}", font=("Segoe UI Semibold", 10), fg=ACCENT_COLOR, bg=CARD_BG).pack(anchor="w", pady=(2, 4))
        tk.Label(text_block, text="Transcrição de voz privada e offline com inteligência artificial.", font=("Segoe UI", 9), fg=MUTED_COLOR, bg=CARD_BG).pack(anchor="w")

        # --- Card 2: Detalhes do Sistema ---
        card_system = self._create_card(frame, "Detalhes do Sistema")

        import sys
        row_python = self._create_card_row(card_system, "Interpretador Python", "Versão do interpretador sendo utilizado pela aplicação.")
        tk.Label(row_python, text=sys.version.split(" ")[0], font=("Segoe UI Bold", 9), fg=TEXT_COLOR, bg=CARD_BG).grid(row=0, column=1, sticky="e", padx=10)

        row_tcl = self._create_card_row(card_system, "Versão do Tk/Tcl", "Versão gráfica do motor Tk/Tcl sendo utilizado pelo Tkinter.")
        tk.Label(row_tcl, text=str(self.tk.call("info", "patchlevel")), font=("Segoe UI Bold", 9), fg=TEXT_COLOR, bg=CARD_BG).grid(row=0, column=1, sticky="e", padx=10)

        row_root = self._create_card_row(card_system, "Diretório de Instalação", "Localização absoluta da pasta contendo o código fonte.")
        path_lbl = tk.Label(row_root, text=str(Path(get_project_root()).name), font=("Segoe UI Bold", 9), fg=MUTED_COLOR, bg=CARD_BG)
        path_lbl.grid(row=0, column=1, sticky="e", padx=10)
        # Ao passar o mouse exibe caminho inteiro como tooltip
        path_lbl.bind("<Enter>", lambda _: path_lbl.configure(text=str(get_project_root()), fg=TEXT_COLOR))
        path_lbl.bind("<Leave>", lambda _: path_lbl.configure(text=str(Path(get_project_root()).name), fg=MUTED_COLOR))

        # --- Card 3: Recursos e Suporte ---
        card_links = self._create_card(frame, "Recursos & Links Úteis")

        row_links = self._create_card_row(card_links, "Links de Desenvolvimento", "Acesse a pasta de desenvolvimento ou repositórios locais.")

        links_frame = tk.Frame(row_links, bg=CARD_BG)
        links_frame.grid(row=0, column=1, sticky="e", padx=10)

        open_folder_btn = tk.Button(
            links_frame, text="Abrir Pasta do Projeto 📂", bg=INPUT_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI", 9),
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=lambda: os.startfile(get_project_root())
        )
        open_folder_btn.pack(side="left", padx=(0, 5))

        tk.Label(
            card_links,
            text="Desenvolvido por Natan Melquiades.\nQuantum Scribe utiliza CTranslate2, faster-whisper e sounddevice.",
            font=("Segoe UI Italic", 8), fg=MUTED_COLOR, bg=CARD_BG, justify="center", anchor="center", pady=10
        ).pack(fill="x")

        return frame

    def _toggle_volume_slider(self) -> None:
        state = "normal" if self.sounds_var.get() else "disabled"
        color = TEXT_COLOR if self.sounds_var.get() else MUTED_COLOR
        self.volume_slider.configure(state=state, fg=color)

    def _toggle_atom_color_row(self) -> None:
        theme_val = self._theme_id_map.get(self.hud_theme_var.get(), "dots")
        is_atom = theme_val in ("atom", "atom_compact", "atom_centered")
        if is_atom:
            self._atom_color_row.pack(fill="x")
        else:
            self._atom_color_row.pack_forget()

    def _pick_atom_color(self) -> None:
        from tkinter import colorchooser
        result = colorchooser.askcolor(
            color=self._atom_color_val,
            title="Escolha a cor do átomo",
            parent=self,
        )
        if result and result[1]:
            chosen = result[1].upper()
            self._atom_color_val = chosen
            self._atom_color_preview.configure(bg=chosen)
            self._atom_color_label.configure(text=chosen)

    def _open_styles_editor(self):
        editor = tk.Toplevel(self)
        editor.title("Editor de Estilos de Inteligência")
        editor.configure(bg=BG_COLOR)
        editor.geometry("600x450")
        editor.transient(self)
        editor.grab_set()

        tk.Label(editor, text="Configuração de Perfis e Tons", font=("Segoe UI Bold", 12), fg=TEXT_COLOR, bg=BG_COLOR).pack(pady=(15, 5))

        list_frame = tk.Frame(editor, bg=BG_COLOR)
        list_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(list_frame, text="Selecione um Estilo:", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=BG_COLOR).pack(side="left")

        style_var = tk.StringVar()
        style_combo = ModernDropdown(list_frame, variable=style_var, values=self.tone_combo.values, width=20)
        style_combo.pack(side="left", padx=10)

        tk.Label(editor, text="Prompt Auxiliar do Whisper (Vocabulário / Regras)", font=("Segoe UI Semibold", 9), fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor="w", padx=20, pady=(15, 2))
        whisper_text = tk.Text(editor, height=3, bg=INPUT_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), relief="flat", highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR)
        whisper_text.pack(fill="x", padx=20)

        tk.Label(editor, text="Instrução do Mini-LLM (Comportamento de Reescrita)", font=("Segoe UI Semibold", 9), fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor="w", padx=20, pady=(15, 2))
        llm_text = tk.Text(editor, height=4, bg=INPUT_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), relief="flat", highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR)
        llm_text.pack(fill="x", padx=20)

        default_whisper_prompts = {
            "natural": "",
            "formal": "Linguagem formal, regras cultas.",
            "developer": "Desenvolvedor de software, termos em inglês, camelCase, Python, React."
        }
        default_llm_prompts = {
            "natural": "Corrija ortografia, acentuação e pontuação básicas. Mantenha 100% das palavras originais, a estrutura e a coloquialidade do ditado.",
            "formal": "Reescreva com linguagem formal, profissional e vocabulário empresarial. Corrija a gramática e remova gírias.",
            "developer": "Mantenha os jargões de programação em inglês e corrija a estrutura do texto para ficar claro e técnico."
        }

        def load_style():
            sel = style_var.get()
            whisper_text.delete("1.0", "end")
            llm_text.delete("1.0", "end")

            if sel in self.current_config.custom_tones:
                whisper_text.insert("1.0", self.current_config.custom_tones[sel])
            else:
                whisper_text.insert("1.0", default_whisper_prompts.get(sel, ""))

            if sel in self.current_config.llm_custom_tones:
                llm_text.insert("1.0", self.current_config.llm_custom_tones[sel])
            else:
                llm_text.insert("1.0", default_llm_prompts.get(sel, "Reescreva o texto com clareza."))

        style_combo.command = load_style

        if self.tone_var.get() in self.tone_combo.values:
            style_var.set(self.tone_var.get())
            load_style()

        def create_new_style():
            from tkinter import simpledialog
            new_name = simpledialog.askstring("Novo Estilo", "Nome do novo perfil de estilo:", parent=editor)
            if new_name and new_name.strip():
                new_name = new_name.strip()
                if new_name not in self.tone_combo.values:
                    new_values = self.tone_combo.values + [new_name]
                    self.tone_combo.configure_values(new_values)
                    style_combo.configure_values(new_values)
                style_var.set(new_name)
                load_style()

        def save_and_close():
            sel = style_var.get()
            if sel:
                w_prompt = whisper_text.get("1.0", "end-1c").strip()
                l_prompt = llm_text.get("1.0", "end-1c").strip()
                self.current_config.custom_tones[sel] = w_prompt
                self.current_config.llm_custom_tones[sel] = l_prompt
                self.tone_var.set(sel)
            editor.destroy()

        btn_frame = tk.Frame(editor, bg=BG_COLOR)
        btn_frame.pack(fill="x", side="bottom", pady=20, padx=20)

        tk.Button(btn_frame, text="Novo Estilo", command=create_new_style, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat", padx=10).pack(side="left")
        tk.Button(btn_frame, text="Salvar Modificações", command=save_and_close, bg=ACCENT_COLOR, fg="#ffffff", relief="flat", padx=15).pack(side="right")
        tk.Button(btn_frame, text="Cancelar", command=editor.destroy, bg=CANCEL_BG, fg=TEXT_COLOR, relief="flat", padx=15).pack(side="right", padx=10)

    def _on_model_changed(self, event: object = None) -> None:
        friendly = self.model_name_var.get()
        model_id = self.friendly_to_id.get(friendly, "medium")
        model_info = MODELS_MAP.get(model_id)

        self.model_desc_label = tk.Label(self.download_status_frame, text="", font=("Segoe UI", 8), fg=MUTED_COLOR, bg=CARD_BG)
        self.model_desc_label.configure(text=model_info["desc"])

        if is_model_downloaded(model_id):
            self.download_status_label.configure(text="✓ Modelo Whisper baixado e pronto", fg=SUCCESS_COLOR)
            self.download_btn.pack_forget()
        else:
            self.download_status_label.configure(
                text="Download pendente — será instalado automaticamente ou pode baixar agora",
                fg=DANGER_COLOR,
            )
            self.download_btn.pack(side="left", pady=(5, 0))

    def _on_rewriter_toggled(self) -> None:
        from .rewriter import is_rewriter_downloaded
        repo_id = getattr(self.current_config, "llm_model_repo", "jncraton/Qwen2.5-0.5B-Instruct-ct2-int8")

        if self.rewriter_var.get():
            if is_rewriter_downloaded(repo_id):
                self.llm_status_label.configure(text="✓ LLM offline disponível na máquina", fg=SUCCESS_COLOR)
                self.download_llm_btn.pack_forget()
            else:
                self.llm_status_label.configure(text="⚠ Requer download do pacote de IA da LLM", fg=DANGER_COLOR)
                self.download_llm_btn.pack(side="left", padx=10)
        else:
            self.llm_status_label.configure(text="")
            self.download_llm_btn.pack_forget()

    def _download_selected_model(self) -> None:
        friendly = self.model_name_var.get()
        model_id = self.friendly_to_id.get(friendly, "medium")

        self._set_widgets_state("disabled")

        self.download_btn.pack_forget()
        self.download_progress_bar.pack(anchor="w", pady=(4, 5))
        self.download_progress_var.set(0.0)
        self.download_progress_bar.configure(mode="indeterminate")
        self.download_progress_bar.start(10)
        self.download_status_label.configure(text="Buscando metadados no Hugging Face...", fg=MUTED_COLOR)

        def download_thread():
            try:
                from .model_manager import ensure_model_downloaded

                ensure_model_downloaded(model_id)
                def on_success():
                    self.download_progress_bar.stop()
                    self._set_widgets_state("normal")
                    self.download_progress_bar.pack_forget()
                    self._on_model_changed()
                    self.error_label.configure(text=f"Modelo {friendly} baixado com sucesso!", fg=SUCCESS_COLOR)
                self.after(0, on_success)
            except Exception as error:
                def on_failure(err=error):
                    self.download_progress_bar.stop()
                    self._set_widgets_state("normal")
                    self.download_progress_bar.pack_forget()
                    self._on_model_changed()
                    self.error_label.configure(text=f"Falha ao baixar modelo: {err}", fg=DANGER_COLOR)
                self.after(0, on_failure)

        threading.Thread(target=download_thread, daemon=True).start()

    def _download_llm_model(self) -> None:
        repo_id = getattr(self.current_config, "llm_model_repo", "jncraton/Qwen2.5-0.5B-Instruct-ct2-int8")
        self._set_widgets_state("disabled")

        progress_win = tk.Toplevel(self)
        progress_win.title("Baixando LLM...")
        progress_win.configure(bg=BG_COLOR)
        progress_win.resizable(False, False)
        progress_win.grab_set()

        pw, ph = 350, 120
        px = self.winfo_x() + (self.winfo_width() - pw) // 2
        py = self.winfo_y() + (self.winfo_height() - ph) // 2
        progress_win.geometry(f"{pw}x{ph}+{px}+{py}")

        tk.Label(progress_win, text="Baixando Mini-LLM (CT2)", font=("Segoe UI Semibold", 10), fg=TEXT_COLOR, bg=BG_COLOR, pady=10).pack()
        status_lbl = tk.Label(progress_win, text="Baixando repositório HF...", font=("Segoe UI", 8), fg=MUTED_COLOR, bg=BG_COLOR)
        status_lbl.pack()

        prog_bar = ttk.Progressbar(progress_win, mode="indeterminate", length=300)
        prog_bar.pack(pady=10)
        prog_bar.start(10)

        def callback(msg: str):
            self.after(0, lambda: status_lbl.configure(text=msg))

        def download_thread():
            from .rewriter import download_rewriter_model
            success = download_rewriter_model(repo_id, callback=callback)
            if success:
                def on_success():
                    progress_win.destroy()
                    self._set_widgets_state("normal")
                    self._on_rewriter_toggled()
                    self.error_label.configure(text="LLM baixado com sucesso!", fg=SUCCESS_COLOR)
                self.after(1000, on_success)
            else:
                def on_failure():
                    progress_win.destroy()
                    self._set_widgets_state("normal")
                    self._on_rewriter_toggled()
                    self.error_label.configure(text="Falha ao baixar LLM.", fg=DANGER_COLOR)
                self.after(1000, on_failure)

        threading.Thread(target=download_thread, daemon=True).start()

    def _toggle_test_stream(self) -> None:
        if self._test_stream_active:
            self._stop_test_stream()
            self.test_btn.configure(text="Iniciar Teste", bg=CANCEL_BG, fg=TEXT_COLOR)
            try:
                self.meter_canvas.coords(self.meter_bar, 1, 1, 1, 17)
            except Exception:
                pass
        else:
            self._start_test_stream()
            if self._test_stream:
                self.test_btn.configure(text="Parar Teste", bg=ACCENT_COLOR, fg="#fff")
                self._update_test_meter()

    def _start_test_stream(self) -> None:
        self._stop_test_stream()
        from .audio import get_device_index_by_name
        selected_name = self.mic_var.get()
        device_index = get_device_index_by_name(selected_name)

        import numpy as np
        import sounddevice as sd

        self._test_amplitude = 0.0
        self._test_stream_active = True

        def callback(indata, frames, time_info, status):
            if not self._test_stream_active or status.input_overflow or len(indata) == 0:
                return
            rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))
            self._test_amplitude = float(rms / 32768.0)

        try:
            self._test_stream = sd.InputStream(device=device_index, samplerate=16000, channels=1, dtype="int16", callback=callback)
            self._test_stream.start()
        except Exception as error:
            self.error_label.configure(text=f"Erro no microfone: {error}", fg=DANGER_COLOR)
            self._test_stream = None
            self._test_stream_active = False

    def _stop_test_stream(self) -> None:
        self._test_stream_active = False
        if getattr(self, "_test_stream", None):
            try:
                self._test_stream.stop()
                self._test_stream.close()
            except Exception:
                pass
            self._test_stream = None

    def _on_mic_changed(self, event: object = None) -> None:
        if self._test_stream_active:
            self._start_test_stream()

    def _update_test_meter(self) -> None:
        if not self._test_stream_active:
            return
        amp_clean = max(0.0, self._test_amplitude - 0.0015)
        target_amp = min(1.0, amp_clean * 300.0)
        self._smooth_level = self._smooth_level * 0.7 + target_amp * 0.3

        try:
            max_w = self.meter_canvas.winfo_width() - 2
            w = int(self._smooth_level * max_w)
            self.meter_canvas.coords(self.meter_bar, 1, 1, 1 + w, 17)
        except Exception:
            pass
        self.after(40, self._update_test_meter)

    def _refresh_transcriptions_list(self) -> None:
        if not hasattr(self, "logs_text") or self.logs_text is None:
            return
        self.logs_text.configure(state="normal")
        self.logs_text.delete("1.0", "end")
        self._listed_files = []

        files = glob.glob(os.path.join(diary_dir(), "*.md"))
        files.sort(reverse=True)

        if not files:
            self.logs_text.insert("end", "Nenhuma transcrição salva ainda.\n")
        else:
            for f in files:
                basename = os.path.basename(f)
                try:
                    with open(f, "r", encoding="utf-8") as f_obj:
                        lines = f_obj.readlines()
                        entries = sum(1 for line in lines if line.startswith("## "))
                except Exception:
                    entries = 0

                self._listed_files.append(f)
                self.logs_text.insert("end", f"📄 {basename:<25} {entries} entrada(s)\n", "link")

        self.logs_text.configure(state="disabled")

    def _on_transcription_clicked(self, event: object) -> None:
        index_str = self.logs_text.index(f"@{event.x},{event.y}")
        line_num = int(index_str.split(".")[0]) - 1
        if 0 <= line_num < len(self._listed_files):
            file_path = self._listed_files[line_num]
            if os.path.exists(file_path):
                try:
                    os.startfile(file_path)
                except Exception as error:
                    messagebox.showerror("Erro ao abrir", f"Não foi possível abrir o arquivo: {error}", parent=self)

    def _delete_all_transcriptions(self) -> None:
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja apagar permanentemente todas as transcrições salvas?", parent=self):
            files = glob.glob(os.path.join(diary_dir(), "*.md"))
            for f in files:
                try:
                    os.remove(f)
                except Exception:
                    pass
            self._refresh_transcriptions_list()
            self.error_label.configure(text="Transcrições apagadas com sucesso.", fg=SUCCESS_COLOR)

    def _open_quantum_brain_folder(self) -> None:
        try:
            from .quantum_brain import quantum_brain_dir
            path = quantum_brain_dir(self.current_config)
            os.startfile(str(path))
        except Exception as e:
            messagebox.showerror("Erro ao abrir pasta", f"Não foi possível abrir a pasta: {e}", parent=self)

    def _trigger_manual_synthesis(self) -> None:
        try:
            from .quantum_brain import QuantumBrainOrchestrator
            orchestrator = QuantumBrainOrchestrator.get_instance(self.current_config)

            def run_sync():
                self.stats_label.configure(text="Sintetizando notas (processamento em background)...")
                try:
                    orchestrator._trigger_synthesis()
                    self.after(2000, self._update_quantum_brain_stats)
                except Exception as error:
                    message = str(error)
                    self.after(
                        0,
                        lambda detail=message: messagebox.showerror(
                            "Erro na síntese",
                            f"Falha ao iniciar síntese: {detail}",
                            parent=self,
                        ),
                    )

            threading.Thread(target=run_sync, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def _update_quantum_brain_stats(self) -> None:
        if not hasattr(self, "stats_label") or self.stats_label is None:
            return
        try:
            from .quantum_brain import QuantumBrainOrchestrator
            orchestrator = QuantumBrainOrchestrator.get_instance(self.current_config)
            stats = orchestrator.get_stats()

            last_synthesis_str = "Nunca"
            if stats["last_synthesis"]:
                import datetime
                dt = datetime.datetime.fromtimestamp(stats["last_synthesis"])
                last_synthesis_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            text = (
                f"• Notas brutas pendentes de síntese: {stats['unsynthesized']}\n"
                f"• Projetos ativos mapeados: {stats['projects']}\n"
                f"• Última síntese realizada: {last_synthesis_str}"
            )
            self.stats_label.configure(text=text)
        except Exception as e:
            self.stats_label.configure(text=f"Erro ao ler estatísticas: {e}")

    def _refresh_backups_list(self) -> None:
        if not hasattr(self, "backup_tree") or self.backup_tree is None:
            return
        self.backup_tree.delete(*self.backup_tree.get_children())
        self._backup_items_map.clear()

        try:
            backups = list_backups()
            if not backups:
                self.backup_tree.insert("", "end", values=("Nenhum backup encontrado.", "-", "-", "-", "-"))
            else:
                for b in backups:
                    item_id = self.backup_tree.insert("", "end", values=(
                        b["filename"],
                        "Apenas Código" if b["code_only"] else "Completo",
                        b["version"],
                        b["datetime"],
                        f"{b['size_kb']:.1f} KB"
                    ))
                    self._backup_items_map[item_id] = b
        except Exception as e:
            messagebox.showerror("Erro ao Listar", f"Não foi possível listar os backups: {e}", parent=self)

    def _on_create_backup_clicked(self) -> None:
        self.btn_create_backup.configure(state="disabled", text="Criando...")
        self.update()

        try:
            code_only = self.code_only_var.get()
            zip_path, elapsed, size = create_backup(code_only=code_only)
            size_mb = size / (1024 * 1024)
            type_str = "Apenas Código" if code_only else "Completo"
            messagebox.showinfo(
                "Backup Concluído",
                f"Backup ({type_str}) criado com sucesso!\n\n"
                f"Arquivo: {zip_path.name}\n"
                f"Tamanho: {size_mb:.2f} MB ({size / 1024:.1f} KB)\n"
                f"Tempo decorrido: {elapsed:.2f}s",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Erro no Backup", f"Erro ao gerar backup: {e}", parent=self)
        finally:
            self.btn_create_backup.configure(state="normal", text="Criar Backup 💾")
            self._refresh_backups_list()

    def _on_restore_file_clicked(self) -> None:
        from tkinter import filedialog

        file_path_str = filedialog.askopenfilename(
            initialdir=str(Path(get_project_root()) / "backups"),
            title="Selecionar Backup para Restaurar",
            filetypes=[("Arquivos Zip", "*.zip")],
            parent=self
        )
        if not file_path_str:
            return

        zip_path = Path(file_path_str)
        if not zip_path.exists():
            return

        is_code = zip_path.name.endswith("_code.zip")
        type_desc = "apenas os arquivos de código" if is_code else "o código E as configurações pessoais"

        confirm = messagebox.askyesno(
            "Confirmar Restauração",
            f"Tem certeza que deseja restaurar {type_desc} do backup '{zip_path.name}'?\n\n"
            "Isso substituirá os arquivos antigos do aplicativo.\n"
            "O aplicativo deve ser reiniciado após a restauração.",
            parent=self
        )
        if not confirm:
            return

        try:
            restore_backup(zip_path)
            messagebox.showinfo(
                "Restauração Concluída",
                "Backup restaurado com sucesso!\n\n"
                "Por favor, feche e abra o Quantum Scribe novamente para carregar as novas configurações e código.",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Erro na Restauração", f"Falha ao restaurar o backup: {e}", parent=self)

    def _on_restore_selected_clicked(self) -> None:
        selected_item = self.backup_tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um backup na lista para restaurar.", parent=self)
            return

        item_id = selected_item[0]
        backup_data = self._backup_items_map.get(item_id)
        if not backup_data:
            return

        zip_path = backup_data["path"]
        is_code = zip_path.name.endswith("_code.zip")
        type_desc = "apenas os arquivos de código" if is_code else "o código E as configurações pessoais"

        confirm = messagebox.askyesno(
            "Confirmar Restauração",
            f"Tem certeza que deseja restaurar {type_desc} do backup '{zip_path.name}'?\n\n"
            "Isso substituirá os arquivos antigos do aplicativo.\n"
            "O aplicativo deve ser reiniciado após a restauração.",
            parent=self
        )
        if not confirm:
            return

        try:
            restore_backup(zip_path)
            messagebox.showinfo(
                "Restauração Concluída",
                "Backup restaurado com sucesso!\n\n"
                "Por favor, feche e abra o Quantum Scribe novamente para carregar as novas configurações e código.",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Erro na Restauração", f"Falha ao restaurar o backup: {e}", parent=self)

    def _on_delete_selected_clicked(self) -> None:
        selected_item = self.backup_tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um backup na lista para excluir.", parent=self)
            return

        item_id = selected_item[0]
        backup_data = self._backup_items_map.get(item_id)
        if not backup_data:
            return

        zip_path = backup_data["path"]
        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir permanentemente o arquivo de backup '{zip_path.name}'?",
            parent=self
        )
        if not confirm:
            return

        try:
            delete_backup(zip_path)
            self._refresh_backups_list()
        except Exception as e:
            messagebox.showerror("Erro ao Excluir", f"Falha ao excluir o backup: {e}", parent=self)

    # ------------------ FOOTER & SALVAR ------------------
    def _build_footer(self) -> None:
        footer_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        footer_frame.pack(side="bottom", fill="x", pady=(20, 0))

        tk.Frame(footer_frame, bg=BORDER_COLOR, height=1).pack(fill="x", pady=(0, 15))

        self.error_label = tk.Label(footer_frame, text="", font=("Segoe UI Semibold", 9), fg=DANGER_COLOR, bg=BG_COLOR, anchor="w")
        self.error_label.pack(side="left", padx=25)  # Espaçamento para alinhar com o padding interno do canvas

        self.save_btn = tk.Button(
            footer_frame, text="Salvar Alterações", bg=ACCENT_COLOR, fg="#ffffff",
            activebackground=ACCENT_HOVER, activeforeground="#ffffff", font=("Segoe UI Bold", 9),
            relief="flat", bd=0, padx=20, pady=6, cursor="hand2", command=self._on_save_clicked
        )
        self.save_btn.pack(side="right", padx=(0, 25))
        self.save_btn.bind("<Enter>", lambda _: self.save_btn.configure(bg=ACCENT_HOVER))
        self.save_btn.bind("<Leave>", lambda _: self.save_btn.configure(bg=ACCENT_COLOR))

        cancel_btn = tk.Button(
            footer_frame, text="Cancelar", bg=CANCEL_BG, fg=TEXT_COLOR,
            activebackground=CANCEL_HOVER, activeforeground=TEXT_COLOR, font=("Segoe UI Semibold", 9),
            relief="flat", bd=0, padx=15, pady=6, cursor="hand2", command=self.destroy
        )
        cancel_btn.pack(side="right")
        cancel_btn.bind("<Enter>", lambda e, b=cancel_btn: b.configure(bg=CANCEL_HOVER))
        cancel_btn.bind("<Leave>", lambda e, b=cancel_btn: b.configure(bg=CANCEL_BG))

    def _set_widgets_state(self, state: str) -> None:
        for sid, btn_data in self._sidebar_btns.items():
            btn_data["frame"].configure(cursor="" if state == "disabled" else "hand2")

    def _on_save_clicked(self) -> None:
        hotkey_normal = self.hotkey_normal_entry.get().strip() if self.hotkey_normal_entry is not None else self.current_config.hotkey
        hotkey_translate = self.hotkey_translate_entry.get().strip() if self.hotkey_translate_entry is not None else getattr(self.current_config, "hotkey_translate", "Ctrl+Alt+Space")
        hotkey_auto_send = self.hotkey_auto_send_entry.get().strip() if self.hotkey_auto_send_entry is not None else getattr(self.current_config, "hotkey_auto_send", "Ctrl+Shift+Space")
        hotkey_quantum_brain = self.hotkey_quantum_brain_entry.get().strip() if self.hotkey_quantum_brain_entry is not None else getattr(self.current_config, "hotkey_quantum_brain", "Ctrl+Shift+D")

        # Valida atalhos
        for name, val in [("Normal", hotkey_normal), ("Tradução", hotkey_translate), ("Auto Enviar", hotkey_auto_send), ("Quantum Brain", hotkey_quantum_brain)]:
            try:
                _parse_hotkey(val)
            except ValueError as exc:
                self.error_label.configure(text=f"Erro no atalho ({name}): {exc}", fg=DANGER_COLOR)
                self._show_section("preferences")
                return

        lang_friendly = self.lang_friendly_var.get()
        lang = self._lang_friendly_map.get(lang_friendly, "auto")
        if lang == "auto":
            lang = ""

        mic_selected = self.mic_var.get()
        if mic_selected == "Padrão do Sistema":
            mic_selected = ""

        selected_model_id = self.friendly_to_id.get(self.model_name_var.get(), "medium")

        custom_dict = self.current_config.custom_dict

        updated_config = AppConfig(
            model=selected_model_id,
            language=lang,
            device=self.device_var.get(),
            compute_type=self.compute_var.get(),
            preload_model=getattr(self.current_config, "preload_model", False),
            auto_download_model=getattr(self.current_config, "auto_download_model", True),
            audio_device=mic_selected,
            auto_paste=self.paste_var.get(),
            hotkey=hotkey_normal,
            hotkey_translate=hotkey_translate,
            hotkey_auto_send=hotkey_auto_send,
            hotkey_quantum_brain=hotkey_quantum_brain,
            quantum_brain_enabled=self.quantum_brain_enabled_var.get(),
            quantum_brain_sync_interval_min=self.quantum_brain_sync_interval_var.get(),
            quantum_brain_sync_threshold=self.quantum_brain_sync_threshold_var.get(),
            quantum_brain_also_paste=self.quantum_brain_also_paste_var.get(),
            quantum_brain_llm_repo=getattr(self.current_config, "quantum_brain_llm_repo", "jncraton/Qwen2.5-3B-Instruct-ct2-int8"),
            quantum_brain_api_key=getattr(self.current_config, "quantum_brain_api_key", ""),
            initial_prompt=self.prompt_text.get("1.0", "end-1c").strip() if self.prompt_text is not None else (getattr(self.current_config, "initial_prompt", "") or ""),
            play_sounds=self.sounds_var.get(),
            sound_volume=float(self.sound_volume_var.get()),
            hud_theme=self._theme_id_map.get(self.hud_theme_var.get(), "dots"),
            atom_color=self._atom_color_val,
            custom_dict=custom_dict,
            tone_style=self.tone_var.get(),
            literal_mode=self.literal_mode_var.get(),
            punctuation_assist=self.punctuation_assist_var.get(),
            punctuation_pause_ms=getattr(self.current_config, "punctuation_pause_ms", 650),
            continuous_learning=self.learning_var.get(),
            use_llm_rewriter=self.rewriter_var.get(),
            ai_mode=self.ai_mode_var.get(),
            llm_model_repo=getattr(self.current_config, "llm_model_repo", "jncraton/Qwen2.5-0.5B-Instruct-ct2-int8"),
            custom_tones=getattr(self.current_config, "custom_tones", {}),
            llm_custom_tones=getattr(self.current_config, "llm_custom_tones", {}),
            # ---- Motor de Voz ----
            streaming_mode=self.streaming_var.get(),
            stream_min_silence_ms=self.min_silence_var.get(),
            audio_enhance=self.audio_enhance_var.get(),
            audio_enhance_profile=self._profile_id_map.get(self.audio_enhance_profile_var.get(), "balanced"),
            remove_stutters=self.remove_stutters_var.get(),
            remove_fillers=self.remove_fillers_var.get(),
            custom_fillers=self.custom_fillers_entry.get().strip() if self.custom_fillers_entry is not None else getattr(self.current_config, "custom_fillers", ""),
            save_audio_for_training=getattr(self.current_config, "save_audio_for_training", False),
        )

        self.on_save_callback(updated_config)
        self.destroy()

    def destroy(self) -> None:
        self._stop_test_stream()
        super().destroy()
