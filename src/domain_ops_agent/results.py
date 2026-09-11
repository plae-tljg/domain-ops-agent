"""Result shapes: Verification, Plan, ApplyResult.

These are the transport-agnostic shapes described in docs/WIRE_CONTRACT.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .cascade import Cascade
from .status import Status


def _new_plan_id() -> str:
    return "op_" + uuid4().hex[:12]


@dataclass
class VerificationCheck:
    assertion: str
    passed: bool
    observed: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {"assertion": self.assertion, "passed": self.passed, "observed": self.observed}


@dataclass
class Verification:
    ok: bool
    checks: List[VerificationCheck] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "checks": [c.to_dict() for c in self.checks]}


def _serialize_cascades(items: Tuple[Any, ...]) -> List[Any]:
    return [c.to_dict() if isinstance(c, Cascade) else c for c in items]


@dataclass
class Plan:
    """A reviewable, non-mutating change proposal."""

    operation: str
    version: int
    params: Dict[str, Any]
    diff: Optional[Dict[str, Any]] = None
    effects: Tuple[str, ...] = ()
    reference_coverage: Tuple[Any, ...] = ()
    verification_plan: Tuple[str, ...] = ()
    impact: Dict[str, Any] = field(default_factory=dict)
    plan_id: str = field(default_factory=_new_plan_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "operation": self.operation,
            "version": self.version,
            "params": self.params,
            "diff": self.diff,
            "effects": list(self.effects),
            "reference_coverage": _serialize_cascades(self.reference_coverage),
            "verification_plan": list(self.verification_plan),
            "impact": self.impact,
        }


@dataclass
class ApplyResult:
    status: Status = Status.DONE
    result: Any = None
    verification: Optional[Verification] = None
    revert_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "result": self.result,
            "verification": self.verification.to_dict() if self.verification else None,
            "revert_token": self.revert_token,
        }
