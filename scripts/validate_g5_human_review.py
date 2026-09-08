"""Validate the G5-20260908-001 human-review preparation package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from spict4all.errors import ArtifactValidationError
from spict4all.g5_human_review import G5_RUN_DIR, G5_RUN_ID, g5_run_failures
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    failures = g5_run_failures(ROOT)
    if failures:
        raise ArtifactValidationError("G5 preparation validation failed: " + "; ".join(failures))
    run_dir = ROOT / G5_RUN_DIR
    print(
        json.dumps(
            {
                "run_id": G5_RUN_ID,
                "status": "PREPARATION_VALID",
                "packet_sha256": sha256_file(run_dir / "G5_HUMAN_REVIEW_PACKET.md"),
                "dispositions_sha256": sha256_file(run_dir / "human_dispositions.tsv"),
                "summary_sha256": sha256_file(run_dir / "G5_REVIEW_SUMMARY.json"),
                "human_adjudication_performed": False,
                "g5_gate_passed": False,
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
