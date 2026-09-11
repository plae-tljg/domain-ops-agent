# Manifesto

## The problem with action-shaped agents

A general coding agent lives in a world of actions: write a file, run a
command, call an endpoint. Each action is judged on its own, and correctness
is discovered *after the fact* — run it, observe the result, fix what broke.

That model is fine when actions are independent. It breaks down when data is
**coupled**. Consider renaming an entity:

- You change the entity's identifier.
- Every table that references it now points at an identifier that no longer
  exists.
- Every cached name, denormalized copy, and index entry is stale.

An action-shaped agent will happily perform the first step and stop, because
nothing in its world says "these four writes are one change." It will then
*test*, discover the breakage, and patch it — if it notices at all.

## Change is an invariant set, not an action

The insight is old and belongs to databases: a transaction is a group of
writes that either all happen or none do, because the database's integrity
depends on them being simultaneous. We take that idea and make it the
**first principle of the agent's execution model**.

> One agent change = one set of coupled records (across tables) that must
> move together for the domain to remain valid.

The agent never composes that set itself. It chooses from **operations that
already encode it**. The operation is the transaction; the agent is the
chooser.

## Correct by construction, not by trial

Two ways to keep a system valid:

- **Trial-and-error**: let the agent act, then test and repair.
- **Correct-by-construction**: make the invalid action inexpressible.

This kit is the second. The agent's tools are not CRUD endpoints; they are
domain operations that carry their own preconditions, transaction boundary,
reference coverage, and postconditions. The model cannot express "rename the
identifier and forget the references," because no such operation exists.

The model still reasons, plans, and chooses — it just chooses inside a space
where every option is valid.

## The biological hierarchy

To talk about coupling we borrow a vocabulary from biology. It is a thinking
tool, not a class hierarchy.

| Level | What it is | Example |
|-------|------------|---------|
| **Cell** | one entity / one row | a `book` row |
| **Tissue** | a coupled set that must change together | a `book` and its `catalog_index` entries |
| **Organ** | an aggregate root with invariants | the catalog: every book has a live author, every index entry points to a live book |
| **Organ system** | coordination across organs | renaming an author and repointing every book and index entry |
| **Human** | application-level policy | who may rename; approval thresholds; whole-domain validation |

The levels exist so a person (and an AI) can answer three questions at a
glance: *how big is this change, what must move with it, and who decides?*

## Killing the decoupling

The usual way to give an agent domain knowledge is a document: here is the
API, here are the fields. The agent reads it and tries to call correctly.

That decoupling — agent on one side, domain knowledge as prose on the other —
is exactly what produces partial changes. Prose cannot enforce anything.

This kit re-couples them at the right seam: **domain knowledge becomes the
agent's action space.** The valid operations are the tools. The invariants
are the tool contracts. The discipline is not something the model is *told*;
it is the shape of what the model can *do*.

## The seam: contract vs implementation

Decoupling the *implementation* of operations from the agent is good — it
lets you keep a clean service layer, deploy it independently, and reuse it.
What must never be decoupled is the *contract*.

So every operation publishes an **Operation Manifest**: a machine-readable
description of its level, parameters, invariants, reference coverage,
transaction boundary, and verification. The manifest travels with the
operation whether it runs in-process or behind an API. The agent's tools are
generated from it.

- Implementation may be local or remote.
- The manifest is always shared.
- The agent always speaks the manifest.

## Two transports, one contract

The same operation can be a Python callable or an HTTP endpoint. The
lifecycle is identical either way:

```
plan(params)  ->  diff, effects, reference coverage, verification plan
   | approve
apply(params) ->  result
   | verify
revert        ->  restore the pre-change snapshot
```

In-process, the call is direct. Remotely, it is `GET /operations` plus
`POST /operations/{name}/plan|apply`. The agent orchestrates approval and
verification; the operation enforces integrity. The enforcement lives at the
operation boundary, never in the model.

## What this is not

- Not a general agent framework. The loop, tool calling, streaming, and
  subagents are commodity; this kit says nothing new about them.
- Not a replacement for your service layer. It is the discipline that turns
  your service layer into an agent's safe action space.
- Not a guarantee that the model reasons well. It is a guarantee that
  whatever the model chooses is a valid, transactional, auditable change.

## The product is the discipline

The technology here is not new — transactions, aggregates, and cascades are
decades old. What is new is packaging them as the *agent's execution model*
and shipping them as an adaptable kit rather than a dependency.

The value is not in the code. It is in the contract, the vocabulary, and the
skills that make a coder's AI build with the discipline. That is what this
repo exists to transmit.
