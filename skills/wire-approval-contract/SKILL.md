---
name: wire-approval-contract
description: Route mutations through plan, human approval, apply, and revert, persisting durable operation identity.
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Wire Approval Contract

The agent never applies a mutation directly. It plans, a human approves, then
it applies. The approval is stored as a durable operation identity so it can
be replayed and audited.

## Procedure

1. **Plan** — produce the diff and effects; write nothing.

   ```python
   def plan_rename_author(ctx, params):
       return {
           "diff": compute_diff(ctx, "rename_author", params),
           "effects": ["author", "catalog_index"],
           "reference_coverage": ["catalog_index.author_name"],
           "verification_plan": ["all index names match author.name"],
       }
   ```

2. **Persist the durable identity** `{name, version, params}` with the plan.
   Resolve the operation by `name` and `version` at approval time.

3. **Emit `plan_pending`** with the diff so a human can review.

4. **Apply only after approval**, inside the transaction, after a snapshot.

5. **Emit `plan_result`** with the status and verification outcome.

6. **Support reject** (nothing applied) and **revert** (restore the snapshot).

## Checklist

- [ ] Plan writes nothing.
- [ ] `{name, version, params}` persisted for every approval.
- [ ] Apply runs only after explicit approval.
- [ ] Snapshot taken before apply.
- [ ] Reject leaves the domain unchanged; revert restores the snapshot.
- [ ] `status` persisted with the result (`queued`, `done`, `failed`, ...).
