from __future__ import annotations

from pathlib import Path

from spict4all.g1_t1_isolation import hide_g1_work_files


def test_hide_g1_files_leaves_placeholder_and_restores(tmp_path: Path) -> None:
    contents = {
        Path("work") / "agent-a" / "candidates.jsonl": "a\n",
        Path("work") / "agent-b" / "candidates.jsonl": "b\n",
        Path("work") / "agent-b" / "runs" / "G1-B-20260908-002" / "candidates.jsonl": "x\n",
    }
    gitkeeps: list[Path] = []
    for relative, text in contents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for agent in ("agent-a", "agent-b"):
        gitkeep = tmp_path / "work" / agent / ".gitkeep"
        gitkeep.write_bytes(b"")
        gitkeeps.append(gitkeep)
    aside = tmp_path / "aside"
    with hide_g1_work_files(tmp_path, aside):
        for relative in contents:
            assert not (tmp_path / relative).exists()
        remaining = [path for path in (tmp_path / "work").rglob("*") if path.is_file()]
        assert set(remaining) == set(gitkeeps)
        assert (aside / "work" / "agent-a" / "candidates.jsonl").read_text(encoding="utf-8") == "a\n"
        assert (aside / "work" / "agent-b" / "candidates.jsonl").read_text(encoding="utf-8") == "b\n"
    for relative, text in contents.items():
        assert (tmp_path / relative).read_text(encoding="utf-8") == text
    for gitkeep in gitkeeps:
        assert gitkeep.read_bytes() == b""
