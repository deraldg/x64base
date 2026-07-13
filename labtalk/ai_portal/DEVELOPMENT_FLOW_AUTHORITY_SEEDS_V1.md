# x64base Development Flow, Locations, and Authority Seeds v1

Status: **Mandatory AI cold-start context**
Declared by: x64base maintainer
Applies to: x64base, DotTalk++, LabTalk, public repository, and website work

These seeds prevent a new AI conversation from inventing a new source tree,
branch, or publication route. Read them before inspecting, changing, staging,
committing, or publishing project work.

## Seed 1 — Development Source Authority

`D:\code\ccode` is the authoritative development tree for source and runtime
truth.

- Begin source investigation and implementation here.
- Inspect the current branch and relevant working-tree state before acting.
- A dirty or mixed working tree may contain valid maintainer work. Preserve it.
- Do not clean, reset, replace, or broadly stage unrelated work.
- Do not treat a clean public checkout as newer or more authoritative merely
  because it is cleaner.

The checked-out branch is current workspace state, not a universal branch name.
A new chat is not a reason to create, switch, or rename a branch. Branch changes
require an explicit maintainer instruction for the task.

## Seed 2 — Curated Publication Flow

The publication flow is one-way and selective:

```text
D:\code\ccode
  authoritative development source and runtime work
        |
        | reviewed, relevant, clean work only
        v
C:\x64base
  curated publication staging tree and Git working repository
        |
        | commit and push from here
        v
github.com/deraldg/x64base
  public projection / snapshot
```

`C:\x64base` is not a competing development source. It receives the clean,
relevant subset promoted from `D:\code\ccode`. Before committing, compare the
staged copy with the intended development files and run proof appropriate to the
change.

The GitHub `main` branch is canonical for the current **public snapshot** only.
It is not the authority over active development in `D:\code\ccode`.

## Seed 3 — Public-Only Work Is Not Integrated Work

A change made directly in `C:\x64base` or on GitHub does not prove that the
authoritative development tree contains the change.

If a public-only fix exists:

1. identify the exact public commit and changed files;
2. inspect the corresponding files in `D:\code\ccode`;
3. implement or reconcile the fix in the development tree without overwriting
   unrelated maintainer work;
4. build or test from the development tree;
5. promote the reviewed result through `C:\x64base` again.

For example, a COMMIT fix present on GitHub but absent from
`D:\code\ccode\src\cli\cmd_commit.cpp` is public-only, not integrated.

## Seed 4 — Documentation and Website Authority

`D:\dev\x64base-site` is the website source tree. The live website and its
repository content are downstream documentation surfaces.

- Public documentation may summarize reviewed project truth.
- Website prose, AI conversation, and generated summaries do not override
  source or runtime evidence.
- Runtime claims must trace back to `D:\code\ccode` and appropriate proof.
- Website work follows its own repository workflow and must not be used to
  reverse-populate runtime source automatically.

## Mandatory Task Start

Every AI-assisted task in this project must begin with this orientation:

1. classify the task as development, publication staging, public-repository,
   website, or read-only review work;
2. identify the authoritative root for that class of work;
3. inspect the relevant files, current branch, and local changes before edits;
4. state any conflict between the request, this seed, and observed workspace
   state instead of silently choosing a different authority;
5. keep the task on the existing branch unless the maintainer explicitly asks
   for a branch operation.

Before any source-code mutation, also complete the mandatory contract preflight
in `D:\code\ccode\labtalk\ai_portal\SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`.
Source authority does not mean source is unconstrained; registered contracts
and source usage/contract annotations must be read before editing.

For runtime/source work, continue in this order:

1. change and prove the work in `D:\code\ccode`;
2. select only the clean, relevant files for `C:\x64base`;
3. compare staged files with the intended development result;
4. test the staged/public form in proportion to risk;
5. commit and push from `C:\x64base` only when authorized.

## Mandatory Long-Build Operator Handoff

Full, clean, dependency-restoring, or otherwise long-running compile/build
scripts are maintainer-operated PowerShell handoffs. An AI partner must prepare
the exact command, working directory, expected outputs, and success/failure
evidence, then return control to the maintainer to run it.

- Do not start, poll, or babysit a long build unless the maintainer explicitly
  authorizes that build in the current task.
- Quick, bounded configuration checks, targeted tests, and artifact inspection
  may be run by the AI when they are proportionate to the task.
- Treat an interrupted or timed-out build as unproven. Do not infer success from
  partial output or prior artifacts.
- After the maintainer runs the handoff, record the command, exit status, key
  output, artifact timestamp, and any supplied transcript before advancing the
  proof or promotion gate.
- Never assume the artifact directory from the configuration name. Read the
  actual target path from the final build output and verify that exact file.
  In the current staged Visual Studio layout the DotTalk++ target is
  `C:\x64base\build\src\Release\dottalkpp.exe`, not
  `C:\x64base\build\Release\dottalkpp.exe`.

This handoff rule applies in both `D:\code\ccode` and `C:\x64base`, and to a
long website build in `D:\dev\x64base-site`. It does not move source authority
or permit a build result to replace behavioral proof.

## Mandatory Task Closeout

Do not report a source task as complete without distinguishing these states:

- development files changed in `D:\code\ccode`;
- development proof run and its result;
- files promoted to `C:\x64base`;
- staging/public proof run and its result;
- commit created in `C:\x64base`;
- branch and commit pushed to GitHub.

Report only the states actually completed. Name the root, branch, and commit
when relevant so the next AI conversation can resume without guessing.

## Authority and Permission Boundary

This seed records project truth and workflow; it does not grant standing
permission to mutate, commit, push, publish, delete, reset, clean, or change
branches.

- The maintainer declares project locations, workflow, and task authorization.
- Source defines implementation.
- Runtime and tests provide proof.
- HELP and reviewed documentation explain proven behavior.
- The AI Portal selects and carries this context forward.

If another document or AI conversation conflicts with these seeds, surface the
conflict to the maintainer. Do not invent a third workflow.
