"""Run the in-process lifecycle end to end:

    PYTHONPATH=src python examples/library_catalog/demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from domain_ops_agent import NullEventSink, OperationContext  # noqa: E402
from examples.library_catalog.domain import seed  # noqa: E402
from examples.library_catalog.operations import build_runtime  # noqa: E402


def main() -> None:
    db = seed()
    events = NullEventSink()
    runtime = build_runtime(db)
    runtime.events = events
    ctx = OperationContext(services={"db": db}, user={"role": "librarian"})

    print("authors before:", {a["id"]: a["name"] for a in db.authors.values()})

    plan = runtime.plan("rename_author", {"author_id": "a1", "new_name": "Ada King"}, ctx=ctx)
    print("plan diff:", plan.to_dict()["diff"])
    result = runtime.apply(plan.plan_id, ctx=ctx)
    print("rename:", result.status.value, "| verified:", result.verification.ok)
    print("index after rename:", {e["id"]: e["author_name"] for e in db.index.values()})

    runtime.revert(result.revert_token)
    print("index after revert:", {e["id"]: e["author_name"] for e in db.index.values()})

    plan = runtime.plan("merge_authors", {"source_id": "a2", "target_id": "a1"}, ctx=ctx)
    result = runtime.apply(plan.plan_id, ctx=ctx)
    print("merge:", result.status.value, "| verified:", result.verification.ok)
    print("authors after merge:", list(db.authors))
    print("book authors after merge:", {b["id"]: b["author_id"] for b in db.books.values()})

    plan = runtime.plan("delete_book", {"book_id": "b1"}, ctx=ctx)
    result = runtime.apply(plan.plan_id, ctx=ctx)
    print("delete:", result.status.value, "| verified:", result.verification.ok)
    print("shelf after delete:", db.shelves["s1"]["book_ids"])

    print("events:", [e["type"] for e in events.events])


if __name__ == "__main__":
    main()
