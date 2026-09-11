"""The library/catalog domain's valid operations.

Each operation is transactional and reference-complete: the agent can choose
among these, and cannot express a partial change.
"""
from __future__ import annotations

from typing import Any, Dict

from domain_ops_agent import (
    Cascade,
    Invariant,
    OperationRegistry,
    OperationRuntime,
    Plan,
    operation,
)

from .domain import LibraryDB, LibrarySnapshotter


def _plan_rename_author(ctx, params: Dict[str, Any]) -> Plan:
    db: LibraryDB = ctx.services["db"]
    author = dict(db.authors[params["author_id"]])
    entries = db.index_entries_of(params["author_id"])
    return Plan(
        operation="rename_author",
        version=1,
        params=params,
        diff={
            "before": {"author": author, "index_names": sorted({e["author_name"] for e in entries})},
            "after": {
                "author": {"id": author["id"], "name": params["new_name"]},
                "index_names": [params["new_name"]],
            },
        },
        effects=("author", "catalog_index"),
        reference_coverage=(Cascade("catalog_index.author_name", "rewrite denormalized copy"),),
        verification_plan=("author.name == new_name", "index names match"),
        impact={"index_entries": len(entries)},
    )


def _plan_merge_authors(ctx, params: Dict[str, Any]) -> Plan:
    db: LibraryDB = ctx.services["db"]
    source = dict(db.authors[params["source_id"]])
    target = dict(db.authors[params["target_id"]])
    books = [b["id"] for b in db.books_of(params["source_id"])]
    entries = [e["id"] for e in db.index_entries_of(params["source_id"])]
    return Plan(
        operation="merge_authors",
        version=1,
        params=params,
        diff={
            "before": {"source": source, "target": target, "books": books, "index_entries": entries},
            "after": {"books_repointed": books, "index_rewritten": entries, "source_removed": source["id"]},
        },
        effects=("author", "book", "catalog_index"),
        reference_coverage=(
            Cascade("book.author_id", "repoint foreign key"),
            Cascade("catalog_index.author_name", "rewrite denormalized copy"),
        ),
        verification_plan=(
            "no book references source",
            "every index name resolves to a live author",
            "source author removed",
        ),
        impact={"books": len(books), "index_entries": len(entries)},
    )


def _plan_delete_book(ctx, params: Dict[str, Any]) -> Plan:
    db: LibraryDB = ctx.services["db"]
    book = dict(db.books[params["book_id"]])
    entries = [e["id"] for e in db.index.values() if e["book_id"] == params["book_id"]]
    shelves = [s["id"] for s in db.shelves.values() if params["book_id"] in s["book_ids"]]
    return Plan(
        operation="delete_book",
        version=1,
        params=params,
        diff={
            "before": {"book": book, "index_entries": entries, "shelves": shelves},
            "after": {"book_removed": book["id"], "index_entries_removed": entries, "shelves_updated": shelves},
        },
        effects=("book", "catalog_index", "shelf"),
        reference_coverage=(
            Cascade("catalog_index.book_id", "delete entries"),
            Cascade("shelf.book_ids", "remove membership"),
        ),
        verification_plan=("no index references the book", "no shelf lists the book"),
        impact={"index_entries": len(entries), "shelves": len(shelves)},
    )


def register_operations(reg: OperationRegistry) -> OperationRegistry:
    @operation(
        name="rename_author",
        version=1,
        level="organ_system",
        description="Rename an author and rewrite every denormalized copy in the catalog index.",
        params={
            "type": "object",
            "properties": {"author_id": {"type": "string"}, "new_name": {"type": "string"}},
            "required": ["author_id", "new_name"],
        },
        preconditions=[
            Invariant("author exists", lambda ctx, p: p["author_id"] in ctx.services["db"].authors),
            Invariant("new name is non-empty", lambda ctx, p: bool(str(p.get("new_name", "")).strip())),
        ],
        effects=["author", "catalog_index"],
        reference_coverage=[Cascade("catalog_index.author_name", "rewrite denormalized copy")],
        postconditions=[
            Invariant(
                "index names match the author",
                lambda ctx, p: ctx.services["db"].index_names_match(p["author_id"]),
            ),
        ],
        transaction_boundary="author + catalog_index",
        diff="before/after of the author row and the affected index entries",
        plan=_plan_rename_author,
        registry=reg,
    )
    def rename_author(ctx, params):
        ctx.services["db"].rename_author(params["author_id"], params["new_name"])
        return {"renamed": params["author_id"]}

    @operation(
        name="merge_authors",
        version=1,
        level="organ_system",
        description="Merge one author into another, repointing books and rewriting index copies.",
        params={
            "type": "object",
            "properties": {"source_id": {"type": "string"}, "target_id": {"type": "string"}},
            "required": ["source_id", "target_id"],
        },
        preconditions=[
            Invariant("source exists", lambda ctx, p: p["source_id"] in ctx.services["db"].authors),
            Invariant("target exists", lambda ctx, p: p["target_id"] in ctx.services["db"].authors),
            Invariant("source differs from target", lambda ctx, p: p["source_id"] != p["target_id"]),
        ],
        effects=["author", "book", "catalog_index"],
        reference_coverage=[
            Cascade("book.author_id", "repoint foreign key"),
            Cascade("catalog_index.author_name", "rewrite denormalized copy"),
        ],
        postconditions=[
            Invariant("no book references source", lambda ctx, p: ctx.services["db"].no_book_references(p["source_id"])),
            Invariant("every index name resolves", lambda ctx, p: ctx.services["db"].index_names_valid()),
            Invariant("source author removed", lambda ctx, p: p["source_id"] not in ctx.services["db"].authors),
        ],
        transaction_boundary="author + book + catalog_index",
        diff="books repointed, index entries rewritten, source removed",
        plan=_plan_merge_authors,
        registry=reg,
    )
    def merge_authors(ctx, params):
        moved = ctx.services["db"].merge_authors(params["source_id"], params["target_id"])
        return {"merged": params["source_id"], "into": params["target_id"], "books_moved": moved}

    @operation(
        name="delete_book",
        version=1,
        level="organ",
        description="Delete a book and remove it from the index and every shelf.",
        params={
            "type": "object",
            "properties": {"book_id": {"type": "string"}},
            "required": ["book_id"],
        },
        preconditions=[
            Invariant("book exists", lambda ctx, p: p["book_id"] in ctx.services["db"].books),
        ],
        effects=["book", "catalog_index", "shelf"],
        reference_coverage=[
            Cascade("catalog_index.book_id", "delete entries"),
            Cascade("shelf.book_ids", "remove membership"),
        ],
        postconditions=[
            Invariant("no index references the book", lambda ctx, p: ctx.services["db"].no_index_references_to_book(p["book_id"])),
            Invariant("no shelf lists the book", lambda ctx, p: ctx.services["db"].no_shelf_lists(p["book_id"])),
        ],
        transaction_boundary="book + catalog_index + shelf",
        diff="book removed, index entries removed, shelves updated",
        plan=_plan_delete_book,
        registry=reg,
    )
    def delete_book(ctx, params):
        ctx.services["db"].delete_book(params["book_id"])
        return {"deleted": params["book_id"]}

    return reg


def build_runtime(db: LibraryDB) -> OperationRuntime:
    reg = OperationRegistry()
    register_operations(reg)
    return OperationRuntime(reg, snapshotter=LibrarySnapshotter(db))
