from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from spict4all.adjudication import BASE, read_json, read_tsv, tsv_text
from spict4all.errors import IntegrityError
from spict4all.jsonl import load_jsonl
from spict4all.terminology_enrichment import (
    ENRICHMENT,
    EVIDENCE,
    QUEUE,
    valid_url,
    validate_enrichment,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch(tmp_path):
    for name in ("sources", "data", "config", "terminology", "docs", "work"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copyfile(ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    return tmp_path


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def mutate_evidence(root, callback):
    path = root / ENRICHMENT / EVIDENCE
    rows = load_jsonl(path)
    callback(rows)
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")


def test_enrichment_complete_and_unapproved():
    result = validate_enrichment(ROOT)
    assert result["concepts_searched"] == 29
    assert result["useful_evidence_records"] == 28
    assert result["no_sufficient_evidence_after"] == 11
    assert result["approved"] == 0


@pytest.mark.parametrize("url", [
    "https://www.terveyskirjasto.fi.evil.test/ltt00001",
    "https://evil.test/?url=https://www.terveyskirjasto.fi",
    "https://www.terveyskirjasto.fi@evil.test/a",
    "http://www.terveyskirjasto.fi/a",
    "https://user@www.terveyskirjasto.fi/a",
])
def test_domain_is_parsed_not_substring(url):
    assert not valid_url(url)


def test_external_evidence_url_rejected(scratch):
    mutate_evidence(scratch, lambda rows: rows[0]["source_evidence"].update(url="https://evil.test/"))
    with pytest.raises(IntegrityError, match="domain"):
        validate_enrichment(scratch)


def test_unknown_decision_rejected(scratch):
    mutate_evidence(scratch, lambda rows: rows[0].update(decision_id="T-999"))
    with pytest.raises(IntegrityError, match="decision reference"):
        validate_enrichment(scratch)


def test_duplicate_evidence_rejected(scratch):
    mutate_evidence(scratch, lambda rows: rows.append(rows[0]))
    with pytest.raises(IntegrityError, match="Duplicate"):
        validate_enrichment(scratch)


@pytest.mark.parametrize("field", ["human_decision", "human_decision_note", "decided_by", "decision_date"])
def test_updated_queue_cannot_populate_human_fields(scratch, field):
    path = scratch / ENRICHMENT / QUEUE
    table = read_tsv(path)
    table[1][table[0].index(field)] = "APPROVED"
    path.write_text(tsv_text(table), encoding="utf-8")
    with pytest.raises(IntegrityError, match="queue mismatch"):
        validate_enrichment(scratch)


def test_model_english_cannot_enter_source_fields(scratch):
    mutate_evidence(scratch, lambda rows: rows[0]["source_evidence"].update(term_en="palliative care"))
    with pytest.raises(IntegrityError, match="separation"):
        validate_enrichment(scratch)


def test_source_explicit_claim_for_model_mapping_rejected(scratch):
    mutate_evidence(scratch, lambda rows: rows[0]["model_interpretation"].update(relationship="SOURCE_EXPLICIT"))
    with pytest.raises(IntegrityError, match="separation"):
        validate_enrichment(scratch)


@pytest.mark.parametrize("change", [
    {"can_satisfy_spict_source_requirements": True},
    {"classification": "CANONICAL_SOURCE"},
    {"classification": "OFFICIAL_CHANGE_SPEC"},
    {"classification": "SPICT_AUTHORITY"},
])
def test_web_reference_cannot_satisfy_spict_authority(scratch, change):
    path = scratch / ENRICHMENT / "web_source_manifest.json"
    registry = read_json(path)
    registry.update(change)
    write_json(path, registry)
    with pytest.raises(IntegrityError, match="source authority"):
        validate_enrichment(scratch)


@pytest.mark.parametrize("relative", [
    f"{BASE}/TERMINOLOGY_ADJUDICATION_QUEUE.tsv", "data/source_units.jsonl",
    "data/source_requirements.jsonl", "terminology/terms.csv",
])
def test_original_inputs_cannot_change(scratch, relative):
    with (scratch / relative).open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(IntegrityError, match="protected input"):
        validate_enrichment(scratch)


def test_translation_work_cannot_be_added(scratch):
    (scratch / "work/candidate-fi.jsonl").write_text('{}\n', encoding="utf-8")
    with pytest.raises(IntegrityError, match="translation work"):
        validate_enrichment(scratch)


def test_quote_hash_tampering_rejected(scratch):
    mutate_evidence(scratch, lambda rows: rows[0]["source_evidence"].update(fragment="invented"))
    with pytest.raises(IntegrityError, match="fragment/hash"):
        validate_enrichment(scratch)


def test_approval_cannot_enter_model_plan(scratch):
    path = scratch / ENRICHMENT / "model_interpretations.json"
    plan = read_json(path)
    plan["approved"] = 1
    write_json(path, plan)
    with pytest.raises(IntegrityError, match="approval"):
        validate_enrichment(scratch)


def test_human_review_cannot_preselect_decision(scratch):
    path = scratch / ENRICHMENT / "TERMINOLOGY_HUMAN_REVIEW_T1_1.md"
    path.write_text(path.read_text(encoding="utf-8").replace("- [ ]", "- [x]", 1), encoding="utf-8")
    with pytest.raises(IntegrityError, match="preselected"):
        validate_enrichment(scratch)


def test_missing_search_for_concept_rejected(scratch):
    path = scratch / ENRICHMENT / "search_receipts.jsonl"
    rows = [x for x in load_jsonl(path) if x["decision_id"] != "T-003"]
    path.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
    with pytest.raises(IntegrityError, match="targeted search"):
        validate_enrichment(scratch)
