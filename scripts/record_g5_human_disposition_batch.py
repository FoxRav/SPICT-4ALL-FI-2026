"""Record the explicit Project Owner G5 disposition batch. Do not adjudicate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from spict4all.errors import ArtifactValidationError
from spict4all.g5_human_dispositions import encode_decision_events, overlay_run_metadata
from spict4all.g5_human_review import (
    G5_RUN_DIR,
    G5_RUN_ID,
    encode_json,
    g5_run_failures,
    live_dispositions_tsv,
    live_summary_text,
    load_packet_units,
    sami_review_markdown,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> None:
    run_dir = ROOT / G5_RUN_DIR
    units = load_packet_units(ROOT)
    summary = json.loads((run_dir / "G5_REVIEW_SUMMARY.json").read_text(encoding="utf-8"))
    created_at = str(summary["created_at_utc"])
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    write_text(run_dir / "human_dispositions.tsv", live_dispositions_tsv(units))
    write_text(run_dir / "human_decision_events.jsonl", encode_decision_events(G5_RUN_ID))
    write_text(run_dir / "G5_REVIEW_SUMMARY.json", live_summary_text(units, ROOT, created_at))
    write_text(run_dir / "run_metadata.json", encode_json(overlay_run_metadata(metadata)))
    write_text(run_dir / "G5_SAMI_DOMAIN_REVIEW.md", sami_review_markdown(units))
    failures = g5_run_failures(ROOT)
    if failures:
        raise ArtifactValidationError(
            "G5 disposition batch validation failed: " + "; ".join(failures)
        )
    print(
        json.dumps(
            {
                "run_id": G5_RUN_ID,
                "status": "PARTIAL_HUMAN_ADJUDICATION_5_OF_54",
                "completed_human_dispositions": 5,
                "remaining_human_dispositions": 49,
                "g5_gate_passed": False,
                "dispositions_sha256": sha256_file(run_dir / "human_dispositions.tsv"),
                "events_sha256": sha256_file(run_dir / "human_decision_events.jsonl"),
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
