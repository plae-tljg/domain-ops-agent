from domain_ops_agent import (
    InProcessTransport,
    OperationRegistry,
    OperationRuntime,
    RemoteOperationClient,
    operation,
)


def _runtime():
    reg = OperationRegistry()

    @operation(name="noop_op", version=1, level="organ", registry=reg)
    def noop_op(ctx, params):
        return {"ok": True}

    return OperationRuntime(reg)


def test_in_process_transport_shares_the_contract():
    transport = InProcessTransport(_runtime())
    assert transport.manifests()[0]["name"] == "noop_op"

    plan = transport.plan("noop_op", {})
    assert plan["operation"] == "noop_op"

    result = transport.apply(plan["plan_id"])
    assert result["status"] == "done"


def test_remote_client_speaks_the_wire_contract():
    calls = []

    def http(method, url, body):
        calls.append((method, url, body))
        if url.endswith("/operations"):
            return 200, {"operations": [{"name": "noop_op"}]}
        if url.endswith("/plan"):
            return 200, {"plan_id": "op_1", "operation": "noop_op", "version": 1, "params": {}}
        return 200, {"status": "done"}

    client = RemoteOperationClient("http://svc", http=http)
    assert client.manifests()[0]["name"] == "noop_op"

    plan = client.plan("noop_op", {})
    result = client.apply(plan)
    assert result["status"] == "done"
    assert calls[-1][1] == "http://svc/operations/noop_op/apply"
    assert calls[-1][2]["plan_id"] == "op_1"
