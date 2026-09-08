"""Validate the frozen G3 blind back-translation run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from spict4all.errors import ArtifactValidationError
from spict4all.g3_backtranslation import (
    EXPECTED_COUNT,
    G3_RUN_ID,
    g3_run_failures,
)
from spict4all.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    failures = g3_run_failures(ROOT)
    if failures:
        raise ArtifactValidationError("G3 run validation failed: " + "; ".join(failures))
    print(
        json.dumps(
            {
                "run_id": G3_RUN_ID,
                "status": "PASS",
                "expected_count": EXPECTED_COUNT,
                "back_translation_sha256": sha256_file(
                    ROOT / "work/backtranslation/G3-20260908-001/back_translation.jsonl"
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
