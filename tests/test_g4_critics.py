from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from spict4all.g4_critics import (
    COMBINED_RELATIVE,
    CRITIC_A_ACTUAL_MODEL,
    CRITIC_A_RELATIVE,
    CRITIC_B_ACTUAL_MODEL,
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
    FRAILTY_ID,
    G2_CANDIDATES_RELATIVE,
    G3_BACK_RELATIVE,
    G4_RUN_DIR,
    G4_RUN_ID,
    HUMAN_DECISION_CONFLICTS,
    REQUIREMENT_ID,
    REVIEW_INPUT_RELATIVE,
    TITLE_ID,
    build_combined_findings,
    encode_combined_row,
    g4_run_failures,
    issue_ids,
    medium_plus_units,
    severity_counts,
    status_groups,
)
from spict4all.hashing import sha256_file
from spict4all.jsonl import load_jsonl

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / G4_RUN_DIR
VERIFY_PATH = ROOT / "scripts/verify_g4_critics_audit.py"
README = ROOT / "README.md"


def test_frozen_g4_input_hashes() -> None:
    for relative, expected in EXPECTED_HASHES.items():
        assert sha256_file(ROOT / relative) == expected


def test_critic_coverage_and_raw_severity() -> None:
    critic_a = load_jsonl(ROOT / CRITIC_A_RELATIVE)
    critic_b = load_jsonl(ROOT / CRITIC_B_RELATIVE)
    review = load_jsonl(ROOT / REVIEW_INPUT_RELATIVE)
    assert len(review) == EXPECTED_COUNT
    assert len(critic_a) == EXPECTED_COUNT
    assert len(critic_b) == EXPECTED_COUNT
    ids = [row["unit_id"] for row in review]
    assert ids == [row["unit_id"] for row in critic_a]
    assert ids == [row["unit_id"] for row in critic_b]
    assert len(set(ids)) == EXPECTED_COUNT
    assert severity_counts(critic_a) == EXPECTED_A_SEVERITY
    assert severity_counts(critic_b) == EXPECTED_B_SEVERITY
    assert len(issue_ids(critic_a)) == EXPECTED_A_ISSUE
    assert len(issue_ids(critic_b)) == EXPECTED_B_ISSUE
    assert tuple(issue_ids(critic_a)) == EXPECTED_CORROBORATED


def test_cross_critic_corroboration_without_adjudication() -> None:
    combined = build_combined_findings(
        load_jsonl(ROOT / REVIEW_INPUT_RELATIVE),
        load_jsonl(ROOT / CRITIC_A_RELATIVE),
        load_jsonl(ROOT / CRITIC_B_RELATIVE),
        load_jsonl(ROOT / G2_CANDIDATES_RELATIVE),
        load_jsonl(ROOT / G3_BACK_RELATIVE),
    )
    groups = status_groups(combined)
    assert tuple(groups["CORROBORATED"]) == EXPECTED_CORROBORATED
    assert groups["CRITIC_A_ONLY"] == []
    assert tuple(groups["CRITIC_B_ONLY"]) == EXPECTED_B_ONLY
    b_only_medium = [
        row["unit_id"]
        for row in combined
        if row["finding_status"] == "CRITIC_B_ONLY" and row["critic_b_severity"] == "MEDIUM"
    ]
    assert tuple(b_only_medium) == EXPECTED_B_ONLY_MEDIUM
    row_025 = next(row for row in combined if row["unit_id"] == "S4A-2026-025")
    row_045 = next(row for row in combined if row["unit_id"] == "S4A-2026-045")
    assert row_025["critic_a_severity"] == "HIGH"
    assert row_025["critic_b_severity"] == "HIGH"
    assert row_045["critic_a_severity"] == "BLOCKER"
    assert row_045["critic_b_severity"] == "HIGH"
    assert row_045["combined_review_priority"] == "BLOCKER"
    assert {row["unit_id"] for row in combined if row["human_decision_conflict"]} == set(
        HUMAN_DECISION_CONFLICTS
    )
    frailty = next(row for row in combined if row["unit_id"] == FRAILTY_ID)
    assert frailty["frailty_human_wording_status"] == (
        "NO_FINAL_RECORDED_HUMAN_WORDING_DECISION"
    )
    assert frailty["human_decision_conflict"] == ""
    title = next(row for row in combined if row["unit_id"] == TITLE_ID)
    requirement = next(row for row in combined if row["unit_id"] == REQUIREMENT_ID)
    assert title["source_authority_status"] == "UNRESOLVED"
    assert title["source_authority_publication_blocking"] is True
    assert requirement["source_authority_status"] == "NONCANONICAL"
    assert requirement["source_authority_publication_blocking"] is True
    assert title["combined_review_priority"] != "BLOCKER"
    assert "S4A-2026-008" in medium_plus_units(combined)


def test_g4_metadata_when_present() -> None:
    if not (RUN_DIR / "run_metadata.json").is_file():
        pytest.skip("G4 metadata has not been written yet")
    failures = g4_run_failures(ROOT)
    assert failures == []
    metadata = json.loads((RUN_DIR / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["run_id"] == G4_RUN_ID
    assert metadata["critic_a_actual_model"] == CRITIC_A_ACTUAL_MODEL
    assert metadata["critic_b_actual_model"] == CRITIC_B_ACTUAL_MODEL
    assert metadata["g5_created"] is False
    assert metadata["finnish_revised"] is False
    report = (RUN_DIR / "G4_REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert "54/54" in report
    assert "does not adjudicate" in report
    combined = load_jsonl(ROOT / COMBINED_RELATIVE)
    expected = build_combined_findings(
        load_jsonl(ROOT / REVIEW_INPUT_RELATIVE),
        load_jsonl(ROOT / CRITIC_A_RELATIVE),
        load_jsonl(ROOT / CRITIC_B_RELATIVE),
        load_jsonl(ROOT / G2_CANDIDATES_RELATIVE),
        load_jsonl(ROOT / G3_BACK_RELATIVE),
    )
    assert (RUN_DIR / "combined_findings.jsonl").read_text(encoding="utf-8") == "".join(
        encode_combined_row(row) for row in expected
    )
    assert [row["unit_id"] for row in combined] == [row["unit_id"] for row in expected]
    readme = README.read_text(encoding="utf-8")
    assert "| **G4** | Independent critics and adversarial review | **PASS** |" in readme
    assert "| **G5** | Human adjudication and final source reconciliation | **IN PROGRESS** |" in readme
    assert "G5 human adjudication is in progress" in readme
    assert "G4 PASS" not in readme


def test_frozen_wording_and_no_document_generation() -> None:
    assert sha256_file(ROOT / G2_CANDIDATES_RELATIVE) == EXPECTED_HASHES[G2_CANDIDATES_RELATIVE]
    assert sha256_file(ROOT / G3_BACK_RELATIVE) == EXPECTED_HASHES[G3_BACK_RELATIVE]
    assert sha256_file(ROOT / CRITIC_A_RELATIVE) == EXPECTED_HASHES[CRITIC_A_RELATIVE]
    assert sha256_file(ROOT / CRITIC_B_RELATIVE) == EXPECTED_HASHES[CRITIC_B_RELATIVE]
    later = []
    directory = ROOT / "work/final"
    if directory.is_dir():
        later.extend(
            path.relative_to(ROOT).as_posix()
            for path in directory.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
    assert later == []


def test_g4_audit_zip_verifies_when_present() -> None:
    if not VERIFY_PATH.is_file():
        pytest.skip("G4 audit verifier is not present yet")
    spec = importlib.util.spec_from_file_location("verify_g4_critics_audit", VERIFY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load G4 audit verifier")
    verify_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify_mod)
    path = ROOT / "deliverables/audit" / verify_mod.NAME
    if not path.exists():
        pytest.skip("G4 audit ZIP has not been sealed yet")
    result = verify_mod.verify(path)
    assert result["crc"] == "PASS"
    assert result["critic_a_actual_model"] == CRITIC_A_ACTUAL_MODEL
    assert result["critic_b_actual_model"] == CRITIC_B_ACTUAL_MODEL
    assert result["g5_created"] is False
    assert result["finnish_revised"] is False
    assert result["g4_pass_claimed"] is False
    assert result["nested_archives"] == 0
    assert result["member_hashes"].startswith("PASS")
    assert result["coverage"] == f"PASS ({EXPECTED_COUNT}/{EXPECTED_COUNT})"
    assert result["corroborated"] == 7
    assert result["critic_a_only"] == 0
    assert result["critic_b_only"] == 14
