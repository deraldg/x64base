# DDICT, AI Portal and full-stack documentation integration review

Implementation follow-up: [October 9 integration closeout](DDICT_INTEGRATION_2026-10-09/CLOSEOUT.md).
The findings below preserve the pre-implementation examination; the closeout
records corrections, new consumers and remaining live-data review findings.

Date: 2026-10-09 (America/Los_Angeles). Owner: member.derald.
Scope: report-only examination within D:/code/ccode using bounded file and
subdirectory reads. No catalog, GUI, manual, website or publication mutation.
This report is the sole new artifact of this review.

## Findings in brief

There is a native DDICT command and a Workbench DDict GUI. The shared native
reader now supports both legacy and long-name catalogs. The Portal can direct
an agent to DDICT documentation, but the inspected feed/recall registries do
not define a DDICT data feed. Full-stack manual generation consumes HELP and
SYS* metadata; it does not yet consume the dictionary's object/attribute/edge/
evidence graph. Source-manual links alone do not close that integration gap.

## 1. Existing examination and reporting surfaces

| Surface | What it provides | Current boundary |
| --- | --- | --- |
| `DDICT STATUS`, `TABLES` | Active path, table families, rows, schema/memo review diagnostics | Read-only; neither counts nor presence certify freshness |
| `DDICT OBJECTS [TYPE ...] [PROFILE ...] [FAMILY LEGACY\|X64]` | Filtered catalog objects and qualified identities | Bounded to 80 displayed rows |
| `DDICT FIELDS <table-or-alias>` | Recognized physical catalog schema plus curated field objects | Physical schema and descriptive catalog rows are different evidence |
| `DDICT TAGS <table-or-alias>` | Curated tags and CDX/LMDB artifact presence | Not an index-integrity or known-key lookup test |
| `DDICT REL <object> [IN\|OUT\|BOTH]` | Typed relationships | Bounded to 40 per direction |
| `DDICT EVIDENCE <object>` | Direct and attribute evidence, decoded native memo text or explicit failure | Bounded to 20 per section |
| Workbench DDict tab | Object grid/filter, Refresh, Fields, Tags, Relations, Evidence, Source panes | Read-only GUI; latest shared-reader behavior awaits rebuilt GUI proof |
| Native regression executable | `--inspect <catalogdir>` and `--command "<DDICT arguments>"` | Developer inspector, not a separate product executable |
| Bounded curation inventory | Maintained JSON inventories and hashes across named roots | File/catalog assessment, not a replacement for runtime inspection |
| Legacy Python dictionary helper | Counts/status/object lookup via pydottalk | Prototype; old path, fixed expected counts, legacy table allowlist |

The GUI is concrete source, not merely a plan:
[main_frame.cpp:673](../../../src/gui/wx/main_frame.cpp#L673) builds the DDict
page and [main_frame.cpp:1474](../../../src/gui/wx/main_frame.cpp#L1474) loads
the shared catalog view. `wb.run.ps1` calls `run-wb.ps1`, which selects the
Workbench executable from named build locations. The inspected
`build/src/gui/wx/Release/dottalk_wb.exe` was last written September 16, before
today's change. No GUI was rebuilt or launched in this review, following the
maintainer's decision to defer wb. Existence of that older binary does not
prove today's long-name GUI behavior.

For daily use, start with the [recipe book](../../datadict/DDICT_METADATA_RECIPE_BOOK_V1.md).
For developer readback, the existing native test covers long filenames,
independent long logical table names, long fields with common prefixes, memo
handling and reporting without writes. The earlier [regression evidence](DDICT_RECIPE_REGRESSION_2026-10-09.json)
records 181 checks and two passing CTests. Those tests were not rerun for this
report and do not certify current live catalog integrity.

## 2. AI Portal incorporation: discoverable, not a direct data feed

Verified connections:

- [Portal search map:77](../../../labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md#L77)
  points to the maintained DDICT index, implementation, tool guide and review.
- [Metadata system registry](../../../selfdoc/metadata_system_registry_v1.json)
  has META-013 (physical dictionary extractor) and META-014 (Python active
  dictionary reader), both marked PROTOTYPE with July verification records.
- [MAINT source:340](../../../src/cli/cmd_maint.cpp#L340) describes DDICT
  cataloging contract rows as a future possibility.

Not found in the specifically inspected integration surfaces:

- No DDICT feed in [portal_feeds.yaml](../../../labtalk/registries/portal_feeds.yaml).
  Its six declared feeds cover HELP, metacollect, accepted manuals, current
  work, audit reports and status projection.
- No DDICT-specific node/trigger in
  [portal_recall_graph.yaml](../../../labtalk/registries/portal_recall_graph.yaml).
- No DDICT reference in `labtalk/portal/labtalk_portal.py` or the inspected
  Portal identifier/task registries. This is a bounded source finding, not
  proof that no other experimental Portal screen exists anywhere.
- The system registry's dictionary entries do not name today's native shared
  reader and its CLI/GUI consumers.

The current full-stack pointer itself needs reconciliation:
[current_fullstack_doc_push.yaml](../../../labtalk/registries/current_fullstack_doc_push.yaml)
still names an August 25 run and August 26 blocked publication entry, while
the maintained full-stack recipe book records September 24/25 work. Its label
must not be treated as a fresh live publication status.

## 3. Full-stack pipeline and schema crosswalk

| Layer | Authority/schema inspected | Integration today |
| --- | --- | --- |
| Native storage | DBF/X64M/DTX and shared DDICT catalog adapter | Long physical/logical/field names and explicit memo failures in CLI/GUI reader |
| Dictionary workspace | `dottalkpp/data/workspaces/ddbase.dtschema` | Eleven legacy DD* tables and their relations; no supplemental DATA_DICTIONARY_* workspace entries |
| Dictionary interchange | DD-006 physical manifest, DD-019 staging package JSON schemas | Sources/tables/fields/run provenance and staged-artifact gates; not a canonical manualgen input contract |
| Reference identity | Reference Identity Authority contract and SelfDoc JSON | Namespaced command/function/subcommand/argument identities with per-field authority rules |
| Structural metadata | SYSCMD physical schema; SYSARGS candidate contract | Separate command metadata and argument export; physical SYSARGS schema absent in inspected metadata schema directory |
| HELP | HELP_TOPIC/SECTION/LINE and HELP_ARTIFACTS, locale companions | Explanatory text, source provenance and reviewed display projections |
| Manual harvest | `manualgen_lib/harvest.py:11` | Exactly six HELP and eight META CSV contracts; no DD* or DATA_DICTIONARY_* family |
| Manual assembly | Accepted workspaces, reference candidates, assembly manifest | Reviewed prose and generated reference paths; source chapter links are not automatic acceptance |
| Website | Website content manifest, accepted-manual feed packet, assembled-manual staging | Accepted publication and assembled candidate are explicitly different products |

Existing intended flow:

```text
source registrations + usage contracts + reference catalogs
    -> HELP and metadata candidates -> validated/accepted stores
    -> hash-bound HELP/META harvest
    -> manualgen reference/prose candidates -> reviewed manual
    -> accepted website feed or explicitly labeled assembled candidate

DDICT native catalog view -> CLI and Workbench
    -> missing versioned export/identity binding -> Portal/manual/site consumers
```

This is not a request to merge all schemas into one table. Storage facts,
documentary assertions, executable behavior, translated text and publication
acceptance have different authorities and lifetimes.

## 4. Confirmed integration and normalization gaps

### A. The dictionary is absent from the explicit manual harvest contract

[harvest.py:11](../../../tools/manualgen/manualgen_lib/harvest.py#L11) requires
14 HELP/META files. The
[input contract](../lanes/full_stack_documentation/MANUALGEN_HELP_META_HARVEST_INPUT_CONTRACT_V1.md)
also warns that attaching fresh evidence does not mean existing prose changes.
The inspected manual assembly and website content manifests contain no DDICT
or recipe-book binding. Today's recipe is linked in source manuals, not yet
registered as a governed assembled/publication part.

### B. Identity normalization is only partial across families

The [reference contract](../lanes/full_stack_documentation/REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1.md)
uses `CMD:`, `FN:`, `SUBCMD:` and owner/kind-qualified `ARG:` keys.
The native [DDICT adapter:18](../../../src/datadict/ddict_catalog_view.cpp#L18)
preserves original IDs and qualifies supplemental rows with `x64:` and source
artifacts with `x64:artifact:`. Those prevent family collisions; they are not
yet a crosswalk to reference identities. A command name match alone is not a
safe join across command, function, physical table and evidence namespaces.

The [SYSARGS emitter:1087](../../../src/meta/metacollect.cpp#L1087) still emits
`ARG_<owner>_<name>` without argument kind. Its candidate contract documents
keyword/placeholder collisions and supplies a uniqueness validator. This
review confirms the construction remains; it does not claim a freshly
measured collision count. The inspected metadata schema directory contains
SYSCMD, SYSCMDSRC and SYSMSG contracts, but no SYSARGS physical contract.

### C. Memo semantics do not survive every export path

[export_help_meta_harvest.py:53](../../../tools/fullstack_docs/export_help_meta_harvest.py#L53)
blanks unresolved memo placeholders. Its manual prose comes from HELP_LINE,
so that behavior is not evidence that all current manual prose is lost.
However, extending that exporter to dictionary memo evidence would discard
information and conflate missing/unresolved/empty. DDICT's native reader has
the stronger behavior: decoded text or an explicit diagnostic.

### D. The registered Python reader lags the native catalog

[datadict_reader.py](../../../tools/datadict/catalog/datadict_reader.py)
defaults to `dottalkpp/data/metadata/datadict`, hard-codes expected counts and
allows only legacy DD* tables. The current native catalog home is
`dottalkpp/data/datadict`. Reusing that prototype as the Portal feed would
reintroduce the location/family split just repaired in the CLI/GUI.

### E. My previous manual anchor edit fails the real vocabulary gate

Executed read-only:

```text
.venv312/Scripts/python.exe tools/fullstack_docs/derive_anchor_map.py --engine D:/code/ccode --check
```

Result: `ANCHOR-DATADICT-SCHEMAS: state 'source-supported' is not in the documented vocabulary`.
Allowed states are candidate, deferred, drift, observed, proven and
proven_candidate. The prior lightweight check verified one linked row, not
this contract. This is my error and corrects the earlier implication that the
manual integration was fully validated. The recipe and source links exist;
the anchor integration is not gate-clean. The CSV is the authority and its
Markdown tables should be derived, not independently edited. Correction is
to classify the row under the existing vocabulary and regenerate/check its
projection, not widen the vocabulary to accommodate this one edit. No repair
was made during this report-only review.

### F. Website candidate and accepted-manual feeds must stay distinct

[build_website_feed_packet.py:15](../../../tools/fullstack_docs/build_website_feed_packet.py#L15)
targets the accepted publication artifact and command-reference pointers.
[stage_assembled_manual_to_site.py:12](../../../tools/fullstack_docs/stage_assembled_manual_to_site.py#L12)
explicitly stages an assembled CANDIDATE to stable latest-download routes.
Both exist. A successful candidate copy cannot establish accepted-publication
freshness or that a chapter reached the public site. Some feed proposal text
also embeds old page counts; derive those from the selected artifact manifest.

## 5. Recommended order for integration

1. Repair the anchor classification/projection and reconcile current-run and
   registry pointers. Add the recipe as a maintained manual part with a stable
   part ID and explicit publication disposition.
2. Define a versioned DDICT export contract over the shared native reader.
   Preserve physical filename, logical table/field names, type/width, original
   ID, family-qualified ID, endpoint kinds, memo state, source hash and run ID.
   Preserve diagnostics; do not replace them with empty strings.
3. Add an explicit identity crosswalk between dictionary entities and canonical
   CMD/FN/SUBCMD/ARG identities. Keep aliases as relationships. Resolve SYSARGS
   owner/kind identity and reviewed physical schema before loading candidates.
4. Register the native producer/consumers and a DDICT Portal feed/recall entry.
   Show freshness, family coverage, review diagnostics and links to raw proof.
   Start with a read-only report, using the same native semantics as Workbench.
5. Extend manualgen with an explicit versioned dictionary input manifest and
   a candidate renderer for schema/relationship/evidence sections. Bind each
   rendered claim to row identity and source hash. Keep authored recipes as
   maintained prose; do not overwrite them with raw row dumps.
6. Feed accepted manual parts and approved dictionary projections to websites
   through the existing manifest/review stages. Preserve the separate candidate
   route and acceptance status. Verify route content and hashes after deployment.

Acceptance should prove member-level completeness, long-name preservation,
typed joins, resolved memo text or explicit failure, stable identity, stale
input detection and consumer lineage. Add an end-to-end fixture with deliberate
ID collisions, missing memo evidence and changed hashes so a gate cannot pass
merely because file counts match.

## Limits and state left behind

Read/source inspection plus one anchor validator run; no full-stack push,
catalog update, GUI launch, export, manual generation, website checkout access
or live website check. Old proof numbers are labeled as inherited. Existing
source/doc edits and all concurrent work were left unchanged. This report
records the manual anchor defect rather than silently correcting it during
an examination request.
