from __future__ import annotations

from pathlib import Path

from spict4all.g1_t1_isolation import hide_g1_agent_b_work_files


def test_hide_g1_files_leaves_placeholder_and_restores(tmp_path: Path) -> None:
    agent_b = tmp_path / "work" / "agent-b"
    agent_b.mkdir(parents=True)
    gitkeep = agent_b / ".gitkeep"
    gitkeep.write_bytes(b"")
    nested = agent_b / "runs" / "G1-B-20260908-002"
    nested.mkdir(parents=True)
    target = nested / "candidates.jsonl"
    target.write_text("x\n", encoding="utf-8")
    aside = tmp_path / "aside"
    with hide_g1_agent_b_work_files(tmp_path, aside):
        assert not target.exists()
        assert gitkeep.is_file()
        remaining = [path for path in agent_b.rglob("*") if path.is_file()]
        assert remaining == [gitkeep]
    assert target.read_text(encoding="utf-8") == "x\n"
    assert gitkeep.read_bytes() == b""
