"""Validate the G4 independent-critic consolidation run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from spict4all.errors import ArtifactValidationError
from spict4all.g4_critics import G4_RUN_ID, g4_run_failures
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    failures = g4_run_failures(ROOT)
    if failures:
        raise ArtifactValidationError("G4 run validation failed: " + "; ".join(failures))
    print(
        json.dumps(
            {
                "run_id": G4_RUN_ID,
                "status": "PASS",
                "combined_findings_sha256": sha256_file(
                    ROOT / "work/critics/G4-20260908-001/combined_findings.jsonl"
                ),
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
