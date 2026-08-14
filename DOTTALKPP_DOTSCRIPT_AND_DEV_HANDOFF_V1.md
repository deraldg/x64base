# DotTalk++ DotScript and Development Handoff v1

Status: developer/AI handoff  
Audience: human developer, AI coding agent, maintainer  
Project root: `D:\code\ccode`

## Purpose

This document explains how I have been working inside DotTalk++ and x64base: not as a loose pile of files, but as a database runtime with source-defined contracts, runtime proof, data dictionary thinking, review gates, and scriptable maintenance lanes.

The core working model is:

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
DotScript executes reviewed procedures.
MDO packages preserve maintenance intent and closeout evidence.
```

That sentence is the best short description of how to continue development safely.

## What DotTalk++ Is in Practice

DotTalk++ should be treated like a serious commercial data/runtime system, even though it is homemade. The working pieces already behave like product subsystems:

- `x64base`: engine/runtime foundation, storage and indexing concepts, DBF/CDX/LMDB direction.
- DotTalk++ shell: command surface, work areas, HELP, scripts, runtime commands, validation commands.
- DotScript: repeatable runtime procedure language and smoke/regression harness.
- Data dictionary packages: schema, command, script, source, metadata, and proof planning.
- SelfDoc: evidence and provenance system, not an oracle and not an auto-repair engine.
- manualgen/MDO: controlled documentation and maintenance lifecycle.
- LabTalk: optional educational overlay, case catalog, teaching material, and story layer.

Do not flatten these into one undifferentiated documentation folder. Their separation is part of the architecture.

## Development Doctrine

The strongest pattern in the repo is controlled promotion:

1. Observe current source/runtime state.
2. Write a report or inventory.
3. Classify the finding.
4. Keep uncertainty explicit.
5. Propose a narrow repair or promotion.
6. Mutate only the intended artifact.
7. Capture runtime or structural proof.
8. Write a closeout/status record.

This is why many files are named as `PLAN`, `STATUS`, `REVIEW`, `CANDIDATE`, `PROOF`, or `PACKAGE`. Those names are not noise. They describe lifecycle state.

## DotScript Role

DotScript is best treated as the operational script layer for DotTalk++.

Use DotScript for:

- reproducible runtime procedures
- smoke tests
- schema/table creation candidates
- import/export experiments
- guarded maintenance execution
- command transcript generation
- repeatable proof capture

Do not use DotScript as a place to hide arbitrary mutation. A `.dts` file should make the intended runtime steps visible.

Typical DotScript responsibilities:

```text
set runtime paths
open or create a workspace
create or validate tables
load fixture data
run commands
capture output
prove expected behavior
close with a clear pass/fail status
```

When a DotScript mutates DBF/CDX/LMDB state, the handoff should say so plainly.

## Running DotTalk++ and DotScript

Use the current built executable when capturing runtime proof:

```powershell
& D:\code\ccode\build\src\Release\dottalkpp.exe
```

Inside the shell, the reliable script runner is:

```text
DOTSCRIPT <file.dts>
DOTSCRIPT <file.dts> OUT <transcript-file>
DOTSCRIPT TRACE <file.dts> OUT <transcript-file>
```

Use `DOTSCRIPT ... OUT ...` when the result is meant to prove behavior. The transcript is the artifact a human or AI should review later.

Existing `.dts` files often use lines such as:

```text
DO X64
DO path\to\other_script.dts
```

Treat that as established script vocabulary inside the DotScript estate. From the interactive shell and handoff docs, prefer the explicit `DOTSCRIPT` command because it has the clear usage contract and transcript support.

DotScript comments are skipped when they begin with `*`, `//`, `&&`, or `;` after trimming. Script resolution tries the typed path, then `.dts`, then `scripts/`, then `tests/`. Nesting is intentionally limited: main script plus one subscript.

## The Meaning of `DO X64`

`DO X64` appears in existing x64 canary scripts as the setup switch before `CREATE X64 ...`. It should be treated as a profile/setup operation used by the script estate to put the runtime into the expected x64 working mode.

When a future agent sees this pattern:

```text
DO X64
CREATE X64 VECALIAS (...)
```

do not remove it as noise. It is part of the x64 test/canary ceremony. If proving behavior from the shell, preserve the same sequence in the DotScript used for proof.

## Creating an X64 DBF Directly

The simplest way to create an x64 table is the `CREATE X64` command.

Pattern:

```text
DO X64
CREATE X64 <table> (<field> <type>, <field> <type>, ...)
STRUCT
```

Concrete example:

```text
DO X64
CREATE X64 DEV_STUDENTS (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2), ACTIVE L)
STRUCT
APPEND
REPLACE SID WITH 1001
REPLACE LNAME WITH "MARTIN"
REPLACE FNAME WITH "ADA"
REPLACE GPA WITH 3.75
REPLACE ACTIVE WITH .T.
LIST
```

Important `CREATE` rules from the command contract:

- `CREATE X64 <name> (...)` writes a DBF through the configured DBF path slot.
- It closes the current area before creating the table.
- It opens the new table after successful creation.
- It clears active order state.
- Memo fields (`M`) attempt memo attach after open.
- X64 applies descriptor fallback/name policy for DBF descriptor safety.
- Long or colliding field names can receive fallback tokens while retaining authoritative logical names where supported.

Use `STRUCT`, `FIELDS`, `LIST`, `TUPLE`, or `STATUS` as readback proof after creation.

## Creating a DBF From `schema.json`

The schema-driven path is `DDL CREATE DBF`.

Pattern:

```text
DDL CREATE DBF <out.dbf> FROM <schema.json>
DDL CREATE DBF <out.dbf> FROM <schema.json> OVERWRITE
DDL CREATE DBF <out.dbf> FROM <schema.json> SEED BLANK <n>
DDL CREATE DBF <out.dbf> FROM <schema.json> EMIT SIDECARS
```

Path rules:

- Relative schema inputs resolve under the `SCHEMAS` path first, then current working directory.
- Relative DBF outputs resolve under the `TMP` path by default.
- Existing DBF output is refused unless `OVERWRITE` is supplied.
- `SEED CSV` is recognized in the command surface but is not implemented in this drop-in.
- `EMIT SIDECARS` writes companion schema/load/index metadata files.

Minimal `schema.json` shape:

```json
{
  "version": "1.0",
  "name": "students",
  "encoding": "UTF-8",
  "date_policy": "ISO",
  "null_policy": "EMPTY_AS_EMPTY",
  "logical_policy": "TF",
  "fields": [
    { "name": "SID", "type": "N", "length": 9, "decimals": 0, "required": true },
    { "name": "LNAME", "type": "C", "length": 20, "required": true, "trim": "right" },
    { "name": "FNAME", "type": "C", "length": 15, "required": true, "trim": "right" },
    { "name": "DOB", "type": "D", "length": 8, "zero_date": "ALLOW" },
    { "name": "ACTIVE", "type": "L" }
  ],
  "indexes": [
    { "name": "SID_PK", "engine": "CNX", "order": ["SID ASC"], "unique": true, "nullable": "DISALLOW" },
    { "name": "NAME1", "engine": "CNX", "order": ["LNAME ASC", "FNAME ASC"], "collation": "nocase", "trim": "right" }
  ]
}
```

The active schema contract at `src\cli\schema_json_v1.schema.json` supports field types `C`, `N`, `D`, `L`, and `M` for `DDL CREATE DBF`. Do not assume every direct `CREATE` type is valid in the JSON schema path.

## Schema Rules for Future Agents

When working with a schema, classify it before using it:

| Schema kind | Meaning | Handling |
|---|---|---|
| `schema.json` | Table field/index/relation contract for DDL/import work. | Candidate until runtime-created/read back. |
| `.dtschema` / `.dtschemas` | x64base workspace/session schema: areas and optional relations. | Do not confuse with SQL schemas. |
| JSON Schema | Validator/specification for another artifact. | Use for structural validation, not runtime proof by itself. |
| Data dictionary package schema | Contract for generated reports/import candidates. | Keep package-local until promoted. |

Rules:

- Keep candidate schemas separate from active schemas.
- Never overwrite active schemas without an explicit promotion package.
- If a schema has indexes, also define how those indexes are created or activated at runtime.
- If a schema has relations, capture workspace/relation proof separately from table creation proof.
- A schema that parses is not proven. A schema is only proven after runtime creation/open/readback.
- For DBF work, prove with `STRUCT` and at least one data navigation/readback command.
- For index work, prove physical order versus logical order.
- For workspace schema work, prove `WORKSPACE` load/save/readback if the runtime supports it for that case.

## Creating and Using an Index

The direct index command builds an INX file from the current open table.

Pattern:

```text
USE <table>
INDEX ON <field> TAG <name>
INDEX ON <field> TAG <name> DESC
INDEX ON <field> TAG <name> ASC 2INX
SET INDEX TO <name>.inx
```

Important rules:

- `INDEX` requires an open table.
- It reads records and writes an index file.
- It does not mutate table records.
- Deleted records are excluded.
- Default direction is `ASC`.
- Default output format is `2INX`.
- `TAG` names an INX file target; non-`.inx` extensions are refused.
- Field-number tokens are accepted by the parser, but field names are clearer in docs and proof.

Use `SET INDEX TO <container>` to attach an index container. For CDX/CNX-style tag activation, use `SET ORDER`.

Patterns:

```text
SET INDEX TO students.cdx
SET ORDER TO TAG LNAME
SET ORDER TO 0
SET ORDER PHYSICAL
```

Key distinction:

```text
SET INDEX names or attaches the index container.
SET ORDER chooses the active logical traversal order.
INDEX creates an INX file from the currently open table.
```

Do not claim an index works until runtime output proves the order changed or a seek uses the expected access path.

## Minimal End-to-End Proof Script

A future AI can use this as a starting pattern. Put it in a temporary `.dts` file, run it with `DOTSCRIPT ... OUT ...`, and review the transcript.

```text
* Status: SMOKE / MUTATING_SANDBOX
* Purpose: Create x64 DBF, add row, build index, attach index, prove readback.
* Mutation: writes DBF and INX in configured runtime paths.

DO X64
ERASE DEV_STUDENTS CONFIRM

CREATE X64 DEV_STUDENTS (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2))
STRUCT

APPEND
REPLACE SID WITH 1001
REPLACE LNAME WITH "MARTIN"
REPLACE FNAME WITH "ADA"
REPLACE GPA WITH 3.75

APPEND
REPLACE SID WITH 1002
REPLACE LNAME WITH "BROWN"
REPLACE FNAME WITH "GRACE"
REPLACE GPA WITH 3.90

LIST
INDEX ON LNAME TAG DEV_STUDENTS_LNAME ASC 2INX
SET INDEX TO DEV_STUDENTS_LNAME.inx
TOP
LIST
CLOSE
```

Proof expectations:

- `STRUCT` shows the expected fields.
- First `LIST` shows inserted rows in table/physical order.
- `INDEX ON` writes the index target without table mutation.
- `SET INDEX` attaches the INX target where the current runtime supports that path.
- For logical-order proof, prefer a CDX/CNX fixture with `SET INDEX TO <container>` and `SET ORDER TO TAG <tag>`, or capture clear INX navigation output if that is the behavior under test.

If the transcript does not visibly prove changed order or indexed access, do not fake the proof. Record the gap and use a CDX/CNX `SET ORDER` proof or a dedicated index fixture.

## DotScript Safety Classes

Class DotScript files before running or promoting them:

| Class | Meaning | Default action |
|---|---|---|
| REPORT_ONLY | Reads runtime/source state and emits evidence. | Safe to inspect; run only if paths are understood. |
| PLAN_ONLY | Documents intended work but should not execute mutation. | Do not execute as a live script. |
| CANDIDATE | Proposed runtime/import/schema action. | Review before execution. |
| OPERATOR_RUN_REQUIRED | Intended to run later under explicit authorization. | Do not run casually. |
| MUTATING | Writes DBF/CDX/LMDB/source/generated docs. | Requires explicit gate and proof plan. |
| SMOKE | Reproducible runtime proof. | Prefer read-only fixtures unless mutation is the behavior under test. |

The existing style often marks guarded scripts directly in comments. Preserve that habit.

## DotScript Pattern

A good DotScript or DotScript-adjacent package should answer these questions:

```text
What subsystem does it touch?
What paths does it read?
What paths does it write?
Does it mutate DBF/CDX/LMDB?
Does it mutate HELP, CMDHELPCHK, manualgen, source, or schemas?
What fixture or workspace does it need?
What output proves success?
What is the rollback or non-promotion path?
```

For future scripts, prefer headers like:

```text
* Status: CANDIDATE / REVIEW_BEFORE_EXECUTION
* Safety: REPORT_ONLY or MUTATING
* Purpose: one-sentence intent
* Inputs: explicit files/directories
* Outputs: explicit reports/tables/transcripts
* Mutation: none / DBF / CDX / LMDB / docs / source
* Gate: who or what must approve before promotion
```

## Schema Practice

The repo has been using schemas as contracts, not as decorative docs.

Good schema work usually has three layers:

1. Human-readable design: Markdown package or plan.
2. Machine-readable contract: `.dtschema`, JSON schema, CSV manifest, or registry row.
3. Runtime proof: DotScript/native command transcript showing the contract is usable.

When building schemas for the homemade database, treat them with the same rigor as a commercial migration:

- define fields intentionally
- preserve source provenance
- mark nullable/required assumptions
- separate candidate schemas from active schemas
- avoid promoting a schema just because it parses
- include field/tag/index reconciliation when CDX/LMDB behavior matters

Do not silently overwrite active schema files. Prefer candidate folders and promotion packages.

## DBF/CDX/LMDB Handling

The runtime has several storage/index concepts that should stay distinct:

| Concept | Developer meaning |
|---|---|
| DBF/XDBF | Table/storage layer and record layout. |
| CDX | User-facing logical index/tag container concept. |
| LMDB | Backend/index environment detail in some paths. |
| DbArea/work area | Runtime session state: open table, cursor, alias, order, filter. |
| Tuple/projection | Rendered relational or query-shaped view of underlying data. |

A common mistake would be to treat an index, a table, and a rendered list as the same thing. DotTalk++ is valuable because it can show those differences.

For proofs, capture the difference between:

```text
physical record order
logical order
active tag/order
current cursor
filtered/predicate view
projected tuple output
persisted table state
buffered or dirty state
```

## HELP, CMDHELPCHK, and Metadata

HELP is not just user text. It is part of the command contract system.

The intended chain is:

```text
source usage contracts
  -> command/help catalog
  -> HELP output
  -> CMDHELPCHK validation
  -> manualgen/manual publication
  -> SelfDoc provenance
```

Avoid raw HELP DBF edits unless a specific guarded package authorizes it. Most repair work should start from source contracts, generated candidates, or validation reports.

When command behavior and HELP disagree, do not immediately patch prose. First determine whether the drift belongs to:

- source command implementation
- usage metadata
- generated HELP artifact
- stale manualgen output
- CMDHELPCHK expectation
- alias/variant policy
- intentional compatibility shim

## SelfDoc Pattern

SelfDoc reports are evidence, not verdicts.

Use SelfDoc to classify, preserve, and route findings. Do not let it become an unreviewed mutation engine.

Useful lanes:

```text
CONFIRMED
LIKELY
STALE_EVIDENCE
CLASSIFIER_REVIEW
CAPTURE_REVIEW
POLICY_REVIEW
SOURCE_REVIEW
INTENTIONAL_EXCEPTION
DO_NOT_REPAIR
```

This matters because many apparent defects are actually:

- stale generated output
- scanner limitations
- command aliases
- backup files under source roots
- compatibility shims
- intentionally optional LabTalk/education material

The correct response is often a review report, not a patch.

## MDO and Manualgen Pattern

MDO packages are maintenance work orders and closeout records. Treat them as the project memory of how a change was reasoned through.

Good MDO-style work has:

- one clear objective
- explicit safety class
- source/evidence paths
- mutation boundary
- generated reports
- validation command or proof
- status/closeout file
- recommended next package

Manualgen work should follow the same promotion flow:

```text
candidate section
  -> evidence review
  -> reviewed candidate
  -> human decision/status
  -> promoted draft
  -> publication artifact
```

Do not skip from raw generated text to final manual prose.

## LabTalk Boundary

LabTalk is an optional educational overlay, not a required engine dependency.

Keep these layers separate:

```text
source evidence DOCX/images/decks
  -> normalized docs/cases/CASE_*.md records
  -> runtime CASE command
  -> manuals/decks/storyboards/publication products
```

The CASE catalog work follows the same doctrine:

- source evidence is preserved
- normalized case files are runtime-readable derivatives
- publication gates remain explicit
- runtime proof is required for engineering claims
- educational material should not leak into engine/professional profiles unless enabled

## How I Have Been Working With DotTalk++

The successful pattern has been:

1. Read existing reports before touching code.
2. Search with `rg` for command names, schemas, and status files.
3. Identify which layer owns the issue: source, runtime, HELP, metadata, SelfDoc, manualgen, LabTalk, or data dictionary.
4. Prefer report-only inventories first.
5. Patch only the narrow artifact that is actually misaligned.
6. Preserve source evidence folders.
7. Run the current executable when possible to capture proof.
8. Write a new review/closeout document instead of rewriting history.

That is why recent LabTalk work fixed registry drift, added inventory and proof scaffolds, and left publication gates closed instead of declaring the cases finished.

## AI Agent Rules

Future AI agents should follow these rules:

- Never assume all generated files are junk.
- Never delete or move source DOCX/case/evidence folders casually.
- Never promote candidate schemas or scripts just because they look complete.
- Never treat SelfDoc classifications as automatic repair authorization.
- Never mutate DBF/CDX/LMDB/HELP/manualgen outputs without an explicit safety gate.
- Prefer small reports, registries, and proof packets over broad rewrites.
- Keep optional overlays optional.
- Preserve dirty user work; inspect before editing.
- If a command can prove behavior, run the runtime and capture the proof.
- If proof requires fixture setup, say that and leave the gate open.

## Human Developer Rules

Human developers can move faster, but the same boundaries matter:

- Put new commands near their owner subsystem and add usage metadata.
- Add HELP/CMDHELPCHK expectations only after runtime behavior is stable.
- Add schema contracts before import/promote scripts.
- Add DotScript smoke tests for repeatable behavior.
- Capture runtime transcripts for important claims.
- Store publication material as derived output, not as the only source.
- Use MDO/status documents to leave a trail for the next maintainer.

## Naming Patterns Worth Preserving

The repo uses names as lifecycle markers. Keep using them:

| Pattern | Meaning |
|---|---|
| `*_PLAN_*` | Design or proposed route, no mutation implied. |
| `*_STATUS.*` | Current closeout/status statement. |
| `*_REVIEW_*` | Evidence review or human/agent assessment. |
| `*_CANDIDATE_*` | Generated or proposed artifact not yet canonical. |
| `*_PROOF_*` | Runtime or structural evidence. |
| `*_PACKAGE_*` | Bundled action or promotion unit. |
| `*_REGISTRY_*` | Catalog of governed objects. |
| `*_BOUNDARY_*` | Explicit separation of ownership/safety/profile. |

## Practical Next Work Pattern

For any new feature or repair:

1. Create or update a short plan/status doc.
2. Identify source-of-truth files.
3. Identify generated/candidate outputs.
4. Define safety class.
5. Make the narrow change.
6. Run runtime or structural validation.
7. Save proof.
8. Update the relevant registry.
9. Leave open gates explicit.

Example closeout shape:

```text
Changed:
- registry alignment
- case front matter
- proof packet scaffold

Verified:
- 15 loader-visible files
- no missing sections
- runtime CASE LIST passes

Still open:
- behavioral fixture proof
- media review
- human publication approval
```

That style is more valuable here than a large undocumented code drop.

## Current Mental Model

The project is strongest when treated as a transparent database engine with a documentation and teaching system wrapped around it.

The goal is not merely to make commands work. The goal is to make records, indexes, relations, schemas, scripts, metadata, HELP, and history explain themselves well enough that a developer, student, or AI agent can reason about the system without guessing.

That is the pattern to continue.
