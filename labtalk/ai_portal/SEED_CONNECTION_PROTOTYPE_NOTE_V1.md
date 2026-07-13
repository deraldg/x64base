# AI Portal Seed Connection Prototype Note v1

Status: **Design-intended — prototype not yet selected**

## Identity

The AI Portal is not a portal through which students access an AI service.

It is a machine-facing orientation and context system through which an AI can
enter the x64base development environment as a development partner, understand
local authority and constraints quickly, and prepare safe, evidence-backed
work without depending on lost chat history.

The immediate work is **fast starts for AI**. Seeds are the durable units used
to carry project identity, authority, workflow, contracts, runtime learning,
safety gates, task recipes, and proof expectations into a new conversation.

## Future Connection Problem

Individual seeds are useful, but a growing pile of seeds would recreate the
same startup problem in a different form. A future prototype needs a simple but
clever way to connect only the seeds relevant to the current task.

The prototype should answer:

```text
What is the AI trying to do?
Which authority and project roots apply?
Which seeds are mandatory for this task?
Why was each seed selected?
What must be read or proved before action?
What context is missing or contradictory?
What readiness state has actually been reached?
Which SDLC owns the task, which lane is active, and what is the next gate?
```

## Smallest Useful Prototype

A first prototype should remain read-only and deterministic:

```text
task statement
-> match task/lane tags
-> follow explicit seed requirements
-> order mandatory first reads
-> explain each connection
-> produce a bounded fast-start packet
-> show missing context, conflicts, permissions, and readiness
```

It does not need autonomous planning, embeddings, a large UI, or a student
chat surface. A command-line or small local prototype that compiles an
inspectable packet from the registry would be enough to test the idea.

## Likely Connection Fields

The current registry can evolve toward a few explicit fields:

* `applies\_to`: task types, lanes, projects, or artifact kinds;
* `triggers`: words or structured intents that select the seed;
* `requires\_seeds`: prerequisite seed IDs;
* `authority`: why the seed may constrain the task;
* `packet\_priority`: ordering in the fast-start packet;
* `readiness\_requires`: evidence needed before action;
* `conflicts\_with`: combinations that require maintainer review;
* `produces`: readiness state, packet section, or proof expectation.
* `owning\_lifecycle`, `sdlc\_lane`, `truth\_state`, `proof\_state`, `risk\_class`,
and `next\_gate`: the maintained SDLC state carried through every connection.

The connector must follow explicit IDs and validation. It must not silently
invent relationships from prose and then treat them as authority.

## Boundary

This note records direction, not a completed architecture or permission to
implement autonomous execution. The prototype should first prove that it can
select a smaller, better fast-start context than a static reading list while
showing every connection and omission to the maintainer.
