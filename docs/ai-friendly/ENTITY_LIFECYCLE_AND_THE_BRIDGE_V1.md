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

### The vocabulary is already declared. Use it.

**Corrected 2026-07-27, within hours of this document being written.** A first
draft invented a chain here -- named / described / contracted / catalogued /
surfaced / proven -- without checking whether the project already had one. It
does. `labtalk/registries/proofs.yaml` declares ten `proof_states`:

| state | meaning |
|---|---|
| `idea` | Concept captured, not reviewed. |
| `source_defined` | Current source declares behavior or contract. |
| `runtime_observed` | Runtime transcript or smoke output exists. |
| `help_documented` | HELP or CMDHELP exposes the behavior. |
| `validated` | CMDHELPCHK, SelfDoc, or another validator checked it. |
| `case_registered` | Case registry knows the teaching context. |
| `runtime_lab_candidate` | Lab is identified but needs proof attachment. |
| `student_ready` | Reviewed for student-facing use. |
| `simulated` | Demonstration is intentionally simulated, not live runtime. |
| `historical_review_needed` | Historical claim needs source or fact review. |

This is strictly better than the invented chain, in two ways that matter.

**`idea` is the zero-byte state.** "Concept captured, not reviewed" is precisely
what `app_army.cpp` is. The system already had a name for the thing this
document spent three paragraphs arguing for.

**It carries the teaching dimension, which the invented chain dropped entirely.**
`case_registered`, `runtime_lab_candidate` and `student_ready` are lifecycle
states in a project whose purpose includes education. Omitting them is not a
simplification, it is a different and smaller system.

Note also that these are **not a single linear position**. An entity holds a SET
of achieved states: something can be `source_defined` and `help_documented`
without being `runtime_observed`, and `validated` without being `student_ready`.
A stage report must therefore show which states an entity holds, not one label.

That this document reproduced the defect it exists to warn about -- a second
description of an already-declared thing, written without comparing -- is
recorded rather than quietly fixed. It is the same failure as every span defect
in section 3, committed by the author of the section describing them, on the
same day. The rule is not hard to state and is evidently easy to break: **before
declaring a vocabulary, search for the one that exists.**

### The rule this produces

An entity may sit at any stage. What it may not do is **claim a later stage than
it occupies.** A zero-byte file may say "I am a reserved slot" (`@dottalk.file`).
It may not say "I am the ARMY command" (`@dottalk.usage`), because everything
downstream -- SYSCMD, HELP, dotref, the census -- reads a usage contract as a
real command surface and counts it.

That single rule resolves the whole confusion this document was written after.
The empty file was right. The contract on it was wrong. They are different
stages, and only one had been reached.

## 2a. The contract a zero-byte entity SHOULD carry: `@dottalk.pdlc`

Section 2's rule says an entity may not claim a stage later than it occupies.
That is stated as a prohibition, which leaves the obvious question unanswered:
what may it claim? A file at the beginning of its life is not contract-less. It
is at a REAL STEP, and that step deserves a contract.

`docs/maintenance/PDLC_STUDENT_WORKING_MODEL_LANE_V1.md` already declares the
six steps, and `owning_lifecycle: labtalk_pdlc` is already a live field in
`labtalk/registries/ai_portal_tasks.yaml` -- PDLC is in use in the AI portals
today, not a proposal:

```
PDLC (inside one milestone)      SDLC / lane governance (around it)
  analyze the problem      <->   intake row (AIF-NNN), truth state
  design the solution      <->   lane doc + contracts
  code                     <->   source change on the branch
  test & debug             <->   proof: unit test / REGRESSION / transcript
  document                 <->   document-as-you-work (AIF-024)
  maintain                 <->   closeout, drift gates
```

A zero-byte entity is not stalled or unfinished. **It is at `analyze` or
`design`,** and those are steps a working programmer is paid to be at.

### Proposed marker (member.derald, 2026-07-27: "you can give them a PDLC
### contract, or similar")

```
// @dottalk.pdlc v1
// pdlc-step: design
// proof-state: idea
// owning-lifecycle: labtalk_pdlc
// planned-command: ARMY
// case: CASE_HIST_020
// gate:
//   Advances to `code` when the JUMPS/Army dataset shape is settled and a
//   handler signature is agreed. At that point a usage contract is written IN
//   THE SAME COMMIT as the handler.
```

### Why this is safe where a usage contract is not

The decisive detail is `planned-command:` rather than `command:`. Nothing
downstream harvests `planned-command`, so `SYSCMD`, `SYSSUBCMD`, HELP, `dotref`
and the census cannot mistake an intention for a surface. The entity becomes
legible to lifecycle tooling WITHOUT becoming countable as a command.

That is the whole shape of the problem this document was written after: the
placeholder files were not wrong to carry a contract, they were wrong to carry
*that* contract. `command: none` was an attempt to say "I am at an early step"
in a vocabulary that only knows how to say "I am a command".

### What it buys

- `entity_stages.py` can report `idea` and `design` entities as INTENTIONAL,
  distinguishing a reserved slot from an oversight -- today it can only observe
  that a file declares no command.
- The AI portal's task registry and the source tree describe the same lifecycle
  in the same words, so a partner reading either sees one system.
- The gate is written down, so advancing a stage becomes a checkable event
  rather than someone's judgement.
- Deleting a reserved slot becomes a visible decision against a stated intent.

### Owed

- Ratify the field set with member.derald before applying it widely; this
  section is a proposal captured at the moment it was made, not a settled spec.
- Apply first to the six known early-step entities: `app_army.cpp`,
  `app_paxon.cpp`, `app_alcoa.cpp` (design layer, matching CASE_HIST_020/030/060)
  and `edu_boyce_codd.cpp`, `edu_dewey_decimal.cpp`, `edu_snx.cpp` (education
  placeholders).
- Teach `entity_stages.py` to read it, and `stack_audit_v1` to treat a declared
  `pdlc-step` as the answer to "why does this file declare no command".

## 2b. One progression, five views

The pieces above were built at different times by different hands and have never
been shown together. They are not five systems. They are five vocabularies for
the same movement, and once aligned the whole model is one table.

| PDLC step | proof_state | source contract | catalog / surface | SDLC governance | direction |
|---|---|---|---|---|---|
| **analyze** | `idea` | `@dottalk.pdlc` (`pdlc-step: analyze`) | -- | intake row, AIF-NNN | up |
| **design** | `idea` | `@dottalk.pdlc` + `@dottalk.file` | -- | lane doc | up |
| **code** | `source_defined` | `@dottalk.usage` / `@dottalk.subusage` | `SYSCMD` / `SYSSUBCMD` row, generated | source change on branch | up |
| **test & debug** | `runtime_observed` | -- | -- | proof: REGRESSION / teed transcript | **down** |
| **document** | `help_documented` | (contract feeds it) | `HELP_TOPIC`, `SET USAGE`, `dotref` | document-as-you-work (AIF-024) | **down** |
| **maintain** | `validated` | -- | drift gates | closeout (AIF-006), `stack_audit_v1` | **span** |

Education overlays the same track rather than paralleling it:
`case_registered` → `runtime_lab_candidate` → `student_ready`, carried in
`labtalk/registries/` and pointing at the same entity.

### What the alignment shows

**The direction column is not decoration.** The first three rows are built UP --
deductive, declared, true before anything runs. The next two are built DOWN --
inductive, observed, meaningless until something runs. `maintain` is the only
row that is neither, because maintenance IS span work: it exists to keep the two
halves meeting after they first met.

**Every artifact has exactly one home.** A fact is declared in one vocabulary and
translated into the others -- contract to catalog to surface -- rather than
authored twice. Where that discipline broke, we got this run's defects: a ladder
and a usage text both hand-written; a schema in a table and a different one in a
CSV; a lifecycle chain invented in a doctrine document when `proofs.yaml` already
had one.

**A gap is now nameable rather than merely felt.** "This entity is `code` but not
`document`" is a sentence with a remedy attached. `entity_stages.py` found 24 of
them on first run -- contracted and HELP-documented but absent from `SYSCMD`,
meaning the surface got ahead of the catalog it derives from.

**And the honest asymmetry:** the up-rows are cheap and the down-rows are
expensive. Anyone can declare; only running the thing and recording the output
earns `runtime_observed`. That is why `proof_state` promotion is guarded and why
"I read the source" never becomes "I observed it" by confidence. The table makes
the temptation visible: every row above the fold can be written at a desk.

## 2c. Declared vs derived -- the rule that keeps this small

Settled 2026-07-27 with member.derald, who asked whether to add SDLC-stage and
PDLC-stage fields to the header contracts and answered his own question in the
asking: *"too much categorisation and we get lost, I prefer the KISS principle as
long as it's gold standard too. I want my cake and keep it too."*

Both are obtainable, because the tension dissolves once declaration and
derivation are separated.

```
status:   INTENT     what the owner promises      DECLARED   tiny closed set
stage     EVIDENCE   what the system can prove    DERIVED    never typed
```

### Why stage must not be a field

**A derived stage cannot drift, because it IS the evidence.** `entity_stages.py`
computes an entity's position from artifacts that already exist -- does it carry a
contract, does it have a catalog row, a HELP topic, a cited proof. Nothing to
maintain, nothing to get wrong, and it cannot disagree with reality because it is
read from reality.

A declared stage field would be a SECOND description of the same fact, on 1036
files, maintained by hand. That is the defect class this entire run catalogued,
adopted deliberately and at scale.

**And a field earns existence by being CONSUMED.** This run found three fields
written and never read -- `SOURCE_HASH` in `HELP_TOPIC_LOCALE`, the X64M
displacement in every DBF descriptor, `mapsize_explicit` in `BUILDLMDB`. Each was
a value produced for a decision nobody made. A stage field on every source file,
read by nothing, would be the largest instance yet.

### The field already exists, and its condition is the argument

`status:` has been carrying stage informally, and it shows:

```
877  supported          94.5% -- no discriminating power
 11  experimental
  9  developer
  6  placeholder-shim
  4  supported-conditional / implementation-shim / active
  3  "source-defined from MDO-282 native MANUAL implementation"   <- a sentence
  2  supported-stub-mixed
  1  supported-stub / stub / supplemental / sample-extension
```

`stub`, `supported-stub`, `supported-stub-mixed`, `placeholder-shim`,
`implementation-shim` and `implementation-helper` are six attempts at one idea by
authors with no vocabulary to reach for. Adding two more stage fields would
reproduce this twice.

Worse, the 877 are not decisions. `tools/fullstack_docs/source_census.py:157`
WRITES `// status: supported` as a backfill default, and says so at line 301.
`stack_audit`'s own `BANNER_CENSUS/DERIVED_ONLY` finding already concludes:
**"Do not treat status/owner/project as authority."**

So the field being considered for extension is 94.5% machine-fabricated and
explicitly flagged untrustworthy by this project's own guard.

### The rules

1. **Do not add SDLC or PDLC stage fields.** Both are derivable from artifacts
   that already exist. Derive them.
2. **`status:` expresses INTENT only** -- what the owner promises, from a small
   closed set. Anything encoding *how finished* a thing is belongs to derivation.
3. **Declare only what cannot be derived.** A zero-byte entity has no artifacts
   to derive from; that is the sole case, and it is `@dottalk.pdlc` on a handful
   of files rather than a field on a thousand.
4. **A field earns existence by being consumed.** If nothing reads it, it is not
   documentation, it is decoration that will drift.
5. **An unauthored default is not information.** `status: supported` on 877
   backfilled files discriminates nothing. Consider making `status:` appear only
   when it is NOT the normal case -- absence carrying the default -- which is
   smaller and more honest than what exists.

## 2d. Interface with the permissions lane

Written 2026-07-27 so a concurrent RBAC session has something to read against.
Neither lane needs the other's internals. **The shared object is `proof_state`
promotion**: the permissions lane owns WHO MAY ASSERT it, this lane owns WHAT
EVIDENCE MAKES IT TRUE.

Existing permission keys are all actions on the system -- `database.read`,
`git.push`, `host.shell`, `source.mutate`, `perm.empty`. Nothing yet covers
claims, proofs, or lifecycle transitions.

### Derivation needs no permission, and that is the point

A derived stage is a READING, not an assertion. It cannot be falsified without
falsifying its inputs -- a `SYSCMD` row, a HELP topic, a source contract -- and
each of those is written by an already-permissioned act.

> **Derived facts inherit their trust from their sources' permissions.**

No new gate, no new surface. Which turns the KISS argument of section 2c into a
security argument as well: **every field not declared is a permission that never
has to be defined.** Keeping the declared surface tiny shrinks the RBAC lane's
scope as a side effect.

### The claim worth gating is promotion, not mutation

`source.mutate` already covers editing a file. The consequential act is asserting
*"this entity is now `runtime_observed`"*, because downstream work trusts it.
Today anyone who can write `proofs.yaml` can assert it; during AIF-065 the AI
partner asserted it four times on its own authority.

That maps onto machinery already built, without inventing a mechanism:

```
agent runs the proof and cites the transcript
    USER REQUEST proof.promote FOR member.ai.claude.cowork   [transcript]
owner reviews the EVIDENCE, not the assertion
    USER APPROVE <id>
```

Teamwork agency (see `AGENCY_MODEL_V1.md` section 8) applied to a lifecycle
transition, through the existing REQUEST/APPROVE flow.

### What must NOT be gated: description

If writing lane documents or analysis required permission, the work that produced
this document would not have happened. The value came from writing freely and
being corrected -- repeatedly, in the same session, by the maintainer attacking
premises.

> **Permission attaches to assertions of FACT, not to EXPLANATIONS.**

Gate `proof_state`, catalog rows, and `status:` promotion. Leave prose, lane docs
and analysis ungated: they are arguments, and arguments are checked by reading,
not by authority. A system that requires authorisation to think will only ever
record what it already believed.

### Owed / to confirm in the permissions lane

- `perm.empty` may be a placeholder that grants nothing while reading as a
  permission -- the same category error as the `command: none` contracts retired
  on 2026-07-27. Confirm it is intentional.
- Whether promotion should be one permission or several (`proof.promote`,
  `catalog.write`, `status.promote`). This lane has no opinion beyond: fewer is
  better, and each must be consumed by something.

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
