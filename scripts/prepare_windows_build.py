"""Generate Windows-only build assets from the tracked project metadata."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
VERSION_PATTERN = re.compile(r'__version__\s*=\s*"([^"]+)"')


def project_version() -> str:
    match = VERSION_PATTERN.search((ROOT / "localwhisper" / "__init__.py").read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError("QuantumScribe version not found")
    return match.group(1)


def numeric_version(version: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in version.split(".")]
    if len(parts) > 4:
        raise ValueError(f"Unsupported Windows version: {version}")
    return tuple((parts + [0] * (4 - len(parts))))  # type: ignore[return-value]


def write_icon() -> None:
    source = ROOT / "localwhisper" / "assets" / "icon.png"
    destination = BUILD_DIR / "QuantumScribe.ico"
    with Image.open(source) as image:
        image.convert("RGBA").save(
            destination,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )


def write_version_info(version: str) -> None:
    numbers = numeric_version(version)
    number_text = ", ".join(str(number) for number in numbers)
    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({number_text}),
    prodvers=({number_text}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041604B0',
        [StringStruct('CompanyName', 'Natan Melquiades'),
         StringStruct('FileDescription', 'QuantumScribe — ditado local para Windows'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', 'QuantumScribe'),
         StringStruct('LegalCopyright', 'Copyright (c) 2026 Natan Melquiades'),
         StringStruct('OriginalFilename', 'QuantumScribe.exe'),
         StringStruct('ProductName', 'QuantumScribe'),
         StringStruct('ProductVersion', '{version}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
"""
    (BUILD_DIR / "QuantumScribe.version.txt").write_text(content, encoding="utf-8")


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    version = project_version()
    write_icon()
    write_version_info(version)
    print(f"Prepared Windows assets for QuantumScribe {version}")


if __name__ == "__main__":
    main()
