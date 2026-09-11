# AGENTS.md — Operating Rules for the Coder's AI

You are porting the **domain ops agent** discipline into a real project.
Read this file first, then `docs/CONCEPTS.md`, then work through
`docs/PORTING.md`. Load the skills in `skills/` as you go.

The project you are editing is the **domain**; this kit is the **discipline**.
Your job is to express the domain's valid operations as the agent's action
space.

## Non-negotiables

These are structural. They are what makes the result correct-by-construction.

1. **Expose valid domain operations as tools.** The agent's tool surface is
   the set of tissue-, organ-, and organ-system-level operations you define.
   Each operation is one transactional change.

2. **Every mutation declares its full contract.** An operation carries its
   level, parameters, preconditions, effects, reference coverage, diff,
   postconditions, transaction boundary, and reversibility. An operation
   without these is not finished.

3. **Enumerate references before a structural change.** Before renaming,
   moving, collapsing, or deleting an entity, list every table, field, index,
   cache, and denormalized copy that points at it, and repoint all of them in
   the same transaction.

4. **One transaction per operation.** All writes an operation performs commit
   together or roll back together. The transaction boundary is the operation,
   not the individual write.

5. **Route mutations through the approval contract.** An operation first
   produces a plan (the diff and its effects); a human approves; then it
   applies. The agent never applies a mutation directly.

6. **Verify after apply.** Every operation declares postconditions and checks
   them after execution. Surface failures honestly.

7. **Keep the manifest the single source of truth.** Derive the agent's tools
   from the Operation Manifest. When the contract changes, bump the operation
   version.

8. **Enforce at the operation boundary.** Integrity lives in the operation
   (in-process function or remote service), never in the model or the prompt.

9. **Snapshot before the first mutation.** Each operation is revertible to its
   pre-change state.

10. **Map the domain before writing any operation.** Assign every entity and
    every intended change to a biological level first.

## The porting workflow

Work in this order. Each step has a skill in `skills/`.

1. **Map the domain to levels** — `skills/map-domain-levels`.
   Inventory entities and coupled sets; assign cell / tissue / organ /
   organ-system / human. Produce a domain map.

2. **Enumerate references** — `skills/enumerate-references`.
   For each entity that can be renamed/moved/deleted, list everything that
   points at it.

3. **Define valid operations** — `skills/define-valid-operations`.
   Turn each intended change into an operation with the full contract.
   The agent's tools come from these.

4. **Publish the manifest** — `skills/publish-operation-manifest`.
   Derive the machine-readable manifest from the operation definitions so
   contract and implementation cannot drift.

5. **Wire the transaction boundary** — `skills/wire-transaction-boundary`.
   Make each operation atomic.

6. **Wire the approval contract** — `skills/wire-approval-contract`.
   Plan → approve → apply → revert, with durable operation identity.

7. **Wire verification** — `skills/verify-invariants`.
   Assert preconditions and postconditions; report honestly.

## Choosing a transport

Both transports share the same manifest and the same lifecycle. Choose by
operational context, not by fashion.

- **In-process** — operations are functions in the same process as the agent.
  Simplest to build and run; no extra service. Good default for a single
  application.
- **Remote** — operations live in a service that publishes `GET /operations`
  and `POST /operations/{name}/plan|apply`. More decoupled and independently
  deployable; more operational weight.

Document your choice in the project. The operation contract does not change.

## What good looks like

- A rename of any entity updates every reference in one transaction, and the
  agent cannot do it any other way.
- Every mutating tool is a domain operation with a manifest, an approval
  plan, and a verification step.
- The agent's tool list is generated from manifests, not hand-written.
- A reader can tell, from the manifest alone, how big a change is, what moves
  with it, and who decides.

## Style for this repo's own docs and skills

State positive principles. Describe the behavior you want rather than naming
what to avoid. Prefer one home per concept, and cross-link instead of
duplicating.
