import json
from pathlib import Path

from scripts.inventory_bundle import build_inventory, main


def test_inventory_is_deterministic_and_contains_sha256(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "b.txt").write_text("b", encoding="utf-8")
    (artifact / "a.txt").write_text("a", encoding="utf-8")

    first = build_inventory(artifact, max_bytes=1024)
    second = build_inventory(artifact, max_bytes=1024)

    assert first == second
    assert [entry["path"] for entry in first["files"]] == ["a.txt", "b.txt"]
    assert all(len(entry["sha256"]) == 64 for entry in first["files"])
    assert first["policy"]["passed"] is True


def test_inventory_rejects_forbidden_content_names_and_size(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "onnxruntime.dll").write_bytes(b"optional")
    (artifact / "model.onnx").write_bytes(b"model")

    report = tmp_path / "inventory.json"
    assert main([str(artifact), "--output", str(report), "--max-bytes", "1"]) == 1

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["policy"]["passed"] is False
    assert {item["path"] for item in payload["forbidden_matches"]} == {
        "model.onnx",
        "onnxruntime.dll",
    }


def test_inventory_excludes_its_output_when_inside_artifact(tmp_path: Path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "app.exe").write_bytes(b"app")
    report = artifact / "inventory.json"

    assert main([str(artifact), "--output", str(report)]) == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert [entry["path"] for entry in payload["files"]] == ["app.exe"]
