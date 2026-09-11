"""An in-memory library/catalog domain.

Deliberately coupled so the cascade discipline is visible:

- ``book.author_id`` references ``author.id``
- ``catalog_index.book_id`` references ``book.id``
- ``catalog_index.author_name`` is a denormalized copy of ``author.name``
- ``shelf.book_ids`` references ``book.id``

A rename that updates ``author.name`` but not ``catalog_index.author_name`` is
a partial change — exactly what the operations here prevent.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List


class LibraryDB:
    def __init__(self) -> None:
        self.authors: Dict[str, Dict[str, Any]] = {}
        self.books: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, Dict[str, Any]] = {}
        self.shelves: Dict[str, Dict[str, Any]] = {}

    # -- helpers ---------------------------------------------------------

    def add_author(self, author_id: str, name: str) -> None:
        self.authors[author_id] = {"id": author_id, "name": name}

    def add_book(self, book_id: str, title: str, author_id: str) -> None:
        self.books[book_id] = {"id": book_id, "title": title, "author_id": author_id}
        self.index[f"idx_{book_id}"] = {
            "id": f"idx_{book_id}",
            "book_id": book_id,
            "author_name": self.authors[author_id]["name"],
            "title": title,
        }

    def add_shelf(self, shelf_id: str, book_ids: List[str]) -> None:
        self.shelves[shelf_id] = {"id": shelf_id, "book_ids": list(book_ids)}

    def books_of(self, author_id: str) -> List[Dict[str, Any]]:
        return [b for b in self.books.values() if b["author_id"] == author_id]

    def index_entries_of(self, author_id: str) -> List[Dict[str, Any]]:
        book_ids = {b["id"] for b in self.books_of(author_id)}
        return [e for e in self.index.values() if e["book_id"] in book_ids]

    # -- invariants the operations check ---------------------------------

    def index_names_match(self, author_id: str) -> bool:
        name = self.authors[author_id]["name"]
        return all(e["author_name"] == name for e in self.index_entries_of(author_id))

    def index_names_valid(self) -> bool:
        names = {a["name"] for a in self.authors.values()}
        return all(e["author_name"] in names for e in self.index.values())

    def no_book_references(self, author_id: str) -> bool:
        return not any(b["author_id"] == author_id for b in self.books.values())

    def no_index_references_to_book(self, book_id: str) -> bool:
        return not any(e["book_id"] == book_id for e in self.index.values())

    def no_shelf_lists(self, book_id: str) -> bool:
        return not any(book_id in s["book_ids"] for s in self.shelves.values())

    # -- mutations the operations perform --------------------------------

    def rename_author(self, author_id: str, new_name: str) -> None:
        self.authors[author_id]["name"] = new_name
        for entry in self.index_entries_of(author_id):
            entry["author_name"] = new_name

    def merge_authors(self, source_id: str, target_id: str) -> int:
        target_name = self.authors[target_id]["name"]
        moved = 0
        for book in self.books.values():
            if book["author_id"] == source_id:
                book["author_id"] = target_id
                moved += 1
        for entry in self.index.values():
            if entry["author_name"] == self.authors[source_id]["name"]:
                entry["author_name"] = target_name
        del self.authors[source_id]
        return moved

    def delete_book(self, book_id: str) -> None:
        self.books.pop(book_id, None)
        for idx_id in [i for i, e in self.index.items() if e["book_id"] == book_id]:
            del self.index[idx_id]
        for shelf in self.shelves.values():
            shelf["book_ids"] = [b for b in shelf["book_ids"] if b != book_id]


def seed() -> LibraryDB:
    db = LibraryDB()
    db.add_author("a1", "Ada Lovelace")
    db.add_author("a2", "Alan Turing")
    db.add_book("b1", "Notes on the Analytical Engine", "a1")
    db.add_book("b2", "On Computable Numbers", "a2")
    db.add_shelf("s1", ["b1", "b2"])
    return db


class LibrarySnapshotter:
    """A real snapshotter for the example: deep-copies the tables."""

    def __init__(self, db: LibraryDB) -> None:
        self.db = db
        self._snaps: Dict[str, Any] = {}
        self._seq = 0

    def snapshot(self, label: str) -> str:
        self._seq += 1
        token = f"{label}:{self._seq}"
        self._snaps[token] = copy.deepcopy(
            (self.db.authors, self.db.books, self.db.index, self.db.shelves)
        )
        return token

    def restore(self, token: str) -> None:
        authors, books, index, shelves = self._snaps[token]
        self.db.authors = copy.deepcopy(authors)
        self.db.books = copy.deepcopy(books)
        self.db.index = copy.deepcopy(index)
        self.db.shelves = copy.deepcopy(shelves)
