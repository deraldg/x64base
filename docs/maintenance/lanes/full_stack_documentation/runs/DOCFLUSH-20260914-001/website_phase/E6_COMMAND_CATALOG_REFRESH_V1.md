# E6 website command catalog refresh

Run: `DOCFLUSH-20260914-001`

Recorded: 2026-09-14

State: **E6 catalog condition MET; publication not authorized or performed**

## Result

    command_catalog check=PASS registry_keys=241 catalog_rows=241 parsed=241 fallback=0

Website source revision: `a7c7935e7` on branch `codex/lean-sites-publish` in
`D:\dev\x64base-site`. The previous E6 (`DOCFLUSH-20260825-001`) recorded
`27ce68e00`; the site has moved on since, and `a7c7935e7` is the revision this
catalog was generated against.

The local production build passed: diagram, public-content, freshness and
opacity guards, TypeScript, the full static render, and a Pagefind index over
**170 pages / 12,049 words** (August: 164 / 10,227).

No website push, deployment, live-route mutation, or `C:\x64base` mutation was
performed.

## E0 was satisfied BEFORE anything was emitted

`tools/fullstack_docs/website_matrix_check.py` was run first, against the real
site tree, and it is what identified the drift. The August run recorded a
procedural failure for regenerating before consulting the matrix; that error was
not repeated.

The matrix check is five fail-closed relationships, and four passed on the first
run: `function_catalog` 79/79, `error_codes` 20/20, `locales` 5/5, and -- after
this refresh -- `fullstack_publication_entry`, whose nine-step preflight now
reads **PREFLIGHT PASS**.

## The regeneration, accounted for line by line

`emit` to a scratch path, `check` on the candidate, diff against the live page,
and only then a copy. The generator is sanctioned; that is a statement about how
the rows were derived, not a substitute for reading them.

    8 insertions / 6 deletions

    snapshot        `239`/`239` -> `241`/`241`                    1/1
    AREA51          status  supported -> DEVELOPER                1/1
    DBAREA          description gains workspace ownership         1/1
    GPS             description gains workspace ownership         1/1
    WORKSPACE       description changed                           1/1
    WSREPORT        description changed                           1/1
    GROUPCOMMIT     ADDED   data / supported                      1/0
    WORKDESK        ADDED   diagnostics / EXPERIMENTAL            1/0

Nothing unexplained.

### Two changes that are claims, not counts

**AREA51 is DOWNGRADED on a public page**, `supported` -> `developer`. A reader
who relied on that status loses it. The source contract says so, so the page
becomes correct -- but this is a claim being WITHDRAWN, and it is not one of the
two commands the drift check named. It would have shipped silently inside
"regenerated the catalog" had the diff not been read.

**WORKDESK arrives already labelled `experimental`.** A new command reaching the
public catalog with an honest status rather than an optimistic one.

### Four descriptions, one cause

DBAREA, GPS, WORKSPACE and WSREPORT all now distinguish the workspace that OWNS
an area from the session's CURRENT workspace. That is the workspace-ownership
work reaching the public surface. Four moving together is the expected shape;
four moving separately would not have been.

## What E6 did NOT close, and why it is not E6's

    website-matrix-check: FAIL -- content_inventory
      pages missing from manifest: docs/engine/primary-keys, docs/engine/rdbms

The site tree is NOT idle. At the time of this refresh it carried uncommitted
work by another hand:

    M content/docs/engine/primary-keys.mdx
    M public/artifacts/primary-key-policy-v1.json
    M public/artifacts/sqlsel-conformance-v1.json

Those two manifest-missing pages are that work in progress, not neglect.
Adding them to `website_content_manifest.yaml` from this lane would be reaching
into someone else's change. It was deliberately not done. `content_inventory`
will close when that work does.

## A caveat the build result carries

The production build compiled `primary-keys.mdx` and both artifact JSONs in
their current UNCOMMITTED state. The pass therefore means "this tree builds with
the new catalog in it". It does NOT isolate this change. Had it failed, the
first question would have been whose failure it was.

## Carried, unresolved, not blocking E6

- `1b. usage_missing=1 unregistered=1` -- one registered command with no usage
  contract, and one contract for a command that is not registered. Single
  instances, advisory today. GROUPCOMMIT and WORKDESK both carry contracts
  (`cmd_commit.cpp:1324`, `cmd_workdesk.cpp:16`), so neither is the missing one.
- `4. WARN status coherence: 138 rows are STATUS=pending and CONFID=AUTHORITATIVE
  at once`. Pending and authoritative simultaneously, 138 times. A category
  error in the data, not a count problem.
- Three push tools carry no interpreter version guard, and one guard is written
  as an EQUALITY (`!= (3, 12)`) so it fails on 3.13 rather than requiring at
  least 3.12.
- 164 command pages against 464 registered commands in the accepted manual. The
  manualgen gate reports `164/164` -- complete against its own input, silent
  about coverage. E8 must state that out loud rather than let a reader infer
  completeness.

## Good Neighbour note

- **WHAT CHANGED:** regenerated the derived website command catalog from the
  registry and source usage contracts, 239 -> 241 rows, zero fallback.
- **WHOSE AREA:** AIF-068 full-stack documentation and the x64base-site
  generated DotTalk++ catalog. The primary-keys / rdbms pages and both artifact
  JSONs belong to concurrent work and were not touched.
- **AUTHORIZATION:** the maintainer directed the documentation push to continue.
  This covers the local E6 source refresh only -- not push, deployment, or
  publication. E8 remains open.
- **VERIFY OR UNDO:** re-run `website_matrix_check.py`; expect
  `fullstack_publication_entry` PASS and `content_inventory` FAIL on the two
  in-flight pages. To undo, `git -C D:\dev\x64base-site checkout --
  content/docs/dottalk/command-catalog.mdx`. No public rollback is needed
  because nothing was published.
