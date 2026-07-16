from __future__ import annotations

import threading
from typing import Callable

import pystray
from PIL import Image, ImageDraw


def create_icon() -> Image.Image:
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
            "Quantum Scribe — Ctrl+Space",
            menu=pystray.Menu(
                pystray.MenuItem("Iniciar/parar ditado", on_toggle, default=True),
                pystray.MenuItem("Abrir configurações", on_open_config),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", on_exit),
            ),
        )
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.icon.stop()
