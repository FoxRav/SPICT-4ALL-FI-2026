from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spict4all.cli import main  # noqa: E402

raise SystemExit(main(["--root", str(ROOT), "verify-sources"]))
