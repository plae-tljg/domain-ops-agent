# Changelog

## v2 — reference domain + examples

- `examples/library_catalog/`: a runnable coupled domain (authors, books,
  catalog index, shelves) with `rename_author`, `merge_authors`, and
  `delete_book` — each transactional, reference-complete, and verified.
- `examples/library_catalog/demo.py`: the in-process lifecycle end to end.
- `examples/service/service.py`: a standard-library operation service serving
  `GET /operations` and `POST /operations/{name}/plan|apply`.
- `examples/service/remote_demo.py`: drives the service through
  `RemoteOperationClient`.
- Example tests for cascade coverage, revert, and precondition gating.

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
