"""Deterministic, non-interpretive discrepancy reporting."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .errors import ArtifactValidationError
from .evidence import EvidenceSource

REPORT_COLUMNS = (
    "unit_id", "source_text_sha256", "agent_a_present", "agent_b_present",
    "candidate_text_equal", "agent_a_status", "agent_b_status",
    "agent_a_issue_count", "agent_b_issue_count",
)


def generate_discrepancy_report(
    source_units: list[dict[str, Any]] | list[EvidenceSource],
    agent_a: list[dict[str, Any]],
    agent_b: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    by_a = {record["unit_id"]: record for record in agent_a}
    by_b = {record["unit_id"]: record for record in agent_b}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            for source in source_units:
                unit_id = (
                    source.evidence_id
                    if isinstance(source, EvidenceSource)
                    else str(source["unit_id"])
                )
                source_hash = (
                    source.source_text_sha256
                    if isinstance(source, EvidenceSource)
                    else source["source_text_sha256"]
                )
                a = by_a.get(unit_id)
                b = by_b.get(unit_id)
                writer.writerow(
                    {
                        "unit_id": unit_id,
                        "source_text_sha256": source_hash,
                        "agent_a_present": str(a is not None).lower(),
                        "agent_b_present": str(b is not None).lower(),
                        "candidate_text_equal": (
                            str(a.get("candidate_fi") == b.get("candidate_fi")).lower()
                            if a is not None and b is not None else ""
                        ),
                        "agent_a_status": a.get("status", "") if a else "",
                        "agent_b_status": b.get("status", "") if b else "",
                        "agent_a_issue_count": len(a.get("issues", [])) if a else "",
                        "agent_b_issue_count": len(b.get("issues", [])) if b else "",
                    }
                )
    except FileExistsError as exc:
        raise ArtifactValidationError(
            f"Report already exists; refusing overwrite: {output_path}"
        ) from exc
    return output_path
