"""Operation — a manifest plus its plan/apply/verify behaviour."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple

from .context import OperationContext
from .invariant import Invariant
from .manifest import OperationManifest
from .results import Plan, Verification


@dataclass
class Operation:
    manifest: OperationManifest
    apply_fn: Callable[[OperationContext, dict], Any]
    plan_fn: Optional[Callable[[OperationContext, dict], Plan]] = None
    verify_fn: Optional[Callable[[OperationContext, dict], Verification]] = None
    precondition_checks: Tuple[Invariant, ...] = field(default_factory=tuple)
    postcondition_checks: Tuple[Invariant, ...] = field(default_factory=tuple)

    def plan(self, ctx: OperationContext, params: dict) -> Plan:
        if self.plan_fn is not None:
            return self.plan_fn(ctx, params)
        return Plan(
            operation=self.manifest.name,
            version=self.manifest.version,
            params=params,
            effects=self.manifest.effects,
            reference_coverage=self.manifest.reference_coverage,
            verification_plan=self.manifest.postconditions,
        )

    def apply(self, ctx: OperationContext, params: dict) -> Any:
        return self.apply_fn(ctx, params)

    def verify(self, ctx: OperationContext, params: dict) -> Verification:
        if self.verify_fn is not None:
            return self.verify_fn(ctx, params)
        checks = [inv.evaluate(ctx, params) for inv in self.postcondition_checks]
        return Verification(ok=all(c.passed for c in checks), checks=checks)
