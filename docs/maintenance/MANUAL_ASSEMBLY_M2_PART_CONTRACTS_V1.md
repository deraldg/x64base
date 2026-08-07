# MANUAL-ASSEMBLY M2 -- part contracts, anchor convention & greenfield generators

Status: **M2 done** (2026-07-20, dev). Companion to
`MANUAL_ASSEMBLY_LANE_V1.md` and `tools/manualgen/manual_assembly_manifest.yaml`
(schema `dottalk.manual.assembly_manifest.v1`, AIF-035).

M1 declared *what* the manual is made of. M2 makes each part **buildable**: a
stable anchor, a region mode that bounds what the assembler may touch, a binding
to a real generator, and -- for the 9 greenfield parts -- an input->output contract
precise enough to implement in M3.

## Region modes (how the assembler may touch a part)

| Mode | Assembler behaviour | Used by |
| --- | --- | --- |
| `whole-file` | Owns the entire file; regenerated every push; **hand-edits forbidden**. | generated standalone parts: title, TOC, function ref, error catalog, index |
| `candidate` | Regenerates a **review candidate**; the published file changes only on human acceptance (manualgen's existing gate). | derived parts that track source: the article chapters, SET family, appendices, glossary |
| `authored` | **Never writes.** Hand-authored; review-gate only when the tracked subject changes. | maintained parts: preface + 3 process chapters |
| `append` | Appends a provenance/evidence snapshot; **never overwrites** prior snapshots. | reported parts: provenance page, runtime-evidence, colophon |
| `bind` | Binds a **set** of externally-generated files into the reader by inclusion. | command reference (183 pages), diagram set |

## Anchor convention

Every non-authored region is delimited so both the assembler and the M4 drift
gate can find exactly what they own:

```text
<!-- MAN:BEGIN id=fm-toc gen=assembler:toc src=assembled-headings -->
...owned content...
<!-- MAN:END id=fm-toc -->
```

`append` regions use `MAN:APPEND id=... at=<iso8601>` ... `MAN:END`; `bind` regions
carry an inner `MAN:BIND id=... set=<set_path> count=<n>` metadata line. Nested
regions are allowed: the
messages-errors chapter (`candidate`) embeds the generated error catalog
(`spine-error-catalog`) inside a nested `MAN:BEGIN id=spine-error-catalog` region,
so the surrounding prose stays a review candidate while the table inside is
`whole-file`-owned.

**M4 refinement (2026-07-20):** for uniform drift-tooling, **every part is now
bracketed** with `MAN:BEGIN/END`, including `bind` and `authored` parts. An
`authored` region carries `gen=authored` to signal the assembler brackets it but
**never rewrites its content** (review-only). This supersedes the earlier
"authored parts carry no anchor" note -- the bracket is a tooling delimiter, not a
claim of ownership; it lets the M4 gate slice all 22 regions by id.

## Binding table (all 22 parts)

`exists:true` = a real manualgen command today; `exists:false` = a generator M3
builds. Authored parts have no generator.

| Part | Anchor | Mode | Generator | Exists |
| --- | --- | --- | --- | :---: |
| fm-title | MAN-FM-TITLE | whole-file | assembler:frontmatter | no |
| fm-provenance | MAN-FM-PROVENANCE | append | assembler:frontmatter | no |
| fm-preface | -- | authored | -- | -- |
| fm-toc | MAN-FM-TOC | whole-file | assembler:toc | no |
| spine-command-reference | MAN-SPINE-CMDREF | bind | manualgen build-command-reference-candidate | yes |
| spine-function-reference | MAN-SPINE-FNREF | whole-file | assembler:function-reference | no |
| spine-set-family | MAN-SPINE-SETFAM | candidate | manualgen build-dry-run (section) | yes |
| spine-error-catalog | MAN-SPINE-ERRCAT | whole-file | assembler:message-catalog | no |
| art-tables-records | MAN-ART-TABLES | candidate | manualgen build-dry-run (section) | yes |
| art-command-surface | MAN-ART-CMDSURFACE | candidate | manualgen build-dry-run (section) | yes |
| art-expressions | MAN-ART-EXPR | candidate | manualgen build-dry-run (section) | yes |
| art-indexing | MAN-ART-INDEXING | candidate | manualgen build-dry-run (section) | yes |
| art-messages-errors | MAN-ART-MSGERR | candidate | manualgen build-dry-run (section) | yes |
| art-help-meta-alignment | -- | authored | -- | -- |
| art-cmdref-assembly-hygiene | -- | authored | -- | -- |
| art-promoted-draft-review | -- | authored | -- | -- |
| art-runtime-evidence | MAN-ART-EVIDENCE | append | manualgen build-dry-run (section) | yes |
| diagrams-from-matrix | MAN-DIAGRAMS | bind | assembler:diagrams | no |
| bm-appendices | MAN-BM-APPENDICES | candidate | manualgen build-dry-run (section) | yes |
| bm-glossary | MAN-BM-GLOSSARY | candidate | assembler:glossary | no |
| bm-index | MAN-BM-INDEX | whole-file | assembler:index | no |
| bm-colophon | MAN-BM-COLOPHON | append | assembler:colophon | no |

## Greenfield generator contracts (built in M3)

Eight new assembler modules. Each is a pure function of its declared inputs
except where a human review gate is called out (`candidate` mode).

### assembler:frontmatter -> fm-title (whole-file), fm-provenance (append)
- **Inputs:** `accepted_artifacts/primary_reader_artifact_v1.json` (lines,
  headings, command-reference page counts, snapshot commit);
  `PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json` (maintainer-attested machine).
- **Transform:** render a title page (title, version, public-source commit,
  attested machine line, build date) and a provenance block (proof labels, the
  nine-gate ledger, the exact source snapshot the manual describes).
- **Output:** `MAN-FM-TITLE` whole-file; `MAN-FM-PROVENANCE` append snapshot.
- **Proof:** generated-reviewed / manual-reviewed. Deterministic given inputs.

### assembler:toc -> fm-toc (whole-file)
- **Inputs:** the **assembled** heading tree of every body/spine/appendix part
  (i.e. runs *after* those parts exist).
- **Transform:** collect H1-H3 headings in manifest order, with anchors; emit an
  ordered, linked table of contents.
- **Output:** `MAN-FM-TOC` whole-file.
- **Ordering:** must run in the **final** pass (depends on assembled headings).
  Deterministic given the assembled manual.

### assembler:function-reference -> spine-function-reference (whole-file)
- **Inputs:** `src/cli/expr/function_catalog.cpp` (`FunctionDoc` table) +
  self-registered functions from `src/ext/fn` -- the same source the website
  function catalog reads (`command_catalog_sync.py` function pass).
- **Transform:** one entry per function -- name, signature, arguments, summary,
  proof/status.
- **Output:** `MAN-SPINE-FNREF` whole-file. Deterministic.

### assembler:message-catalog -> spine-error-catalog (whole-file)
- **Inputs:** HRESULT catalog + message catalog + locale spine (the harvest
  behind the website messaging-and-localization page).
- **Transform:** table of {code, symbol, message text, locale coverage}.
- **Output:** `MAN-SPINE-ERRCAT` whole-file, also embedded (nested region) inside
  `art-messages-errors`. Deterministic.

### assembler:diagrams -> diagrams-from-matrix (bind)
- **Inputs:** `reports/diagram-publication-attachment-matrix-v1.csv` (12 promoted
  rows; columns: diagram_id, owner_lane, source_asset_path, source_kind,
  manual_targets, website_targets, site_asset_path, proof_level, review_status,
  notes).
- **Transform:** for each `review_status=promoted` row, resolve
  `source_asset_path` and bind it at each `manual_targets` location, carrying
  `proof_level`.
- **Output:** `MAN-DIAGRAMS` bind set. **Ties to AIF-032** -- when diagrams become
  data-generated from the fullstack push, this binder consumes the regenerated
  assets unchanged. Deterministic given the matrix.

### assembler:glossary -> bm-glossary (candidate)
- **Inputs:** candidate term harvest from HELP/metadata + article headings.
- **Transform:** collect candidate terms, propose definitions, sort; emit a
  **review candidate** (definitions are human-reviewed -> `candidate` mode, not
  auto-published). Distinct from `commands/glossary.md` (the GLOSSARY *command*).
- **Output:** `MAN-BM-GLOSSARY` candidate. Terms deterministic; definitions gated.

### assembler:index -> bm-index (whole-file)
- **Inputs:** assembled headings + command/function names + anchor ids.
- **Transform:** build an alphabetized term->location index (chapter/anchor) with
  cross-references.
- **Output:** `MAN-BM-INDEX` whole-file.
- **Ordering:** final pass (depends on the fully assembled manual). Deterministic.

### assembler:colophon -> bm-colophon (append)
- **Inputs:** assembler version, source commit, tool versions (Python 3.12,
  manualgen version), machine profile, build timestamp.
- **Transform:** render a build-provenance colophon -- *how the manual assembled
  itself*.
- **Output:** `MAN-BM-COLOPHON` append. This is the part that literally closes
  the self-doc loop. Deterministic given the build environment.

## Assembly ordering (what M3 must respect)

1. **Source parts first** -- command reference (bind), function reference, error
   catalog, the derived article candidates, appendices.
2. **Diagrams** bound to their target chapters.
3. **Provenance/colophon/evidence** append from build + report metadata.
4. **TOC and Index last** -- both read the fully assembled heading tree; they are
   the only parts with a hard "run-after-everything" dependency.

## What M3 consumes from M2

M3's assembler is a loop over `parts` in `order`: dispatch on `region_mode`
(`whole-file`->generate+own, `candidate`->build-candidate+gate, `authored`->skip,
`append`->append-snapshot, `bind`->bind-set), invoking `binding.generator`. The 9
existing bindings reuse manualgen as-is; the 8 new modules above are the M3 build
list. Acceptance stays gated -- the assembler produces candidates and owns only
`whole-file`/`append` regions.
