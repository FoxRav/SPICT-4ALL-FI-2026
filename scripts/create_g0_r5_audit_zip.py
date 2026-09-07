"""Create the R5 final-remediation audit archive."""

from __future__ import annotations

import zipfile
from pathlib import Path

from create_g0_audit_zip import AuditProfile, collect_repository_payload, create_audit

R5_PROFILE = AuditProfile(
    work_package="WP-G0-T0-R5-FINAL-REMEDIATION",
    results_title="SPICT-4ALL FI G0 R5 FINAL REMEDIATION AUDIT RESULTS",
    output_name="SPICT4ALL-FI-G0-R5-final-audit-20260907.zip",
    extended_checks=True,
    terminology_checks=True,
    governance_checks=True,
)


def main() -> int:
    result = create_audit(R5_PROFILE)
    repository = Path(__file__).resolve().parents[1]
    payload = collect_repository_payload(repository)
    with zipfile.ZipFile(repository / "deliverables/audit" / R5_PROFILE.output_name) as archive:
        for name, expected in payload.items():
            if archive.read(name) != expected:
                raise RuntimeError(f"Archived file differs from current tree: {name}")
        if any(name.lower().endswith(".zip") for name in archive.namelist()):
            raise RuntimeError("Nested ZIP in audit payload")
    print(f"CURRENT_TREE_MATCH_PASS={len(payload)} CURRENT_TREE_MATCH_FAIL=0")
    print("NESTED_PREVIOUS_AUDIT_ZIPS=0")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
