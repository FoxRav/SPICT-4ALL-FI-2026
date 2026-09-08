"""Targeted G1-B correction run. Original 001 evidence is never overwritten."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import ArtifactValidationError, ImmutableRunError
from .g1_forward_runner import build_run, validate_run
from .hashing import sha256_file
from .runs import build_run_metadata, create_immutable_run

G1_B_001_RUN_ID = "G1-B-20260908-001"
G1_B_002_RUN_ID = "G1-B-20260908-002"
CORRECTION_WORKPACKAGE = "WP-G1-B-CORRECTION-R2-001"
TRANSLATOR_ROLE = "forward_translation_B"

FROZEN_G1_B_001_HASHES: dict[str, str] = {
    "work/agent-b/agent_b_translations.json": (
        "1d10eb85a0fbad412148e90c2f890a05c473bcf4165b1b3bca99dfbd185a775e"
    ),
    "work/agent-b/candidates.jsonl": (
        "0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640"
    ),
}

AUTHORIZED_CORRECTION_UNIT_IDS: tuple[str, ...] = (
    "S4A-2026-001",
    "S4A-2026-004",
    "S4A-2026-014",
    "S4A-2026-017",
    "S4A-2026-042",
)

CORRECTED_CANDIDATE_FI: dict[str, str] = {
    "S4A-2026-001": (
        "SPICT auttaa meit\u00e4 etsim\u00e4\u00e4n ihmisi\u00e4, joilla on "
        "elinik\u00e4\u00e4 lyhent\u00e4vi\u00e4 terveydentiloja ja joiden "
        "terveydentila on heikentynyt. N\u00e4m\u00e4 ihmiset tarvitsevat nyt "
        "enemm\u00e4n apua ja hoitoa sek\u00e4 suunnitelman tulevaa hoitoa varten."
    ),
    "S4A-2026-004": (
        "Toimintakyky on heikentynyt tavanomaisissa toimissa; ei ole yht\u00e4 "
        "hyv\u00e4ss\u00e4 kunnossa kuin ennen.\n"
        "(Henkil\u00f6 on usein vuoteessa tai tuolissa yli puolet p\u00e4iv\u00e4st\u00e4.)"
    ),
    "S4A-2026-014": (
        "Toimintakyky on heikentynyt tavanomaisissa toimissa, ja terveys heikkenee."
    ),
    "S4A-2026-017": (
        "Ei ole riitt\u00e4v\u00e4n hyv\u00e4kuntoinen sy\u00f6p\u00e4hoitoon, "
        "tai hoito on oireiden helpottamiseksi."
    ),
    "S4A-2026-042": (
        "Ihmiset, joiden terveydentila on heikentynyt ja joilla on muita "
        "elinik\u00e4\u00e4 lyhent\u00e4vi\u00e4 ruumiillisia tai henkisi\u00e4 "
        "sairauksia tai terveydentiloja. Hoitoa ei ole saatavilla, tai se ei tehoa hyvin."
    ),
}

ISOLATION_STATEMENT = (
    "Targeted correction of G1-B-20260908-001 following independent audit. "
    "No Agent A artifact, sibling worktree, synthesis output, back-translation "
    "or critic output from another candidate was read or supplied. Authorized "
    "inputs only: the exact frozen English source, the existing G1-B-20260908-001 "
    "candidate, existing T0/T1 evidence in this B worktree, and human decisions "
    "recorded before G1. T1.2 Project Owner wordings were applied exactly; no "
    "terminology decision IDs were invented. T-002, T-013 and T-016 remain applied."
)


def verify_frozen_g1_b_001(root: Path) -> None:
    """Refuse to proceed if the original G1-B run bytes have changed."""

    for relative, expected in FROZEN_G1_B_001_HASHES.items():
        path = root / relative
        if not path.is_file():
            raise ImmutableRunError(f"Frozen G1-B-20260908-001 missing: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise ImmutableRunError(
                f"Frozen G1-B-20260908-001 changed: {relative} "
                f"has {actual}, expected {expected}"
            )


def refuse_frozen_overwrite(destination: Path, root: Path) -> None:
    frozen = {(root / relative).resolve() for relative in FROZEN_G1_B_001_HASHES}
    if destination.resolve() in frozen:
        raise ImmutableRunError(
            f"Refusing to overwrite frozen G1-B-20260908-001: {destination}"
        )


def load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ArtifactValidationError(f"JSONL record is not an object: {path}")
        records.append(value)
    return records


def candidate_fi_by_id(records: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for record in records:
        unit_id = record.get("unit_id")
        candidate = record.get("candidate_fi")
        if not isinstance(unit_id, str) or not isinstance(candidate, str):
            raise ArtifactValidationError("candidate record missing unit_id or candidate_fi")
        if unit_id in mapping:
            raise ArtifactValidationError(f"duplicate unit_id {unit_id}")
        mapping[unit_id] = candidate
    return mapping


def build_correction_diff(
    original_records: list[dict[str, Any]],
    corrected_records: list[dict[str, Any]],
) -> dict[str, Any]:
    original_fi = candidate_fi_by_id(original_records)
    corrected_fi = candidate_fi_by_id(corrected_records)
    if set(original_fi) != set(corrected_fi):
        raise ArtifactValidationError("Corrected run source membership differs from original")
    changed = sorted(unit_id for unit_id, text in original_fi.items() if text != corrected_fi[unit_id])
    unauthorized = [unit_id for unit_id in changed if unit_id not in AUTHORIZED_CORRECTION_UNIT_IDS]
    if unauthorized:
        raise ArtifactValidationError(
            f"Unauthorized candidate_fi changes: {unauthorized}"
        )
    missing = [unit_id for unit_id in AUTHORIZED_CORRECTION_UNIT_IDS if unit_id not in changed]
    if missing:
        raise ArtifactValidationError(
            f"Authorized units were not changed: {missing}"
        )
    unchanged = len(original_fi) - len(changed)
    return {
        "base_run_id": G1_B_001_RUN_ID,
        "corrected_run_id": G1_B_002_RUN_ID,
        "work_package": CORRECTION_WORKPACKAGE,
        "agent_a_inspected": False,
        "synthesis_performed": False,
        "g2_performed": False,
        "human_approval_created": False,
        "changed_fields": ["candidate_fi"],
        "changed_unit_ids": list(AUTHORIZED_CORRECTION_UNIT_IDS),
        "unchanged_candidate_fi_count": unchanged,
        "changes": [
            {
                "unit_id": unit_id,
                "field": "candidate_fi",
                "before": original_fi[unit_id],
                "after": corrected_fi[unit_id],
            }
            for unit_id in AUTHORIZED_CORRECTION_UNIT_IDS
        ],
    }


def corrected_authored_payload(original: dict[str, Any], timestamp_utc: str) -> dict[str, Any]:
    payload = deepcopy(original)
    run = payload.get("run")
    candidates = payload.get("candidates")
    if not isinstance(run, dict) or not isinstance(candidates, dict):
        raise ArtifactValidationError("Original authored translations are malformed")
    run["run_id"] = G1_B_002_RUN_ID
    run["workpackage"] = CORRECTION_WORKPACKAGE
    run["run_timestamp_utc"] = timestamp_utc
    run["corrects_run_id"] = G1_B_001_RUN_ID
    run["isolation_statement"] = ISOLATION_STATEMENT
    run["correction_note"] = (
        "Targeted correction of G1-B-20260908-001 following independent audit. "
        "No Agent A evidence was supplied or inspected. Only five authorized "
        "Finnish candidate_fi fields were changed."
    )
    for unit_id, finnish in CORRECTED_CANDIDATE_FI.items():
        entry = candidates.get(unit_id)
        if not isinstance(entry, dict):
            raise ArtifactValidationError(f"Original authored entry missing: {unit_id}")
        entry["candidate_fi"] = finnish
    return payload


def correction_report_text(diff: dict[str, Any], validation: dict[str, Any]) -> str:
    changes = "\n".join(
        f"- `{item['unit_id']}`: `{item['before']}` → `{item['after']}`"
        for item in diff["changes"]
    )
    return f"""# G1-B-20260908-002 correction report

Work package: **{CORRECTION_WORKPACKAGE}**
Corrected run: **{G1_B_002_RUN_ID}**
Original run: **{G1_B_001_RUN_ID}** (byte-for-byte unchanged)

## Purpose

Independent audit found that G1-B-20260908-001 did not apply three explicit
Project Owner wording decisions recorded in
`terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md`. Those
decisions pre-date G1 and are authorized input. They are not Agent A evidence.

This run is a targeted correction. It is not synthesis.

## Independence

- Agent A was not inspected.
- No Agent A translation evidence was supplied.
- No synthesis was performed.
- No G2 was performed.
- No human approval state was created.
- Schema status remains `READY_FOR_SYNTHESIS` (repository forward-run marker, not approval).

## Project Owner wordings applied exactly

1. less well → `terveydentila on heikentynyt` (`S4A-2026-001`, `S4A-2026-042`)
2. less able to manage usual activities → `toimintakyky on heikentynyt` (`S4A-2026-004`, `S4A-2026-014`), with usual/tavanomaiset activities kept in the surrounding sentence
3. not well enough for cancer treatment → `ei ole riittävän hyväkuntoinen syöpähoitoon` (`S4A-2026-017`)

No terminology decision IDs were invented for these wordings.
T-002, T-013 and T-016 remain applied.

## Changed units

Exactly five `candidate_fi` fields changed. No other Finnish candidate was edited.

{changes}

Unchanged `candidate_fi` count: {diff["unchanged_candidate_fi_count"]}

## Validation snapshot

- candidate_count: {validation.get("candidate_count")}
- canonical_count: {validation.get("canonical_count")}
- source_requirement_count: {validation.get("source_requirement_count")}
- schema_valid: {validation.get("schema_valid")}
- coverage_complete: {validation.get("coverage_complete")}
"""


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def create_correction_run(
    root: Path,
    *,
    timestamp_utc: str | None = None,
) -> Path:
    """Create G1-B-20260908-002 beside the immutable original 001 evidence."""

    verify_frozen_g1_b_001(root)
    original_authored_path = root / "work/agent-b/agent_b_translations.json"
    original_candidates_path = root / "work/agent-b/candidates.jsonl"
    original_authored = json.loads(original_authored_path.read_text(encoding="utf-8"))
    stamp = timestamp_utc or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    authored = corrected_authored_payload(original_authored, stamp)
    input_paths = [
        original_authored_path,
        original_candidates_path,
        root / "terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md",
        root / "data/source_units.jsonl",
        root / "data/source_requirements.jsonl",
        root / "terminology/adjudication/human_terminology_decisions.tsv",
    ]
    metadata = build_run_metadata(
        G1_B_002_RUN_ID,
        TRANSLATOR_ROLE,
        input_paths,
        created_at_utc=stamp,
    )
    run_dir = create_immutable_run(root / "work/agent-b/runs", metadata)
    authored_path = run_dir / "agent_b_translations.json"
    destination = run_dir / "candidates.jsonl"
    refuse_frozen_overwrite(authored_path, root)
    refuse_frozen_overwrite(destination, root)
    write_json(authored_path, authored)
    records = build_run(root, authored_path, destination)
    original_records = load_jsonl_records(original_candidates_path)
    diff = build_correction_diff(original_records, records)
    validation = validate_run(root, destination, translator_role=TRANSLATOR_ROLE)
    write_json(run_dir / "correction_diff.json", diff)
    write_json(run_dir / "validation_results.json", validation)
    (run_dir / "CORRECTION_REPORT.md").write_text(
        correction_report_text(diff, validation),
        encoding="utf-8",
        newline="\n",
    )
    verify_frozen_g1_b_001(root)
    return run_dir
