"""Invariant — a named, checkable statement about the domain.

An invariant is evaluated before an operation (precondition) or after it
(postcondition). Its description is what a human reads; its ``check`` is what
the runtime evaluates. A check that raises is treated as a failure, with the
error reported as the observed value.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .results import VerificationCheck


@dataclass(frozen=True)
class Invariant:
    description: str
    check: Callable[[Any, dict], bool]

    def evaluate(self, ctx: Any, params: dict) -> VerificationCheck:
        try:
            passed = bool(self.check(ctx, params))
            return VerificationCheck(assertion=self.description, passed=passed)
        except Exception as exc:  # a raising check is a failed check
            return VerificationCheck(assertion=self.description, passed=False, observed=str(exc))
