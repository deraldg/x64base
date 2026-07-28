---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260720-BF4
  recorded_at_utc: 2026-07-26T05:25:45Z
  agent:
    provider: not_exposed
    product: not_exposed
    model: not_exposed
    access_mode: human_operated_tool
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 156980512
  authorization:
    requested_by: maintainer
    scope: >
      Envelope reconstructed 2026-07-28 during AI-portal audit backfill
      (AIPR-20260728-002). AI-authored, human-committed (introducing commit
      156980512, 2026-07-26); original session/agent identity was not recorded and is
      marked not_exposed; access_mode human_operated_tool per
      AI_REPORT_AUDIT_CONTRACT_V1.md.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_MANUAL_ASSEMBLY_2026-07-20.md
    kind: session_closeout
---

# Session Closeout — Documentation assembly architecture: website content manifest + manual assembler (2026-07-20)

```yaml
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260720-001
  recorded_at_utc: 2026-07-20T19:34:52Z
  agent:
    provider: not_exposed
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:\code\ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 8ee746dee21c14b02eaf0398034b15634132a33f
  authorization:
    requested_by: maintainer
    scope: >
      Systematize the documentation architecture on the simplex/duplex spine.
      (1) Website content classification manifest (AIF-033, WEBSITE-ASSEMBLY M1).
      (2) A doc/SDLC model brainstorm pinned as AIF-034 (AI-Portal as source+governor,
      the manual as generated-spine + authored-branch, reviewed manual<->website
      duplex, and a diagram-update trigger). (3) The MANUAL-ASSEMBLY lane (AIF-035),
      M1-M5: bill of materials, part contracts, a manifest-driven assembler with 8
      generators, a per-class drift gate, and public exports + an always-latest site
      link + two educational pages. (4) A "historify" development lesson. Engine-tree
      docs/tools are original edits on the existing branch in D:\code\ccode (no branch
      created/switched, no commit, not applied to C:\x64base or GitHub). Website files
      are staged in D:\dev\x64base-site only, held behind the engine push.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_MANUAL_ASSEMBLY_2026-07-20.md
    kind: session_closeout
```

Owning lifecycle: DotTalk++ SDLC · fullstack documentation → manual + website.
SDLC lane: documentation architecture + tooling + proof.
Truth state: source-defined + tool-proven (assembler runs, drift gate proven).
Proof state: assembler build (22/22 parts) + drift gate (PASS→corrupt-FAIL→PASS) + manifest validators.

## One-line summary

Put the manual and the website on one governed spine: a machine-readable content
manifest classifies every website page, and a new manifest-driven **assembler**
builds the developer manual from a declared bill of materials (spine + authored
branch + generated front/back matter), guarded by a **drift gate** and published
to the site under an always-latest permalink — the self-documentation claim made
literal and demonstrable. All dev-only; website staged in `D:\dev`.

## What was done, by lane

### AIF-033 — WEBSITE-ASSEMBLY, M1 (content classification manifest)

All 108 `content/**` website pages classified onto the **direction × class** grid
and locked into `tools/fullstack_docs/website_content_manifest.yaml`
(`dottalk.website.content_manifest.v1`; validated: generated 6, derived 23,
maintained 54, reported 6, static 19 = 108). Maintainer decisions applied
(command-reference→generated, roadmap+current-lanes→reported, product pages→derived,
rest accepted). Human view: `docs/maintenance/WEBSITE_CONTENT_MANIFEST_M1_CLASSIFICATION_V1.md`;
lane: `docs/maintenance/WEBSITE_CONTENT_MANIFEST_AND_ASSEMBLY_LANE_V1.md`.

### AIF-034 — doc/SDLC model pin

A brainstorm was pinned (not built) as intake row AIF-034: the model refined into a
graph with three source-of-record origins — implementation (behaviour/harvest
spine), AI-Portal (process/lane-state; both governor and a source feeding the
website `reported` class), and the manual's authored branch — plus reviewed duplex
manual↔website tributaries for website-originated derived/report content (behaviour
truth never travels that edge). **The pin's trigger:** any change to the doc/SDLC
model must drive a flowchart/diagram-update pass. Ties to AIF-032 (diagrams) and
AIF-033.

### AIF-035 — MANUAL-ASSEMBLY, M1-M5

- **M1 — bill of materials.** `tools/manualgen/manual_assembly_manifest.yaml`
  (`dottalk.manual.assembly_manifest.v1`): 22 parts in reading order, sharing the
  `class`+`direction` vocabulary with the website manifest. Validated: 13 exist, 9
  greenfield (title, provenance, TOC, function reference, error catalog, glossary,
  index, colophon, preface). The greenfield set is the honest gap — nothing
  generated a TOC, index, or glossary before.
- **M2 — part contracts + anchor convention.** Every part carries a stable `MAN-*`
  anchor, a region mode (whole-file / candidate / authored / append / bind) that
  bounds what the assembler may touch, and a generator binding (9 reuse manualgen,
  13 → 8 new assembler modules, specced with I/O contracts in
  `MANUAL_ASSEMBLY_M2_PART_CONTRACTS_V1.md`).
- **M3 — the assembler.** `tools/manualgen/assemble_manual.py` reads the manifest
  and emits the manual in one pass, dispatching on region mode. First build:
  **22/22 parts, 13,782 lines, anchors balanced**; 63 functions harvested from
  `function_catalog.cpp`, 183 command pages bound, 12 diagrams bound from the
  attachment matrix, generated TOC/glossary/index, and a **colophon that records
  how the manual assembled itself**. Writes to `generated/`, never `published/`;
  acceptance stays gated.
- **M4 — drift gate.** `tools/manualgen/check_manual_drift.py` re-assembles from
  current source and compares region by region. Generated/bind drift = **FAIL**
  (blocks the build); derived/maintained/reported = review (non-blocking). Proven
  end to end: clean PASS (22 parts) → a corrupted generated region flips to FAIL and
  names the part → restore returns to PASS. Required uniform anchoring (every part
  bracketed; authored regions carry `gen=authored`, never rewritten).
- **M5 — exports + site.** The assembler’s output was rendered to **MD + PDF + HTML**
  (pandoc/xelatex; the PDF needed 19 stray `\`-escape artifacts dropped from some
  command pages — a rendering-only cleanup). `tools/fullstack_docs/stage_assembled_manual_to_site.py`
  stages all three to the site under **stable "latest" permalinks**
  (`/downloads/current/developer-manual-latest.{md,pdf,html}` + a
  `DEVELOPER_MANUAL_LATEST.json` build manifest) — every rebuild overwrites the same
  files. Two educational pages built and sidebar-wired in the site:
  `content/docs/dev/manual-assembly.mdx` (assembly-process view) and
  `content/docs/dev/developer-manual.mdx` (reader landing). Downloads page carries an
  "always current" section. All site work is in `D:\dev`, held behind the engine push.

### Development lesson (historify)

`docs/maintenance/MANUAL_ASSEMBLY_HISTORIFY_OLD_TO_NEW_V1.md` records the shift from
the old ~20-step "build the pieces and force them together" hand-stitch to the
manifest → assembler → drift gate, with a before/after evidence table and the
generalizable takeaway: when you can name the pieces but still force them together,
declare the whole and generate to it.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Website content manifest (NEW) | `tools/fullstack_docs/website_content_manifest.yaml` | 108 pages classified; direction × class grid |
| Manual assembly manifest (NEW) | `tools/manualgen/manual_assembly_manifest.yaml` | 22-part bill of materials + M2 anchors/region-modes/bindings |
| Assembler (NEW) | `tools/manualgen/assemble_manual.py` | manifest-driven; 8 generators; emits manual + assembly_report |
| Drift gate (NEW) | `tools/manualgen/check_manual_drift.py` | per-class drift; generated/bind = build-fail |
| Site staging (NEW) | `tools/fullstack_docs/stage_assembled_manual_to_site.py` | stable "latest" permalinks + build manifest |
| Assembled outputs (NEW, generated/) | `docs/manuals/developer/manualgen/generated/assembled/developer_manual_assembled_v1.{md}` + `_v1.{pdf,html}` + `assembly_report_v1.json` + `drift_report_v1.json` | candidate build; not `published/` |
| Lane + spec docs (NEW) | `docs/maintenance/{WEBSITE_CONTENT_MANIFEST_AND_ASSEMBLY_LANE_V1,WEBSITE_CONTENT_MANIFEST_M1_CLASSIFICATION_V1,MANUAL_ASSEMBLY_LANE_V1,MANUAL_ASSEMBLY_M2_PART_CONTRACTS_V1,MANUAL_ASSEMBLY_HISTORIFY_OLD_TO_NEW_V1}.md` | lane records + development lesson |
| Intake | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | AIF-033, AIF-034, AIF-035 |

## Changed (website, D:\dev\x64base-site — staged, NOT published)

`content/docs/dev/manual-assembly.mdx` (NEW), `content/docs/dev/developer-manual.mdx`
(NEW), `config/sidebars.ts` (two entries), `app/downloads/page.tsx` ("always
current" section), and `public/downloads/current/developer-manual-latest.{md,pdf,html}`
+ `DEVELOPER_MANUAL_LATEST.json` (staged artifacts).

## Verified (proof performed this session)

- **Website manifest** validated: 108/108 classified, class tallies balanced.
- **Manual manifest** validated twice (M1 then M2): 22 parts, unique ids/orders, 18
  unique anchors, every generated/derived part carries a generator + source.
- **Assembler** runs green: 22/22 parts, anchors balanced 18/18 (23 openers incl. one
  nested region), 63 functions / 183 command pages / 12 diagrams; `assembly_report_v1.json`
  written.
- **Drift gate** proven: clean PASS → inject stale content into the generated
  function-reference region → FAIL (exit 1, names `spine-function-reference`) →
  restore → PASS.
- **Exports**: MD/PDF/HTML built; staged to the site with sha256s recorded in
  `DEVELOPER_MANUAL_LATEST.json`.
- **Site pages** parse; docs route auto-discovers them; sidebar hrefs + internal +
  download links resolve.

## Published

**Not promoted.** Engine-tree docs/tools are original edits on the existing
`homegrown-cnx-20251112-branch` in `D:\code\ccode`; no commit, no `C:\x64base`
staging, no GitHub push. Website files are staged in `D:\dev\x64base-site` only and
are held behind the engine push (the maintainer's standing gate). The assembled
manual is an **assembled-candidate**; the accepted `developer_manual_publication_v1.md`
remains the reviewed baseline.

## Still open — for the next session

- **MANUAL-ASSEMBLY M6** — retire the ~20-step hand-stitch so the assembler becomes
  the real build path (candidate build only; acceptance stays gated).
- **WEBSITE-ASSEMBLY M2-M5** — anchor convention for generated regions, the assembly
  runner, per-class drift gate, retire the sparse pass.
- **AIF-032 (FULLSTACK-DIAGRAMS)** — data-driven diagram generation from the fullstack
  push (still the harvest-SVG staleness gap; the manual’s diagram binder consumes
  the matrix and will consume regenerated assets unchanged).
- **AIF-034** — pinned, not built; a doc/SDLC model change triggers a diagram-update pass.
- **Command-page escape artifacts** — some command pages carry literal `\n`/`<<`
  escape tokens (surfaced by the LaTeX PDF path); worth a source review.
- **Promotion** of this session's engine-tree tooling + the staged website changes
  (maintainer's call, behind the standing push gate).

## Provenance pointers

- Lanes: `docs/maintenance/MANUAL_ASSEMBLY_LANE_V1.md`,
  `docs/maintenance/WEBSITE_CONTENT_MANIFEST_AND_ASSEMBLY_LANE_V1.md`
- Specs/lesson: `docs/maintenance/MANUAL_ASSEMBLY_M2_PART_CONTRACTS_V1.md`,
  `docs/maintenance/MANUAL_ASSEMBLY_HISTORIFY_OLD_TO_NEW_V1.md`
- Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-033, AIF-034, AIF-035)
- Predecessor: `docs/maintenance/SESSION_CLOSEOUT_FIELDTYPE_CODEC_2026-07-19.md` (AIPR-20260719-007)
- Tools: `tools/manualgen/assemble_manual.py`, `tools/manualgen/check_manual_drift.py`,
  `tools/fullstack_docs/stage_assembled_manual_to_site.py`
```
