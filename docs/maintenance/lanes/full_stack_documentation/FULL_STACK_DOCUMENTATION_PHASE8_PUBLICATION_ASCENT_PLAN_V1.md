# Full-stack documentation flush -- Phase 8: publication ascent (data to the UI)

Lane: `full_stack_documentation`
Owner and final authority: `member.derald`
Steward: `member.ai.claude.cowork`
Recorded: 2026-08-05
Status: **plan; Phase 8 not started (gated behind the Gate 7 -> 8 entry check below)**

## Why Phase 8 exists

The development-tree flush (Phases 0.5 -> 7) makes the *source of truth* current:
HELP DATA, reference headers, source contracts, and the website catalog source.
But a reader cannot see any of that until the **published manual** and the
**deployed website** are refreshed. A flush that stops at Gate 7 is a half push.
Phase 8 is the arc that carries the reviewed evidence all the way to the two
reader-facing surfaces and proves they are live.

## Producer vs consumer -- the diff (read this first)

The documentation flush maintains a **producer**: the source-of-truth pipeline --
source `@dottalk` contracts, HELP DATA, the reference headers (dotref/foxref/
edref), and the command-catalog source. Phases 0.5 -> 7 make that producer current
and prove it.

The **developer manual** and the **website** are **consumers**. They read the
producer's reviewed evidence and present it to humans. They are not part of the
documentation system; they have their own lifecycles (manual assembly lane; website
publication/ascent lane) and are documented in their own right, not here.

The diff matters for three reasons:

1. **Authority direction is one-way.** Producer -> consumer only. Manual prose and
   website prose never flow back as technical authority (ascent doctrine rule 3).
2. **The seam is a hand-across, not ownership.** Phase 8 is where consumers *pull*
   from a proven producer. This plan owns the **entry gate** and the **seam**; the
   consumers' internal steps (manual acceptance, website integration) belong to
   their own lanes and are referenced, not copied.
3. **"Full flush" is the producer being current AND both consumers refreshed from
   it.** A green producer is not a delivered document until the consumers re-pull
   and go live.

So Phase 8 in this lane = the Gate 7 -> 8 entry check + the pull seam. The manual
assembly lane and the website ascent lane do the consumer-internal work.

## Prior art -- build on, do not duplicate

This plan re-instantiates an existing, proven vertical. Do NOT invent a new one.

- `DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md` -- the canonical **9-gate** ascent
  from candidate to verified `https://x64base.com/`. Ran to completion for
  `DOCFLUSH-20260716-001` (all 9 PASS, live via GitHub Pages). This is the spine
  of Phase 8.
- Manual assembly: `MANUAL_ASSEMBLY_LANE_V1.md`, `MANUALGEN_*` contracts, and the
  manualgen accept pipeline (`build-selective-merge-candidate` ->
  `build-controlled-acceptance-plan` -> `apply-controlled-acceptance` ->
  command-reference + review-book + Gate 4).
- Website: `tools/fullstack_docs/build_website_feed_packet.py`,
  `validate_website_feed_packet.py`, `validate_website_integration_plan.py`,
  `website_content_manifest.yaml`, `tools/reports/stage_public.py`, and the site
  repo `D:\dev\x64base-site` (Next.js -> GitHub Pages).
- Historical run evidence: `runs/DOCFLUSH-20260716-001/gate6_website_feed ..
  gate9_live_verification`.

## Gate 7 -> Phase 8 entry check (NEW -- required)

Phase 8 MUST NOT start until every row is true for the current run. This is the
readiness gate the owner asked for: publication cannot begin on an unready dev
tree.

| # | Entry condition | How to prove |
| ---: | --- | --- |
| E1 | Dev-tree run closed at Gate 7 | `GATE7_REVIEW_AND_RUN_CLOSEOUT_V1.md` exists and says CLOSED |
| E2 | HELP DATA current + reflection PASS | Gate 4 record; `CMDHELPCHK` structural PASS |
| E3 | Source contracts complete | `source_census` 100 percent; `command_catalog_sync check` fallback 0 |
| E4 | Reference guards clean | `refcheck_v1.py` PASS; `normcheck_v1.py` PASS |
| E5 | Manual harvest reflects current HELP | HELP/META harvest re-exported AFTER the Phase-4 build (else the manual will omit new commands) |
| E6 | Website catalog source current | `command-catalog.mdx` regenerated, fallback 0 |
| E7 | Backups + rollback ready | HELP store backup exists; promotion rollback path named |
| E8 | Owner authorization for mutation | manual acceptance, source staging, and website publish are distinct mutations; each needs its own owner go |

Fail-closed: if any row is unproven, Phase 8 stops and the dev-tree lane reopens
the relevant phase. E5 is the one this run currently fails (harvest predates the
Phase-4 rebuild); it is the first thing Phase 8 fixes.

## Data flow to the UI

```text
SOURCE OF TRUTH (dev tree, D:\code\ccode)
  include/*ref.hpp + src @dottalk contracts + shell registry
        |
        v
  CMDHELP BUILD  ->  HELP DATA (dottalkpp\data\help)  --------------------+
        |                                                                 |
        |  HELP/META harvest export (re-harvest, entry check E5)          |
        v                                                                 |
  docs\manuals\...\harvested (HELP_*.csv, META_*.csv)                     |
  ============ PRODUCER (documentation system) ends here ============     |
  ============ CONSUMERS (manual, website) pull below =============       |
        |                                                                 |
        v   [CONSUMER: manual assembly lane]                              |
        v   manualgen candidate -> curation -> disposition ->             |
        |   structural reconciliation -> section deltas -> prose ->       |
        |   selective merge -> CONTROLLED ACCEPTANCE (mutation)           |
        v                                                                 |
  ACCEPTED developer manual (reader artifact + publication manifest)      |
        |                                                                 |
        |  Gate 5 source-staging promotion                                |
        v                                                                 |
  C:\x64base  ->  github.com/deraldg/x64base  (reviewed source + manual)  |
        |                                                                 |
        |  [CONSUMER: website ascent lane]
        |  Gate 6 website feed/export packet  <---------------------------+
        v         (reviewed manual summaries + command catalog + anchors)
  D:\dev\x64base-site  (content\...  + generated public blob)
        |
        |  Gate 7 integration + local Next.js build (static pages)
        v
  Gate 8 website publication -> commit/push -> GitHub Pages deploy
        |
        v
  Gate 9 live verification (cache-bypassed HTTP; routes/content 200 + exact)
        |
        v
  READER SURFACES:  (1) published developer manual   (2) https://x64base.com/
```

Rule (from the ascent doctrine): the website consumes reviewed source/manual
evidence; website prose never flows backward as technical authority. A green
build is not live proof -- Gate 9 reads what is actually served.

## The Phase 8 gate ladder (reused 9-gate ascent)

### Manual sub-arc -- gates 1-4 (human-assisted until automated)

The owner assists here. RECORD every required step so it is not forgotten before
it is automated. Each `apply-*` is a MUTATION and needs its own owner go.

1. **Re-harvest** HELP/META from current HELP DATA (fixes entry check E5).
2. `manualgen build-reference-candidate` -> `build-curation-candidate` ->
   `build-disposition-candidate` -> `build-structural-reconciliation` ->
   `build-section-delta-candidates` -> `build-prose-review-batch` ->
   `build-selective-merge-candidate` (candidate chain; report/candidate only).
3. **Gate 2** `build-controlled-acceptance-plan --candidate-run <MANRUN>
   --pointer-audit <json> --context-decision <md>` (plan only).
4. **Gate 3** `apply-controlled-acceptance --plan-run <MANRUN>
   --authorization-record <json>` (MUTATION: accepts manual sections/appendix/
   reader/manifests).
5. **Gate 4** `build-command-reference-candidate` + `build-command-reference-review-book`,
   then the Gate 4 plan/apply for status/marker rows.
6. Manual publication-readiness proof (links, TOC, headers, provenance,
   accessibility): `audit_manual_publication_readiness.py`,
   `audit_manual_documentation_pointers.py`.

Automation status: MANUAL. Target: wrap steps 1-6 behind a single reviewed
`manualgen ascend --manual developer` driver (see automation ledger).

### Source staging -- gate 5 (owner-authorized promotion)

Promote reviewed files only: `D:\code\ccode -> C:\x64base -> github` with staged
validation and a supporting commit. `tools/reports/stage_public.py` governs the
public blob. Distinct mutation; distinct owner go.

### Website sub-arc -- gates 6-9 (steward-drivable; deploy is host/network)

6. **Website feed/export packet**: `build_website_feed_packet.py` +
   `validate_website_feed_packet.py` (reviewed manual summaries, catalog, source
   anchors, route targets). Steward can run.
7. **Integration + local build**: apply the packet into `D:\dev\x64base-site`,
   `validate_website_integration_plan.py`, then the Next.js build (static pages).
   Steward can run the packet + local build in the site repo.
8. **Publication**: site commit/push + GitHub Pages deploy. Host/network + owner.
9. **Live verification**: cache-bypassed HTTP over the deployed routes; record the
   content actually served. Host/network.

## Automation ledger (what to automate next, so this stops being manual)

| Step | Today | Automate to |
| --- | --- | --- |
| Re-harvest (E5) | manual host build | a `harvest` target chained after `CMDHELP BUILD` |
| Manual candidate chain | many manualgen subcommands | one reviewed `manualgen ascend` driver |
| Website feed + integration | packet + manual apply | one `website-ascend` driver over `website_content_manifest.yaml` |
| Live verification | manual HTTP checks | a route-manifest verifier that reads deployed content |

Until automated, these stay in this plan's manual ladder and in the cookbook so no
run re-derives them.

## Definition of done (Phase 8)

Both reader surfaces are refreshed and PROVEN live: the published developer manual
reflects current HELP (including this pass's new commands), and `x64base.com`
serves the updated routes under cache-bypassed verification. Only then is the
full-stack flush actually full.
