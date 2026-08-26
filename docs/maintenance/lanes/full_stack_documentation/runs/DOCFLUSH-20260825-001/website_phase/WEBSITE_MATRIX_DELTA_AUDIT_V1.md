# Website matrix delta audit V1

Run: `DOCFLUSH-20260825-001`

Audit date: 2026-08-26

State: **LOCAL RECONCILIATION COMPLETE; OWNER WEBSITE SIGNOFF OPEN**

## Scope and rules

This audit reads every row of
`D:\dev\x64base-site\content\docs\dev\website-documentation-matrix.mdx`
and classifies its disposition against the current full-stack producer. Generated
and derived outputs are changed only through their source/generator. Static and
maintained pages change only when the current run supplies relevant reviewed
evidence. `maintained_current` pages replace their present-state region while
retaining sealed event history.

Direction is implementation/runtime/HELP/metadata/SelfDoc/manualgen -> website.
Website prose is not promoted backward into source authority.

## Measured producer state

- source census: 1,082 tracked source files; 1,082 file contracts; 231 files with
  usage contracts; 100 percent coverage;
- HELP: 462 legacy command rows, 2,614 argument rows, 670 reachable topics, and
  29,480 line rows;
- canonical HELP/META harvest: 14/14 tables, 63,217 rows;
- command website projection: 239/239 parsed, zero fallback;
- function website projection: 73 core `FunctionDoc` rows plus 2 self-registering
  extension examples;
- manual candidate: `MANRUN-20260826T012054Z-B9F8B8BD`, accepted review-needed,
  with no publication replacement;
- publication: not entered.

## Matrix-wide disposition

| Website matrix row | Class / handling | Disposition | Result |
| --- | --- | --- | --- |
| Home and top-level positioning | maintained framing + maintained-current project truth | UPDATED | Project-truth present-state measurements reconciled; home framing unchanged. |
| Proven capabilities | maintained | VERIFIED_NO_CHANGE | The current run changed documentation machinery, not feature proof; 2026-08-21 corrections remain current. |
| Schemas: a table of databases | maintained | DEFERRED_CONCURRENT_LANE | Workspace/MINIDB work is concurrent and supplies no new committed publication evidence in this run. |
| Ecosystem feature comparison | maintained | VERIFIED_NO_CHANGE | The 2026-08-21 writeback correction is already present; no new comparison claim supplied. |
| Docs landing cards | maintained navigation | VERIFIED_NO_CHANGE | No route was added or removed by this pass. |
| Engine Specifications | maintained | UPDATED | Replaced ambiguous 243/74 counts with named 245 runtime, 239 website, 212 SYSCMD, and 75-function boundaries. |
| x64base Engine product page | derived hub | VERIFIED_NO_CHANGE | Linked destinations remain valid; no product-framing change required. |
| Workspaces (engine) | maintained | DEFERRED_CONCURRENT_LANE | Claude's active workspace/MINIDB work is outside this documentation mutation. |
| Coined vocabulary | maintained pointer | VERIFIED_NO_CHANGE | Pointer remains non-perishable; vocabulary source is not promoted through this run. |
| DotTalk AI development history | reported | VERIFIED_NO_CHANGE | No new reviewed historical evidence packet. |
| Public database schema catalog | maintained | VERIFIED_NO_CHANGE | No accepted schema-family change supplied by this run. |
| ECO map | generated | DEFERRED_SOURCE_DIRTY | Canonical ECO artifact is independently dirty; regeneration would absorb another lane. |
| LMS proposal | static | NO_CHANGE | Preserved received material. |
| LMS architecture assessment | static | NO_CHANGE | Report baseline intentionally unchanged. |
| x64base Engine docs | derived/reviewed | UPDATED | Specifications, project truth, roadmap, current lanes, and full-stack status reconciled. |
| DotTalk++ docs | generated/reviewed derivative | UPDATED | Function catalog regenerated; command catalog rechecked; command diagram regenerated with provenance. |
| Data mutator safety | derived | VERIFIED_NO_CHANGE | No mutator behavior change entered this run. |
| Workbench / Parallel GUI/TUI | maintained | DEFERRED_CONCURRENT_LANE | Existing 2026-08-20/21 evidence remains; APPGUI work is concurrent and untouched. |
| Laboratory Campus | maintained | VERIFIED_NO_CHANGE | No curriculum or lesson acceptance entered this run. |
| Current tasks and projects | maintained_current/generated | DEFERRED_SOURCE_DIRTY | `ai_portal_tasks.yaml` has unrelated uncommitted work; generating from it would publish an uncommitted authority. |
| LMS communications lane | maintained | VERIFIED_NO_CHANGE | Local-only boundary unchanged. |
| Runtime evidence gallery | reported/curated | VERIFIED_NO_CHANGE | No new approved screenshot or runtime-evidence packet. |
| Important documents shelf | maintained | UPDATED | Developer-manual landing now distinguishes stable links, accepted checkpoint, and the non-replacing v6 candidate. |
| Documentation progress | maintained_current | UPDATED | Human and JSON views now report v6 measurements and retain the sealed 2026-07-18 checkpoint. |
| RAM DBF and VDISK | derived | VERIFIED_NO_CHANGE | No new accepted storage behavior in this run. |
| Identity/authentication/RBAC | derived | VERIFIED_NO_CHANGE | No new accepted identity proof in this run. |
| Pinocchio benchmarks | reported | VERIFIED_NO_CHANGE | Historical ledger remains append-only; no new benchmark run. |
| dottalkpp.com lean entry site | external | OUT_OF_SCOPE_EXTERNAL | Cross-site role retained; no external repository mutation. |
| SelfDoc publication path | maintained process | VERIFIED_NO_CHANGE | Process boundaries remain correct; v6 evidence is recorded in the owning run. |
| Historical source lineage | reported/generated | VERIFIED_NO_CHANGE | Archive and checksums unchanged. |
| Application UI DSL lane | maintained/planned | DEFERRED_CONCURRENT_LANE | Claude's APPGUI work does not by itself prove the planned language surface. |
| Coding standards and safeguards | maintained | VERIFIED_NO_CHANGE | No new public policy ruling. |
| News announcements | maintained | NO_CHANGE | A local reconciliation is not a publishable milestone announcement. |
| News, licensing, brand | static/maintained | NO_CHANGE | No brand, license, or press change. |
| AI views and process diagrams | maintained gateway | VERIFIED_NO_CHANGE | Portal reports remain development-gateway artifacts; no copied public snapshot. |
| AI Portal private reference | maintained/private | DEFERRED_PRIVATE_IGNORED | Content remains intentionally unlisted and locally excluded from site Git. |
| Frontal Memory private reference | maintained/private | VERIFIED_NO_CHANGE | No memory-lane mutation. |
| Site search | maintained/generated build output | REGENERATED_BUILD | Production build regenerates Pagefind; private exclusions remain enforced. |

## Content-manifest hardening

The detailed `website_content_manifest.yaml` claimed to classify every content
page but declared 120 while the site contains 146 MDX pages. The audit registered
all 26 missing pages, moved the website matrix to `maintained_current`, and now
proves 146 declared == 146 actual, with no duplicates, missing files, or phantom
entries. Totals are 8 generated, 30 derived, 75 maintained, 9
maintained-current, 5 reported, and 19 static.

## Publication-freshness amendment -- 2026-08-26

The Phase 8 entry failure exposed a missing relationship in this audit: page
classification and website build success did not themselves assert that the
canonical HELP producer state matched the selected engine state.

The matrix now declares five hard publication gates and routes them through
`tools/fullstack_docs/website_matrix_check.py`. The full-stack entry gate calls
`docpush_preflight.py`, so the current engine/HELP order check, HELP join
integrity, and producer freshness are part of the matrix result.

The present order check is a cheap conservative fallback: because HELP carries
no content-addressed producer fingerprint, a later recompile makes the matrix
red even when the code change is unrelated to HELP. That is operationally cheap
to detect but can trigger an unnecessary rebuild. The intended refinement is a
digest over the catalogs, extracted HELP contracts, and HELP generator
implementation. Until that provenance exists, the owner recompile is retained
as the live negative arm and `fullstack_publication_entry` must return nonzero.
The same live run also caught the newly tracked
`include/dottalk/scratch_sidecar.hpp` outside the universal source census, so
the matrix currently reports both producer freshness and 100-percent source
coverage truth rather than stopping after the first failure.

## Remaining signoff boundary

The matrix's `Last audited` stamp remains 2026-08-21 until the owner reviews the
rendered v6 site revision. This local audit adds a pending-signoff note but does
not self-approve, push, deploy, or claim live readback. The `current-work` feed
must be regenerated after its source registry is committed or otherwise returned
to a clean authority state.

## Good Neighbor

- **WHAT CHANGED:** audited all matrix rows, refreshed unblocked generated and
  maintained-current website surfaces, and reconciled the detailed 146-page
  content manifest.
- **WHOSE AREA:** AIF-068 full-stack documentation and x64base-site publication,
  intersecting AIF-132 Portal feed status and Claude's APPGUI/workspace lanes.
- **AUTHORIZATION:** maintainer instruction `do it` following the matrix-wide
  delta plan; publication and live deployment remain behind owner rendered-site
  signoff.
- **VERIFY OR UNDO:** run the catalog checks, manifest exact-set check, JSON parse,
  and site production build. Revert the exact ccode and site reconciliation
  commits to undo; no public rollback exists because nothing was deployed.
