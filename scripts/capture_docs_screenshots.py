"""Capture sanitized documentation screenshots from the real Tk interfaces."""

from __future__ import annotations

import ctypes
import os
import sys
import tempfile
import time
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageGrab

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "docs" / "assets" / "screenshots"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _window_rect(widget: tk.Misc, padding: int = 0) -> tuple[int, int, int, int]:
    widget.update_idletasks()
    hwnd = widget.winfo_id()
    rect = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (
        rect.left - padding,
        rect.top - padding,
        rect.right + padding,
        rect.bottom + padding,
    )


def _capture(widget: tk.Misc, filename: str, padding: int = 0) -> Path:
    widget.update()
    time.sleep(0.25)
    image = ImageGrab.grab(bbox=_window_rect(widget, padding), all_screens=True)
    path = OUTPUT_DIR / filename
    image.save(path, "PNG", optimize=True)
    return path


def capture_settings() -> list[Path]:
    import localwhisper.settings_ui as settings_ui
    from localwhisper.config import AppConfig

    demo_diary = Path(os.environ["LOCALAPPDATA"]) / "QuantumScribeDemo" / "diary"
    demo_diary.mkdir(parents=True, exist_ok=True)
    (demo_diary / "2026-07-19.md").write_text(
        "# 2026-07-19\n\n## 09:42\n\nExemplo sanitizado de transcrição.\n\n"
        "## 14:18\n\nPlanejamento local e privado.\n\n",
        encoding="utf-8",
    )
    (demo_diary / "2026-07-18.md").write_text(
        "# 2026-07-18\n\n## 16:05\n\nRegistro de demonstração.\n\n",
        encoding="utf-8",
    )
    demo_files = [str(path) for path in demo_diary.glob("*.md")]
    settings_ui.diary_dir = lambda: Path(r"C:\QuantumScribe\Historico")
    settings_ui.get_project_root = lambda: Path(r"C:\Program Files\QuantumScribe")
    settings_ui.glob.glob = lambda _pattern: demo_files

    root = tk.Tk()
    root.withdraw()
    config = AppConfig(
        model="small",
        language="pt",
        device="cpu",
        compute_type="int8",
        audio_device="",
        initial_prompt="Português do Brasil. Preservar nomes de produtos e termos técnicos.",
        literal_mode=True,
        punctuation_assist=True,
        continuous_learning=False,
        use_llm_rewriter=False,
        hud_theme="atom_centered",
        atom_color="#BF5AF2",
        theme_mode="dark",
        accent_color="#BF5AF2",
        quantum_brain_enabled=True,
    )
    window = settings_ui.SettingsWindow(root, config, lambda _config: None)
    window.attributes("-topmost", True)

    captures: list[Path] = []
    sections = (
        ("appearance", "01-aparencia.png"),
        ("dictation", "02-ditado.png"),
        ("ai", "03-inteligencia-artificial.png"),
        ("audio", "04-microfone-audio.png"),
        ("shortcuts", "05-atalhos.png"),
        ("brain", "06-quantum-brain.png"),
        ("storage", "07-armazenamento.png"),
        ("about", "08-sobre.png"),
    )
    for section, filename in sections:
        window._show(section, update_sidebar=True)
        window.update()
        captures.append(_capture(window, filename))

    window.destroy()
    root.destroy()
    return captures


def _make_demo_stage(root: tk.Tk, title: str) -> None:
    root.configure(bg="#111318")
    root.geometry("640x220+220+180")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    frame = tk.Frame(root, bg="#171a20", highlightbackground="#30343d", highlightthickness=1)
    frame.pack(fill="both", expand=True, padx=8, pady=8)
    tk.Label(
        frame,
        text=title,
        bg="#171a20",
        fg="#f5f7fa",
        font=("Segoe UI Semibold", 14),
    ).pack(anchor="w", padx=24, pady=(22, 0))
    tk.Label(
        frame,
        text="Reconhecimento local • Seus dados permanecem no computador",
        bg="#171a20",
        fg="#8f96a3",
        font=("Segoe UI", 9),
    ).pack(anchor="w", padx=24, pady=(4, 0))


def capture_hud() -> list[Path]:
    from localwhisper.config import AppConfig
    from localwhisper.ui import Popup

    def capture_state(filename: str, processing: bool) -> Path:
        root = tk.Tk()
        _make_demo_stage(root, "QuantumScribe em ação")
        config = AppConfig(hud_theme="atom_centered", atom_color="#BF5AF2")
        popup = Popup(root, lambda: None, get_amplitude=lambda: 0.42, config=config)
        popup.show_recording(theme="atom_centered", color="#BF5AF2")
        if processing:
            popup.show_processing_with_progress(2.5)
        else:
            popup.set_text("Ouvindo…", "Ctrl+Space para concluir")
        popup.window.geometry("+425+285")
        popup.window.attributes("-topmost", True)
        root.update()
        popup.window.update()
        path = _capture(root, filename)
        popup.hide()
        popup.window.destroy()
        root.destroy()
        return path

    return [
        capture_state("09-hud-gravando.png", processing=False),
        capture_state("10-hud-processando.png", processing=True),
    ]


def capture_tray_menu() -> Path:
    root = tk.Tk()
    _make_demo_stage(root, "QuantumScribe na bandeja")
    menu = tk.Frame(
        root,
        bg="#f7f7f7",
        highlightbackground="#aeb3ba",
        highlightthickness=1,
        width=230,
        height=142,
    )
    menu.place(x=360, y=68)
    menu.pack_propagate(False)

    items = (
        ("Iniciar/parar ditado", True),
        ("Abrir configurações", False),
        ("", False),
        ("Sair", False),
    )
    for label, bold in items:
        if not label:
            tk.Frame(menu, bg="#d6d8dc", height=1).pack(fill="x", padx=8, pady=3)
            continue
        tk.Label(
            menu,
            text=label,
            bg="#f7f7f7",
            fg="#18191c",
            anchor="w",
            padx=14,
            font=("Segoe UI Semibold" if bold else "Segoe UI", 10),
        ).pack(fill="x", ipady=5)

    root.update()
    path = _capture(root, "11-menu-bandeja.png")
    root.destroy()
    return path


def create_social_preview() -> Path:
    width, height = 1280, 640
    image = Image.new("RGB", (width, height), "#0a0b0d")
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / height
        color = (
            int(10 + 12 * ratio),
            int(11 + 8 * ratio),
            int(13 + 12 * ratio),
        )
        draw.line((0, y, width, y), fill=color)

    icon_path = PROJECT_ROOT / "localwhisper" / "assets" / "icon.png"
    icon = Image.open(icon_path).convert("RGBA").resize((210, 210), Image.Resampling.LANCZOS)
    image.paste(icon, (95, 215), icon)

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        name = "seguisb.ttf" if bold else "segoeui.ttf"
        return ImageFont.truetype(str(Path(os.environ["WINDIR"]) / "Fonts" / name), size)

    draw.text((365, 205), "QuantumScribe", fill="#ffffff", font=font(74, bold=True))
    draw.text(
        (370, 310),
        "Ditado por voz local para Windows",
        fill="#BF5AF2",
        font=font(31, bold=True),
    )
    draw.text(
        (370, 365),
        "Fiel ao que você falou. Rápido. Privado. Offline.",
        fill="#b7bdc8",
        font=font(24),
    )
    draw.rounded_rectangle((370, 430, 615, 478), radius=24, fill="#20242c")
    draw.text((398, 441), "faster-whisper", fill="#f5f7fa", font=font(18, bold=True))
    draw.rounded_rectangle((630, 430, 820, 478), radius=24, fill="#20242c")
    draw.text((666, 441), "CPU + CUDA", fill="#f5f7fa", font=font(18, bold=True))

    path = PROJECT_ROOT / "docs" / "assets" / "social-preview.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
    return path


def main() -> None:
    _enable_dpi_awareness()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="quantumscribe-docs-") as temp_dir:
        os.environ["LOCALAPPDATA"] = temp_dir
        paths = capture_settings() + capture_hud() + [capture_tray_menu(), create_social_preview()]
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
