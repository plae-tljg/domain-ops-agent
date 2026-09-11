"""Errors raised by the runtime."""
from __future__ import annotations

from typing import Any, Optional


class DomainOpsError(Exception):
    """Base class for all domain-ops-agent errors."""


class DuplicateOperationError(DomainOpsError):
    """Two operations share a name and version."""


class UnknownOperationError(DomainOpsError):
    """No operation matches the requested name/version."""


class UnknownPlanError(DomainOpsError):
    """No stored plan matches the requested id."""


class PreconditionError(DomainOpsError):
    """A precondition failed; the operation did not run."""

    def __init__(self, description: str, check: Optional[Any] = None) -> None:
        super().__init__(description)
        self.description = description
        self.check = check
