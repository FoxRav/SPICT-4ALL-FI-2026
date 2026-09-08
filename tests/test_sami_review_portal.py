from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("portal_validator", ROOT / "scripts/validate_sami_review_portal.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_portal_integrity() -> None:
    MODULE.validate()


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "hash", "source", "candidate", "extra"])
def test_portal_rejects_changed_data(tmp_path: Path, mutation: str) -> None:
    from build_sami_review_portal import DATA_PATH, artifacts

    for relative, content in artifacts().items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    path = tmp_path / DATA_PATH
    rows = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[1] = rows[0]
    elif mutation == "hash":
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "source":
        rows[0]["source_text_en"] = "changed"
    elif mutation == "candidate":
        rows[0]["current_candidate_fi"] = "changed"
    else:
        rows[0]["critic_alternative"] = "not permitted"
    if mutation != "hash":
        path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match="mismatch"):
        MODULE.validate(tmp_path)


@pytest.mark.parametrize("target,old,new", [
    ("review-portal/README.md", "DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED", "omitted"),
    ("review-portal/PUBLICATION_STATUS.md", "DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED", "omitted"),
    (".github/workflows/pages-review.yml", "11bd71901bbe5b1630ceea73d27597364c9af683", "v4"),
    ("review-portal/worker/wrangler.toml", 'GITHUB_EVIDENCE_REPOSITORY = "FoxRav/SPICT-4ALL-FI-2026-review-evidence"', 'GITHUB_EVIDENCE_REPOSITORY = "public/repo"'),
    ("review-portal/worker/wrangler.toml", 'GITHUB_EVIDENCE_REPOSITORY = "FoxRav/SPICT-4ALL-FI-2026-review-evidence"', 'GITHUB_EVIDENCE_REPOSITORY = ""'),
    ("review-portal/worker/wrangler.toml", 'PUBLICATION_AUTHORIZED = "true"', 'PUBLICATION_AUTHORIZED = "false"'),
    ("review-portal/worker/wrangler.toml", 'workers_dev = true', 'workers_dev = false'),
    ("review-portal/worker/wrangler.toml", 'ALLOWED_ORIGIN = "https://foxrav.github.io"', 'ALLOWED_ORIGIN = "*"'),
    ("review-portal/site/review/sami/index.html", 'minlength="24"', 'minlength="1"'),
    ("review-portal/worker/wrangler.toml", '["GITHUB_TOKEN", "REVIEW_ACCESS_CODE"]', '["GITHUB_TOKEN"]'),
    ("review-portal/worker/wrangler.toml", '["GITHUB_TOKEN", "REVIEW_ACCESS_CODE"]', '["GITHUB_TOKEN", "REVIEW_ACCESS_CODE", "EXTRA"]'),
    (".gitignore", '.dev.vars\n', ''),
    (".gitignore", '.dev.vars.*', ''),
])
def test_activation_safety_regressions(tmp_path: Path, target: str, old: str, new: str) -> None:
    shutil.copytree(ROOT / "review-portal", tmp_path / "review-portal", ignore=shutil.ignore_patterns(".dev.vars", ".dev.vars.*"))
    shutil.copytree(ROOT / ".github", tmp_path / ".github")
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / target
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    with pytest.raises(AssertionError):
        MODULE.validate(tmp_path)


def test_force_tracked_local_secret_file_rejected_without_reading(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    (tmp_path / ".dev.vars").write_text("# Empty test fixture; no secret values\n")
    MODULE.validate_local_secrets(tmp_path)
    subprocess.run(["git", "add", "-f", ".dev.vars"], cwd=tmp_path, check=True)
    with pytest.raises(AssertionError, match="tracked"):
        MODULE.validate_local_secrets(tmp_path)
