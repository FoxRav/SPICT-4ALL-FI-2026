"""Check generated data, frozen evidence, and publication safety."""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

from build_sami_review_portal import ROOT, artifacts


def validate_local_secrets(root: Path) -> None:
    probes = [".dev.vars", ".dev.vars.local", "review-portal/worker/.dev.vars",
              "review-portal/worker/.dev.vars.preview", ".wrangler/cache.bin",
              "review-portal/worker/.wrangler/cache.bin"]
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"], cwd=root,
        input=("\n".join(probes) + "\n").encode(), capture_output=True, check=False,
    )
    assert set(ignored.stdout.decode().splitlines()) == set(probes), "Local secret files must be gitignored"
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    assert not any(Path(name).name == ".dev.vars" or Path(name).name.startswith(".dev.vars.")
                   for name in tracked), "Local secret file is tracked; contents not read"


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
    runtime = (site / "runtime-config.js").read_text(encoding="utf-8")
    match = re.fullmatch(
        r'\s*window\.REVIEW_RUNTIME_CONFIG\s*=\s*Object\.freeze\(\{\s*'
        r'workerSubmitUrl:\s*"([^"]+)"\s*\}\);\s*', runtime,
    )
    assert match, "Unexpected runtime configuration"
    endpoint = match.group(1)
    url = urlsplit(endpoint)
    assert url.scheme == "https"
    assert url.hostname == "spict-sami-review.mmvirta75.workers.dev"
    assert url.path == "/submit"
    assert url.username is None and url.password is None
    assert not url.query and not url.fragment
    assert endpoint == "https://spict-sami-review.mmvirta75.workers.dev/submit"
    assert "PUBLICATION_STATUS: CONTROLLED_G5_REVIEWER_ACTIVATION_CONFIGURED" in (root / "review-portal/PUBLICATION_STATUS.md").read_text()
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
    publication_status = (root / "review-portal/PUBLICATION_STATUS.md").read_text(encoding="utf-8")
    readme = (root / "review-portal/README.md").read_text(encoding="utf-8")
    assert "DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_COMPLETED" in publication_status
    assert "GitHub Pages frontend: DEPLOYED." in publication_status
    assert "Production E2E: PASS (synthetic Issue #3; never import as human adjudication)." in publication_status
    assert "DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED" not in publication_status
    assert "The Pages workflow is bootstrapped on main" in readme
    assert "https://foxrav.github.io/SPICT-4ALL-FI-2026/review/sami/" in readme
    assert "Production E2E passed using synthetic Issue #3." in readme
    assert "DEFAULT_BRANCH_WORKFLOW_BOOTSTRAP_REQUIRED" not in readme
    assert 'minlength="24" maxlength="256"' in html
    assert '<textarea maxlength="2000">' in html
    assert '<textarea maxlength="1200">' in html
    assert 'edit.maxLength = 2000' in js and 'rationale.maxLength = 1200' in js
    assert "issue-link" not in html and "result.issue_url" not in js
    wrangler = (root / "review-portal/worker/wrangler.toml").read_text()
    worker_config = tomllib.loads(wrangler)
    assert worker_config["workers_dev"] is True
    assert worker_config["preview_urls"] is False
    assert worker_config["secrets"] == {"required": ["GITHUB_TOKEN", "REVIEW_ACCESS_CODE"]}
    worker_vars = worker_config["vars"]
    assert worker_vars == {
        "GITHUB_EVIDENCE_REPOSITORY": "FoxRav/SPICT-4ALL-FI-2026-review-evidence",
        "PUBLICATION_AUTHORIZED": "true",
        "ALLOWED_ORIGIN": "https://foxrav.github.io",
    }
    assert 'GITHUB_REPOSITORY' not in wrangler
    worker = (root / "review-portal/worker/src/index.js").read_text(encoding="utf-8")
    assert worker.count("redirect: 'manual'") == 2
    assert "redirect: 'error'" not in worker and "redirect: 'follow'" not in worker
    assert "repository.status !== 200" in worker and "upstream.status !== 201" in worker
    assert worker.count("AbortSignal.timeout(15000)") == 2
    validate_local_secrets(root)
    for path in (root / "review-portal").rglob("*"):
        if ".wrangler" in path.relative_to(root / "review-portal").parts:
            continue  # Local Wrangler runtime cache is not source or review evidence.
        if not path.is_file() or path.name == ".dev.vars" or path.name.startswith(".dev.vars."):
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}", text), path
        if path.suffix in (".html", ".js", ".json", ".toml") and "test" not in path.parts:
            assert not re.search(r'(?:access_code|REVIEW_ACCESS_CODE|GITHUB_TOKEN)\s*[:=]\s*[\"\'][^\"\']+[\"\']', text), path


if __name__ == "__main__":
    validate()
    print("Sami portal validation PASS (data and engineering checks; not clinical validation)")
