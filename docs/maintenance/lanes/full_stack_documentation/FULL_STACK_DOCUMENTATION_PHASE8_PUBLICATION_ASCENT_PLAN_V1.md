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

The **developer manual**, the **website**, and the **GPTbase advisor knowledge
bundle** are **consumers**. They read the producer's reviewed evidence and present
it (to humans, or to a hosted advisor). They are not part of the documentation
system; they have their own lifecycles and are documented in their own right, not
here. The GPTbase bundle is now derived like the others -- generator
`tools/fullstack_docs/build_gptbase_bundle.py`, manifest
`docs/ai-friendly/GPTBASE_BUNDLE_MANIFEST_V1.md`, public-safe, run as a website-feed
step -- so all three consumers derive the same `as_of_date` from the registry.

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
| E5 | Manual harvest reflects current HELP | HELP/META harvest re-exported AFTER the Phase-4 build (else the manual omits new commands). SEE "Known gap" below -- no exporter exists yet. |
| E6 | Website catalog source current | `command-catalog.mdx` regenerated, fallback 0 |
| E7 | Backups + rollback ready | HELP store backup exists; promotion rollback path named |
| E8 | Owner authorization for mutation | manual acceptance, source staging, and website publish are distinct mutations; each needs its own owner go |

Status as of 2026-08-05 (DOCFLUSH-20260805-001):

- E1 done -- Gate 7 closeout says CLOSED.
- E2 done -- Gate 4: reflection PASS, 525 topics.
- E3 done -- source_census 100 percent; catalog fallback 0.
- E4 done -- `refcheck_v1.py` PASS (0 guarded phantoms across dotref/foxref/edref/
  pshell_ref/sql_ref/devref); `normcheck_v1.py` PASS (0 findings in the IDENTITY
  and FN_IDENTITY fail-lanes).
- E5 interim-satisfied -- `export_help_meta_harvest.py` produced a current,
  manualgen-accepted candidate harvest (memo TEXT deferred to the native verb).
- E6 done -- `command-catalog.mdx` regenerated, fallback 0.
- E7 pending -- take a fresh HELP-store backup before any Phase 8 mutation.
- E8 pending -- owner authorization per mutation (manual accept, source stage,
  website publish).

Fail-closed: if any row is unproven, Phase 8 stops and the dev-tree lane reopens
the relevant phase. E5 was the deep one -- worse than a stale file -- see below.

### Known gap: E5 has no producer (build it first)

The harvest is the hand-across artifact at the producer/consumer seam, but **no
code produces it.** Confirmed 2026-08-05:

- The 14 required `harvested/*.csv` are a hand-made snapshot dated 2026-05-25;
  HELP DATA is current as of 2026-08-05.
- `HELP_META_EXPORT_MANIFEST_v0.csv` lists every table as `current_status =
  PENDING_EXPORT` with a blank `export_method` -- it is a plan, never executed.
- `tools/manualgen/manualgen_lib/harvest.py` only SELECTS and VALIDATES an existing
  harvest ("Select HELP/META evidence without copying or promoting it"). It does
  not write `harvested/`. Nothing else does either.
- The engine's nearest export, `export_helpdata_v2_dbfs`, emits DBFs, not these CSVs.

Consequence: E5 cannot be satisfied by anyone today. The **first Phase 8 work item
is to build the harvest exporter** -- a defined HELP/META -> `harvested/*.csv`
producer (the 14 files in `harvest.py`), executed from current HELP DATA, that
flips the manifest from `PENDING_EXPORT` to a recorded method. Only then can the
manual be made current. This is a source/tooling task in the dev tree, not a
publication step; it is the true blocker the Phase-6 dry-run masked (it ran green
on the May snapshot).

**Placement (producer/consumer -- do not blur):** the exporter is PRODUCER-side.
It dumps the HELP tables (`data/help/*.dbf`) and META `SYS*` tables
(`data/metadata/SYS*.dbf`) that this documentation system produces. It does NOT
belong on the `MANUAL` command -- `MANUAL` is a read-only CONSUMER of the accepted
manual catalog (`mutates: none`), and adding a writing exporter there would make a
consumer also a producer. Native home: a `CMDHELP` / HELP-META export verb (CMDHELP
already produces HELP DATA and exports helpdata to DBFs via
`export_helpdata_v2_dbfs`; a harvest CSV export sits beside it). A Python
`dbfread`-based dump is interim scaffolding only; the permanent producer is native
C++ per the maintenance-app doctrine.

**Status 2026-08-05:** an interim producer now exists --
`tools/fullstack_docs/export_help_meta_harvest.py` -- and satisfies E5 in effect:
it dumps the 14 HELP/META tables to a candidate harvest, includes this pass's new
commands (BBS/NET/CANARY/CMDREL/FORMULA/EDIT), resolves the manual prose
(`HELP_LINE` has no memo fields), and manualgen selects it 14/14 with only the
`PYTHON_312` self-check failing. Limitation: it uses the v32-era `dbfread`, which
does not follow x64 memo blocks, so the memo columns (`COMMANDS.USAGE/VERBOSE`,
`CMD_ARGS.USAGE/VERBOSE`, `HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE`, `SYSFUNC.NOTES`)
are blanked rather than resolved. The permanent native `CMDHELP` harvest verb must
resolve memo TEXT properly by reusing the x64 open/memo logic already in
`src/cli/cmd_use.cpp` (USE auto-attaches memo storage). Candidate harvest lives at
`runs/DOCFLUSH-20260805-001/manualgen_phase/harvest_candidate_v1/` (gitignored CSVs).

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

1. **Re-harvest** (fixes E5): run the producer-side HELP/META -> `harvested/*.csv`
   exporter -- which must be BUILT first (native CMDHELP/HELP-META side, NOT the
   MANUAL consumer). Then the manual pipeline sees the current command set.
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
| Re-harvest (E5) | INTERIM Python producer now exists (`tools/fullstack_docs/export_help_meta_harvest.py`); current harvest, manualgen-accepted, prose resolved, but x64 memo TEXT blanked (v32 reader) | native `CMDHELP` harvest verb that resolves memo TEXT by reusing the USE/memo-open logic in `cmd_use.cpp`, chained after `CMDHELP BUILD` |
| Manual candidate chain | many manualgen subcommands | one reviewed `manualgen ascend` driver |
| Website feed + integration | packet + manual apply | one `website-ascend` driver over `website_content_manifest.yaml` |
| Live verification | manual HTTP checks | a route-manifest verifier that reads deployed content |

Until automated, these stay in this plan's manual ladder and in the cookbook so no
run re-derives them.

## Phase 9: consumer refinement and owner signoff (reiterative)

Phase 8 builds the consumer content from the producer. Phase 9 is the reiterative
human loop that refines each consumer and captures owner signoff. The manual and
the website are **two separate-but-equal consumer tasks** -- neither is subordinate;
each has its own review/refine/signoff cycle and can be signed off independently.

### Two parallel tracks (separate but equal)

| Track | Refine (at SOURCE, then regenerate) | Owner gate |
| --- | --- | --- |
| Manual | assembled candidate; edits go to harvest/registry/manual source, not the generated manual | owner reviews the reader artifact; signs off a named revision |
| Website | pages by maintenance class; edit `generated`/`derived` at source + regenerate, hand-edit only `static`/`maintained` | owner reviews the rendered site; signs off ("I like it") |

Reiterative: each track loops review -> refine -> owner review -> signoff; it is not
one-shot. A track is done only when the owner signs off, and any later change
reopens it.

### Co-consumers -- the two reference each other at the UI level

The manual and website cite and reuse each other. Reuse is allowed only in the
sanctioned direction, per the website matrix Direction Gates, with proof labels and
provenance. Neither becomes a system of record; both derive from the producer.

```
        producer (engine: contracts, HELP, references, registries)
               |                                     |
               v                                     v
         [ MANUAL ]  <---- talk-about / link ---->  [ WEBSITE ]
               |                                     ^
   manual   -->|  manual -> web: DUPLEX REVIEWED     |  web uses
   sections    |  (proof labels + source anchors)    |  manual parts
   feed web    +-------------------------------------+
   summaries   |  web -> manual: BLOCKED by default;  |
   web-owned   |  EXCEPTION only for website-owned    |
   artifacts   |  artifacts not derivable elsewhere   |
               +-------------------------------------+
```

- **Web uses manual parts:** `manual -> web` is DUPLEX REVIEWED -- reviewed manual
  sections may feed website summaries when proof labels and source anchors are
  preserved (e.g. the command-reference landing page).
- **Web talks about the manual, manual talks about the web:** plain cross-links and
  prose references -- always allowed.
- **Manual consumes web parts?** `web -> manual` is BLOCKED by default. EXCEPTION
  (matrix): curated screenshots, public-only media, branding, hosted-download
  metadata, contact/nav artifacts -- web-owned things not derivable elsewhere,
  carried with provenance. So yes, but only under the exception, and never web
  prose as technical authority.

### Signoff record

Each track produces a signoff: owner, date, the reviewed revision (manual reader
hash / site commit), and any Direction-Gate exceptions used. Signoff is per
consumer -- the manual can be signed off while the website still iterates, and vice
versa. Phase 9 (and the whole flush) is not "done" until both consumers carry a
current owner signoff.

## First-attempt lessons: integration and normalization (2026-08-05)

Recorded as a teaching case, not a fault report. The first time this run touched
the website consumer, the "Updated" date was stale (2026-07-28) on **every page**.
Diagnosing that one wrong date exposed a chain of integration/normalization debt --
which is exactly what pushing the whole stack is meant to surface. We will run
Phase 8 again and improve the integration each time.

What actually went wrong (all the same disease at different levels):

1. **Governance not consulted first.** Site pages were edited before reading
   `content/docs/dev/website-documentation-matrix.mdx` (page maintenance classes)
   and the sitemap/nav (`app/sitemap.ts`, `config/nav.ts`, `config/sidebars.ts`).
   Rule: classify every page -- `static` / `maintained` / `maintained_current` /
   `derived` / `generated` / `reported` -- BEFORE editing.
2. **Hand-edited generated output.** `current-work.mdx` and
   `public/artifacts/current-work-v1.json` were edited directly. Both are
   `generated`/`maintained_current`, produced by `build_current_work_feed.py` from
   the registry. Rule: never hand-edit a generated/derived region; fix the SOURCE
   (registry) and regenerate.
3. **The fact was not normalized.** The same fact -- `as_of_date` -- lived in the
   registry, the generated JSON, the generated mdx, and (as prose) the hero. With
   no single authority derived everywhere, one stale source became a site-wide lie.
4. **The pipeline step was missing.** The flush did not advance the registry
   `as_of_date` on reconciliation, nor run the generator. Both are manual steps
   that were skipped, so July output froze across the site.
5. **Stored, not derived.** HELP counts (topics/lines) are STORED in the registry
   flush block and hand-updated, instead of DERIVED from the HELP store. A number
   that can be measured should never be typed.

Normalization target (what "integrated" looks like):

- One authority per fact. `as_of_date` = the reconciliation date, advanced in the
  registry only at reconciliation. HELP counts measured from the HELP store. Page
  content produced by the generator.
- The full-stack flush MUST, as its website-feed step: advance the registry
  `as_of_date`, reconcile the flush block (ideally from measured HELP), then run
  `build_current_work_feed.py` (current-work) and `command_catalog_sync` (catalog).
  Until that runs, the site is stale by construction.
- Consult the website matrix before ANY site edit; edit source and regenerate;
  hand-edit only `static`/`maintained` pages (home framing, news, brand, licensing).

## Definition of done (Phase 8)

Both reader surfaces are refreshed and PROVEN live: the published developer manual
reflects current HELP (including this pass's new commands), and `x64base.com`
serves the updated routes under cache-bypassed verification. Only then is the
full-stack flush actually full.
