---
name: map-domain-levels
description: Assign a domain's entities and intended changes to the biological levels (cell, tissue, organ, organ-system, human) before defining any operation.
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Map Domain Levels

Produce the domain map that every later step depends on. Do this before
writing any operation.

## Procedure

1. **Inventory the entities.** List every table/aggregate in the domain and
   its key columns. Note which columns are foreign keys or denormalized
   copies of other entities.

2. **Find the coupled sets.** A tissue is a set of records that must change
   together to stay coherent (an entity plus its owned children, or a record
   plus its denormalized copies).

3. **Name the organs.** An organ is an aggregate root with invariants —
   statements that must always be true about the coupled set.

4. **Identify the organ systems.** Organ-system operations coordinate across
   organs: rename, merge, move, collapse, delete-with-cascade.

5. **Record the human level.** Who is allowed to perform which operation, and
   which need explicit approval.

6. **Write the map** into the project (e.g. `docs/DOMAIN.md`).

## Output

A table with one row per entity/operation:

| Level | Member | Invariant or role |
|-------|--------|-------------------|
| Cell | `book` row | — |
| Tissue | `book` + its `catalog_index` rows | index entries point to a live book |
| Organ | the catalog | every book has a live author |
| Organ system | `merge_authors` | no reference to the source remains |
| Human | librarian role | merges over N books require approval |

## Checklist

- [ ] Every entity assigned a level.
- [ ] Every invariant stated as a checkable sentence.
- [ ] Every cross-organ change named as an organ-system operation.
- [ ] The approval policy for each mutating operation recorded.
