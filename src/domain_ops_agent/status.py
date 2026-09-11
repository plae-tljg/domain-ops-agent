"""The single status vocabulary shared by operations, plans, and results."""
from __future__ import annotations

from enum import Enum


class Status(str, Enum):
    """Outcome of an operation or tool call."""

    DONE = "done"
    NOOP = "noop"
    QUEUED = "queued"
    FAILED = "failed"
    CANCELLED = "cancelled"
