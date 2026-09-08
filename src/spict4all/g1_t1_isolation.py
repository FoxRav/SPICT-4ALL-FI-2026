"""Hide post-T1 work files from historical T1 work-inventory checks.

T1 validators must keep the T1 work_files lock exact. G1, G2, G3, G4 and G5
evidence live under work/agent-a/, work/agent-b/, work/synthesis/,
work/backtranslation/, work/critics/ and work/human-review/ and must not be
accommodated by weakening T1. Tests hide those files only while T1 inventory
is evaluated.
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
    Path("work") / "synthesis",
    Path("work") / "backtranslation",
    Path("work") / "critics",
    Path("work") / "human-review",
)


@contextmanager
def hide_g1_work_files(root: Path, aside: Path) -> Iterator[list[Path]]:
    """Move non-placeholder G1/G2/G3/G4/G5 work files aside, then restore them.

    Empty directories may remain under the agent, synthesis, backtranslation
    and critics trees; T1 inventory counts files only. Placeholder .gitkeep
    files stay in place.
    Aside paths are keyed from `root` so same-named files cannot collide.
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
