# AIF-107 Low-Key Entry Surface Lane V1

    status        : claimed 2026-08-11 via session_coordinator.py claim-aif
    owner         : member.derald
    steward       : member.ai.claude.cowork
    created_utc   : 2026-08-11T00:00:00Z
    run_id        : COWORK-20260811-001
    lane          : low-key-entry-surface
    supersedes    : nothing
    siblings      : AIF-095 (dottalkpp-site), AIF-092 (publication-surface-recovery)

## SDLC fields

    id                : AIF-107
    title             : Low-key entry surface for x64base
    area              : publication / website
    owning_lifecycle  : PDLC
    sdlc_lane         : publication-surface
    operating_mode    : authoring
    change_class      : new publication surface; no engine source touched
    build_target      : none (static HTML, no build step, no framework)
    product_profile   : n/a
    index_profile     : n/a
    scope_reason      : audience mismatch on the existing entry surface; see 1
    truth_state       : source-evidenced (from `main` + x64base.com, NOT
                        reconciled against `development`)
    proof_state       : not proven -- reconciliation is gate G2 below
    risk_class        : low for runtime (no source, no data, no build);
                        moderate for publication (evidence tiers restated
                        from a lagging branch)
    source_path       : none in D:\code\ccode
    website_path      : dottalkpp.com apex (owner ruling 2026-08-11 superseded
                        the earlier lean.dottalkpp.com plan; deployed and
                        verified same day). x64base.com possible after reorg.
    next_gate         : G2 reconcile status board against `development`
    status            : claimed; deliverable live at dottalkpp.com

---

## 1. Why this lane exists

x64base.com is doing a job it does well: it is the maintainer's tracking,
organizational, and planning surface, and it shows per-section completion
honestly. That is not the problem and is not what this lane changes.

The problem is that the same surface is also the project's front door, and the
two audiences read the identical signals in opposite directions.

To the maintainer, seven named products, a configurable campus, an LMS boundary
proposal, a nine-gate publication process, and eighteen tracked lanes are a map
of the work. To a developer arriving cold, the same page reads as scope far
ahead of delivery, and the reasonable inference is overclaiming -- which is
precisely the opposite of what the evidence-tier discipline is for. The most
rigorous thing about this project is the part a stranger is least likely to
reach.

The vision is not the defect. The single surface serving both audiences is.

**Lane objective:** a low-key entry surface that a DBF-experienced stranger can
read in ninety seconds, from which the working record remains one click away.
x64base.com and `D:\dev\x64base-site` are not modified by this lane.

## 2. Relationship to AIF-095

AIF-095 (`dottalkpp-site`, claimed 2026-08-07) is a claim stub: five lines, no
lane doc, no closeout, no ruling. Investigation: `AIF-095_INVESTIGATION_2026-08-11.md`.

The `deraldg/dottalkpp` repo it names charters the dottalkpp.com **apex** as the
deep manual room: "the focused manual, reference, generated-documentation, and
proof-library surface ... It supports, but does not replace, x64base.com."

This lane is the opposite artifact -- deliberately shallow. It therefore must
NOT take the apex, which would invert AIF-095's charter. It takes
`lean.dottalkpp.com` and leaves the apex to AIF-095.

**Sibling, not supersession.** Both lanes stay open.

## 3. Deliverable (already built, ahead of this lane)

A static site, 17 pages, no build step, no framework, one generator script.

    index.html        one-screen entry: what it is, what it does, where to get it
    status/           the whole point: every area against its evidence tier,
                      filterable, including work not started
    docs/             9 pages: getting started, command families, architecture,
                      formats, indexing, query and relations, scripting,
                      teaching, ecosystem context
    about/            what it is and, explicitly, what it is not
    downloads/  schemas/  contact/  404
    build_lean_site.py    single source of truth; pages are generated
    check_site.py         link, metadata, and retired-vocabulary gate

Editorial rules enforced by `check_site.py`:

- every capability claim carries an evidence tier
- all growth rates live on `/status/` and nowhere else
- unstarted work is listed, not omitted
- no product storefronts; command groupings are chapters, not products
- retired vocabulary stays retired (checked on every build)
- six navigation items; a seventh means removing one

**Doctrine violation, recorded rather than hidden:** the deliverable was built
before this lane was opened, without a prior-art check and without registration.
House rule is "prior art first, then claim-aif, then register before or with the
work." That did not happen. AIF-095 was discovered afterward, by onboarding.
This lane exists partly to close that gap honestly.

## 4. Gates

**G1 -- owner rulings. PASSED 2026-08-11; rulings recorded:**

    R1  RULED: lane adopted as AIF-107 (this document). AIF-095 remains open
        and unmodified as a sibling.
    R2  RULED: dottalkpp.com APEX, not a subdomain. Owner: "priority is the
        lean-site existence and pointing dottalkpp.com to it; ALL OTHER
        reorganization is a separate effort." The apex-charter conflict noted
        in section 2 is accepted by the owner as a staging-period condition.
    R3  RULED by action: the lean site replaced `main` of deraldg/dottalkpp.
        Old skeleton preserved at branch archive/nextjs-skeleton-2026-07 and
        in the local clone D:\dev\dottalkpp-site.
    R4  OPEN: ASCII compliance for rendered HTML (entities vs literal `--`).
        161 non-ASCII characters shipped in the deployed site.
    R5  DEFERRED by owner ruling: all domain reorganization (x64base /
        dottalkpp / derald / dottalk) is explicitly a separate future effort,
        not part of this lane.

**Deployment record (2026-08-11).** Pushed as commit `c0fc326` to
`deraldg/dottalkpp` `main` (forced; prior head `1359278` archived first).
Deploy via GitHub Actions to Pages. Verified live at https://dottalkpp.com:
status board renders with all 32 entries and filters, docs pages carry tier
chips, sitemap and CNAME correct, footer reaches the working archive.
AIF number allocated post-deployment via
`session_coordinator.py claim-aif` -> AIF-107, run COWORK-20260811-001.

**G2 -- reconcile against `development` (blocking before publication).**
Every claim on the status board was derived from `main` and x64base.com. `main`
is a lagging snapshot. Anything proven on `development` since the last promotion
is under-reported; anything demoted there is over-reported. The board is honest
about `main` and may be stale about reality. Requires either repo access or a
maintainer-supplied current state.

**G3 -- sibling-site rules.** `deraldg/dottalkpp` requires downloads to carry
type, source, proof status, and accessibility status. The lean Downloads page
carries proof status only. Add the rest.

**G4 -- license.** The site footer says GPLv3 with the license file pending, and
`/status/` lists it as not started. Honest today, embarrassing in a month. The
`LICENSE` file is prepared and waiting to be committed.

**G5 -- publication.** Deploy, then verify: six nav items, status filters
respond, styled 404 serves, sitemap and robots carry the right host, footer
reaches the working archive, HTTPS enforced once the certificate issues.

## 5. Out of scope

- x64base.com and `D:\dev\x64base-site`: not modified by this lane
- `deraldg/dottalkpp` apex content: belongs to AIF-095
- engine source, HELP tables, metadata, proofs, manuals: untouched
- the runs-registry gap found during investigation: its own lane, see below

## 6. Adjacent finding, deliberately not folded in

`labtalk/registries/ai_runs.yaml` has recorded no run since 2026-08-03
(`AIPR-20260803-003`) and contains no `COWORK-*` run at all, while Tier 0 lists
nine of them and lanes through AIF-101. Two run-id namespaces coexist and
roughly fifteen lanes have no run record. That is AIF-050's own failure mode
recurring.

It is not a website problem and must not ride along on a website lane. Detail in
`AIF-095_INVESTIGATION_2026-08-11.md` section 2.

## Run id namespace

Claims since 2026-08-06 write `COWORK-YYYYMMDD-NNN`. The traceability contract
and `ai_runs.yaml` know only `AIPR-YYYYMMDD-NNN`. Pick one at claim time; this
draft does not assume either.

---

## How to claim (maintainer, host-side)

The lane number must be allocated atomically. Grep is not an allocator, and
`claim-aif` shells out to `git grep`, so it is host-side only. A sandboxed agent
runs no git. From `D:\code\ccode`:

    python labtalk/ai_portal/claim-aif ... low-key-entry-surface

Then replace `AIF-107` throughout this file with the allocated number, set
`run_id`, add the intake row, and commit with named paths only -- never
`git add -A`, never `git add .`.
