# Comments, Help, and Router Proof Workflow v1

Status: active maintenance workflow doctrine
Scope: comments, help, cmdhelp, cmdhelpchk, dothelp, help /dot

## Purpose

This workflow defines the current proof order for the DotTalk++ help family.

It exists to prevent category mistakes such as:

- blaming `HELP /DOT` when the failure is really in HELP DATA generation
- blaming `CMDHELP` when the command contract never existed in source
- assuming the `comments` workspace is already the live build input for HELP DATA

The workflow is intentionally conservative and continuity-first.

## Current doctrine

The live system currently works in four distinct layers:

1. `COMMENTS`
   Source evidence preservation:
   source comments, header blocks, and `@dottalk.usage v1` are harvested into `SRC*` evidence tables.

2. `CMDHELP BUILD`
   Collection/build layer:
   current HELP DATA is built from registry facts, source usage contracts, curated rows, standard messages, and direct source mining.

3. `CMDHELPCHK`
   Validation/checkpoint layer:
   compare registry, source contracts, HELP DATA, and related catalogs without assuming all runtime surfaces are green.

4. `DOTHELP` / `HELP /DOT`
   Router/catalog proof layer:
   prove compiled DOTREF routing and runtime lookup behavior.

These layers are related, but one green layer does not prove the others.

## Continuity rules

- Start report-only.
- Do not mutate more than one proof layer at a time.
- Keep evidence, build, validation, and router proof separate in notes and closure reports.
- Record the last green point before moving upward to the next layer.
- If a lower layer is red, stop and repair there before testing the next layer.

## Workflow

### Phase 1: Evidence

Goal:
prove the source contract exists before touching HELP DATA or DOTREF.

Check:

- source file exists
- header/comment block exists where expected
- leading usage-contract headers may be `//` line blocks or `/* ... */` block headers
- `@dottalk.usage v1` exists where expected
- command identity may come from `command:` or `surface:` depending on the lane contract
- comments workspace knows the file and command
- classifier/disposition state is understandable
- if source is green but `SRC*` rows are missing, inspect the staged source-comment import snapshot before blaming HELP or DOTREF

Primary evidence:

- `dottalkpp/data/comments`
- `dottalkpp/data/workspaces/comments.dtschema`
- `SRCFILE`
- `SRCUSAGE`
- `SRCCLASS`
- `SRCDISP`
- `dottalkpp/docs/generated/staging/source_comment_metadata_import_v1`

Current repair rule:

- if staged `SRC*` imports are stale or missing the target command, repair the comments lane first
- prefer staged source-comment upsert/regeneration plus canonical comments reload
- do not bypass the comments lane by hand-editing HELP DATA or DOTREF to compensate

Do not conclude yet:

- that HELP DATA is correct
- that `CMDHELP` is green
- that `DOTHELP` or `HELP /DOT` is green

### Phase 2: HELP DATA build

Goal:
prove current HELP DATA was built correctly from the current live inputs.

Check:

- `CMDHELP BUILD` completes
- current HELP DATA DBFs are present
- expected artifact rows are present
- contract rows were mined/reported

Primary evidence:

- `CMDHELP BUILD`
- `help_line.dbf`
- `help_topic.dbf`
- `help_artifacts.dbf`
- `commands.dbf`
- `cmd_args.dbf`

Important boundary:

- current HELP DATA builds still mine source/contracts directly
- current HELP DATA builds do not yet consume the `comments` DBFs as the primary live feed

### Phase 3: Validation

Goal:
prove the collection is internally coherent before blaming the router/catalog layer.

Check:

- registry entry exists
- usage contract exists
- HELP DATA artifacts exist
- legacy rows are understood where applicable
- known mismatches are classified, not hand-waved

Primary evidence:

- `CMDHELPCHK`
- coverage reports
- artifact summaries
- mismatch notes

Do not conclude yet:

- that `DOTHELP` or `HELP /DOT` must therefore work

### Phase 4: Router proof

Goal:
prove compiled DOTREF/runtime routing.

Check:

- `DOTHELP <topic>`
- `HELP /DOT <topic>`
- router/catalog smoke against the built runtime

Primary evidence:

- `DOTHELP`
- `HELP /DOT`
- `dotref.hpp`
- runtime smoke/readback

Interpretation rule:

- green `CMDHELP` with red `HELP /DOT` means the problem is above HELP DATA
- likely layers then are DOTREF source, compiled binary, install copy, or router behavior

### Phase 5: Closure

Every workflow pass should end with a short closure note:

- source evidence status
- HELP DATA build status
- CMDHELPCHK status
- DOTHELP/HELP /DOT status
- last green checkpoint
- next allowed gate

## Minimal troubleshooting ladder

When a command/help topic is wrong, classify in this order:

1. runtime command surface
2. source usage contract
3. comments evidence
4. HELP DATA build
5. CMDHELPCHK validation
6. DOTREF/catalog source
7. compiled binary/install copy
8. router/runtime lookup

## Workflow ownership

- `comments` lane owns evidence preservation
- `help` lane owns HELP DATA collection/build
- `cmdhelpchk` lane owns validation/checkpoint duties
- `help` plus DOTREF/router surfaces own `DOTHELP` / `HELP /DOT` proof

## Current next step

Use this workflow as the continuity rule for:

- comments-to-HELP crosswalk audits
- HELP/CMDHELP/DOTREF pipeline audits
- CMDHELPCHK crosswalk alignment
