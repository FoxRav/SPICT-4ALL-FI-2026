"""Build the targeted G1-B-20260908-002 correction run. Never overwrites 001."""

from pathlib import Path

from spict4all.g1_b_correction import create_correction_run

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    run_dir = create_correction_run(ROOT)
    print(f"WROTE {run_dir.relative_to(ROOT).as_posix()}")
