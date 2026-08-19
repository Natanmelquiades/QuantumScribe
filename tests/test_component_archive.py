import hashlib
import json
import zipfile
from pathlib import Path

from scripts.validate_component_archive import main


def _write_component(path: Path, *, key: str = "silero_vad", version: str = "2.2.34") -> None:
    content = b"component payload"
    manifest = {
        "schema": 1,
        "key": key,
        "version": version,
        "required_files": ["payload.bin"],
        "files": [
            {
                "path": "payload.bin",
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        ],
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("payload.bin", content)
        archive.writestr("component.json", json.dumps(manifest))


def test_valid_component_archive_is_accepted(tmp_path: Path):
    archive = tmp_path / "component.zip"
    _write_component(archive)

    assert main(
        [
            str(archive),
            "--key",
            "silero_vad",
            "--version",
            "2.2.34",
            "--required",
            "payload.bin",
        ]
    ) == 0


def test_component_archive_rejects_tampering_and_path_traversal(tmp_path: Path):
    archive = tmp_path / "tampered.zip"
    content = b"component payload"
    manifest = {
        "schema": 1,
        "key": "silero_vad",
        "version": "2.2.34",
        "files": [{"path": "payload.bin", "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}],
    }
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("payload.bin", b"tampered")
        handle.writestr("component.json", json.dumps(manifest))
        handle.writestr("../escape.txt", b"unsafe")

    assert main([str(archive), "--key", "silero_vad", "--version", "2.2.34"]) == 1
