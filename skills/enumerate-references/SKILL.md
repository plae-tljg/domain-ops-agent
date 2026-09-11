---
name: enumerate-references
description: List every table, field, index, cache, and denormalized copy that points at an entity, so structural changes can repoint all of them in one transaction.
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Enumerate References

For every entity that can be renamed, merged, moved, or deleted, find
everything that depends on it. This list becomes the operation's
`reference_coverage` — the answer to "rename the id but not the other things
using it."

## Procedure

1. **Search the schema** for the entity's key: foreign keys, join tables,
   array columns, JSON fields, and any column whose name suggests it.

2. **Search the codebase** for the entity's key and name: queries, caches,
   search indexes, denormalized copies, event payloads, and fixtures.

3. **Classify each reference:**
   - **foreign key** — repoint or cascade.
   - **denormalized copy** — rewrite.
   - **membership** (array/set) — add or remove.
   - **derived/cache** — invalidate or rebuild.

4. **Record the update strategy** for each reference.

## Output

| Reference | Kind | Update strategy |
|-----------|------|-----------------|
| `book.author_id` | foreign key | repoint on merge |
| `catalog_index.author_name` | denormalized copy | rewrite on rename |
| `shelf.book_ids` | membership | remove on delete |

## Checklist

- [ ] Every reference found by both schema search and code search.
- [ ] Each reference has a kind and an update strategy.
- [ ] Indirect references (through another entity) are followed.
- [ ] The list is attached to the relevant operations as `reference_coverage`.
