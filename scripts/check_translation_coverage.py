from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spict4all.cli import main  # noqa: E402

if len(sys.argv) != 2:
    print("Usage: python scripts/check_translation_coverage.py <candidate.jsonl>")
    raise SystemExit(2)

raise SystemExit(main(["--root", str(ROOT), "check-coverage", sys.argv[1]]))
