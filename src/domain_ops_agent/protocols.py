"""Host seams — the protocols an adopter implements.

None of these is required for the core to run; the adapters module provides
in-memory defaults. Implement them to connect the runtime to real storage,
transactions, snapshots, and event streams.
"""
from __future__ import annotations

from typing import Any, ContextManager, Optional, Protocol

from .results import Plan


class PlanStore(Protocol):
    def save(self, plan: Plan) -> None: ...
    def get(self, plan_id: str) -> Optional[Plan]: ...
    def delete(self, plan_id: str) -> None: ...


class Snapshotter(Protocol):
    def snapshot(self, label: str) -> str: ...
    def restore(self, token: str) -> None: ...


class EventSink(Protocol):
    def emit(self, event: dict) -> None: ...


class TransactionManager(Protocol):
    def begin(self) -> ContextManager[Any]: ...
