# Entities, and the Bridge: how work enters and crosses this system

- **Status**: doctrine, source-defined
- **Owner**: member.derald
- **Recorded**: 2026-07-27 (AIF-067), Cowork
- **Companions**: `AGENCY_MODEL_V1.md`, `AI_RUN_TRACEABILITY_CONTRACT_V1.md`,
  `labtalk/lessons/career/discovery_by_documentation_v0.md`

---

## Why this document exists

The practice was already being followed. It had never been stated, so it kept
being misread -- including, on the day this was written, by an AI partner who
described three deliberate zero-byte design files as unfinished work needing
cleanup. The correction was easy. The fact that the correction was NEEDED is the
argument for writing this down.

Two ideas, both from member.derald, both load-bearing:

> "0 byte commands, plugs, and prototypes help define the top level layer of our
> systems design."

> "Even unfinished, they are entities and can be tracked in the SDLC as they are
> onboarded into the system, and we just track their progression through our
> documentation process."

> "We build up (solid) and build down (empirical) until we build both ends of the
> bridge, build the span."

---

## 0. Declaring is the first act of building

> "Declaring something is the first step to making it real by defining it and
> then building it, testing it, proofing it and release etc."
> -- member.derald, 2026-07-27

This is the load-bearing sentence, and it should be read as a claim about
CAUSATION rather than about paperwork.

The common model treats documentation as downstream: build the thing, then
describe it. Under that model a zero-byte file is an empty gesture, and
documentation is a tax paid after the value is created. That model is why an
empty `app_army.cpp` reads as neglect to anyone encountering it cold.

The model here runs the other way:

```
declare -> define -> build -> test -> proof -> release
```

**Declaration is generative.** Naming the entity is what brings it into the
system; everything after is elaboration of something that now exists. The file
is not a note about future work, it is the work's first state.

This gives the project thesis its second reading, and the two are **equally
important** (member.derald, 2026-07-27). An earlier draft of this section called
the upstream reading "the strongest form", which was wrong -- and wrong in a way
this document should have caught, since it makes a hierarchy out of the two
directions section 3 says must meet:

| Reading | Direction | Documentation is | Answers |
|---|---|---|---|
| Declaration is generative | building **up** -- solid, deductive | **upstream**; the first act of making the thing | what is this supposed to be? |
| Documentation verifies | building **down** -- empirical, inductive | **downstream**; the record against which behaviour is checked | does it actually do that? |

Neither subsumes the other. A system with only the upstream half is an elegant
declaration nothing satisfies. A system with only the downstream half is a pile
of true observations describing whatever happened to get built. **The thesis is
the span**: documentation improves and proves the code because it both
originates the entity and later measures it, and the gap between those two is
where every defect this project has recorded actually lives.

Each stage's documentation is what makes the next stage possible:

| Stage | What it declares | What it makes possible |
|---|---|---|
| declare | this entity exists | a name to define against |
| define | what it is, its contract | an implementation to build against |
| build | behaviour | something to test |
| test | it does what was defined | evidence to proof |
| proof | observed, recorded, cited | a release that can be trusted |
| release | it is available | others build on it |

Skip the declaration and the later stages have nothing to be measured against --
which is exactly the failure the span defects in section 3 describe. You cannot
detect drift from a specification that was never written.

## 1. An entity exists before it works

The unit of tracking in this system is not a ticket, a branch, or a task. It is
an **entity** -- a named thing the design has decided should exist.

An entity can be created with no behaviour at all. `app_army.cpp` is 184 bytes
and does nothing; `edu_boyce_codd.cpp` is comments and nothing else. Both are
real entities. They occupy a name, a subsystem, a layer, and a place in the
census. Nothing about them is provisional except the code.

This is deliberate, and it is stronger than the alternatives:

| Way to record a planned thing | Survives refactor | In the census | Must be deliberately removed |
|---|---|---|---|
| TODO comment | sometimes | no | no |
| Backlog item | yes | no | no |
| **Zero-byte translation unit** | **yes** | **yes** | **yes** |

A file that exists is a claim the build itself carries. It cannot be lost in a
tracker migration, and deleting it is a visible act with an author.

**The names are not placeholders either.** `app_army`, `app_alcoa`, `app_paxon`
correspond exactly to `docs/cases/CASE_HIST_020` (Army/JUMPS),
`CASE_HIST_030` (Unisys/CODASYL/Alcoa), `CASE_HIST_060` (TitleScan/Paxon). The
empty files and the historical case studies are one list, expressed twice.

## 2. Onboarding is the SDLC, and documentation is the tracker

An entity's position in the documentation chain IS its position in the
lifecycle. There is no second system to keep in sync -- which matters, because
this project's recurring defect is precisely two systems that never compare
themselves.

Roughly, an entity progresses:

```
  named             a file exists; nothing else
    |
  described         @dottalk.file -- subsystem, layer, owner, status
    |
  contracted        @dottalk.usage / @dottalk.subusage -- an identity, once
    |               there is something to identify
  catalogued        SYSCMD / SYSSUBCMD / SYSFUNC row, generated not typed
    |
  surfaced          HELP topic, SET USAGE line, dotref entry
    |
  proven            runtime_observed -- someone ran it and recorded the output
```

The `proof_state` vocabulary already in use across the lane docs and registries
(`design-intended`, `source_defined`, `runtime_observed`, `active_development`,
`review_needed`) is not documentation metadata. **It is lifecycle state.**

### The rule this produces

An entity may sit at any stage. What it may not do is **claim a later stage than
it occupies.** A zero-byte file may say "I am a reserved slot" (`@dottalk.file`).
It may not say "I am the ARMY command" (`@dottalk.usage`), because everything
downstream -- SYSCMD, HELP, dotref, the census -- reads a usage contract as a
real command surface and counts it.

That single rule resolves the whole confusion this document was written after.
The empty file was right. The contract on it was wrong. They are different
stages, and only one had been reached.

## 3. Build up, build down, then build the span

The method has two directions, and they are different KINDS of work.

**Build up -- solid.** Structure declared from the top. The subsystem layout,
the reserved names, the contracts, the schemas, the layer vocabulary. This work
is deductive: it says what the system IS, and it can be done before anything
runs. Its failure mode is elegant architecture with nothing underneath.

**Build down -- empirical.** Evidence gathered from the bottom. Runtime proofs,
measured row counts, `stat` on a data file, the actual bytes of a DBF header,
`SET USAGE` output diffed against a contract. This work is inductive: it says
what the system DOES. Its failure mode is a pile of true observations that
compose into no design.

Neither direction alone reaches the other side. **The span is the reconciliation
-- and every defect this project has recorded lives exactly there:**

| Lane | Built up (declared) | Built down (observed) | The gap |
|---|---|---|---|
| AIF-065 | `BUILDLMDB` documents a size ladder | every env is 128 MiB or 1 GiB | the ladder is cosmetic |
| AIF-066 | `HELP_TOPIC_LOCALE` has `SOURCE_HASH` | nothing reads it | drift undetectable |
| AIF-067 | 33 ladder arms | 30 listed in `SET USAGE` | two options undiscoverable |
| AIF-067 | `SYSSUBCMD` 20-field schema | harvest CSV has 10 | could never load |
| AIF-067 | `registry().add("SET RELATION")` | dispatcher keys on first token | dead registration |

Each is a bridge with two good ends and no span. Nothing in those rows is
individually wrong, which is why no test failed -- a test checks one end.

**`stack_audit_v1` is span inspection.** Its WARN count is not a quality score;
it is the current measured distance between what has been declared and what has
been observed. A finding closes when the two ends meet, not when someone
silences it.

## 4. What this asks of a contributor, human or AI

1. **Do not clean up entities.** A zero-byte file, an empty header, a stub with
   one `#include` -- assume design until you have checked `docs/cases/`, the
   registries, and the maintainer. Deletion destroys a declaration.
2. **Do not let an entity claim a stage it has not reached.** Especially: no
   usage contract without a command. A contract written ahead of its
   implementation is counted by tooling that has no way to know better.
3. **Work both directions and say which one you are in.** "I read the source"
   and "I ran it and observed X" are different evidence and get different
   `proof_state` values. Do not promote one to the other by confidence.
4. **When the ends do not meet, record the gap rather than closing it by
   assertion.** The lane docs exist for this. A documented gap is span work
   scheduled; an undocumented one is a bridge that looks finished.

## 5. Owed

- The ten implemented apps (`COBOL`, `CODASYL`, `ERP`, `MCC`, `IDX`, `RETRO`,
  `DRAWIO`, `BIBLETALK`, `CASE`, `SIX`) are contracted and catalogued but do not
  live in the `app_` layer their design declares. `cmd_cobol -> app_cobol` is
  scheduled first; COBOL is runtime-proofed, so it is a safe mover.
- No tool currently reports an entity's lifecycle STAGE. The information exists
  -- file contract, usage contract, catalog row, HELP topic, proof state -- but
  is never assembled per entity. A stage report would make this document
  operational rather than descriptive, and is the natural next instrument.
