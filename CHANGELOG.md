# Changelog

## v1 — domain-neutral core

- `Operation`, `Invariant`, `Cascade`, `OperationManifest`, `OperationContext`.
- `@operation` decorator: define an operation, derive its manifest, register it.
- `OperationRegistry`: versioned lookup and manifest enumeration.
- `OperationRuntime`: the `plan -> approve -> apply -> verify -> revert`
  lifecycle, with precondition gating, snapshots, and event emission.
- Host seams as protocols: `PlanStore`, `Snapshotter`, `EventSink`,
  `TransactionManager`, with in-memory/no-op adapters.
- Transport adapters: `InProcessTransport` and `RemoteOperationClient`
  (manifest registry + `plan`/`apply` over HTTP).
- Tests for manifest derivation, registry versioning, the runtime lifecycle,
  and both transports.

## v0 — documentation kit

- `README`, `MANIFESTO`, `AGENTS.md`.
- `docs/CONCEPTS.md`, `docs/PORTING.md`, `docs/WIRE_CONTRACT.md`.
- Seven porting skills under `skills/`.
