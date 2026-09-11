# Domain Ops Agent

> A kit for building AI agents whose **action space is a domain's valid
> operations** — transactional, invariant-preserving, approval-gated, and
> verifiable — instead of the raw rows underneath them.

*(Working title. The repo is intentionally a portable, adaptable kit, not a
pip-installable framework.)*

## The one-sentence thesis

A general coding agent sees a change as an **action** (write a file, call an
endpoint). A domain ops agent sees a change as an **invariant set** — a group
of coupled records across several tables that must move together or not at
all. This kit is how you give an agent that second view.

## Who this is for

You are building an agent that operates on a system where **data is coupled
across tables** and **partial changes are invalid**: renaming an entity and
forgetting everything that references it, applying half of a migration,
leaving a dangling foreign key. Examples: ERP, healthcare, finance, telecom
callflows, catalog/inventory, bioinformatics.

If your agent only edits documents or makes independent API calls, you do not
need this. The discipline is overhead where there are no invariants.

## How to use this repo

This is an **adaptation kit**. You do not `pip install` it. You point your
coding agent (opencode, Claude Code, Codex, …) at this repo and ask it to
port the discipline into your project.

1. Read `AGENTS.md` — the operating rules your agent must follow.
2. Read `docs/CONCEPTS.md` — the vocabulary: levels, the Operation contract,
   the Operation Manifest.
3. Follow `docs/PORTING.md` — the step-by-step playbook, worked through a
   self-contained library/catalog example.
4. Load the skills in `skills/` as your agent works (see below).

## Wiring the skills

Each directory under `skills/` is an [Agent Skill](https://code.claude.com/docs/en/skills)
— a `SKILL.md` with frontmatter and a focused procedure.

- **opencode**: copy/symlink `skills/*` into `.opencode/skills/`.
- **Claude Code**: copy/symlink into `.claude/skills/` (or `~/.claude/skills/`).
- **Codex / others**: include the relevant `SKILL.md` in the agent's context,
  or paste it into the task prompt.

They are plain Markdown; any agent that can read files can use them.

## Repo map

| Path | What it is |
|------|------------|
| `MANIFESTO.md` | The philosophy: why decoupling the agent from the domain fails. |
| `AGENTS.md` | Operating rules + porting workflow for the coder's AI. |
| `docs/CONCEPTS.md` | Levels, the Operation contract, the Operation Manifest, the approval lifecycle. |
| `docs/PORTING.md` | Numbered playbook over a library/catalog domain; in-process and service paths. |
| `docs/WIRE_CONTRACT.md` | The transport-agnostic manifest, plan/apply, and event shapes. |
| `skills/` | Focused procedures the coder's AI loads while porting. |

## The three load-bearing ideas

1. **Valid operations are the action space.** The agent may call tissue-,
   organ-, and organ-system-level operations only — never cellular CRUD. The
   model chooses among operations that are already transactional and
   invariant-preserving.
2. **The Operation Manifest is the contract that survives decoupling.**
   Derived from code decorators, it declares the level, invariants, reference
   coverage, transaction boundary, and verification. Agent tools are
   *generated* from it, so the discipline is literally in the schema. A bare
   API without a manifest is disallowed.
3. **Two transports, one contract.** In-process (a callable) and remote
   (`GET /operations` + `POST /operations/{name}/plan|apply`) share the same
   manifest and the same `plan → approve → apply → verify` lifecycle.

## Using the core

```python
from domain_ops_agent import (
    Invariant, OperationRegistry, OperationRuntime, OperationContext, operation,
)

registry = OperationRegistry()

@operation(
    name="rename_author",
    version=1,
    level="organ_system",
    description="Rename an author and rewrite every denormalized copy.",
    params={"type": "object", "properties": {"author_id": {"type": "string"},
                                             "new_name": {"type": "string"}},
            "required": ["author_id", "new_name"]},
    preconditions=[Invariant("author exists", lambda ctx, p: p["author_id"] in ctx.services["db"].authors)],
    postconditions=[Invariant("index matches", lambda ctx, p: ctx.services["db"].index_names_match(p["author_id"]))],
    reference_coverage=[("catalog_index.author_name", "rewrite")],
    transaction_boundary="author + catalog_index",
    registry=registry,
)
def rename_author(ctx: OperationContext, params: dict):
    db = ctx.services["db"]
    db.rename_author(params["author_id"], params["new_name"])
    return {"renamed": params["author_id"]}

runtime = OperationRuntime(registry)

plan = runtime.plan("rename_author", {"author_id": "a1", "new_name": "Ada"})  # writes nothing
result = runtime.apply(plan.plan_id)                                          # after approval
assert result.verification.ok
runtime.revert(result.revert_token)                                           # restore
```

The same contract runs behind an API via `RemoteOperationClient`
(`GET /operations`, `POST /operations/{name}/plan|apply`).

## Examples

The `examples/` directory has a runnable **library/catalog** domain that
demonstrates a cross-table cascade (`rename_author`, `merge_authors`,
`delete_book`).

```bash
pip install -e .            # or run with PYTHONPATH=src

# in-process lifecycle: plan -> apply -> verify -> revert
python examples/library_catalog/demo.py

# remote transport: a stdlib operation service + the HTTP client
python examples/service/service.py        # serve on :8765 (approval UI at /)
python examples/service/remote_demo.py    # drives it end to end
```

With the service running, open `http://127.0.0.1:8765/` for the minimal
approval UI: pick an operation, plan, review the diff, approve, see the
verification, and revert. It is plain HTML/JS with no build step — copy it as
a starting point for your own review surface.

## Status and roadmap

- **v0 — documentation + `AGENTS.md` + skills.** Done.
- **v1 — domain-neutral core.** Done: `Operation`, `Invariant`, `Cascade`,
  `UnitOfWork` (transaction seam), `OperationManifest`, the `@operation`
  decorator, the plan/apply/verify runtime, and in-process + remote transport
  adapters. See `src/domain_ops_agent/` and `tests/`.
- **v2 — reference domain + examples.** Done: a runnable `library-catalog`
  domain (`examples/library_catalog/`) with three cascade operations, an
  in-process demo, a stdlib operation service (`examples/service/service.py`),
  and a remote-transport demo.
- **v3 — optional minimal approval UI.** Done: a plain HTML/JS review surface
  at `examples/approval_ui/index.html`, served by the operation service at `/`,
  plus a `POST /revert` endpoint. No build step; copy it as a starting point.

## License

MIT (see `LICENSE`).
