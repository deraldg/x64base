# Help / Document Family System Guide v1

Status: active operator and maintainer guide
Scope: comments evidence, HELP DATA, CMDHELP, CMDHELPCHK, DOTHELP, FOXHELP, MANUAL, and the current documentation-generation family around them

## Purpose

This guide explains the DotTalk++ help/document family from beginning to end:

- what belongs to the family
- where the physical files live
- which parts are evidence, generated data, runtime surfaces, or validation layers
- how to regenerate and maintain each layer
- how an operator should inspect and use the family without breaking continuity

This is the practical starting document. The lane manifests and proof reports remain supporting doctrine.

## Family model

The current family is not one monolithic system. It is a stack of related systems.

### Layer 1: Source contracts and comments

This is the lowest durable source of truth for command help continuity.

Inputs:

- `src/cli/cmd_*.cpp`
- other command or subsystem source files
- leading header comments
- `@dottalk.usage v1` blocks
- command identity fields such as `command:` or `surface:`

Primary outputs:

- `SRCFILE`
- `SRCBLOCK`
- `SRCLINE`
- `SRCUSAGE`
- `SRCCLASS`
- `SRCDISP`
- `SRCALIAS`
- `MEMO_LINES`

Runtime location:

- [comments.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- `D:\code\ccode\dottalkpp\data\comments`

This layer answers: "does the source contract exist, and how was it classified?"

### Layer 2: HELP DATA build

This is the current generated help catalog used by `CMDHELP` and related help data readers.

Primary tables:

- `HELP_TOPIC`
- `HELP_SECTION`
- `HELP_LINE`
- `HELP_ARTIFACTS`

Locale seam tables already present:

- `HELP_TOPIC_LOCALE`
- `HELP_SECTION_LOCALE`
- `HELP_LINE_LOCALE`
- `HELP_ARTIFACT_LOCALE`

Legacy compatibility tables still carried:

- `commands.dbf`
- `cmd_args.dbf`

Runtime location:

- [help.dtschemas](/D:/code/ccode/dottalkpp/data/workspaces/help.dtschemas:1)
- `D:\code\ccode\dottalkpp\data\help`
- `D:\code\ccode\dottalkpp\data\indexes\help`
- `D:\code\ccode\dottalkpp\data\lmdb\help`

Important current boundary:

- `CMDHELP BUILD` still mines source files and usage contracts directly
- the `comments` DBFs are preserved evidence, but are not yet the primary live feed for HELP DATA generation

### Layer 3: Validation and checkpointing

This is the audit layer between source, evidence, generated help data, and runtime surfaces.

Primary command:

- `CMDHELPCHK`

This layer answers: "do registry, contracts, help artifacts, and related catalogs align?"

### Layer 4: Compiled router catalogs

These are compiled read-only lookup catalogs, separate from HELP DATA.

Primary source files:

- `dotref.hpp`
- `foxref.hpp`

Primary runtime surfaces:

- `DOTHELP`
- `FOXHELP`
- `HELP /DOT <term>`
- `HELP /FOX <term>`

This layer answers: "does the compiled catalog and router path work?"

### Layer 5: Manual/document catalog family

This is related to HELP, but separate from HELP DATA.

Primary runtime inspector:

- `MANUAL`

Primary accepted catalog workspace:

- [manual.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/manual.dtschema:1)

Primary accepted catalog location:

- `D:\code\ccode\docs\manuals\developer\manualgen\accepted_catalogs\man_catalog_v1\dbf`

Catalog tables:

- `MANANCHOR`
- `MANAPPX`
- `MANHASH`
- `MANMEDIA`
- `MANPUB`
- `MANREVIEW`
- `MANRUN`
- `MANSECTION`

This layer answers: "what accepted manual/document artifacts exist, and can the runtime inspect them?"

## What belongs to the family

The practical help/document family currently includes:

- source usage contracts and source header comments
- comments evidence tables and reload pipeline
- HELP DATA generation via `CMDHELP BUILD`
- runtime help readers such as `HELP` and `CMDHELP`
- compiled catalog readers such as `DOTHELP` and `FOXHELP`
- validation/checkpoint command `CMDHELPCHK`
- manual/document accepted catalog inspection through `MANUAL`
- legacy compatibility help tables `commands.dbf` and `cmd_args.dbf`

It does not mean all layers are generated from one master database yet. That is still future work.

## Physical layout

### Source and compiled-reference inputs

- `D:\code\ccode\src\cli\cmd_help.cpp`
- `D:\code\ccode\src\cli\cmdhelp.cpp`
- `D:\code\ccode\src\cli\command_helpchk.cpp`
- `D:\code\ccode\src\cli\cmd_dothelp.cpp`
- `D:\code\ccode\src\cli\cmd_foxhelp.cpp`
- `D:\code\ccode\src\cli\cmd_manual.cpp`
- `D:\code\ccode\src\dotref.hpp`
- `D:\code\ccode\src\foxref.hpp`

### Comments evidence runtime assets

- [comments.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- [SOURCE_COMMENT_RESET_RELOAD.dts](/D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- `D:\code\ccode\dottalkpp\data\comments`
- `D:\code\ccode\dottalkpp\data\indexes\comments`
- `D:\code\ccode\dottalkpp\data\lmdb\comments`
- `D:\code\ccode\dottalkpp\docs\generated\staging\source_comment_metadata_import_v1`

### HELP DATA runtime assets

- [cmdhelp.dts](/D:/code/ccode/dottalkpp/data/cmdhelp.dts:1)
- [selfhelp.dts](/D:/code/ccode/dottalkpp/data/selfhelp.dts:1)
- [help.dtschemas](/D:/code/ccode/dottalkpp/data/workspaces/help.dtschemas:1)
- `D:\code\ccode\dottalkpp\data\help`
- `D:\code\ccode\dottalkpp\data\indexes\help`
- `D:\code\ccode\dottalkpp\data\lmdb\help`

### Manual/document accepted catalog assets

- [manual.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/manual.dtschema:1)
- `D:\code\ccode\docs\manuals\developer\manualgen\accepted_catalogs\man_catalog_v1\dbf`

### Maintenance doctrine and proof notes

- [README.md](/D:/code/ccode/docs/maintenance/lanes/help/README.md:1)
- [COOKBOOK_v1.md](/D:/code/ccode/docs/maintenance/lanes/help/COOKBOOK_v1.md:1)
- [COMMENTS_HELP_PROOF_WORKFLOW_v1.md](/D:/code/ccode/docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md:1)
- [HELP_FAMILY_STATUS_MANIFEST_v1.md](/D:/code/ccode/docs/maintenance/lanes/help/HELP_FAMILY_STATUS_MANIFEST_v1.md:1)
- [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](/D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md:1)
- [COMMENTS_PIPELINE_MANIFEST_v1.md](/D:/code/ccode/docs/maintenance/lanes/comments/COMMENTS_PIPELINE_MANIFEST_v1.md:1)
- [MANUALGEN_BLACKBOX_MANIFEST_v1.md](/D:/code/ccode/docs/maintenance/lanes/manualgen/MANUALGEN_BLACKBOX_MANIFEST_v1.md:1)
- [CMDHELPCHK_MAINTENANCE_NOTES_v1.md](/D:/code/ccode/docs/maintenance/lanes/cmdhelpchk/CMDHELPCHK_MAINTENANCE_NOTES_v1.md:1)

## Current truth hierarchy

When a help or documentation surface is wrong, classify from the bottom upward.

1. Source command/runtime behavior
2. Source usage contract and header comment
3. Comments evidence tables
4. HELP DATA generation
5. `CMDHELPCHK` validation
6. `dotref.hpp` / `foxref.hpp`
7. Compiled binary or copied runtime binary
8. Router/runtime help surface
9. Manual/document accepted catalog, if the issue is in `MANUAL`

Do not jump straight to `HELP /DOT` or `MANUAL` output and assume that is the broken layer.

## Runtime surfaces and what they prove

### `HELP`

Top-level user help router.

Important paths:

- `HELP`
- `HELP <topic>`
- `HELP /DOT <term>`
- `HELP /FOX <term>`

What it proves:

- router behavior
- help presentation behavior
- related surface integration

What it does not prove by itself:

- current HELP DATA build correctness
- comments evidence correctness
- compiled catalog correctness in every other surface

### `CMDHELP`

Current HELP DATA build/report/inspection surface.

Important paths:

- `CMDHELP`
- `CMDHELP <topic>`
- `CMDHELP BUILD`
- `CMDHELP BUILD V2`
- `CMDHELP BUILD LEGACY`

What it proves:

- current HELP DATA visibility
- help-data builder/report continuity

What it does not prove by itself:

- `HELP /DOT`
- `DOTHELP`
- `FOXHELP`

### `CMDHELPCHK`

Validation and checkpoint surface.

Important paths:

- `CMDHELPCHK`
- `CMDHELPCHK REF`
- `CMDHELPCHK REFLECT`
- `CMDHELPCHK ARTIFACTS`
- `CMDHELPCHK ARTIFACTS . 20`
- `CMDHELPCHK V2 . 20`
- `CMDHELPCHK <dir> [limit]`

What it proves:

- alignment of reflection data, HELP/catalog files, and legacy/current artifact structure

What it should remain:

- report-only by default

### `DOTHELP`

Read-only compiled `dotref.hpp` inspector.

Important paths:

- `DOTHELP`
- `DOTHELP <term>`
- `DOTHELP USAGE`
- `HELP /DOT <term>`

What it proves:

- compiled DotTalk catalog visibility
- router/catalog continuity above HELP DATA

### `FOXHELP`

Read-only compiled `foxref.hpp` inspector.

Important paths:

- `FOXHELP`
- `FOXHELP <name>`
- `FOXHELP <search>`
- `FOXHELP USAGE`

Alias:

- `FH`

What it proves:

- historical/compatibility catalog visibility

### `MANUAL`

Read-only accepted-catalog manual inspector.

Important paths:

- `MANUAL`
- `MANUAL STATUS`
- `MANUAL TABLES`
- `MANUAL COUNTS`
- `MANUAL RESOLVE <token>`

What it proves:

- accepted `MAN*` catalog availability and inspection continuity

What it does not prove by itself:

- HELP DATA correctness
- router/catalog correctness in `DOTHELP`

## Beginning-to-end generation workflow

This is the current practical workflow.

### Phase A: Maintain source contracts

Keep command and subsystem source headers current.

Current expectations:

- a command/subsystem should have a top header block
- usage contract should be present where applicable
- command identity can come from `command:` or `surface:`

This is the first layer to repair when a surface disappears.

### Phase B: Stage or regenerate comments evidence inputs

The canonical live reload script is:

- [SOURCE_COMMENT_RESET_RELOAD.dts](/D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)

It recreates the comments lane tables and imports staged CSV snapshots from:

- `D:\code\ccode\dottalkpp\docs\generated\staging\source_comment_metadata_import_v1`

Current important note:

- the `IMPORT` path is now CSV-record aware
- this matters because multiline quoted metadata rows must survive import intact

### Phase C: Reload comments evidence

In DotTalk++ runtime:

```text
DO x64
DO scripts\comments\SOURCE_COMMENT_RESET_RELOAD
```

Or inspect the comments workspace directly:

```text
SETPATH DBF COMMENTS
SETPATH INDEXES INDEXES\COMMENTS
SETPATH LMDB LMDB\COMMENTS
WORKSPACE LOAD comments
WORKSPACE
```

Use this to answer:

- does `SRCFILE` know the source file
- does `SRCUSAGE` know the command
- was the block classified correctly
- was the item accepted, deferred, or marked for review

### Phase D: Build HELP DATA

In DotTalk++ runtime:

```text
CMDHELP BUILD
```

Compatibility path:

```text
CMDHELP BUILD LEGACY
```

Current behavior:

- `CMDHELP BUILD` writes the current HELP DATA DBFs
- `CMDHELP BUILD V2` is a compatibility alias for `CMDHELP BUILD`
- `CMDHELP BUILD LEGACY` drives the older `commands.dbf` / `cmd_args.dbf` path

### Phase E: Inspect HELP DATA runtime tables

Use the stock helper script:

```text
DO cmdhelp
```

That script sets:

- `DBF = HELP`
- `INDEXES = INDEXES\HELP`
- `LMDB = LMDB\HELP`

And opens the help workspace.

Equivalent direct sequence:

```text
SETPATH DBF HELP
SETPATH INDEXES INDEXES\HELP
SETPATH LMDB LMDB\HELP
WORKSPACE LOAD help
WORKSPACE
```

Current workspace file name is:

- `help.dtschemas`

That plural extension is intentional and accepted.

### Phase E.1: Apply locale workflow rules

Before treating HELP locale tables as live user text, preserve the current contract:

1. canonical HELP rows are still the source-authority default
2. locale rows are companion overlays
3. missing or unreviewed locale rows must fall back to canonical HELP text

See:

- [HELP_LOCALE_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_LOCALE_WORKFLOW_v1.md)

Current intended consumer shape remains explicit preview first, not silent default replacement:

```text
CMDHELP <topic> PREVIEW LOCALE <locale>
```

or:

```text
CMDHELP <topic> LOCALE <locale>
```

Normal behavior must remain:

```text
CMDHELP <topic>
```

That rule keeps canonical HELP continuity intact while locale rows mature.

### Phase F: Validate alignment

Use report-only validation before making more edits.

Examples:

```text
CMDHELPCHK
CMDHELPCHK ARTIFACTS
CMDHELPCHK ARTIFACTS . 20
CMDHELPCHK REF
```

Use this layer to decide whether the defect is in:

- registry/reflection
- HELP DATA artifacts
- legacy compatibility rows
- a higher router/catalog layer

### Phase G: Prove runtime router/catalog surfaces

Examples:

```text
HELP
HELP HELP
HELP /DOT HELP
DOTHELP
DOTHELP HELP
FOXHELP
FOXHELP APPEND
```

Interpretation rule:

- green `CMDHELP` with red `HELP /DOT` means the fault is above HELP DATA
- that usually points at `dotref.hpp`, compile/copy continuity, or router behavior

### Phase H: Inspect manual/document accepted catalogs

Examples:

```text
MANUAL STATUS
MANUAL TABLES
MANUAL COUNTS
MANUAL RESOLVE HELP
```

Or open the workspace:

```text
WORKSPACE LOAD manual
WORKSPACE
```

Current note:

- `manual.dtschema` uses absolute DBF paths into the accepted manualgen catalog directory
- that is valid today, but is a portability seam to revisit later

## Operator use patterns

### Use the help family as a reader

For ordinary reading:

- `HELP`
- `HELP <topic>`
- `CMDHELP <topic>`
- `DOTHELP <term>`
- `FOXHELP <term>`
- `MANUAL STATUS`

### Use the family as an inspector

For table/workspace inspection:

- `DO cmdhelp`
- `WORKSPACE LOAD comments`
- `WORKSPACE LOAD manual`

### Use the family as a checkpoint chain

When proving a surface:

1. inspect source contract
2. inspect comments evidence
3. rebuild HELP DATA if appropriate
4. run `CMDHELPCHK`
5. smoke `HELP`, `CMDHELP`, `DOTHELP`, `FOXHELP`, or `MANUAL`

## Maintenance rules

### Rule 1: Start report-only

Before mutating:

- identify the failing layer
- name the intended mutation
- keep backups/rollback in mind

### Rule 2: Do not patch higher layers to hide lower-layer defects

Examples of bad practice:

- hand-editing HELP tables when the source contract is missing
- patching `dotref.hpp` to hide a comments-pipeline failure
- blaming `MANUAL` for a HELP DATA defect

### Rule 3: Only mutate one proof layer at a time

If comments are red, repair comments first.
If HELP DATA is red, repair HELP DATA next.
Only then move to router/catalog smoke.

### Rule 4: Keep evidence and presentation separate

- `comments` is preserved evidence
- HELP DATA is generated presentation/catalog material
- `dotref.hpp` and `foxref.hpp` are compiled curated catalogs
- `MAN*` accepted catalogs are document/publication evidence

### Rule 5: Preserve legacy compatibility until a deliberate retirement gate

`commands.dbf` and `cmd_args.dbf` are still part of the family.
They should not be removed casually while older surfaces still rely on them.

## Language and locale status

The family already contains real localization seams, and the locale workflow is now explicit even though full multilingual shell reporting is still in progress.

Current state:

- HELP DATA has locale companion tables
- canonical HELP remains the default source-authority read path
- locale HELP should resolve by canonical identity plus `LOCALE_ID`
- future locale consumers should use explicit preview behavior first
- manuals/document artifacts are good localization candidates
- source comments remain English evidence by design
- many shell/runtime status lines are still being migrated into language-aware messaging

Practical policy:

- preserve and maintain the locale tables now
- do not let locale rows silently replace canonical HELP rows
- use canonical/source English as the fallback authority
- keep comments/source-contract evidence English-focused
- continue moving user-facing shell/status output toward language-aware selection at runtime

This means the help/document family is already partially prepared for multilingual documentation even though full multilingual runtime shell reporting is not finished.

## Common failure classes

### Source exists, help missing

Check:

- source contract block
- staged comments import snapshot
- comments reload
- `CMDHELP BUILD`

### `CMDHELP` green, `HELP /DOT` red

Check:

- `dotref.hpp`
- compiled binary freshness
- copy-to-runtime freshness
- router behavior

### `MANUAL` green, `CMDHELP` missing

Check:

- source contract and comments lane for `MANUAL`
- HELP DATA build and artifact presence

### Comments reload ran, but rows are wrong

Check:

- staging CSV snapshots
- import quoting/multiline integrity
- classification/disposition logic

### Workspace opens fail

Check:

- `SETPATH` roots
- workspace filename
- absolute path dependencies, especially in `manual.dtschema`

## Canonical smoke recipes

### Parent help family smoke

```text
HELP
HELP HELP
CMDHELP
CMDHELP USAGE
DOTHELP
DOTHELP HELP
FOXHELP
FOXHELP APPEND
CMDHELPCHK
CMDHELPCHK ARTIFACTS . 20
```

### Comments evidence smoke

```text
SETPATH DBF COMMENTS
SETPATH INDEXES INDEXES\COMMENTS
SETPATH LMDB LMDB\COMMENTS
WORKSPACE LOAD comments
WORKSPACE
```

### HELP DATA workspace smoke

```text
DO cmdhelp
WORKSPACE
```

### Manual accepted-catalog smoke

```text
MANUAL STATUS
MANUAL TABLES
MANUAL COUNTS
WORKSPACE LOAD manual
WORKSPACE
```

## What is stable today

- comments lane as preserved evidence
- canonical comments reload path
- HELP DATA tables plus legacy compatibility tables
- `CMDHELP` build/report surface
- `CMDHELPCHK` checkpoint role
- `DOTHELP` and `FOXHELP` as compiled read-only catalogs
- `MANUAL` as accepted-catalog runtime inspector

## What is still an active future seam

- making comments DBFs the primary HELP DATA builder feed
- broader multilingual shell/status reporting
- portability cleanup for absolute-path catalog/workspace assets such as `manual.dtschema`
- fuller checkpoint comparison between HELP DATA and DOTREF/FOXREF/router surfaces

## Practical bottom line

If you are maintaining the help/document family, think in this order:

1. source contract
2. comments evidence
3. HELP DATA generation
4. validation/checkpoint
5. compiled help catalogs
6. runtime help surfaces
7. accepted manual/document catalogs

That order prevents category mistakes, keeps the family repeatable, and matches the way the current DotTalk++ repo actually works.
