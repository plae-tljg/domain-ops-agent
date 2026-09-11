"""The @operation decorator — define an operation and register its manifest.

The decorated function is the ``apply`` step. Optional ``plan`` and ``verify``
callables refine the lifecycle. Preconditions and postconditions accept either
a plain string (documentation) or an :class:`Invariant` (evaluated by the
runtime).
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional, Tuple, Union

from .cascade import Cascade
from .context import OperationContext
from .invariant import Invariant
from .manifest import OperationManifest
from .operation import Operation
from .registry import DEFAULT_REGISTRY, OperationRegistry

Condition = Union[str, Invariant]
CascadeLike = Union[Cascade, str, Tuple[str, str], list]


def _as_cascades(items: Iterable[CascadeLike]) -> Tuple[Cascade, ...]:
    out = []
    for item in items:
        if isinstance(item, Cascade):
            out.append(item)
        elif isinstance(item, str):
            out.append(Cascade(reference=item))
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            out.append(Cascade(reference=str(item[0]), strategy=str(item[1])))
        else:
            raise TypeError(f"reference_coverage entry must be Cascade/str/(ref, strategy): {item!r}")
    return tuple(out)


def _split_conditions(items: Iterable[Condition]) -> Tuple[Tuple[str, ...], Tuple[Invariant, ...]]:
    descriptions = []
    checks = []
    for item in items:
        if isinstance(item, Invariant):
            descriptions.append(item.description)
            checks.append(item)
        elif isinstance(item, str):
            descriptions.append(item)
        else:
            raise TypeError(f"condition must be str or Invariant: {item!r}")
    return tuple(descriptions), tuple(checks)


def operation(
    *,
    name: str,
    level: str,
    version: int = 1,
    description: str = "",
    params: Optional[dict] = None,
    preconditions: Iterable[Condition] = (),
    effects: Iterable[str] = (),
    reference_coverage: Iterable[CascadeLike] = (),
    postconditions: Iterable[Condition] = (),
    transaction_boundary: str = "",
    reversibility: str = "restore pre-operation snapshot",
    diff: str = "",
    plan: Optional[Callable[[OperationContext, dict], Any]] = None,
    verify: Optional[Callable[[OperationContext, dict], Any]] = None,
    registry: Optional[OperationRegistry] = None,
) -> Callable[[Callable[[OperationContext, dict], Any]], Callable[[OperationContext, dict], Any]]:
    pre_desc, pre_checks = _split_conditions(preconditions)
    post_desc, post_checks = _split_conditions(postconditions)
    manifest = OperationManifest(
        name=name,
        version=version,
        level=level,
        description=description,
        params=params or {},
        preconditions=pre_desc,
        effects=tuple(effects),
        reference_coverage=_as_cascades(reference_coverage),
        diff=diff,
        postconditions=post_desc,
        transaction_boundary=transaction_boundary,
        reversibility=reversibility,
    )

    def decorate(fn: Callable[[OperationContext, dict], Any]) -> Callable[[OperationContext, dict], Any]:
        op = Operation(
            manifest=manifest,
            apply_fn=fn,
            plan_fn=plan,
            verify_fn=verify,
            precondition_checks=pre_checks,
            postcondition_checks=post_checks,
        )
        (registry or DEFAULT_REGISTRY).register(op)
        fn.__operation__ = op  # type: ignore[attr-defined]
        return fn

    return decorate
