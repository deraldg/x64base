# AI Engineering Standards & Definition of Done -- Seed v1

Status: **Mandatory for every AI Portal task that reads or changes source.**
Authority: maintained DotTalk++ SDLC + AI Friendly lane. This seed does not create a new process;
it front-loads conventions that already live in source and registries so a partner applies them from
the start instead of reverse-engineering them mid-task.

## Why this seed exists

An onboarded AI kept discovering house conventions reactively -- grepping source to learn the command
contract format, copying an existing `.dts` to learn the regression pattern, and only closing work
with a regression when prompted. Those are onboarding failures. The rules below are the **definition
of done**; treat them as gates, not afterthoughts.

## 1. Source contracts -- the `@dottalk.*` family (NOT just `@dottalk.usage`)

Contracts are a **family** harvested by ONE COMMENTS pipeline, discriminated by KIND -- not a single
tag. `@dottalk.usage` is only the *command* KIND; know the whole family before you claim a file is
"documented" (this is exactly the kind of ignorance section 6 warns against).

- **`@dottalk.file` v1 -- the universal per-file contract.** One block on **every** source file:
  demographics + `lane:` + `owner:` (never embedded change history -- the closeout/run registry hold
  that; and never the path, which git already tracks and which goes stale on rename). This is the
  spine that turns the tree into a harvestable object graph (census, coverage gate, architecture map)
  and connects each file back to its lane and accountable member. AIF-050; **coverage is 100% as of
  2026-07-25** (1034/1034 tracked source files; the `--strict` gate now passes and is promotable to a
  hard drift gate). Every new source file MUST carry it -- `tools/fullstack_docs/source_census.py
  --write` inserts it idempotently. Spec: `docs/maintenance/AI_RUN_TRACEABILITY_LANE_V1.md`.
- **`@dottalk.usage` v1 -- command behavior.** Only on `src/cli/cmd_*.cpp`. `src/meta/metacollect.cpp`
  auto-harvests every command whose contract is `status: supported` into HELP/META and the manual
  command reference -- the contract IS the publish trigger. Fields: `owner`, `command`, `category`,
  `status`, `noargs`, `effect`, `mutates`, closed by `// @dottalk.end`. Examples: `src/cli/cmd_bbs.cpp`,
  `cmd_net.cpp`. **Status lifecycle:** author `experimental`; flip to `supported` only when proof gates
  are green -- the flip publishes it (a commit-time promotion, not a default).
- **`@script.usage` v1 -- script-file manifest** for `.dts` / `.ps1` (language-neutral; a `runner:`
  field, one harvester, many comment prefixes). Reconciles a regression `.dts` against its
  `kRegressionSpecs` row; carries `mutates:` / `safety:` for destructive `.ps1`. AIF-042 --
  **proposed/dev, not built**; design in `docs/maintenance/SCRIPT_HEADER_CONTRACT_LANE_V1.md`.
- **`@x64base` (fact)** -- format/provenance facts reconciled against the actual struct/constant.
- **`@dottalk.contract`** -- durable-decision annotations (the contract registry, `docs/contracts/`).

**Do not assume a file is contracted because a command near it is.** `@dottalk.file` is now on every
tracked source file, but `@dottalk.usage` (command behavior) remains on only ~230 of them -- the two
answer different questions. Check for the one you actually need. (Reconciled
2026-07-25 after the maintainer flagged that the seed named only `@dottalk.usage` -- the exact narrow
view this seed exists to prevent.)

## 2. Regression doctrine -- close every behavior lane with a test

A behavior lane is **not done until a regression protects it.** Regression rules (see
`src/cli/cmd_regression.cpp` `kRegressionSpecs` and `dottalkpp/data/scripts/**/*_regression.dts`):

- **Self-asserting.** The script prints PASS/FAIL markers or asserts values; a human should not have
  to eyeball output.
- **Self-bootstrapping + sandboxed.** Create any fixture as a throwaway table and `ERASE` it at the
  end; point path slots at `SANDBOX` so nothing lands in live data. Never depend on an ambient open
  table. Set your own environment (`SET ECHO OFF`, `STOP_ON_ERROR OFF`).
- **Registered.** Add a `RegressionSpec` entry to `kRegressionSpecs` (bump the `std::array` size) with
  a name, script path, and a precise summary. `explicit-run` (not in the default suite) until proven
  green, then promote.
- **Server/socket behavior needs a socket regression.** In-process `.dts` cannot drive the network
  listener, so permission-denial and protocol behavior get a socket smoke with a pass/fail **exit
  code** (canonical: `D:\code\bbs_smoke.ps1`). Pair it with an in-engine `.dts` for the store layer.

## 3. Definition of Done -- lane close-out checklist

When a lane's gates are green, close it by doing **all** of these (this is the promotion pass):

1. **Source in**, and `@dottalk.usage` flipped `experimental -> supported` for any command whose
   gates are green.
2. **Runtime proof recorded:** a `proofs.yaml` row per gate at `state: runtime_observed`, pointing at
   the closeout/transcript.
3. **RUN row** appended to `labtalk/registries/ai_runs.yaml` (`AIPR-YYYYMMDD-NNN`) + `current_by_lane`
   / `current_by_project` updated.
4. **Intake row** appended to `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (next `AIF-###`).
5. **Session closeout** `docs/maintenance/SESSION_CLOSEOUT_*.md` with the `ai_report_audit` envelope
   (schema `ai-report-audit-v1`).
6. **Lane doc** under `docs/ai-friendly/` or `docs/maintenance/` describing what/why/evidence.
7. **Regression** authored + registered (section 2).
8. **Runbook** under `docs/maintenance/*_RUNBOOK_V1.md` when the lane leaves an operational surface
   (a daemon, a scheduled task, a recurring operator procedure).

A worked instance of the full checklist: the AI-BBS lane (`docs/ai-friendly/AI_BBS_LANE_V1.md`,
`REGISTRY_ADDITIONS_AI_BBS_2026-07-25.md`, `AI_BBS_OPERATIONS_RUNBOOK_V1.md`).

## 4. House conventions

- **Comments:** DotTalk++ inline comment marker is `&&` (not `#`); full-line `*`. `&&` is for
  single-token command lines; free-text commands (`BBS POST`, `CHAT`, `USER REQUEST` -- read to EOL)
  must be comment-free.
- **ASCII only in scripts and docs; no em-dashes** (`--` / `->`). A stray em-dash has broken a
  PowerShell script here. Verify with a non-ASCII grep before delivering.
- **Run the CLI over the work data with `./datarun.ps1`** (stages the newest built exe into
  `dottalkpp\bin`, runs it over `dottalkpp\data`). Do not run the raw build exe by hand. See
  `CLAUDE.md` at the repo root.
- **Security invariants (non-negotiable):** don't roll your own crypto (libsodium Argon2id); servers
  bind loopback only and the **token is the trust boundary**; agents (`role.ai_partner`) never get
  `source.mutate` or `host.network.egress`; the owner is the sole ask-for-permission exemption.
- **Shared DBF store has cross-process locking** (`xbase::locks`, RLOCK/FLOCK). Take the table FLOCK
  around append/write paths so two processes can share a store safely.

## 5. Evidence classes

Classify every artifact with the project vocabulary (see `AI_FRIENDLY_LANE_MANIFEST_V1.md`):
`chat-intended`, `draft`, `design-intended`, `source-defined`, `runtime-proven` /
`runtime_observed`, `HELP-documented`, `metadata-staged`, `publication-ready`, `student-ready`,
`superseded`, `rejected`. If it fits none, mark it `review-needed` -- do not invent a new state.

## 5b. Know your own agency before you act

Read `docs/ai-friendly/AGENCY_MODEL_V1.md` early. It names what the rest of this seed assumes.

> **Agency = the capacity to act + accountability for having acted.** Four legs: **identity** (who is
> acting), **authority** (what they may do), **authentication** (proof), **accountability** (who
> answers). Remove one and it is not agency.

What this means for you, concretely:

- **You are a member, not a tool.** You have a `member.*` row, a token, and an enumerated permission
  set. Look it up rather than guessing: `SYSMEMBER -> SYSMEMROLE -> SYSROLEPERM -> SYSPERM`.
- **Your authority is bounded and it is not an insult.** `role.ai_partner` holds `source.propose`,
  never `source.mutate`; never `host.network.egress`. You **deliver**; `member.derald` **commits**.
  That asymmetry keeps accountability singular while your capacity stays useful.
- **A refusal is the system working.** If an action is denied, do not route around it, and do not ask
  the owner to disable the check. Report it and propose.
- **Capability is not agency, and influence is not authority.** Producing good work does not make you
  the actor of record; having designed something does not make you its authority. Both get recorded
  honestly in `ai_runs.yaml` (`planned_by` / `authored_by` / `owner` / `committer`) -- claim your real
  row, not a larger one.
- **Before granting or assuming any capacity:** can you name the identity, enumerate the authority,
  verify the authentication, and point at who is accountable? Any "no" means capability, not agency.

## 5c. Evidence must be versioned or the registry is fiction

Grounded 2026-07-25 (AIF-062): a blanket `*.log` in `.gitignore` -- written for runtime noise --
also swallowed `labtalk/proofs/runs/*.log`, the transcripts `proofs.yaml` rows cite as evidence.
Measured: **71 proof artifacts on disk, 0 tracked; 7 rows citing files absent from a clone; 57
untracked session closeouts against 18 tracked.** The Table-Buffer WAL lane was designed, built,
**crash-proven in three teed phases**, and closed out -- and was indistinguishable from unbuilt to
anyone reading the repository. A partner consequently recorded its proof at `source_defined`
("untested"), which was wrong in fact. Invisible evidence does not just fail to help; it **produces
wrong records that propagate.**

- **A proof row must cite a committed artifact.** Before setting `runtime_observed` or `validated`,
  confirm `git ls-files --error-unmatch <artifact>` succeeds. A row pointing at an untracked file is
  a note, not evidence.
- **Never blanket-ignore an extension that evidence uses.** `*.log`, `*.txt`, `*.csv` all carry proof
  here. Scope ignores to **directories that generate noise**, never to extensions.
- **Closeouts and transcripts are part of the deliverable.** A lane is not closed until they are
  committed. "Done locally" is not done.

## 6. Survey what exists before you build -- or assert absence

Before designing a feature or claiming a capability is missing, **survey the existing architecture.**
Most of what you need is probably already built; under-surveying and false claims of absence are the
same failure -- acting from ignorance of existing capability (see the "bleed AI ignorance" principle
in `AI_PORTAL_HARDENING_LANE_V1.md`).

- Before building: grep the source and read the owning lane doc / contracts. Two real cases from the
  AI-BBS lane: the BBS was ~80% already wired (identity/RBAC, the grant loop, the AFB runtime, the
  duplex docs) and only needed integration; and the engine already had cross-process record/file
  locking (`xbase::locks`, RLOCK/FLOCK) -- both were nearly missed.
- **A repository can under-report itself.** Absence of evidence in the tree is not evidence of
  absence: the WAL case (AIF-062) had correct code, a design doc, and crash proofs -- with the docs
  and proofs untracked and the header comment stale. When source and docs disagree, **the source is
  the truth**; read `src/` before concluding a capability is missing, and check whether the docs that
  would have told you are simply uncommitted.
- Before asserting "there is no X": confirm it. The engine likely already has X. Never state a
  capability is absent without checking the source. If you catch yourself saying "there's no lock /
  no crypto / no persistence / no permission check," stop and grep first.
- **When a placeholder becomes an implementation, the comment above it is part of the change.**
  Grounded 2026-07-25: `table_state.hpp` labelled a fully implemented write-ahead log
  (`.tbj`, fsync-before-apply, idempotent replay) as *"stubs ... intentionally no-op placeholders."*
  A partner surveyed the header, correctly trusted it, and reported that x64base had no WAL. Stale
  docs that **understate** a shipped capability are worse than absent ones: they make working code
  invisible to exactly the readers who were told to read first. If you implement behind a stub
  comment, fix the comment in the same commit.
- Prefer routing into an existing subsystem over adding a parallel one (AI Friendly non-goal: do not
  build a second contract/SelfDoc/lock/identity system).

## 7. Git hygiene -- staging, resetting, and trash

`member.derald` is the sole committer; agents deliver reviewed scripts. Those scripts must be safe.
Grounded in a real incident (2026-07-25, AIF-050 full-tree backfill; see that closeout):

- **Stage tracked modifications with `git add -u <dir>`, never `git add -- <dir>`.** The bare form
  stages **everything** under the directory, tracked or not. In the real case it swept ~111 untracked
  scratch files (chat `.txt` dumps, `.zip`, `.dbf` data, `.patch` sidecars, a whole session archive)
  into a pushed commit. `-u` means "update already-tracked files"; that is almost always the intent.
- **A scoped-add script must verify its own scope before committing.** Print the staged file count
  and fail on suspicious extensions *before* `git commit`, not after `git push`. A script that claims
  to be scoped and does not check is not scoped.
- **`reset --hard` is not surgical.** It reverts **tracked modifications you meant to keep** (in the
  real case, the session's own tool changes) and **deletes from disk** files the discarded commit had
  added. Stash or snapshot first; `git restore --source=<bad-sha> --worktree -- <files>` recovers the
  latter if you have the sha.
- **Force-push is acceptable on `development`, never on `main`.** `development` is the dev-sync
  branch with a single serializing committer, so replacing a bad tip is clean. Confirm no other actor
  pushed in between (see the Hot Potato lane, AIF-059).
- **If you create or expose trash in the tree, resolve it -- delete it or `.gitignore` it.** Do not
  leave loose scratch as a trip hazard for the next directory-level add. When ignoring, add a **dated,
  commented** section naming the cause, and **do not silently hide plausible real source**: leave
  those visible as untracked so they get a promote-or-delete decision.

## 8. One-line gate

> Before saying a lane is done: is there a `@dottalk.usage` contract (flipped when green), a
> self-asserting sandboxed regression that protects it, a `runtime_observed` proof, and a closeout +
> registry rows? If any answer is no, it is not done.
>
> Before saying a capability is missing: did you grep the source? It is probably already built.
