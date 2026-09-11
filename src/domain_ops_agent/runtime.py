"""OperationRuntime — the plan -> approve -> apply -> verify -> revert lifecycle.

The runtime orchestrates; the operation enforces integrity. It never mutates
during ``plan``, always snapshots before ``apply``, and evaluates the
operation's postconditions after.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from .adapters import InMemoryPlanStore, NullEventSink, NullSnapshotter, NullTransactionManager
from .context import OperationContext
from .errors import PreconditionError, UnknownPlanError
from .registry import OperationRegistry
from .results import ApplyResult, Plan
from .status import Status


class OperationRuntime:
    def __init__(
        self,
        registry: OperationRegistry,
        store: Optional[Any] = None,
        snapshotter: Optional[Any] = None,
        events: Optional[Any] = None,
        transactions: Optional[Any] = None,
    ) -> None:
        self.registry = registry
        self.store = store if store is not None else InMemoryPlanStore()
        self.snapshotter = snapshotter if snapshotter is not None else NullSnapshotter()
        self.events = events if events is not None else NullEventSink()
        self.transactions = transactions if transactions is not None else NullTransactionManager()

    def plan(
        self,
        name: str,
        params: dict,
        version: Optional[int] = None,
        ctx: Optional[OperationContext] = None,
    ) -> Plan:
        op = self.registry.get(name, version)
        ctx = ctx or OperationContext()
        self._assert(op.precondition_checks, ctx, params, phase="precondition")
        plan = op.plan(ctx, params)
        self.store.save(plan)
        self.events.emit({"type": "plan_pending", **plan.to_dict()})
        return plan

    def apply(self, plan_id: str, ctx: Optional[OperationContext] = None) -> ApplyResult:
        plan = self.store.get(plan_id)
        if plan is None:
            raise UnknownPlanError(plan_id)
        op = self.registry.get(plan.operation, plan.version)
        ctx = ctx or OperationContext()
        token = self.snapshotter.snapshot(plan.operation)
        with self.transactions.begin() as tx:
            ctx.transaction = tx
            raw = op.apply(ctx, plan.params)
        verification = op.verify(ctx, plan.params)
        result = ApplyResult(
            status=Status.DONE,
            result=raw,
            verification=verification,
            revert_token=token,
        )
        self.store.delete(plan_id)
        self.events.emit({"type": "plan_result", **result.to_dict()})
        return result

    def reject(self, plan_id: str) -> None:
        self.store.delete(plan_id)

    def revert(self, token: str) -> None:
        self.snapshotter.restore(token)

    @staticmethod
    def _assert(invariants: Iterable[Any], ctx: OperationContext, params: dict, phase: str) -> None:
        for inv in invariants:
            check = inv.evaluate(ctx, params)
            if not check.passed:
                raise PreconditionError(f"{phase}: {inv.description}", check)
