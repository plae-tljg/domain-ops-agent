"""OperationRegistry — the catalogue the agent's tools are generated from."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .errors import DuplicateOperationError, UnknownOperationError
from .operation import Operation


class OperationRegistry:
    def __init__(self) -> None:
        self._ops: Dict[Tuple[str, int], Operation] = {}

    def register(self, op: Operation) -> Operation:
        key = (op.manifest.name, op.manifest.version)
        if key in self._ops:
            raise DuplicateOperationError(f"{op.manifest.name} v{op.manifest.version} is already registered")
        self._ops[key] = op
        return op

    def get(self, name: str, version: Optional[int] = None) -> Operation:
        if version is not None:
            op = self._ops.get((name, version))
            if op is None:
                raise UnknownOperationError(f"no operation {name!r} v{version}")
            return op
        versions = [v for (n, v) in self._ops if n == name]
        if not versions:
            raise UnknownOperationError(f"no operation named {name!r}")
        return self._ops[(name, max(versions))]

    def operations(self) -> List[Operation]:
        return [self._ops[key] for key in sorted(self._ops)]

    def manifests(self) -> List[dict]:
        return [op.manifest.to_dict() for op in self.operations()]


DEFAULT_REGISTRY = OperationRegistry()
