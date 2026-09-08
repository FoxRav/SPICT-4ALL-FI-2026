"""Validate the G2-20260908-001 synthesis run against frozen G1 inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from spict4all.coverage import require_complete_coverage
from spict4all.errors import ArtifactValidationError
from spict4all.g1_forward_runner import load_evidence_sources
from spict4all.g2_synthesis import (
    EXPECTED_COUNT,
    G2_RUN_DIR,
    G2_RUN_ID,
    classification_counts,
    g2_run_failures,
    load_g2_run,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    failures = g2_run_failures(ROOT)
    if failures:
        raise ArtifactValidationError("G2 run validation failed: " + "; ".join(failures))
    run_dir = ROOT / G2_RUN_DIR
    candidates, decisions = load_g2_run(run_dir)
    evidence = load_evidence_sources(ROOT)
    coverage = require_complete_coverage(evidence, candidates)
    print(
        json.dumps(
            {
                "run_id": G2_RUN_ID,
                "status": "PASS",
                "candidate_count": len(candidates),
                "decision_count": len(decisions),
                "expected_count": EXPECTED_COUNT,
                "coverage_complete": coverage.complete,
                "classifications": classification_counts(decisions),
                "candidate_sha256": sha256_file(run_dir / "candidates.jsonl"),
                "synthesis_decisions_sha256": sha256_file(
                    run_dir / "synthesis_decisions.jsonl"
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
