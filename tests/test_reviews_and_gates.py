from __future__ import annotations

from pathlib import Path

import pytest

from spict4all.cli import main
from spict4all.errors import ArtifactValidationError, GateError
from spict4all.evidence import (
    EvidenceProvenance,
    EvidenceSource,
    EvidenceSourceKind,
    FinalInclusionStatus,
)
from spict4all.gates import assert_finalizable, required_generation_gates
from spict4all.reviews import validate_human_reviews


def _review(unit_id: str, **overrides: str) -> dict[str, str]:
    row = {
        "unit_id": unit_id,
        "clinical_reviewer": "Clinical reviewer",
        "language_reviewer": "Language reviewer",
        "methodology_reviewer": "Methodology reviewer",
        "decision": "APPROVED",
        "approved_fi": "approved text",
        "issues_remaining": "",
        "date": "2026-09-07",
    }
    row.update(overrides)
    return row


def test_complete_human_review_passes(make_unit) -> None:
    unit = make_unit()
    assert validate_human_reviews([_review(unit["unit_id"])], [unit])


def test_pending_authority_is_valid_for_unresolved_requirement() -> None:
    source = EvidenceSource(
        evidence_id="S4A-REQ-2026-001",
        source_kind=EvidenceSourceKind.OFFICIAL_CHANGE_REQUIREMENT,
        exact_source_text_en="Exact source fixture",
        source_text_sha256="0" * 64,
        source_provenance=EvidenceProvenance(
            source_role="official_change_spec",
            document_part="word/document.xml",
            location=(("paragraph_index", 0),),
        ),
        requires_translation_evidence=True,
        requires_human_signoff=True,
        final_inclusion_status=FinalInclusionStatus.UNRESOLVED,
        eligible_for_document_insertion=False,
    )
    review = _review(
        source.evidence_id,
        decision="PENDING_AUTHORITY",
        approved_fi="",
    )
    assert validate_human_reviews([review], [source])
    with pytest.raises(ArtifactValidationError, match="pending authority blocks release"):
        validate_human_reviews([review], [source], require_release_ready=True)


def test_missing_required_human_disposition_fails(make_unit) -> None:
    unit = make_unit()
    with pytest.raises(ArtifactValidationError, match="missing required human disposition"):
        validate_human_reviews([_review(unit["unit_id"], decision="PENDING")], [unit])


def test_missing_human_review_unit_fails(make_unit) -> None:
    with pytest.raises(ArtifactValidationError, match="missing human review"):
        validate_human_reviews([], [make_unit()])


def test_unresolved_human_review_issue_fails(make_unit) -> None:
    unit = make_unit()
    with pytest.raises(ArtifactValidationError, match="unresolved issues"):
        validate_human_reviews(
            [_review(unit["unit_id"], issues_remaining="clinical issue")], [unit]
        )


def test_revised_review_requires_approved_text(make_unit) -> None:
    unit = make_unit()
    with pytest.raises(ArtifactValidationError, match="requires approved_fi"):
        validate_human_reviews(
            [_review(unit["unit_id"], decision="REVISED", approved_fi="")], [unit]
        )


def test_rejected_review_blocks_release(make_unit) -> None:
    unit = make_unit()
    with pytest.raises(ArtifactValidationError, match="rejected disposition blocks release"):
        validate_human_reviews(
            [_review(unit["unit_id"], decision="REJECTED", approved_fi="")],
            [unit],
            require_release_ready=True,
        )


@pytest.mark.parametrize("reverse_order", [False, True])
def test_multirow_review_validation_is_per_unit_and_order_independent(
    make_unit,
    reverse_order: bool,
) -> None:
    units = [make_unit(0), make_unit(1)]
    deficient = _review(
        units[0]["unit_id"],
        clinical_reviewer="",
        language_reviewer="",
        methodology_reviewer="",
        approved_fi="",
        issues_remaining="serious clinical issue",
    )
    reviews = [deficient, _review(units[1]["unit_id"])]
    if reverse_order:
        reviews.reverse()
    with pytest.raises(ArtifactValidationError) as error:
        validate_human_reviews(reviews, units)
    message = str(error.value)
    assert f"{units[0]['unit_id']}: missing clinical_reviewer" in message
    assert f"{units[0]['unit_id']}: missing language_reviewer" in message
    assert f"{units[0]['unit_id']}: missing methodology_reviewer" in message
    assert f"{units[0]['unit_id']}: APPROVED requires approved_fi" in message
    assert f"{units[0]['unit_id']}: unresolved issues block release" in message


def test_quality_gate_config_requires_g0_through_g5() -> None:
    root = Path(__file__).resolve().parents[1]
    assert required_generation_gates(root / "config/quality_gates.yaml") == (
        "G0_source_integrity",
        "T0_terminology_evidence_ready",
        "G1_independent_forward_translation",
        "G2_synthesis",
        "G3_blind_back_translation",
        "G4_automated_and_agent_critique",
        "G5_human_review",
    )


def test_attempt_to_mark_draft_final_fails() -> None:
    with pytest.raises(GateError, match="still a draft"):
        assert_finalizable("DRAFT", {"G0": "PASS"}, ("G0",))


def test_attempt_to_mark_final_with_missing_gate_fails() -> None:
    with pytest.raises(GateError, match="G1"):
        assert_finalizable("FINAL", {"G0": "PASS", "G1": "FAIL"}, ("G0", "G1"))


def test_final_with_all_required_gates_passes() -> None:
    assert_finalizable("FINAL", {"G0": "PASS", "G1": "PASS"}, ("G0", "G1"))


def test_final_cli_reports_source_authority_before_missing_review_files(
    tmp_path: Path, capsys
) -> None:
    root = Path(__file__).resolve().parents[1]
    exit_code = main(
        [
            "--root",
            str(root),
            "check-final",
            "--status",
            "FINAL",
            "--gate-results",
            str(tmp_path / "missing-gates.json"),
            "--review",
            str(tmp_path / "missing-review.tsv"),
        ]
    )
    assert exit_code == 1
    assert "Publication is blocked by unresolved source authority" in capsys.readouterr().err
