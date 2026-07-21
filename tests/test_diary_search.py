import datetime

from localwhisper.diary import diary_dir, search_entries


def test_search_entries_finds_text_without_accent_or_case(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    path = diary_dir() / "2026-07-20.md"
    path.write_text(
        "# 2026-07-20\n\n## 09:30\n\nReunião sobre oração e café.\n\n"
        "## 10:15\n\nPlanejar o lançamento local.\n",
        encoding="utf-8",
    )

    results = search_entries("REUNIAO SOBRE ORACAO")

    assert len(results) == 1
    assert results[0].time == "09:30"
    assert results[0].date == datetime.date(2026, 7, 20)
    assert results[0].preview == "Reunião sobre oração e café."


def test_search_entries_respects_date_range(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    root = diary_dir()
    (root / "2026-07-19.md").write_text("## 10:00\n\nTermo comum\n", encoding="utf-8")
    (root / "2026-07-20.md").write_text("## 11:00\n\nTermo comum novo\n", encoding="utf-8")

    results = search_entries("termo comum", start_date=datetime.date(2026, 7, 20))

    assert [entry.time for entry in results] == ["11:00"]
