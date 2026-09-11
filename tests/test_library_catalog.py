import pytest

from domain_ops_agent import OperationContext, PreconditionError
from examples.library_catalog.domain import seed
from examples.library_catalog.operations import build_runtime


def _ctx(db):
    return OperationContext(services={"db": db}, user={"role": "librarian"})


def test_rename_updates_index_and_reverts():
    db = seed()
    runtime = build_runtime(db)
    ctx = _ctx(db)

    plan = runtime.plan("rename_author", {"author_id": "a1", "new_name": "Ada King"}, ctx=ctx)
    assert db.authors["a1"]["name"] == "Ada Lovelace"  # plan writes nothing

    result = runtime.apply(plan.plan_id, ctx=ctx)
    assert result.verification.ok
    assert db.authors["a1"]["name"] == "Ada King"
    assert db.index["idx_b1"]["author_name"] == "Ada King"

    runtime.revert(result.revert_token)
    assert db.authors["a1"]["name"] == "Ada Lovelace"
    assert db.index["idx_b1"]["author_name"] == "Ada Lovelace"


def test_merge_repoints_every_reference():
    db = seed()
    runtime = build_runtime(db)
    ctx = _ctx(db)

    plan = runtime.plan("merge_authors", {"source_id": "a2", "target_id": "a1"}, ctx=ctx)
    result = runtime.apply(plan.plan_id, ctx=ctx)
    assert result.verification.ok
    assert "a2" not in db.authors
    assert db.books["b2"]["author_id"] == "a1"
    assert db.index["idx_b2"]["author_name"] == "Ada Lovelace"


def test_delete_book_cascades_index_and_shelf():
    db = seed()
    runtime = build_runtime(db)
    ctx = _ctx(db)

    plan = runtime.plan("delete_book", {"book_id": "b1"}, ctx=ctx)
    result = runtime.apply(plan.plan_id, ctx=ctx)
    assert result.verification.ok
    assert "b1" not in db.books
    assert "idx_b1" not in db.index
    assert "b1" not in db.shelves["s1"]["book_ids"]


def test_precondition_blocks_missing_author():
    db = seed()
    runtime = build_runtime(db)
    ctx = _ctx(db)
    with pytest.raises(PreconditionError):
        runtime.plan("rename_author", {"author_id": "missing", "new_name": "x"}, ctx=ctx)


def test_merge_requires_distinct_authors():
    db = seed()
    runtime = build_runtime(db)
    ctx = _ctx(db)
    with pytest.raises(PreconditionError):
        runtime.plan("merge_authors", {"source_id": "a1", "target_id": "a1"}, ctx=ctx)
