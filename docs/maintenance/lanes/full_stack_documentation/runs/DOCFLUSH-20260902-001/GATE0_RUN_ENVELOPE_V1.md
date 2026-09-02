# DOCFLUSH-20260902-001 (v9) -- Gate 0 run envelope

    opened    2026-09-02
    owner     member.derald
    steward   member.ai.claude.cowork
    scope     WEBSITE PUSH ONLY -- Phase 8 publication ascent for the v8 flush.
              No source change, no HELP rebuild, no manual re-acceptance.

## What this run is, and what it is not

v8 (`DOCFLUSH-20260901-002`) closed in the development tree on 2026-09-02. The
manual was accepted, verified on disk, and committed. **The website was not
reconciled**, and the site is the surface that claims to be current.

So v9 is the PUSH half only. The flush is done; this run carries it to the two
reader surfaces and proves what is actually served.

**NOT IN SCOPE, stated so the boundary cannot drift mid-run:** no source
mutation, no `CMDHELP BUILD`, no harvest re-export, no Gate 4 manual acceptance.
If any of those becomes necessary, this run STOPS and a dev-tree phase reopens.
That is the cookbook's rule and it is also the practical one: a push that starts
rebuilding is no longer a push.

## Baseline, measured 2026-09-02 at Gate 0

    ccode HEAD              8eb35ba6b
    site HEAD               85cdb95c5

    accepted manual         164 command pages, 4 appendices
    reader tracked          yes
    link integrity          PASS -- every linked page exists and is tracked
    Gate 4 applied          MANRUN-20260902T164010Z-78127AF4
    command-ref candidate   MANRUN-20260902T163714Z-F403AD2D
    manual candidate        MANRUN-20260902T113417Z-BE63D201  (newest DRY RUN)

    CORRECTED 2026-09-02 before any site edit. This envelope first recorded the
    site's "Manual candidate" field as needing F403AD2D. It does not. That field
    is derived from `manualgen_build_dry_runs` and means the newest DRY RUN;
    F403AD2D is a COMMAND-REFERENCE CANDIDATE and appears nowhere in that
    directory. The site tracks three distinct manual ids -- dry run, command-ref
    candidate, and Gate 4 apply -- and conflating any two of them would have
    published a correct-looking id in the wrong row.

    HELP store (harvest)    462 command rows
                            2368 argument rows
                            666 reachable topics
                            29700 lines
                            212 SYSCMD rows

    site as_of_date         2026-08-26 (documentation-progress-v1.json)
    site freshness contracts 13 (5 of them human ATTESTATIONS)
    matrix Last audited     2026-08-21 (v5) -- NOT advanced by this envelope

## Phase 7 -> 8 entry check: what is proven, INHERITED, or OPEN

The cookbook requires E1-E8 before Phase 8 starts. This run inherits several
rows from v8, and **an inherited PASS is recorded as inherited, never restated
as current** -- a rule this lane wrote after a previous run cited one.

    E1  dev-tree run closed          PROVEN. v8 RUN_CLOSEOUT_V1.md says closed
                                     2026-09-02; committed.

    E2  HELP current + CMDHELPCHK    INHERITED from v8. Valid ONLY because this
                                     run performs no source or HELP mutation. If
                                     anything in this run touches either, E2 must
                                     be re-proven on the host before publication.

    E3  contracts 100%, fallback 0   INHERITED from v8, same condition.
    E4  refcheck_v1 + normcheck_v1   INHERITED from v8, same condition.
    E5  harvest re-exported after    INHERITED from v8, where it was the row that
        the Phase-4 build            failed and was FIXED (the gate was inverted;
                                     four bindings to the Python scaffold removed).

    E6  command-catalog.mdx          OPEN. This is a WEBSITE artifact and is the
        regenerated, fallback 0      one E-row this run must actually re-run,
                                     because the website is what changes here.

    E7  HELP store backup + named    INHERITED from v8. Gate 4 apply
        rollback                     MANRUN-20260902T164010Z-78127AF4 retained its
                                     backup root; no HELP mutation is planned.

    E8  owner authorization per      OPEN, AND DELIBERATELY SO. v8 granted manual
        distinct mutation            acceptance ONLY. Website publication is a
                                     SEPARATE mutation under gate rule 2 and has
                                     not been authorized. Nothing in this run may
                                     treat the v8 grant as covering it.

## The drift this run exists to close

Measured before opening, and recorded in the website matrix on 2026-09-02:

    claim                     site says                 store holds
    HELP argument rows        2,614                     2,368
    reachable topics          670                       666
    HELP lines                29,480                    29,700
    Gate 4 applied            MANRUN-20260728T041930Z   MANRUN-20260902T164010Z
    manual candidate          MANRUN-20260826T012054Z   MANRUN-20260902T163714Z
    as_of_date                2026-08-26                not yet advanced

STILL ACCURATE and not to be touched: 212 SYSCMD rows, 462 legacy command rows.
Re-measured at Gate 0 and unchanged. **A reconciliation that rewrites figures
which did not move is churn, not hardening**, and it also destroys the signal
that the ones which DID move are real.

The -246 on argument rows is the E5 fix landing, not content loss: the
engine-backed exporter resolves memo text the Python scaffold left blank.

## Standing constraints for this run

- The 9-gate ascent (`DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md`) governs
  Phase 8. Gate rule 6 is the one that matters most here: **a green build is not
  live-site proof.** Final verification reads the deployed routes.
- `D:\dev\x64base-site` is the publication repository. GitHub Pages is the
  canonical path. The older IIS copy is not a route.
- The website matrix is the ENTRY gate and the CLOSEOUT gate. It was read and
  updated on 2026-09-02 before this envelope was opened. `Last audited` moves
  only after the owner reviews a rendered site revision -- not here.
- Five of the thirteen freshness contracts are ATTESTATIONS, not measurements
  ("FAQ reviewed <date>", "reconciled through <date>"). **A date typed to satisfy
  a checker is a fabricated attestation.** Those five are owner acts and this run
  will present them for signature rather than filling them in.
- Sandbox limits: no mutating git, no `git diff` in any form. Staging is prepared
  here and committed on the host.

## Gate 0 status

    OPEN. Baseline captured. E1 proven, E2-E5 and E7 inherited under a stated
    no-mutation condition, E6 and E8 open.
