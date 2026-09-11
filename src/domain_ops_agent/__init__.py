"""domain-ops-agent — make a domain's valid operations the agent's action space.

Core, transport-agnostic primitives. See README.md and docs/.
"""
from .adapters import (
    InMemoryPlanStore,
    NullEventSink,
    NullSnapshotter,
    NullTransactionManager,
)
from .cascade import Cascade
from .context import OperationContext
from .decorators import operation
from .errors import (
    DomainOpsError,
    DuplicateOperationError,
    PreconditionError,
    UnknownOperationError,
    UnknownPlanError,
)
from .invariant import Invariant
from .manifest import OperationManifest
from .operation import Operation
from .registry import DEFAULT_REGISTRY, OperationRegistry
from .results import ApplyResult, Plan, Verification, VerificationCheck
from .runtime import OperationRuntime
from .status import Status
from .transports import InProcessTransport, RemoteOperationClient

__version__ = "0.1.0"

__all__ = [
    "Status",
    "Cascade",
    "Invariant",
    "OperationManifest",
    "OperationContext",
    "Operation",
    "OperationRegistry",
    "DEFAULT_REGISTRY",
    "operation",
    "Plan",
    "ApplyResult",
    "Verification",
    "VerificationCheck",
    "OperationRuntime",
    "InMemoryPlanStore",
    "NullSnapshotter",
    "NullEventSink",
    "NullTransactionManager",
    "InProcessTransport",
    "RemoteOperationClient",
    "DomainOpsError",
    "DuplicateOperationError",
    "UnknownOperationError",
    "UnknownPlanError",
    "PreconditionError",
]
