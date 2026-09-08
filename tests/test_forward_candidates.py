from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from spict4all.errors import ArtifactValidationError, CoverageError
from spict4all.evidence import (
    EvidenceProvenance,
    EvidenceSource,
    EvidenceSourceKind,
    FinalInclusionStatus,
)
from spict4all.forward_candidates import (
    build_forward_candidate_records,
    validate_forward_candidates,
)
from spict4all.g1_b_correction import FROZEN_G1_B_001_HASHES, G1_B_002_RUN_ID
from spict4all.g1_forward_runner import build_run, validate_run
from spict4all.hashing import sha256_file, sha256_text

ROOT = Path(__file__).resolve().parents[1]
AGENT_B_002_DIR = ROOT / "work/agent-b/runs" / G1_B_002_RUN_ID
AGENT_B_AUTHORED = AGENT_B_002_DIR / "agent_b_translations.json"
AGENT_B_CANDIDATES = AGENT_B_002_DIR / "candidates.jsonl"

RUN = {
    "run_id": "TEST-FORWARD-001",
    "translator_role": "forward_translation_B",
    "translator_identity": "test translator B",
    "model": "test-model",
    "prompt_version": "prompts/02-agent-b-forward.md",
    "run_timestamp_utc": "2026-09-08T00:00:00Z",
}


def _source(
    evidence_id: str,
    text: str,
    *,
    kind: EvidenceSourceKind = EvidenceSourceKind.CANONICAL_SOURCE_UNIT,
    status: FinalInclusionStatus = FinalInclusionStatus.CANONICAL,
    insertable: bool = True,
) -> EvidenceSource:
    return EvidenceSource(
        evidence_id=evidence_id,
        source_kind=kind,
        exact_source_text_en=text,
        source_text_sha256=sha256_text(text),
        source_provenance=EvidenceProvenance(
            source_role="canonical_source",
            document_part="word/document.xml",
            location=(("paragraph_index", 0),),
        ),
        requires_translation_evidence=True,
        requires_human_signoff=True,
        final_inclusion_status=status,
        eligible_for_document_insertion=insertable,
    )


def _authored(candidate_fi: str, **overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "candidate_fi": candidate_fi,
        "decision_note": "Test note.",
        "issues": [],
        "human_terminology_decisions_applied": [],
        "untranslated_verbatim": False,
    }
    entry.update(overrides)
    return entry


def test_happy_path_builds_and_validates_matching_candidate() -> None:
    source = _source("S4A-2026-011", "Cancer")
    records = build_forward_candidate_records(
        [source],
        RUN,
        {"S4A-2026-011": _authored("Syöpä")},
    )
    report = validate_forward_candidates(
        [source], records, expected_translator_role="forward_translation_B"
    )
    assert report.expected_source_count == 1
    assert report.candidate_count == 1
    assert records[0]["source_text_sha256"] == source.source_text_sha256
    assert records[0]["extensions"]["g1_forward"]["exact_source_text_en"] == "Cancer"


def test_blank_candidate_fails() -> None:
    source = _source("S4A-2026-011", "Cancer")
    records = build_forward_candidate_records(
        [source],
        RUN,
        {"S4A-2026-011": _authored("   ")},
    )
    with pytest.raises(ArtifactValidationError, match="candidate_fi is blank"):
        validate_forward_candidates(
            [source], records, expected_translator_role="forward_translation_B"
        )


def test_missing_negation_marker_fails() -> None:
    source = _source("S4A-2026-016", "Kidneys are not working well.")
    records = build_forward_candidate_records(
        [source],
        RUN,
        {"S4A-2026-016": _authored("Munuaiset toimivat huonosti.")},
    )
    with pytest.raises(ArtifactValidationError, match="negation"):
        validate_forward_candidates(
            [source], records, expected_translator_role="forward_translation_B"
        )


def test_missing_inclusive_alternative_fails() -> None:
    source = _source(
        "S4A-2026-005",
        "Needs more help due to physical and/or mental health problems.",
    )
    records = build_forward_candidate_records(
        [source],
        RUN,
        {
            "S4A-2026-005": _authored(
                "Tarvitsee enemmän apua ruumiillisten tai mielenterveyden ongelmien vuoksi."
            )
        },
    )
    with pytest.raises(ArtifactValidationError, match="inclusive_alternative"):
        validate_forward_candidates(
            [source], records, expected_translator_role="forward_translation_B"
        )


def test_unresolved_requirement_without_blocker_fails() -> None:
    source = _source(
        "S4A-REQ-2026-001",
        "A liver transplant is not possible.",
        kind=EvidenceSourceKind.OFFICIAL_CHANGE_REQUIREMENT,
        status=FinalInclusionStatus.UNRESOLVED,
        insertable=False,
    )
    records = build_forward_candidate_records(
        [source],
        RUN,
        {
            "S4A-REQ-2026-001": _authored(
                "Maksansiirto ei ole mahdollinen.",
                issues=[],
            )
        },
    )
    with pytest.raises(ArtifactValidationError, match="unresolved_source_authority"):
        validate_forward_candidates(
            [source], records, expected_translator_role="forward_translation_B"
        )


def test_authored_extra_source_fails() -> None:
    source = _source("S4A-2026-011", "Cancer")
    with pytest.raises(ArtifactValidationError, match="unknown sources"):
        build_forward_candidate_records(
            [source],
            RUN,
            {
                "S4A-2026-011": _authored("Syöpä"),
                "S4A-2026-999": _authored("extra"),
            },
        )


def test_authored_missing_source_fails() -> None:
    sources = [
        _source("S4A-2026-011", "Cancer"),
        _source("S4A-2026-013", "Kidney problems"),
    ]
    with pytest.raises(ArtifactValidationError, match="missing for sources"):
        build_forward_candidate_records(
            sources,
            RUN,
            {"S4A-2026-011": _authored("Syöpä")},
        )


def test_coverage_rejects_invented_unit() -> None:
    with pytest.raises(CoverageError, match="S4A-2026-999"):
        validate_forward_candidates(
            [_source("S4A-2026-011", "Cancer")],
            [
                {
                    "unit_id": "S4A-2026-011",
                    "source_text_sha256": sha256_text("Cancer"),
                    "model": "test-model",
                    "candidate_fi": "Syöpä",
                    "decision_note": "ok",
                    "issues": [],
                    "status": "READY_FOR_SYNTHESIS",
                    "extensions": {
                        "g1_forward": {
                            "exact_source_text_en": "Cancer",
                            "source_kind": "canonical_source_unit",
                            "source_role": "canonical_source",
                            "document_part": "word/document.xml",
                            "source_location": {"paragraph_index": 0},
                            "final_inclusion_status": "CANONICAL",
                            "eligible_for_document_insertion": True,
                            "translator_role": "forward_translation_B",
                            "translator_identity": "test",
                            "run_id": "x",
                            "run_timestamp_utc": "2026-09-08T00:00:00Z",
                            "run_prompt_version": "p",
                            "human_terminology_decisions_applied": [],
                            "untranslated_verbatim": False,
                        }
                    },
                },
                {
                    "unit_id": "S4A-2026-999",
                    "source_text_sha256": sha256_text("extra"),
                    "model": "test-model",
                    "candidate_fi": "lisä",
                    "decision_note": "ok",
                    "issues": [],
                    "status": "READY_FOR_SYNTHESIS",
                    "extensions": {
                        "g1_forward": {
                            "exact_source_text_en": "extra",
                            "source_kind": "canonical_source_unit",
                            "source_role": "canonical_source",
                            "document_part": "word/document.xml",
                            "source_location": {"paragraph_index": 0},
                            "final_inclusion_status": "CANONICAL",
                            "eligible_for_document_insertion": True,
                            "translator_role": "forward_translation_B",
                            "translator_identity": "test",
                            "run_id": "x",
                            "run_timestamp_utc": "2026-09-08T00:00:00Z",
                            "run_prompt_version": "p",
                            "human_terminology_decisions_applied": [],
                            "untranslated_verbatim": False,
                        }
                    },
                },
            ],
            expected_translator_role="forward_translation_B",
        )


def test_agent_b_authored_translations_cover_frozen_universe(tmp_path: Path) -> None:
    destination = tmp_path / "candidates.jsonl"
    records = build_run(ROOT, AGENT_B_AUTHORED, destination)
    report = validate_run(
        ROOT, destination, translator_role="forward_translation_B"
    )
    assert len(records) == 54
    assert report["expected_source_count"] == 54
    assert report["candidate_count"] == 54
    assert report["canonical_count"] == 53
    assert report["source_requirement_count"] == 1
    assert report["unresolved_authority_count"] == 2
    assert report["schema_valid"] is True
    assert report["coverage_complete"] is True
    assert report["human_terminology_decisions_applied"] == {
        "S4A-2026-001": ["T-002"],
        "S4A-2026-035": ["T-013"],
        "S4A-2026-042": ["T-002"],
        "S4A-2026-049": ["T-016"],
    }


def test_frozen_g1_b_001_hashes_unchanged() -> None:
    for relative, expected in FROZEN_G1_B_001_HASHES.items():
        assert sha256_file(ROOT / relative) == expected


def test_project_owner_less_well_wording_missing_fails() -> None:
    source = _source(
        "S4A-2026-001",
        "The SPICT helps us look for people who have life shortening health conditions and are less well.",
    )
    records = build_forward_candidate_records(
        [source],
        RUN,
        {
            "S4A-2026-001": _authored(
                "SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä terveydentiloja ja jotka voivat huonommin.",
                human_terminology_decisions_applied=["T-002"],
            )
        },
    )
    with pytest.raises(ArtifactValidationError, match="Project Owner wording"):
        validate_forward_candidates(
            [source], records, expected_translator_role="forward_translation_B"
        )


def test_agent_b_repository_artifact_validates() -> None:
    report = validate_run(
        ROOT,
        AGENT_B_CANDIDATES,
        translator_role="forward_translation_B",
    )
    assert report["artifact"] == f"work/agent-b/runs/{G1_B_002_RUN_ID}/candidates.jsonl"
    assert report["candidate_count"] == 54
    assert report["canonical_count"] == 53
    assert report["source_requirement_count"] == 1
