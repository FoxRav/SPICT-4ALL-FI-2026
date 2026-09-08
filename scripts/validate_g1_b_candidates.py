"""Validate the corrected Agent B run and prove the original 001 hashes are intact."""

import json
from pathlib import Path

from spict4all.g1_b_correction import G1_B_002_RUN_ID, verify_frozen_g1_b_001
from spict4all.g1_forward_runner import validate_run

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "work/agent-b/runs" / G1_B_002_RUN_ID / "candidates.jsonl"

if __name__ == "__main__":
    verify_frozen_g1_b_001(ROOT)
    result = validate_run(ROOT, CANDIDATES, translator_role="forward_translation_B")
    print(json.dumps(result, ensure_ascii=False, indent=2))
