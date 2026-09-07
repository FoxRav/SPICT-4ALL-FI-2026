"""Immutable run-directory creation and input provenance."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .errors import ImmutableRunError
from .hashing import sha256_file

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def build_run_metadata(
    run_id: str,
    role: str,
    inputs: Iterable[Path],
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ImmutableRunError(f"Invalid run_id: {run_id!r}")
    input_records = []
    for path in sorted((item.resolve() for item in inputs), key=lambda item: str(item)):
        if not path.is_file():
            raise ImmutableRunError(f"Run input does not exist: {path}")
        input_records.append(
            {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        )
    timestamp = created_at_utc or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return {
        "run_id": run_id,
        "role": role,
        "status": "DRAFT",
        "created_at_utc": timestamp,
        "tool_version": __version__,
        "inputs": input_records,
    }


def create_immutable_run(runs_root: Path, metadata: dict[str, Any]) -> Path:
    run_id = metadata.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise ImmutableRunError(f"Invalid run_id: {run_id!r}")
    runs_root.mkdir(parents=True, exist_ok=True)
    run_dir = runs_root / run_id
    try:
        run_dir.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise ImmutableRunError(f"Run directory already exists; refusing overwrite: {run_dir}") from exc
    metadata_path = run_dir / "run_metadata.json"
    with metadata_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return run_dir
