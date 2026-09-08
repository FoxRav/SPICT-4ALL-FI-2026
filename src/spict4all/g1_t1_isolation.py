"""Hide G1 work files from historical T1 work-inventory checks.

T1 validators must keep the T1 work_files lock exact. G1 evidence lives under
work/agent-a/ and work/agent-b/ and must not be accommodated by weakening T1.
Tests hide those files only while T1 inventory is evaluated.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

PLACEHOLDER_NAME = ".gitkeep"
G1_WORK_RELATIVES = (
    Path("work") / "agent-a",
    Path("work") / "agent-b",
)


@contextmanager
def hide_g1_work_files(root: Path, aside: Path) -> Iterator[list[Path]]:
    """Move non-placeholder G1 Agent A/B work files aside, then restore them.

    Empty directories may remain under the agent trees; T1 inventory counts
    files only. Placeholder .gitkeep files stay in place. Aside paths are keyed
    from `root` so same-named files in agent-a and agent-b cannot collide.
    """

    moved: list[tuple[Path, Path]] = []
    for relative_dir in G1_WORK_RELATIVES:
        agent_dir = root / relative_dir
        if not agent_dir.is_dir():
            continue
        for path in sorted(item for item in agent_dir.rglob("*") if item.is_file()):
            if path.name == PLACEHOLDER_NAME:
                continue
            relative = path.relative_to(root)
            destination = aside / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
            moved.append((path, destination))
    try:
        yield [original for original, _stored in moved]
    finally:
        for original, stored in moved:
            original.parent.mkdir(parents=True, exist_ok=True)
            if original.exists():
                original.unlink()
            shutil.move(str(stored), str(original))


hide_g1_agent_b_work_files = hide_g1_work_files
