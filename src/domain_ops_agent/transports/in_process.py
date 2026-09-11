"""In-process transport — operations are callables in the agent's process."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..context import OperationContext
from ..runtime import OperationRuntime


class InProcessTransport:
    def __init__(self, runtime: OperationRuntime) -> None:
        self.runtime = runtime

    def manifests(self) -> List[Dict[str, Any]]:
        return self.runtime.registry.manifests()

    def plan(
        self,
        name: str,
        params: dict,
        version: Optional[int] = None,
        ctx: Optional[OperationContext] = None,
    ) -> Dict[str, Any]:
        return self.runtime.plan(name, params, version, ctx).to_dict()

    def apply(self, plan_id: str, ctx: Optional[OperationContext] = None) -> Dict[str, Any]:
        return self.runtime.apply(plan_id, ctx).to_dict()
