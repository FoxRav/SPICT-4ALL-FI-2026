"""Build the G5-20260908-001 human-review preparation package."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from spict4all.errors import ArtifactValidationError
from spict4all.g5_human_review import (
    G5_RUN_DIR,
    G5_RUN_ID,
    REQUIRED_OUTPUTS,
    encode_json,
    g5_run_failures,
    load_packet_units,
    render_required_artifacts,
    run_metadata_payload,
)

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> None:
    units = load_packet_units(ROOT)
    run_dir = ROOT / G5_RUN_DIR
    artifacts = render_required_artifacts(units, ROOT, CREATED_AT)
    for name in REQUIRED_OUTPUTS:
        write_text(run_dir / name, artifacts[name])
    write_text(run_dir / "run_metadata.json", encode_json(run_metadata_payload(ROOT, CREATED_AT)))
    failures = g5_run_failures(ROOT)
    if failures:
        raise ArtifactValidationError("G5 preparation failed: " + "; ".join(failures))
    print(
        json.dumps(
            {
                "run_id": G5_RUN_ID,
                "status": "PREPARATION_WRITTEN",
                "unit_count": len(units),
                "output_dir": run_dir.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
