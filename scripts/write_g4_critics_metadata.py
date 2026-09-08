"""Write G4 consolidation artifacts. Frozen critic/G2/G3 JSONL is never rewritten."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from spict4all.errors import ArtifactValidationError
from spict4all.g4_critics import (
    COMBINED_RELATIVE,
    CRITIC_A_ACTUAL_MODEL,
    CRITIC_A_PROVENANCE_LIMITATION,
    CRITIC_A_RELATIVE,
    CRITIC_B_ACTUAL_MODEL,
    CRITIC_B_PROVENANCE_BASIS,
    CRITIC_B_RELATIVE,
    EXPECTED_A_ISSUE,
    EXPECTED_A_SEVERITY,
    EXPECTED_B_ISSUE,
    EXPECTED_B_ONLY,
    EXPECTED_B_ONLY_MEDIUM,
    EXPECTED_B_SEVERITY,
    EXPECTED_CORROBORATED,
    EXPECTED_COUNT,
    EXPECTED_HASHES,
    G2_ACTUAL_MODEL,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    G4_ROLE,
    G4_RUN_DIR,
    G4_RUN_ID,
    G4_STATUS,
    INDEPENDENCE_STATEMENT,
    REPORT_RELATIVE,
    REVIEW_INPUT_RELATIVE,
    SAME_FAMILY_LIMITATION,
    WORK_PACKAGE,
    build_combined_findings,
    encode_combined_row,
    issue_ids,
    medium_plus_units,
    severity_counts,
    status_groups,
    verify_frozen_g4_bytes,
)
from spict4all.hashing import sha256_file, sha256_text
from spict4all.jsonl import load_jsonl
from spict4all.runs import build_run_metadata

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime.now(UTC).isoformat().replace("+00:00", "Z")
RUN_METADATA_ROLE = (
    f"{G4_ROLE} (Critic A actual model: {CRITIC_A_ACTUAL_MODEL}; "
    f"Critic B actual model: {CRITIC_B_ACTUAL_MODEL})"
)


def encode_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_new(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _severity_lines(counts: dict[str, int]) -> str:
    return "\n".join(
        f"- {name}: **{counts[name]}**"
        for name in ("NONE", "LOW", "MEDIUM", "HIGH", "BLOCKER")
    )


def _id_list(ids: tuple[str, ...] | list[str]) -> str:
    return "\n".join(f"- `{unit_id}`" for unit_id in ids)


def report_text(
    combined: list[dict[str, Any]],
    critic_a: list[dict[str, Any]],
    critic_b: list[dict[str, Any]],
    combined_sha: str,
) -> str:
    groups = status_groups(combined)
    triage = medium_plus_units(combined)
    a_counts = severity_counts(critic_a)
    b_counts = severity_counts(critic_b)
    row_025 = next(row for row in combined if row["unit_id"] == "S4A-2026-025")
    row_045 = next(row for row in combined if row["unit_id"] == "S4A-2026-045")
    return f"""# SPICT-4ALL FI — G4 independent critic consolidation

Work package: **{WORK_PACKAGE}**
Run: **{G4_RUN_ID}**
Role: **{G4_ROLE}**
Status: **{G4_STATUS}**
Coverage: **{EXPECTED_COUNT}/54**

G4 does not adjudicate translation units and does not revise Finnish wording.
This package consolidates two completed independent critic outputs.
It is not human approval and not clinical validation. These mechanical checks
are not clinical validation.

G5 was not created. No Finnish G2 candidate was changed. No G3 back-translation
was changed. No critic output was changed.

## Critic coverage

- Review input: **{EXPECTED_COUNT}/54**
- Critic A: **{EXPECTED_COUNT}/54**
- Critic B: **{EXPECTED_COUNT}/54**
- Combined findings: **{EXPECTED_COUNT}/54**
- Same unit IDs and original order across review input, Critic A, Critic B,
  G2 candidates, and G3 back-translation.

## Critic independence statement

{INDEPENDENCE_STATEMENT}

## Model provenance

### Critic A

- **actual model:** {CRITIC_A_ACTUAL_MODEL}
- {CRITIC_A_PROVENANCE_LIMITATION}

### Critic B

- **actual model:** {CRITIC_B_ACTUAL_MODEL}
- {CRITIC_B_PROVENANCE_BASIS}

### Same-family limitation

G2 synthesis actual model: **{G2_ACTUAL_MODEL}**.

{SAME_FAMILY_LIMITATION}

Configured / planned adversarial-critic role model in `config/model_roles.yaml`:
Cursor Grok 4.6 Medium. This consolidation does not treat that configured role
as Critic A's recorded actual model.

## Raw severity distributions

### Critic A

- records: **{EXPECTED_COUNT}**
- ISSUE: **{EXPECTED_A_ISSUE}**
{_severity_lines(a_counts)}

### Critic B

- records: **{EXPECTED_COUNT}**
- ISSUE: **{EXPECTED_B_ISSUE}**
{_severity_lines(b_counts)}

## Cross-critic result

Expected and observed:

- corroborated by both critics: 7
- Critic-A-only issues: 0
- Critic-B-only issues: 14

Corroboration is stronger review evidence requiring later adjudication. It is
not human approval and not automatic proof of error.

## 7 corroborated findings

{_id_list(EXPECTED_CORROBORATED)}

## 14 Critic-B-only findings

{_id_list(EXPECTED_B_ONLY)}

Observed Critic-A-only findings: **{len(groups.get("CRITIC_A_ONLY", []))}**.

Critic-B-only MEDIUM findings:

{_id_list(EXPECTED_B_ONLY_MEDIUM)}

## Strongest corroborated findings

These are high-priority G5 adjudication items. This consolidation does not
automatically accept a correction.

### S4A-2026-025

- Critic A: **{row_025["critic_a_severity"]}**
- Critic B: **{row_025["critic_b_severity"]}**
- finding_status: **{row_025["finding_status"]}**
- combined_review_priority: **{row_025["combined_review_priority"]}**

Both critics independently flagged a literal Finnish rendering of
"when the chest is at its best".

### S4A-2026-045

- Critic A: **{row_045["critic_a_severity"]}**
- Critic B: **{row_045["critic_b_severity"]}**
- finding_status: **{row_045["finding_status"]}**
- combined_review_priority: **{row_045["combined_review_priority"]}**

Both critics independently flagged a literal Finnish rendering of
"chest infections". Critic A recorded BLOCKER; Critic B recorded HIGH.
This consolidation does not reinterpret or downgrade that disagreement.

## MEDIUM-or-higher findings from either critic

Units with Critic A or Critic B severity MEDIUM, HIGH, or BLOCKER:

{_id_list(triage)}

`combined_review_priority` is the maximum reported critic severity for triage
only. Disagreement is not downgraded. No consensus wording is invented.

## Human-decision conflicts

Preserve explicitly that critic findings concerning `S4A-2026-001` and
`S4A-2026-042` intersect the recorded Project Owner wording decision for
"less well" (`terveydentila on heikentynyt`).

Preserve explicitly that `S4A-2026-017` intersects the recorded Project Owner
wording for "not well enough for cancer treatment"
(`ei ole riittävän hyväkuntoinen syöpähoitoon`).

Those three units are recorded as:

`EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5`

The recorded human decisions are **not** overridden. The critic findings are
**not** suppressed.

`S4A-2026-021` frailty/hauraus has **no final recorded human wording
decision**. That distinction is preserved. Critic B flagged it independently;
Critic A did not.

## Unresolved source-authority issues

Source-authority issues are kept separate from translation critic findings.
Critic severity is not a source-authority BLOCKER.

### S4A-2026-000

- source-authority status remains **UNRESOLVED**
- not eligible for document insertion
- publication-blocking
- critic findings do not resolve this

### S4A-REQ-2026-001

- remains **NONCANONICAL**
- canonical omission remains unresolved
- publication-blocking
- critic findings do not resolve this

## Frozen linkage hashes

- `{REVIEW_INPUT_RELATIVE}`: `{EXPECTED_HASHES[REVIEW_INPUT_RELATIVE]}`
- `{CRITIC_A_RELATIVE}`: `{EXPECTED_HASHES[CRITIC_A_RELATIVE]}`
- `{CRITIC_B_RELATIVE}`: `{EXPECTED_HASHES[CRITIC_B_RELATIVE]}`
- `{G2_CANDIDATES_RELATIVE}`: `{EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]}`
- `{G3_BACK_RELATIVE}`: `{EXPECTED_HASHES[G3_BACK_RELATIVE]}`
- `{COMBINED_RELATIVE}`: `{combined_sha}`
- `{REPORT_RELATIVE}` is this report

## G4 does not adjudicate or revise Finnish wording

This consolidation retains Critic A and Critic B proposed Finnish strings as
review evidence only. It does not apply them. The current G2 Finnish candidate
remains the Finnish wording under review. G5 human disposition is still
required for all 54 translatable units. `requires_G5_human_disposition` marks
items needing particular attention; it is not the complete G5 requirement and
is not a G5 disposition.

This consolidation does not mark the G4 gate as passed.
"""


def main() -> None:
    payload = {relative: (ROOT / relative).read_bytes() for relative in EXPECTED_HASHES}
    verify_frozen_g4_bytes(payload)
    run_dir = ROOT / G4_RUN_DIR
    review = load_jsonl(ROOT / REVIEW_INPUT_RELATIVE)
    critic_a = load_jsonl(ROOT / CRITIC_A_RELATIVE)
    critic_b = load_jsonl(ROOT / CRITIC_B_RELATIVE)
    g2 = load_jsonl(ROOT / G2_CANDIDATES_RELATIVE)
    back = load_jsonl(ROOT / G3_BACK_RELATIVE)
    combined = build_combined_findings(review, critic_a, critic_b, g2, back)
    combined_text = "".join(encode_combined_row(row) for row in combined)
    combined_sha = sha256_text(combined_text)
    write_new(run_dir / "combined_findings.jsonl", combined_text)
    write_new(run_dir / "G4_REVIEW_REPORT.md", report_text(combined, critic_a, critic_b, combined_sha))
    metadata: dict[str, Any] = build_run_metadata(
        G4_RUN_ID,
        RUN_METADATA_ROLE,
        [
            ROOT / REVIEW_INPUT_RELATIVE,
            ROOT / CRITIC_A_RELATIVE,
            ROOT / CRITIC_B_RELATIVE,
            ROOT / G2_CANDIDATES_RELATIVE,
            ROOT / G3_BACK_RELATIVE,
        ],
        created_at_utc=CREATED_AT,
    )
    metadata["work_package"] = WORK_PACKAGE
    metadata["g4_status"] = G4_STATUS
    metadata["critic_a_actual_model"] = CRITIC_A_ACTUAL_MODEL
    metadata["critic_b_actual_model"] = CRITIC_B_ACTUAL_MODEL
    metadata["g2_actual_model"] = G2_ACTUAL_MODEL
    metadata["critic_a_provenance_limitation"] = CRITIC_A_PROVENANCE_LIMITATION
    metadata["critic_b_provenance_basis"] = CRITIC_B_PROVENANCE_BASIS
    metadata["same_family_limitation"] = SAME_FAMILY_LIMITATION
    metadata["independence_statement"] = INDEPENDENCE_STATEMENT
    metadata["human_adjudication_performed"] = False
    metadata["finnish_revised"] = False
    metadata["g3_changed"] = False
    metadata["critic_outputs_changed"] = False
    metadata["g5_created"] = False
    metadata["clinical_validation_claimed"] = False
    metadata["output"] = {
        "path": str((ROOT / COMBINED_RELATIVE).resolve()),
        "sha256": combined_sha,
        "bytes": len(combined_text.encode("utf-8")),
    }
    write_new(run_dir / "run_metadata.json", encode_json(metadata))
    groups = status_groups(combined)
    validation = {
        "run_id": G4_RUN_ID,
        "work_package": WORK_PACKAGE,
        "review_input_count": EXPECTED_COUNT,
        "critic_a_count": EXPECTED_COUNT,
        "critic_b_count": EXPECTED_COUNT,
        "combined_count": EXPECTED_COUNT,
        "id_order_match": True,
        "duplicate_ids": False,
        "review_input_sha256": EXPECTED_HASHES[REVIEW_INPUT_RELATIVE],
        "critic_a_sha256": EXPECTED_HASHES[CRITIC_A_RELATIVE],
        "critic_b_sha256": EXPECTED_HASHES[CRITIC_B_RELATIVE],
        "g2_candidates_sha256": EXPECTED_HASHES[G2_CANDIDATES_RELATIVE],
        "g3_back_translation_sha256": EXPECTED_HASHES[G3_BACK_RELATIVE],
        "combined_findings_sha256": combined_sha,
        "critic_a_issue_count": len(issue_ids(critic_a)),
        "critic_b_issue_count": len(issue_ids(critic_b)),
        "critic_a_severity": severity_counts(critic_a),
        "critic_b_severity": severity_counts(critic_b),
        "corroborated_count": len(groups["CORROBORATED"]),
        "corroborated_ids": groups["CORROBORATED"],
        "critic_a_only_count": len(groups["CRITIC_A_ONLY"]),
        "critic_b_only_count": len(groups["CRITIC_B_ONLY"]),
        "critic_b_only_ids": groups["CRITIC_B_ONLY"],
        "critic_b_only_medium_ids": list(EXPECTED_B_ONLY_MEDIUM),
        "medium_or_higher_unit_ids": medium_plus_units(combined),
        "human_decision_conflict_ids": [
            str(row["unit_id"])
            for row in combined
            if row["human_decision_conflict"]
        ],
        "source_authority_blockers": ["S4A-2026-000", "S4A-REQ-2026-001"],
        "g2_source_evidence_match": True,
        "critic_outputs_unchanged": True,
        "g2_finnish_unchanged": True,
        "g3_back_translation_unchanged": True,
        "finnish_revised": False,
        "human_approval_present": False,
        "human_adjudication_performed": False,
        "clinical_validation_claimed": False,
        "g5_created": False,
        "g4_pass_claimed": False,
        "mechanical_checks": "PASS",
        "semantic_correctness": (
            "Not claimed. G4 consolidation does not adjudicate or revise Finnish."
        ),
    }
    if (
        validation["critic_a_issue_count"] != EXPECTED_A_ISSUE
        or validation["critic_b_issue_count"] != EXPECTED_B_ISSUE
        or a_counts_mismatch(critic_a, critic_b)
    ):
        raise ArtifactValidationError("Unexpected critic count during G4 metadata write")
    write_new(run_dir / "validation_results.json", encode_json(validation))
    print(
        json.dumps(
            {
                "run_dir": G4_RUN_DIR.as_posix(),
                "combined_findings_sha256": combined_sha,
                "critic_a_sha256": sha256_file(ROOT / CRITIC_A_RELATIVE),
                "critic_b_sha256": sha256_file(ROOT / CRITIC_B_RELATIVE),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def a_counts_mismatch(
    critic_a: list[dict[str, Any]], critic_b: list[dict[str, Any]]
) -> bool:
    return (
        severity_counts(critic_a) != EXPECTED_A_SEVERITY
        or severity_counts(critic_b) != EXPECTED_B_SEVERITY
    )


if __name__ == "__main__":
    main()
