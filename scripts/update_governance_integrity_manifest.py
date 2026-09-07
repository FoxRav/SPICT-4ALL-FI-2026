"""Explicitly regenerate the project governance integrity ledger."""

from __future__ import annotations

from pathlib import Path

from spict4all.governance import (
    build_governance_manifest,
    serialize_governance_manifest,
)


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    output = repository / "data/governance_integrity_manifest.json"
    output.write_text(
        serialize_governance_manifest(build_governance_manifest(repository)),
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
