"""Create the independent-review remediation audit archive."""

from __future__ import annotations

from create_g0_audit_zip import AuditProfile, create_audit

R1_PROFILE = AuditProfile(
    work_package="WP-G0-SOURCE-FREEZE-001-R1",
    results_title="SPICT-4ALL FI G0 R1 SOURCE-FREEZE AUDIT RESULTS",
    output_name="SPICT4ALL-FI-G0-R1-source-freeze-audit-20260907.zip",
)


if __name__ == "__main__":
    raise SystemExit(create_audit(R1_PROFILE))
