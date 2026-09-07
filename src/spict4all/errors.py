"""Domain-specific failures surfaced by the command-line tools."""


class SpictError(Exception):
    """Base class for expected validation and workflow failures."""


class IntegrityError(SpictError):
    """Raised when source or artifact integrity checks fail."""


class ArtifactValidationError(SpictError):
    """Raised when an evidence artifact is malformed or inconsistent."""


class CoverageError(SpictError):
    """Raised when unit coverage is incomplete or contains unexpected IDs."""


class GateError(SpictError):
    """Raised when release/finalization gates are not satisfied."""


class ImmutableRunError(SpictError):
    """Raised when code attempts to overwrite an existing run directory."""
