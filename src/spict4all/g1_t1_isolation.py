"""Hide G1 Agent B work files from historical T1 work-inventory checks.

T1 validators must keep the T1 work_files lock exact. G1 evidence lives under
work/agent-b/ and must not be accommodated by weakening T1. Tests and G1
packaging hide those files only while T1 inventory is evaluated.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

PLACEHOLDER_NAME = ".gitkeep"
AGENT_B_RELATIVE = Path("work") / "agent-b"


@contextmanager
def hide_g1_agent_b_work_files(root: Path, aside: Path) -> Iterator[list[Path]]:
    """Move non-placeholder Agent B work files aside, then restore them.

    Empty directories may remain under work/agent-b/; T1 inventory counts files
    only. Placeholder .gitkeep files stay in place.
    """

    agent_b = root / AGENT_B_RELATIVE
    moved: list[tuple[Path, Path]] = []
    if agent_b.is_dir():
        for path in sorted(item for item in agent_b.rglob("*") if item.is_file()):
            if path.name == PLACEHOLDER_NAME:
                continue
            relative = path.relative_to(agent_b)
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
