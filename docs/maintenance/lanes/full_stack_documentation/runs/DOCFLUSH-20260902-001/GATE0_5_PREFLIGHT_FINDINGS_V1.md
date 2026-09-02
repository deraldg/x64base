# DOCFLUSH-20260902-001 (v9) -- preflight findings

    measured  2026-09-02, sandbox (Python 3.10.12)
    tool      tools/fullstack_docs/website_matrix_check.py --root . --site-root <site>

## 1. THE PUBLICATION GATE REPORTS "CATALOG DRIFTED" WHEN THE TRUTH IS "TOOL DID NOT RUN"

The hard publication gate failed with five red rows. FOUR OF THE FIVE ARE A
VERSION GUARD, NOT A FINDING:

    == docpush preflight ==
      2. catalog: Python 3.12+ required
    PREFLIGHT FAIL:
      - command_catalog_sync check: catalog drifted from source     <- FALSE
    == website matrix: function_catalog ==   Python 3.12+ required
    == website matrix: error_codes ==        Python 3.12+ required
    == website matrix: locales ==            Python 3.12+ required

`command_catalog_sync.main()` returns **exit 2** for "Python 3.12+ required".
Catalog DRIFT also returns exit 2. The caller reads the code, cannot tell the two
apart, and prints the alarming one. **This is the AIF-118 shape in the
publication gate itself: a check that returns the same answer for "I could not
run" and "I found a problem."**

MEASURED, by setting `MIN_PYTHON=(3,10)` and calling the same entry points.
**ALL FOUR GUARD-BLOCKED CHECKS PASS:**

    command_catalog  check=PASS registry_keys=239 catalog_rows=239 parsed=239 fallback=0
    function_catalog check=PASS core=73 self_registered=2 website_rows=75
    error_codes      check=PASS source_codes=20 page_rows=20
    locale           check=PASS source_locales=[de,en-US,es,fr,it]
                                page_locales=[de,en-US,es,fr,it]

So the publication gate reported FIVE failures against a site that is current on
EVERY SUBSTANTIVE RELATIONSHIP IT TESTS. One failure was real (the content
inventory, below). The other four were the guard, and the underlying artifacts
were clean the whole time.

That is the expensive form of this bug. A gate that cries wolf on four of five
rows teaches its operator to discount it, and this one had a real finding hiding
among the noise. The catalog is CLEAN. E6 is proven, not open. A run that trusted the gate's own
wording would have regenerated a correct artifact to fix a defect that did not
exist -- and, worse, would have believed the site was drifting when it was not.

WHY THE GUARD EXISTS, and why the version test is the wrong test. Owner,
2026-09-02: 3.12 is required "only with dottalkpp/xbase ... because of vcpkg
version installed". The guard's real subject is the HOST INTERPRETER ROUTING
problem `CLAUDE.md` already documents -- the vcpkg python is minimal and has no
PyYAML, so a tool that lands on it dies with `ModuleNotFoundError: yaml`. The
guard is trying to say "not that interpreter" and is saying "not that version".

Version is a PROXY, and it fails in both directions:

    false negative   a perfectly capable 3.10 (this sandbox) is refused, and the
                     refusal is reported as catalog drift
    false positive   if vcpkg ever ships 3.12, the guard PASSES and the tool then
                     dies later on the real problem, the missing dependency

**The fix is to test the capability, not the version** -- import what the tool
actually needs and fail with a message naming the interpreter. That is a small
change with a large blast radius (ten files carry this guard), so it is recorded
here and filed rather than made mid-push.

Files carrying the guard: `apply_newline_reconciliation.py`,
`audit_help_contract_continuation.py`, `audit_manual_publication_readiness.py`,
`audit_supported_command_publication_coverage.py`, `build_current_work_feed.py`,
`build_historical_source_museum.py`, `build_website_feed_packet.py`,
`command_catalog_sync.py`, `stage_assembled_manual_to_site.py`,
`validate_website_feed_packet.py`.

The preflight ALSO reports one of these guards is an EQUALITY test --
`build_postbaseline_supported_command_pages.py` uses `!= (3, 12)`, so 3.13 would
be refused too. The preflight already knew the guards were suspect and said so in
a NOTE; nothing acted on it.

## 2. CONTENT INVENTORY -- THREE ROUTES WERE NEVER CLASSIFIED. FIXED.

    website-content-manifest: FAIL
      - pages missing from manifest: docs/labtalk/ai-portal-schemas,
        lab/ai-portal-human-guide, lab/website-matrix-inspector

The matrix's first stated relationship is "every MDX route is classified exactly
once", and three were not. `docs/labtalk/ai-portal-schemas` is DESCRIBED in the
matrix prose (the AI Portal row names it) while being absent from the manifest
the gate reads -- described is not classified.

Added to `maintained`, matching the class the matrix already assigns their
neighbours (`docs/labtalk/ai-portal` is maintained; `/lab/*` is maintained,
local-only).

    website-content-manifest: PASS -- 149 pages classified exactly once

A SECOND, SMALLER FINDING FELL OUT OF THE FIX. The manifest carries hand-kept
totals beside the lists (`totals: {maintained: 75, ..., total: 146}`) and the
validator compares declared against measured, so adding three pages failed the
gate again until the totals were hand-corrected to 78 / 149. That is a hand-kept
count beside the list it counts -- the same shape as the retired
`collect_set_subcommands()` and the 64-name literal in `cmdhelp.cpp`. It is
CORRECT today and will drift the next time someone adds a page. Worth deriving.

## 3. GENUINE ADVISORIES CARRIED FORWARD, NOT FIXED HERE

    1b. command contracts: usage_missing=1 unregistered=1 helpers=10 (advisory debt)
    4.  skip  binding                could not read worktree state
    4.  WARN  status coherence       167 rows are STATUS=pending and
                                     CONFID=AUTHORITATIVE at once

The status-coherence warning is worth connecting to OI-028: 167 HELP rows claim
`pending` status and `AUTHORITATIVE` confidence simultaneously. That is a third
place where a status vocabulary is carrying two answers at once, alongside the 33
contract-vs-manual disagreements and the 24 distinct `@dottalk.usage` status
values. Three independent surfaces, one underlying problem.

The `binding` skip is a sandbox limitation (worktree state needs git operations
this environment must not perform), not a finding.

## Gate status after these fixes

    content_inventory              PASS  (was FAIL, three unclassified routes)
    fullstack_publication_entry    BLOCKED BY THE GUARD, not by drift; the one
                                   substantive row (catalog) measured CLEAN
    function_catalog               UNRUN -- guard
    error_codes                    UNRUN -- guard
    locales                        UNRUN -- guard

**UNRUN is recorded as UNRUN.** None of the three guard-blocked gates is claimed
as passing, and the catalog result is reported as measured-by-bypass rather than
as the gate having passed.
