# The 20 written-debt command pages were generated

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    Lane   : AIF-068. Ruling: R127.
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : **CANDIDATE ONLY, review-needed. NOT accepted, NOT published.**

---

## 1. Why this document exists at all

**The pages themselves are NOT tracked**, following the precedent set by the
July candidate run (`git ls-files` on `command_page_candidate_v2/` returns
zero) and the OI-011 reasoning for the harvest: an artifact reproducible from
tracked tooling need not enter history.

But that argument only holds if the RECIPE is tracked, and it was not. The
chain runs tracked HELP DBFs -> tracked exporter -> harvest CSVs -> tracked
generator -> **the command line** -> pages. The command line existed only in a
chat transcript, and the manifest that records the selector and the key list is
itself untracked. **This file is the tracked link.** Without it the pages are
reproducible in principle and irreproducible in practice.

## 2. What was run

    tools/manualgen/build_postbaseline_supported_command_pages.py

      --current-topics       harvested/HELP_HELP_TOPIC.csv
      --help-lines           harvested/HELP_HELP_LINE.csv
      --accepted-command-dir published/developer_manual_publication_v1/
                             command_reference_v1/commands
      --output-dir           <this directory>/command_pages_20260825
      --compose-catalog      FOX   --compose-catalog UI   --compose-catalog DEV
      --reference-run        DOCFLUSH-20260812-001/harvest_20260825
      --only-topic-key       DOT|<each of the 20 below>
      --expected-topic-key   DOT|<each of the 20 below>

The `harvested/` root is `docs/manuals/developer/manualgen/harvested/` and the
accepted-command root is under `docs/manuals/developer/manualgen/published/`.
Neither is spelled as a full path here on purpose: `harvested/` is gitignored
and the output directory is untracked, so a path-shaped citation of either
would be reported by the `cited-paths` gate -- correctly.

**THE TWENTY KEYS**, which are an ALLOW-LIST and not a selector result. R127
and `SELECTOR_CHOICE_EXAMINED_V1.md` section 6a record why: "supported topic
with no page" returns 109 on this tree, and nothing in the data distinguishes
these twenty from the other eighty-nine.

    AVERAGE   BOOLEAN   BROWSETUI  BROWSETV   DISPLAY
    ECHO      FIRST     FORMULA    INDEXSEEK  LAST
    LIST_LMDB NEXT      PRIOR      RBROWSE    REFRESH
    REL_LIST  SIMPLEBROWSER SMARTBROWSER SORT WHERECACHE

## 3. What came out

    status              PASS_CANDIDATE_ONLY      findings   NONE
    pages               20                       files      24
    lineage_rows        1531                     included   502
    selector            allowlist
    baseline_topics     ""  (there is no baseline in allow-list mode)
    reference_run       DOCFLUSH-20260812-001/harvest_20260825
    compose_catalogs    FOX, UI, DEV

Input hashes are in the manifest. The current-topics and help-lines CSVs are
the PROMOTED harvest of 2026-08-25, confirmed byte-identical to
`harvest_candidate_20260825/` and different from
`harvested_preexisting_20260825/` -- checked before the run, because measuring
the wrong publication is a mistake this flush has already paid for once.

### Composition under R127 2a

    BROWSETV    3 own +  3 FOX + 41 UI = 47 src, 18 included
    AVERAGE     3 own +  3 FOX         =  6 src,  5 included
    REL_LIST    3 own +  3 FOX         =  6 src,  5 included
    BROWSETUI / DISPLAY / ECHO / INDEXSEEK / LIST_LMDB / REFRESH / FORMULA
                composed with their FOX sibling

`browsetv.md` renders `Catalog/topic: DOT+FOX+UI`, and its summary now carries
all three sources -- vertical record display, the editor/REPLACE delegation,
and the Turbo Vision grid browser. Before R127 that page would have been three
lines.

### Cross-references recorded, per R127 2a

    BOOLEAN   xref EDU|BOOLEAN   (32 lines, ruled out of a developer page)
    FORMULA   xref EDU|FORMULA   (53 lines, same)

These two pages are THIN BY RULING, not by absence of material, and the ledger
says so in its `cross_reference` column. That distinction is the whole reason
the column exists.

## 4. What this is NOT

- **Not accepted.** Every page carries
  `CANDIDATE ONLY: report-only command-reference page; no publication
  authority`, verified across all twenty. Acceptance into
  `command_reference_v1` is a separate act with its own hashes and its own
  authorization.
- **Not published.** Nothing under `published/` was touched.
- **Not tracked.** See section 1.

## 5. Reproducing it

Re-run section 2 against the same harvest. The manifest's input hashes are the
check: if `current_topics_sha256` or `help_lines_sha256` differs, the harvest
moved and the pages are not comparable.

`--dry-run` performs selection, composition and classification and writes
nothing, including no output directory. Use it first. It reports the included
row count per page and predicts `NO_INCLUDED_HELP_ROWS` failures in advance;
for these twenty it predicted none, and none occurred.

## 6. What it cost to get here, recorded because it will happen again

The first generate attempt **crashed after writing 20 pages, a ledger, a
lineage and a review document**, dying on `sha256(None)` while assembling the
manifest -- the baseline path is None in allow-list mode by design. It left 23
files with no manifest: artifacts with no status, no input hashes and no
findings record.

The dry run had passed. It could not have caught this: it returns before the
write path, so it never executed the failing line. **A check that answers
"fine" for a path it never executes is the AIF-118 shape, and it was in the
verification rather than the code.** Fixed in `bb6712b20` by hashing the inputs
BEFORE the first write, so anything that can refuse refuses while the output
directory is still empty. The partial run was quarantined rather than
overwritten -- overwriting would have worked only because the file set happened
to be identical.

## 7. Good neighbour

    What changed:      this record only. The pages are untracked by decision.
    Whose area:        AIF-068 / manualgen, full_stack_documentation.
    Authorization:     member.derald, 2026-08-25 -- he ran the generate command
                       himself after the dry run; this records what he ran.
    How to verify:     section 3 against
                       `command_pages_20260825/postbaseline_supported_command_pages_manifest_v1.json`
                       in the working tree.
    How to undo:       delete the output directory; nothing references it and
                       nothing was accepted. Delete this file.
