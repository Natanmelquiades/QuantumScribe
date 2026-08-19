"""Valida ZIPs de componentes antes que entrem no conjunto de release."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import PurePosixPath


def _safe_name(name: str) -> PurePosixPath:
    relative = PurePosixPath(name)
    if "\\" in name or relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"caminho inseguro no ZIP: {name!r}")
    return relative


def validate_archive(path: str, *, key: str, version: str, required: tuple[str, ...]) -> dict:
    with zipfile.ZipFile(path) as archive:
        entries = {_safe_name(info.filename).as_posix(): info for info in archive.infolist()}
        marker = entries.get("component.json")
        if marker is None:
            raise ValueError("component.json ausente")
        manifest = json.loads(archive.read(marker).decode("utf-8"))
        if manifest.get("schema") != 1 or manifest.get("key") != key or manifest.get("version") != version:
            raise ValueError("manifesto do componente não corresponde à release")

        for relative in required:
            if relative not in entries:
                raise ValueError(f"arquivo obrigatório ausente: {relative}")

        for item in manifest.get("files", []):
            relative = _safe_name(str(item["path"])).as_posix()
            if relative not in entries:
                raise ValueError(f"arquivo do manifesto ausente no ZIP: {relative}")
            content = archive.read(entries[relative])
            digest = hashlib.sha256(content).hexdigest()
            if len(content) != int(item["bytes"]) or digest != item["sha256"]:
                raise ValueError(f"hash/tamanho inválido no componente: {relative}")

        return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--key", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--required", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        validate_archive(args.archive, key=args.key, version=args.version, required=tuple(args.required))
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"Componente inválido: {error}", file=sys.stderr)
        return 1
    print(f"Componente válido: {args.key} {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
