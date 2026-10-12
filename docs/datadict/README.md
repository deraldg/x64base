# DotTalk++ Data Dictionary

Maintained entry point. Owner: member.derald. Curation review: 2026-10-09.

DDICT is the read-only Data Dictionary command inside DotTalk++. The same catalog
helpers also serve the Workbench GUI. This directory holds its design history,
catalog definitions, policies, and evidence; the implementation is under `src`.

Start with the [current catalog assessment](../maintenance/reviews/DDICT_CATALOG_AUTHORITY_2026-10-09.md)
before refreshing data. The [shared-view implementation and proof](../maintenance/reviews/DDICT_CATALOG_VIEW_IMPLEMENTATION_2026-10-09.md)
adds both families to the CLI and GUI through an explicit read-only adapter.
The workspace schema remains legacy. DATA_DICTIONARY_* tables hold different
records and fields; they are not drop-in replacements. See the proof for local
build status and unresolved data findings before assuming a deployed runtime.

## Navigate by task

| Task | Start here |
| --- | --- |
| Build, report and maintain metadata | [Data dictionary and metadata recipe book](DDICT_METADATA_RECIPE_BOOK_V1.md) |
| Understand the command | [cmd_ddict.cpp](../../src/cli/cmd_ddict.cpp), `cmd_DDICT` |
| Locate catalogs | [ddict_catalog_paths.cpp](../../src/datadict/ddict_catalog_paths.cpp), `find_catalog_dir` |
| Understand field reads | [ddict_dbf_reader.cpp](../../src/datadict/ddict_dbf_reader.cpp), `read_dbf_table_checked` |
| Read both families | [ddict_catalog_view.cpp](../../src/datadict/ddict_catalog_view.cpp), `read_catalog_view` |
| Resolve objects and aliases | [object resolver](../../src/datadict/ddict_object_resolver.cpp) and [catalog bindings](../../src/datadict/ddict_catalog_resolver.cpp) |
| Inspect GUI use | [main_frame.cpp](../../src/gui/wx/main_frame.cpp), `LoadDDictCatalog` and `read_catalog_view` |
| Inspect workspace use | [ddbase.dtschema](../../dottalkpp/data/workspaces/ddbase.dtschema) |
| Find runtime usage text | [helpdata_messages.cpp](../../src/help/helpdata_messages.cpp), `DDictUsageText` |
| Choose a maintenance tool | [tool guide](../../tools/datadict/README.md) |
| Review catalog families and curation | [authority assessment](../maintenance/reviews/DDICT_CATALOG_AUTHORITY_2026-10-09.md), [consolidation plan](../maintenance/reviews/DDICT_CONSOLIDATION_PLAN_2026-10-09.md) |
| Inspect measured members and hashes | [bounded inventory](../maintenance/reviews/DDICT_CURATION_INVENTORY_2026-10-09.json) |
| Find historical HELP validation | [June 26 closeout](../maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md) |
| Dogfood long names and native DTX | [test_ddict_catalog_view.cpp](../../src/tests/test_ddict_catalog_view.cpp) |
| Review resolver regression coverage | [test_ddict_catalog_dir.cpp](../../src/tests/test_ddict_catalog_dir.cpp) |

## Command surface

```text
DDICT                         && STATUS when no subcommand is given
DDICT HELP                    && also ? or USAGE
DDICT STATUS
DDICT TABLES
DDICT OBJECTS [TYPE <type>] [PROFILE <profile>] [FAMILY LEGACY|X64]
DDICT FIELDS <table-or-alias>
DDICT TAGS <table-or-alias>
DDICT REL <object> [IN|OUT|BOTH]
DDICT EVIDENCE <object>
```

FIELDS shows physical schema names and widths for recognized catalog tables,
then curated field objects through the existing owner aliases. STATUS reports
presence, family counts and review diagnostics; it does not certify freshness.
TAGS requires a CDX/LMDB artifact before claiming physical index artifacts.
Use `DDICT OBJECTS FAMILY X64` to reach supplemental records within the bounded
listing, then the displayed `x64:` identity for REL/EVIDENCE. Full long names and
memo text are preserved. Unavailable memos are labeled, not silently empty.
The [original review](../maintenance/reviews/DDICT_CROSSWALK_2026-10-09.md) is the
pre-implementation baseline.

## Storage and authority

| Surface | Repository location |
| --- | --- |
| Catalog DBFs and memo sidecars | `dottalkpp/data/datadict/` |
| CDX artifacts | `dottalkpp/data/indexes/datadict/` |
| LMDB artifacts | `dottalkpp/data/lmdb/datadict/` |
| Workspace schema | `dottalkpp/data/workspaces/ddbase.dtschema` |

The [layout policy](policy/DD095_DATADICT_LAYOUT_POLICY.md) separates this catalog
from feature metadata. `data/metadata/datadict` is a historical/fallback location,
not the active home in this checkout. The nested `data/datadict/datadict` copy is
under review; its presence is not a second authoring authority.

## Supporting directory roles

| Directory | Role |
| --- | --- |
| `specs/` | [Closed DD-series history](specs/README.md); old NEXT_ACTIONS are not current instructions |
| `contracts/`, `definitions/`, `schemas/` | Historical stage contracts, table/field/tag definitions, interchange schemas; check current applicability before use |
| `policy/` | Recorded layout and schema-promotion policy |
| `policies/` | Baseline, status, script-boundary, and generated-artifact policies; distinct from `policy/` |
| `packages/`, `drafts/`, `fragments/` | Original packages and historical candidate material |
| `reports/`, `manifests/`, `runlog/` | Run evidence and generated outputs; reports are ignored by default |
| `baselines/`, `review_queue/`, `reviews/` | Accepted snapshot pointers and review/disposition evidence |
| `candidates/`, `backups/` | Staged artifacts and recovery material; not maintained source |
| `templates/` | Engineering templates; runtime-facing templates also live under `dottalkpp/scripts/datadict` |

New maintained assessments live in `docs/maintenance/reviews` so they are visible
to Git. An old green report retains its date and scope; it does not certify the
current binary. Do not run a historical patch/apply script simply because this
index links its directory. Catalog promotion, index rebuilds, and publication
remain separate operations. The companion website is https://x64base.com.
