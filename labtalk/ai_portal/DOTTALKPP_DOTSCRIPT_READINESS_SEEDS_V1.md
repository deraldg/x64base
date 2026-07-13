# DotTalk++ and DotScript Startup Readiness Seeds v1

Status: **Mandatory before AI-authored DotScript execution**
Authority: current source, runtime, HELP surfaces, and reviewed proof scripts
Applies to: every new or resumed AI conversation that will write, modify, review,
or execute `.dts` files

## Why This Gate Exists

Knowing xBase, SQL, shell scripting, or another procedural language does not
mean an AI knows DotTalk++. DotScript is not a place to translate remembered
syntax from another system.

The current runner reads a script one noncomment line at a time and sends that
line to the DotTalk++ shell command executor. Therefore good DotScript depends
on knowing the actual DotTalk++ commands, session state, path profiles, work
areas, storage effects, and proof surfaces used by the installed runtime.

An AI that has only read descriptive prose is **not ready to execute DotScript**.

## Seed 1 — Learn the Runtime Before Authoring the Procedure

Read these sources before drafting a script:

1. `D:\code\ccode\DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`
2. `D:\code\ccode\docs\agents\AI_BABY_BOOTSTRAP_CARD.md`
3. `D:\code\ccode\docs\maintenance\MAINTENANCE_SCRIPT_ROOT_POLICY_v1.md`
4. `D:\code\ccode\src\cli\cmd_dotscript.cpp`
5. one current, proven `.dts` file from the same subsystem as the task

Then query the current built runtime. At minimum, inspect:

```text
MAINT AI ASSIMILATE
DOTSCRIPT USAGE
CMDHELP DOTSCRIPT
DOTHELP DOTSCRIPT
CMDHELP <each command planned for the script>
```

If source, runtime output, HELP, and an old example disagree, stop and classify
the drift. Do not pick the syntax that merely looks most familiar.

## Seed 2 — DotScript Is a Command Sequence, Not an Imagined Language

Use one proven DotTalk++ shell command per executable line. Comments may begin
with `*`, `//`, `&&`, or `;` after leading whitespace.

Do not invent:

- control flow, variables, functions, or operators from another language;
- SQL syntax where a native DotTalk++ command is required;
- Visual FoxPro behavior that current source/runtime does not prove;
- command abbreviations, quoting, clauses, or path behavior from model memory;
- unlimited script nesting—the current limit is a main script plus one
  subscript.

Unknown commands are reported in the transcript, but the runner continues to
later lines. A process exit code of zero is therefore not sufficient proof that
the script executed correctly.

## Seed 3 — Bootstrap State Explicitly

Every regression or proof script must establish its own runtime profile before
touching tables, workspaces, relations, metadata, or ERSATZ state.

Use the profile proved for the owning lane, such as:

```text
DO X32
DO VFP
DO X64
DO SANDBOX
DO METADATA
DO MESSAGING
```

Do not inherit whatever paths, area, alias, table, order, filter, or record
position an operator happened to leave active. Nested scripts must use a path
that is correct from their registered runtime script location.

## Seed 4 — Classify Before Running

Every new or changed script must declare:

```text
* Status: CANDIDATE / REVIEW_BEFORE_EXECUTION
* Safety: REPORT_ONLY / SMOKE / MUTATING / OPERATOR_RUN_REQUIRED
* Purpose: one sentence
* Inputs: exact paths or runtime objects
* Outputs: exact paths, objects, or transcript
* Mutation: none / DBF / CDX / LMDB / HELP / metadata / docs / source
* Fixture: disposable target or explicit active target
* Gate: authorization required before execution or promotion
```

A script that contains `CREATE`, `ERASE`, `ZAP`, `APPEND`, `REPLACE`, import,
index creation, catalog rebuild, or another write-capable command is not
read-only merely because it is called a smoke test.

## Seed 5 — Command Evidence Table

Before executing an AI-authored script, record this small table in the task
context or review note:

| Command | Exact syntax evidence | Required state | Side effects | Expected readback |
| --- | --- | --- | --- | --- |
| one row per command family | runtime HELP, source usage block, or current proven script | profile, table, area, order, fixture | none or named mutation | output that proves success |

If any row cannot be completed honestly, the script remains a candidate and
must not execute against maintained data.

## Seed 6 — Readiness States

Use these states explicitly:

| State | Meaning | Allowed action |
| --- | --- | --- |
| `UNASSIMILATED` | Current runtime and task command surface have not been inspected. | Read and query only. |
| `ORIENTED` | Mandatory sources read and the read-only startup probe is green. | Draft or review only. |
| `SYNTAX_BACKED` | Every planned command has current syntax/state/effect evidence. | Run only against an authorized disposable fixture. |
| `SANDBOX_PROVEN` | Trace/transcript proves expected behavior with no unexplained errors. | Request promotion or maintained-data authorization. |
| `AUTHORIZED_FOR_TARGET` | Maintainer explicitly approved the named target and mutation. | Execute only the reviewed script on that target. |

Readiness never carries automatically from one script family to another. An AI
that proved a HELP inspection script has not thereby proved competence to write
a DBF/CDX mutation script.

## Seed 7 — Transcript Review Is Part of Execution

Use trace and transcript capture for proof:

```text
DOTSCRIPT TRACE <file.dts> OUT <transcript-file>
```

Review the full transcript. At minimum reject or investigate:

- `Unknown command`;
- script-not-found or transcript-open failures;
- nesting-limit messages;
- missing table, area, field, index, tag, or path errors;
- output that shows the command ran against an unintended target;
- missing expected readback;
- success claims supported only by the process exit code.

Use `SMARTLIST` for order/index proof unless `LIST` itself is the behavior under
test. For DBF work, include structure and data readback. For index work, prove
logical order or seek behavior rather than merely proving an index file exists.

## Mandatory AI Rule

Until the task reaches `SYNTAX_BACKED`, the AI may explain, inspect, and draft,
but it must not present its DotScript as executable truth. Until it reaches
`AUTHORIZED_FOR_TARGET`, it must not run against maintained or publication
data.

If the task also changes DotTalk++ source code, complete
`SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md` before applying the source patch.
