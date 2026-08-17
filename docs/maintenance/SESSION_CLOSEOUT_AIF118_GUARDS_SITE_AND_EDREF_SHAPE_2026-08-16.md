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
    path: docs/maintenance/SESSION_CLOSEOUT_AIF118_GUARDS_SITE_AND_EDREF_SHAPE_2026-08-16.md
    kind: session_closeout
---

# Session Closeout -- AIF-118: guards, the published site, and the EDREF shape

Date: 2026-08-16 (work spans the evening of 2026-08-15 and the morning of 2026-08-16).
Owning lifecycle: PDLC.
SDLC lane: tooling / publication. **AIF-118** (claimed 2026-08-17T01:04:55Z, run `COWORK-20260816-001`, lane
`guards-site-contrast-and-edref-shape`). Charter: `docs/maintenance/AIF_118_SILENT_PASS_GUARD_LANE_V1.md`.
Intake row: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-118).
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
workaround. **FIXED LATER THE SAME DAY, `57de30b35`:** `tools/reports/ws_proxy.py`
detects the upgrade before `_dispatch`, opens a raw socket upstream, replays the
request line and headers byte-for-byte, forwards the `101`, then relays both
directions with `selectors`. Six tests against a real RFC 6455 echo upstream, and
four mutations each proven to fail (never detect the upgrade; compare `Connection`
whole rather than tokenised; drop `Sec-WebSocket-Key`; relay one direction).
**VERIFIED LIVE the same evening, 19:32 local:** through the running gateway,
`:3000` hydrated **436 of 493 elements** (was 3 of 490) and the console carried
**`[HMR] connected`** -- the single line that had only ever appeared on `:3002`.
Confirmed `next dev` with Turbopack rather than a `-Built` static serve, since a
static build hydrates without any socket and would have proved nothing.
Attribution settled by clock, not assumption: the gateway process started
`18:59:56`, three minutes after the commit at `18:56:57`, so this is not the
stale-binary-passing-for-fixed shape this project has hit before.
Two of the verifier's own probes were wrong on the way and are recorded because
the correction is the lesson: a combined measurement returned `{}`, which is a
blank rather than a result, and the direct socket probes targeted
`/_next/webpack-hmr` when this build uses Turbopack and never opens that path.
The app's own console message settled it -- the socket reporting itself, rather
than a guess at its address.

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

## Addendum, same day: the still-open list, implemented

Written after the closeout above, at the maintainer's instruction to implement
what remained. Each item below was measured before and after.

**The light-mode contrast defects are fixed, and the cause was not what the
closeout said.** `--brand` and `--orange` were darkened against a measurement
rather than an eye: brand 4.21:1 -> **4.61:1** on `--bg` and 4.45 -> **4.87:1**
on `--card`, orange 4.29 -> **4.54:1**, hue preserved, dark palette untouched
(still 10.02:1 and 9.00:1).

But the hero caption was a different bug entirely. The closeout reported 1.24:1
and blamed `--fg` over a dark image. Wrong mechanism. The caption sits inside a
bar classed `bg-bg/78`, and Tailwind's opacity scale has no 78 -- so the utility
never generated and the bar's computed background was `rgba(0, 0, 0, 0)`. Not a
wrong background: NO background. The caption was text painted onto a photograph.
A sweep found **six more** off-scale values doing the same thing silently across
five files. All fixed; the caption now measures **11.88:1** in light and 16.49:1
in dark. Recorded as `proof.site.invalid_opacity_renders_nothing`.

**A guard now exists for it.** `scripts/check-opacity-scale.mjs`, wired into
`npm run build` so it blocks before a publish can happen. Verified against all
six original values and verified to let bracket syntax (`bg-bg/[78%]`) through,
since that form is explicit about being unusual. The scale is fixed and
knowable, so this was cheap -- and it would have caught every one of them before
publication.

**start-ai.ps1's warning is widened.** It said dev mode breaks SEARCH. It breaks
all client-side React behind the gateway, which is a different blast radius and
cost five rounds of theme-button "fixes" plus two more today. The header now
carries the measurement (3/490 hydrated via :3000 against 445/493 direct) and
the launcher prints a yellow warning at dev start.

**Four of the eight remaining local-path detectors are migrated** onto
`tools/common/local_paths`: `audit_manual_publication_readiness.py`,
`ecoschema_map.py`, `command_reference_candidate.py`, `regression_index.py`.
Each verified to import, resolve the shim from its own directory depth, and
match both Windows and POSIX host paths without the `https://`-as-drive-`s:`
false positive.

**Four are deliberately NOT migrated**, because they are different shapes and
substituting mechanically would be wrong:
- `artifact_disposition.py:126` -- a path REWRITER with a capture group, not a
  detector.
- `build_gptbase_bundle.py:57` (`_SCRUB`) -- also a rewriter.
- `build_gptbase_bundle.py:58` (`_LEAK`) -- mixes path detection with SECRETS
  (`BEGIN PRIVATE KEY`, `password`, `api_key`). The secrets half is a separate
  concern and should probably become its own named pattern rather than be folded
  in.
- `stage_public.py:39` -- part of a labelled `LEAK_PATTERNS` tuple list using
  dev-roots semantics; wants `dev_roots_only()` and a small restructure.

## Second addendum: the site published, and EDREF settled

**The site is live at release 131**, with the contrast repairs verified on the
published page rather than by arithmetic: hero caption **1.24:1 -> 17.64:1** in
light (16.49 dark), `--brand` **4.21 -> 4.87:1**, horizontal overflow 0. The
theme flag used for testing was cleared afterwards.

**Three guards fired during that publish, and one of them was wrong in a way
worth keeping.** `check-public-content.mjs` blocked the push over
`app/retro/page.tsx` linking to derald.com -- a host deliberately retired in
`c244300da` (2026-07-10). The retirement is correct. The guard was not: it scans
SOURCE and had no concept of a local-only route, so it was policing a file that
`strip-local-only-output.mjs` deletes from every build and that the publish
aborts over if it survives. Fixed by narrowing SCOPE, not the rule -- it now
skips paths under `LOCAL_ONLY_DIRS`, and a published page referencing derald.com
still fails. That is the third list in this repo pointed at that one authority
after two had already drifted.

**The `build` / `build:publish` split**, made earlier the same day, was also
exercised for the first time here. `build` keeps local-only routes so a `-Built`
preview can serve them; `build:publish` strips then packages. Stripping used to
live in `build`, which meant a local preview deleted the very page it was meant
to show while the nav link survived in the bundle -- a link to a guaranteed 404.

**EDREF storage is settled, and nothing needed inventing.** Recorded in full as
`proof.edref.storage_was_already_decided`. The short version: the policy was set
on 2026-07-14 in `lean.manifest` and `educational.manifest`, the DBF already
carried `CATALOG='ED'` with 29 topics, 842 lines and `PRIMARY='EDREF'`, and the
proposed design was correct and five weeks late. What was genuinely missing was
a one-line summary, which existed nowhere: `TITLE` echoed `TOPIC` on all 29 rows,
and `SUMMARY` is a C200 hard truncation sitting at 195-200 chars on every one.
29 titles written, longest 70 of 80, with three new guard arms.

**Four detectors migrated**, four deliberately not -- see the first addendum.

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
