---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260816-COWORK-001
  recorded_at_utc: 2026-08-16T15:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: cab673a20
  authorization:
    requested_by: maintainer (member.derald), in-session, "document all and do your house work and the golden rule"
    scope: >
      Session closeout for a run spanning two repositories. Records the local-path
      detector consolidation, the CI licence-posture repair and its route to main,
      the repository role guard gaining a PR-branch role, four defects found on the
      published website, the RETRO local-only surface, and the EDREF catalog shape
      settled before population. Includes an explicit ground-truth ledger, because
      a large share of this session's work was host-only.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_GUARDS_SITE_AND_EDREF_SHAPE_2026-08-16.md
    kind: session_closeout
---

# Session Closeout -- guards, the published site, and the EDREF shape

Date: 2026-08-16 (work spans the evening of 2026-08-15 and the morning of 2026-08-16).
Owning lifecycle: PDLC.
SDLC lane: tooling / publication.
Repositories touched: `D:\code\ccode` (development), `D:\dev\x64base-site`
(`codex/lean-sites-publish`), and one branch cut from `origin/main`.

## Why this session existed

The maintainer emailed the Xbase++, Harbour and LMDB projects. Everything below is
downstream of one question: what does a developer from those lists see when they
arrive, and is any of it a lie.

## What landed, by commit

| commit | repo | what |
| --- | --- | --- |
| `199ad511b` | ccode | GnuCOBOL acknowledgement, closing a gate the project had opened against itself; GCC 15.1 `gcobol` parked as an unevaluated alternative |
| `dec2f3802` | ccode | `source_policy.py` asserts the decided GPL-3.0 posture; the README licence section, which had never been committed |
| `0dc63f4b9` | ccode | `tools/common/local_paths.json` -- one local-path authority replacing nine private regexes |
| `b105ae99a` | ccode | the licence gate fails cleanly when `LICENSING.md` is absent, instead of raising `FileNotFoundError` |
| `1e3a94a1d` | ccode | role guard recognises a PR branch cut from `origin/main` in a linked worktree |
| `0c4a13f74`, `329b3caee` | main (PR #13) | the above, carried to public main |
| releases 125-128 | site | header fits, code blocks readable in light mode, release stamp visible, visitor counter with a working opt-out, third-party credits |

## The findings, in the order they matter

**1. Nine local-path detectors, seven blind to the environment agents run in.**
A task titled "consolidate the four detectors" found nine. Seven matched only
`[A-Za-z]:` drive letters, while `CLAUDE.md` states agents run under WSL and in
mounted sandboxes. Measured: 3,063 POSIX host paths across the tracked tree,
12 files carrying them with no drive letter at all -- reported clean by every one
of those seven, including the staging guard written the same day by an agent that
had read the WSL section. Recorded as
`proof.tooling.local_path_detector_consolidation`.

**2. The CI gate was the drift.** `Repository policy` had been failing on public
main. Cause: the gate asserted `LICENSE` read "To be determined." -- a policy the
project replaced on 2026-08-08. Two builds were passing the whole time. The repair
also surfaced that the README's dual-licence section had never been committed and
that `LICENSING.md`, allow-listed for promotion since the decision, had never been
promoted. All three had to travel to main together or CI would fail on a new line.

**3. The role guard refused the documented path to main.** Cutting a PR branch from
`origin/main` in a worktree was blocked, so the only way through was
`git commit --no-verify` plus `git push --no-verify`. That is the worst available
outcome: a guard that forbids a safe operation teaches the operator to switch it
off, and `--no-verify` disables every check behind the hook, not one. The guard now
recognises that case under four conditions, each proven to fail when removed. 17
tests, and mutation testing exposed one of them as fake -- see below.

**4. The local site could not execute JavaScript.** Five rounds of theme-toggle
"fixes" had been judged against `localhost:3000`, which is the reports gateway
proxying `next dev`. The gateway proxies GET/HEAD via `urllib` and cannot carry a
WebSocket upgrade, so HMR never connects and React never hydrates: 3/490 elements
had a fiber, against 445/493 direct on `:3002`. The HTML is byte-identical through
the proxy and every chunk loads; the only console difference is that
`[HMR] connected` appears on `:3002` and never on `:3000`. Nothing errored. The
theme button had never worked there, and nothing said so. `-Built` mode is the
workaround; real WebSocket proxying is the fix, unwritten.

**5. Four defects on the published site**, all invisible in dark mode and all
measured rather than eyeballed: the nav needed 1,324px against a 1,152px container
so every page scrolled sideways; code blocks rendered at 1.2:1 contrast in light
mode ("ghost scripts") because Tailwind Typography's `pre` default is light text
for a dark chip and only the background had been overridden; the hero caption sat
at 1.24:1; `--brand` runs 4.21:1 across 61 uses. The first three are fixed and
verified live. `--brand` is not.

**6. An empty catalog advertised as supported.** Recorded separately as
`proof.tooling.catalog_state_blindness`.

## Ground truth ledger (the golden rule)

Stated plainly, because most of this was host-only and the rule exists because
confident reasoning has broken this project before.

**Verified by running, output read:**
- `local_paths.py` selftest, 22/22, and the corpus sweep behind finding 1.
- `source_policy.py` on the working tree, and on a fabricated copy of main's actual
  state -- five clean errors, exit 1, no traceback.
- `repository_role_guard.py` against the real worktree: BLOCKED before, PASS after.
- 17 guard tests, plus three mutations each producing a failure.
- `refcheck_v1.py` on true exit codes, four mutations.
- `edrefcheck_v1.py`, eight arms, each fired.
- `edref_csv_v1.py` round trip: 29 entries, 16,882 characters of prose, byte-identical.
- The live site at release 128, in the browser: overflow 0, code-block colour
  `rgb(10,19,32)`, release stamp present, counter `silent` mode producing **zero**
  requests to the counting service and `quiet` producing one that cannot count.
- PR #13: `CI / Repository policy (pull_request) -- Successful in 6s`.

**NOT verified, and must not be reported as done:**
- **No C++ was compiled this session.** The `edref.hpp` struct change is additive
  with default member initialisers and C++20 permits that for aggregates, so the 29
  existing brace initialisers should still compile -- *should*. It has not been built.
- `rebuild-staging.ps1` reads the new pattern via `ConvertFrom-Json`; the .NET regex
  engine never executed it. Constructs are .NET-legal by inspection only.
- `verifyLiveReleaseArtifact()` in the publish script was untested when written; it
  has since run twice for real and passed, so this one has been discharged.
- The two remaining site contrast defects are measured but unfixed.
- `edrefcheck_v1.py` is not wired into `prepush_gate.py`; it runs only when invoked.

## Errors made in this session, recorded

Six instances of one error, kept because the pattern is the finding: a check was
believed because the visible part looked right. The opt-out was verified by reading
its URL while the network showed it still firing. A test in the new guard passed
with its rule deleted, because the only case exercised was refused for an unrelated
reason -- caught by mutation testing, not by review. The EDREF parser reported 28 of
29 and passed, because it required a trailing comma the last entry does not have.
A pipeline's exit code was read as the tool's, reporting 0 for a run that printed
FAIL -- the third recorded instance of `${PIPESTATUS[0]}` in this project. Twice,
shell fragments meant as explanation were placed in code blocks and pasted into
PowerShell.

## Still open

- `--brand` at 4.21:1 across 61 uses, and the hero caption at 1.24:1.
- Eight Python local-path detectors still carry private regexes.
- Gateway WebSocket proxying, so `next dev` behind `:3000` hydrates.
- EDREF storage direction: generate-header-from-CSV, or CSV-seeds-DBF-at-runtime.
  The round trip is proven either way; the decision is a product one, because the
  second makes HELP depend on data files.
- `edrefcheck_v1.py` into the prepush gate.
- `start-ai.ps1`'s header warns that dev mode breaks search. It breaks all
  client-side React. The warning was true and far too narrow.
