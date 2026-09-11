# Wire Contract

The transport-agnostic shapes shared by in-process and remote transports.
Any UI or transport can attach by speaking these.

- [Operation Manifest](#operation-manifest)
- [Registry](#registry)
- [Plan / Apply](#plan--apply)
- [Events](#events)
- [Statuses](#statuses)
- [Transport mapping](#transport-mapping)

---

## Operation Manifest

The machine-readable contract for one operation. Derived from the operation's
decorator/annotation.

```json
{
  "name": "rename_author",
  "version": 1,
  "level": "organ_system",
  "description": "Rename an author and repoint every book and index entry.",
  "params": {
    "type": "object",
    "properties": {
      "author_id": { "type": "string" },
      "new_name": { "type": "string" }
    },
    "required": ["author_id", "new_name"]
  },
  "preconditions": [
    "author exists",
    "new_name is non-empty and unique"
  ],
  "effects": ["author", "book", "catalog_index"],
  "reference_coverage": [
    { "reference": "book.author_id", "strategy": "update foreign key" },
    { "reference": "catalog_index.author_name", "strategy": "rewrite denormalized copy" }
  ],
  "diff": "before/after for author row, affected books, affected index entries",
  "postconditions": [
    "no book references a missing author",
    "no index entry references a missing book",
    "all rewritten names equal new_name"
  ],
  "transaction_boundary": "author + book + catalog_index in one transaction",
  "reversibility": "restore pre-operation snapshot"
}
```

A **manifest set** is the array of all manifests for a domain.

## Registry

Remote transports publish the manifest set:

```
GET /operations
->  { "operations": [ <OperationManifest>, ... ] }
```

In-process transports expose the same set from the registry imported at
startup. In both cases the agent generates its tools from this set.

## Plan / Apply

`plan` performs no mutation and returns the reviewable change. `apply` runs
only after approval.

```
POST /operations/{name}/plan
body:    { "params": { ... }, "version": 1 }
->  {
      "plan_id": "op_...",
      "operation": "rename_author",
      "version": 1,
      "params": { ... },
      "diff": {
        "before": { ... },
        "after":  { ... }
      },
      "effects": ["author", "book", "catalog_index"],
      "reference_coverage": [ ... ],
      "verification_plan": [ "no book references a missing author", ... ],
      "impact": { "rows_changed": 37 }
    }

POST /operations/{name}/apply
body:    { "plan_id": "op_...", "params": { ... }, "version": 1 }
->  {
      "result": "applied",
      "verification": {
        "ok": true,
        "checks": [ { "assertion": "...", "passed": true } ]
      },
      "revert_token": "snapshot_..."
    }
```

In-process, `plan` and `apply` are direct function calls with the same shapes.

## Events

The agent emits these while orchestrating. They are transport-agnostic; a UI
subscribes to render and to collect approvals.

| Event | Payload |
|-------|---------|
| `tool_call` | `{ call_id, name, level, mutating, params }` |
| `tool_result` | `{ call_id, status, content, details }` |
| `plan_pending` | `{ plan_id, operation, version, params, diff, effects, reference_coverage, verification_plan }` |
| `plan_result` | `{ plan_id, status, verification, revert_token }` |
| `progress` | `{ phase, done, total }` |
| `error` | `{ message }` |

`tool_call.mutating` is `true` for operations that go through the approval
lifecycle. The UI colors those for review.

## Statuses

Operation and tool results use one status vocabulary:

| Status | Meaning |
|--------|---------|
| `done` | Completed successfully. |
| `noop` | Ran correctly, nothing changed. |
| `queued` | A plan is awaiting approval; nothing applied. |
| `failed` | Did not complete; nothing applied. |
| `cancelled` | Interrupted; partial work reverted. |

Persist `status` with the result so a reloaded session shows a queued change
as *awaiting approval*, never as success.

## Transport mapping

| Concept | In-process | Remote |
|---------|------------|--------|
| Manifest set | registry import | `GET /operations` |
| Plan | `operation.plan(params)` | `POST /operations/{name}/plan` |
| Apply | `operation.apply(params)` | `POST /operations/{name}/apply` |
| Events | callback / async iterator | SSE stream |
| Enforcement | operation function | operation service |
| Snapshot / revert | host snapshot provider | service + host snapshot provider |

The contract does not change between transports; only the call mechanism does.
