---
name: publish-operation-manifest
description: Derive a machine-readable Operation Manifest from code decorators and validate it, so the agent's tools and the implementation cannot drift.
license: MIT
compatibility: any agent that reads SKILL.md
metadata:
  kit: domain-ops-agent
  category: porting
---

# Publish Operation Manifest

The manifest is the contract that survives decoupling: it lets the operation
implementation live in-process or behind an API while the agent still sees
the level, invariants, and reference coverage. Derive it from code.

## Procedure

1. **Decorate operations** with their contract metadata:

   ```python
   @operation(
       name="rename_author",
       version=1,
       level="organ_system",
       description="Rename an author and rewrite every denormalized copy.",
       params={...},
       reference_coverage=["catalog_index.author_name"],
   )
   def rename_author(ctx, params): ...
   ```

2. **Generate the manifest set by introspection** at startup. Emit the shape
   in `docs/WIRE_CONTRACT.md`.

3. **Validate at startup:**
   - every operation has a manifest;
   - every `reference_coverage` entry names a real reference;
   - `name` is unique; `version` is a positive integer;
   - `params` is a valid JSON schema.

4. **Serve or expose the set** — `GET /operations` for remote transports, a
   registry import for in-process.

5. **Bump `version`** whenever the contract changes; keep the name stable.

## Checklist

- [ ] Manifests are derived, not hand-written.
- [ ] Startup validation runs and fails loudly on a bad manifest.
- [ ] The agent's tools are generated from the manifest set.
- [ ] Contract changes bump the version.
