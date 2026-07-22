from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import pystray
from PIL import Image, ImageDraw


def create_icon() -> Image.Image:
    """Carrega o asset oficial; o desenho legado é somente um fallback seguro."""
    icon_path = Path(__file__).with_name("assets") / "icon.png"
    try:
        with Image.open(icon_path) as official:
            return official.convert("RGBA").copy()
    except (OSError, ValueError):
        pass

    # Fundo em preto profundo (10, 11, 13) e barras em laranja neon (255, 96, 0)
    image = Image.new("RGBA", (64, 64), (10, 11, 13, 255))
    draw = ImageDraw.Draw(image)
    color = (255, 96, 0, 255)
    widths = [10, 22, 36, 22, 10]
    for index, height in enumerate(widths):
        x = 12 + index * 10
        draw.rounded_rectangle(
            (x, 32 - height // 2, x + 5, 32 + height // 2),
            radius=3,
            fill=color,
        )
    return image


class TrayIcon:
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_open_config: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self.icon = pystray.Icon(
            "QuantumScribe",
            create_icon(),
            "Quantum Scribe - Ctrl+Space",
            menu=pystray.Menu(
                pystray.MenuItem("Iniciar/parar ditado", on_toggle, default=True),
                pystray.MenuItem("Abrir configurações", on_open_config),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", on_exit),
            ),
        )
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
