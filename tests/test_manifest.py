from domain_ops_agent import Cascade, Invariant, OperationRegistry, operation


def test_decorator_builds_and_serializes_manifest():
    reg = OperationRegistry()

    @operation(
        name="rename_item",
        version=2,
        level="organ_system",
        description="Rename an item and its index copies.",
        params={"type": "object"},
        preconditions=[
            "item exists",
            Invariant("name non-empty", lambda ctx, p: bool(p.get("new_name"))),
        ],
        effects=["item", "index"],
        reference_coverage=[("index.name", "rewrite"), Cascade("cache.name")],
        postconditions=["index matches"],
        transaction_boundary="item + index",
        registry=reg,
    )
    def rename_item(ctx, params):
        return "ok"

    manifest = reg.manifests()[0]
    assert manifest["name"] == "rename_item"
    assert manifest["version"] == 2
    assert manifest["level"] == "organ_system"
    assert manifest["preconditions"] == ["item exists", "name non-empty"]
    assert manifest["effects"] == ["item", "index"]
    assert manifest["reference_coverage"] == [
        {"reference": "index.name", "strategy": "rewrite"},
        {"reference": "cache.name", "strategy": ""},
    ]
    assert manifest["transaction_boundary"] == "item + index"
    assert rename_item.__operation__.manifest.name == "rename_item"


def test_manifest_roundtrip_has_all_contract_fields():
    reg = OperationRegistry()

    @operation(name="x", level="organ", registry=reg)
    def x(ctx, params):
        return None

    m = reg.manifests()[0]
    for field in (
        "name", "version", "level", "description", "params", "preconditions",
        "effects", "reference_coverage", "diff", "postconditions",
        "transaction_boundary", "reversibility",
    ):
        assert field in m
