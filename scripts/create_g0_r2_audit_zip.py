"""Create the second independent-review remediation audit archive."""

from __future__ import annotations

from create_g0_audit_zip import AuditProfile, create_audit

R2_PROFILE = AuditProfile(
    work_package="WP-G0-SOURCE-FREEZE-001-R2",
    results_title="SPICT-4ALL FI G0 R2 SOURCE-FREEZE AUDIT RESULTS",
    output_name="SPICT4ALL-FI-G0-R2-source-freeze-audit-20260907.zip",
    extended_checks=True,
)


if __name__ == "__main__":
    raise SystemExit(create_audit(R2_PROFILE))
