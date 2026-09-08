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
        raise ArtifactValidationError("G5 validation failed: " + "; ".join(failures))
    run_dir = ROOT / G5_RUN_DIR
    summary = json.loads((run_dir / "G5_REVIEW_SUMMARY.json").read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "run_id": G5_RUN_ID,
                "status": summary.get("status"),
                "completed_human_dispositions": summary.get(
                    "completed_human_dispositions"
                ),
                "remaining_human_dispositions": summary.get(
                    "remaining_human_dispositions"
                ),
                "g5_gate_passed": False,
                "packet_sha256": sha256_file(run_dir / "G5_HUMAN_REVIEW_PACKET.md"),
                "dispositions_sha256": sha256_file(run_dir / "human_dispositions.tsv"),
                "events_sha256": sha256_file(run_dir / "human_decision_events.jsonl"),
                "summary_sha256": sha256_file(run_dir / "G5_REVIEW_SUMMARY.json"),
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
