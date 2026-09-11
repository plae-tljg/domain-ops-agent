"""OperationManifest — the machine-readable contract of an operation.

The manifest is the contract that survives decoupling: it travels with the
operation whether it runs in-process or behind an API, and the agent's tools
are generated from it. See docs/CONCEPTS.md and docs/WIRE_CONTRACT.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .cascade import Cascade


@dataclass(frozen=True)
class OperationManifest:
    name: str
    version: int
    level: str  # "tissue" | "organ" | "organ_system"
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    preconditions: Tuple[str, ...] = ()
    effects: Tuple[str, ...] = ()
    reference_coverage: Tuple[Cascade, ...] = ()
    diff: str = ""
    postconditions: Tuple[str, ...] = ()
    transaction_boundary: str = ""
    reversibility: str = "restore pre-operation snapshot"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "level": self.level,
            "description": self.description,
            "params": self.params,
            "preconditions": list(self.preconditions),
            "effects": list(self.effects),
            "reference_coverage": [c.to_dict() for c in self.reference_coverage],
            "diff": self.diff,
            "postconditions": list(self.postconditions),
            "transaction_boundary": self.transaction_boundary,
            "reversibility": self.reversibility,
        }
