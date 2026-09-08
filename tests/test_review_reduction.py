import json
import shutil
from pathlib import Path

import pytest

from spict4all.adjudication import BASE, read_tsv, tsv_text
from spict4all.errors import IntegrityError
from spict4all.human_terminology_decisions import BINDINGS, HUMAN_FILE
from spict4all.review_reduction import (
    QUEUE,
    assessment,
    minimal_table,
    validate_reduction,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch(tmp_path):
    for name in ("sources", "data", "config", "terminology", "docs", "work"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copyfile(ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    return tmp_path


def test_complete_reduction_counts_and_human_attribution():
    result = validate_reduction(ROOT)
    assert result["original_concepts"] == 29
    assert result["previous_sami_count"] == 21
    assert result["final_sami_count"] == 3
    table = read_tsv(ROOT / HUMAN_FILE)
    accepted = {r[0]: r for r in table[1:] if r[1]}
    assert set(accepted) == set(BINDINGS)
    for identifier, (_, term, maker) in BINDINGS.items():
        assert accepted[identifier][1:3] == ["ACCEPT", term]
        assert accepted[identifier][4:] == [maker, ""]


def test_all_retained_have_material_difference_and_no_decided_items():
    rows = assessment(ROOT)["decisions"]
    retained = [r for r in rows if r["category"] == "SAMI"]
    assert {r["decision_id"] for r in retained} == {"T-003", "T-018", "T-027"}
    assert all(r["material_meaning_difference"] and r["question"] for r in retained)
    assert not set(BINDINGS) & {r["decision_id"] for r in retained}


def test_unbound_phrase_decisions_not_promoted_to_broader_ids():
    table = read_tsv(ROOT / HUMAN_FILE)
    for row in table[1:]:
        if row[0] in {"T-014", "T-017", "T-009"}:
            assert all(value == "" for value in row[1:])
    a = assessment(ROOT)
    assert len(a["explicit_human_decisions_without_exact_decision_id"]) == 3
    assert a["frailty_final_term"] is None


@pytest.mark.parametrize("identifier,column,value", [
    ("T-002", 2, "invented alternative"), ("T-013", 4, "AI"),
    ("T-016", 5, "2019-01-01"), ("T-009", 2, "gerastenia"),
    ("T-017", 1, "ACCEPT"), ("T-014", 2, "ei ole riittävän hyväkuntoinen syöpähoitoon"),
])
def test_only_exact_authorized_human_cells_can_change(scratch, identifier, column, value):
    path = scratch / HUMAN_FILE
    table = read_tsv(path)
    next(r for r in table[1:] if r[0] == identifier)[column] = value
    path.write_text(tsv_text(table), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Human decisions"):
        validate_reduction(scratch)


def test_material_reason_cannot_be_removed(scratch):
    path = scratch / BASE / "T1_2_reclassification.json"
    a = json.loads(path.read_text(encoding="utf-8"))
    a["decisions"][2]["material_meaning_difference"] = ""
    path.write_text(json.dumps(a), encoding="utf-8")
    with pytest.raises(IntegrityError, match="classification"):
        validate_reduction(scratch)


def test_no_human_decisions_in_minimal_queue(scratch):
    path = scratch / BASE / QUEUE
    table = read_tsv(path)
    if len(table) == 1:
        table.append(minimal_table(scratch)[1])
    table[1][-2] = "ACCEPT"
    path.write_text(tsv_text(table), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Minimal Sami queue"):
        validate_reduction(scratch)


def test_old_evidence_is_immutable(scratch):
    path = scratch / BASE / "enrichment/TERM-SRC-006-terveyskirjasto-evidence.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="protected artifact"):
        validate_reduction(scratch)
