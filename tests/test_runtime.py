import pytest

from domain_ops_agent import (
    Invariant,
    NullEventSink,
    OperationContext,
    OperationRegistry,
    OperationRuntime,
    PreconditionError,
    Status,
    UnknownPlanError,
    operation,
)


class _RecordingSnapshotter:
    def __init__(self):
        self.calls = []

    def snapshot(self, label):
        token = f"snap:{label}"
        self.calls.append(("snap", token))
        return token

    def restore(self, token):
        self.calls.append(("restore", token))


def _make_runtime():
    reg = OperationRegistry()
    events = NullEventSink()
    snapshots = _RecordingSnapshotter()
    runtime = OperationRuntime(reg, events=events, snapshotter=snapshots)

    @operation(
        name="rename_item",
        version=1,
        level="organ_system",
        preconditions=[
            Invariant("item exists", lambda ctx, p: p["item_id"] in ctx.services["db"]["items"]),
        ],
        postconditions=[
            Invariant(
                "index matches",
                lambda ctx, p: all(
                    e["name"] == p["new_name"] for e in ctx.services["db"]["index"].values()
                ),
            ),
        ],
        reference_coverage=["index.name"],
        registry=reg,
    )
    def rename_item(ctx, params):
        db = ctx.services["db"]
        db["items"][params["item_id"]]["name"] = params["new_name"]
        for entry in db["index"].values():
            entry["name"] = params["new_name"]
        return {"renamed": params["item_id"]}

    return runtime, events, snapshots


def _ctx():
    return OperationContext(
        services={"db": {"items": {"a": {"name": "old"}}, "index": {"i1": {"name": "old"}}}},
        user={"id": 1},
    )


def test_plan_does_not_mutate_and_emits_pending():
    runtime, events, _snap = _make_runtime()
    ctx = _ctx()
    plan = runtime.plan("rename_item", {"item_id": "a", "new_name": "new"}, ctx=ctx)
    assert plan.to_dict()["operation"] == "rename_item"
    assert ctx.services["db"]["items"]["a"]["name"] == "old"
    assert events.events[-1]["type"] == "plan_pending"


def test_apply_mutates_verifies_and_snapshots():
    runtime, events, snap = _make_runtime()
    ctx = _ctx()
    plan = runtime.plan("rename_item", {"item_id": "a", "new_name": "new"}, ctx=ctx)
    result = runtime.apply(plan.plan_id, ctx=ctx)
    assert result.status == Status.DONE
    assert result.verification.ok is True
    assert result.revert_token == "snap:rename_item"
    assert ctx.services["db"]["items"]["a"]["name"] == "new"
    assert events.events[-1]["type"] == "plan_result"
    assert snap.calls[0] == ("snap", "snap:rename_item")


def test_precondition_failure_blocks_plan():
    runtime, events, _snap = _make_runtime()
    with pytest.raises(PreconditionError):
        runtime.plan("rename_item", {"item_id": "missing", "new_name": "x"}, ctx=_ctx())
    assert not any(e["type"] == "plan_pending" for e in events.events)


def test_reject_discards_plan():
    runtime, _events, _snap = _make_runtime()
    ctx = _ctx()
    plan = runtime.plan("rename_item", {"item_id": "a", "new_name": "new"}, ctx=ctx)
    runtime.reject(plan.plan_id)
    with pytest.raises(UnknownPlanError):
        runtime.apply(plan.plan_id, ctx=ctx)


def test_revert_restores_snapshot():
    runtime, _events, snap = _make_runtime()
    ctx = _ctx()
    plan = runtime.plan("rename_item", {"item_id": "a", "new_name": "new"}, ctx=ctx)
    result = runtime.apply(plan.plan_id, ctx=ctx)
    runtime.revert(result.revert_token)
    assert snap.calls[-1] == ("restore", "snap:rename_item")


def test_failed_postcondition_is_reported_honestly():
    reg = OperationRegistry()
    runtime = OperationRuntime(reg)

    @operation(
        name="broken",
        level="organ",
        postconditions=[Invariant("always false", lambda ctx, p: False)],
        registry=reg,
    )
    def broken(ctx, params):
        return None

    plan = runtime.plan("broken", {})
    result = runtime.apply(plan.plan_id)
    assert result.verification.ok is False
    assert result.verification.checks[0].assertion == "always false"
