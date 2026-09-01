# DotTalk++ (ccode) -- working notes for Claude

**Start with `labtalk/ai_portal/AI_TIER1_SEED_V1.md`** -- the canonical Tier 1
body: repo roles, mutation guard, git rules, house conventions, and a five-question
stopping rule. This file is a Claude-specific shim over it and must not restate it
(AIF-082, 6.8: two shims that restate will diverge, and have).

Conventions and locations to remember when working in this repo. Keep terse; correct in place.

**Maintenance rule for this file (AIF-082).** Auto-injection guarantees delivery,
not accuracy: whatever is here reaches every session with full authority and no
retrieval friction. So it carries only *invariants* and *pointers to maintained
artifacts*. **No perishable literals** -- versions, counts, lane states, current
targets. If an agent can cheaply measure it, say "measure it" instead of asserting
it. Perishable state lives behind the pointer table in the Tier 1 seed.

## Before designing anything: WALK THE PORTAL PROJECTS

**A session has no memory. The tree does. Reading it is the one duty that does
not depend on remembering.**

Before reasoning about how a subsystem SHOULD work -- before proposing a design,
opening a lane, or calling something an open question -- walk the portal, in this
order. Steps 1 and 2 are cheap and answer most of it.

1. **The projects walk.** `labtalk/registries/projects.yaml` -- every project,
   its `lanes:` list and its `docs:`. A subsystem you are about to design almost
   certainly sits in a lane that already exists. `AI_PORTAL.md` section
   "Projects, Lanes, and Promotion (AIF-040)" is the governing doctrine.
2. **The search map.** `labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md` -- go straight
   there, do not scan. Its own rule: **"A scan you did not record is a scan the
   next agent repeats"** -- so when you DO have to grep for something, ADD A ROW.
   That is not optional tidiness; it is how the map stays worth reading.
3. **The intake row.** `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` --
   one row per AIF, naming that lane's design documents.
4. **The lane's plan.** Read the section headed **"decisions already made"**
   FIRST. Several plans carry an explicit *agnostic-planner contract* stating
   they assume no session memory and can be executed from the tree alone by a
   reader with no context. They mean you.

Resolve by intent when you can: `python3 labtalk/ai_portal/recall.py <trigger>`
returns the smallest working set, measured. `trigger.where_is` surfaces the map.

WHY THIS IS AN INVARIANT AND NOT A TIP. The gates are change-set scoped by
deliberate design, so nothing surfaces an adjacent lane that solved your problem
last month. **Nothing will prompt you.** On 2026-09-01 one session re-derived a
buffering finding, a STOP_ON_ERROR measurement, an array reference-semantics
ruling and a procedures lane -- all four already recorded, three in documents
authored by the SAME member identity weeks earlier, and the owner had to point at
prior art three times in one day. OI-024 records the same shape: an hour spent
reasoning about how to govern external AI, in a tree whose external-AI governance
was designed, built, running and published.

Measurement is cheap and worth doing. Re-deriving a ruling is neither.

COROLLARY, for reading code once you are in the right place: an include proves
compilation, a comment proves nothing, and a measurement of one thing is not a
fact about another. Check the CALL SITES, not the declaration.

## Running the CLI over the work directory

Use **`./datarun.ps1`** from `D:\code\ccode`. Do NOT run the raw build exe by hand.

`datarun.ps1` (via `launch-common.ps1`) stages the **newest** built `dottalkpp.exe` into the
runtime bin and runs it over the work data:

- Runtime exe: `dottalkpp\bin\dottalkpp.exe`  (staged copy; `*.exe` is gitignored)
- Runtime data root (cwd when it runs): `dottalkpp\data`
- It also stages the full runtime DLL set beside the exe.

Interactive:  `./datarun.ps1`
Batch:        `./datarun.ps1 -CommandLines 'USER LIST','BBS BOARDS','USER SAVE'`
              (each string is one CLI line; written to a temp `.dts` and run with `--script`)

If it cannot copy the fresh build into the runtime bin (a process holds it), it now warns LOUDLY
and quantifies staleness instead of silently running the old copy.

## Build outputs (MSVC Release, default `pro-md` preset)

- `dottalkpp.exe`   -> `build\src\Release\dottalkpp.exe`   (datarun finds newest across presets)
- `dottalk_bbsd.exe` -> `build\Release\dottalk_bbsd.exe`   (standalone BBS daemon, M6)

Build both:  `cmake --build build --target dottalkpp dottalk_bbsd --config Release`
WSL builds also exist (`build-wsl`, etc.); `.exe` cross-platform via guarded code.

## BBS agent-server daemon (dottalk_bbsd)

- Runs headless via the **`DotTalkBBSD`** logon scheduled task; binds `127.0.0.1:8765` (loopback only).
- Shares the SAME data root as the CLI: `dottalkpp\data` (launched with `--data D:\code\ccode\dottalkpp\data`).
- Log: `D:\code\_bbsd_logs\bbsd.log`. Register/start scripts in `D:\code\` (`register-bbsd-startup.ps1`).
- **Rebuilding the daemon requires KILLING THE PROCESS, from an ELEVATED shell.** A running instance
  locks `dottalk_bbsd.exe` (LNK1104 on build otherwise). `Stop-ScheduledTask -TaskName 'DotTalkBBSD'`
  alone is NOT enough and this line used to say it was: it stops what the scheduler still tracks,
  returns success, and leaves the process running. Measured 2026-08-21, two builds in a row still
  LNK1104 after a clean `Stop-ScheduledTask`. What worked:
  `Get-Process dottalk_bbsd | Stop-Process -Force` **run elevated** -- the task starts the daemon at
  logon, so an unelevated shell cannot end it. Confirm before and after with
  `Get-Process dottalk_bbsd | Select-Object Id, Path`. Restart it afterwards
  (`Start-ScheduledTask -TaskName 'DotTalkBBSD'`) or the BBS stays down until next logon.
- Companion: `AFB-Ollama-Startup` task brings up the isolated WSL Ollama on `127.0.0.1:11434` (version
  `0.9.5` = WSL/isolated; `0.32.3` = Windows/non-isolated -- CHAT must hit the WSL one).

## Shared store + locking

- `dottalkpp` and `dottalk_bbsd` share the on-disk DBF store; there are NO pipes/IPC between them.
  In-memory identity/catalog is per-process, loaded from DBF at startup -- changes need a restart to be seen.
- The engine HAS cross-process cooperative locking (`xbase::locks`, RLOCK/FLOCK/UNLOCK via `.lock`
  sidecars, pid-stamped, stale-owner recovery). The BBS store write paths take a table FLOCK per append.

## Conventions

- DotTalk++ inline comment marker is `&&` (not `#`). Applies to single-token CLI lines; free-text
  commands (BBS POST/CHAT read to EOL) must be comment-free.
- Owner/maintainer: `member.derald`. Author docs as review-needed until committed; mirror `C:\x64base`
  and public repo are separate promotion steps.
- No em-dashes in scripts or docs (maintainer preference); use `--` / `->`.
- **Python 3.12 host tools** (`tools/fullstack_docs/**`, anything importing yaml) run under the
  repo venv `.venv312` via `$py12 = "D:\code\ccode\.venv312\Scripts\python.exe"`. NOT `py -3.12`
  (not installed) and NOT the vcpkg python (minimal, no PyYAML -> `ModuleNotFoundError: yaml`).
  Recipes + the vcpkg-vs-venv rationale: the full-stack flush cookbook interpreters note.

## Sandbox agents: NO mutating git -- but you CAN build and run (AIF-082 2026-07-31, corrected AIF-130 2026-08-26)

If you are running in a mounted Linux sandbox rather than on the Windows host:

- **No git that can take `.git/index.lock`.** No `add`/`commit`/mutate, and NOT
  plain `git status` -- it refreshes the index and takes the lock, which cannot
  reliably unlink across the mount; a killed git leaves a zero-byte lock that
  **blocks the maintainer's commits**. This wedged `D:\code\ccode` on 2026-07-31.
  **Read-only IS allowed and does not take the lock** (verified 2026-08-05, git
  2.34.1: no `index.lock` created): `git --no-optional-locks status`
  (equivalently `GIT_OPTIONAL_LOCKS=0`) for status, and the read-only plumbing
  `git log` / `ls-files` / `check-ignore` / `cat-file`. Use these to inspect the
  tree; still hand every mutating git to the maintainer.
  **NOT `git diff`, in ANY form, including `--stat` / `--shortstat` / `--numstat`.**
  `--no-optional-locks` suppresses the index refresh for `status` but NOT for
  `diff`: measured 2026-08-17, `git --no-optional-locks diff --shortstat` created
  `.git/index.lock`, could not unlink it (`Operation not permitted` across the
  mount), and left the zero-byte lock this bullet exists to prevent. The
  allow-list above is exhaustive, not illustrative -- a command's being
  conceptually read-only does NOT mean it leaves the index alone. To size
  uncommitted work from a sandbox use `git --no-optional-locks status --porcelain`
  (file counts only); for line counts, ask the maintainer to run `diff` host-side. **`claim-aif` no longer shells
  out to git** (AIF-135, 2026-08-30: the repository-wide citation grep was
  removed from the allocation universe), so the claim path itself runs
  anywhere; `session_coordinator.py status` still greps and stays host-side. **Measured 2026-08-26: `git add` from a
  sandbox works but LEAVES A LOCK IT CANNOT UNLINK** -- the add succeeds, then
  warns `unable to unlink .git/index.lock`, and the NEXT add fails with "another
  git process seems to be running" until that zero-byte lock is moved aside. So
  pass every path to ONE `git add`, or clear between adds; and an `add` whose
  stderr you filtered is not an `add` you verified -- one returned exit 0 here
  and staged nothing. **`git commit` does not work from a sandbox at all** -- the `pre-commit` hook runs
  `repository_role_guard.py` then `prepush_gate.py`, minutes of work that
  outlives a sandbox tool's per-call timeout, and a killed commit leaves exactly
  the zero-byte lock this bullet warns about (it happened twice that night).
  **So: stage from here, commit from the host.** A sandbox cannot delete either,
  so an orphaned lock must be `mv`d aside, not removed.
- **YOU CAN BUILD AND RUN. Do not file work as blocked without trying it.**
  This bullet used to read "assume you cannot build or run the engine" and drew
  a `g++ -fsyntax-only` ceiling from a 2026-07-31 toolchain table. That was
  measured false on 2026-08-12 and corrected in `AI_README.md` on 2026-08-25 --
  and NOT here, which is where a Claude session actually starts. Four agents
  re-derived it. **Measured, on the whole stack, not just the engine:**

      dottalkpp        full build, ~9 min; REGRESSION RUN WORKSPACE_WRITEBACK
                       green twice (2026-08-12 mounted sandbox; 2026-08-25
                       cloud container)
      metacollect      UNDER 40 SECONDS, g++ -O0 -j4, no cmake needed --
                       `dt_meta` at CMakeLists.txt:771 enumerates every TU
      store rebuild    CMDHELP BUILD LEGACY + BUILD . <src>, 2.9 seconds
      python tooling   manualgen, the harvest exporter and the page generator
                       all run; a sandbox may carry SEVERAL interpreters
                       (3.10/3.11/3.12/3.13 seen side by side), so a tool
                       pinned to one version is usually a routing problem,
                       not a wall

  **Measure your own; never cite this file for versions** -- `ldd --version`,
  `command -v cmake ninja g++`, `ls /usr/bin/python3.*`. Absent by default is
  not prevented: pip, apt, or a preinstalled image each fix it.

  **What is still true:** the staged `dottalkpp/bin-wsl-lean/dottalkpp` is built
  against the host's newer glibc/GLIBCXX and will not execute here. That is a
  property of THAT BINARY, not a ceiling on the sandbox, and conflating the two
  is what produced the false rule.

  **A sandbox green is not a green on the maintainer's toolchain.** Name the
  platform every time. The sandbox's job is to PREDICT and to REFUTE; it is
  never the authority. Recipe and traps:
  `docs/agents/HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md`. Host-vs-
  sandbox detail: `AI_README.md`, "A sandbox is not the WSL host". What this
  changes about the doc push:
  `docs/maintenance/lanes/full_stack_documentation/AI_PUSH_AUTOMATION_WHAT_THE_SANDBOX_CHANGES_V1.md`.
- **`repository_role_guard.py` will refuse a root it does not recognise.** In
  the sandbox that is correct and expected -- the mount path is unrelated to
  either declared root (`AI_PORTAL.md`, "Sandbox / non-host agents"). Verify the
  slice by hand and hand it over.
  Corrected 2026-07-31: this was previously described as a sandbox issue. It was
  a path-FORM issue, and WSL hit it identically -- `/mnt/d/code/ccode` is the
  development root spelled in POSIX, and the guard refused it. Fixed in
  3dd3871ef. If a guard or gate blocks you, read its message before assuming
  "sandbox"; that assumption sent one session looking in the wrong place.

Full WSL build/run detail and the host-vs-sandbox table: `AI_README.md`,
"WSL working environment".

## Commit coordination + pre-push gate (AIF-050)

Concurrent AI sessions share ONE working tree, so commits go out as scoped, per-path
slices -- NEVER `git add -A`/`git add .` (that fuses several sessions' half-done work).
`git status --short -uall` between add and commit is the safety check. **Keep `-uall`.**
This repo sets `status.showUntrackedFiles=no`, so a bare `git status` shows nothing at
all for a file you just created: an unstaged NEW document is indistinguishable from a
clean tree. Measured 2026-08-17 (OI-008), after the prescribed check reported clean
while five new files sat unstaged.

Anti-collision loop (prevents two sessions claiming the same AIF-NNN lane number):

- **Claim/release numbers:** `python tools/coordination/session_coordinator.py claim-aif`
  (atomic `O_EXCL`); the ledger lives at `coordination/aif/AIF-NNN.claim` (tracked).
  `coordination/active_sessions/` and `coordination/locks/` are transient (gitignored).
- **Quip a co-session:** `session_coordinator.py quip send --from <run> --to <run|all> --msg "..."`
  and `quip read --run <me> [--ack]` -- an ephemeral heads-up between concurrent sessions (the
  lightest coordination rung; `coordination/quips/` is transient). Guarded by
  `tools/coordination/test_session_coordinator.py`. Full policy: `AI_SESSION_COORDINATION_PROTOCOL_V1.md`.
- **Detection:** `tools/coordination/aif_collision_gate.py` hard-fails (exit 1) a duplicate
  AIF number in the intake queue.
- **Enforcement:** `tools/staging/prepush_gate.py` runs that gate by default and HARD-blocks
  (exit 2) on a duplicate. It also blocks build trees/binaries and warns on data fixtures.

**Per-clone one-time setup (hooks are NOT version-controlled):**
`python tools/staging/prepush_gate.py --install-hook` installs `.git/hooks/pre-commit`, so
every `git commit` runs the gate automatically. Re-run on each machine/clone/worktree.
Bypass one deliberate commit with `git commit --no-verify`.

Authoritative doctrine: `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`.
