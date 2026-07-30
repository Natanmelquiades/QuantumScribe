from __future__ import annotations

import os
import sys
import tempfile
import threading
from pathlib import Path
from types import MethodType
from typing import Callable

# O backend Xorg do pystray não implementa menus; no Ubuntu preferimos
# AppIndicator quando as bibliotecas do sistema estão disponíveis.
if sys.platform.startswith("linux"):
    try:
        import gi

        gi.require_version("AyatanaAppIndicator3", "0.1")
        gi.require_version("Gtk", "3.0")
        from gi.repository import AyatanaAppIndicator3, Gtk  # noqa: F401
    except (ImportError, ValueError):
        pass
    else:
        os.environ.setdefault("PYSTRAY_BACKEND", "appindicator")

import pystray
from PIL import Image, ImageDraw


def create_icon() -> Image.Image:
    """Carrega o asset oficial; o desenho legado é somente um fallback seguro."""
    asset_name = "tray-icon.png" if sys.platform.startswith("linux") else "icon.png"
    icon_path = Path(__file__).with_name("assets") / asset_name
    try:
        with Image.open(icon_path) as official:
            return official.convert("RGBA").copy()
    except (OSError, ValueError):
        pass

    # Fallback circular transparente para nunca expor um quadrado na bandeja.
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (255, 96, 0, 255)
    draw.ellipse((5, 5, 59, 59), fill=(10, 11, 13, 210), outline=color, width=2)
    widths = [10, 22, 36, 22, 10]
    for index, height in enumerate(widths):
        x = 12 + index * 10
        draw.rounded_rectangle(
            (x, 32 - height // 2, x + 5, 32 + height // 2),
            radius=3,
            fill=color,
        )
    return image


def _force_png_suffix_for_appindicator(icon: object) -> bool:
    """Evita que o AppIndicator trate o PNG temporário como bitmap opaco."""
    if icon.__class__.__module__ != "pystray._appindicator":
        return False

    def update_fs_icon(instance) -> None:
        descriptor, path = tempfile.mkstemp(prefix="quantumscribe-tray-", suffix=".png")
        try:
            with os.fdopen(descriptor, "wb") as stream:
                instance.icon.save(stream, "PNG")
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                os.unlink(path)
            except OSError:
                pass
            raise
        instance._icon_path = path
        instance._icon_valid = True

    try:
        icon._update_fs_icon = MethodType(update_fs_icon, icon)
    except (AttributeError, TypeError):
        return False
    return True


class TrayIcon:
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_open_config: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        has_context_menu = pystray.Icon.HAS_MENU
        self.icon = pystray.Icon(
            "QuantumScribe",
            create_icon(),
            "Quantum Scribe - Ctrl+Space",
            menu=pystray.Menu(
                pystray.MenuItem("Iniciar/parar ditado", on_toggle, default=has_context_menu),
                # No fallback Xorg, que não exibe menus, o clique principal abre
                # as configurações em vez de iniciar uma gravação por acidente.
                pystray.MenuItem("Abrir configurações", on_open_config, default=not has_context_menu),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", on_exit),
            ),
        )
        _force_png_suffix_for_appindicator(self.icon)
        self.thread: threading.Thread | None = None
        self.ready = threading.Event()

    def start(self) -> None:
        self.ready.clear()

        def run_icon() -> None:
            # Marca que o backend da bandeja recebeu o trabalho sem bloquear o
            # loop Tk; o título inicial já comunica que o app está disponível.
            self.ready.set()
            self.icon.run()

        self.thread = threading.Thread(target=run_icon, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.icon.stop()
