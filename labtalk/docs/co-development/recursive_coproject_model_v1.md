# The Recursive Co-development Model

Status: Architectural narrative  
Version: 1  
Date: 2026-07-11

## Definition

Co-development does not mean that an engine is built first and documented
later. x64base, DotTalk++, and their documentation infrastructure are developed
as interdependent parts of one system:

- **x64base is the stateful database engine**: tables, fields, records, memos,
  indexes, relations, work areas, buffers, validation, and storage lifecycles.
- **DotTalk++ is the engine's executable language and observation surface**: it
  names operations, invokes engine behavior, exposes state, runs DotScript, and
  provides the command boundary used by people, tests, GUIs, and automation.
- **HELP, messages, metadata, contracts, SelfDoc, and MDO are the system's
  explanatory and verification structure**: they preserve what operations are
  called, how they are used, what they mutate, what status they have, and which
  evidence supports them.

The documentation layer is therefore not merely a report about the engine. Its
contracts, registrations, HELP identities, status records, and validation gaps
actively shape implementation work. Runtime and source remain authoritative,
but documentation completeness is itself an engineering test.

This is recursion in the engineering sense: engine and command work produce
evidence; the documentation system turns that evidence into structured
knowledge; review of that knowledge finds missing or contradictory behavior;
those findings become inputs to the next engine, command, metadata, and proof
pass.

## The engine/runtime/documentation triad

| Layer | Primary responsibility | Co-development dependency |
| --- | --- | --- |
| x64base engine | Own database state and storage behavior. | Must expose stable concepts, lifecycle hooks, validation state, and observable outcomes. |
| DotTalk++ runtime | Name, execute, script, and inspect engine operations. | Commands require registration, HELP identity, contracts, messages, status, and proof paths. |
| Documentation system | Explain, inventory, crosswalk, validate, preserve, and publish. | Missing documentation reveals missing contracts, unstable names, hidden mutation boundaries, or insufficient runtime evidence. |

None of these layers is a substitute for another. Together they make the
system inspectable, teachable, testable, and increasingly self-describing.

## Three primary coproject systems

1. **x64base engine and DotTalk++ runtime** - a tightly coupled engine/language
   pair. x64base supplies state and behavior; DotTalk++ supplies the readable
   command, scripting, inspection, and automation surface over that behavior.
   Their source and captured runtime evidence are primary technical truth.
2. **Embedded documentation and Laboratory Campus** - HELP, messages,
   metadata, contracts, SelfDoc, and MDO provide collection, validation,
   provenance, proof preservation, diagrams, datasets, cases, labs, and lessons.
3. **Public documentation and website systems** - reviewed manuals,
   x64base.com, and dottalkpp.com. Publication is a consumer and diagnostic
   surface, not an independent source of engine truth.

## The websites are development instruments

The websites have separate but cooperating responsibilities:

- **x64base.com is the primary ecosystem website and public integration
  surface.** It must reconcile the engine, DotTalk++, product status,
  architecture, Laboratory Campus, evidence, development lanes, downloads, and
  governance into one coherent public model.
- **dottalkpp.com is the deeper documentation and artifact room.** It provides
  space for manuals, DotScript material, generated references, relationship
  views, larger reviewed artifacts, and developer-facing detail that should not
  overwhelm the primary site.

Their role is active rather than ornamental. A route that cannot be populated
from governed evidence, a command family that cannot be organized coherently,
an orphan diagram, a broken cross-site relationship, or contradictory status
copy is a development finding. Those findings return through MDO and SelfDoc to
the responsible metadata, HELP, source, test, manual, or site lane.

The websites therefore test whether the system can explain itself at two
scales: x64base.com tests ecosystem coherence; dottalkpp.com tests documentary
depth and artifact continuity. Neither site can redefine runtime truth, but
both can expose where runtime truth is incomplete, inaccessible, or poorly
structured.

## Recursive loop

```text
x64base state and storage behavior
    -> DotTalk++ commands, scripts, inspection, and runtime evidence
    -> HELP + messages + registrations + usage/mutation contracts
    -> metadata normalization + SelfDoc preservation + MDO review
    -> manuals + diagrams + Laboratory Campus lessons + public pages
    -> review exposes drift, missing contracts, hidden behavior, or weak proof
    -> findings return to x64base, DotTalk++, metadata, and tests
    -> the next pass strengthens both behavior and explanation
```

The loop is controlled by provenance and review gates. Website prose cannot
silently become engine truth, and generated material cannot promote itself.

## AI collaborators are part of the coproject

The human maintainer, Claude, Codex, and other AI systems are participants in
the same co-development loop. They are not independent authorities, and access
to tools does not grant permission to act. Collaboration stays coherent by
putting one bounded task through one evidence lens at a time.

The AI-facing information layer therefore has an engineering purpose beyond
human education. Repo-local authority seeds, contracts, risk classifications,
proof requirements, task context, and session closeouts are controls for
predictable collaborator failure modes: trusting stale descriptions, cleaning
valid work, inventing syntax, broadening scope, or treating a plausible result
as proof. These controls reduce risk; they do not make an AI self-authorizing or
infallible. Maintainer review remains part of the system.

This adds another recursive path:

```text
maintainer intent + bounded task
    -> AI reads authority, contracts, current state, and relevant evidence
    -> proposed or authorized work produces inspectable changes and proof
    -> closeout records what actually happened and what remains open
    -> the next human or AI resumes from the governed record
    -> observed collaborator failures improve the portal's controls
```

## Convergent refinement

The project develops like a reusable sculpture: add structure where evidence
shows a missing capability, remove structure where it duplicates or distorts,
and continue until implementation, explanation, and teaching surfaces describe
the same supported shape. Git and reproducible generation make this both
additive and subtractive rather than an irreversible carving process.

The simplifying axiom is not that the documentation tree must be small. It is
that descriptions can drift from the systems they describe. The many artifacts
are justified only when they apply that one axiom at a distinct boundary. When
two artifacts enforce the same boundary without adding evidence, ownership, or
recovery value, consolidation is the correct refinement.

## What documentation changes in development

The documentation system exerts concrete pressure on implementation:

- a command without a stable registration and HELP identity is incomplete;
- a mutator without usage, mutation, risk, stale, and dirty semantics is
  incomplete;
- an engine feature without an observable command/API path is difficult to
  teach or prove;
- a public claim without source or runtime provenance is blocked;
- contradictory HELP, metadata, and behavior become a drift finding;
- a missing failure transcript or canary becomes a proof requirement;
- manual and website organization expose gaps in the engine's conceptual model.

Conversely, the engine constrains documentation: public prose cannot promise a
transaction, index, field type, API, or command behavior that source and runtime
do not support. This bidirectional constraint is the core of co-development.

## LabTalk is broader than an executable

The Laboratory Campus, with LabTalk retained as its project and historical
name, is a hybrid collaboration layer. It contains implemented components,
developing labs, datasets, runtime demonstrations, help systems, GUI and portal
experiments, planning material, and proof artifacts. Its public repository
boundary may be incomplete without making the working local coproject empty.

## Governing doctrine

> Runtime proves, source defines, HELP explains, metadata organizes, and
> SelfDoc preserves.

The website publishes reviewed derivatives of that chain. Review then recurses
back into the system, making documentation an active engineering instrument
rather than an after-the-fact report.

## Boundaries

- Runtime and source remain authoritative for implementation claims.
- SelfDoc and metadata preserve provenance rather than manufacturing proof.
- Laboratory Campus may contain existing, developing, planned, and experimental
  work, but each item must state its status.
- Website review may identify a defect or omission; it cannot repair the source
  merely by changing public prose.
- Manual-to-website and website-to-manual movement must follow the documented
  simplex and duplex publication gates.

## Public derivative

The website page derived from this source should link onward to the SelfDoc feed
pipeline, website publication rules, Laboratory Campus overview, and important
documents index.
