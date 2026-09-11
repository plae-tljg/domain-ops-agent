"""Transport adapters. One contract, two transports."""
from .in_process import InProcessTransport
from .remote import RemoteOperationClient

__all__ = ["InProcessTransport", "RemoteOperationClient"]
