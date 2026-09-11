"""Cascade — one coupled reference an operation must keep coherent.

A ``Cascade`` names a reference (a foreign key, a denormalized copy, an index,
a cache) and the strategy for updating it when the operation runs. The set of
cascades on an operation is its ``reference_coverage``: the answer to "rename
the id but not the other things using it".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Cascade:
    reference: str
    strategy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"reference": self.reference, "strategy": self.strategy}
