# Porting Guide

A numbered playbook for porting the discipline into a project. Worked through
a self-contained **library/catalog** domain so the shapes are concrete.

Load the skill named at each step in `skills/`.

- [The example domain](#the-example-domain)
- [Step 1 — Map the domain to levels](#step-1--map-the-domain-to-levels)
- [Step 2 — Enumerate references](#step-2--enumerate-references)
- [Step 3 — Define valid operations](#step-3--define-valid-operations)
- [Step 4 — Publish manifests](#step-4--publish-manifests)
- [Step 5 — Wire the transaction boundary](#step-5--wire-the-transaction-boundary)
- [Step 6 — Wire the approval lifecycle](#step-6--wire-the-approval-lifecycle)
- [Step 7 — Wire verification](#step-7--wire-verification)
- [Step 8 — Generate the agent's tools](#step-8--generate-the-agents-tools)
- [Step 9 — Choose a transport](#step-9--choose-a-transport)
- [Checklist](#checklist)

---

## The example domain

A small library catalog:

| Table | Columns |
|-------|---------|
| `author` | `id`, `name` |
| `book` | `id`, `title`, `author_id` |
| `catalog_index` | `id`, `book_id`, `author_name`, `title` |
| `shelf` | `id`, `book_ids` (array) |

Coupling to notice:

- `book.author_id` references `author.id`.
- `catalog_index.book_id` references `book.id`.
- `catalog_index.author_name` is a **denormalized copy** of `author.name`.
- `shelf.book_ids` references `book.id`.

A rename that updates `author.name` but not `catalog_index.author_name` is a
partial change. That is the failure this kit prevents.

---

## Step 1 — Map the domain to levels

Skill: `skills/map-domain-levels`.

Assign every entity and intended change to a level.

| Level | In this domain |
|-------|----------------|
| Cell | an `author` row, a `book` row, an index row |
| Tissue | a `book` and its `catalog_index` entries |
| Organ | the catalog: every book has a live author; every index entry points to a live book; index names match authors |
| Organ system | `merge_authors` (repoint books + rewrite index + delete source); `delete_book` (cascade index + shelves) |
| Human | only the librarian role may merge/rename; merges affecting > N books need approval |

Write this table into the project (for example in `docs/DOMAIN.md`). It is the
domain map; later steps fill in operations.

---

## Step 2 — Enumerate references

Skill: `skills/enumerate-references`.

For each entity that can be renamed, merged, moved, or deleted, list
everything that points at it.

For `author`:

| Reference | Kind | Must update |
|-----------|------|-------------|
| `book.author_id` | foreign key | repoint on merge/delete |
| `catalog_index.author_name` | denormalized copy | rewrite on rename/merge |
| `shelf.book_ids` (via books) | indirect | follow when a book moves/deletes |

For `book`:

| Reference | Kind | Must update |
|-----------|------|-------------|
| `catalog_index.book_id` | foreign key | delete/rewrite index entries |
| `shelf.book_ids` | array membership | remove on delete |

This table is the operation's `reference_coverage`. It is the answer to
"rename the id but not the other things using it."

---

## Step 3 — Define valid operations

Skill: `skills/define-valid-operations`.

Turn each intended change into an operation with the full contract from
`docs/CONCEPTS.md`.

### `rename_author` (organ system)

```
name: rename_author
version: 1
level: organ_system
params: { author_id: string, new_name: string }
preconditions:
  - author exists
  - new_name is non-empty
  - new_name is not used by another author
effects: [author, catalog_index]
reference_coverage:
  - catalog_index.author_name: rewrite where book_id in (books of author)
diff: before/after of author row + affected index rows
postconditions:
  - author.name == new_name
  - every index row for the author's books has author_name == new_name
transaction_boundary: author + catalog_index
reversibility: restore pre-operation snapshot
```

### `merge_authors` (organ system)

```
name: merge_authors
version: 1
level: organ_system
params: { source_id: string, target_id: string }
preconditions:
  - source and target both exist
  - source != target
effects: [author, book, catalog_index]
reference_coverage:
  - book.author_id: repoint source -> target
  - catalog_index.author_name: rewrite to target.name
diff: books repointed + index rows rewritten + source row removed
postconditions:
  - no book references source
  - no index row names source
  - source author row is gone
transaction_boundary: author + book + catalog_index
reversibility: restore pre-operation snapshot
```

### `delete_book` (organ)

```
name: delete_book
version: 1
level: organ
params: { book_id: string }
preconditions: [book exists]
effects: [book, catalog_index, shelf]
reference_coverage:
  - catalog_index.book_id: delete entries
  - shelf.book_ids: remove the id
postconditions:
  - no index row references the book
  - no shelf lists the book
transaction_boundary: book + catalog_index + shelf
reversibility: restore pre-operation snapshot
```

Each of these is a tool the agent may call. Raw `UPDATE author SET name=...`
is not.

---

## Step 4 — Publish manifests

Skill: `skills/publish-operation-manifest`.

Define operations with a decorator so the manifest is derived, not
hand-written.

```python
@operation(
    name="rename_author",
    version=1,
    level="organ_system",
    description="Rename an author and rewrite every denormalized copy.",
    params={
        "type": "object",
        "properties": {
            "author_id": {"type": "string"},
            "new_name": {"type": "string"},
        },
        "required": ["author_id", "new_name"],
    },
    reference_coverage=["catalog_index.author_name"],
)
def rename_author(ctx, params):
    ...
```

The registry introspects decorators and produces the manifest set
(`docs/WIRE_CONTRACT.md`). The agent's tools are generated from this set.

Validate at startup: every operation has a manifest, and every declared
`reference_coverage` entry names a real reference from Step 2.

---

## Step 5 — Wire the transaction boundary

Skill: `skills/wire-transaction-boundary`.

Wrap the operation's writes in one transaction. In-process:

```python
def rename_author(ctx, params):
    with unit_of_work() as uow:
        author = uow.authors.get(params["author_id"])
        uow.authors.set_name(author.id, params["new_name"])
        uow.index.rewrite_author_name(author.id, params["new_name"])
    # committed together, or rolled back together
```

Remote: the operation service owns the transaction; the agent only calls
`plan`/`apply`.

---

## Step 6 — Wire the approval lifecycle

Skill: `skills/wire-approval-contract`.

`plan` returns the diff and writes nothing. `apply` runs after approval.
Persist `{name, version, params}`.

```python
def plan_rename_author(ctx, params):
    return {
        "diff": compute_diff(ctx, "rename_author", params),
        "effects": ["author", "catalog_index"],
        "reference_coverage": ["catalog_index.author_name"],
        "verification_plan": ["all index names match author.name"],
    }
```

The agent emits `plan_pending`; a human approves; the agent calls `apply`;
the agent emits `plan_result`. See `docs/WIRE_CONTRACT.md`.

---

## Step 7 — Wire verification

Skill: `skills/verify-invariants`.

Evaluate preconditions before, postconditions after. Report honestly.

```python
def verify_rename_author(ctx, params):
    checks = [
        check("author.name == new_name", ...),
        check("all index names match", ...),
    ]
    return {"ok": all(c.passed for c in checks), "checks": checks}
```

A failed check is surfaced to the user; the change stays revertible.

---

## Step 8 — Generate the agent's tools

Generate one tool per operation from its manifest. The tool description
includes the level and the reference coverage so the model sees the
discipline.

```python
for manifest in registry.manifests():
    register_tool(
        name=manifest["name"],
        description=f"[{manifest['level']}] {manifest['description']}",
        params=manifest["params"],
        plan=make_plan(manifest),
        apply=make_apply(manifest),
    )
```

The agent never receives a cell-level tool.

---

## Step 9 — Choose a transport

Document the choice; the contract does not change.

**In-process path** — operations are functions in the agent process.

- Simplest to build and run; no extra service.
- Enforcement is in the operation function.
- Good default for a single application.

**Service path** — operations live in a service.

- Publish `GET /operations`, `POST /operations/{name}/plan`, and
  `POST /operations/{name}/apply` (`docs/WIRE_CONTRACT.md`).
- The agent fetches manifests, generates tools, and orchestrates approval.
- Enforcement is in the service; the agent is a thin orchestrator.
- Good when the operation layer is shared or independently deployed.

---

## Checklist

- [ ] Domain map written; every entity and change assigned a level.
- [ ] References enumerated for every rename/merge/move/delete.
- [ ] Every mutating operation has the full contract.
- [ ] Manifests derived from decorators; validated at startup.
- [ ] Each operation is one transaction.
- [ ] Plan writes nothing; apply runs after approval.
- [ ] `{name, version, params}` persisted for every approval.
- [ ] Postconditions checked after apply; failures surfaced.
- [ ] Snapshot taken before the first mutation; revert works.
- [ ] Agent tools generated from manifests; no cell-level tools.
- [ ] Transport chosen and documented.
