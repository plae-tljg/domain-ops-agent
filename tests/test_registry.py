import pytest

from domain_ops_agent import (
    DuplicateOperationError,
    OperationRegistry,
    UnknownOperationError,
    operation,
)


def _register(reg, name, version):
    @operation(name=name, version=version, level="organ", registry=reg)
    def _fn(ctx, params):
        return None

    return _fn


def test_latest_version_is_the_default_lookup():
    reg = OperationRegistry()
    _register(reg, "x", 1)
    _register(reg, "x", 2)
    assert reg.get("x").manifest.version == 2
    assert reg.get("x", 1).manifest.version == 1


def test_unknown_operation_raises():
    reg = OperationRegistry()
    with pytest.raises(UnknownOperationError):
        reg.get("missing")


def test_duplicate_name_and_version_rejected():
    reg = OperationRegistry()
    _register(reg, "x", 1)
    with pytest.raises(DuplicateOperationError):
        _register(reg, "x", 1)
