"""Check generated data, frozen evidence, and publication safety."""
from __future__ import annotations

import re
from pathlib import Path

from build_sami_review_portal import ROOT, artifacts


def validate(root: Path = ROOT) -> None:
    for relative, expected in artifacts().items():
        if (root / relative).read_bytes() != expected:
            raise ValueError(f"Generated artifact mismatch: {relative}")
    site = root / "review-portal/site/review/sami"
    html = (site / "index.html").read_text(encoding="utf-8")
    assert 'id="submit" type="submit" disabled' in html
    js = (site / "review.js").read_text(encoding="utf-8")
    for value in ("ACCEPT_CURRENT", "ACCEPT_WITH_EDIT", "NEEDS_FURTHER_CLINICAL_OR_TERMINOLOGY_REVIEW"):
        assert value in js
    assert "innerHTML" not in js and "eval(" not in js
    assert 'workerSubmitUrl: ""' in (site / "runtime-config.js").read_text()
    assert "PUBLICATION_STATUS: BLOCKED_PENDING_SPICT_PERMISSION_CONFIRMATION" in (root / "review-portal/PUBLICATION_STATUS.md").read_text()
    workflow = (root / ".github/workflows/pages-review.yml").read_text()
    assert "workflow_dispatch:" in workflow and "push:" not in workflow
    assert "SPICT_REVIEW_PORTAL_PUBLICATION_AUTHORIZED" in workflow
    assert 'path: review-portal/site' in workflow
    assert "g5-human-adjudication" in workflow
    pins = {
        "checkout": "11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2",
        "setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0",
        "upload-pages-artifact": "56afc609e74202658d3ffba0e8f6dda462b719fa # v3.0.1",
        "deploy-pages": "d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4.0.5",
    }
    for action, pin in pins.items():
        assert f"uses: actions/{action}@{pin}" in workflow
    assert len(re.findall(r"uses:", workflow)) == len(pins)
    for name in ("README.md", "PUBLICATION_STATUS.md"):
        doc = (root / "review-portal" / name).read_text(encoding="utf-8")
        assert "DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED" in doc
        assert "default branch main" in doc
    assert 'minlength="24" maxlength="256"' in html
    assert '<textarea maxlength="2000">' in html
    assert '<textarea maxlength="1200">' in html
    assert 'edit.maxLength = 2000' in js and 'rationale.maxLength = 1200' in js
    assert "issue-link" not in html and "result.issue_url" not in js
    wrangler = (root / "review-portal/worker/wrangler.toml").read_text()
    assert 'GITHUB_EVIDENCE_REPOSITORY = ""' in wrangler
    assert 'GITHUB_REPOSITORY' not in wrangler
    for path in (root / "review-portal").rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}", text), path
        if path.suffix in (".html", ".js", ".json", ".toml") and "test" not in path.parts:
            assert not re.search(r'(?:access_code|REVIEW_ACCESS_CODE|GITHUB_TOKEN)\s*[:=]\s*[\"\'][^\"\']+[\"\']', text), path


if __name__ == "__main__":
    validate()
    print("Sami portal validation PASS (data and engineering checks; not clinical validation)")
