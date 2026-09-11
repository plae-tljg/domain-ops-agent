---
name: verify-invariants
description: Check an operation's preconditions before it runs and its postconditions after, and report the outcome honestly.
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Verify Invariants

Every operation declares checkable statements. Verify them before and after,
and surface the result. A failed check is information, not something to hide.

## Procedure

1. **Check preconditions** before planning. If one fails, refuse the
   operation with a clear message.

2. **Check postconditions** after apply:

   ```python
   def verify_rename_author(ctx, params):
       checks = [
           check("author.name == new_name", ...),
           check("all index names match author.name", ...),
       ]
       return {"ok": all(c.passed for c in checks), "checks": checks}
   ```

3. **Report honestly.** Include the failing assertion and the observed value.
   Keep the change revertible when a check fails.

4. **Include a verification plan in the diff** so the human sees what will be
   checked.

## Checklist

- [ ] Preconditions checked before planning.
- [ ] Postconditions checked after apply.
- [ ] Failures reported with the assertion and observed value.
- [ ] A failed postcondition leaves the change revertible.
- [ ] The verification plan is part of the reviewable diff.
