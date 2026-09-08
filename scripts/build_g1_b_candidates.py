"""Build work/agent-b/candidates.jsonl from authored Finnish text plus frozen sources.

The sealed G1-B-20260908-001 originals must never be overwritten. Use
scripts/build_g1_b_correction_run.py for the corrected run.
"""

from pathlib import Path

from spict4all.g1_b_correction import refuse_frozen_overwrite
from spict4all.g1_forward_runner import build_run

ROOT = Path(__file__).resolve().parents[1]
AUTHORED = ROOT / "work/agent-b/agent_b_translations.json"
DESTINATION = ROOT / "work/agent-b/candidates.jsonl"

if __name__ == "__main__":
    refuse_frozen_overwrite(DESTINATION, ROOT)
    refuse_frozen_overwrite(AUTHORED, ROOT)
    records = build_run(ROOT, AUTHORED, DESTINATION)
    print(f"WROTE {DESTINATION.relative_to(ROOT).as_posix()} records={len(records)}")
