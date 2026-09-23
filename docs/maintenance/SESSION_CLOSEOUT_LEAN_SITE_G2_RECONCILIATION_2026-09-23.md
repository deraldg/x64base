---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260923-001
  recorded_at_utc: 2026-09-23T23:30:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: COWORK-20260811-001 (same conversation, resumed after 43 days)
  project:
    id: project.x64base.website
    root: D:/dev/x64base-site
  git:
    branch: development
    baseline_commit: ee1b446e32f375098189889f79e8dffd95c53220
  authorization:
    requested_by: maintainer
    scope: fix the lean site (dottalkpp.com) -- reconcile its claims against
      development; engine source untouched
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_LEAN_SITE_G2_RECONCILIATION_2026-09-23.md
    kind: session_closeout
---

# Session Closeout -- Lean site reconciled against development; G2 passed (AIF-107)

Date: 2026-09-23.
Owning lifecycle: PDLC.
SDLC lane: publication.
Truth state: mixed -- every runtime-proven row cites a spec verified present in
the registry at ee1b446e3; the specs themselves were NOT run this session.
Proof state: build (site build + check_site + two negative tests of new guards).

Note on project.root: borrowed registered root of project.x64base.website, as
in the 2026-08-11 closeout; no project id exists for the dottalkpp site repo.
Work happened in D:\dev\dottalkpp-lean (site) and, for two docs, this tree.

## One-line summary

43 days after deployment the lean site had joins marked unbuilt, told users to
type a verb that has been a no-op since 2026-09-04, and named four commands
that do not exist; it is now rebuilt from a snapshot of the engine's regression
registry, with build-failing guards so that drift cannot ship silently again.

## Changed (development, D:\code\ccode) -- uncommitted, maintainer to commit

| Area | Files | Note |
| --- | --- | --- |
| lane doc | docs/maintenance/AIF_107_LOW_KEY_ENTRY_SURFACE_LANE_V1.md | truth/proof/risk/next_gate fields; "G2 PASSED" block with findings and mechanism |
| search map | labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md | two rows: "which spec proves X" and "does command X exist" (owed from re-onboarding; scans recorded) |
| closeout | this file | new |
| intake queue | docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md | AIF-107 status cell only |

## Changed (site repo deraldg/dottalkpp, D:\dev\dottalkpp-lean) -- uncommitted

| File | Change |
| --- | --- |
| engine-facts.json | NEW: kRegressionSpecs snapshot via tools/reports/regression_index.py, stamped ee1b446e3 / 2026-09-23 |
| build_lean_site.py | STATUS rebuilt (45 rows, 31 runtime-proven, other sessions' rows carried forward), evidence via `ev()` against the snapshot; FAMILIES corrected; Getting Started, Query, Scripting, Formats pages corrected; banner engine stamp; group order derived; row-count assertion; changelog + README history |
| check_site.py | "SQLsel" brand ban made case-sensitive so the verb SQLSEL is sayable; 30-day freshness advisory |
| generated HTML, CHANGELOG.md, README.md | regenerated; also copied from x64base-lean/ to repo root |

## Verified (proof performed this session)

- Registry snapshot: regression_index.py parsed 84 specs, 32 default (run on
  the mounted tree at ee1b446e3, sandbox). All six specs the August board cited
  are still registered.
- Command names: the site's verbs checked against `registry().add` in src/cli
  -- an INCOMPLETE authority, as it turned out. It reported SHELLO absent;
  SHELLO registers via `dli::register_extension_command` in src/ext, and the
  maintainer's CMDHELP BUILD LEGACY run the same evening lists it IMPLEMENTED.
  Corrected and restored. Final: SMARTBROWSE, SIMPLEBROWSE and URL were not
  verbs; SB is a shortcut for SIMPLEBROWSER.
- Other sessions' work: the site repo carried three post-deploy commits by
  other sessions. The first patch overwrote their STATUS rows (memo-zoo
  promotion demoted, REL JOIN and two-walker rows dropped). Detected by
  comparison with HEAD before push, and restored. Board: 31 of 45
  runtime-proven.
- `SQL` reserved: src/cli/cmd_sql.cpp comment block and print_sql_reserved;
  commit a3243e7aa (2026-09-04).
- Examples: taken from sqlsel_select_v1_regression.dts (default suite) and
  canaries/major_shakedown.dts; `LIST NEXT` absent from cmd_list.cpp.
- Build: build_lean_site.py OK; check_site.py 272 links, 0 broken, 0 orphans,
  0 retired vocabulary; FRESHNESS 0 days.
- Negative test 1: INDEX_TXN deleted from a scratch facts copy -> build exits 1
  naming the spec.
- Negative test 2: two-group order list in a scratch copy -> "status board
  rendered 11 of 43 STATUS rows", exit 1.
- NOT verified: that the 28 cited specs PASS today (not run); the live site
  after push (push not yet done); rendering in a browser (HTML inspected only).
- Platform for all of the above: Cowork mounted Linux sandbox. Not the
  maintainer's toolchain.

## A defect this session nearly shipped

While rebuilding, the status page's hard-coded group list silently dropped the
12 rows in two new groups -- 31 of 43 rendered, every gate green. Caught only by
counting tiers in the output. Now a build failure (negative test 2). Recorded
because it is the Tier 1 section 6 shape, produced by the session that was
fixing that shape elsewhere.

## AI-facing docs updated (AIF-006 gate)

- Lane doc updated (G2 passed; next gate G3).
- Search map: two rows added.
- Intake queue AIF-107 row: status cell updated (G2 passed, next G3, this
  closeout named).
- Session Log row in AI_FRIENDLY_DASHBOARD_V1.md: OWED, deliberately not
  written. The file carries another session's uncommitted edits, and the
  good-neighbor rule wins over the gate. Also observed: the Session Log is
  newest-first, and the steward's 2026-08-11 row was appended at the bottom
  (out of order). Fix both when the file is free.

## Published

- Nothing published. Site repo changes uncommitted; this tree's changes
  uncommitted. dottalkpp.com still serves the 2026-08-11 content until the
  maintainer pushes.

## Handoff left (AIF-082 gate)

No separate handoff file. The durable how-to lives where the next agent will
look: the lane doc's G2 block (mechanism, refresh duty) and the site README
("refresh engine-facts.json from the engine tree whenever the board changes").

## Close-out checks (AIF-156)

1. Status: in this tree, exactly three tracked files modified by this session
   (lane doc, search map, intake queue) plus this new file; measured with a pathspec-scoped
   `git --no-optional-locks status --porcelain -uall`. A whole-tree `-uall`
   timed out at 90 s across the mount, so other sessions' dirty files were NOT
   enumerated.
2. Concurrent work: not touched. In D:\dev\x64base-site another session has
   scripts/check-site-freshness.mjs modified and three untracked
   retirement-polarity files -- left alone.
3. Residue: sandbox-only /tmp/negtest and /tmp/negtest2 (not on the host);
   scratch files in the agent outputs folder (engine-capabilities-v1.json,
   regression_index.md, specs.txt, registered.txt, patch_lean_g2.py); two
   reports written to D:\dev on request (STATE_REFRESH_2026-09-23.md,
   ONBOARDING_EXPERIENCE_REPORT_2026-09-23.md). No grants, env vars, catalog
   rows, or index locks (checked: none in ccode, x64base-site, dottalkpp-site).
4. State a next session needs: engine-facts.json is time-stamped; it goes stale
   as the engine moves, and check_site.py will say so after 30 days.

## Still open -- for the next session

1. Push the site (maintainer): commands are in the chat and in the site README.
2. Commit this tree's four files (maintainer).
3. Session Log row (AIF-006) once AI_FRIENDLY_DASHBOARD_V1.md is free, at
   the TOP of the table (newest-first), and move the 2026-08-11 row to its
   dated position.
4. Unverified rows, flagged in the lane doc: Interface definition language
   (APPLICATION_UI_DSL lane closed out 2026-09-16 may have moved it),
   CDX-on-classic, 64-bit widening.
5. G3: downloads metadata (type, source, proof, accessibility).
6. R4: non-ASCII in rendered HTML still open; new text is ASCII.
7. From the re-onboarding report, maintainer rulings: Tier 0 "no warnings"
   while its own inputs failed; runs registry knows one of at least four run-id
   namespaces; claim files mixed CRLF/LF; seven stale sessions; Tier 1 should
   call the read-only git allow-list exhaustive; AI_README still carries the
   builds-are-impossible table (search map row flags it as measured false).

## Provenance pointers

- Lane: docs/maintenance/AIF_107_LOW_KEY_ENTRY_SURFACE_LANE_V1.md
- Registry: src/cli/cmd_regression.cpp (kRegressionSpecs) via
  tools/reports/regression_index.py
- Reports: D:\dev\STATE_REFRESH_2026-09-23.md,
  D:\dev\ONBOARDING_EXPERIENCE_REPORT_2026-09-23.md
- Site: deraldg/dottalkpp @ D:\dev\dottalkpp-lean
