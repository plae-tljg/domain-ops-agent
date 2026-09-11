"""OperationContext — the host-provided environment an operation runs in.

Operations never reach for global state. Everything they need (the current
transaction, the acting user, host services, an event sink) arrives here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class OperationContext:
    user: Dict[str, Any] = field(default_factory=dict)
    services: Dict[str, Any] = field(default_factory=dict)
    transaction: Any = None
    events: Optional[Callable[[Dict[str, Any]], None]] = None

    def emit(self, event: Dict[str, Any]) -> None:
        if self.events is not None:
            self.events(event)
