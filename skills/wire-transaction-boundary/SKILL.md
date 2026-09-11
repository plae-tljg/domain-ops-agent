---
name: wire-transaction-boundary
description: Make each domain operation atomic so all of its writes commit together or roll back together.
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Wire Transaction Boundary

The transaction boundary is the operation, not the individual write. If any
write fails, the whole operation leaves the domain unchanged.

## Procedure

1. **Wrap all of an operation's writes in one unit of work.**

   ```python
   def rename_author(ctx, params):
       with unit_of_work() as uow:
           author = uow.authors.get(params["author_id"])
           uow.authors.set_name(author.id, params["new_name"])
           uow.index.rewrite_author_name(author.id, params["new_name"])
   ```

2. **Keep the boundary at the operation level.** Nested helpers share the
   same transaction; they do not open their own.

3. **Compute the plan without writing.** `plan` reads and diffs; only `apply`
   writes.

4. **For remote transports**, the operation service owns the transaction; the
   agent calls `plan`/`apply` and never opens a transaction itself.

5. **Take a snapshot before the first mutation** so the operation is
   revertible.

## Checklist

- [ ] One transaction per operation.
- [ ] Helpers join the operation's transaction.
- [ ] `plan` writes nothing.
- [ ] Snapshot taken before the first mutation.
- [ ] A failed write rolls back the entire operation.
