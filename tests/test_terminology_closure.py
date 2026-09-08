import json
import shutil
from pathlib import Path

import pytest

from spict4all.adjudication import BASE, read_tsv
from spict4all.errors import IntegrityError
from spict4all.review_reduction import QUEUE
from spict4all.terminology_closure import validate_closure

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch(tmp_path):
    for name in ("sources", "data", "config", "terminology", "docs", "work"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copyfile(ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    return tmp_path


def test_closed_phase_has_no_active_items_and_preserves_history():
    result = validate_closure(ROOT)
    assert result["t1_status"] == "READY_FOR_G1"
    assert result["pre_g1_terminology_blockers"] == 0
    assert result["active_sami_review_count"] == 0
    assert result["g1_started"] is False
    assert len(read_tsv(ROOT / BASE / QUEUE)) == 1
    assert len(read_tsv(ROOT / BASE / "T1_3_SAMI_QUEUE_BEFORE_CLOSURE.tsv")) == 4


def test_reopening_queue_is_rejected(scratch):
    shutil.copyfile(scratch / BASE / "T1_3_SAMI_QUEUE_BEFORE_CLOSURE.tsv", scratch / BASE / QUEUE)
    with pytest.raises(IntegrityError, match="queue mismatch"):
        validate_closure(scratch)


@pytest.mark.parametrize("change", ["blocker", "frailty_wording", "approval", "start"])
def test_no_unsupported_disposition_or_approval(scratch, change):
    path = scratch / BASE / "T1_3_project_owner_disposition.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if change == "blocker":
        data["dispositions"][0]["mandatory_pre_g1"] = True
    elif change == "frailty_wording":
        data["dispositions"][3]["mandatory_finnish_term"] = "invented"
    elif change == "approval":
        data["glossary_entries_approved_by_this_work_package"] = 1
    else:
        data["g1_started"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(IntegrityError, match="disposition mismatch"):
        validate_closure(scratch)
