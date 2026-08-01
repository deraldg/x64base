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
- **Rebuilding the daemon requires stopping the task first** (`Stop-ScheduledTask -TaskName 'DotTalkBBSD'`);
  a running instance locks `dottalk_bbsd.exe` (LNK1104 on build otherwise).
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

## Sandbox agents: NO git, and you cannot build (AIF-082, 2026-07-31)

If you are running in a mounted Linux sandbox rather than on the Windows host:

- **Run NO git commands. None.** Even `git status` refreshes the index, takes
  `.git/index.lock`, and cannot reliably unlink it across the mount. A killed or
  timed-out git leaves a zero-byte lock that **blocks the maintainer's commits**.
  This wedged `D:\code\ccode` on 2026-07-31. Read and write files freely with
  file tools; prepare git as commands and hand them to the maintainer.
  `claim-aif` shells out to `git grep`, so it is host-side too.
- **Assume you cannot build or run the engine, and verify rather than trust this
  line.** The sandbox has historically lagged the WSL host on glibc/GLIBCXX and
  carried no cmake, ninja, or lmdb/sqlite3/nlohmann/sodium headers, so the staged
  `dottalkpp/bin-wsl-lean/dottalkpp` will not execute and the ceiling is
  `g++ -fsyntax-only` on single translation units. **Exact versions are
  deliberately not recorded here** -- they are perishable, and you can measure
  yours in one command (`ldd --version`, `command -v cmake ninja`). Measure, do
  not cite this file. Builds and runs are maintainer-operated handoffs either
  way. Host-vs-sandbox detail: `AI_README.md`, "A sandbox is not the WSL host".
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
`git status --short` between add and commit is the safety check.

Anti-collision loop (prevents two sessions claiming the same AIF-NNN lane number):

- **Claim/release numbers:** `python tools/coordination/session_coordinator.py claim-aif`
  (atomic `O_EXCL`); the ledger lives at `coordination/aif/AIF-NNN.claim` (tracked).
  `coordination/active_sessions/` and `coordination/locks/` are transient (gitignored).
- **Detection:** `tools/coordination/aif_collision_gate.py` hard-fails (exit 1) a duplicate
  AIF number in the intake queue.
- **Enforcement:** `tools/staging/prepush_gate.py` runs that gate by default and HARD-blocks
  (exit 2) on a duplicate. It also blocks build trees/binaries and warns on data fixtures.

**Per-clone one-time setup (hooks are NOT version-controlled):**
`python tools/staging/prepush_gate.py --install-hook` installs `.git/hooks/pre-commit`, so
every `git commit` runs the gate automatically. Re-run on each machine/clone/worktree.
Bypass one deliberate commit with `git commit --no-verify`.

Authoritative doctrine: `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`.
