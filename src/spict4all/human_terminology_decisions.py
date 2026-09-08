"""Exact, attributable T1.2 human decisions; no glossary promotion."""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

from .errors import IntegrityError

BASE = "terminology/adjudication"
HUMAN_FILE = f"{BASE}/human_terminology_decisions.tsv"
BEFORE_HASH = "be3269d83f394a80889803aef6cbfeb198178cc02d781de630d11f0b02ffc97a"
BINDINGS = {
    "T-002": ("life shortening health conditions", "elinikää lyhentävät terveydentilat", "Project Owner"),
    "T-013": ("breathing machine", "hengityskone", "Project Owner"),
    "T-016": ("holistic care", "kokonaisvaltainen hoito", "Sami / domain expert"),
}
NOTE = ("Explicit existing human project decision reported by Project Owner in "
        "WP-T1.2-HUMAN-REVIEW-REDUCTION-001; recorded 2026-09-07. "
        "Original decision date not supplied. No automatic glossary promotion or source-authority disposition.")


def parse(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8")), delimiter="\t"))


def expected_human_table(root: Path) -> list[list[str]]:
    data = (root / BASE / "T1_2_human_decisions_before.tsv").read_bytes()
    if hashlib.sha256(data).hexdigest() != BEFORE_HASH:
        raise IntegrityError("Human decision baseline snapshot changed")
    table = parse(data)
    for row in table[1:]:
        if row[0] in BINDINGS:
            _, term, maker = BINDINGS[row[0]]
            row[1:] = ["ACCEPT", term, NOTE, maker, ""]
    return table


def historical_human_bytes(root: Path) -> bytes:
    """Validate the current authorized transition, return the unchanged historical bytes."""
    current = (root / HUMAN_FILE).read_bytes()
    if not (root / BASE / "T1_2_human_decisions_before.tsv").exists():
        return current
    if parse(current) != expected_human_table(root):
        raise IntegrityError("Human decisions: unauthorized change or blank decision mismatch")
    return (root / BASE / "T1_2_human_decisions_before.tsv").read_bytes()
