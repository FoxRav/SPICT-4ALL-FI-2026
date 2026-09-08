"""Validate the blank T1 preparation package without promoting terminology."""
from __future__ import annotations

import json
from pathlib import Path

from spict4all.adjudication import validate_package

if __name__ == "__main__":
    print(json.dumps(validate_package(Path(__file__).resolve().parents[1]), indent=2))
