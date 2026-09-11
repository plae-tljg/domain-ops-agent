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

## Status and roadmap

**v0 (this repo): documentation + `AGENTS.md` + skills.** No runtime code.

Later phases:

- **v1** — thin interfaces (`Operation`, `Invariant`, `Cascade`, `UnitOfWork`,
  `OperationManifest`) + decorators + transport adapters.
- **v2** — reference `library-catalog` domain + in-process and remote
  examples + a reference operation-service skeleton.
- **v3** — wire-contract implementation + an optional minimal approval UI.

## License

MIT (see `LICENSE`).
