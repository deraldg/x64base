# Gate corrections required

    measured  2026-09-02, across DOCFLUSH-20260901-002 (v8) and -20260902-001 (v9)
    status    REPORT. Nothing here is fixed. Each item names the defect, the
              measurement, the blast radius, and the recommended change.

Every gate in this chain did its job at least once on 2026-09-02. These are the
places where a gate was RIGHT and UNREADABLE, or where it could not distinguish
two conditions it reports with one answer. They are ordered by how much damage
the defect can do, not by how hard it is to fix.

## G1 -- THE PUBLICATION GATE CANNOT TELL "DID NOT RUN" FROM "FOUND A PROBLEM"

**Severity: high. This is the AIF-118 shape inside the publication gate itself.**

`tools/fullstack_docs/command_catalog_sync.py:main()` returns **exit 2** for
`Python 3.12+ required`. Catalog DRIFT also returns exit 2. `docpush_preflight.py`
reads the exit code, cannot distinguish them, and prints the alarming one:

    2. catalog: Python 3.12+ required
    PREFLIGHT FAIL:
      - command_catalog_sync check: catalog drifted from source     <- FALSE

Measured the same day by calling the entry point with the guard relaxed, then
CONFIRMED EXACTLY on the host under `.venv312`:

    command_catalog  PASS  registry_keys=239 catalog_rows=239 parsed=239 fallback=0
    function_catalog PASS  core=73 self_registered=2 website_rows=75
    error_codes      PASS  source_codes=20 page_rows=20
    locale           PASS  5/5 exact

**The whole gate reported FIVE failures against a site current on every
relationship it tests.** One was real (G2). Four were the guard.

The expensive part is not the wrong message. A gate that cries wolf on four of
five rows teaches its operator to discount it, and this one had a real finding
hiding in the noise.

RECOMMENDED: give "could not run" its own exit code (3), distinct from "found a
problem" (2), and have the preflight report it as UNRUN rather than as a finding.
UNRUN is not PASS and it is not FAIL.

## G2 -- THE VERSION GUARD TESTS THE WRONG THING

**Severity: high. Ten files. Fails in both directions.**

The guard's real subject is INTERPRETER ROUTING, not version. Owner, 2026-09-02:
3.12 is required "only with dottalkpp/xbase ... because of vcpkg version
installed". `CLAUDE.md` already documents the underlying problem -- the vcpkg
python is minimal and has no PyYAML, so a tool that lands on it dies with
`ModuleNotFoundError: yaml`.

Version is a proxy for that, and it is wrong both ways:

    false negative   a capable 3.10 is refused (measured: every check it blocked
                     passed when run)
    false positive   if vcpkg ever ships 3.12 the guard PASSES and the tool dies
                     later on the real problem, the missing dependency

Carrying the guard: `apply_newline_reconciliation.py`,
`audit_help_contract_continuation.py`, `audit_manual_publication_readiness.py`,
`audit_supported_command_publication_coverage.py`, `build_current_work_feed.py`,
`build_historical_source_museum.py`, `build_website_feed_packet.py`,
`command_catalog_sync.py`, `stage_assembled_manual_to_site.py`,
`validate_website_feed_packet.py`.

The preflight ALREADY KNEW. It emits:

    6. NOTE  tools/manualgen/build_postbaseline_supported_command_pages.py
             guard is an EQUALITY: != (3, 12)

so 3.13 would be refused too. The NOTE has been printing and nothing acted on it.

RECOMMENDED: test the CAPABILITY, not the version -- import what the tool needs
and fail naming the interpreter that was used. `build_current_work_feed.py` uses
a different shape again (`require_python_312()` raising `RuntimeError`), so the
fix should also make the guard ONE implementation rather than three.

## G3 -- THE CONTENT MANIFEST VALIDATES AGAINST THE FILESYSTEM, NOT GIT

**Severity: high. It is OI-027 in a second surface, and it bit on 2026-09-02.**

`validate_website_content_manifest.py` compares declared pages against
`content_root.rglob("*.mdx")`. A page that exists on the author's disk and
NOWHERE ELSE classifies cleanly.

Measured: `content/lab/ai-portal-human-guide.mdx` and
`content/lab/website-matrix-inspector.mdx` were added to the manifest during v9,
the gate reported `PASS -- 149 pages classified exactly once`, and both files are
UNTRACKED. The manifest now declares pages git does not have.

This is exactly the defect `check_manual_link_integrity.py` was written to close
for the accepted manual -- where 165 pages were "accepted" for six weeks while
being invisible to git. The manifest validator has no equivalent assertion.

RECOMMENDED: add a tracking assertion, matching
`check_manual_link_integrity.py`'s: every declared page must exist AND be
tracked. Report untracked-but-declared as its own class, because
untracked-and-declared is wrong whichever way it is resolved.

## G4 -- THE MANIFEST CARRIES HAND-KEPT TOTALS BESIDE THE LIST IT COUNTS

**Severity: medium. Guaranteed to drift.**

`website_content_manifest.yaml` line 8:

    totals: {generated: 8, derived: 30, maintained: 78, ..., total: 149}

The validator compares declared totals against measured, so adding three pages
failed the gate a second time until the totals were hand-corrected 75 -> 78 and
146 -> 149.

This is the shape this lane keeps retiring: a hand-kept count beside the list it
counts, the same as `collect_set_subcommands()` and the 64-name literal
`cmdhelp.cpp` used to carry. It is correct today and will be wrong the next time
someone adds a page.

RECOMMENDED: derive the totals, or drop them. A count that must agree with a list
in the same file is a second copy of that list.

## G5 -- HOUSE STYLE JUDGED GENERATED OUTPUT (fixed 2026-09-02, recorded here)

**Severity: was high. FIXED, and kept because the reasoning generalises.**

`check_house_style.py` blocked a commit over three U+26A0 in the GENERATED
command-reference README. The demand was unsatisfiable in its own terms: the only
way to make a rendered page ASCII-clean is to change the generator or its source,
because editing the page is undone by the next regeneration. The practical effect
was a `--no-verify` (OI-026).

The correct reasoning ALREADY EXISTED IN THAT FILE, above `PRUNE`, for the
`--audit` walk: "mostly vendored and generated text that nobody authored and
nobody should edit." It had been written for the REPORTING mode and never applied
to the ENFORCING one.

FIXED: the gate path now excludes generated manualgen output; authored docs are
still checked hard, including authored docs inside a generated tree. Falsification
tested with a canned diff: 3 lines judged without the exclusion, 1 with, and an
authored em-dash still fails.

RECOMMENDED CARRY-FORWARD: **classify the artifact before choosing where to
enforce.** Any new rule should state which bank it applies to.

## G6 -- THE CHECKER COULD NOT PRINT THE CHARACTER IT EXISTS TO COMPLAIN ABOUT

**Severity: was medium. FIXED 2026-09-02.**

`check_house_style.py` printed the offending line raw and died on a Windows
cp1252 console at the first U+26A0. The operator saw a traceback instead of
findings 2 through 9, and the exit code changed from 2 to 3 -- a different failure
class produced by a reporting bug.

FIXED: non-ASCII is escaped as `<U+XXXX>` for display. The finding is unchanged.

RECOMMENDED CARRY-FORWARD: any tool that reports on characters must be able to
print its own findings on the platform it runs on.

## G7 -- A FRESHNESS CONTRACT CANNOT RECORD THAT A BLOCKER WAS RESOLVED

**Severity: low, but it forces a false claim to persist.**

`current-work-freshness-disclosure` requires the page to carry
``Freshness disposition: `{current_vertical.current_work_feed_state}` ``,
interpolated from the authority. That is correct design -- and on 2026-09-02 it
correctly caught the steward changing the disposition on the PAGE without
changing the ARTIFACT.

The residual issue is upstream of the contract: the page had carried
`deferred-dirty-uncommitted-source-authority` for three runs, and the reason
stopped being true when `ai_portal_tasks.yaml` was committed. Nothing prompts a
re-check of whether a stated blocker still holds, so a dead reason can ride
indefinitely behind a passing gate.

RECOMMENDED: when a disposition names a condition (a dirty file, a pending gate),
record the condition in a form something can test, so the disposition can be
challenged rather than merely repeated.

## G8 -- STATUS COHERENCE WARNING NOBODY HAS ACTED ON

**Severity: unknown, and that is the point.**

`docpush_preflight.py` reports, every run:

    4. WARN  status coherence   167 row(s) are STATUS=pending and
                                CONFID=AUTHORITATIVE at once

167 HELP rows claim to be pending and authoritative simultaneously. This is a
THIRD surface carrying the status-vocabulary problem, alongside the 33
contract-versus-manual disagreements (OI-028) and the 24 distinct
`@dottalk.usage` status values.

RECOMMENDED: fold into OI-028 rather than treating it separately. Three surfaces,
one underlying cause: a status field answering several questions at once.

## Summary

    G1  publication gate: unrun reported as drift          HIGH    open
    G2  version guard tests version, not capability        HIGH    open
    G3  content manifest ignores git tracking              HIGH    open
    G4  hand-kept totals beside the list                   MEDIUM  open
    G5  house style judged generated output                HIGH    FIXED
    G6  reporter crashed on its own subject                MEDIUM  FIXED
    G7  disposition cannot record its own resolution       LOW     open
    G8  167 pending-and-authoritative rows                 ?       open, fold into OI-028

**G1, G2 and G3 are the ones that cost time on 2026-09-02.** G1 and G2 sent a
run chasing drift that did not exist. G3 let the steward reintroduce, in a second
surface, the exact defect that had just been found and gated in the first.
