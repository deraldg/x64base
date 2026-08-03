# Pre-Push Gate -- Mechanism Reference V1

    status      : review-needed -- reference, derived from source 2026-08-01
    authority   : tools/staging/prepush_gate.py IS the authority. This document
                  describes it; where they disagree, the source wins and this
                  document is wrong.
    policy home : AI_PORTAL.md "Pre-Push Gate" (the rule and the why)
    this doc    : the mechanism (order, severities, triggers, exit codes)

---

## 0. Why this document exists

`AI_PORTAL.md` "Pre-Push Gate" states the rule and names **two** mechanical
guards. The gate as implemented runs **twelve** checks across five families. The
policy section has not drifted in its *doctrine* -- the rule it states is still
the rule -- but it no longer describes what actually runs, so an agent reading it
cannot predict a block.

This document carries the mechanism only. It deliberately restates no doctrine.

---

## 1. What it inspects, and the trap in that

```
default:    git diff --cached --name-only --diff-filter=ACMR      (prepush_gate.py:167)
--range R:  git diff --name-only --diff-filter=ACMR R             (prepush_gate.py:165)
```

**It reads the STAGED INDEX, not the working tree.** An edit you have made but
not staged is invisible to the gate, will not be reported, and will not be
committed. A green gate says nothing about unstaged work.

**`--diff-filter=ACMR` covers Added, Copied, Modified, Renamed. Deletions are
NOT inspected.** A commit that only removes files passes every content check
trivially.

Corollary worth internalising: the gate answers *"is what I am about to commit
acceptable?"*, never *"is what I changed committed?"* Those are different
questions and only `git status --short` answers the second.

---

## 2. Execution order

Order matters because the first failure can short-circuit everything after it.

| # | Check | Severity | Runs when | Source |
|---|---|---|---|---|
| 0 | `--install-hook` | n/a, exits | flag given | `:341` |
| 1 | **repository role guard** | **HARD, short-circuits** | always | `:344` |
| 2 | collect + classify paths | n/a | always | `:351` |
| 3 | hard-block classification | **HARD (2)** | always | `:368` |
| 4 | data/fixture churn | WARN (3) | always | `:379` |
| 5 | mass change (> 60 paths) | WARN (3) | always | `:391` |
| 6 | embedded UTF-8 BOM | **HARD (2)** | C/C++ files in set | `:400` |
| 7 | AIF-number collision | **HARD (2)** | unless `--skip-aif` | `:412` |
| 8 | AI report-audit | **HARD (2)** | **only if the set touches the report surface** | `:420` |
| 9 | normalization (refcheck/normcheck) | ADVISORY | **only if the set touches the command surface** | `:431` |
| 10 | portal: stale `index.lock` | **HARD (2)** | unless `--skip-portal` | `:457` |
| 11 | portal: house style | **HARD (2)** | unless `--skip-portal` | `:466` |
| 12 | portal: mandatory-tracked | **HARD (2)** | unless `--skip-portal` | `:476` |
| 13 | portal: Session Log row | ADVISORY | unless `--skip-portal` | `:486` |

**Step 1 short-circuits.** If the repository role guard fails, `main()` returns 2
immediately (`:344-349`) and **nothing else runs** -- no classification, no
sub-gates. A sandbox mount fails here, which is why an agent on a mounted copy
sees only that one line.

**A hard block does not stop the run.** Steps 3 onward set `exit_code` and
continue, so one invocation reports every problem rather than making you fix them
one at a time. `exit_code = 2` dominates a previously-set 3 (`:418`); a WARN only
sets 3 `if exit_code == 0` (`:388`, `:397`).

---

## 3. Exit codes

| Code | Meaning |
|---|---|
| 0 | clean, or every WARN acknowledged |
| 2 | hard-blocked |
| 3 | WARN needing acknowledgement (`--allow-data` / `--allow-mass`) |
| 4 | usage or git error (git absent, git command failed) |

---

## 4. The conditional sub-gates -- why sections appear and vanish

Two expensive sub-gates run only when the change set touches their surface. This
is why two consecutive runs can print different sections, which reads as
non-determinism and is not.

**AI report-audit** (`:420-421`) runs only if some path starts with one of
(`:111-118`):

```
docs/maintenance/SESSION_CLOSEOUT_
docs/maintenance/external_ai_intake/
labtalk/ai_portal/
labtalk/registries/ai_report_audit.yaml
labtalk/registries/ai_report_index.yaml
labtalk/registries/projects.yaml
```

**Normalization guards** (`:431-432`) run only if some path starts with one of
(`:132-135`):

```
include/   src/cli/   src/ext/   src/help/
dottalkpp/data/metadata/   tools/fullstack_docs/
```

A docs-only commit outside those prefixes skips both. That is intended, not a
gap: neither guard's finding can be caused by a change that misses its surface.

---

## 5. Classification (steps 3-5)

**HARD BLOCK** (`:56-83`) -- build trees and binaries:
directory segments `/CMakeFiles/`, `/build-msvc/`, `/_tvision_local/`;
path prefixes `build/ out/ dist/ bin/ obj/`;
prefix globs `build-* build_* cmake-build-*`;
suffixes `.exe .dll .lib .pdb .obj .ilk .exp .pch .sln .vcxproj* .recipe .tlog .lastbuildstate`;
basenames `CMakeCache.txt cmake_install.cmake CTestTestfile.cmake build.ninja`.

**WARN / data fixtures** (`:86-94`) -- suffixes `.dbf .dbt .fpt .cnx .cdx .inx .mdx`,
or any path containing `/data/{dbf,indexes,lmdb,help,metadata,manuals}/`.
Cleared with `--allow-data`, which means *the task named this mutation*.

**Mass change** -- more than **60** paths (`MASS_CHANGE_THRESHOLD`, `:52`).
Cleared with `--allow-mass`.

**Embedded BOM** (`:137-145`, `:213-222`) -- a UTF-8 BOM at any offset **after
byte 0** in a staged `.h .hpp .hh .hxx .ipp .inl .c .cc .cpp .cxx`. Byte 0 is
legal; mid-file is the AIF-062 regression that breaks MSVC with C3872/C2014.

---

## 6. House style, and the whole-file trap

`check_house_style.py` checks **ADDED LINES ONLY** (`:463-465`). The existing
non-ASCII backlog never blocks anyone; new violations become impossible.

**The trap:** staging a previously-**untracked** file makes *every* line an added
line. Correcting one word in an untracked document therefore submits the entire
document to the check, and it will be blocked for characters you did not write.

That is the gate working correctly. The right response is almost never to
sanitise someone else's document -- it is to unstage it, because tracking a
document you did not author is a separate decision from fixing a typo in it.

---

## 7. Missing versus broken -- a real asymmetry

**A missing sub-script is skipped, never fatal.** `_run_portal_check`
(`:295-313`) returns 0 when the script does not exist, with an argued rationale
in its docstring: the portal checks are newer than the gate, and hard-failing
because an optional check is absent would wedge exactly the people it protects.
`run_aif_collision_gate` (`:232`), `run_report_audit_gate` (`:249`) and
`run_normalization_guards` (`:264`) each skip a missing script the same way.

**A sub-script that EXISTS and CRASHES is reported as a substantive finding.**
`run_report_audit_gate` (`:253`) returns the subprocess exit code, and `:424-428`
renders any non-zero as:

> BLOCKED -- AI report-audit found hard findings (a closeout is missing its
> `ai_report_audit` envelope, or a report id is duplicated).

Observed 2026-08-01: `audit_trail.py` exited non-zero with
`ModuleNotFoundError: No module named 'yaml'`, and the gate reported the message
above. **Neither named cause was true.** The validator never ran.

`_run_portal_check` catches `OSError`/`SubprocessError`, but that covers failure
to *launch*, not a non-zero exit from a script that launched and then died.

**Recorded as a defect, not documented as behaviour.** A wrong specific cause is
worse than a generic failure, because it sends the reader hunting for a missing
envelope that does not exist. Owner: AIF-082 (the portal-gate surface).

---

## 8. Hook installation, and which Python runs

```
python tools/staging/prepush_gate.py --install-hook
```

delegates to `repository_role_guard.py --install-hooks` (`:287-292`). The
installed `.git/hooks/pre-commit` is `/bin/sh` and selects its interpreter as:

```sh
PY="$(command -v python3 || command -v python)"
```

**`python3` is preferred.** On Windows that frequently resolves to a *different*
interpreter than the `python` on the PowerShell PATH -- and therefore a different
site-packages. A gate that passes when run by hand and fails under the hook is
this, not a code difference. `command -v python3` from Git Bash identifies the
one that needs the dependencies.

Hooks are not version-controlled. `--install-hook` is per-clone, per-worktree.

---

## 9. Flags

| Flag | Effect |
|---|---|
| `--range R` | inspect a commit range instead of the staged index |
| `--allow-data` | acknowledge intentional data/fixture changes |
| `--allow-mass` | acknowledge a change set over 60 paths |
| `--strict-aif` | promote AIF ledger/intake reconciliation to hard failure |
| `--skip-aif` | skip the AIF-number collision gate |
| `--skip-report-audit` | skip the portal report-hygiene gate |
| `--skip-norm` | skip refcheck/normcheck |
| `--strict-norm` | promote catalog drift to a hard block (exit 2) |
| `--skip-portal` | skip all four AIF-082 portal checks |
| `--install-hook` | install managed commit + push hooks, then exit |

`git commit --no-verify` bypasses the hook entirely. Legitimate when the gate has
been run standalone against the same staged set and passed -- record why in the
commit message.

---

## 10. Severity design

The AIF-082 comment block (`:445-449`) records the measurement behind the
severities: obligations carrying a gate held 83-94 percent compliance; the one
without a gate held 33. Severities differ deliberately and each is argued in
place, notably step 13 -- a closeout landing without a Session Log row is a WARN
because "refusing it would punish the sessions doing the most work."

---

## 11. Known defects

1. **Crash reported as finding** (sec 7). `ModuleNotFoundError` renders as
   "a closeout is missing its envelope, or a report id is duplicated".
2. **The gate emits non-ASCII while enforcing ASCII.** `prepush_gate.py` carries
   em-dashes in its own output strings, including the PASS line at `:493`, which
   mojibakes on a non-UTF-8 console codepage. `check_house_style.py` inspects
   added *documentation* lines, so the gate's own source escapes the rule it
   enforces. `AI_ENGINEERING_STANDARDS_SEED_V1.md` sec 4 covers scripts too.
3. **`AI_PORTAL.md` "Pre-Push Gate" names two guards; twelve checks run** (sec 0).

None are fixed by this document. All three are AIF-082's surface.

---

## 12. Evidence tier

**Source-evidenced.** Every claim cites `tools/staging/prepush_gate.py` at a line
number, read at commit `99b32f5e6` (2026-08-01). The sec 7 crash is
**runtime-observed** -- it blocked a real commit in this session.

Not verified here: the internals of the eight delegated sub-scripts. This
document describes how they are *invoked* and how their exit codes are
*interpreted*, not what they check.
