# Concepts

The vocabulary of the domain ops agent. Read this before defining operations.

- [Biological levels](#biological-levels)
- [The Operation contract](#the-operation-contract)
- [The Operation Manifest](#the-operation-manifest)
- [The approval lifecycle](#the-approval-lifecycle)
- [Durable operation identity](#durable-operation-identity)
- [Transports](#transports)
- [The domain map](#the-domain-map)
- [How the discipline reaches the agent](#how-the-discipline-reaches-the-agent)

---

## Biological levels

Levels are a thinking tool for sizing a change and deciding who may make it.
They are a **convention**, not a class hierarchy.

| Level | What it is | The agent's access | Guarantee |
|-------|------------|--------------------|-----------|
| **Cell** | one entity / one row | none — internal only | — |
| **Tissue** | a coupled set that must change together | only as one atomic operation | transaction |
| **Organ** | an aggregate root with invariants | via domain operations | pre/post invariants |
| **Organ system** | coordination across organs | via domain operations | full reference coverage |
| **Human** | application policy | enforced at the boundary | final gate |

The rule that carries the whole philosophy: **the agent's tools are
tissue-, organ-, and organ-system-level operations — never cell-level CRUD.**

## The Operation contract

Every valid operation the agent may call declares the following. This is the
minimum; a domain may add fields.

| Field | Meaning |
|-------|---------|
| `name` | Stable operation identifier (the durable identity). |
| `version` | Integer. Bump when the contract changes. |
| `level` | `tissue` \| `organ` \| `organ_system`. |
| `description` | One paragraph the model reads to choose the operation. |
| `params` | JSON-schema for the only values the model supplies. |
| `preconditions` | Invariants that must hold before the operation runs. |
| `effects` | The tissues/organs the operation touches. |
| `reference_coverage` | The coupled references it updates, and how it finds them. |
| `diff` | How the before/after change is produced for approval. |
| `postconditions` | Machine-checked assertions evaluated after apply. |
| `transaction_boundary` | What commits together. |
| `reversibility` | How the operation is reverted (usually: restore a snapshot). |

Two functions implement the contract:

```
plan(params)  ->  { diff, effects, reference_coverage, verification_plan }
apply(params) ->  { result, verification }
```

`plan` performs no mutation. `apply` runs only after approval.

## The Operation Manifest

The manifest is the **contract that survives decoupling**. It is the
machine-readable form of the Operation contract, and it is the source of
truth for what the agent may call and what each call guarantees.

Derive it from code (decorators/annotations) so it cannot drift from the
implementation:

```
@operation(
    name="rename_author",
    version=1,
    level="organ_system",
    reference_coverage=["book.author_id", "catalog_index.author_name"],
)
def rename_author(ctx, params): ...
```

The manifest is then produced by introspection. See
`skills/publish-operation-manifest` and `docs/WIRE_CONTRACT.md` for the exact
shape.

**The manifest is non-optional.** An operation exposed to the agent without a
manifest is not exposed correctly — the agent would lose the level, the
invariants, and the reference coverage that make the discipline real.

## The approval lifecycle

```
queued  ->  approved  ->  applied  ->  verified
                  \                      |
                   ->  rejected          ->  revertible
```

- **queued** — `plan` produced a diff; nothing has changed. Persist
  `{name, version, params}` (the durable identity) plus the diff.
- **approved** — a human selected the operation(s). Snapshot is taken.
- **applied** — `apply` executed inside its transaction.
- **verified** — postconditions passed. A failure is reported honestly and
  the change remains revertible.
- **rejected** — nothing applied.
- **revertible** — restoring the snapshot returns the domain to its
  pre-operation state.

The agent orchestrates this lifecycle. The operation enforces integrity.

## Durable operation identity

Approvals persist `{name, version, params}`, never a tool-call index or a
prompt. At approval time the operation is resolved from the registry by
`name` and `version`. This means:

- The model-facing description can change without invalidating in-flight
  approvals.
- An approval recorded today can be replayed and audited later.
- Bumping `version` is an explicit, reviewable contract change.

## Transports

The manifest and the `plan`/`apply` contract are transport-agnostic.

| | In-process | Remote |
|---|---|---|
| Operation | a callable in the agent process | an HTTP endpoint |
| Discovery | registry imported at startup | `GET /operations` |
| Plan | direct call | `POST /operations/{name}/plan` |
| Apply | direct call | `POST /operations/{name}/apply` |
| Enforcement | in the operation function | in the operation service |
| Good when | single app, low ceremony | independent deployment, reuse |

The agent's orchestration (approval, snapshot, verify, revert) is identical
in both. The enforcement always lives at the operation boundary.

## The domain map

The domain map is the human/AI-readable view of the domain's levels and
operations. It answers: *what are the organs, what operations exist at each
level, and what does each operation move with it?*

Generate it from the manifests — group operations by `level`, and show each
operation's `effects` and `reference_coverage`. It is the answer to "what do
the organism-level operations do?"

## How the discipline reaches the agent

Three layers, three jobs:

1. **Manifests → generated tools.** *What* the agent can call, and the
   level/guarantees. The discipline is in the schema the model sees.
2. **Domain map.** *How* the pieces relate: organs, operations, coupling.
3. **Skills + `AGENTS.md`.** *Why*: how to reason about levels, when to
   prefer an organ-system operation, and why reference coverage matters.

None of these is prose-only. The first is machine-readable and generated; the
second is generated from the first; the third teaches the reasoning that the
first two assume.
