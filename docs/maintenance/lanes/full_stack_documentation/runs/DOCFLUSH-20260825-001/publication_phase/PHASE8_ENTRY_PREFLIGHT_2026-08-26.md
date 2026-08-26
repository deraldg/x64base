# Phase 8 entry preflight -- 2026-08-26

Run: `DOCFLUSH-20260825-001`

Session: `CODEX-20260826-012`

State: **FAIL CLOSED AT E2; NO PUBLICATION MUTATION**

## Authorization received

The owner instructed Codex to proceed to Phase 8 if ready. This authorized the
entry check and publication only if every fail-closed prerequisite remained
current. It did not authorize bypassing a failed prerequisite or rebuilding a
shared data authority from an executable bound to concurrent work.

## Exact website candidate

The website source tree was clean on `codex/lean-sites-publish` at
`8522344260b313bf2f3b84eb437cbc605c10f78a`. The remote source branch was
`7eb566c96818c05265b01e43354c605f1c55e42f`, so the candidate contained three
committed revisions. GitHub Pages was built, public, HTTPS-enforced, and sourced
from `gh-pages` before this entry check. No source branch or Pages branch was
pushed.

## Failed entry row

The governed `docpush_preflight.py` returned nonzero:

    E2 / build-store order: FAIL
    current engine executable: 2026-08-26 08:29:59
    canonical HELP store:      2026-08-26 05:09:48
    result: canonical HELP predates the engine executable

The same preflight reported that the executable was bound against a working
tree with 44 tracked modifications. During the check, development HEAD advanced
from the documentation closeout to `892245854`, an AIF-133 workspace/FIELDMGR
commit. Refreshing HELP from the existing executable could therefore absorb a
concurrent lane into the documentation authority and violate the Good Neighbor
boundary.

Other measured rows were healthy: source annotation coverage 100 percent,
website command catalog 239/239 with zero fallback, HELP join clean at 670
reachable topics, generation date coherent, and metacollect newer than its
source. Those PASS rows do not override E2.

## Required re-entry

Before Phase 8 can publish:

1. choose a stable committed engine revision after the concurrent lane settles,
   or explicitly authorize an isolated clean build of the selected revision;
2. separately authorize the guarded canonical HELP rebuild with backup and
   rollback;
3. refresh the post-E2 HELP/META harvest;
4. rerun E2 through E7 and the publication build; and
5. enter source push, Pages deployment, and live verification only after every
   row passes.

## Good Neighbor note

- **WHAT CHANGED:** recorded the failed Phase 8 entry and moved the maintained
  current-run pointer from E8 back to E2.
- **WHOSE AREA:** AIF-068 documentation ascent and AIF-132 Portal projection,
  intersecting AIF-133 workspace/FIELDMGR only as a measured concurrency fact.
- **AUTHORIZATION:** owner instruction to proceed to Phase 8 if ready.
- **VERIFY OR UNDO:** rerun `docpush_preflight.py` with the website catalog; undo
  by reverting the exact documentation-state commit. No website or public
  rollback is required because no publication mutation occurred.

## Matrix-control follow-up

Owner ruling: the failed E2 relationship belongs in the website matrix check.
The machine manifest now requires `fullstack_publication_entry` as a hard gate,
and `website_matrix_check.py` runs that gate through `docpush_preflight.py` before
publication.

The timestamp rule is necessary as a fail-closed fallback with today's
provenance, but "every recompile semantically changes HELP" is not the durable
rule. The efficient target is a content-addressed HELP-producer fingerprint.
Until it exists, the later owner recompile supplies the negative proof: the
complete matrix returns nonzero and publication remains closed. The first live
matrix run also found `include/dottalk/scratch_sidecar.hpp` missing its universal
source-census contract, independently keeping the publication entry red.
