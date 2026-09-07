"""Create the R3 source-freeze and terminology-foundation audit archive."""

from __future__ import annotations

from create_g0_audit_zip import AuditProfile, create_audit

R3_PROFILE = AuditProfile(
    work_package="WP-G0-SOURCE-FREEZE-001-R3-AND-TERMINOLOGY-FOUNDATION",
    results_title="SPICT-4ALL FI G0 R3 SOURCE-FREEZE AND TERMINOLOGY AUDIT RESULTS",
    output_name="SPICT4ALL-FI-G0-R3-source-freeze-audit-20260907.zip",
    extended_checks=True,
    terminology_checks=True,
)


if __name__ == "__main__":
    raise SystemExit(create_audit(R3_PROFILE))
