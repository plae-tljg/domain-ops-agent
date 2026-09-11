"""In-memory / no-op implementations of the host seams.

Useful for tests, examples, and single-process agents. Replace with real
adapters when connecting to a database, snapshot store, or event stream.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional
from uuid import uuid4

from .results import Plan


class InMemoryPlanStore:
    def __init__(self) -> None:
        self._plans: Dict[str, Plan] = {}

    def save(self, plan: Plan) -> None:
        self._plans[plan.plan_id] = plan

    def get(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)

    def delete(self, plan_id: str) -> None:
        self._plans.pop(plan_id, None)

    def list(self) -> List[Plan]:
        return list(self._plans.values())


class NullSnapshotter:
    def snapshot(self, label: str) -> str:
        return "snapshot_" + uuid4().hex[:12]

    def restore(self, token: str) -> None:
        return None


class NullEventSink:
    def __init__(self) -> None:
        self.events: List[dict] = []

    def emit(self, event: dict) -> None:
        self.events.append(event)


class NullTransactionManager:
    @contextmanager
    def begin(self) -> Iterator[Any]:
        yield None
