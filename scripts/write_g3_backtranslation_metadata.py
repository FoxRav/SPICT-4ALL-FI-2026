"""Write G3 metadata beside frozen blind-input and back-translation JSONL."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from spict4all.errors import ArtifactValidationError
from spict4all.g3_backtranslation import (
    ACTUAL_MODEL,
    BACK_TRANSLATION_RELATIVE,
    BLIND_INPUT_RELATIVE,
    BLINDING_CLAIM,
    CONFIGURED_ROLE_MODEL,
    ENVIRONMENT,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_CANDIDATES_RELATIVE,
    G3_ROLE,
    G3_RUN_DIR,
    G3_RUN_ID,
    MODEL_PROVENANCE_BASIS,
    REASONING_EFFORT,
    derivation_failures,
    g2_fi_by_id,
    g3_pair_failures,
    verify_frozen_g3_bytes,
)
from spict4all.jsonl import load_jsonl
from spict4all.runs import build_run_metadata

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime.now(UTC).isoformat().replace("+00:00", "Z")
RUN_METADATA_ROLE = (
    f"{G3_ROLE} (actual model: {ACTUAL_MODEL}; reasoning_effort: "
    f"{REASONING_EFFORT}; environment: {ENVIRONMENT})"
)


def encode_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_new(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def report_text(uncertainties: list[tuple[str, str]]) -> str:
    recorded = "\n".join(
        f"- `{unit_id}`: {note}" for unit_id, note in uncertainties
    ) or "- None recorded."
    return f"""# SPICT-4ALL FI — G3 blind back-translation

Work package: **WP-G3-BLIND-BACKTRANSLATION-AUDIT-001**
Run: **{G3_RUN_ID}**
Role: **{G3_ROLE}**
Coverage: **{EXPECTED_COUNT}/54**

## Actual model provenance

- **model:** {ACTUAL_MODEL}
- **reasoning_effort:** {REASONING_EFFORT}
- **environment:** {ENVIRONMENT}

Configured / planned role model in `config/model_roles.yaml`: {CONFIGURED_ROLE_MODEL}.
These identities differ. The discrepancy is preserved.

{MODEL_PROVENANCE_BASIS}

## Method

Blind FI→EN back-translation. The back-translator received only Finnish-only
blind input (`unit_id`, `text_fi`).

{BLINDING_CLAIM}

This work package does **not** compare the back-translation with the original
English source. **No semantic comparison** with the frozen English SPICT source
was performed in G3. That comparison belongs to a later review stage.

G3 output is evidence for later comparison. It is not human approval and not
clinical validation. These mechanical checks are not clinical validation.

G4 was not started.

## Frozen artifacts

- `{BLIND_INPUT_RELATIVE}`: `{EXPECTED_HASHES[BLIND_INPUT_RELATIVE]}`
- `{BACK_TRANSLATION_RELATIVE}`: `{EXPECTED_HASHES[BACK_TRANSLATION_RELATIVE]}`
- `{G2_CANDIDATES_RELATIVE}` (auditor derivation source only; not a translator input): `{EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]}`

Finnish blind `text_fi` matches G2 `candidate_fi` for all 54 IDs, including
`S4A-2026-000` and `S4A-REQ-2026-001`. Source-authority issues were not resolved.

## Recorded back-translator uncertainties

{recorded}

No G3 JSONL was rewritten by this metadata writer.
"""


def main() -> None:
    payload = {relative: (ROOT / relative).read_bytes() for relative in EXPECTED_HASHES}
    verify_frozen_g3_bytes(payload)
    run_dir = ROOT / G3_RUN_DIR
    blind = load_jsonl(run_dir / "blind_input.jsonl")
    back = load_jsonl(run_dir / "back_translation.jsonl")
    g2 = load_jsonl(ROOT / G2_CANDIDATES_RELATIVE)
    failures = g3_pair_failures(blind, back) + derivation_failures(blind, g2_fi_by_id(g2))
    if failures:
        raise ArtifactValidationError("G3 JSONL validation failed: " + "; ".join(failures))
    uncertainties = [
        (str(row["unit_id"]), str(row["uncertainty"]).strip())
        for row in back
        if str(row.get("uncertainty") or "").strip()
    ]
    metadata: dict[str, Any] = build_run_metadata(
        G3_RUN_ID,
        RUN_METADATA_ROLE,
        [ROOT / BLIND_INPUT_RELATIVE],
        created_at_utc=CREATED_AT,
    )
    metadata["actual_model"] = ACTUAL_MODEL
    metadata["reasoning_effort"] = REASONING_EFFORT
    metadata["environment"] = ENVIRONMENT
    metadata["configured_role_model"] = CONFIGURED_ROLE_MODEL
    metadata["model_provenance_basis"] = MODEL_PROVENANCE_BASIS
    metadata["blinding_claim"] = BLINDING_CLAIM
    metadata["work_package"] = "WP-G3-BLIND-BACKTRANSLATION-AUDIT-001"
    metadata["output"] = {
        "path": str((ROOT / BACK_TRANSLATION_RELATIVE).resolve()),
        "sha256": EXPECTED_HASHES[BACK_TRANSLATION_RELATIVE],
        "bytes": (ROOT / BACK_TRANSLATION_RELATIVE).stat().st_size,
    }
    metadata["semantic_comparison_with_source_performed"] = False
    metadata["g4_started"] = False
    write_new(run_dir / "run_metadata.json", encode_json(metadata))
    write_new(run_dir / "G3_BACKTRANSLATION_REPORT.md", report_text(uncertainties))
    validation = {
        "run_id": G3_RUN_ID,
        "actual_model": ACTUAL_MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "environment": ENVIRONMENT,
        "blind_input_count": EXPECTED_COUNT,
        "back_translation_count": EXPECTED_COUNT,
        "id_order_match": True,
        "g2_candidate_fi_derivation": "PASS",
        "blind_input_sha256": EXPECTED_HASHES[BLIND_INPUT_RELATIVE],
        "back_translation_sha256": EXPECTED_HASHES[BACK_TRANSLATION_RELATIVE],
        "g2_candidates_sha256": EXPECTED_HASHES[G2_CANDIDATES_RELATIVE],
        "title_and_requirement_preserved": True,
        "human_approval_present": False,
        "clinical_validation_claimed": False,
        "semantic_comparison_with_source_performed": False,
        "g4_started": False,
        "recorded_uncertainty_unit_ids": [item[0] for item in uncertainties],
        "jsonl_rewritten": False,
        "mechanical_checks": "PASS",
        "semantic_correctness": "Not claimed. No source-equivalence comparison was performed in G3.",
    }
    write_new(run_dir / "validation_results.json", encode_json(validation))
    print(
        json.dumps(
            {
                "run_dir": G3_RUN_DIR.as_posix(),
                "back_translation_sha256": EXPECTED_HASHES[BACK_TRANSLATION_RELATIVE],
                "blind_input_sha256": EXPECTED_HASHES[BLIND_INPUT_RELATIVE],
                "derivation": "PASS",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
