"""Create the R4 final-remediation audit archive."""

from __future__ import annotations

from create_g0_audit_zip import AuditProfile, create_audit

R4_PROFILE = AuditProfile(
    work_package="WP-G0-T0-R4-FINAL-REMEDIATION",
    results_title="SPICT-4ALL FI G0 R4 FINAL REMEDIATION AUDIT RESULTS",
    output_name="SPICT4ALL-FI-G0-R4-final-audit-20260907.zip",
    extended_checks=True,
    terminology_checks=True,
    governance_checks=True,
)


if __name__ == "__main__":
    raise SystemExit(create_audit(R4_PROFILE))
