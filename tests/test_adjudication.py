from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from spict4all.adjudication import (
    BASE,
    HUMAN_FIELDS,
    build_tables,
    read_json,
    read_tsv,
    tsv_text,
    validate_package,
    validate_plan,
)
from spict4all.errors import IntegrityError

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def plan():
    return copy.deepcopy(read_json(ROOT / BASE / "model_mapping_plan.json"))


@pytest.fixture
def scratch(tmp_path):
    for directory in ("sources", "data", "config", "terminology", "docs", "work"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copyfile(ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    return tmp_path


def test_complete_t1_package_is_unapproved_and_source_linked():
    result = validate_package(ROOT)
    assert result["concepts"] == 29
    assert result["approved"] == 0
    assert result["candidate_origins"]["SOURCE_EXPLICIT"] == 0
    assert result["relevant_conflicts"] == 3


@pytest.mark.parametrize("field", HUMAN_FIELDS[1:])
def test_human_decision_template_fields_must_be_blank(scratch, field):
    path = scratch / BASE / "human_terminology_decisions.tsv"
    table = read_tsv(path)
    table[1][table[0].index(field)] = "fixture"
    path.write_text(tsv_text(table), encoding="utf-8")
    with pytest.raises(IntegrityError, match="blank decision mismatch"):
        validate_package(scratch)


@pytest.mark.parametrize("field", ["human_decision", "human_decision_note", "decided_by", "decision_date"])
def test_plan_cannot_smuggle_human_decisions(plan, field):
    plan["decisions"][0][field] = " "
    with pytest.raises(IntegrityError, match="human fields must be blank"):
        validate_plan(ROOT, plan)


def test_approved_status_cannot_enter_preparation(plan):
    plan["decisions"][0]["status"] = "APPROVED"
    with pytest.raises(IntegrityError, match="APPROVED"):
        validate_plan(ROOT, plan)


def test_unknown_terminology_reference_fails(plan):
    plan["decisions"][0]["terminology_evidence_ids"].append("TERM-EVID-NOT-REAL")
    with pytest.raises(IntegrityError, match="evidence reference"):
        validate_plan(ROOT, plan)


def test_unknown_source_unit_fails(plan):
    plan["decisions"][0]["source_unit_ids"].append("S4A-2026-999")
    with pytest.raises(IntegrityError, match="source_unit_id"):
        validate_plan(ROOT, plan)


def test_origin_must_be_explicit(plan):
    plan["decisions"][0]["candidate_origin"] = "INFERRED_BUT_APPROVED"
    with pytest.raises(IntegrityError, match="origin must be explicit"):
        validate_plan(ROOT, plan)


@pytest.mark.parametrize("decision", [0, 3, 21])
def test_finnish_or_different_english_label_cannot_be_source_explicit(plan, decision):
    plan["decisions"][decision]["candidate_origin"] = "SOURCE_EXPLICIT"
    with pytest.raises(IntegrityError, match="inferred English equivalent"):
        validate_plan(ROOT, plan)


def test_no_evidence_cannot_have_model_guess(plan):
    plan["decisions"][5]["candidate_fi"] = "fixture"
    with pytest.raises(IntegrityError, match="must not invent"):
        validate_plan(ROOT, plan)


def test_all_existing_conflicts_must_be_accounted_for(plan):
    plan["conflict_review"].pop()
    with pytest.raises(IntegrityError, match="all existing conflicts"):
        validate_plan(ROOT, plan)


def test_conflict_cannot_be_resolved_by_model(plan):
    plan["conflict_review"][0]["resolution"] = "resolved"
    with pytest.raises(IntegrityError, match="must not be resolved"):
        validate_plan(ROOT, plan)


def test_both_conflict_source_records_must_be_present(plan):
    plan["decisions"][22]["terminology_evidence_ids"].remove("TERM-EVID-005-ROW-0026")
    with pytest.raises(IntegrityError, match="conflict evidence sides"):
        validate_plan(ROOT, plan)


def test_conflict_cannot_disappear_through_relevance_relabelling(plan):
    plan["conflict_review"][0]["relevance"] = "NOT_INCLUDED"
    with pytest.raises(IntegrityError, match="relevance and queue disagree"):
        validate_plan(ROOT, plan)


def test_source_context_is_exact_and_hashes_retained(plan):
    tables = build_tables(ROOT, plan)
    records = tables["TERMINOLOGY_ADJUDICATION_QUEUE.tsv"]
    assert "A liver transplant is not possible." == records[11][2]
    assert records[11][3] == "S4A-REQ-2026-001"
    assert records[11][6] == ""


def test_tampered_source_quote_fails(scratch):
    path = scratch / BASE / "TERMINOLOGY_ADJUDICATION_QUEUE.tsv"
    table = read_tsv(path)
    table[1][2] = "fabricated context"
    path.write_text(tsv_text(table), encoding="utf-8")
    with pytest.raises(IntegrityError, match="source context"):
        validate_package(scratch)


def test_evidence_cannot_be_relabelled_as_bilingual(scratch):
    path = scratch / BASE / "terminology_adjudication_evidence.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["source_provided_evidence"]["term_en_origin"] = "SOURCE_EXPLICIT"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(IntegrityError, match="exact evidence"):
        validate_package(scratch)


def test_terminology_preparation_cannot_change_canonical_input(scratch):
    path = scratch / "data/source_units.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="protected input changed"):
        validate_package(scratch)


def test_t1_cannot_create_translation_artifacts(scratch):
    (scratch / "work/agent-a").mkdir(exist_ok=True)
    (scratch / "work/agent-a/candidates.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="must not create translation"):
        validate_package(scratch)


def test_human_review_choices_are_not_prechecked(scratch):
    path = scratch / BASE / "TERMINOLOGY_HUMAN_REVIEW.md"
    path.write_text(path.read_text(encoding="utf-8").replace("[ ] ACCEPT", "[x] ACCEPT", 1), encoding="utf-8")
    with pytest.raises(IntegrityError, match="unselected choices"):
        validate_package(scratch)
