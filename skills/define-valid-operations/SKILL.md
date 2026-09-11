---
name: define-valid-operations
description: Turn each intended domain change into an operation with the full contract (level, params, preconditions, effects, reference coverage, diff, postconditions, transaction boundary, reversibility).
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Define Valid Operations

An operation is one transactional, invariant-preserving change at the tissue,
organ, or organ-system level. The agent's tools come from these — never from
raw table CRUD.

## Procedure

1. **Start from a change**, not from a table. "Rename an author," not "update
   the author table."

2. **Assign the level** from the domain map (`skills/map-domain-levels`).

3. **Declare the params** — the only values the model supplies. Use a JSON
   schema. Never accept identity fields the host can inject.

4. **Write the preconditions** — invariants that must hold before running.

5. **Attach the reference coverage** from `skills/enumerate-references`.

6. **Specify the diff** — how the before/after change is produced for review.

7. **Write the postconditions** — checkable statements that must hold after.

8. **Name the transaction boundary** — what commits together.

9. **Name the reversibility** — usually "restore the pre-operation snapshot."

## Output

One contract per operation. See `docs/PORTING.md` Step 3 for worked
examples (`rename_author`, `merge_authors`, `delete_book`).

## Checklist

- [ ] The operation is named for a change, not a table.
- [ ] Level is tissue, organ, or organ-system.
- [ ] Params, preconditions, effects, reference coverage, diff,
      postconditions, transaction boundary, and reversibility are all present.
- [ ] The operation is the unit the human approves — not a single write.
