"""Non-blank, attributable source-authority dispositions.

A final authority disposition is the only mechanism that may change an authority
state, clear a publication blocker, or make evidence document-insertable. Every
attribution field must therefore carry real content. JSON Schema rejects blank
and whitespace-only values, and these domain models reject them again so that a
bypassed or replaced schema cannot admit an unattributable decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .errors import IntegrityError

FINAL_DISPOSITION_STATUS = "FINAL"


class CanonicalAuthorityDecision(str, Enum):
    APPROVE = "APPROVE_CANONICAL_EXCEPTION"
    REJECT = "REJECT_CANONICAL_EXCEPTION"


class RequirementAuthorityDecision(str, Enum):
    INCLUDE = "INCLUDE_IN_FINAL_SOURCE"
    EXCLUDE = "EXCLUDE_FROM_FINAL_SOURCE"


def require_attributable(context: str, field: str, value: object) -> str:
    """Return a value that contains at least one non-whitespace character."""

    if not isinstance(value, str) or not value.strip():
        raise IntegrityError(
            f"{context}: authority disposition {field} must be non-blank and "
            f"non-whitespace; got {value!r}"
        )
    return value


def require_decision_date(context: str, value: object) -> str:
    """Return an attributable ISO-8601 calendar decision date."""

    text = require_attributable(context, "decision_date", value)
    if text != text.strip():
        raise IntegrityError(
            f"{context}: authority disposition decision_date must not be padded "
            f"with whitespace; got {text!r}"
        )
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise IntegrityError(
            f"{context}: authority disposition decision_date must be an ISO-8601 "
            f"calendar date; got {text!r}"
        ) from exc
    return text


def _require_final_status(context: str, status: object) -> None:
    if require_attributable(context, "status", status) != FINAL_DISPOSITION_STATUS:
        raise IntegrityError(
            f"{context}: authority disposition status must be "
            f"{FINAL_DISPOSITION_STATUS}; got {status!r}"
        )


@dataclass(frozen=True)
class RequirementAuthorityDisposition:
    """Final source-authority inclusion or exclusion of one official requirement."""

    requirement_id: str
    decision: RequirementAuthorityDecision
    status: str
    decision_maker: str
    decision_date: str
    evidence_reference: str

    def __post_init__(self) -> None:
        context = require_attributable(
            "<unidentified requirement>", "requirement_id", self.requirement_id
        )
        if not isinstance(self.decision, RequirementAuthorityDecision):
            raise IntegrityError(
                f"{context}: invalid authority decision {self.decision!r}"
            )
        _require_final_status(context, self.status)
        require_attributable(context, "decision_maker", self.decision_maker)
        require_attributable(context, "evidence_reference", self.evidence_reference)
        require_decision_date(context, self.decision_date)


@dataclass(frozen=True)
class CanonicalAuthorityDisposition:
    """Final source-authority disposition of one canonical normalization exception."""

    unit_id: str
    decision: CanonicalAuthorityDecision
    decision_maker: str
    decision_date: str
    evidence_reference: str
    status: str

    def __post_init__(self) -> None:
        context = require_attributable("<unidentified unit>", "unit_id", self.unit_id)
        if not isinstance(self.decision, CanonicalAuthorityDecision):
            raise IntegrityError(
                f"{context}: invalid authority decision {self.decision!r}"
            )
        _require_final_status(context, self.status)
        require_attributable(context, "decision_maker", self.decision_maker)
        require_attributable(context, "evidence_reference", self.evidence_reference)
        require_decision_date(context, self.decision_date)
