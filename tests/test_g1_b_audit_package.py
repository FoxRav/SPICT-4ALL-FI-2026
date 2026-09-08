from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from spict4all.hashing import sha256_text

ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts/verify_g1_b_audit_package.py"
SPEC = importlib.util.spec_from_file_location("verify_g1_b_audit_package", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load scripts/verify_g1_b_audit_package.py")
verify_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_mod)


def test_independence_allows_agent_b_and_placeholders() -> None:
    names = [
        "work/agent-b/candidates.jsonl",
        "work/agent-a/.gitkeep",
        "work/synthesis/.gitkeep",
        "work/backtranslation/.gitkeep",
        "work/critics/.gitkeep",
    ]
    assert verify_mod.independence_failures(names) == []


def test_independence_rejects_agent_a_candidates() -> None:
    names = [
        "work/agent-a/.gitkeep",
        "work/agent-a/candidates.jsonl",
        "work/synthesis/.gitkeep",
        "work/backtranslation/.gitkeep",
        "work/critics/.gitkeep",
    ]
    failures = verify_mod.independence_failures(names)
    assert any("later-gate artifact" in item for item in failures)


def test_independence_rejects_sibling_worktree_marker() -> None:
    reason = verify_mod.forbidden_member_reason("notes/120.SPICT-G1-A/candidates.jsonl")
    assert reason is not None
    assert "sibling" in reason or "Agent A" in reason


def _unit(unit_id: str, text: str) -> dict[str, Any]:
    return {
        "unit_id": unit_id,
        "source_text_en": text,
        "source_text_sha256": sha256_text(text),
    }


def _requirement() -> dict[str, Any]:
    text = "A liver transplant is not possible."
    return {
        "requirement_id": "S4A-REQ-2026-001",
        "exact_source_text_en": text,
        "exact_text_sha256": sha256_text(text),
        "translation_evidence_required": True,
        "canonical_source_presence": False,
        "final_inclusion_status": "UNRESOLVED",
        "publication_blocking": True,
    }


def _candidate(
    unit_id: str,
    text: str,
    finnish: str,
    *,
    kind: str = "canonical_source_unit",
    status: str = "READY_FOR_SYNTHESIS",
    inclusion: str = "CANONICAL",
    insertable: bool = True,
    sha: str | None = None,
) -> dict[str, Any]:
    return {
        "unit_id": unit_id,
        "source_text_sha256": sha or sha256_text(text),
        "model": "Cursor Grok 4.6",
        "candidate_fi": finnish,
        "status": status,
        "issues": [],
        "extensions": {
            "g1_forward": {
                "exact_source_text_en": text,
                "source_kind": kind,
                "source_location": {"paragraph_index": 0},
                "final_inclusion_status": inclusion,
                "eligible_for_document_insertion": insertable,
            }
        },
    }


def test_candidate_evidence_rejects_blank_finnish() -> None:
    text = "Cancer"
    units = [_unit("S4A-2026-011", text)]
    candidates = [_candidate("S4A-2026-011", text, "   ")]
    failures = verify_mod.candidate_evidence_failures(candidates, units, [_requirement()])
    assert any("blank Finnish" in item for item in failures)


def test_candidate_evidence_rejects_human_approved_state() -> None:
    text = "Cancer"
    units = [_unit("S4A-2026-011", text)]
    candidates = [
        _candidate("S4A-2026-011", text, "Syöpä", status="HUMAN_APPROVED"),
        _candidate(
            "S4A-REQ-2026-001",
            "A liver transplant is not possible.",
            "Maksansiirto ei ole mahdollinen.",
            kind="official_change_requirement",
            inclusion="UNRESOLVED",
            insertable=False,
        ),
        _candidate(
            "S4A-2026-000",
            "Supportive and Palliative Care Indicators Tool (SPICT-4ALL-……)",
            "otsikko",
            inclusion="UNRESOLVED",
            insertable=False,
        ),
    ]
    failures = verify_mod.candidate_evidence_failures(candidates, units, [_requirement()])
    assert any("unsupported approval state" in item for item in failures)


def test_sealed_translation_hashes_match_repository_bytes() -> None:
    for relative, expected in verify_mod.TRANSLATION_HASHES.items():
        actual = verify_mod.sha256_bytes((ROOT / relative).read_bytes())
        assert actual == expected


def test_delivery_zip_verifies_when_present() -> None:
    path = ROOT / "deliverables/audit" / verify_mod.NAME
    if not path.exists():
        pytest.skip("G1-B audit ZIP has not been sealed yet")
    result = verify_mod.verify(path)
    assert result["crc"] == "PASS"
    assert result["actual_model"] == "Cursor Grok 4.6"
    assert result["translation_evidence_unchanged"] is True
    assert result["human_approval_present"] is False
