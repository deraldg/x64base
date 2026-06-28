# DotTalk++ Command Reference Usage Contract Harvest v1

Status: simple source harvest  
Source root: `D:\code\ccode`  
Generated from `@dottalk.usage v1` blocks and nearby source comments.

This is not the final polished command reference. It is the current raw manual seed: each entry keeps the usage contract, source path, and nearby comments that a human or AI can turn into reference prose.

Total harvested usage blocks: 457

Companion CSV: `docs/manuals/command_reference/command_reference_usage_contract_harvest_v1.csv`

## How To Use This Harvest

- Treat `summary`, `usage`, `notes`, `risk`, and `related` as the command contract seed.
- Treat `Source comments` as prose hints, not automatically reader-ready documentation.
- Promote a command to the reader manual only after HELP/META alignment and runtime proof are checked.
- Keep support-only entries if they explain infrastructure, but do not present them as normal user commands.

## Commands

### (unnamed)

Source: `src/cli/cmd_ddict.cpp`  

---

### (unnamed)

Source: `src/cli/cmd_dotscript.cpp`  

Usage contract:

```text
DOTSCRIPT <file>
DOTSCRIPT @<file>
DOTSCRIPT <file> OUT <transcript-file>
DOTSCRIPT <file> OUTPUT <transcript-file>
DOTSCRIPT TRACE <file>
DOTSCRIPT TRACE <file> OUT <transcript-file>
DOTSCRIPT <file> OUT <transcript-file> APPEND
```

Source comments:

```text
@dottalk.contract DOTSCRIPT TRANSCRIPT v1
command: DOTSCRIPT
source: cmd_dotscript.cpp
contract_update: MDO-377G v1.1
purpose: DOTSCRIPT executes .dts command scripts and may tee full runtime output to a transcript.
```

---

### (unnamed)

Source: `src/cli/cmd_if.cpp`  

---

### (unnamed)

Source: `src/cli/cmd_lmdb.cpp`  

Source comments:

```text
closes_lmdb_backend: LMDB CLOSE
  mutates_order_state: OPEN USE CLOSE
  reads_index_data: INFO SEEK DUMP SCAN
  mutates_table_data: no
  global_lmdb_state: no
related:
  CDX
  CNX
  SET INDEX
  SET ORDER
  LMDBDUMP
  LMDB_UTIL
```

---

### (unnamed)

Source: `src/cli/cmd_rel.cpp`  

Source comments:

```text
src/cli/cmd_rel.cpp
REL command dispatcher. Keeps REL subcommand parsing in one place and forwards
to the underlying RELATIONS / SET RELATIONS / JOIN / ENUM handlers.
```

---

### (unnamed)

Source: `src/cli/helpdata_cmdhelp_bridge.cpp`  

Source comments:

```text
Other metadata/risk keys are intentionally not emitted as
renderable help rows.
```

---

### (unnamed)

Source: `src/cli/helpdata_cmdhelp_bridge.cpp`  

Source comments:

```text
Other metadata/risk keys are intentionally not emitted as
renderable help rows.
```

---

### (unnamed)

Source: `src/cli/helpdata_cmdhelp_bridge.cpp`  

Source comments:

```text
Contract supplement: if the heuristic miner skips a small command file
```

---

### (unnamed)

Source: `src/cli/helpdata_cmdhelp_bridge.hpp`  

Source comments:

```text
Source miner diagnostics. These are for operator confidence and
CMDHELPCHK-style validation, not for user-facing command help.
```

---

### (unnamed)

Source: `src/cli/shell_transcript.cpp`  

Source comments:

```text
@dottalk.contract v1
component: shell_transcript
role: implementation of shared shell transcript capture service
owner: DotTalk++ CLI / SelfDoc command infrastructure
first_consumer: DOTSCRIPT OUT/OUTPUT transcript capture
behavior: TranscriptTeeBuf duplicates stream writes; ScopedShellTranscript owns start/stop lifecycle
safety: restores std::cout/std::cerr buffers on scope exit; nested calls reuse active transcript instead of replacing it
mutation_boundary: no DBF/CDX/LMDB/HELP/CMDHELPCHK/MANSTAR mutation; source service only
```

---

### (unnamed)

Source: `src/cli/shell_transcript.hpp`  

Source comments:

```text
@dottalk.contract v1
component: shell_transcript
role: shared shell transcript capture service
owner: DotTalk++ CLI / SelfDoc command infrastructure
first_consumer: DOTSCRIPT OUT/OUTPUT transcript capture
future_consumer: TEST logfile/full-output capture after DOTSCRIPT proof
safety: service only; no DBF/CDX/LMDB/HELP/CMDHELPCHK/MANSTAR mutation
```

---

### (unnamed)

Source: `src/help/helpdata_messages.cpp`  

Source comments:

```text
============================================================================
File: src/help/helpdata_messages.cpp
Purpose: Phase-two localized message resolver for DotTalk++.
============================================================================
```

---

### (unnamed)

Source: `src/help/helpdata_messages.cpp`  

Source comments:

```text
en-US is explicit even though MessageDef::text remains the final fallback.
```

---

### (unnamed)

Source: `src/help/helpdata_source_miner.cpp`  

Source comments:

```text
Intentionally require stream-output syntax. This avoids re-mining catalog
initializer prose while still catching local usage/help emitters.
```

---

### (unnamed)

Source: `src/help/helpdata_source_miner.cpp`  

Source comments:

```text
Fallback: collect a comment/plain-text block until two blank lines.
```

---

### (unnamed)

Source: `src/meta/metacollect.cpp`  

Source comments:

```text
============================================================================
File: src/meta/metacollect.cpp
Purpose: Read-only source and metadata fact extraction for metacollect.
Boundary: Scan source and metadata DBFs only; emit reports; never mutate DBFs.
============================================================================
```

---

### (unnamed)

Source: `src/meta/metacollect.cpp`  

Source comments:

```text
============================================================================
File: src/meta/metacollect.cpp
Purpose: Read-only source and metadata fact extraction for metacollect.
Boundary: Scan source and metadata DBFs only; emit reports; never mutate DBFs.
============================================================================
```

---

### (unnamed)

Source: `x64base/src/cli/cmd_bbox.cpp`  

Source comments:

```text
usage: BBOX USAGE
usage: BBOX MODEL
usage: BBOX LANES
usage: BBOX COMMENTS
usage: BBOX HELP
usage: BBOX MANUALGEN
usage: BBOX DATADICT
usage: BBOX MESSAGING
usage: BBOX MAINT
note: BBOX is read-only and educational.
note: BBOX explains SelfDoc maintenance lanes as data -> process -> information systems.
note: BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source files, runtime scripts, or publication artifacts.
```

---

### (unnamed)

Source: `x64base/src/cli/cmd_ddict.cpp`  

---

### (unnamed)

Source: `x64base/src/cli/cmd_dotscript.cpp`  

Usage contract:

```text
DOTSCRIPT <file>
DOTSCRIPT @<file>
DOTSCRIPT <file> OUT <transcript-file>
DOTSCRIPT <file> OUTPUT <transcript-file>
DOTSCRIPT TRACE <file>
DOTSCRIPT TRACE <file> OUT <transcript-file>
DOTSCRIPT <file> OUT <transcript-file> APPEND
```

Source comments:

```text
@dottalk.contract DOTSCRIPT TRANSCRIPT v1
command: DOTSCRIPT
source: cmd_dotscript.cpp
contract_update: MDO-377G v1.1
purpose: DOTSCRIPT executes .dts command scripts and may tee full runtime output to a transcript.
```

---

### (unnamed)

Source: `x64base/src/cli/cmd_if.cpp`  

---

### (unnamed)

Source: `x64base/src/cli/cmd_lmdb.cpp`  

Source comments:

```text
closes_lmdb_backend: LMDB CLOSE
  mutates_order_state: OPEN USE CLOSE
  reads_index_data: INFO SEEK DUMP SCAN
  mutates_table_data: no
  global_lmdb_state: no
related:
  CDX
  CNX
  SET INDEX
  SET ORDER
  LMDBDUMP
  LMDB_UTIL
```

---

### (unnamed)

Source: `x64base/src/cli/cmd_rel.cpp`  

Source comments:

```text
src/cli/cmd_rel.cpp
REL command dispatcher. Keeps REL subcommand parsing in one place and forwards
to the underlying RELATIONS / SET RELATIONS / JOIN / ENUM handlers.
```

---

### (unnamed)

Source: `x64base/src/cli/helpdata_cmdhelp_bridge.cpp`  

Source comments:

```text
Other metadata/risk keys are intentionally not emitted as
renderable help rows.
```

---

### (unnamed)

Source: `x64base/src/cli/helpdata_cmdhelp_bridge.cpp`  

Source comments:

```text
Other metadata/risk keys are intentionally not emitted as
renderable help rows.
```

---

### (unnamed)

Source: `x64base/src/cli/helpdata_cmdhelp_bridge.cpp`  

Source comments:

```text
Contract supplement: if the heuristic miner skips a small command file
```

---

### (unnamed)

Source: `x64base/src/cli/helpdata_cmdhelp_bridge.hpp`  

Source comments:

```text
Source miner diagnostics. These are for operator confidence and
CMDHELPCHK-style validation, not for user-facing command help.
```

---

### (unnamed)

Source: `x64base/src/cli/shell_transcript.cpp`  

Source comments:

```text
@dottalk.contract v1
component: shell_transcript
role: implementation of shared shell transcript capture service
owner: DotTalk++ CLI / SelfDoc command infrastructure
first_consumer: DOTSCRIPT OUT/OUTPUT transcript capture
behavior: TranscriptTeeBuf duplicates stream writes; ScopedShellTranscript owns start/stop lifecycle
safety: restores std::cout/std::cerr buffers on scope exit; nested calls reuse active transcript instead of replacing it
mutation_boundary: no DBF/CDX/LMDB/HELP/CMDHELPCHK/MANSTAR mutation; source service only
```

---

### (unnamed)

Source: `x64base/src/cli/shell_transcript.hpp`  

Source comments:

```text
@dottalk.contract v1
component: shell_transcript
role: shared shell transcript capture service
owner: DotTalk++ CLI / SelfDoc command infrastructure
first_consumer: DOTSCRIPT OUT/OUTPUT transcript capture
future_consumer: TEST logfile/full-output capture after DOTSCRIPT proof
safety: service only; no DBF/CDX/LMDB/HELP/CMDHELPCHK/MANSTAR mutation
```

---

### (unnamed)

Source: `x64base/src/help/helpdata_messages.cpp`  

Source comments:

```text
============================================================================
File: src/help/helpdata_messages.cpp
Purpose: Phase-two localized message resolver for DotTalk++.
============================================================================
```

---

### (unnamed)

Source: `x64base/src/help/helpdata_messages.cpp`  

Source comments:

```text
en-US is explicit even though MessageDef::text remains the final fallback.
```

---

### (unnamed)

Source: `x64base/src/help/helpdata_source_miner.cpp`  

Source comments:

```text
Intentionally require stream-output syntax. This avoids re-mining catalog
initializer prose while still catching local usage/help emitters.
```

---

### (unnamed)

Source: `x64base/src/help/helpdata_source_miner.cpp`  

Source comments:

```text
Fallback: collect a comment/plain-text block until two blank lines.
```

---

### ABOUT

Source: `src/cli/cmd_about.cpp`  
Owner: `DOT|ABOUT`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `ABOUT USAGE`  

Purpose:

Print DotTalk++ project identity, lineage, author, runtime environment, and
  current session summary.

Usage contract:

```text
ABOUT
  ABOUT USAGE
```

Notes:

```text
ABOUT with no arguments prints the full project/runtime report.
  ABOUT USAGE prints command usage only.
  ABOUT is read-only and does not mutate table data or session state.
```

Related:

```text
VERSION
  SQLVER
```

Source comments:

```text
src/cli/cmd_about.cpp
ABOUT
Print project identity, lineage, author, history, and runtime environment.
```

---

### ABOUT

Source: `x64base/src/cli/cmd_about.cpp`  
Owner: `DOT|ABOUT`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `ABOUT USAGE`  

Purpose:

Print DotTalk++ project identity, lineage, author, runtime environment, and
  current session summary.

Usage contract:

```text
ABOUT
  ABOUT USAGE
```

Notes:

```text
ABOUT with no arguments prints the full project/runtime report.
  ABOUT USAGE prints command usage only.
  ABOUT is read-only and does not mutate table data or session state.
```

Related:

```text
VERSION
  SQLVER
```

Source comments:

```text
src/cli/cmd_about.cpp
ABOUT
Print project identity, lineage, author, history, and runtime environment.
```

---

### AGGS

Source: `src/cli/cmd_aggs.cpp`  
Owner: `DOT|AGGS`  
Category: `aggregate`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `AGGS USAGE`  

Purpose:

AGGS is the aggregate family/owner for the direct aggregate verbs
  SUM, AVG, MIN, and MAX.

Usage contract:

```text
AGGS USAGE
  SUM USAGE
  SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
  AVG USAGE
  AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
  MIN USAGE
  MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
  MAX USAGE
  MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
```

Notes:

```text
AGGS with no arguments prints aggregate-family usage.
  SUM, AVG, MIN, and MAX are the direct aggregate verbs; AGGS owns the aggregate family.
  Persistent SET FILTER and optional FOR/WHERE predicates both participate in visibility.
  Cursor position is restored best-effort after the aggregate scan.
  Aggregate commands report values; they do not mutate table data.
```

Related:

```text
COUNT
  WHERE
  SETFILTER
```

Source comments:

```text
Key behavior:
  - If <value_expr> compiles to a numeric program (LitNumber or Arith), use it.
  - Else, if <value_expr> is a simple identifier matching a field name,
    read that field directly and parse as double (FoxPro-ish SUM <field>).
Filtering model:
  - persistent SET FILTER is part of the logical rowset
  - optional FOR/WHERE predicate is additionally applied
  - optional DELETED / NOT DELETED / !DELETED suffix
Cursor cohesion:
  - save/restore recno()
Relation refresh suppression during full scan:
  - shell_rel_refresh_push/pop
```

---

### AGGS

Source: `x64base/src/cli/cmd_aggs.cpp`  
Owner: `DOT|AGGS`  
Category: `aggregate`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `AGGS USAGE`  

Purpose:

AGGS is the aggregate family/owner for the direct aggregate verbs
  SUM, AVG, MIN, and MAX.

Usage contract:

```text
AGGS USAGE
  SUM USAGE
  SUM <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
  AVG USAGE
  AVG <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
  MIN USAGE
  MIN <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
  MAX USAGE
  MAX <value_expr> [FOR <pred>] [WHERE <pred>] [DELETED|NOT DELETED|!DELETED]
```

Notes:

```text
AGGS with no arguments prints aggregate-family usage.
  SUM, AVG, MIN, and MAX are the direct aggregate verbs; AGGS owns the aggregate family.
  Persistent SET FILTER and optional FOR/WHERE predicates both participate in visibility.
  Cursor position is restored best-effort after the aggregate scan.
  Aggregate commands report values; they do not mutate table data.
```

Related:

```text
COUNT
  WHERE
  SETFILTER
```

Source comments:

```text
Key behavior:
  - If <value_expr> compiles to a numeric program (LitNumber or Arith), use it.
  - Else, if <value_expr> is a simple identifier matching a field name,
    read that field directly and parse as double (FoxPro-ish SUM <field>).
Filtering model:
  - persistent SET FILTER is part of the logical rowset
  - optional FOR/WHERE predicate is additionally applied
  - optional DELETED / NOT DELETED / !DELETED suffix
Cursor cohesion:
  - save/restore recno()
Relation refresh suppression during full scan:
  - shell_rel_refresh_push/pop
```

---

### APPEND

Source: `src/cli/cmd_append.cpp`  
Owner: `DOT|APPEND`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data index memo record-pointer`  
Usage access: `APPEND USAGE`  

Purpose:

Append one or more blank records to the current table, using smart append
  paths that maintain keys and active indexes, or raw append paths when requested.

Usage contract:

```text
APPEND USAGE
  APPEND
  APPEND <count>
  APPEND MANY <count>
  APPEND RAW
  APPEND RAW MANY <count>
```

Notes:

```text
APPEND with no arguments appends one blank record through the shared smart append path.
  APPEND <count> is shorthand for APPEND MANY <count>.
  APPEND MANY <count> performs smart batch append under one lock.
  APPEND RAW appends one record without inline index update.
  APPEND RAW MANY <count> performs raw batch append under one lock.
  Count values must be positive integers.
  APPEND is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
APPEND_BLANK
  REPLACE
  MULTIREP
  TABLE
  COMMIT
```

Source comments:

```text
Supported forms:
  APPEND
  APPEND RAW
  APPEND MANY <count>
  APPEND RAW MANY <count>
  APPEND <count>
Behavior:
  APPEND              -> smart append (keys + inline active index update)
  APPEND RAW          -> raw one-record append (keys, no inline index update)
  APPEND MANY <n>     -> smart batch append under one lock
  APPEND RAW MANY <n> -> raw batch append under one lock
  APPEND <n>          -> shorthand for APPEND MANY <n>
```

---

### APPEND

Source: `x64base/src/cli/cmd_append.cpp`  
Owner: `DOT|APPEND`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data index memo record-pointer`  
Usage access: `APPEND USAGE`  

Purpose:

Append one or more blank records to the current table, using smart append
  paths that maintain keys and active indexes, or raw append paths when requested.

Usage contract:

```text
APPEND USAGE
  APPEND
  APPEND <count>
  APPEND MANY <count>
  APPEND RAW
  APPEND RAW MANY <count>
```

Notes:

```text
APPEND with no arguments appends one blank record through the shared smart append path.
  APPEND <count> is shorthand for APPEND MANY <count>.
  APPEND MANY <count> performs smart batch append under one lock.
  APPEND RAW appends one record without inline index update.
  APPEND RAW MANY <count> performs raw batch append under one lock.
  Count values must be positive integers.
  APPEND is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
APPEND_BLANK
  REPLACE
  MULTIREP
  TABLE
  COMMIT
```

Source comments:

```text
Supported forms:
  APPEND
  APPEND RAW
  APPEND MANY <count>
  APPEND RAW MANY <count>
  APPEND <count>
Behavior:
  APPEND              -> smart append (keys + inline active index update)
  APPEND RAW          -> raw one-record append (keys, no inline index update)
  APPEND MANY <n>     -> smart batch append under one lock
  APPEND RAW MANY <n> -> raw batch append under one lock
  APPEND <n>          -> shorthand for APPEND MANY <n>
```

---

### APPEND_BLANK

Source: `src/cli/cmd_append_blank.cpp`  
Owner: `DOT|APPEND_BLANK`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data index memo record-pointer`  
Usage access: `APPEND_BLANK USAGE`  

Purpose:

Append one blank record using the shared append support path so APPEND
  and APPEND BLANK behavior stay aligned.

Usage contract:

```text
APPEND_BLANK USAGE
  APPEND_BLANK
  APPEND BLANK
```

Notes:

```text
APPEND_BLANK with no arguments appends one blank record.
  APPEND BLANK is the friendly command spelling when routed by the dispatcher.
  The implementation delegates to dottalk_append_blank_core.
  APPEND_BLANK is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
APPEND
  REPLACE
  TABLE
  COMMIT
```

Source comments:

```text
src/cli/cmd_append_blank.cpp — APPEND BLANK
Delegates to shared append support so APPEND and APPEND BLANK stay aligned.
```

---

### APPEND_BLANK

Source: `x64base/src/cli/cmd_append_blank.cpp`  
Owner: `DOT|APPEND_BLANK`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data index memo record-pointer`  
Usage access: `APPEND_BLANK USAGE`  

Purpose:

Append one blank record using the shared append support path so APPEND
  and APPEND BLANK behavior stay aligned.

Usage contract:

```text
APPEND_BLANK USAGE
  APPEND_BLANK
  APPEND BLANK
```

Notes:

```text
APPEND_BLANK with no arguments appends one blank record.
  APPEND BLANK is the friendly command spelling when routed by the dispatcher.
  The implementation delegates to dottalk_append_blank_core.
  APPEND_BLANK is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
APPEND
  REPLACE
  TABLE
  COMMIT
```

Source comments:

```text
src/cli/cmd_append_blank.cpp — APPEND BLANK
Delegates to shared append support so APPEND and APPEND BLANK stay aligned.
```

---

### AREA

Source: `src/cli/cmd_area.cpp`  
Owner: `DOT|AREA`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `AREA USAGE`  

Purpose:

Report the current work-area slot and current area file/session state.

Usage contract:

```text
AREA
  AREA USAGE
```

Notes:

```text
AREA with no arguments reports the current work-area number, open file,
  record count, current record, DBF flavor, runtime kind, logical name,
  absolute path, and active order/index line.
  AREA is read-only; it reports current area state and does not mutate table data.
```

Related:

```text
DBAREA
  DBAREAS
  STATUS
  STRUCT
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_area.cpp
```

---

### AREA

Source: `x64base/src/cli/cmd_area.cpp`  
Owner: `DOT|AREA`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `AREA USAGE`  

Purpose:

Report the current work-area slot and current area file/session state.

Usage contract:

```text
AREA
  AREA USAGE
```

Notes:

```text
AREA with no arguments reports the current work-area number, open file,
  record count, current record, DBF flavor, runtime kind, logical name,
  absolute path, and active order/index line.
  AREA is read-only; it reports current area state and does not mutate table data.
```

Related:

```text
DBAREA
  DBAREAS
  STATUS
  STRUCT
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_area.cpp
```

---

### ASCEND

Source: `src/cli/cmd_ascend.cpp`  
Owner: `DOT|ASCEND`  
Category: `index`  
Status: `supported`  
Effect: `configure`  
Mutates: `order-state`  
Usage access: `ASCEND USAGE`  

Purpose:

Set the active order/tag direction to ascending for the current work area.

Usage contract:

```text
ASCEND
  ASCEND USAGE
```

Notes:

```text
ASCEND requires an active order except for ASCEND USAGE.
  ASCEND with no arguments mutates order direction to ascending.
  ASCEND does not mutate table records or rebuild indexes.
```

Related:

```text
DESCEND
  SET ORDER
  ORDER
```

---

### ASCEND

Source: `x64base/src/cli/cmd_ascend.cpp`  
Owner: `DOT|ASCEND`  
Category: `index`  
Status: `supported`  
Effect: `configure`  
Mutates: `order-state`  
Usage access: `ASCEND USAGE`  

Purpose:

Set the active order/tag direction to ascending for the current work area.

Usage contract:

```text
ASCEND
  ASCEND USAGE
```

Notes:

```text
ASCEND requires an active order except for ASCEND USAGE.
  ASCEND with no arguments mutates order direction to ascending.
  ASCEND does not mutate table records or rebuild indexes.
```

Related:

```text
DESCEND
  SET ORDER
  ORDER
```

---

### ASCEND/DESCEND

Source: `src/cli/cmd_order.cpp`  
Owner: `DOT|ORDER_IMPL`  
Category: `order-helper`  
Status: `implementation-helper`  
Effect: `order-support`  
Mutates: `none-here`  
Usage access: `owned-by ASCEND/DESCEND command handlers`  

Purpose:

Consolidated order helper/prototype translation unit for ASCEND/DESCEND.

Usage contract:

```text
This file is not the SET ORDER or ORDER command owner.
  User-visible ASCEND/DESCEND usage is owned by their command handlers.
```

Notes:

```text
The file is intentionally low-behavior in this source drop.
  Keep active-order mutation in the actual command handlers/order_state layer.
```

Source comments:

```text
cmd_order.cpp ? consolidated ASCEND and DESCEND commands
Safe to build even if indexing isn't wired yet.
```

---

### ASCEND/DESCEND

Source: `x64base/src/cli/cmd_order.cpp`  
Owner: `DOT|ORDER_IMPL`  
Category: `order-helper`  
Status: `implementation-helper`  
Effect: `order-support`  
Mutates: `none-here`  
Usage access: `owned-by ASCEND/DESCEND command handlers`  

Purpose:

Consolidated order helper/prototype translation unit for ASCEND/DESCEND.

Usage contract:

```text
This file is not the SET ORDER or ORDER command owner.
  User-visible ASCEND/DESCEND usage is owned by their command handlers.
```

Notes:

```text
The file is intentionally low-behavior in this source drop.
  Keep active-order mutation in the actual command handlers/order_state layer.
```

Source comments:

```text
cmd_order.cpp ? consolidated ASCEND and DESCEND commands
Safe to build even if indexing isn't wired yet.
```

---

### ASCII

Source: `src/edu/edu_ascii_table.cpp`  
Owner: `EDU|ASCII`  
Category: `education-reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `ASCII USAGE`  

Purpose:

Print ASCII/extended ASCII reference tables and selected ranges.

Usage contract:

```text
ASCII USAGE
  ASCII
  ASCII ASCII
  ASCII EXT
  ASCII PRINT
  ASCII CTRL
  ASCII RANGE <lo> <hi>
```

Examples:

```text
ASCII
  ASCII ASCII
  ASCII EXT
  ASCII RANGE 32 126
```

Notes:

```text
ASCII USAGE/HELP/? prints usage and does not emit table rows.
  This command is read-only reference output.
  The older source comment name "EDU ASCII TABLE" is not the registered
  command surface in the current runtime.
```

---

### ASCII

Source: `x64base/src/edu/edu_ascii_table.cpp`  
Owner: `EDU|ASCII`  
Category: `education-reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `ASCII USAGE`  

Purpose:

Print ASCII/extended ASCII reference tables and selected ranges.

Usage contract:

```text
ASCII USAGE
  ASCII
  ASCII ASCII
  ASCII EXT
  ASCII PRINT
  ASCII CTRL
  ASCII RANGE <lo> <hi>
```

Examples:

```text
ASCII
  ASCII ASCII
  ASCII EXT
  ASCII RANGE 32 126
```

Notes:

```text
ASCII USAGE/HELP/? prints usage and does not emit table rows.
  This command is read-only reference output.
  The older source comment name "EDU ASCII TABLE" is not the registered
  command surface in the current runtime.
```

---

### AUTODBF

Source: `src/cli/cmd_autodbf.cpp`  
Owner: `DOT|AUTODBF`  
Category: `io schema`  
Status: `experimental`  
Effect: `create import`  
Mutates: `filesystem session schema table-data cursor`  
Usage access: `AUTODBF USAGE`  

Purpose:

Create an X64 DBF from a CSV file and import the CSV rows into the newly
  created table.  CSV headers may become field names; when there is no header,
  deterministic FIELDnnn names are generated.

Usage contract:

```text
AUTODBF USAGE
  AUTODBF <table> FROM <csvfile>
  AUTODBF X64 <table> FROM <csvfile>
  AUTODBF <table> FROM <csvfile> HEADER
  AUTODBF <table> FROM <csvfile> NOHEADER
  AUTODBF <table> FROM <csvfile> AUTO
  AUTODBF <table> FROM <csvfile> TEXTONLY
  AUTODBF <table> FROM <csvfile> INFER
  AUTODBF <table> FROM <csvfile> OVERWRITE
```

Notes:

```text
AUTODBF defaults to X64, AUTO header detection, INFER types, comma CSV.
  AUTO is conservative: it chooses HEADER only when the first row looks like
  names and later data strongly indicates typed data.  Use HEADER or NOHEADER
  to remove ambiguity.
  Field names are normalized to command-safe x64 logical names, uniquified,
  capped to the current x64 logical-name limit, and then passed through the
  existing x64 descriptor fallback/mangling policy.
  Long text is not auto-promoted to M yet; values must fit current fixed-field
  x64base limits.  This avoids silently writing memo object id 0.
  Existing target DBFs are not overwritten unless OVERWRITE is supplied.
```

Related:

```text
CREATE
  IMPORT
  IMPORTSQL
  SETPATH
  STRUCT
```

---

### AUTODBF

Source: `x64base/src/cli/cmd_autodbf.cpp`  
Owner: `DOT|AUTODBF`  
Category: `io schema`  
Status: `experimental`  
Effect: `create import`  
Mutates: `filesystem session schema table-data cursor`  
Usage access: `AUTODBF USAGE`  

Purpose:

Create an X64 DBF from a CSV file and import the CSV rows into the newly
  created table.  CSV headers may become field names; when there is no header,
  deterministic FIELDnnn names are generated.

Usage contract:

```text
AUTODBF USAGE
  AUTODBF <table> FROM <csvfile>
  AUTODBF X64 <table> FROM <csvfile>
  AUTODBF <table> FROM <csvfile> HEADER
  AUTODBF <table> FROM <csvfile> NOHEADER
  AUTODBF <table> FROM <csvfile> AUTO
  AUTODBF <table> FROM <csvfile> TEXTONLY
  AUTODBF <table> FROM <csvfile> INFER
  AUTODBF <table> FROM <csvfile> OVERWRITE
```

Notes:

```text
AUTODBF defaults to X64, AUTO header detection, INFER types, comma CSV.
  AUTO is conservative: it chooses HEADER only when the first row looks like
  names and later data strongly indicates typed data.  Use HEADER or NOHEADER
  to remove ambiguity.
  Field names are normalized to command-safe x64 logical names, uniquified,
  capped to the current x64 logical-name limit, and then passed through the
  existing x64 descriptor fallback/mangling policy.
  Long text is not auto-promoted to M yet; values must fit current fixed-field
  x64base limits.  This avoids silently writing memo object id 0.
  Existing target DBFs are not overwritten unless OVERWRITE is supplied.
```

Related:

```text
CREATE
  IMPORT
  IMPORTSQL
  SETPATH
  STRUCT
```

---

### BANG

Source: `src/cli/cmd_bang.cpp`  
Owner: `DOT|BANG`  
Category: `shell`  
Status: `supported`  
Effect: `execute`  
Mutates: `external-process delegates-command-effects`  
Usage access: `BANG USAGE`  

Purpose:

Launch the host operating-system shell or execute a host shell command.

Usage contract:

```text
BANG
  BANG USAGE
  BANG <command>
  !
  ! <command>
```

Notes:

```text
BANG with no arguments opens an interactive host shell.
  BANG <command> executes the host command and returns.
  The exclamation mark is a shell shortcut/alias for BANG.
  BANG USAGE prints usage and does not launch a shell.
  BANG may indirectly read, write, delete, or execute anything the host shell command does.
```

Related:

```text
PSHELL
  SFTP
  WEB
```

---

### BANG

Source: `x64base/src/cli/cmd_bang.cpp`  
Owner: `DOT|BANG`  
Category: `shell`  
Status: `supported`  
Effect: `execute`  
Mutates: `external-process delegates-command-effects`  
Usage access: `BANG USAGE`  

Purpose:

Launch the host operating-system shell or execute a host shell command.

Usage contract:

```text
BANG
  BANG USAGE
  BANG <command>
  !
  ! <command>
```

Notes:

```text
BANG with no arguments opens an interactive host shell.
  BANG <command> executes the host command and returns.
  The exclamation mark is a shell shortcut/alias for BANG.
  BANG USAGE prints usage and does not launch a shell.
  BANG may indirectly read, write, delete, or execute anything the host shell command does.
```

Related:

```text
PSHELL
  SFTP
  WEB
```

---

### BBOX

Source: `src/cli/cmd_bbox.cpp`  
Owner: `DOT|BBOX`  
Category: `education`  
Status: `experimental`  
Effect: `report`  
Mutates: `none`  
Usage access: `no-open-table`  

Purpose:

Teach and inspect the Blackbox model: data enters a processing system and information comes out.

Usage contract:

```text
BBOX
BBOX USAGE
BBOX MODEL
BBOX LANES
BBOX COMMENTS
BBOX HELP
BBOX MANUALGEN
BBOX DATADICT
BBOX MESSAGING
BBOX MAINT
```

Source comments:

```text
cmd_bbox.cpp
DotTalk++ native Blackbox educational command surface.
```

---

### BBOX

Source: `x64base/src/cli/cmd_bbox.cpp`  
Owner: `DOT|BBOX`  
Category: `education`  
Status: `experimental`  
Effect: `report`  
Mutates: `none`  
Usage access: `no-open-table`  

Purpose:

Teach and inspect the Blackbox model: data enters a processing system and information comes out.

Usage contract:

```text
BBOX
BBOX USAGE
BBOX MODEL
BBOX LANES
BBOX COMMENTS
BBOX HELP
BBOX MANUALGEN
BBOX DATADICT
BBOX MESSAGING
BBOX MAINT
```

Source comments:

```text
cmd_bbox.cpp
DotTalk++ native Blackbox educational command surface.
```

---

### BELL

Source: `src/cli/cmd_bell.cpp`  
Owner: `DOT|BELL`  
Category: `ui`  
Status: `supported`  
Effect: `configure`  
Mutates: `bell-setting audible-notification`  
Usage access: `BELL USAGE`  

Purpose:

Ring the bell when enabled, or turn the shell bell setting on or off.

Usage contract:

```text
BELL
  BELL USAGE
  BELL ON
  BELL OFF
```

Notes:

```text
BELL with no arguments rings the bell when bell is ON; otherwise reports that bell is OFF.
  BELL ON enables the bell and rings it once.
  BELL OFF disables the bell.
  BELL mutates only the shell bell setting and audible notification state.
```

Related:

```text
SET
  COLOR
```

---

### BELL

Source: `x64base/src/cli/cmd_bell.cpp`  
Owner: `DOT|BELL`  
Category: `ui`  
Status: `supported`  
Effect: `configure`  
Mutates: `bell-setting audible-notification`  
Usage access: `BELL USAGE`  

Purpose:

Ring the bell when enabled, or turn the shell bell setting on or off.

Usage contract:

```text
BELL
  BELL USAGE
  BELL ON
  BELL OFF
```

Notes:

```text
BELL with no arguments rings the bell when bell is ON; otherwise reports that bell is OFF.
  BELL ON enables the bell and rings it once.
  BELL OFF disables the bell.
  BELL mutates only the shell bell setting and audible notification state.
```

Related:

```text
SET
  COLOR
```

---

### BETA

Source: `src/cli/cmd_beta.cpp`  
Owner: `DOT|BETA`  
Category: `help`  
Status: `supported`  
Effect: `mixed`  
Mutates: `beta-status-overrides filesystem`  
Usage access: `BETA USAGE`  

Purpose:

List, inspect, and update beta tracking items and runtime beta-status overrides.

Usage contract:

```text
BETA
  BETA USAGE
  BETA LIST
  BETA <id>
  BETA DONE <id>
  BETA DEFER <id>
  BETA DEFERRED <id>
  BETA OPEN <id>
  BETA CLEAR <id>
  BETA CLEAR ALL
  BETA SAVE
  BETA LOAD
```

Notes:

```text
BETA with no arguments lists beta items.
  BETA <id> shows a beta item when the id begins with BETA-.
  DONE, DEFER, DEFERRED, OPEN, CLEAR, and CLEAR ALL mutate runtime beta status overrides.
  SAVE writes beta status overrides to the default status path.
  LOAD reads beta status overrides from the default status path.
  BETA mutates only beta tracking/status data, not table records.
```

Related:

```text
ABOUT
  HELP
  FOXHELP
```

---

### BETA

Source: `x64base/src/cli/cmd_beta.cpp`  
Owner: `DOT|BETA`  
Category: `help`  
Status: `supported`  
Effect: `mixed`  
Mutates: `beta-status-overrides filesystem`  
Usage access: `BETA USAGE`  

Purpose:

List, inspect, and update beta tracking items and runtime beta-status overrides.

Usage contract:

```text
BETA
  BETA USAGE
  BETA LIST
  BETA <id>
  BETA DONE <id>
  BETA DEFER <id>
  BETA DEFERRED <id>
  BETA OPEN <id>
  BETA CLEAR <id>
  BETA CLEAR ALL
  BETA SAVE
  BETA LOAD
```

Notes:

```text
BETA with no arguments lists beta items.
  BETA <id> shows a beta item when the id begins with BETA-.
  DONE, DEFER, DEFERRED, OPEN, CLEAR, and CLEAR ALL mutate runtime beta status overrides.
  SAVE writes beta status overrides to the default status path.
  LOAD reads beta status overrides from the default status path.
  BETA mutates only beta tracking/status data, not table records.
```

Related:

```text
ABOUT
  HELP
  FOXHELP
```

---

### BOOLEAN

Source: `src/edu/edu_boolean.cpp`  
Owner: `EDU|BOOLEAN`  
Category: `education-expression`  
Status: `supported`  
Effect: `evaluate-expression`  
Mutates: `none`  
Usage access: `BOOLEAN USAGE`  

Purpose:

Evaluate a boolean expression through xexpr and print .T. or .F.

Usage contract:

```text
BOOLEAN USAGE
  BOOLEAN <expr>
```

Examples:

```text
BOOLEAN 1 = 1
  BOOLEAN GPA >= 3.0
```

Notes:

```text
BOOLEAN USAGE prints usage before expression evaluation.
  When a table is open, field-aware expressions use the current record.
  This command does not mutate table data.
```

Source comments:

```text
src/cli/edu_boolean.cpp
DotTalk++ BOOLEAN
xexpr migration note:
  This command now calls the xexpr facade instead of reaching directly into
  cli/expr/api.hpp, cli/expr/ast.hpp, and cli/expr/glue_xbase.hpp.
  The command syntax and output remain unchanged.
```

---

### BOOLEAN

Source: `x64base/src/edu/edu_boolean.cpp`  
Owner: `EDU|BOOLEAN`  
Category: `education-expression`  
Status: `supported`  
Effect: `evaluate-expression`  
Mutates: `none`  
Usage access: `BOOLEAN USAGE`  

Purpose:

Evaluate a boolean expression through xexpr and print .T. or .F.

Usage contract:

```text
BOOLEAN USAGE
  BOOLEAN <expr>
```

Examples:

```text
BOOLEAN 1 = 1
  BOOLEAN GPA >= 3.0
```

Notes:

```text
BOOLEAN USAGE prints usage before expression evaluation.
  When a table is open, field-aware expressions use the current record.
  This command does not mutate table data.
```

Source comments:

```text
src/cli/edu_boolean.cpp
DotTalk++ BOOLEAN
xexpr migration note:
  This command now calls the xexpr facade instead of reaching directly into
  cli/expr/api.hpp, cli/expr/ast.hpp, and cli/expr/glue_xbase.hpp.
  The command syntax and output remain unchanged.
```

---

### BOTTOM

Source: `src/cli/cmd_bottom.cpp`  
Owner: `DOT|BOTTOM`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `BOTTOM USAGE`  

Purpose:

Move the current work-area cursor to the last visible/logical record.

Usage contract:

```text
BOTTOM
  BOTTOM USAGE
```

Notes:

```text
BOTTOM with no arguments moves to the last visible/logical record.
  BOTTOM requires an open table except for BOTTOM USAGE.
  BOTTOM uses the AutoByFilter last-record navigation selector.
  BOTTOM mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

---

### BOTTOM

Source: `x64base/src/cli/cmd_bottom.cpp`  
Owner: `DOT|BOTTOM`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `BOTTOM USAGE`  

Purpose:

Move the current work-area cursor to the last visible/logical record.

Usage contract:

```text
BOTTOM
  BOTTOM USAGE
```

Notes:

```text
BOTTOM with no arguments moves to the last visible/logical record.
  BOTTOM requires an open table except for BOTTOM USAGE.
  BOTTOM uses the AutoByFilter last-record navigation selector.
  BOTTOM mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

---

### BROWSE

Source: `src/cli/cmd_browse.cpp`  
Owner: `DOT|BROWSE`  
Category: `ui`  
Status: `supported`  
Effect: `interactive`  
Mutates: `delegates browse module commands`  
Usage access: `BROWSE USAGE`  

Purpose:

Enter the refactored BROWSE module through the legacy global command
  symbol, preserving existing callers while delegating implementation.

Usage contract:

```text
BROWSE USAGE
  BROWSE
  BROWSE EDIT
```

Notes:

```text
BROWSE is a thin forwarder to the browse module.
  BROWSE with no arguments enters interactive browse mode.
  BROWSE EDIT requests edit-capable browse behavior where supported by the module.
  Side effects depend on browse actions and delegated commands.
```

Related:

```text
BROWSER
  BROWSETUI
  LIST
  DISPLAY
  REPLACE
```

Source comments:

```text
src/cli/cmd_browse.cpp — thin forwarder to the refactored BROWSE module
```

---

### BROWSE

Source: `x64base/src/cli/cmd_browse.cpp`  
Owner: `DOT|BROWSE`  
Category: `ui`  
Status: `supported`  
Effect: `interactive`  
Mutates: `delegates browse module commands`  
Usage access: `BROWSE USAGE`  

Purpose:

Enter the refactored BROWSE module through the legacy global command
  symbol, preserving existing callers while delegating implementation.

Usage contract:

```text
BROWSE USAGE
  BROWSE
  BROWSE EDIT
```

Notes:

```text
BROWSE is a thin forwarder to the browse module.
  BROWSE with no arguments enters interactive browse mode.
  BROWSE EDIT requests edit-capable browse behavior where supported by the module.
  Side effects depend on browse actions and delegated commands.
```

Related:

```text
BROWSER
  BROWSETUI
  LIST
  DISPLAY
  REPLACE
```

Source comments:

```text
src/cli/cmd_browse.cpp — thin forwarder to the refactored BROWSE module
```

---

### BROWSER

Source: `src/cli/cmd_browser.cpp`  
Owner: `DOT|BROWSER`  
Category: `ui`  
Status: `supported`  
Effect: `interactive`  
Mutates: `delegates LIST DISPLAY GOTO REPLACE`  
Usage access: `BROWSER USAGE`  

Purpose:

Enter a minimal interactive browser with list, display, goto, edit,
  help, and quit commands, delegating work to existing command handlers.

Usage contract:

```text
BROWSER USAGE
  BROWSER
  BROWSER EDIT
```

Notes:

```text
BROWSER with no arguments enters interactive browse mode.
  BROWSER EDIT displays edit mode in the banner; edit command is available inside the browser.
  Inside BROWSER, L lists records, D displays current record, G moves to a record, E edits via REPLACE, H or question-mark shows help, and Q quits.
  BROWSER itself is interactive; side effects come from delegated GOTO and REPLACE actions.
```

Related:

```text
BROWSE
  BROWSETUI
  LIST
  DISPLAY
  GOTO
  REPLACE
```

Source comments:

```text
cmd_browser.cpp
DotTalk++ ? Minimal interactive BROWSE with editing, no DbArea internals.
Uses existing handlers: LIST, DISPLAY, GOTO, REPLACE.
```

---

### BROWSER

Source: `x64base/src/cli/cmd_browser.cpp`  
Owner: `DOT|BROWSER`  
Category: `ui`  
Status: `supported`  
Effect: `interactive`  
Mutates: `delegates LIST DISPLAY GOTO REPLACE`  
Usage access: `BROWSER USAGE`  

Purpose:

Enter a minimal interactive browser with list, display, goto, edit,
  help, and quit commands, delegating work to existing command handlers.

Usage contract:

```text
BROWSER USAGE
  BROWSER
  BROWSER EDIT
```

Notes:

```text
BROWSER with no arguments enters interactive browse mode.
  BROWSER EDIT displays edit mode in the banner; edit command is available inside the browser.
  Inside BROWSER, L lists records, D displays current record, G moves to a record, E edits via REPLACE, H or question-mark shows help, and Q quits.
  BROWSER itself is interactive; side effects come from delegated GOTO and REPLACE actions.
```

Related:

```text
BROWSE
  BROWSETUI
  LIST
  DISPLAY
  GOTO
  REPLACE
```

Source comments:

```text
cmd_browser.cpp
DotTalk++ ? Minimal interactive BROWSE with editing, no DbArea internals.
Uses existing handlers: LIST, DISPLAY, GOTO, REPLACE.
```

---

### BROWSETUI

Source: `src/cli/cmd_browsetui.cpp`  
Owner: `DOT|BROWSETUI`  
Category: `ui`  
Status: `supported`  
Effect: `interactive`  
Mutates: `delegates create append delete goto replace-like staged edits`  
Usage access: `BROWSETUI USAGE`  

Purpose:

Enter the full-screen Turbo/console browse UI with create, read, update,
  delete, append, navigation, and staged edit support.

Usage contract:

```text
BROWSETUI USAGE
  BROWSETUI
```

Notes:

```text
BROWSETUI with no arguments enters the interactive TUI browser.
  The TUI uses function keys and single-key commands for create, read/list, update/edit, delete, append, goto, help, and quit.
  Edits may be staged and then saved or discarded when navigating or exiting.
  BROWSETUI delegates to existing command handlers for create, append, delete, list/display, goto, and update-like operations.
  BROWSETUI is interactive and may mutate table data or session state depending on user actions.
```

Related:

```text
BROWSE
  BROWSER
  CREATE
  APPEND
  DELETE
  GOTO
```

Source comments:

```text
src/cli/cmd_browsetui.cpp
COMPLETE + TARGETED CLEAR VERSION - No more "declared but not defined" errors
```

---

### BROWSETUI

Source: `x64base/src/cli/cmd_browsetui.cpp`  
Owner: `DOT|BROWSETUI`  
Category: `ui`  
Status: `supported`  
Effect: `interactive`  
Mutates: `delegates create append delete goto replace-like staged edits`  
Usage access: `BROWSETUI USAGE`  

Purpose:

Enter the full-screen Turbo/console browse UI with create, read, update,
  delete, append, navigation, and staged edit support.

Usage contract:

```text
BROWSETUI USAGE
  BROWSETUI
```

Notes:

```text
BROWSETUI with no arguments enters the interactive TUI browser.
  The TUI uses function keys and single-key commands for create, read/list, update/edit, delete, append, goto, help, and quit.
  Edits may be staged and then saved or discarded when navigating or exiting.
  BROWSETUI delegates to existing command handlers for create, append, delete, list/display, goto, and update-like operations.
  BROWSETUI is interactive and may mutate table data or session state depending on user actions.
```

Related:

```text
BROWSE
  BROWSER
  CREATE
  APPEND
  DELETE
  GOTO
```

Source comments:

```text
src/cli/cmd_browsetui.cpp
COMPLETE + TARGETED CLEAR VERSION - No more "declared but not defined" errors
```

---

### BUILDLMDB

Source: `src/cli/cmd_buildlmdb.cpp`  
Owner: `DOT|BUILDLMDB`  
Category: `index`  
Status: `supported`  
Effect: `rebuild`  
Mutates: `lmdb-index-backend filesystem order-state`  
Usage access: `BUILDLMDB USAGE`  

Purpose:

Build or rebuild the LMDB backing store for a CDX container using one LMDB
  environment per table container and named databases for tags.

Usage contract:

```text
BUILDLMDB USAGE
  BUILDLMDB
  BUILDLMDB YES
  BUILDLMDB AUTO
  BUILDLMDB NOPROMPT
  BUILDLMDB CLEAN YES
  BUILDLMDB FORCE YES
  BUILDLMDB QUIET
  BUILDLMDB SILENT
  BUILDLMDB TINY
  BUILDLMDB SMALL
  BUILDLMDB MEDIUM
  BUILDLMDB LARGE
  BUILDLMDB XL
  BUILDLMDB HUGE
  BUILDLMDB MAPSIZE <size> YES
  BUILDLMDB CLEAN MAPSIZE <size> YES
```

Notes:

```text
BUILDLMDB requires an open table except for usage/help requests.
  The public CDX container resolves under INDEXES and the LMDB backend environment resolves under LMDB.
  If an existing LMDB environment would be destructively rebuilt, explicit YES, AUTO, NOPROMPT, QUIET, or SILENT is required.
  CLEAN and FORCE archive the existing environment before rebuild.
  BUILDLMDB releases active index/order state before destructive rebuild.
  BUILDLMDB rebuilds tag databases from current table data.
```

Related:

```text
CDX
  LMDB
  SET ORDER
  INDEX
  REINDEX
```

Source comments:

```text
One LMDB env per table container; multiple tags as named DBs inside (MDB_MAXDBS=1024).
Public/Backend policy:
- Public CDX container resolves under INDEXES.
- LMDB backend env resolves under LMDB.
- Example:
    data\indexes\students.cdx
  -> data\lmdb\students.cdx.d
Workflow policy:
- BUILDLMDB is shell-safe: no nested std::cin prompt reads.
- If an existing LMDB env would be destructively rebuilt, caller must supply
  YES / Y / AUTO / NOPROMPT / QUIET / SILENT explicitly.
- CLEAN / FORCE archives first and proceeds without the destructive prompt path.
```

---

### BUILDLMDB

Source: `x64base/src/cli/cmd_buildlmdb.cpp`  
Owner: `DOT|BUILDLMDB`  
Category: `index`  
Status: `supported`  
Effect: `rebuild`  
Mutates: `lmdb-index-backend filesystem order-state`  
Usage access: `BUILDLMDB USAGE`  

Purpose:

Build or rebuild the LMDB backing store for a CDX container using one LMDB
  environment per table container and named databases for tags.

Usage contract:

```text
BUILDLMDB USAGE
  BUILDLMDB
  BUILDLMDB YES
  BUILDLMDB AUTO
  BUILDLMDB NOPROMPT
  BUILDLMDB CLEAN YES
  BUILDLMDB FORCE YES
  BUILDLMDB QUIET
  BUILDLMDB SILENT
  BUILDLMDB TINY
  BUILDLMDB SMALL
  BUILDLMDB MEDIUM
  BUILDLMDB LARGE
  BUILDLMDB XL
  BUILDLMDB HUGE
  BUILDLMDB MAPSIZE <size> YES
  BUILDLMDB CLEAN MAPSIZE <size> YES
```

Notes:

```text
BUILDLMDB requires an open table except for usage/help requests.
  The public CDX container resolves under INDEXES and the LMDB backend environment resolves under LMDB.
  If an existing LMDB environment would be destructively rebuilt, explicit YES, AUTO, NOPROMPT, QUIET, or SILENT is required.
  CLEAN and FORCE archive the existing environment before rebuild.
  BUILDLMDB releases active index/order state before destructive rebuild.
  BUILDLMDB rebuilds tag databases from current table data.
```

Related:

```text
CDX
  LMDB
  SET ORDER
  INDEX
  REINDEX
```

Source comments:

```text
One LMDB env per table container; multiple tags as named DBs inside (MDB_MAXDBS=1024).
Public/Backend policy:
- Public CDX container resolves under INDEXES.
- LMDB backend env resolves under LMDB.
- Example:
    data\indexes\students.cdx
  -> data\lmdb\students.cdx.d
Workflow policy:
- BUILDLMDB is shell-safe: no nested std::cin prompt reads.
- If an existing LMDB env would be destructively rebuilt, caller must supply
  YES / Y / AUTO / NOPROMPT / QUIET / SILENT explicitly.
- CLEAN / FORCE archives first and proceeds without the destructive prompt path.
```

---

### CALC

Source: `src/cli/cmd_calc.cpp`  
Owner: `DOT|CALC`  
Category: `expression`  
Status: `supported`  
Effect: `evaluate`  
Mutates: `none unless assignment targets an open field`  
Usage access: `CALC USAGE`  

Purpose:

Evaluate an xexpr scalar expression and print the result. When the input
  is an assignment to a real field in the current area, CALC delegates to
  CALCWRITE for mutation semantics.

Usage contract:

```text
CALC USAGE
  CALC <expr>
  CALC (<expr>)
  CALC <field> = <expr>
```

Examples:

```text
CALC 1 + 2
  CALC DATE()
  CALC UPPER(LNAME)
  CALC BALANCE = BALANCE + 10
```

Notes:

```text
CALC with an empty expression preserves existing behavior and prints .F.
  CALC prints Bool, Number, String, and Date results.
  CALC uses xexpr for scalar and field-aware expression evaluation.
  CALC assignment mutates only when the LHS is a real field in the open area.
  Field assignment is delegated to CALCWRITE so table-buffer, memo, validation,
  and direct-write/index semantics stay centralized.
  CALC expression-only mode is read-only; CALC field-assignment mode is a data mutation path.
```

Related:

```text
CALCWRITE
  REPLACE
  MULTIREP
  XEXPR
```

Source comments:

```text
===============================
FILE: src/cli/cmd_calc.cpp
CALC routes RHS evaluation through xexpr facade.
Notes:
- Supports scalar expressions and field-based expressions.
- Supports CALCWRITE-style assignment when the LHS is a real field.
- Result printing preserves Bool / Number / String / Date.
- No-file-open messaging is intentionally not emitted here anymore;
  whether a no-area expression can evaluate is decided deeper in the
  expression layer, not by CALC's final fallback.
===============================
```

---

### CALC

Source: `x64base/src/cli/cmd_calc.cpp`  
Owner: `DOT|CALC`  
Category: `expression`  
Status: `supported`  
Effect: `evaluate`  
Mutates: `none unless assignment targets an open field`  
Usage access: `CALC USAGE`  

Purpose:

Evaluate an xexpr scalar expression and print the result. When the input
  is an assignment to a real field in the current area, CALC delegates to
  CALCWRITE for mutation semantics.

Usage contract:

```text
CALC USAGE
  CALC <expr>
  CALC (<expr>)
  CALC <field> = <expr>
```

Examples:

```text
CALC 1 + 2
  CALC DATE()
  CALC UPPER(LNAME)
  CALC BALANCE = BALANCE + 10
```

Notes:

```text
CALC with an empty expression preserves existing behavior and prints .F.
  CALC prints Bool, Number, String, and Date results.
  CALC uses xexpr for scalar and field-aware expression evaluation.
  CALC assignment mutates only when the LHS is a real field in the open area.
  Field assignment is delegated to CALCWRITE so table-buffer, memo, validation,
  and direct-write/index semantics stay centralized.
  CALC expression-only mode is read-only; CALC field-assignment mode is a data mutation path.
```

Related:

```text
CALCWRITE
  REPLACE
  MULTIREP
  XEXPR
```

Source comments:

```text
===============================
FILE: src/cli/cmd_calc.cpp
CALC routes RHS evaluation through xexpr facade.
Notes:
- Supports scalar expressions and field-based expressions.
- Supports CALCWRITE-style assignment when the LHS is a real field.
- Result printing preserves Bool / Number / String / Date.
- No-file-open messaging is intentionally not emitted here anymore;
  whether a no-area expression can evaluate is decided deeper in the
  expression layer, not by CALC's final fallback.
===============================
```

---

### CALCWRITE

Source: `src/cli/cmd_calcwrite.cpp`  
Owner: `DOT|CALCWRITE`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data table-buffer memo stale-state index`  
Usage access: `CALCWRITE USAGE`  

Purpose:

Evaluate an expression and write the result into a field in the current
  record, preserving type normalization, validation, memo conversion,
  table-buffer semantics, and direct-write index maintenance.

Usage contract:

```text
CALCWRITE USAGE
  CALCWRITE <field> = <expr>
```

Examples:

```text
CALCWRITE BALANCE = BALANCE + 10
  CALCWRITE LNAME = UPPER(LNAME)
  CALCWRITE POSTED = TODAY
```

Notes:

```text
CALCWRITE requires an open table and a current record.
  CALCWRITE requires assignment syntax using '='.
  RHS expressions are evaluated with xexpr against the current area.
  Result values are normalized for the target field type before storage.
  Currency pair fields are validated and normalized through currency helpers.
  X64 memo fields update memo payloads and store memo object-id text.
  When TABLE buffering is ON, CALCWRITE buffers the change and marks the field stale/dirty.
  When TABLE buffering is OFF, CALCWRITE writes through DbArea::replaceFieldStored.
  Direct-write mode uses the engine mutation funnel so active indexes stay consistent.
  CALCWRITE is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
CALC
  REPLACE
  MULTIREP
  TABLE
  COMMIT
```

Source comments:

```text
src/cli/cmd_calcwrite.cpp
```

---

### CALCWRITE

Source: `x64base/src/cli/cmd_calcwrite.cpp`  
Owner: `DOT|CALCWRITE`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data table-buffer memo stale-state index`  
Usage access: `CALCWRITE USAGE`  

Purpose:

Evaluate an expression and write the result into a field in the current
  record, preserving type normalization, validation, memo conversion,
  table-buffer semantics, and direct-write index maintenance.

Usage contract:

```text
CALCWRITE USAGE
  CALCWRITE <field> = <expr>
```

Examples:

```text
CALCWRITE BALANCE = BALANCE + 10
  CALCWRITE LNAME = UPPER(LNAME)
  CALCWRITE POSTED = TODAY
```

Notes:

```text
CALCWRITE requires an open table and a current record.
  CALCWRITE requires assignment syntax using '='.
  RHS expressions are evaluated with xexpr against the current area.
  Result values are normalized for the target field type before storage.
  Currency pair fields are validated and normalized through currency helpers.
  X64 memo fields update memo payloads and store memo object-id text.
  When TABLE buffering is ON, CALCWRITE buffers the change and marks the field stale/dirty.
  When TABLE buffering is OFF, CALCWRITE writes through DbArea::replaceFieldStored.
  Direct-write mode uses the engine mutation funnel so active indexes stay consistent.
  CALCWRITE is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
CALC
  REPLACE
  MULTIREP
  TABLE
  COMMIT
```

Source comments:

```text
src/cli/cmd_calcwrite.cpp
```

---

### CASE

Source: `src/edu/edu_case.cpp`  
Owner: `EDU|CASE`  
Category: `education-reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `CASE USAGE`  

Purpose:

List and show educational case-study catalog entries.

Usage contract:

```text
CASE USAGE
  CASE HELP
  CASE LIST
  CASE SHOW <id>
```

Examples:

```text
CASE
  CASE LIST
  CASE SHOW normalization
```

Notes:

```text
CASE USAGE/HELP/? prints usage before catalog lookup.
  CASE is read-only catalog/reference output.
```

---

### CASE

Source: `x64base/src/edu/edu_case.cpp`  
Owner: `EDU|CASE`  
Category: `education-reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `CASE USAGE`  

Purpose:

List and show educational case-study catalog entries.

Usage contract:

```text
CASE USAGE
  CASE HELP
  CASE LIST
  CASE SHOW <id>
```

Examples:

```text
CASE
  CASE LIST
  CASE SHOW normalization
```

Notes:

```text
CASE USAGE/HELP/? prints usage before catalog lookup.
  CASE is read-only catalog/reference output.
```

---

### CATALOGCANARY

Source: `src/cli/cmd_catalogcanary.cpp`  
Owner: `DOT|CATALOGCANARY`  
Category: `metadata-dev`  
Status: `dev-canary`  
Effect: `report`  
Mutates: `none`  
Usage access: `CATALOGCANARY USAGE`  

Purpose:

Dev canary for the metadata catalog reader adapter. Reads the current
  already-open SYSCMD area and reports adapter row/distribution counts.

Usage contract:

```text
CATALOGCANARY
  CATALOGCANARY USAGE
```

Notes:

```text
CATALOGCANARY does not open SYSCMD.dbf.
  CATALOGCANARY does not call USE or WORKSPACE OPEN.
  CATALOGCANARY expects DotTalk++ to have already prepared the area:
    DO METADATA
    WORKSPACE OPEN DBF
    SELECT SYSCMD
  It calls load_commands_from_area(current_area).
  Registration is intentionally left to the house shell command registry.
```

Related:

```text
METADATA
  WORKSPACE
  USE
  FIELDS
  LIST
  CMDHELPCHK
```

Source comments:

```text
src/cli/cmd_catalogcanary.cpp
```

---

### CATALOGCANARY

Source: `x64base/src/cli/cmd_catalogcanary.cpp`  
Owner: `DOT|CATALOGCANARY`  
Category: `metadata-dev`  
Status: `dev-canary`  
Effect: `report`  
Mutates: `none`  
Usage access: `CATALOGCANARY USAGE`  

Purpose:

Dev canary for the metadata catalog reader adapter. Reads the current
  already-open SYSCMD area and reports adapter row/distribution counts.

Usage contract:

```text
CATALOGCANARY
  CATALOGCANARY USAGE
```

Notes:

```text
CATALOGCANARY does not open SYSCMD.dbf.
  CATALOGCANARY does not call USE or WORKSPACE OPEN.
  CATALOGCANARY expects DotTalk++ to have already prepared the area:
    DO METADATA
    WORKSPACE OPEN DBF
    SELECT SYSCMD
  It calls load_commands_from_area(current_area).
  Registration is intentionally left to the house shell command registry.
```

Related:

```text
METADATA
  WORKSPACE
  USE
  FIELDS
  LIST
  CMDHELPCHK
```

Source comments:

```text
src/cli/cmd_catalogcanary.cpp
```

---

### CDX

Source: `src/cli/cmd_cdx.cpp`  
Owner: `DOT|CDX`  
Category: `index`  
Status: `supported`  
Effect: `mixed`  
Mutates: `index-metadata filesystem`  
Usage access: `CDX USAGE`  

Purpose:

Manage CDX index container metadata: create containers, inspect header/tag
  directories, add tags, and drop tags.

Usage contract:

```text
CDX USAGE
  CDX INFO [<path.cdx>]
  CDX TAGS [<path.cdx>]
  CDX CREATE [<path.cdx>]
  CDX ADDTAG <name> [<path.cdx>]
  CDX DROPTAG <name> [<path.cdx>]
```

Notes:

```text
CDX with no arguments shows usage and does not default to INFO.
  If no path is supplied, CDX first uses the active CDX path from order state when available.
  Otherwise CDX derives <current_dbf_basename>.cdx through the INDEXES path slot.
  CREATE refuses to overwrite an existing file.
  INFO and TAGS are read-only inspection operations and require an existing file.
  ADDTAG and DROPTAG mutate the CDX container tag directory and require an existing file.
  CDX manages container header/tag metadata; backend tag build data persistence is owned elsewhere.
```

Related:

```text
CNX
  INDEX
  SET CDX
  SET ORDER
  REINDEX
```

Source comments:

```text
Behavior change requested:
  - If invoked with no arguments (". cdx"), print help/options and return.
    (Do NOT default to INFO.)
Policy enforced:
  - CREATE: refuse if file exists.
  - INFO/TAGS/ADDTAG/DROPTAG: require existing file (no implicit creation).
  - Default path (no path arg):
      1) if area has active CDX in orderstate: use it
      2) else <current_dbf_basename>.cdx resolved via INDEXES slot
Notes:
  - Tag build data (RUN1) persistence is handled by cdx backend; this command
    is only for container header + tag directory management.
```

---

### CDX

Source: `x64base/src/cli/cmd_cdx.cpp`  
Owner: `DOT|CDX`  
Category: `index`  
Status: `supported`  
Effect: `mixed`  
Mutates: `index-metadata filesystem`  
Usage access: `CDX USAGE`  

Purpose:

Manage CDX index container metadata: create containers, inspect header/tag
  directories, add tags, and drop tags.

Usage contract:

```text
CDX USAGE
  CDX INFO [<path.cdx>]
  CDX TAGS [<path.cdx>]
  CDX CREATE [<path.cdx>]
  CDX ADDTAG <name> [<path.cdx>]
  CDX DROPTAG <name> [<path.cdx>]
```

Notes:

```text
CDX with no arguments shows usage and does not default to INFO.
  If no path is supplied, CDX first uses the active CDX path from order state when available.
  Otherwise CDX derives <current_dbf_basename>.cdx through the INDEXES path slot.
  CREATE refuses to overwrite an existing file.
  INFO and TAGS are read-only inspection operations and require an existing file.
  ADDTAG and DROPTAG mutate the CDX container tag directory and require an existing file.
  CDX manages container header/tag metadata; backend tag build data persistence is owned elsewhere.
```

Related:

```text
CNX
  INDEX
  SET CDX
  SET ORDER
  REINDEX
```

Source comments:

```text
Behavior change requested:
  - If invoked with no arguments (". cdx"), print help/options and return.
    (Do NOT default to INFO.)
Policy enforced:
  - CREATE: refuse if file exists.
  - INFO/TAGS/ADDTAG/DROPTAG: require existing file (no implicit creation).
  - Default path (no path arg):
      1) if area has active CDX in orderstate: use it
      2) else <current_dbf_basename>.cdx resolved via INDEXES slot
Notes:
  - Tag build data (RUN1) persistence is handled by cdx backend; this command
    is only for container header + tag directory management.
```

---

### CHRISTMAS

Source: `src/edu/edu_christmas.cpp`  
Owner: `EDU|CHRISTMAS`  
Category: `education-demo`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `CHRISTMAS USAGE`  

Purpose:

Print the retro colored ASCII Christmas tree demo.

Usage contract:

```text
CHRISTMAS USAGE
  CHRISTMAS
```

Examples:

```text
CHRISTMAS
```

Notes:

```text
CHRISTMAS USAGE/HELP/? prints usage before emitting the tree.
  Non-usage arguments are ignored to preserve prior demo behavior.
```

Source comments:

```text
edu_christmas.cpp
Retro ASCII Christmas tree for DotTalk++ terminal.
Uses segment-level ANSI coloring so visible width and raw output width stay sane.
```

---

### CHRISTMAS

Source: `x64base/src/edu/edu_christmas.cpp`  
Owner: `EDU|CHRISTMAS`  
Category: `education-demo`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `CHRISTMAS USAGE`  

Purpose:

Print the retro colored ASCII Christmas tree demo.

Usage contract:

```text
CHRISTMAS USAGE
  CHRISTMAS
```

Examples:

```text
CHRISTMAS
```

Notes:

```text
CHRISTMAS USAGE/HELP/? prints usage before emitting the tree.
  Non-usage arguments are ignored to preserve prior demo behavior.
```

Source comments:

```text
edu_christmas.cpp
Retro ASCII Christmas tree for DotTalk++ terminal.
Uses segment-level ANSI coloring so visible width and raw output width stay sane.
```

---

### CLEAR

Source: `src/cli/cmd_clear.cpp`  
Owner: `DOT|CLEAR`  
Category: `ui`  
Status: `supported`  
Effect: `screen`  
Mutates: `console`  
Usage access: `CLEAR USAGE`  

Purpose:

Clear the terminal screen using the platform console command or ANSI
  escape sequence without touching the database engine.

Usage contract:

```text
CLEAR USAGE
  CLEAR
  CLS
```

Notes:

```text
CLEAR with no arguments clears the console screen.
  CLS is the registry alias where configured.
  CLEAR is UI-only and does not mutate table data or session state.
```

Related:

```text
COLOR
  HELP
```

Source comments:

```text
src/cli/cmd_clear.cpp
DotTalk++ ? CLEAR (and CLS alias via registry)
Cross-platform default: Windows -> cls; others -> ANSI escape.
We keep it minimal and non-invasive (no engine touches).
```

---

### CLEAR

Source: `x64base/src/cli/cmd_clear.cpp`  
Owner: `DOT|CLEAR`  
Category: `ui`  
Status: `supported`  
Effect: `screen`  
Mutates: `console`  
Usage access: `CLEAR USAGE`  

Purpose:

Clear the terminal screen using the platform console command or ANSI
  escape sequence without touching the database engine.

Usage contract:

```text
CLEAR USAGE
  CLEAR
  CLS
```

Notes:

```text
CLEAR with no arguments clears the console screen.
  CLS is the registry alias where configured.
  CLEAR is UI-only and does not mutate table data or session state.
```

Related:

```text
COLOR
  HELP
```

Source comments:

```text
src/cli/cmd_clear.cpp
DotTalk++ ? CLEAR (and CLS alias via registry)
Cross-platform default: Windows -> cls; others -> ANSI escape.
We keep it minimal and non-invasive (no engine touches).
```

---

### CLOSE

Source: `src/cli/cmd_close.cpp`  
Owner: `DOT|CLOSE`  
Category: `workspace`  
Status: `supported`  
Effect: `close`  
Mutates: `session area memo order table-buffer relations`  
Usage access: `CLOSE USAGE`  

Purpose:

Close the current work area, honoring dirty table-buffer prompts,
  clearing memo/order/table slot state, and clearing affected relation state.

Usage contract:

```text
CLOSE USAGE
  CLOSE
  CLOSE ALL
```

Notes:

```text
CLOSE with no arguments closes the current work area.
  CLOSE ALL currently clears all relations before closing the current area.
  CLOSE prompts or cancels through dirty table-buffer protection when needed.
  CLOSE runs memo sidecar lifecycle hooks before clearing area identity.
  CLOSE clears active order/index state.
  CLOSE resets table buffering state for the slot to off, clean, and fresh.
  CLOSE is a session/area mutation command; it does not directly mutate table records.
```

Related:

```text
USE
  WORKSPACE
  TABLE
  COMMIT
  REL
```

Source comments:

```text
src/cli/cmd_close.cpp
```

---

### CLOSE

Source: `x64base/src/cli/cmd_close.cpp`  
Owner: `DOT|CLOSE`  
Category: `workspace`  
Status: `supported`  
Effect: `close`  
Mutates: `session area memo order table-buffer relations`  
Usage access: `CLOSE USAGE`  

Purpose:

Close the current work area, honoring dirty table-buffer prompts,
  clearing memo/order/table slot state, and clearing affected relation state.

Usage contract:

```text
CLOSE USAGE
  CLOSE
  CLOSE ALL
```

Notes:

```text
CLOSE with no arguments closes the current work area.
  CLOSE ALL currently clears all relations before closing the current area.
  CLOSE prompts or cancels through dirty table-buffer protection when needed.
  CLOSE runs memo sidecar lifecycle hooks before clearing area identity.
  CLOSE clears active order/index state.
  CLOSE resets table buffering state for the slot to off, clean, and fresh.
  CLOSE is a session/area mutation command; it does not directly mutate table records.
```

Related:

```text
USE
  WORKSPACE
  TABLE
  COMMIT
  REL
```

Source comments:

```text
src/cli/cmd_close.cpp
```

---

### CMDHELP

Source: `src/cli/cmdhelp.cpp`  
Owner: `DOT|CMDHELP`  
Category: `help`  
Status: `supported`  
Effect: `build-report`  
Mutates: `helpdata`  
Usage access: `CMDHELP USAGE`  

Purpose:

Build or report the current HELP DATA catalogs and their legacy compatibility views.

Usage contract:

```text
CMDHELP
  CMDHELP USAGE
  CMDHELP BUILD
  CMDHELP BUILD V2
  CMDHELP BUILD LEGACY
  CMDHELP LEGACY
  CMDHELP <topic> PREVIEW LOCALE <locale>
  CMDHELP <topic> LOCALE <locale>
```

Notes:

```text
CMDHELP BUILD writes the current HELP DATA DBFs.
  CMDHELP BUILD V2 is a silent compatibility alias for CMDHELP BUILD.
  CMDHELP BUILD LEGACY drives the old commands.dbf/cmd_args.dbf builder path.
  CMDHELP with no arguments reports current HELP DATA from help_line.dbf.
  CMDHELP LEGACY reports the old commands.dbf/cmd_args.dbf surface.
  Locale preview is explicit-only and does not change normal CMDHELP behavior.
  Preview falls back to canonical/source HELP text when locale rows are missing or blocked.
  The legacy writer/reader remains in this file only as an explicit compatibility path.
  It is no longer the default build/report surface.
```

Related:

```text
HELP
  CMDHELPCHK
  DOTHELP
  FOXHELP
```

---

### CMDHELP

Source: `x64base/src/cli/cmdhelp.cpp`  
Owner: `DOT|CMDHELP`  
Category: `help`  
Status: `supported`  
Effect: `build-report`  
Mutates: `helpdata`  
Usage access: `CMDHELP USAGE`  

Purpose:

Build or report the current HELP DATA catalogs and their legacy compatibility views.

Usage contract:

```text
CMDHELP
  CMDHELP USAGE
  CMDHELP BUILD
  CMDHELP BUILD V2
  CMDHELP BUILD LEGACY
  CMDHELP LEGACY
  CMDHELP <topic> PREVIEW LOCALE <locale>
  CMDHELP <topic> LOCALE <locale>
```

Notes:

```text
CMDHELP BUILD writes the current HELP DATA DBFs.
  CMDHELP BUILD V2 is a silent compatibility alias for CMDHELP BUILD.
  CMDHELP BUILD LEGACY drives the old commands.dbf/cmd_args.dbf builder path.
  CMDHELP with no arguments reports current HELP DATA from help_line.dbf.
  CMDHELP LEGACY reports the old commands.dbf/cmd_args.dbf surface.
  Locale preview is explicit-only and does not change normal CMDHELP behavior.
  Preview falls back to canonical/source HELP text when locale rows are missing or blocked.
  The legacy writer/reader remains in this file only as an explicit compatibility path.
  It is no longer the default build/report surface.
```

Related:

```text
HELP
  CMDHELPCHK
  DOTHELP
  FOXHELP
```

---

### CMDHELPCHK

Source: `src/cli/command_helpchk.cpp`  
Owner: `DOT|CMDHELPCHK`  
Category: `help-diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `CMDHELPCHK USAGE`  

Purpose:

Validate HELP/catalog artifacts and reflection metadata against command
  registry expectations, legacy HELP DBF rows, and HELP DATA v2 artifacts.

Usage contract:

```text
CMDHELPCHK
  CMDHELPCHK USAGE
  CMDHELPCHK REF
  CMDHELPCHK REFLECT
  CMDHELPCHK ARTIFACTS
  CMDHELPCHK ARTIFACTS <dir>
  CMDHELPCHK ARTIFACTS <dir> <limit>
  CMDHELPCHK V2 <dir> <limit>
  CMDHELPCHK <dir> [limit]
```

Notes:

```text
CMDHELPCHK with no arguments runs reflection-system validation.
  REF and REFLECT are explicit names for the reflection validation mode.
  ARTIFACTS and V2 validate HELP DATA v2 help_artifacts.dbf/.dbt.
  A directory argument without a mode runs the legacy commands.dbf/.dbt check.
  CMDHELPCHK reads HELP/catalog files but does not mutate table data.
  CMDHELPCHK v2 external scanner remains separate from this runtime command.
```

Related:

```text
HELP
  CMDHELP
  HELP DATA

Robust validator for commands.dbf/.dbt produced by CMDHELP.
Adds HELP DATA v2 artifact validation for help_artifacts.dbf/.dbt.
Plus reflection-system audit mode.
============================================================================
```

Source comments:

```text
============================================================================
File: src/cli/command_helpchk.cpp
```

---

### CMDHELPCHK

Source: `x64base/src/cli/command_helpchk.cpp`  
Owner: `DOT|CMDHELPCHK`  
Category: `help-diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `CMDHELPCHK USAGE`  

Purpose:

Validate HELP/catalog artifacts and reflection metadata against command
  registry expectations, legacy HELP DBF rows, and HELP DATA v2 artifacts.

Usage contract:

```text
CMDHELPCHK
  CMDHELPCHK USAGE
  CMDHELPCHK REF
  CMDHELPCHK REFLECT
  CMDHELPCHK ARTIFACTS
  CMDHELPCHK ARTIFACTS <dir>
  CMDHELPCHK ARTIFACTS <dir> <limit>
  CMDHELPCHK V2 <dir> <limit>
  CMDHELPCHK <dir> [limit]
```

Notes:

```text
CMDHELPCHK with no arguments runs reflection-system validation.
  REF and REFLECT are explicit names for the reflection validation mode.
  ARTIFACTS and V2 validate HELP DATA v2 help_artifacts.dbf/.dbt.
  A directory argument without a mode runs the legacy commands.dbf/.dbt check.
  CMDHELPCHK reads HELP/catalog files but does not mutate table data.
  CMDHELPCHK v2 external scanner remains separate from this runtime command.
```

Related:

```text
HELP
  CMDHELP
  HELP DATA

Robust validator for commands.dbf/.dbt produced by CMDHELP.
Adds HELP DATA v2 artifact validation for help_artifacts.dbf/.dbt.
Plus reflection-system audit mode.
============================================================================
```

Source comments:

```text
============================================================================
File: src/cli/command_helpchk.cpp
```

---

### CNX

Source: `src/cli/cmd_cnx.cpp`  
Owner: `DOT|CNX`  
Category: `index`  
Status: `supported`  
Effect: `mixed`  
Mutates: `index-metadata filesystem`  
Usage access: `CNX USAGE`  

Purpose:

Manage CNX index container metadata: create containers, inspect header/tag
  directories, add/drop tags, and walk/trace RUN1 tag structures.

Usage contract:

```text
CNX USAGE
  CNX INFO [<path.cnx>]
  CNX TAGS [<path.cnx>]
  CNX CREATE [<path.cnx>]
  CNX ADDTAG <name> [<path.cnx>]
  CNX DROPTAG <name> [<path.cnx>]
  CNX WALK <tag> [<path.cnx>]
  CNX TRACE <tag> [<path.cnx>]
```

Notes:

```text
CNX with no arguments shows usage.
  If no path is supplied, CNX first uses the active CNX path from order state when available.
  Otherwise CNX derives <current_dbf_basename>.cnx through the INDEXES path slot.
  CREATE refuses to overwrite an existing file.
  INFO, TAGS, WALK, and TRACE are read-only inspection/diagnostic operations and require an existing file.
  WALK/TRACE use root_page_off from the CNX tag directory and follow plausible child offsets with loop/depth protection.
  ADDTAG and DROPTAG mutate the CNX container tag directory and require an existing file.
```

Related:

```text
CDX
  INDEX
  SET CNX
  SET ORDER
  REINDEX
```

Source comments:

```text
- ". cnx" with no args prints help/options and returns.
  - CREATE: refuse if file exists.
  - INFO/TAGS/ADDTAG/DROPTAG/WALK: require existing file.
  - Default path (no path arg):
      1) if area has active CNX in orderstate: use it
      2) else <current_dbf_basename>.cnx resolved via INDEXES slot
WALK notes:
  - Read-only diagnostic
  - Uses root_page_off from the CNX tag directory
  - Prints RUN1 header/body summary
  - Follows plausible child offsets recursively with loop/depth protection
  - Does NOT modify CNX or replace backend traversal
```

---

### CNX

Source: `x64base/src/cli/cmd_cnx.cpp`  
Owner: `DOT|CNX`  
Category: `index`  
Status: `supported`  
Effect: `mixed`  
Mutates: `index-metadata filesystem`  
Usage access: `CNX USAGE`  

Purpose:

Manage CNX index container metadata: create containers, inspect header/tag
  directories, add/drop tags, and walk/trace RUN1 tag structures.

Usage contract:

```text
CNX USAGE
  CNX INFO [<path.cnx>]
  CNX TAGS [<path.cnx>]
  CNX CREATE [<path.cnx>]
  CNX ADDTAG <name> [<path.cnx>]
  CNX DROPTAG <name> [<path.cnx>]
  CNX WALK <tag> [<path.cnx>]
  CNX TRACE <tag> [<path.cnx>]
```

Notes:

```text
CNX with no arguments shows usage.
  If no path is supplied, CNX first uses the active CNX path from order state when available.
  Otherwise CNX derives <current_dbf_basename>.cnx through the INDEXES path slot.
  CREATE refuses to overwrite an existing file.
  INFO, TAGS, WALK, and TRACE are read-only inspection/diagnostic operations and require an existing file.
  WALK/TRACE use root_page_off from the CNX tag directory and follow plausible child offsets with loop/depth protection.
  ADDTAG and DROPTAG mutate the CNX container tag directory and require an existing file.
```

Related:

```text
CDX
  INDEX
  SET CNX
  SET ORDER
  REINDEX
```

Source comments:

```text
- ". cnx" with no args prints help/options and returns.
  - CREATE: refuse if file exists.
  - INFO/TAGS/ADDTAG/DROPTAG/WALK: require existing file.
  - Default path (no path arg):
      1) if area has active CNX in orderstate: use it
      2) else <current_dbf_basename>.cnx resolved via INDEXES slot
WALK notes:
  - Read-only diagnostic
  - Uses root_page_off from the CNX tag directory
  - Prints RUN1 header/body summary
  - Follows plausible child offsets recursively with loop/depth protection
  - Does NOT modify CNX or replace backend traversal
```

---

### COBOL

Source: `src/edu/edu_cobol.cpp`  
Owner: `EDU|COBOL`  
Category: `education-toolchain`  
Status: `supported`  
Effect: `export-build-run`  
Mutates: `filesystem external-process`  
Usage access: `COBOL USAGE`  

Purpose:

Export STUDENTS data for COBOL exercises and build/run/test COBOL programs.

Usage contract:

```text
COBOL USAGE
  COBOL EXPORT STUDENTS
  COBOL RUN <program>
  COBOL BUILD <source.cob|source.cbl>
  COBOL TEST <source.cob|source.cbl>
```

Examples:

```text
COBOL EXPORT STUDENTS
  COBOL BUILD hello.cob
  COBOL RUN hello
  COBOL TEST hello.cob
```

Notes:

```text
COBOL USAGE/HELP/? returns before table checks, file export, build, or run.
  EXPORT STUDENTS requires the current area to be the MCC STUDENTS table.
  BUILD/TEST may invoke the configured COBOL compiler.
  RUN/TEST may launch an external program.
```

Source comments:

```text
src/cli/cmd_cobol.cpp
```

---

### COBOL

Source: `x64base/src/edu/edu_cobol.cpp`  
Owner: `EDU|COBOL`  
Category: `education-toolchain`  
Status: `supported`  
Effect: `export-build-run`  
Mutates: `filesystem external-process`  
Usage access: `COBOL USAGE`  

Purpose:

Export STUDENTS data for COBOL exercises and build/run/test COBOL programs.

Usage contract:

```text
COBOL USAGE
  COBOL EXPORT STUDENTS
  COBOL RUN <program>
  COBOL BUILD <source.cob|source.cbl>
  COBOL TEST <source.cob|source.cbl>
```

Examples:

```text
COBOL EXPORT STUDENTS
  COBOL BUILD hello.cob
  COBOL RUN hello
  COBOL TEST hello.cob
```

Notes:

```text
COBOL USAGE/HELP/? returns before table checks, file export, build, or run.
  EXPORT STUDENTS requires the current area to be the MCC STUDENTS table.
  BUILD/TEST may invoke the configured COBOL compiler.
  RUN/TEST may launch an external program.
```

Source comments:

```text
src/cli/cmd_cobol.cpp
```

---

### CODASYL

Source: `src/cli/cmd_codaysl.cpp`  
Owner: `DOT|CODASYL`  
Category: `education`  
Status: `supported`  
Effect: `teaching`  
Mutates: `codasyl-teaching-state cursor`  
Usage access: `CODASYL USAGE`  

Purpose:

Provide a thin CODASYL teaching veneer over already-open DotTalk++ work areas,
  simulating owner/member set traversal without a second storage engine.

Usage contract:

```text
CODASYL USAGE
  CODASYL HELP
  CODASYL MODE ON
  CODASYL MODE OFF
  CODASYL LOAD <world>
  CODASYL SETS
  CODASYL SHOW SET <name>
  CODASYL FIND OWNER <set> <value>
  CODASYL FIND OWNER <owner_alias> <value>
  CODASYL GET FIRST
  CODASYL GET FIRST <set>
  CODASYL GET FIRST <member_alias>
  CODASYL GET NEXT
  CODASYL GET NEXT <set>
  CODASYL GET NEXT <member_alias>
  CODASYL WALK
  CODASYL WALK <set>
  CODASYL WALK <member_alias>
  CODASYL STATUS
```

Notes:

```text
CODASYL with no arguments shows usage.
  This is a teaching adapter and does not create physical CODASYL storage.
  It uses already-open work areas and named set definitions.
  LOAD installs a predefined set map for a named lesson world.
  FIND OWNER captures the current owner and builds a member snapshot.
  GET FIRST and GET NEXT move through the simulated member ring.
  WALK prints a simulated owner/member ring and preserves the member-area cursor best-effort.
  STATUS reports CODASYL teaching state.
```

Related:

```text
WORKSPACE
  REL
  BROWSE
  USE
```

Source comments:

```text
- Uses already-open work areas
  - Uses named "set" definitions (owner alias / member alias / fields)
  - Traversal is computed dynamically by scanning the member area for matches
  - "Ring" behavior is simulated by GET FIRST / GET NEXT over a snapshot vector
Deliberate non-goals:
  - No physical owner/member pointers
  - No on-disk CODASYL storage
  - No bypass of DbArea or the existing engine
Notes:
  - LOAD currently installs a predefined world definition only.
    It does NOT auto-run SCHEMAS LOAD here. Keep this layer thin.
  - This is a LabTalk-facing teaching command, not a new backend.
```

---

### CODASYL

Source: `x64base/src/cli/cmd_codaysl.cpp`  
Owner: `DOT|CODASYL`  
Category: `education`  
Status: `supported`  
Effect: `teaching`  
Mutates: `codasyl-teaching-state cursor`  
Usage access: `CODASYL USAGE`  

Purpose:

Provide a thin CODASYL teaching veneer over already-open DotTalk++ work areas,
  simulating owner/member set traversal without a second storage engine.

Usage contract:

```text
CODASYL USAGE
  CODASYL HELP
  CODASYL MODE ON
  CODASYL MODE OFF
  CODASYL LOAD <world>
  CODASYL SETS
  CODASYL SHOW SET <name>
  CODASYL FIND OWNER <set> <value>
  CODASYL FIND OWNER <owner_alias> <value>
  CODASYL GET FIRST
  CODASYL GET FIRST <set>
  CODASYL GET FIRST <member_alias>
  CODASYL GET NEXT
  CODASYL GET NEXT <set>
  CODASYL GET NEXT <member_alias>
  CODASYL WALK
  CODASYL WALK <set>
  CODASYL WALK <member_alias>
  CODASYL STATUS
```

Notes:

```text
CODASYL with no arguments shows usage.
  This is a teaching adapter and does not create physical CODASYL storage.
  It uses already-open work areas and named set definitions.
  LOAD installs a predefined set map for a named lesson world.
  FIND OWNER captures the current owner and builds a member snapshot.
  GET FIRST and GET NEXT move through the simulated member ring.
  WALK prints a simulated owner/member ring and preserves the member-area cursor best-effort.
  STATUS reports CODASYL teaching state.
```

Related:

```text
WORKSPACE
  REL
  BROWSE
  USE
```

Source comments:

```text
- Uses already-open work areas
  - Uses named "set" definitions (owner alias / member alias / fields)
  - Traversal is computed dynamically by scanning the member area for matches
  - "Ring" behavior is simulated by GET FIRST / GET NEXT over a snapshot vector
Deliberate non-goals:
  - No physical owner/member pointers
  - No on-disk CODASYL storage
  - No bypass of DbArea or the existing engine
Notes:
  - LOAD currently installs a predefined world definition only.
    It does NOT auto-run SCHEMAS LOAD here. Keep this layer thin.
  - This is a LabTalk-facing teaching command, not a new backend.
```

---

### COLOR

Source: `src/cli/cmd_color.cpp`  
Owner: `DOT|COLOR`  
Category: `ui`  
Status: `supported`  
Effect: `configure`  
Mutates: `ui-theme tree-color-setting`  
Usage access: `COLOR USAGE`  

Purpose:

Report or set the console color theme and tree-color behavior.

Usage contract:

```text
COLOR
  COLOR USAGE
  COLOR DEFAULT
  COLOR GREEN
  COLOR AMBER
  COLOR TREE ON
  COLOR TREE OFF
  COLOR TREECOLOR ON
  COLOR TREECOLOR OFF
```

Notes:

```text
COLOR with no arguments reports the current theme, tree-color setting, and tree palette levels.
  COLOR DEFAULT, GREEN, AMBER, and other parseable theme names apply the console theme.
  COLOR TREE ON and COLOR TREE OFF toggle tree-color behavior.
  COLOR TREECOLOR is accepted as an alias for COLOR TREE.
  COLOR mutates UI presentation settings only.
```

Related:

```text
CLEAR
  TREE
  HELP
```

Source comments:

```text
src/cli/cmd_color.cpp
```

---

### COLOR

Source: `x64base/src/cli/cmd_color.cpp`  
Owner: `DOT|COLOR`  
Category: `ui`  
Status: `supported`  
Effect: `configure`  
Mutates: `ui-theme tree-color-setting`  
Usage access: `COLOR USAGE`  

Purpose:

Report or set the console color theme and tree-color behavior.

Usage contract:

```text
COLOR
  COLOR USAGE
  COLOR DEFAULT
  COLOR GREEN
  COLOR AMBER
  COLOR TREE ON
  COLOR TREE OFF
  COLOR TREECOLOR ON
  COLOR TREECOLOR OFF
```

Notes:

```text
COLOR with no arguments reports the current theme, tree-color setting, and tree palette levels.
  COLOR DEFAULT, GREEN, AMBER, and other parseable theme names apply the console theme.
  COLOR TREE ON and COLOR TREE OFF toggle tree-color behavior.
  COLOR TREECOLOR is accepted as an alias for COLOR TREE.
  COLOR mutates UI presentation settings only.
```

Related:

```text
CLEAR
  TREE
  HELP
```

Source comments:

```text
src/cli/cmd_color.cpp
```

---

### COMMIT

Source: `src/cli/cmd_commit.cpp`  
Owner: `DOT|COMMIT`  
Category: `data`  
Status: `supported`  
Effect: `commit`  
Mutates: `table-data table-buffer memo stale-state index`  
Usage access: `COMMIT USAGE`  

Purpose:

Apply buffered TABLE changes to the current area or all open buffered areas,
  locking records at commit time and preserving legacy index rebuild compatibility.

Usage contract:

```text
COMMIT USAGE
  COMMIT
  COMMIT ALL
  COMMIT MANUAL
  COMMIT INTERACTIVE
  COMMIT AUTO
  COMMIT ALL MANUAL
  COMMIT ALL INTERACTIVE
  COMMIT ALL AUTO
```

Notes:

```text
COMMIT with no arguments applies buffered changes for the current area.
  COMMIT ALL applies buffered changes for all open buffered areas.
  TABLE ON buffers changes; COMMIT applies them with record locking.
  MANUAL, INTERACTIVE, and AUTO are accepted for compatibility.
  COMMIT does not rebuild CDX or LMDB containers.
  Legacy INX/IDX and CNX rebuild behavior remains only for legacy index families.
  COMMIT is a data mutation command when buffers contain changes.
```

Related:

```text
TABLE
  REPLACE
  CALCWRITE
  ROLLBACK
  REINDEX
  REBUILD
```

Source comments:

```text
Contract:
- TABLE ON buffers changes; no OS locking should occur during REPLACE/DELETE.
- COMMIT applies buffered changes with locking at commit time.
- COMMIT ALL commits all open areas with buffered changes.
- COMMIT does not rebuild CDX/LMDB. CDX/LMDB has a runtime lifecycle:
  key-field mutations, append, delete, and recall are handled by mutation hooks.
- Legacy index rebuild behavior remains only for legacy index families:
    * INX/IDX -> REINDEX
    * CNX     -> REBUILD
Notes:
- MANUAL / INTERACTIVE / AUTO are accepted for compatibility, but CDX/LMDB
  rebuilds are intentionally ignored by COMMIT.
```

---

### COMMIT

Source: `x64base/src/cli/cmd_commit.cpp`  
Owner: `DOT|COMMIT`  
Category: `data`  
Status: `supported`  
Effect: `commit`  
Mutates: `table-data table-buffer memo stale-state index`  
Usage access: `COMMIT USAGE`  

Purpose:

Apply buffered TABLE changes to the current area or all open buffered areas,
  locking records at commit time and preserving legacy index rebuild compatibility.

Usage contract:

```text
COMMIT USAGE
  COMMIT
  COMMIT ALL
  COMMIT MANUAL
  COMMIT INTERACTIVE
  COMMIT AUTO
  COMMIT ALL MANUAL
  COMMIT ALL INTERACTIVE
  COMMIT ALL AUTO
```

Notes:

```text
COMMIT with no arguments applies buffered changes for the current area.
  COMMIT ALL applies buffered changes for all open buffered areas.
  TABLE ON buffers changes; COMMIT applies them with record locking.
  MANUAL, INTERACTIVE, and AUTO are accepted for compatibility.
  COMMIT does not rebuild CDX or LMDB containers.
  Legacy INX/IDX and CNX rebuild behavior remains only for legacy index families.
  COMMIT is a data mutation command when buffers contain changes.
```

Related:

```text
TABLE
  REPLACE
  CALCWRITE
  ROLLBACK
  REINDEX
  REBUILD
```

Source comments:

```text
Contract:
- TABLE ON buffers changes; no OS locking should occur during REPLACE/DELETE.
- COMMIT applies buffered changes with locking at commit time.
- COMMIT ALL commits all open areas with buffered changes.
- COMMIT does not rebuild CDX/LMDB. CDX/LMDB has a runtime lifecycle:
  key-field mutations, append, delete, and recall are handled by mutation hooks.
- Legacy index rebuild behavior remains only for legacy index families:
    * INX/IDX -> REINDEX
    * CNX     -> REBUILD
Notes:
- MANUAL / INTERACTIVE / AUTO are accepted for compatibility, but CDX/LMDB
  rebuilds are intentionally ignored by COMMIT.
```

---

### CONTINUE

Source: `src/cli/cmd_continue.cpp`  
Owner: `DOT|CONTINUE`  
Category: `navigation`  
Status: `supported`  
Effect: `locate`  
Mutates: `cursor continue-state`  
Usage access: `CONTINUE USAGE`  

Purpose:

Continue a previous LOCATE search, or continue with an explicit FOR
  predicate, following active order when present.

Usage contract:

```text
CONTINUE
  CONTINUE USAGE
  CONTINUE FOR <expr>
```

Notes:

```text
CONTINUE with no arguments reuses the active LOCATE/CONTINUE predicate.
  CONTINUE FOR <expr> searches forward from the current record using the supplied predicate.
  CONTINUE follows active order when one is present; otherwise it scans physical order.
  CONTINUE requires an open table except for CONTINUE USAGE.
  CONTINUE mutates cursor/search state but does not mutate table data.
```

Related:

```text
LOCATE
  FIND
  SEEK
```

Source comments:

```text
src/cli/cmd_continue.cpp
CONTINUE
CONTINUE FOR <expr>
Continues search after the current record.
If an order is active, traversal follows active order.
Otherwise traversal is physical forward order.
```

---

### CONTINUE

Source: `x64base/src/cli/cmd_continue.cpp`  
Owner: `DOT|CONTINUE`  
Category: `navigation`  
Status: `supported`  
Effect: `locate`  
Mutates: `cursor continue-state`  
Usage access: `CONTINUE USAGE`  

Purpose:

Continue a previous LOCATE search, or continue with an explicit FOR
  predicate, following active order when present.

Usage contract:

```text
CONTINUE
  CONTINUE USAGE
  CONTINUE FOR <expr>
```

Notes:

```text
CONTINUE with no arguments reuses the active LOCATE/CONTINUE predicate.
  CONTINUE FOR <expr> searches forward from the current record using the supplied predicate.
  CONTINUE follows active order when one is present; otherwise it scans physical order.
  CONTINUE requires an open table except for CONTINUE USAGE.
  CONTINUE mutates cursor/search state but does not mutate table data.
```

Related:

```text
LOCATE
  FIND
  SEEK
```

Source comments:

```text
src/cli/cmd_continue.cpp
CONTINUE
CONTINUE FOR <expr>
Continues search after the current record.
If an order is active, traversal follows active order.
Otherwise traversal is physical forward order.
```

---

### COPY

Source: `src/cli/cmd_copy.cpp`  
Owner: `DOT|COPY`  
Category: `file-table`  
Status: `supported`  
Effect: `copy-or-convert`  
Mutates: `filesystem`  
Usage access: `COPY USAGE`  

Purpose:

Copy the current DBF, convert the current table to a target DBF flavor, or
  copy a filesystem file.

Usage contract:

```text
COPY USAGE
  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]
  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]
  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]
  COPY FILE <SRC> TO <DST> [OVERWRITE]
```

Examples:

```text
COPY TO students_copy
  COPY TO students_x64 AS X64 VECTOR OVERWRITE
  COPY TO students_vfp AS VFP
  COPY TO students_backup WITH SIDECARS OVERWRITE
  COPY FILE source.txt TO tmp\source_copy.txt OVERWRITE
```

Notes:

```text
COPY USAGE prints usage and does not require an open table.
  COPY TO requires an open table.
  COPY FILE does not require an open table.
  WITH SIDECARS applies only to binary COPY TO.
  OVERWRITE is required when the destination already exists.
```

Related:

```text
USE
  EXPORT
  PACK
```

Source comments:

```text
src/cli/cmd_copy.cpp
```

---

### COPY

Source: `x64base/src/cli/cmd_copy.cpp`  
Owner: `DOT|COPY`  
Category: `file-table`  
Status: `supported`  
Effect: `copy-or-convert`  
Mutates: `filesystem`  
Usage access: `COPY USAGE`  

Purpose:

Copy the current DBF, convert the current table to a target DBF flavor, or
  copy a filesystem file.

Usage contract:

```text
COPY USAGE
  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]
  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]
  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]
  COPY FILE <SRC> TO <DST> [OVERWRITE]
```

Examples:

```text
COPY TO students_copy
  COPY TO students_x64 AS X64 VECTOR OVERWRITE
  COPY TO students_vfp AS VFP
  COPY TO students_backup WITH SIDECARS OVERWRITE
  COPY FILE source.txt TO tmp\source_copy.txt OVERWRITE
```

Notes:

```text
COPY USAGE prints usage and does not require an open table.
  COPY TO requires an open table.
  COPY FILE does not require an open table.
  WITH SIDECARS applies only to binary COPY TO.
  OVERWRITE is required when the destination already exists.
```

Related:

```text
USE
  EXPORT
  PACK
```

Source comments:

```text
src/cli/cmd_copy.cpp
```

---

### COUNT

Source: `src/cli/cmd_count.cpp`  
Owner: `DOT|COUNT`  
Category: `query`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor transient-relation-refresh-state`  
Usage access: `COUNT USAGE`  

Purpose:

Count records in the current logical rowset using selector-backed and
  predicate-backed scan paths, preserving cursor cohesion.

Usage contract:

```text
COUNT
  COUNT USAGE
  COUNT ALL
  COUNT FOR <expr>
  COUNT WHERE <expr>
  COUNT <expr>
  COUNT DELETED
  COUNT NOT DELETED
  COUNT !DELETED
```

Notes:

```text
COUNT with no arguments counts the current logical rowset.
  With no open table, COUNT preserves existing behavior and prints 0.
  Persistent SET FILTER is part of the logical rowset.
  COUNT FOR and COUNT WHERE normalize the predicate form before scanning.
  COUNT DELETED and COUNT NOT DELETED select by deletion state.
  COUNT preserves the active cursor where possible after scans.
  COUNT suppresses relation auto-refresh during full scans to avoid refresh thrash.
  COUNT is read-only for table data, though it may temporarily move and restore the cursor.
```

Related:

```text
LOCATE
  LIST
  FILTER
  SET FILTER
  GOTO
```

Source comments:

```text
COUNT <expr>          (implicit expression)
  COUNT DELETED
  COUNT NOT DELETED
  COUNT !DELETED
  COUNT ALL
Notes:
  • Uses cli::scan::collect_selected_recnos(...) for the common scan/selection path.
  • Keeps the active-tag simple equality fast path local to COUNT.
  • Preserves cursor cohesion: COUNT must not leave the work area at EOF/last rec.
  • Suppresses relations auto-refresh during full scans to prevent refresh thrash.
  • Persistent SET FILTER is part of the logical rowset.
    Therefore plain COUNT must NOT use raw recCount() when a persistent filter is active.
```

---

### COUNT

Source: `x64base/src/cli/cmd_count.cpp`  
Owner: `DOT|COUNT`  
Category: `query`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor transient-relation-refresh-state`  
Usage access: `COUNT USAGE`  

Purpose:

Count records in the current logical rowset using selector-backed and
  predicate-backed scan paths, preserving cursor cohesion.

Usage contract:

```text
COUNT
  COUNT USAGE
  COUNT ALL
  COUNT FOR <expr>
  COUNT WHERE <expr>
  COUNT <expr>
  COUNT DELETED
  COUNT NOT DELETED
  COUNT !DELETED
```

Notes:

```text
COUNT with no arguments counts the current logical rowset.
  With no open table, COUNT preserves existing behavior and prints 0.
  Persistent SET FILTER is part of the logical rowset.
  COUNT FOR and COUNT WHERE normalize the predicate form before scanning.
  COUNT DELETED and COUNT NOT DELETED select by deletion state.
  COUNT preserves the active cursor where possible after scans.
  COUNT suppresses relation auto-refresh during full scans to avoid refresh thrash.
  COUNT is read-only for table data, though it may temporarily move and restore the cursor.
```

Related:

```text
LOCATE
  LIST
  FILTER
  SET FILTER
  GOTO
```

Source comments:

```text
COUNT <expr>          (implicit expression)
  COUNT DELETED
  COUNT NOT DELETED
  COUNT !DELETED
  COUNT ALL
Notes:
  • Uses cli::scan::collect_selected_recnos(...) for the common scan/selection path.
  • Keeps the active-tag simple equality fast path local to COUNT.
  • Preserves cursor cohesion: COUNT must not leave the work area at EOF/last rec.
  • Suppresses relations auto-refresh during full scans to prevent refresh thrash.
  • Persistent SET FILTER is part of the logical rowset.
    Therefore plain COUNT must NOT use raw recCount() when a persistent filter is active.
```

---

### CREATE

Source: `src/cli/cmd_create.cpp`  
Owner: `DOT|CREATE`  
Category: `schema`  
Status: `supported`  
Effect: `create`  
Mutates: `filesystem session schema`  
Usage access: `CREATE USAGE`  

Purpose:

Create a DBF table in the configured DBF path slot using the requested
  xBase/DBF flavor and field specification.

Usage contract:

```text
CREATE USAGE
  CREATE <name> (<field> <type>[, ...])
  CREATE MSDOS <name> (<field> <type>[, ...])
  CREATE DBASE <name> (<field> <type>[, ...])
  CREATE FOX26 <name> (<field> <type>[, ...])
  CREATE FOXPRO <name> (<field> <type>[, ...])
  CREATE VFP <name> (<field> <type>[, ...])
  CREATE X64 <name> (<field> <type>[, ...])
```

Examples:

```text
CREATE students (sid N(6), lname C(20), fname C(15))
  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)
  CREATE VFP ledger (acct C(12), amount Y, posted D)
```

Notes:

```text
CREATE with no usable table/field specification shows usage and does not create a file.
  Relative table names resolve through the configured DBF path slot.
  CREATE clears active order state and closes the current area before writing the new table.
  After a successful write, CREATE opens the created table in the current area.
  If any field is M, CREATE attempts automatic memo attach after opening the table.
  X64 CREATE applies descriptor fallback/name policy for DBF descriptor safety.
  Long, duplicate, or descriptor-unsafe X64 field names may receive fallback tokens.
  X64 logical/authoritative metadata names are preserved when they fit the current x64 metadata limits.
  CREATE is a filesystem/schema mutation command; do not classify it as a read-only report command.
```

Related:

```text
USE
  STRUCT
  FIELDS
  WORKSPACE
  SETPATH
```

---

### CREATE

Source: `x64base/src/cli/cmd_create.cpp`  
Owner: `DOT|CREATE`  
Category: `schema`  
Status: `supported`  
Effect: `create`  
Mutates: `filesystem session schema`  
Usage access: `CREATE USAGE`  

Purpose:

Create a DBF table in the configured DBF path slot using the requested
  xBase/DBF flavor and field specification.

Usage contract:

```text
CREATE USAGE
  CREATE <name> (<field> <type>[, ...])
  CREATE MSDOS <name> (<field> <type>[, ...])
  CREATE DBASE <name> (<field> <type>[, ...])
  CREATE FOX26 <name> (<field> <type>[, ...])
  CREATE FOXPRO <name> (<field> <type>[, ...])
  CREATE VFP <name> (<field> <type>[, ...])
  CREATE X64 <name> (<field> <type>[, ...])
```

Examples:

```text
CREATE students (sid N(6), lname C(20), fname C(15))
  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)
  CREATE VFP ledger (acct C(12), amount Y, posted D)
```

Notes:

```text
CREATE with no usable table/field specification shows usage and does not create a file.
  Relative table names resolve through the configured DBF path slot.
  CREATE clears active order state and closes the current area before writing the new table.
  After a successful write, CREATE opens the created table in the current area.
  If any field is M, CREATE attempts automatic memo attach after opening the table.
  X64 CREATE applies descriptor fallback/name policy for DBF descriptor safety.
  Long, duplicate, or descriptor-unsafe X64 field names may receive fallback tokens.
  X64 logical/authoritative metadata names are preserved when they fit the current x64 metadata limits.
  CREATE is a filesystem/schema mutation command; do not classify it as a read-only report command.
```

Related:

```text
USE
  STRUCT
  FIELDS
  WORKSPACE
  SETPATH
```

---

### DBAREA

Source: `src/cli/cmd_dbarea.cpp`  
Owner: `DOT|DBAREA`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `DBAREA USAGE`  

Purpose:

Report the current DbArea/work-area state, including file identity,
  logical name, record counts, current record, active order/index status,
  and field structure.

Usage contract:

```text
DBAREA
  DBAREA USAGE
```

Notes:

```text
DBAREA with no arguments is a read-only report for the current work area.
  The current implementation receives an argument stream but does not consume it.
  Slot, ALL, and relation-context report forms are currently implemented by DBAREAS.
  Keep DBAREA focused as the canonical single-area report.
```

Related:

```text
DBAREAS
  WORKSPACE
  STATUS
  STRUCT
```

Source comments:

```text
engine access: compute area slot without changing DbArea API
```

---

### DBAREA

Source: `x64base/src/cli/cmd_dbarea.cpp`  
Owner: `DOT|DBAREA`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `DBAREA USAGE`  

Purpose:

Report the current DbArea/work-area state, including file identity,
  logical name, record counts, current record, active order/index status,
  and field structure.

Usage contract:

```text
DBAREA
  DBAREA USAGE
```

Notes:

```text
DBAREA with no arguments is a read-only report for the current work area.
  The current implementation receives an argument stream but does not consume it.
  Slot, ALL, and relation-context report forms are currently implemented by DBAREAS.
  Keep DBAREA focused as the canonical single-area report.
```

Related:

```text
DBAREAS
  WORKSPACE
  STATUS
  STRUCT
```

Source comments:

```text
engine access: compute area slot without changing DbArea API
```

---

### DBAREAS

Source: `src/cli/cmd_dbareas.cpp`  
Owner: `DOT|DBAREAS`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `DBAREAS USAGE`  

Purpose:

Report current, selected, or all open DbArea/work-area state.

Usage contract:

```text
DBAREAS
  DBAREAS USAGE
  DBAREAS <n>
  DBAREAS ALL
  DBAREAS REL
```

Notes:

```text
DBAREAS with no arguments reports the current area by delegating to DBAREA.
  DBAREAS <n> reports slot n when that slot is open.
  DBAREAS ALL reports all open slots using filename() as the open-area truth.
  DBAREAS REL reports the current area and appends relation summary/tree context.
  DBAREAS is read-only; it reports session/work-area state and does not mutate table data.
```

Related:

```text
DBAREA
  WORKSPACE
  REL
  STATUS
```

Source comments:

```text
src/cli/cmd_dbareas.cpp
DBAREAS - Convenience wrapper around DBAREA.
Key rule (matches cmd_schemas.cpp): filename() is the source of truth for
whether a slot is "open". DbArea::isOpen() is not reliable during refactors.
```

---

### DBAREAS

Source: `x64base/src/cli/cmd_dbareas.cpp`  
Owner: `DOT|DBAREAS`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `DBAREAS USAGE`  

Purpose:

Report current, selected, or all open DbArea/work-area state.

Usage contract:

```text
DBAREAS
  DBAREAS USAGE
  DBAREAS <n>
  DBAREAS ALL
  DBAREAS REL
```

Notes:

```text
DBAREAS with no arguments reports the current area by delegating to DBAREA.
  DBAREAS <n> reports slot n when that slot is open.
  DBAREAS ALL reports all open slots using filename() as the open-area truth.
  DBAREAS REL reports the current area and appends relation summary/tree context.
  DBAREAS is read-only; it reports session/work-area state and does not mutate table data.
```

Related:

```text
DBAREA
  WORKSPACE
  REL
  STATUS
```

Source comments:

```text
src/cli/cmd_dbareas.cpp
DBAREAS - Convenience wrapper around DBAREA.
Key rule (matches cmd_schemas.cpp): filename() is the source of truth for
whether a slot is "open". DbArea::isOpen() is not reliable during refactors.
```

---

### DDL

Source: `src/cli/cmd_ddl.cpp`  
Owner: `DOT|DDL`  
Category: `schema`  
Status: `supported`  
Effect: `mixed`  
Mutates: `filesystem schema dbf sidecar`  
Usage access: `DDL USAGE`  

Purpose:

Fetch schema files, validate schema files, and create DBF tables from
  JSON schema definitions with optional seed rows and sidecar metadata.

Usage contract:

```text
DDL USAGE
  DDL FETCH <url> TO <file>
  DDL FETCH <url> TO <file> OVERWRITE
  DDL VALIDATE <schema.json> USING <validator.json>
  DDL CREATE DBF <out.dbf> FROM <schema.json>
  DDL CREATE DBF <out.dbf> FROM <schema.json> OVERWRITE
  DDL CREATE DBF <out.dbf> FROM <schema.json> SEED CSV <path.csv>
  DDL CREATE DBF <out.dbf> FROM <schema.json> SEED BLANK <n>
  DDL CREATE DBF <out.dbf> FROM <schema.json> REJECTS <rejects.csv>
  DDL CREATE DBF <out.dbf> FROM <schema.json> EMIT SIDECARS
```

Notes:

```text
DDL with no arguments shows usage.
  FETCH writes a schema-side file and refuses overwrite unless OVERWRITE is supplied.
  VALIDATE currently checks that both schema and validator inputs exist and reports OK.
  CREATE DBF writes a DBF file from schema field definitions.
  CREATE DBF refuses existing output unless OVERWRITE is supplied.
  Relative schema inputs resolve under SCHEMAS.
  Relative FETCH outputs resolve under SCHEMAS.
  Relative CREATE DBF outputs resolve under TMP.
  EMIT SIDECARS writes companion schema, load, and index metadata files.
  SEED CSV is recognized but not yet implemented in this drop-in.
```

Related:

```text
CREATE
  WORKSPACE
  USE
  STRUCT
  FIELDMGR
```

---

### DDL

Source: `x64base/src/cli/cmd_ddl.cpp`  
Owner: `DOT|DDL`  
Category: `schema`  
Status: `supported`  
Effect: `mixed`  
Mutates: `filesystem schema dbf sidecar`  
Usage access: `DDL USAGE`  

Purpose:

Fetch schema files, validate schema files, and create DBF tables from
  JSON schema definitions with optional seed rows and sidecar metadata.

Usage contract:

```text
DDL USAGE
  DDL FETCH <url> TO <file>
  DDL FETCH <url> TO <file> OVERWRITE
  DDL VALIDATE <schema.json> USING <validator.json>
  DDL CREATE DBF <out.dbf> FROM <schema.json>
  DDL CREATE DBF <out.dbf> FROM <schema.json> OVERWRITE
  DDL CREATE DBF <out.dbf> FROM <schema.json> SEED CSV <path.csv>
  DDL CREATE DBF <out.dbf> FROM <schema.json> SEED BLANK <n>
  DDL CREATE DBF <out.dbf> FROM <schema.json> REJECTS <rejects.csv>
  DDL CREATE DBF <out.dbf> FROM <schema.json> EMIT SIDECARS
```

Notes:

```text
DDL with no arguments shows usage.
  FETCH writes a schema-side file and refuses overwrite unless OVERWRITE is supplied.
  VALIDATE currently checks that both schema and validator inputs exist and reports OK.
  CREATE DBF writes a DBF file from schema field definitions.
  CREATE DBF refuses existing output unless OVERWRITE is supplied.
  Relative schema inputs resolve under SCHEMAS.
  Relative FETCH outputs resolve under SCHEMAS.
  Relative CREATE DBF outputs resolve under TMP.
  EMIT SIDECARS writes companion schema, load, and index metadata files.
  SEED CSV is recognized but not yet implemented in this drop-in.
```

Related:

```text
CREATE
  WORKSPACE
  USE
  STRUCT
  FIELDMGR
```

---

### DELETE

Source: `src/cli/cmd_delete.cpp`  
Owner: `DOT|DELETE`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data deletion-flag index stale-state cursor`  
Usage access: `DELETE USAGE`  

Purpose:

Mark the current record or selected records deleted, honoring filters and
  applying index delete snapshots in direct-write mode.

Usage contract:

```text
DELETE USAGE
  DELETE
  DELETE ALL
  DELETE REST
  DELETE NEXT <n>
  DELETE FOR <field> <op> <value>
```

Notes:

```text
DELETE with no arguments deletes the current record.
  DELETE requires an open table except for DELETE USAGE.
  DELETE honors active SET FILTER in ALL, REST, NEXT, and FOR scans.
  DELETE snapshots target recnos before mutating to avoid active-index traversal mutation.
  Direct-write mode captures index keys before delete and applies index delete snapshots after delete.
  Buffered table mode leaves rebuild or final application to COMMIT.
  DELETE marks fields stale best-effort and refreshes current navigation best-effort.
  If index snapshot or apply fails, data delete may still succeed and a rebuild warning is emitted.
```

Related:

```text
RECALL
  PACK
  TABLE
  COMMIT
  COUNT
  SET FILTER
```

Source comments:

```text
- DELETE honors active SET FILTER in ALL / REST / NEXT / FOR scans.
- No-arg DELETE (current record) remains explicit on the current row.
Traversal behavior:
- DELETE snapshots target recnos first, then deletes by recno.
- This avoids mutating an active index while simultaneously iterating it.
- ALL / FOR use ordered snapshot traversal when an order is active.
- REST / NEXT preserve current navigation semantics through the shared selector.
Stabilization notes:
- If index snapshot/apply fails while an order/index backend is active,
  DELETE still succeeds at the data layer, but a warning is emitted that the
  active index may now require rebuild.
- After a successful delete, current navigation is refreshed best-effort.
```

---

### DELETE

Source: `x64base/src/cli/cmd_delete.cpp`  
Owner: `DOT|DELETE`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data deletion-flag index stale-state cursor`  
Usage access: `DELETE USAGE`  

Purpose:

Mark the current record or selected records deleted, honoring filters and
  applying index delete snapshots in direct-write mode.

Usage contract:

```text
DELETE USAGE
  DELETE
  DELETE ALL
  DELETE REST
  DELETE NEXT <n>
  DELETE FOR <field> <op> <value>
```

Notes:

```text
DELETE with no arguments deletes the current record.
  DELETE requires an open table except for DELETE USAGE.
  DELETE honors active SET FILTER in ALL, REST, NEXT, and FOR scans.
  DELETE snapshots target recnos before mutating to avoid active-index traversal mutation.
  Direct-write mode captures index keys before delete and applies index delete snapshots after delete.
  Buffered table mode leaves rebuild or final application to COMMIT.
  DELETE marks fields stale best-effort and refreshes current navigation best-effort.
  If index snapshot or apply fails, data delete may still succeed and a rebuild warning is emitted.
```

Related:

```text
RECALL
  PACK
  TABLE
  COMMIT
  COUNT
  SET FILTER
```

Source comments:

```text
- DELETE honors active SET FILTER in ALL / REST / NEXT / FOR scans.
- No-arg DELETE (current record) remains explicit on the current row.
Traversal behavior:
- DELETE snapshots target recnos first, then deletes by recno.
- This avoids mutating an active index while simultaneously iterating it.
- ALL / FOR use ordered snapshot traversal when an order is active.
- REST / NEXT preserve current navigation semantics through the shared selector.
Stabilization notes:
- If index snapshot/apply fails while an order/index backend is active,
  DELETE still succeeds at the data layer, but a warning is emitted that the
  active index may now require rebuild.
- After a successful delete, current navigation is refreshed best-effort.
```

---

### DESCEND

Source: `src/cli/cmd_descend.cpp`  
Owner: `DOT|DESCEND`  
Category: `index`  
Status: `supported`  
Effect: `configure`  
Mutates: `order-state`  
Usage access: `DESCEND USAGE`  

Purpose:

Set the active order/tag direction to descending for the current work area.

Usage contract:

```text
DESCEND
  DESCEND USAGE
```

Notes:

```text
DESCEND requires an active order except for DESCEND USAGE.
  DESCEND with no arguments mutates order direction to descending.
  DESCEND does not mutate table records or rebuild indexes.
```

Related:

```text
ASCEND
  SET ORDER
  ORDER
```

---

### DESCEND

Source: `x64base/src/cli/cmd_descend.cpp`  
Owner: `DOT|DESCEND`  
Category: `index`  
Status: `supported`  
Effect: `configure`  
Mutates: `order-state`  
Usage access: `DESCEND USAGE`  

Purpose:

Set the active order/tag direction to descending for the current work area.

Usage contract:

```text
DESCEND
  DESCEND USAGE
```

Notes:

```text
DESCEND requires an active order except for DESCEND USAGE.
  DESCEND with no arguments mutates order direction to descending.
  DESCEND does not mutate table records or rebuild indexes.
```

Related:

```text
ASCEND
  SET ORDER
  ORDER
```

---

### DIR

Source: `src/cli/cmd_dir.cpp`  
Owner: `DOT|DIR`  
Category: `filesystem`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `DIR USAGE`  

Purpose:

List a directory or show a single file entry through DotTalk++ path
  resolution.

Usage contract:

```text
DIR
  DIR USAGE
  DIR <path>
  DIR <slot>
  DIR <slot>:<path>
```

Notes:

```text
DIR with no arguments lists the configured DBF path.
  DIR <path> lists a directory or prints a single file entry.
  Slot-style paths resolve through the common path resolver.
  DIR is read-only and does not mutate table data or filesystem contents.
```

Related:

```text
SETPATH
  SHOWINI
```

Source comments:

```text
src/cli/cmd_dir.cpp
```

---

### DIR

Source: `x64base/src/cli/cmd_dir.cpp`  
Owner: `DOT|DIR`  
Category: `filesystem`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `DIR USAGE`  

Purpose:

List a directory or show a single file entry through DotTalk++ path
  resolution.

Usage contract:

```text
DIR
  DIR USAGE
  DIR <path>
  DIR <slot>
  DIR <slot>:<path>
```

Notes:

```text
DIR with no arguments lists the configured DBF path.
  DIR <path> lists a directory or prints a single file entry.
  Slot-style paths resolve through the common path resolver.
  DIR is read-only and does not mutate table data or filesystem contents.
```

Related:

```text
SETPATH
  SHOWINI
```

Source comments:

```text
src/cli/cmd_dir.cpp
```

---

### DISPLAY

Source: `src/cli/cmd_display.cpp`  
Owner: `DOT|DISPLAY`  
Category: `record`  
Status: `supported`  
Effect: `mixed`  
Mutates: `cursor`  
Usage access: `DISPLAY USAGE`  

Purpose:

Display the current record or display a requested record by record number.

Usage contract:

```text
DISPLAY
  DISPLAY USAGE
  DISPLAY <recno>
```

Notes:

```text
DISPLAY with no arguments displays the current record.
  DISPLAY <recno> navigates to that record number, then displays it.
  Memo payload display values are resolved through the memo display layer.
  DISPLAY USAGE prints usage before open-table checks or cursor movement.
```

Related:

```text
LIST
  BROWSE
  RECNO
```

---

### DISPLAY

Source: `x64base/src/cli/cmd_display.cpp`  
Owner: `DOT|DISPLAY`  
Category: `record`  
Status: `supported`  
Effect: `mixed`  
Mutates: `cursor`  
Usage access: `DISPLAY USAGE`  

Purpose:

Display the current record or display a requested record by record number.

Usage contract:

```text
DISPLAY
  DISPLAY USAGE
  DISPLAY <recno>
```

Notes:

```text
DISPLAY with no arguments displays the current record.
  DISPLAY <recno> navigates to that record number, then displays it.
  Memo payload display values are resolved through the memo display layer.
  DISPLAY USAGE prints usage before open-table checks or cursor movement.
```

Related:

```text
LIST
  BROWSE
  RECNO
```

---

### DOTHELP

Source: `src/cli/cmd_dothelp.cpp`  
Owner: `DOT|DOTHELP`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `DOTHELP USAGE`  

Purpose:

Show project-native DotTalk++ reference entries from the dotref catalog.

Usage contract:

```text
DOTHELP
  DOTHELP USAGE
  DOTHELP <term>
  HELP /DOT <term>
```

Notes:

```text
DOTHELP with no arguments lists project-native commands and subsystems.
  DOTHELP <term> prints a matching dotref entry or search matches.
  DOTHELP USAGE prints usage only.
  HELP /DOT <term> is the related HELP-surface access path.
  DOTHELP is read-only.
```

Related:

```text
HELP
  FOXHELP
  CMDHELP
```

---

### DOTHELP

Source: `x64base/src/cli/cmd_dothelp.cpp`  
Owner: `DOT|DOTHELP`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `DOTHELP USAGE`  

Purpose:

Show project-native DotTalk++ reference entries from the dotref catalog.

Usage contract:

```text
DOTHELP
  DOTHELP USAGE
  DOTHELP <term>
  HELP /DOT <term>
```

Notes:

```text
DOTHELP with no arguments lists project-native commands and subsystems.
  DOTHELP <term> prints a matching dotref entry or search matches.
  DOTHELP USAGE prints usage only.
  HELP /DOT <term> is the related HELP-surface access path.
  DOTHELP is read-only.
```

Related:

```text
HELP
  FOXHELP
  CMDHELP
```

---

### DOTSCRIPT

Source: `src/cli/cmd_dotscript.cpp`  
Owner: `DOT|DOTSCRIPT`  
Category: `script`  
Status: `supported`  
Effect: `execute`  
Mutates: `delegates script commands session`  
Usage access: `DOTSCRIPT USAGE`  

Purpose:

Run a DotTalk++ script file, resolving bare names through script/test
  search locations, supporting @file notation, TRACE mode, and one-level
  subscript nesting.

Usage contract:

```text
DOTSCRIPT USAGE
  DOTSCRIPT <file>
  DOTSCRIPT @<file>
  DOTSCRIPT TRACE
  DOTSCRIPT TRACE ON
  DOTSCRIPT TRACE OFF
  DOTSCRIPT TRACE <file>
  DOTSCRIPT TRACE @<file>
  DOTSCRIPT TRACE ON <file>
  DOTSCRIPT TRACE OFF <file>
  DOTSCRIPT TRACE ON @<file>
  DOTSCRIPT TRACE OFF @<file>
```

Notes:

```text
DOTSCRIPT with no arguments shows usage.
  DOTSCRIPT reads an external script file and executes each nonblank,
  noncomment line through the shell command executor.
  Script comments/blank lines are ignored when they begin with *, //, &&, or ; after trimming.
  Bare script names try the typed name, .dts extension, scripts/, and tests/ candidates.
  @file notation is accepted and unquoted before path resolution.
  TRACE without a file reports the current trace state and usage.
  TRACE ON/OFF changes global DOTSCRIPT trace state.
  TRACE <file> runs a single script with trace enabled without changing global trace state.
  Nesting is limited to main script plus one subscript.
  DOTSCRIPT itself delegates side effects to the commands inside the script; it is not read-only.
```

Related:

```text
TEST
  CMDHELP
  WORKSPACE
  CREATE
  USE
```

Source comments:

```text
src/commands/cmd_dotscript.cpp
DOTSCRIPT runner with TRACE banner + scripts/tests resolver + @file support + one-level subscript limit.
```

---

### DOTSCRIPT

Source: `x64base/src/cli/cmd_dotscript.cpp`  
Owner: `DOT|DOTSCRIPT`  
Category: `script`  
Status: `supported`  
Effect: `execute`  
Mutates: `delegates script commands session`  
Usage access: `DOTSCRIPT USAGE`  

Purpose:

Run a DotTalk++ script file, resolving bare names through script/test
  search locations, supporting @file notation, TRACE mode, and one-level
  subscript nesting.

Usage contract:

```text
DOTSCRIPT USAGE
  DOTSCRIPT <file>
  DOTSCRIPT @<file>
  DOTSCRIPT TRACE
  DOTSCRIPT TRACE ON
  DOTSCRIPT TRACE OFF
  DOTSCRIPT TRACE <file>
  DOTSCRIPT TRACE @<file>
  DOTSCRIPT TRACE ON <file>
  DOTSCRIPT TRACE OFF <file>
  DOTSCRIPT TRACE ON @<file>
  DOTSCRIPT TRACE OFF @<file>
```

Notes:

```text
DOTSCRIPT with no arguments shows usage.
  DOTSCRIPT reads an external script file and executes each nonblank,
  noncomment line through the shell command executor.
  Script comments/blank lines are ignored when they begin with *, //, &&, or ; after trimming.
  Bare script names try the typed name, .dts extension, scripts/, and tests/ candidates.
  @file notation is accepted and unquoted before path resolution.
  TRACE without a file reports the current trace state and usage.
  TRACE ON/OFF changes global DOTSCRIPT trace state.
  TRACE <file> runs a single script with trace enabled without changing global trace state.
  Nesting is limited to main script plus one subscript.
  DOTSCRIPT itself delegates side effects to the commands inside the script; it is not read-only.
```

Related:

```text
TEST
  CMDHELP
  WORKSPACE
  CREATE
  USE
```

Source comments:

```text
src/commands/cmd_dotscript.cpp
DOTSCRIPT runner with TRACE banner + scripts/tests resolver + @file support + one-level subscript limit.
```

---

### DRAWIO

Source: `src/cli/cmd_drawio.cpp`  
Owner: `DOT|DRAWIO`  
Category: `integration`  
Status: `supported`  
Effect: `launch`  
Mutates: `external-browser`  
Usage access: `DRAWIO USAGE`  

Purpose:

Launch diagrams.net, or list/open draw.io files from configured diagram paths.

Usage contract:

```text
DRAWIO USAGE
  DRAWIO
  DRAWIO PATHS
  DRAWIO LIST
  DRAWIO LIST SYSTEM
  DRAWIO LIST USER
  DRAWIO LIST ALL
  DRAWIO OPEN
  DRAWIO OPEN <url-or-path>
  DRAWIO OPEN SYSTEM <n|filename>
  DRAWIO OPEN USER <n|filename>
  DRAWIO OPEN ALL <n|filename>
```

Notes:

```text
DRAWIO with no arguments launches the default diagrams.net URL.
  DRAWIO OPEN with no target also launches the default diagrams.net URL.
  DRAWIO LIST defaults to SYSTEM.
  SYSTEM diagrams come from SETPATH SYSTEM_DIAGRAMS / DIAGRAMS.
  USER diagrams come from SETPATH USER_DIAGRAMS.
  DRAWIO does not mutate table data or workspace state.
```

Related:

```text
HELP
  EXPORT
  SETPATH
```

Source comments:

```text
src/cli/cmd_drawio.cpp
DRAWIO command
Launches diagrams.net / draw.io and can list/open project diagram files.
Usage:
  DRAWIO
  DRAWIO PATHS
  DRAWIO LIST [SYSTEM|USER|ALL]
  DRAWIO OPEN
  DRAWIO OPEN <url-or-path>
  DRAWIO OPEN [SYSTEM|USER|ALL] <n|filename>
```

---

### DRAWIO

Source: `x64base/src/cli/cmd_drawio.cpp`  
Owner: `DOT|DRAWIO`  
Category: `integration`  
Status: `supported`  
Effect: `launch`  
Mutates: `external-browser`  
Usage access: `DRAWIO USAGE`  

Purpose:

Launch diagrams.net, or list/open draw.io files from configured diagram paths.

Usage contract:

```text
DRAWIO USAGE
  DRAWIO
  DRAWIO PATHS
  DRAWIO LIST
  DRAWIO LIST SYSTEM
  DRAWIO LIST USER
  DRAWIO LIST ALL
  DRAWIO OPEN
  DRAWIO OPEN <url-or-path>
  DRAWIO OPEN SYSTEM <n|filename>
  DRAWIO OPEN USER <n|filename>
  DRAWIO OPEN ALL <n|filename>
```

Notes:

```text
DRAWIO with no arguments launches the default diagrams.net URL.
  DRAWIO OPEN with no target also launches the default diagrams.net URL.
  DRAWIO LIST defaults to SYSTEM.
  SYSTEM diagrams come from SETPATH SYSTEM_DIAGRAMS / DIAGRAMS.
  USER diagrams come from SETPATH USER_DIAGRAMS.
  DRAWIO does not mutate table data or workspace state.
```

Related:

```text
HELP
  EXPORT
  SETPATH
```

Source comments:

```text
src/cli/cmd_drawio.cpp
DRAWIO command
Launches diagrams.net / draw.io and can list/open project diagram files.
Usage:
  DRAWIO
  DRAWIO PATHS
  DRAWIO LIST [SYSTEM|USER|ALL]
  DRAWIO OPEN
  DRAWIO OPEN <url-or-path>
  DRAWIO OPEN [SYSTEM|USER|ALL] <n|filename>
```

---

### DUMP

Source: `src/cli/cmd_dump.cpp`  
Owner: `DOT|DUMP`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `DUMP USAGE`  

Purpose:

Dump every record from the current work area in legacy pipe-delimited form.

Usage contract:

```text
DUMP
  DUMP USAGE
```

Notes:

```text
DUMP requires an open table except for DUMP USAGE.
  DUMP operates only on the current work area.
  DUMP does not resolve paths and does not open files.
  Deleted records are prefixed with an asterisk marker.
  DUMP iterates by record number and reads each record.
  DUMP is read-only for table data but moves the current cursor during output.
```

Related:

```text
LIST
  DISPLAY
  BROWSE
  COUNT
```

Source comments:

```text
src/cli/cmd_dump.cpp
DotTalk++ — DUMP
Legacy, path-blind record dumper.
Operates ONLY on the current work area.
No path resolution, no file opens, no side effects.
```

---

### DUMP

Source: `x64base/src/cli/cmd_dump.cpp`  
Owner: `DOT|DUMP`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `DUMP USAGE`  

Purpose:

Dump every record from the current work area in legacy pipe-delimited form.

Usage contract:

```text
DUMP
  DUMP USAGE
```

Notes:

```text
DUMP requires an open table except for DUMP USAGE.
  DUMP operates only on the current work area.
  DUMP does not resolve paths and does not open files.
  Deleted records are prefixed with an asterisk marker.
  DUMP iterates by record number and reads each record.
  DUMP is read-only for table data but moves the current cursor during output.
```

Related:

```text
LIST
  DISPLAY
  BROWSE
  COUNT
```

Source comments:

```text
src/cli/cmd_dump.cpp
DotTalk++ — DUMP
Legacy, path-blind record dumper.
Operates ONLY on the current work area.
No path resolution, no file opens, no side effects.
```

---

### ECHO

Source: `src/cli/cmd_echo.cpp`  
Owner: `DOT|ECHO`  
Category: `output`  
Status: `supported`  
Effect: `output`  
Mutates: `output-stream`  
Usage access: `ECHO USAGE`  

Purpose:

Print or comment-echo text through the output router depending on SET ECHO state.

Usage contract:

```text
ECHO
  ECHO USAGE
  ECHO <text>
```

Notes:

```text
ECHO with no arguments preserves existing behavior and emits an empty comment/output line.
  ECHO <text> is comment-style console output when router echo is OFF.
  ECHO <text> routes normally when router echo is ON.
  ECHO ON is not the toggle command; use SET ECHO ON or SET ECHO OFF.
  ECHO USAGE prints usage directly and does not route through echo mode.
```

Related:

```text
SET ECHO
  PRINT
  ALTERNATE
```

Source comments:

```text
src/cli/cmd_echo.cpp
```

---

### ECHO

Source: `x64base/src/cli/cmd_echo.cpp`  
Owner: `DOT|ECHO`  
Category: `output`  
Status: `supported`  
Effect: `output`  
Mutates: `output-stream`  
Usage access: `ECHO USAGE`  

Purpose:

Print or comment-echo text through the output router depending on SET ECHO state.

Usage contract:

```text
ECHO
  ECHO USAGE
  ECHO <text>
```

Notes:

```text
ECHO with no arguments preserves existing behavior and emits an empty comment/output line.
  ECHO <text> is comment-style console output when router echo is OFF.
  ECHO <text> routes normally when router echo is ON.
  ECHO ON is not the toggle command; use SET ECHO ON or SET ECHO OFF.
  ECHO USAGE prints usage directly and does not route through echo mode.
```

Related:

```text
SET ECHO
  PRINT
  ALTERNATE
```

Source comments:

```text
src/cli/cmd_echo.cpp
```

---

### EDIT

Source: `src/edu/edu_edit.cpp`  
Owner: `EDU|EDIT`  
Category: `utility-editor`  
Status: `supported`  
Effect: `launch-editor`  
Mutates: `filesystem-through-editor`  
Usage access: `EDIT USAGE`  

Purpose:

Launch the configured external editor for a file path.

Usage contract:

```text
EDIT USAGE
  EDIT <file>
```

Examples:

```text
EDIT notes.txt
  EDIT scripts\demo.dts
```

Notes:

```text
EDIT USAGE/HELP/? returns before launching an external editor.
  EDIT may create or modify files through the configured editor.
```

Source comments:

```text
Custom,
      Off
  };
  struct EditorSettings {
      EditorMode mode = EditorMode::Default;
      std::string command;
  };
  struct Settings {
      ...
      EditorSettings editor;
      ...
  };
```

---

### EDIT

Source: `x64base/src/edu/edu_edit.cpp`  
Owner: `EDU|EDIT`  
Category: `utility-editor`  
Status: `supported`  
Effect: `launch-editor`  
Mutates: `filesystem-through-editor`  
Usage access: `EDIT USAGE`  

Purpose:

Launch the configured external editor for a file path.

Usage contract:

```text
EDIT USAGE
  EDIT <file>
```

Examples:

```text
EDIT notes.txt
  EDIT scripts\demo.dts
```

Notes:

```text
EDIT USAGE/HELP/? returns before launching an external editor.
  EDIT may create or modify files through the configured editor.
```

Source comments:

```text
Custom,
      Off
  };
  struct EditorSettings {
      EditorMode mode = EditorMode::Default;
      std::string command;
  };
  struct Settings {
      ...
      EditorSettings editor;
      ...
  };
```

---

### EDU_BIBLETALK / BIBLETALK

Source: `src/edu/edu_bibletalk.cpp`  
Owner: `EDU|BIBLETALK`  
Category: `education-database-demo`  
Status: `supported`  
Effect: `sqlite-demo-query`  
Mutates: `sqlite-connection-state`  
Usage access: `EDU_BIBLETALK USAGE; BIBLETALK USAGE`  

Purpose:

Educational BibleTalk/KJV SQLite database wrapper for status, schema,
  table inspection, verse lookup, search, and random scripture output.

Usage contract:

```text
EDU_BIBLETALK USAGE
  EDU_BIBLETALK HELP
  EDU_BIBLETALK STATUS
  EDU_BIBLETALK BIBLE
  EDU_BIBLETALK BIBLECHECK
  EDU_BIBLETALK BOOKS
  EDU_BIBLETALK VERSE <ref>
  EDU_BIBLETALK QUOTE
  EDU_BIBLETALK SEARCH <phrase>
  EDU_BIBLETALK LIST <table> [limit]
  EDU_BIBLETALK COLUMNS <table>
  EDU_BIBLETALK TABLES
  EDU_BIBLETALK SCHEMA [table]
  EDU_BIBLETALK EXEC <sql...>
  EDU_BIBLETALK SELECT <sql...>
  EDU_BIBLETALK CLOSE
```

Examples:

```text
EDU_BIBLETALK USAGE
  EDU_BIBLETALK BIBLE
  EDU_BIBLETALK VERSE John 3:16
  EDU_BIBLETALK SEARCH faith
  BIBLETALK QUOTE
```

Notes:

```text
USAGE/HELP/? returns before SQLite database work.
  No-arg behavior remains status plus brief usage.
  BIBLETALK is a compatibility alias for EDU_BIBLETALK.
```

Source comments:

```text
EDU_BIBLETALK LIST <table> [limit]    -> quick table preview
  EDU_BIBLETALK COLUMNS <table>         -> show table columns
  EDU_BIBLETALK CLOSE                   -> close
  EDU_BIBLETALK TABLES                  -> list user tables/views
  EDU_BIBLETALK SCHEMA [name]           -> show schema rows; optional table/view name
  EDU_BIBLETALK EXEC <sql...>           -> execute non-SELECT SQL
  EDU_BIBLETALK SELECT <sql...>         -> run a SELECT and print rows
Notes:
  - Uses dottalk::sqlite::* from sqlite/sqlite_adapter.hpp.
  - Independent of DBF open/order state.
  - SQLite here is an external SQL/RDBMS backend surface, not native DbArea storage.
  - SELECT output is capped (MAX_SELECT_ROWS) to keep CLI responsive.
```

---

### EDU_BIBLETALK / BIBLETALK

Source: `x64base/src/edu/edu_bibletalk.cpp`  
Owner: `EDU|BIBLETALK`  
Category: `education-database-demo`  
Status: `supported`  
Effect: `sqlite-demo-query`  
Mutates: `sqlite-connection-state`  
Usage access: `EDU_BIBLETALK USAGE; BIBLETALK USAGE`  

Purpose:

Educational BibleTalk/KJV SQLite database wrapper for status, schema,
  table inspection, verse lookup, search, and random scripture output.

Usage contract:

```text
EDU_BIBLETALK USAGE
  EDU_BIBLETALK HELP
  EDU_BIBLETALK STATUS
  EDU_BIBLETALK BIBLE
  EDU_BIBLETALK BIBLECHECK
  EDU_BIBLETALK BOOKS
  EDU_BIBLETALK VERSE <ref>
  EDU_BIBLETALK QUOTE
  EDU_BIBLETALK SEARCH <phrase>
  EDU_BIBLETALK LIST <table> [limit]
  EDU_BIBLETALK COLUMNS <table>
  EDU_BIBLETALK TABLES
  EDU_BIBLETALK SCHEMA [table]
  EDU_BIBLETALK EXEC <sql...>
  EDU_BIBLETALK SELECT <sql...>
  EDU_BIBLETALK CLOSE
```

Examples:

```text
EDU_BIBLETALK USAGE
  EDU_BIBLETALK BIBLE
  EDU_BIBLETALK VERSE John 3:16
  EDU_BIBLETALK SEARCH faith
  BIBLETALK QUOTE
```

Notes:

```text
USAGE/HELP/? returns before SQLite database work.
  No-arg behavior remains status plus brief usage.
  BIBLETALK is a compatibility alias for EDU_BIBLETALK.
```

Source comments:

```text
EDU_BIBLETALK LIST <table> [limit]    -> quick table preview
  EDU_BIBLETALK COLUMNS <table>         -> show table columns
  EDU_BIBLETALK CLOSE                   -> close
  EDU_BIBLETALK TABLES                  -> list user tables/views
  EDU_BIBLETALK SCHEMA [name]           -> show schema rows; optional table/view name
  EDU_BIBLETALK EXEC <sql...>           -> execute non-SELECT SQL
  EDU_BIBLETALK SELECT <sql...>         -> run a SELECT and print rows
Notes:
  - Uses dottalk::sqlite::* from sqlite/sqlite_adapter.hpp.
  - Independent of DBF open/order state.
  - SQLite here is an external SQL/RDBMS backend surface, not native DbArea storage.
  - SELECT output is capped (MAX_SELECT_ROWS) to keep CLI responsive.
```

---

### ELSE

Source: `src/cli/cmd_else.cpp`  
Owner: `DOT|ELSE_IMPL`  
Category: `script-flow-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by IF/ELSE/ENDIF handler`  

Purpose:

Empty translation-unit shim for ELSE command ownership.

Usage contract:

```text
ELSE usage is owned by the IF/ELSE/ENDIF command implementation.
  This file intentionally exports no command handler.
```

Notes:

```text
This file exists only because ELSE has a cmd_*.cpp translation unit in the
  build tree. Do not add a second ELSE implementation here.
```

---

### ELSE

Source: `x64base/src/cli/cmd_else.cpp`  
Owner: `DOT|ELSE_IMPL`  
Category: `script-flow-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by IF/ELSE/ENDIF handler`  

Purpose:

Empty translation-unit shim for ELSE command ownership.

Usage contract:

```text
ELSE usage is owned by the IF/ELSE/ENDIF command implementation.
  This file intentionally exports no command handler.
```

Notes:

```text
This file exists only because ELSE has a cmd_*.cpp translation unit in the
  build tree. Do not add a second ELSE implementation here.
```

---

### ENDIF

Source: `src/cli/cmd_if.cpp`  
Owner: `DOT|ENDIF`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDIF USAGE`  

Purpose:

Close an IF control block.

Usage contract:

```text
ENDIF
```

Notes:

```text
Syntax command paired with IF and ELSE. It does not mutate table data by itself.
```

Related:

```text
IF, ELSE, CASE
```

Source comments:

```text
Already suppressed by outer IF -> do not evaluate.
```

---

### ENDIF

Source: `x64base/src/cli/cmd_if.cpp`  
Owner: `DOT|ENDIF`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDIF USAGE`  

Purpose:

Close an IF control block.

Usage contract:

```text
ENDIF
```

Notes:

```text
Syntax command paired with IF and ELSE. It does not mutate table data by itself.
```

Related:

```text
IF, ELSE, CASE
```

Source comments:

```text
Already suppressed by outer IF -> do not evaluate.
```

---

### ENDLOOP

Source: `src/cli/cmd_loop.cpp`  
Owner: `DOT|ENDLOOP`  
Category: `script`  
Status: `supported`  
Effect: `execute`  
Mutates: `loop-buffer loop-state delegates-command-effects`  
Usage access: `ENDLOOP USAGE`  

Purpose:

End the active LOOP block and replay buffered commands through the shell
  executor.

Usage contract:

```text
ENDLOOP
  ENDLOOP USAGE
```

Notes:

```text
ENDLOOP with no arguments executes the active LOOP buffer.
  ENDLOOP requires an active LOOP block except for ENDLOOP USAGE.
  ENDLOOP clears active loop state before replay.
  ENDLOOP replays buffered commands through the registered loop executor.
  ENDLOOP reports when no LOOP is active.
  ENDLOOP may indirectly mutate data, session state, or files depending on buffered commands.
```

Related:

```text
LOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL
```

Source comments:

```text
risk:
  mutates_loop_state: yes
  buffers_commands: yes
  executes_commands: through ENDLOOP
  mutates_table_data: depends on buffered commands
  max_iterations: clamped
related:
  ENDLOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL
```

---

### ENDLOOP

Source: `x64base/src/cli/cmd_loop.cpp`  
Owner: `DOT|ENDLOOP`  
Category: `script`  
Status: `supported`  
Effect: `execute`  
Mutates: `loop-buffer loop-state delegates-command-effects`  
Usage access: `ENDLOOP USAGE`  

Purpose:

End the active LOOP block and replay buffered commands through the shell
  executor.

Usage contract:

```text
ENDLOOP
  ENDLOOP USAGE
```

Notes:

```text
ENDLOOP with no arguments executes the active LOOP buffer.
  ENDLOOP requires an active LOOP block except for ENDLOOP USAGE.
  ENDLOOP clears active loop state before replay.
  ENDLOOP replays buffered commands through the registered loop executor.
  ENDLOOP reports when no LOOP is active.
  ENDLOOP may indirectly mutate data, session state, or files depending on buffered commands.
```

Related:

```text
LOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL
```

Source comments:

```text
risk:
  mutates_loop_state: yes
  buffers_commands: yes
  executes_commands: through ENDLOOP
  mutates_table_data: depends on buffered commands
  max_iterations: clamped
related:
  ENDLOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL
```

---

### ENDSCAN

Source: `src/cli/cmd_scan.hpp`  
Owner: `DOT|ENDSCAN`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDSCAN USAGE`  

Purpose:

Close a SCAN loop block.

Usage contract:

```text
ENDSCAN
```

Notes:

```text
Syntax command paired with SCAN. It does not mutate table data by itself.
```

Related:

```text
SCAN
```

Source comments:

```text
SCAN subsystem commands
```

---

### ENDSCAN

Source: `x64base/src/cli/cmd_scan.hpp`  
Owner: `DOT|ENDSCAN`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDSCAN USAGE`  

Purpose:

Close a SCAN loop block.

Usage contract:

```text
ENDSCAN
```

Notes:

```text
Syntax command paired with SCAN. It does not mutate table data by itself.
```

Related:

```text
SCAN
```

Source comments:

```text
SCAN subsystem commands
```

---

### ENDUNTIL

Source: `src/cli/cmd_loop.hpp`  
Owner: `DOT|ENDUNTIL`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDUNTIL USAGE`  

Purpose:

Close an UNTIL loop/control block.

Usage contract:

```text
ENDUNTIL
```

Notes:

```text
Syntax command paired with UNTIL where supported. It does not mutate table data by itself.
```

Related:

```text
UNTIL, LOOP
```

Source comments:

```text
noargs: closes-control-block
effect: control-flow
mutates: none
usage-access: ENDWHILE USAGE
summary:
  Close a WHILE loop block.
usage:
  ENDWHILE
notes:
  Syntax command paired with WHILE. It does not mutate table data by itself.
related:
  WHILE
```

---

### ENDUNTIL

Source: `x64base/src/cli/cmd_loop.hpp`  
Owner: `DOT|ENDUNTIL`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDUNTIL USAGE`  

Purpose:

Close an UNTIL loop/control block.

Usage contract:

```text
ENDUNTIL
```

Notes:

```text
Syntax command paired with UNTIL where supported. It does not mutate table data by itself.
```

Related:

```text
UNTIL, LOOP
```

Source comments:

```text
noargs: closes-control-block
effect: control-flow
mutates: none
usage-access: ENDWHILE USAGE
summary:
  Close a WHILE loop block.
usage:
  ENDWHILE
notes:
  Syntax command paired with WHILE. It does not mutate table data by itself.
related:
  WHILE
```

---

### ENDWHILE

Source: `src/cli/cmd_loop.hpp`  
Owner: `DOT|ENDWHILE`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDWHILE USAGE`  

Purpose:

Close a WHILE loop block.

Usage contract:

```text
ENDWHILE
```

Notes:

```text
Syntax command paired with WHILE. It does not mutate table data by itself.
```

Related:

```text
WHILE
```

Source comments:

```text
WHILE/UNTIL commands
```

---

### ENDWHILE

Source: `x64base/src/cli/cmd_loop.hpp`  
Owner: `DOT|ENDWHILE`  
Category: `syntax-command`  
Status: `active`  
Effect: `control-flow`  
Mutates: `none`  
Usage access: `ENDWHILE USAGE`  

Purpose:

Close a WHILE loop block.

Usage contract:

```text
ENDWHILE
```

Notes:

```text
Syntax command paired with WHILE. It does not mutate table data by itself.
```

Related:

```text
WHILE
```

Source comments:

```text
WHILE/UNTIL commands
```

---

### ERASE

Source: `src/cli/cmd_erase.cpp`  
Owner: `DOT|ERASE`  
Category: `destructive-file`  
Status: `supported`  
Effect: `delete-table-files`  
Mutates: `filesystem`  
Usage access: `ERASE USAGE`  

Purpose:

Physically delete a DBF table file and known same-stem sidecar files.

Usage contract:

```text
ERASE USAGE
  ERASE <table> [CONFIRM]
  ERASE TABLE <table> [CONFIRM]
```

Examples:

```text
ERASE TABLE clients
  ERASE TABLE clients CONFIRM
  ERASE students.dbf CONFIRM
```

Notes:

```text
ERASE USAGE prints usage and does not inspect or delete files.
  Without CONFIRM, ERASE performs a dry-run and lists files that would be deleted.
  CONFIRM physically deletes the DBF and known same-stem sidecars.
```

Related:

```text
ZAP
  PACK
  COPY
```

Source comments:

```text
Supported syntax:
  ERASE <table> [CONFIRM]
  ERASE TABLE <table> [CONFIRM]
Examples:
  ERASE TABLE clients CONFIRM
  ERASE students.dbf CONFIRM
Behavior:
  - Resolves <table> to a .dbf path (adds .dbf if missing).
  - Resolves relative table names through the active SETPATH DBF slot.
  - Deletes the DBF plus known sidecars with the same stem in the same directory:
      .fpt .dbt .inx .cnx .cdx .idx .dtx .dti.json .schema.json
  - Safety gate: without CONFIRM, it prints what it *would* delete and does nothing.
```

---

### ERASE

Source: `x64base/src/cli/cmd_erase.cpp`  
Owner: `DOT|ERASE`  
Category: `destructive-file`  
Status: `supported`  
Effect: `delete-table-files`  
Mutates: `filesystem`  
Usage access: `ERASE USAGE`  

Purpose:

Physically delete a DBF table file and known same-stem sidecar files.

Usage contract:

```text
ERASE USAGE
  ERASE <table> [CONFIRM]
  ERASE TABLE <table> [CONFIRM]
```

Examples:

```text
ERASE TABLE clients
  ERASE TABLE clients CONFIRM
  ERASE students.dbf CONFIRM
```

Notes:

```text
ERASE USAGE prints usage and does not inspect or delete files.
  Without CONFIRM, ERASE performs a dry-run and lists files that would be deleted.
  CONFIRM physically deletes the DBF and known same-stem sidecars.
```

Related:

```text
ZAP
  PACK
  COPY
```

Source comments:

```text
Supported syntax:
  ERASE <table> [CONFIRM]
  ERASE TABLE <table> [CONFIRM]
Examples:
  ERASE TABLE clients CONFIRM
  ERASE students.dbf CONFIRM
Behavior:
  - Resolves <table> to a .dbf path (adds .dbf if missing).
  - Resolves relative table names through the active SETPATH DBF slot.
  - Deletes the DBF plus known sidecars with the same stem in the same directory:
      .fpt .dbt .inx .cnx .cdx .idx .dtx .dti.json .schema.json
  - Safety gate: without CONFIRM, it prints what it *would* delete and does nothing.
```

---

### ERP

Source: `src/cli/cmd_erp.cpp`  
Owner: `DOT|ERP_IMPL`  
Category: `integration-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Translation-unit shim for ERP/LabTalk integration includes.

Usage contract:

```text
This file currently does not export a command handler.
  If ERP becomes user-facing from this file, add the runtime command handler and full usage contract together.
```

Notes:

```text
Keep ERP application behavior owned by the ERP/LabTalk application layer.
```

---

### ERP

Source: `x64base/src/cli/cmd_erp.cpp`  
Owner: `DOT|ERP_IMPL`  
Category: `integration-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Translation-unit shim for ERP/LabTalk integration includes.

Usage contract:

```text
This file currently does not export a command handler.
  If ERP becomes user-facing from this file, add the runtime command handler and full usage contract together.
```

Notes:

```text
Keep ERP application behavior owned by the ERP/LabTalk application layer.
```

---

### ERP / EDU_ERP

Source: `src/edu/edu_erp.cpp`  
Owner: `EDU|ERP`  
Category: `education-database-demo`  
Status: `supported`  
Effect: `sqlite-demo-query`  
Mutates: `sqlite-connection-state`  
Usage access: `ERP USAGE; EDU_ERP USAGE`  

Purpose:

Educational Cascade Precision manufacturing ERP SQLite wrapper for
  status, schema/table inspection, and domain shortcut reports.

Usage contract:

```text
ERP USAGE
  ERP HELP
  ERP STATUS
  ERP CASCADE
  ERP CHECK
  ERP MODULES
  ERP TABLES
  ERP VIEWS
  ERP COLUMNS <table>
  ERP LIST <table> [limit]
  ERP ITEMS
  ERP STOCK
  ERP REORDER
  ERP BOM [sku]
  ERP WORKORDERS
  ERP THREEWAY
  ERP TRIAL
  ERP SCHEMA [table]
  ERP EXEC <sql...>
  ERP SELECT <sql...>
  ERP CLOSE
```

Examples:

```text
ERP USAGE
  ERP CASCADE
  ERP MODULES
  ERP ITEMS
  ERP STOCK
  ERP SELECT select * from items limit 5
```

Notes:

```text
USAGE/HELP/? returns before SQLite database work.
  No-arg behavior remains status plus brief usage.
  EDU_ERP and cmd_ERP are compatibility aliases for ERP behavior.
```

Source comments:

```text
ERP STOCK
  ERP REORDER
  ERP BOM [sku]
  ERP WORKORDERS
  ERP THREEWAY
  ERP TRIAL
Notes:
  - Uses dottalk::sqlite::* from sqlite/sqlite_adapter.hpp.
  - Independent of DBF open/order state.
  - SQLite here is an external SQL/RDBMS backend surface, not native DbArea storage.
  - ERP-specific behavior belongs here, not in the generic SQLITE command.
  - SELECT output is capped to keep CLI responsive.
```

---

### ERP / EDU_ERP

Source: `x64base/src/edu/edu_erp.cpp`  
Owner: `EDU|ERP`  
Category: `education-database-demo`  
Status: `supported`  
Effect: `sqlite-demo-query`  
Mutates: `sqlite-connection-state`  
Usage access: `ERP USAGE; EDU_ERP USAGE`  

Purpose:

Educational Cascade Precision manufacturing ERP SQLite wrapper for
  status, schema/table inspection, and domain shortcut reports.

Usage contract:

```text
ERP USAGE
  ERP HELP
  ERP STATUS
  ERP CASCADE
  ERP CHECK
  ERP MODULES
  ERP TABLES
  ERP VIEWS
  ERP COLUMNS <table>
  ERP LIST <table> [limit]
  ERP ITEMS
  ERP STOCK
  ERP REORDER
  ERP BOM [sku]
  ERP WORKORDERS
  ERP THREEWAY
  ERP TRIAL
  ERP SCHEMA [table]
  ERP EXEC <sql...>
  ERP SELECT <sql...>
  ERP CLOSE
```

Examples:

```text
ERP USAGE
  ERP CASCADE
  ERP MODULES
  ERP ITEMS
  ERP STOCK
  ERP SELECT select * from items limit 5
```

Notes:

```text
USAGE/HELP/? returns before SQLite database work.
  No-arg behavior remains status plus brief usage.
  EDU_ERP and cmd_ERP are compatibility aliases for ERP behavior.
```

Source comments:

```text
ERP STOCK
  ERP REORDER
  ERP BOM [sku]
  ERP WORKORDERS
  ERP THREEWAY
  ERP TRIAL
Notes:
  - Uses dottalk::sqlite::* from sqlite/sqlite_adapter.hpp.
  - Independent of DBF open/order state.
  - SQLite here is an external SQL/RDBMS backend surface, not native DbArea storage.
  - ERP-specific behavior belongs here, not in the generic SQLITE command.
  - SELECT output is capped to keep CLI responsive.
```

---

### ERROR_CLEAR

Source: `src/cli/cmd_error_clear.cpp`  
Owner: `DOT|ERROR_CLEAR`  
Category: `diagnostics`  
Status: `supported`  
Effect: `clear`  
Mutates: `error-state`  
Usage access: `ERROR_CLEAR USAGE`  

Purpose:

Clear the last xBase_64 error context.

Usage contract:

```text
ERROR_CLEAR
  ERROR_CLEAR USAGE
```

Notes:

```text
ERROR_CLEAR with no arguments clears the last error.
  ERROR_CLEAR USAGE prints usage and does not clear the error state.
  ERROR_CLEAR mutates diagnostic error state only, not table data.
```

Related:

```text
ERROR_STATUS
  ERROR_TEST
```

Source comments:

```text
src/cli/cmd_ERROR_CLEAR.cpp
Clear the last xBase_64 error and report success.
```

---

### ERROR_CLEAR

Source: `x64base/src/cli/cmd_error_clear.cpp`  
Owner: `DOT|ERROR_CLEAR`  
Category: `diagnostics`  
Status: `supported`  
Effect: `clear`  
Mutates: `error-state`  
Usage access: `ERROR_CLEAR USAGE`  

Purpose:

Clear the last xBase_64 error context.

Usage contract:

```text
ERROR_CLEAR
  ERROR_CLEAR USAGE
```

Notes:

```text
ERROR_CLEAR with no arguments clears the last error.
  ERROR_CLEAR USAGE prints usage and does not clear the error state.
  ERROR_CLEAR mutates diagnostic error state only, not table data.
```

Related:

```text
ERROR_STATUS
  ERROR_TEST
```

Source comments:

```text
src/cli/cmd_ERROR_CLEAR.cpp
Clear the last xBase_64 error and report success.
```

---

### ERROR_STATUS

Source: `src/cli/cmd_error_status.cpp`  
Owner: `DOT|ERROR_STATUS`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `output-format-state`  
Usage access: `ERROR_STATUS USAGE`  

Purpose:

Display the last xBase_64 error in a structured, HRESULT-style diagnostic format.

Usage contract:

```text
ERROR_STATUS
  ERROR_STATUS USAGE
```

Notes:

```text
ERROR_STATUS with no arguments reports the last error.
  ERROR_STATUS prints severity, facility, number, HRESULT, and message.
  ERROR_STATUS changes stream formatting while printing diagnostic output.
  ERROR_STATUS does not mutate table data.
```

Related:

```text
ERROR_CLEAR
  ERROR_TEST
```

Source comments:

```text
src/cli/cmd_ERROR_STATUS.cpp
Display the last xBase_64 error in a structured, MS-conformal format.
```

---

### ERROR_STATUS

Source: `x64base/src/cli/cmd_error_status.cpp`  
Owner: `DOT|ERROR_STATUS`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `output-format-state`  
Usage access: `ERROR_STATUS USAGE`  

Purpose:

Display the last xBase_64 error in a structured, HRESULT-style diagnostic format.

Usage contract:

```text
ERROR_STATUS
  ERROR_STATUS USAGE
```

Notes:

```text
ERROR_STATUS with no arguments reports the last error.
  ERROR_STATUS prints severity, facility, number, HRESULT, and message.
  ERROR_STATUS changes stream formatting while printing diagnostic output.
  ERROR_STATUS does not mutate table data.
```

Related:

```text
ERROR_CLEAR
  ERROR_TEST
```

Source comments:

```text
src/cli/cmd_ERROR_STATUS.cpp
Display the last xBase_64 error in a structured, MS-conformal format.
```

---

### ERROR_TEST

Source: `src/cli/cmd_error_test.cpp`  
Owner: `DOT|ERROR_TEST`  
Category: `diagnostics`  
Status: `supported`  
Effect: `test`  
Mutates: `error-state`  
Usage access: `ERROR_TEST USAGE`  

Purpose:

Run the xBase_64 error subsystem self-test and update last-error state on failure.

Usage contract:

```text
ERROR_TEST
  ERROR_TEST USAGE
```

Notes:

```text
ERROR_TEST with no arguments runs the error subsystem self-test.
  ERROR_TEST USAGE prints usage and does not run tests.
  Passing tests clear the last error.
  Failing tests set a canonical unknown error.
  ERROR_TEST mutates diagnostic error state only, not table data.
```

Related:

```text
ERROR_STATUS
  ERROR_CLEAR
```

Source comments:

```text
src/cli/cmd_ERROR_TEST.cpp
Self-test for the xBase_64 error subsystem.
```

---

### ERROR_TEST

Source: `x64base/src/cli/cmd_error_test.cpp`  
Owner: `DOT|ERROR_TEST`  
Category: `diagnostics`  
Status: `supported`  
Effect: `test`  
Mutates: `error-state`  
Usage access: `ERROR_TEST USAGE`  

Purpose:

Run the xBase_64 error subsystem self-test and update last-error state on failure.

Usage contract:

```text
ERROR_TEST
  ERROR_TEST USAGE
```

Notes:

```text
ERROR_TEST with no arguments runs the error subsystem self-test.
  ERROR_TEST USAGE prints usage and does not run tests.
  Passing tests clear the last error.
  Failing tests set a canonical unknown error.
  ERROR_TEST mutates diagnostic error state only, not table data.
```

Related:

```text
ERROR_STATUS
  ERROR_CLEAR
```

Source comments:

```text
src/cli/cmd_ERROR_TEST.cpp
Self-test for the xBase_64 error subsystem.
```

---

### ERSATZ

Source: `src/cli/cmd_ersatz.cpp`  
Owner: `DOT|ERSATZ`  
Category: `relational-browser`  
Status: `supported`  
Effect: `mixed`  
Mutates: `browser-session workspace-files cursor delta-baselines`  
Usage access: `ERSATZ USAGE`  

Purpose:

Relational browser and tuple-stream helper for current workspace/session,
  with navigation, tree/grid rendering, workspace handoff, and delta baselines.

Usage contract:

```text
ERSATZ
  ERSATZ USAGE
  ERSATZ SHOW
  ERSATZ REFRESH
  ERSATZ TREE
  ERSATZ GRID
  ERSATZ STATUS
  ERSATZ ORDER
  ERSATZ TOP
  ERSATZ BOTTOM
  ERSATZ NEXT
  ERSATZ NEXT <n>
  ERSATZ PREV
  ERSATZ PREV <n>
  ERSATZ SKIP <n>
  ERSATZ ROOT
  ERSATZ ROOT <alias>
  ERSATZ LIMIT <n>
  ERSATZ PATH <alias>
  ERSATZ CLEARPATH
  ERSATZ BACK
  ERSATZ OPEN <workspace>
  ERSATZ LOAD <name>
  ERSATZ SAVE <name>
  ERSATZ WLOAD <name>
  ERSATZ DELTA MARK <name>
  ERSATZ DELTA SHOW <name>
  ERSATZ DELTA CLEAR <name>
  ERSATZ DELTA CLEAR ALL
  ERSATZ DELTA STATUS
  ERSATZ RESET
```

Notes:

```text
ERSATZ with no arguments renders the current relational browser snapshot.
  SHOW, REFRESH, TREE, and GRID render the current browser session.
  TOP, BOTTOM, NEXT, PREV, and SKIP navigate the root cursor and render.
  ROOT, LIMIT, PATH, CLEARPATH, and BACK mutate browser session settings.
  OPEN hands off to WORKSPACE.
  LOAD, SAVE, and WLOAD read or write workspace files.
  DELTA commands manage in-memory tuple-stream baselines.
  RESET clears ERSATZ browser session state.
  ERSATZ is not table-data mutation by itself, but it can mutate cursor/session/workspace state.
```

Related:

```text
WORKSPACE
  REL
  BROWSE
  TUPLE
  GPS
```

Source comments:

```text
src/cli/cmd_ersatz.cpp
```

---

### ERSATZ

Source: `x64base/src/cli/cmd_ersatz.cpp`  
Owner: `DOT|ERSATZ`  
Category: `relational-browser`  
Status: `supported`  
Effect: `mixed`  
Mutates: `browser-session workspace-files cursor delta-baselines`  
Usage access: `ERSATZ USAGE`  

Purpose:

Relational browser and tuple-stream helper for current workspace/session,
  with navigation, tree/grid rendering, workspace handoff, and delta baselines.

Usage contract:

```text
ERSATZ
  ERSATZ USAGE
  ERSATZ SHOW
  ERSATZ REFRESH
  ERSATZ TREE
  ERSATZ GRID
  ERSATZ STATUS
  ERSATZ ORDER
  ERSATZ TOP
  ERSATZ BOTTOM
  ERSATZ NEXT
  ERSATZ NEXT <n>
  ERSATZ PREV
  ERSATZ PREV <n>
  ERSATZ SKIP <n>
  ERSATZ ROOT
  ERSATZ ROOT <alias>
  ERSATZ LIMIT <n>
  ERSATZ PATH <alias>
  ERSATZ CLEARPATH
  ERSATZ BACK
  ERSATZ OPEN <workspace>
  ERSATZ LOAD <name>
  ERSATZ SAVE <name>
  ERSATZ WLOAD <name>
  ERSATZ DELTA MARK <name>
  ERSATZ DELTA SHOW <name>
  ERSATZ DELTA CLEAR <name>
  ERSATZ DELTA CLEAR ALL
  ERSATZ DELTA STATUS
  ERSATZ RESET
```

Notes:

```text
ERSATZ with no arguments renders the current relational browser snapshot.
  SHOW, REFRESH, TREE, and GRID render the current browser session.
  TOP, BOTTOM, NEXT, PREV, and SKIP navigate the root cursor and render.
  ROOT, LIMIT, PATH, CLEARPATH, and BACK mutate browser session settings.
  OPEN hands off to WORKSPACE.
  LOAD, SAVE, and WLOAD read or write workspace files.
  DELTA commands manage in-memory tuple-stream baselines.
  RESET clears ERSATZ browser session state.
  ERSATZ is not table-data mutation by itself, but it can mutate cursor/session/workspace state.
```

Related:

```text
WORKSPACE
  REL
  BROWSE
  TUPLE
  GPS
```

Source comments:

```text
src/cli/cmd_ersatz.cpp
```

---

### EVALUATE / EVAL

Source: `src/edu/edu_evaluate.cpp`  
Owner: `EDU|EVALUATE`  
Category: `education-expression`  
Status: `supported`  
Effect: `evaluate-expression`  
Mutates: `none`  
Usage access: `EVALUATE USAGE`  

Purpose:

Evaluate a boolean predicate expression through xexpr and print .T. or .F.

Usage contract:

```text
EVALUATE USAGE
  EVALUATE <expr>
  EVAL <expr>
```

Examples:

```text
EVALUATE 1 = 1
  EVALUATE GPA >= 3.0
  EVAL LNAME = "SMITH"
```

Notes:

```text
EVALUATE USAGE prints usage before expression evaluation.
  When a table is open, field-aware expressions use the current record.
  This command does not mutate table data.
```

Source comments:

```text
src/cli/edu_evaluate.cpp
DotTalk++ EVALUATE / EVAL
Boolean predicate evaluator (IF/SCAN compatible)
xexpr migration note:
  This command now calls the xexpr facade instead of reaching directly into
  cli/expr/evaluate.hpp.  The command syntax and output remain unchanged.
```

---

### EVALUATE / EVAL

Source: `x64base/src/edu/edu_evaluate.cpp`  
Owner: `EDU|EVALUATE`  
Category: `education-expression`  
Status: `supported`  
Effect: `evaluate-expression`  
Mutates: `none`  
Usage access: `EVALUATE USAGE`  

Purpose:

Evaluate a boolean predicate expression through xexpr and print .T. or .F.

Usage contract:

```text
EVALUATE USAGE
  EVALUATE <expr>
  EVAL <expr>
```

Examples:

```text
EVALUATE 1 = 1
  EVALUATE GPA >= 3.0
  EVAL LNAME = "SMITH"
```

Notes:

```text
EVALUATE USAGE prints usage before expression evaluation.
  When a table is open, field-aware expressions use the current record.
  This command does not mutate table data.
```

Source comments:

```text
src/cli/edu_evaluate.cpp
DotTalk++ EVALUATE / EVAL
Boolean predicate evaluator (IF/SCAN compatible)
xexpr migration note:
  This command now calls the xexpr facade instead of reaching directly into
  cli/expr/evaluate.hpp.  The command syntax and output remain unchanged.
```

---

### EXAMPLE

Source: `src/cli/cmd_example.cpp`  
Owner: `DOT|EXAMPLE`  
Category: `diagnostics`  
Status: `supported`  
Effect: `test`  
Mutates: `none`  
Usage access: `EXAMPLE USAGE`  

Purpose:

Minimal example/test command used to verify token parsing and command routing.

Usage contract:

```text
EXAMPLE USAGE
  EXAMPLE TEST
```

Notes:

```text
EXAMPLE with no arguments shows usage.
  EXAMPLE TEST prints OK.
  EXAMPLE is read-only and does not mutate table data.
```

Related:

```text
ERROR_TEST
  TEST
```

---

### EXAMPLE

Source: `x64base/src/cli/cmd_example.cpp`  
Owner: `DOT|EXAMPLE`  
Category: `diagnostics`  
Status: `supported`  
Effect: `test`  
Mutates: `none`  
Usage access: `EXAMPLE USAGE`  

Purpose:

Minimal example/test command used to verify token parsing and command routing.

Usage contract:

```text
EXAMPLE USAGE
  EXAMPLE TEST
```

Notes:

```text
EXAMPLE with no arguments shows usage.
  EXAMPLE TEST prints OK.
  EXAMPLE is read-only and does not mutate table data.
```

Related:

```text
ERROR_TEST
  TEST
```

---

### EXPORT

Source: `src/cli/cmd_export.cpp`  
Owner: `DOT|EXPORT`  
Category: `io`  
Status: `supported`  
Effect: `export`  
Mutates: `filesystem`  
Usage access: `EXPORT USAGE`  

Purpose:

Export the current DBF rowset, or an already-open named work area, to a delimited file.

Usage contract:

```text
EXPORT USAGE
  EXPORT [TO] <file> [CSV|PIPE]
  EXPORT <open-area-token> TO <file> [CSV|PIPE]
```

Notes:

```text
EXPORT [TO] <file> writes the current table to the named file.
  EXPORT <open-area-token> TO <file> writes an already-open work area without changing
  the user's selected area intentionally.
  Named tokens may be an area number, #area, alias/name, logical name, DBF basename/stem,
  filename, or full path, if those values resolve uniquely to an open area.
  Named EXPORT does not auto-open tables from disk.
  CSV is the default format; PIPE uses a pipe delimiter.
  A missing extension is added automatically (.csv for CSV, .txt for PIPE).
  EXPORT writes a header row.
  EXPORT honors the active SET FILTER for the exported area.
  EXPORT reads records in physical table order.
  EXPORT may report file/write errors and still emit a summary when appropriate.
```

Related:

```text
DUMP
  LIST
  COPY TO
  DDL
  WORKSPACE
  WSREPORT
```

Source comments:

```text
src/cli/cmd_export.cpp
```

---

### EXPORT

Source: `x64base/src/cli/cmd_export.cpp`  
Owner: `DOT|EXPORT`  
Category: `io`  
Status: `supported`  
Effect: `export`  
Mutates: `filesystem`  
Usage access: `EXPORT USAGE`  

Purpose:

Export the current DBF rowset, or an already-open named work area, to a delimited file.

Usage contract:

```text
EXPORT USAGE
  EXPORT [TO] <file> [CSV|PIPE]
  EXPORT <open-area-token> TO <file> [CSV|PIPE]
```

Notes:

```text
EXPORT [TO] <file> writes the current table to the named file.
  EXPORT <open-area-token> TO <file> writes an already-open work area without changing
  the user's selected area intentionally.
  Named tokens may be an area number, #area, alias/name, logical name, DBF basename/stem,
  filename, or full path, if those values resolve uniquely to an open area.
  Named EXPORT does not auto-open tables from disk.
  CSV is the default format; PIPE uses a pipe delimiter.
  A missing extension is added automatically (.csv for CSV, .txt for PIPE).
  EXPORT writes a header row.
  EXPORT honors the active SET FILTER for the exported area.
  EXPORT reads records in physical table order.
  EXPORT may report file/write errors and still emit a summary when appropriate.
```

Related:

```text
DUMP
  LIST
  COPY TO
  DDL
  WORKSPACE
  WSREPORT
```

Source comments:

```text
src/cli/cmd_export.cpp
```

---

### EXPORTFUNCTIONS

Source: `src/cli/cmd_export_functions.cpp`  
Owner: `DOT|EXPORTFUNCTIONS`  
Category: `help`  
Status: `supported`  
Effect: `export`  
Mutates: `filesystem`  
Usage access: `EXPORTFUNCTIONS USAGE`  

Purpose:

Export the expression/function catalog to Markdown documentation.

Usage contract:

```text
EXPORTFUNCTIONS
  EXPORTFUNCTIONS USAGE
  EXPORTFUNCTIONS MD
  EXPORTFUNCTIONS MD <path>
  EXPORTFUNCTIONS <path>
```

Notes:

```text
EXPORTFUNCTIONS with no arguments writes ./data/docs/functions.md.
  EXPORTFUNCTIONS MD writes the default Markdown output.
  EXPORTFUNCTIONS MD <path> writes Markdown to the supplied path.
  EXPORTFUNCTIONS <path> treats the argument as the Markdown output path.
  EXPORTFUNCTIONS USAGE prints usage and does not write files.
  The expression function catalog remains the source of truth.
```

Related:

```text
HELP
  CMDHELP
  DOTHELP
```

Source comments:

```text
Export the function catalog to Markdown.
Command surface:
  EXPORTFUNCTIONS
  EXPORTFUNCTIONS MD
  EXPORTFUNCTIONS MD <path>
  EXPORTFUNCTIONS <path>
Default output path:
  ./data/docs/functions.md
Notes:
- Keeps function_catalog as the single source of truth.
- Does not depend on cmd_help.cpp internals.
- Category order matches grouped HELP output.
```

---

### EXPORTFUNCTIONS

Source: `x64base/src/cli/cmd_export_functions.cpp`  
Owner: `DOT|EXPORTFUNCTIONS`  
Category: `help`  
Status: `supported`  
Effect: `export`  
Mutates: `filesystem`  
Usage access: `EXPORTFUNCTIONS USAGE`  

Purpose:

Export the expression/function catalog to Markdown documentation.

Usage contract:

```text
EXPORTFUNCTIONS
  EXPORTFUNCTIONS USAGE
  EXPORTFUNCTIONS MD
  EXPORTFUNCTIONS MD <path>
  EXPORTFUNCTIONS <path>
```

Notes:

```text
EXPORTFUNCTIONS with no arguments writes ./data/docs/functions.md.
  EXPORTFUNCTIONS MD writes the default Markdown output.
  EXPORTFUNCTIONS MD <path> writes Markdown to the supplied path.
  EXPORTFUNCTIONS <path> treats the argument as the Markdown output path.
  EXPORTFUNCTIONS USAGE prints usage and does not write files.
  The expression function catalog remains the source of truth.
```

Related:

```text
HELP
  CMDHELP
  DOTHELP
```

Source comments:

```text
Export the function catalog to Markdown.
Command surface:
  EXPORTFUNCTIONS
  EXPORTFUNCTIONS MD
  EXPORTFUNCTIONS MD <path>
  EXPORTFUNCTIONS <path>
Default output path:
  ./data/docs/functions.md
Notes:
- Keeps function_catalog as the single source of truth.
- Does not depend on cmd_help.cpp internals.
- Category order matches grouped HELP output.
```

---

### FIELDMGR

Source: `src/cli/cmd_fieldmgr.cpp`  
Owner: `DOT|FIELDMGR`  
Category: `schema`  
Status: `supported`  
Effect: `mixed`  
Mutates: `table-schema index metadata`  
Usage access: `FIELDMGR USAGE`  

Purpose:

Inspect and modify field definitions for the current DBF through the shared
  fields manager layer.

Usage contract:

```text
FIELDMGR
  FIELDMGR USAGE
  FIELDMGR HELP
  FIELDMGR SHOW
  FIELDMGR LIST
  FIELDMGR APPEND <name> <type>
  FIELDMGR DELETE <name>
  FIELDMGR MODIFY <name> NAME <newname>
  FIELDMGR MODIFY <name> TYPE <type>
  FIELDMGR MODIFY <name> TO <newname> <type>
  FIELDMGR COPY TO <target>
  FIELDMGR VALIDATE
  FIELDMGR CHECK
  FIELDMGR REBUILD INDEXES
```

Examples:

```text
FIELDMGR SHOW
  FIELDMGR APPEND ZIP C10
  FIELDMGR DELETE ZIP
  FIELDMGR MODIFY ZIP NAME POSTAL
  FIELDMGR VALIDATE
```

Notes:

```text
FIELDMGR with no arguments shows current field metadata.
  SHOW and LIST are read-only reports.
  APPEND, DELETE, and MODIFY mutate table schema.
  COPY exports or copies field metadata through the fields manager layer.
  VALIDATE and CHECK report field/schema consistency.
  REBUILD INDEXES delegates index rebuild through the fields manager layer.
  FIELDMGR is schema mutation capable and is not purely read-only.
```

Related:

```text
STRUCT
  FIELDS
  DDL
  CREATE
  INDEX
```

---

### FIELDMGR

Source: `x64base/src/cli/cmd_fieldmgr.cpp`  
Owner: `DOT|FIELDMGR`  
Category: `schema`  
Status: `supported`  
Effect: `mixed`  
Mutates: `table-schema index metadata`  
Usage access: `FIELDMGR USAGE`  

Purpose:

Inspect and modify field definitions for the current DBF through the shared
  fields manager layer.

Usage contract:

```text
FIELDMGR
  FIELDMGR USAGE
  FIELDMGR HELP
  FIELDMGR SHOW
  FIELDMGR LIST
  FIELDMGR APPEND <name> <type>
  FIELDMGR DELETE <name>
  FIELDMGR MODIFY <name> NAME <newname>
  FIELDMGR MODIFY <name> TYPE <type>
  FIELDMGR MODIFY <name> TO <newname> <type>
  FIELDMGR COPY TO <target>
  FIELDMGR VALIDATE
  FIELDMGR CHECK
  FIELDMGR REBUILD INDEXES
```

Examples:

```text
FIELDMGR SHOW
  FIELDMGR APPEND ZIP C10
  FIELDMGR DELETE ZIP
  FIELDMGR MODIFY ZIP NAME POSTAL
  FIELDMGR VALIDATE
```

Notes:

```text
FIELDMGR with no arguments shows current field metadata.
  SHOW and LIST are read-only reports.
  APPEND, DELETE, and MODIFY mutate table schema.
  COPY exports or copies field metadata through the fields manager layer.
  VALIDATE and CHECK report field/schema consistency.
  REBUILD INDEXES delegates index rebuild through the fields manager layer.
  FIELDMGR is schema mutation capable and is not purely read-only.
```

Related:

```text
STRUCT
  FIELDS
  DDL
  CREATE
  INDEX
```

---

### FIELDS

Source: `src/cli/cmd_fields.cpp`  
Owner: `DOT|FIELDS`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `FIELDS USAGE`  

Purpose:

Report the field list for the current work area with aligned field number,
  name, type, length, and decimal columns.

Usage contract:

```text
FIELDS
  FIELDS USAGE
```

Notes:

```text
FIELDS with no arguments reports field metadata.
  FIELDS is read-only and does not mutate table data or cursor position.
  If no fields are available, FIELDS prints a no-fields message.
```

Related:

```text
STRUCT
  FIELDMGR
  DUMP
```

---

### FIELDS

Source: `x64base/src/cli/cmd_fields.cpp`  
Owner: `DOT|FIELDS`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `FIELDS USAGE`  

Purpose:

Report the field list for the current work area with aligned field number,
  name, type, length, and decimal columns.

Usage contract:

```text
FIELDS
  FIELDS USAGE
```

Notes:

```text
FIELDS with no arguments reports field metadata.
  FIELDS is read-only and does not mutate table data or cursor position.
  If no fields are available, FIELDS prints a no-fields message.
```

Related:

```text
STRUCT
  FIELDMGR
  DUMP
```

---

### FIND

Source: `src/cli/cmd_find.cpp`  
Owner: `DOT|FIND`  
Category: `navigation`  
Status: `supported`  
Effect: `locate`  
Mutates: `cursor`  
Usage access: `FIND USAGE`  

Purpose:

Find text in the current table, delegating to SEEK when the active order
  can satisfy the request and otherwise scanning the selected field.

Usage contract:

```text
FIND USAGE
  FIND <text>
  FIND <field> <text>
  FIND <text> IN <field>
```

Notes:

```text
FIND requires an open table except for FIND USAGE.
  FIND with one text argument delegates to SEEK when an order is active.
  FIND with a field delegates to SEEK only when that field is the active tag.
  Otherwise FIND scans the requested field using ordered or physical traversal.
  FIND honors active SET FILTER visibility.
  FIND positions on the found record when successful.
  FIND restores the prior cursor when not found.
```

Related:

```text
SEEK
  LOCATE
  GOTO
  COUNT
  SET ORDER
```

Source comments:

```text
src/cli/cmd_find.cpp
FIND <text>
FIND <field> <text>
Dev-tool contract:
- FIND <text> delegates to SEEK when an order is active.
- FIND <field> <text> and FIND <text> IN <field> delegate to SEEK only
  when <field> is the active tag.
- Otherwise fall back to ordered or physical scan of the requested field.
- Honors active SET FILTER via filter::visible(&A, nullptr).
- Positions on the found record when successful; restores the prior cursor when not found.
```

---

### FIND

Source: `x64base/src/cli/cmd_find.cpp`  
Owner: `DOT|FIND`  
Category: `navigation`  
Status: `supported`  
Effect: `locate`  
Mutates: `cursor`  
Usage access: `FIND USAGE`  

Purpose:

Find text in the current table, delegating to SEEK when the active order
  can satisfy the request and otherwise scanning the selected field.

Usage contract:

```text
FIND USAGE
  FIND <text>
  FIND <field> <text>
  FIND <text> IN <field>
```

Notes:

```text
FIND requires an open table except for FIND USAGE.
  FIND with one text argument delegates to SEEK when an order is active.
  FIND with a field delegates to SEEK only when that field is the active tag.
  Otherwise FIND scans the requested field using ordered or physical traversal.
  FIND honors active SET FILTER visibility.
  FIND positions on the found record when successful.
  FIND restores the prior cursor when not found.
```

Related:

```text
SEEK
  LOCATE
  GOTO
  COUNT
  SET ORDER
```

Source comments:

```text
src/cli/cmd_find.cpp
FIND <text>
FIND <field> <text>
Dev-tool contract:
- FIND <text> delegates to SEEK when an order is active.
- FIND <field> <text> and FIND <text> IN <field> delegate to SEEK only
  when <field> is the active tag.
- Otherwise fall back to ordered or physical scan of the requested field.
- Honors active SET FILTER via filter::visible(&A, nullptr).
- Positions on the found record when successful; restores the prior cursor when not found.
```

---

### FIRST

Source: `src/cli/cmd_first.cpp`  
Owner: `DOT|FIRST`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `FIRST USAGE`  

Purpose:

Move the current work-area cursor to the first visible/logical record.

Usage contract:

```text
FIRST
  FIRST USAGE
```

Notes:

```text
FIRST with no arguments moves to the first visible/logical record.
  FIRST requires an open table except for FIRST USAGE.
  FIRST uses the logical_nav first_recno helper.
  FIRST mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

Source comments:

```text
src/cli/cmd_first.cpp
FIRST = first visible record in current logical view
(active order + filter visibility).
```

---

### FIRST

Source: `x64base/src/cli/cmd_first.cpp`  
Owner: `DOT|FIRST`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `FIRST USAGE`  

Purpose:

Move the current work-area cursor to the first visible/logical record.

Usage contract:

```text
FIRST
  FIRST USAGE
```

Notes:

```text
FIRST with no arguments moves to the first visible/logical record.
  FIRST requires an open table except for FIRST USAGE.
  FIRST uses the logical_nav first_recno helper.
  FIRST mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

Source comments:

```text
src/cli/cmd_first.cpp
FIRST = first visible record in current logical view
(active order + filter visibility).
```

---

### FORMULA / ?

Source: `src/edu/edu_formula.cpp`  
Owner: `EDU|FORMULA`  
Category: `education-expression`  
Status: `supported`  
Effect: `evaluate-expression`  
Mutates: `none`  
Usage access: `FORMULA USAGE`  

Purpose:

Evaluate a scalar expression through xexpr and print the formatted value.

Usage contract:

```text
FORMULA USAGE
  FORMULA <expr>
  ? <expr>
```

Examples:

```text
FORMULA 2 + 2
  FORMULA UPPER(LNAME)
  ? GPA + 0
```

Notes:

```text
FORMULA USAGE prints usage before expression evaluation.
  When a table is open, field-aware expressions use the current record.
  This command does not mutate table data.
```

Source comments:

```text
===============================
FILE: src/cli/edu_formula.cpp
FORMULA / "?" <expr>
Phase 1 xexpr migration:
- FORMULA now routes expression evaluation through xexpr.
- No direct dependency on cli/expr AST/parser/eval headers.
- No manual DBF header scanning or disk reads.
- Table-aware expressions use the current DbArea through xexpr::EvalContext.
===============================
```

---

### FORMULA / ?

Source: `x64base/src/edu/edu_formula.cpp`  
Owner: `EDU|FORMULA`  
Category: `education-expression`  
Status: `supported`  
Effect: `evaluate-expression`  
Mutates: `none`  
Usage access: `FORMULA USAGE`  

Purpose:

Evaluate a scalar expression through xexpr and print the formatted value.

Usage contract:

```text
FORMULA USAGE
  FORMULA <expr>
  ? <expr>
```

Examples:

```text
FORMULA 2 + 2
  FORMULA UPPER(LNAME)
  ? GPA + 0
```

Notes:

```text
FORMULA USAGE prints usage before expression evaluation.
  When a table is open, field-aware expressions use the current record.
  This command does not mutate table data.
```

Source comments:

```text
===============================
FILE: src/cli/edu_formula.cpp
FORMULA / "?" <expr>
Phase 1 xexpr migration:
- FORMULA now routes expression evaluation through xexpr.
- No direct dependency on cli/expr AST/parser/eval headers.
- No manual DBF header scanning or disk reads.
- Table-aware expressions use the current DbArea through xexpr::EvalContext.
===============================
```

---

### FOXHELP

Source: `src/cli/cmd_foxhelp.cpp`  
Owner: `DOT|FOXHELP`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `FOXHELP USAGE`  

Purpose:

List or search the static FoxPro-style command catalog.

Usage contract:

```text
FOXHELP
  FOXHELP USAGE
  FOXHELP <name>
  FOXHELP <search>
  FH
  FH <name>
  FH <search>
```

Notes:

```text
FOXHELP with no arguments lists the FoxPro-style command subset.
  FOXHELP <name> prints an exact catalog item when found.
  FOXHELP <search> searches the catalog and prints matching items.
  FH is a short alias for FOXHELP.
  FOXHELP is a read-only help/report command.
```

Related:

```text
HELP
  CMDHELP
  FOXSTANDARD
```

Source comments:

```text
src/cli/cmd_foxhelp.cpp
```

---

### FOXHELP

Source: `x64base/src/cli/cmd_foxhelp.cpp`  
Owner: `DOT|FOXHELP`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `FOXHELP USAGE`  

Purpose:

List or search the static FoxPro-style command catalog.

Usage contract:

```text
FOXHELP
  FOXHELP USAGE
  FOXHELP <name>
  FOXHELP <search>
  FH
  FH <name>
  FH <search>
```

Notes:

```text
FOXHELP with no arguments lists the FoxPro-style command subset.
  FOXHELP <name> prints an exact catalog item when found.
  FOXHELP <search> searches the catalog and prints matching items.
  FH is a short alias for FOXHELP.
  FOXHELP is a read-only help/report command.
```

Related:

```text
HELP
  CMDHELP
  FOXSTANDARD
```

Source comments:

```text
src/cli/cmd_foxhelp.cpp
```

---

### FOXREF

Source: `src/cli/cmd_foxref.cpp`  
Owner: `DOT|FOXREF_IMPL`  
Category: `reference-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by FOXREF/HELP surface`  

Purpose:

Empty translation-unit shim for FOXREF inline implementation.

Usage contract:

```text
This file does not export a command handler.
  FOXREF command behavior and usage are owned by the actual FOXREF/help surface.
```

Notes:

```text
This file exists to keep the FOXREF implementation layout/build graph stable.
  Do not add command dispatch behavior here unless the FOXREF architecture changes.
```

---

### FOXREF

Source: `x64base/src/cli/cmd_foxref.cpp`  
Owner: `DOT|FOXREF_IMPL`  
Category: `reference-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by FOXREF/HELP surface`  

Purpose:

Empty translation-unit shim for FOXREF inline implementation.

Usage contract:

```text
This file does not export a command handler.
  FOXREF command behavior and usage are owned by the actual FOXREF/help surface.
```

Notes:

```text
This file exists to keep the FOXREF implementation layout/build graph stable.
  Do not add command dispatch behavior here unless the FOXREF architecture changes.
```

---

### FOXSTANDARD

Source: `src/cli/cmd_foxstandard.cpp`  
Owner: `DOT|FOXSTANDARD`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `FOXSTANDARD USAGE`  

Purpose:

Render static historical FoxPro-standard reference topics.

Usage contract:

```text
FOXSTANDARD USAGE
  FOXSTANDARD <command>
  FOXSTANDARD ALL
  FOXSTANDARD TOPICS
  FOXSTANDARD LIST
```

Notes:

```text
FOXSTANDARD with no arguments shows usage.
  FOXSTANDARD ALL, TOPICS, and LIST render the available topic list.
  FOXSTANDARD <command> renders the static reference for that command.
  FOXSTANDARD is separate from the live HELP and command catalogs.
```

Related:

```text
FOXHELP
  HELP
  CMDHELP
```

Source comments:

```text
src/cli/cmd_foxstandard.cpp
FOXSTANDARD is a static historical reference command.
It is intentionally separate from live HELP and the live command catalogs.
```

---

### FOXSTANDARD

Source: `x64base/src/cli/cmd_foxstandard.cpp`  
Owner: `DOT|FOXSTANDARD`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `FOXSTANDARD USAGE`  

Purpose:

Render static historical FoxPro-standard reference topics.

Usage contract:

```text
FOXSTANDARD USAGE
  FOXSTANDARD <command>
  FOXSTANDARD ALL
  FOXSTANDARD TOPICS
  FOXSTANDARD LIST
```

Notes:

```text
FOXSTANDARD with no arguments shows usage.
  FOXSTANDARD ALL, TOPICS, and LIST render the available topic list.
  FOXSTANDARD <command> renders the static reference for that command.
  FOXSTANDARD is separate from the live HELP and command catalogs.
```

Related:

```text
FOXHELP
  HELP
  CMDHELP
```

Source comments:

```text
src/cli/cmd_foxstandard.cpp
FOXSTANDARD is a static historical reference command.
It is intentionally separate from live HELP and the live command catalogs.
```

---

### GO

Source: `src/cli/cmd_go.cpp`  
Owner: `DOT|GO`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `GO USAGE`  

Purpose:

Refresh the current record, move to table/order endpoints, move to an
  absolute record number, or skip relative to the current record.

Usage contract:

```text
GO
  GO USAGE
  GO TOP
  GO BOTTOM
  GO FIRST
  GO LAST
  GO TO <recno>
  GO RECORD <recno>
  GO <recno>
  GO +<n>
  GO -<n>
```

Notes:

```text
GO with no arguments refreshes/re-reads the current record through the navigation layer.
  GO TOP/BOTTOM/FIRST/LAST move to logical endpoints.
  GO <recno>, GO TO <recno>, and GO RECORD <recno> navigate absolutely.
  GO +/-<n> delegates to relative skip.
  GO USAGE prints usage before navigation.
```

Related:

```text
GOTO
  TOP
  BOTTOM
  SKIP
```

Source comments:

```text
src/cli/cmd_go.cpp
FoxPro-style GO router.
Supported forms:
  GO
  GO TOP | BOTTOM | FIRST | LAST
  GO [TO] <recno>
  GO RECORD <recno>
  GO +/-<n>
```

---

### GO

Source: `x64base/src/cli/cmd_go.cpp`  
Owner: `DOT|GO`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `GO USAGE`  

Purpose:

Refresh the current record, move to table/order endpoints, move to an
  absolute record number, or skip relative to the current record.

Usage contract:

```text
GO
  GO USAGE
  GO TOP
  GO BOTTOM
  GO FIRST
  GO LAST
  GO TO <recno>
  GO RECORD <recno>
  GO <recno>
  GO +<n>
  GO -<n>
```

Notes:

```text
GO with no arguments refreshes/re-reads the current record through the navigation layer.
  GO TOP/BOTTOM/FIRST/LAST move to logical endpoints.
  GO <recno>, GO TO <recno>, and GO RECORD <recno> navigate absolutely.
  GO +/-<n> delegates to relative skip.
  GO USAGE prints usage before navigation.
```

Related:

```text
GOTO
  TOP
  BOTTOM
  SKIP
```

Source comments:

```text
src/cli/cmd_go.cpp
FoxPro-style GO router.
Supported forms:
  GO
  GO TOP | BOTTOM | FIRST | LAST
  GO [TO] <recno>
  GO RECORD <recno>
  GO +/-<n>
```

---

### GOTO

Source: `src/cli/cmd_goto.cpp`  
Owner: `DOT|GOTO`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `GOTO USAGE`  

Purpose:

Move the current work-area cursor to an absolute record number, first
  record, or last record through the shared navigation layer.

Usage contract:

```text
GOTO USAGE
  GOTO <recno>
  GOTO FIRST
  GOTO LAST
```

Notes:

```text
GOTO requires a target argument except for GOTO USAGE.
  GOTO FIRST and GOTO LAST use endpoint navigation.
  GOTO <recno> uses absolute record navigation.
  GOTO mutates cursor position but does not mutate table data.
```

Related:

```text
SKIP
  GO
  TOP
  BOTTOM
  GPS
```

Source comments:

```text
src/cli/cmd_goto.cpp
Narrow, engine-facing GOTO command.
Supported forms:
  GOTO <recno>
  GOTO FIRST
  GOTO LAST
```

---

### GOTO

Source: `x64base/src/cli/cmd_goto.cpp`  
Owner: `DOT|GOTO`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `GOTO USAGE`  

Purpose:

Move the current work-area cursor to an absolute record number, first
  record, or last record through the shared navigation layer.

Usage contract:

```text
GOTO USAGE
  GOTO <recno>
  GOTO FIRST
  GOTO LAST
```

Notes:

```text
GOTO requires a target argument except for GOTO USAGE.
  GOTO FIRST and GOTO LAST use endpoint navigation.
  GOTO <recno> uses absolute record navigation.
  GOTO mutates cursor position but does not mutate table data.
```

Related:

```text
SKIP
  GO
  TOP
  BOTTOM
  GPS
```

Source comments:

```text
src/cli/cmd_goto.cpp
Narrow, engine-facing GOTO command.
Supported forms:
  GOTO <recno>
  GOTO FIRST
  GOTO LAST
```

---

### GPS

Source: `src/cli/cmd_gps.cpp`  
Owner: `DOT|GPS`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `GPS USAGE`  

Purpose:

Report current work-area position, including area slot, table label,
  physical record number, and computed logical row.

Usage contract:

```text
GPS
  GPS USAGE
```

Notes:

```text
GPS with no arguments reports cursor position.
  GPS with no open table reports the current area and no-table state.
  GPS computes logical row by iterating visible ordered records.
  GPS is read-only for table data but may temporarily move the cursor while computing logical row.
```

Related:

```text
GOTO
  SKIP
  AREA
  STATUS
```

---

### GPS

Source: `x64base/src/cli/cmd_gps.cpp`  
Owner: `DOT|GPS`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `GPS USAGE`  

Purpose:

Report current work-area position, including area slot, table label,
  physical record number, and computed logical row.

Usage contract:

```text
GPS
  GPS USAGE
```

Notes:

```text
GPS with no arguments reports cursor position.
  GPS with no open table reports the current area and no-table state.
  GPS computes logical row by iterating visible ordered records.
  GPS is read-only for table data but may temporarily move the cursor while computing logical row.
```

Related:

```text
GOTO
  SKIP
  AREA
  STATUS
```

---

### HELP

Source: `src/cli/cmd_help.cpp`  
Owner: `DOT|HELP`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `HELP USAGE`  

Purpose:

Route user help requests across DotTalk command, function, FoxPro,
  PowerShell, SQL, beta, predicate, and educational help surfaces.

Usage contract:

```text
HELP
  HELP USAGE
  HELP GIANT
  HELP BETA
  HELP PS
  HELP SQL
  HELP PREDICATES
  HELP FUNCTIONS
  HELP FUNCTION <name>
  HELP /FOX <topic>
  HELP /DOT <topic>
  HELP /ED <topic>
  HELP <command>
```

Notes:

```text
HELP with no arguments prints the top-level help router.
  HELP <command> normalizes through the reflected command catalog first.
  HELP FUNCTION <name> checks reflected function metadata and catalog docs.
  HELP GIANT delegates to the full command catalog.
  HELP is read-only for table data and path state.
```

Related:

```text
CMDHELP
  CMDHELPCHK
  FOXHELP
  PREDHELP
```

Source comments:

```text
src/cli/cmd_help.cpp
```

---

### HELP

Source: `src/cli/cmd_help_grouped.cpp`  
Owner: `DOT|HELP_GROUPED_IMPL`  
Category: `help-helper`  
Status: `implementation-helper`  
Effect: `report`  
Mutates: `none`  
Usage access: `owned-by HELP`  

Purpose:

Helper implementation for grouped HELP/reflection output.

Usage contract:

```text
This file does not export a standalone shell command.
  User-visible usage is owned by HELP, CMDHELP, and related HELP reflection commands.
```

Notes:

```text
Keep this file focused on grouped presentation/reporting support.
  Do not register a separate HELP_GROUPED command from here.
```

---

### HELP

Source: `x64base/src/cli/cmd_help.cpp`  
Owner: `DOT|HELP`  
Category: `help`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `HELP USAGE`  

Purpose:

Route user help requests across DotTalk command, function, FoxPro,
  PowerShell, SQL, beta, predicate, and educational help surfaces.

Usage contract:

```text
HELP
  HELP USAGE
  HELP GIANT
  HELP BETA
  HELP PS
  HELP SQL
  HELP PREDICATES
  HELP FUNCTIONS
  HELP FUNCTION <name>
  HELP /FOX <topic>
  HELP /DOT <topic>
  HELP /ED <topic>
  HELP <command>
```

Notes:

```text
HELP with no arguments prints the top-level help router.
  HELP <command> normalizes through the reflected command catalog first.
  HELP FUNCTION <name> checks reflected function metadata and catalog docs.
  HELP GIANT delegates to the full command catalog.
  HELP is read-only for table data and path state.
```

Related:

```text
CMDHELP
  CMDHELPCHK
  FOXHELP
  PREDHELP
```

Source comments:

```text
src/cli/cmd_help.cpp
```

---

### HELP

Source: `x64base/src/cli/cmd_help_grouped.cpp`  
Owner: `DOT|HELP_GROUPED_IMPL`  
Category: `help-helper`  
Status: `implementation-helper`  
Effect: `report`  
Mutates: `none`  
Usage access: `owned-by HELP`  

Purpose:

Helper implementation for grouped HELP/reflection output.

Usage contract:

```text
This file does not export a standalone shell command.
  User-visible usage is owned by HELP, CMDHELP, and related HELP reflection commands.
```

Notes:

```text
Keep this file focused on grouped presentation/reporting support.
  Do not register a separate HELP_GROUPED command from here.
```

---

### HIER

Source: `src/dewey/cmd_hier.cpp`  
Owner: `DEV|HIER`  
Category: `dev-hierarchy`  
Status: `dev-tool`  
Effect: `hierarchy-table-operation`  
Mutates: `current-table hierarchy-fields`  
Usage access: `HIER USAGE`  

Purpose:

Developer hierarchy service command for creating, moving, validating, and
  listing nested hierarchy nodes in the current DbArea.

Usage contract:

```text
HIER USAGE
  HIER CREATE ROOT <node_id> [NAME <text>] [TYPE <text>] [SORT <n>]
  HIER ADD CHILD <parent_id> <node_id> [NAME <text>] [TYPE <text>] [SORT <n>]
  HIER INSERT BETWEEN <left_id> <right_id> <node_id>
  HIER MOVE <node_id> TO <new_parent_id>
  HIER DELETE <node_id>
  HIER DELETE SUBTREE <node_id>
  HIER REBUILD
  HIER VALIDATE
  HIER CHILDREN <node_id>
  HIER SUBTREE <node_id>
```

Examples:

```text
HIER CREATE ROOT ROOT NAME Root
  HIER ADD CHILD ROOT CHILD1 NAME Child
  HIER VALIDATE
  HIER CHILDREN ROOT
```

Notes:

```text
HIER USAGE/HELP/? prints usage before constructing HierarchyService.
  HIER is a developer command and may mutate hierarchy state in the current table.
```

---

### HIER

Source: `x64base/src/dewey/cmd_hier.cpp`  
Owner: `DEV|HIER`  
Category: `dev-hierarchy`  
Status: `dev-tool`  
Effect: `hierarchy-table-operation`  
Mutates: `current-table hierarchy-fields`  
Usage access: `HIER USAGE`  

Purpose:

Developer hierarchy service command for creating, moving, validating, and
  listing nested hierarchy nodes in the current DbArea.

Usage contract:

```text
HIER USAGE
  HIER CREATE ROOT <node_id> [NAME <text>] [TYPE <text>] [SORT <n>]
  HIER ADD CHILD <parent_id> <node_id> [NAME <text>] [TYPE <text>] [SORT <n>]
  HIER INSERT BETWEEN <left_id> <right_id> <node_id>
  HIER MOVE <node_id> TO <new_parent_id>
  HIER DELETE <node_id>
  HIER DELETE SUBTREE <node_id>
  HIER REBUILD
  HIER VALIDATE
  HIER CHILDREN <node_id>
  HIER SUBTREE <node_id>
```

Examples:

```text
HIER CREATE ROOT ROOT NAME Root
  HIER ADD CHILD ROOT CHILD1 NAME Child
  HIER VALIDATE
  HIER CHILDREN ROOT
```

Notes:

```text
HIER USAGE/HELP/? prints usage before constructing HierarchyService.
  HIER is a developer command and may mutate hierarchy state in the current table.
```

---

### IDX

Source: `src/cli/cmd_idx.cpp`  
Owner: `DOT|IDX`  
Category: `education`  
Status: `supported`  
Effect: `mixed`  
Mutates: `edu-idx-memory`  
Usage access: `IDX USAGE`  

Purpose:

Memory-only educational index lab for teaching sorting and index concepts
  without writing persistent INX/CNX/CDX files.

Usage contract:

```text
IDX
  IDX USAGE
  IDX ON <field|#n> TAG <name>
  IDX ON <field|#n> TAG <name> SORT <algo>
  IDX ON <field|#n> TAG <name> <algo>
  IDX ON <field|#n> TAG <name> ASC
  IDX ON <field|#n> TAG <name> DESC
  IDX LIST
  IDX DROP <tag>
  IDX DROP ALL
```

Examples:

```text
IDX ON LNAME TAG lname_std
  IDX ON LNAME TAG lname_bubble BUBBLE
  IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC
```

Notes:

```text
IDX with no arguments prints help/usage.
  IDX is memory-only and does not write .inx files.
  IDX does not participate in SET ORDER, REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.
  Use INDEX for persistent index files.
  SORT algorithms currently include STD and BUBBLE.
```

Related:

```text
INDEX
  SET ORDER
  REINDEX
```

Source comments:

```text
src/cli/cmd_idx.cpp
IDX is the EDU IDX command surface: a memory-only educational index lab.
It is intentionally orthogonal to persistent index families.
Supported Phase 1 commands:
  IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]
  IDX LIST
  IDX DROP <tag>
  IDX DROP ALL
  IDX HELP
IDX does not write .inx files and does not participate in SET ORDER,
REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.
```

---

### IDX

Source: `src/edu/edu_idx.cpp`  
Owner: `EDU|IDX_BACKEND`  
Category: `education-index-helper`  
Status: `backend-helper`  
Effect: `in-memory-index-support`  
Mutates: `in-memory-index-state`  
Usage access: `owned-by cmd_idx.cpp`  

Purpose:

Backend/helper implementation for the educational memory-only IDX command.

Usage contract:

```text
Runtime IDX command behavior and usage are owned by src/cli/cmd_idx.cpp.
  This file provides dottalk::edu_idx support functions and should not define
  a second command surface.
```

Notes:

```text
Keep command dispatch and usage text centralized in cmd_idx.cpp to avoid
  drift between the shell command and backend helper.
```

---

### IDX

Source: `x64base/src/cli/cmd_idx.cpp`  
Owner: `DOT|IDX`  
Category: `education`  
Status: `supported`  
Effect: `mixed`  
Mutates: `edu-idx-memory`  
Usage access: `IDX USAGE`  

Purpose:

Memory-only educational index lab for teaching sorting and index concepts
  without writing persistent INX/CNX/CDX files.

Usage contract:

```text
IDX
  IDX USAGE
  IDX ON <field|#n> TAG <name>
  IDX ON <field|#n> TAG <name> SORT <algo>
  IDX ON <field|#n> TAG <name> <algo>
  IDX ON <field|#n> TAG <name> ASC
  IDX ON <field|#n> TAG <name> DESC
  IDX LIST
  IDX DROP <tag>
  IDX DROP ALL
```

Examples:

```text
IDX ON LNAME TAG lname_std
  IDX ON LNAME TAG lname_bubble BUBBLE
  IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC
```

Notes:

```text
IDX with no arguments prints help/usage.
  IDX is memory-only and does not write .inx files.
  IDX does not participate in SET ORDER, REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.
  Use INDEX for persistent index files.
  SORT algorithms currently include STD and BUBBLE.
```

Related:

```text
INDEX
  SET ORDER
  REINDEX
```

Source comments:

```text
src/cli/cmd_idx.cpp
IDX is the EDU IDX command surface: a memory-only educational index lab.
It is intentionally orthogonal to persistent index families.
Supported Phase 1 commands:
  IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]
  IDX LIST
  IDX DROP <tag>
  IDX DROP ALL
  IDX HELP
IDX does not write .inx files and does not participate in SET ORDER,
REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.
```

---

### IDX

Source: `x64base/src/edu/edu_idx.cpp`  
Owner: `EDU|IDX_BACKEND`  
Category: `education-index-helper`  
Status: `backend-helper`  
Effect: `in-memory-index-support`  
Mutates: `in-memory-index-state`  
Usage access: `owned-by cmd_idx.cpp`  

Purpose:

Backend/helper implementation for the educational memory-only IDX command.

Usage contract:

```text
Runtime IDX command behavior and usage are owned by src/cli/cmd_idx.cpp.
  This file provides dottalk::edu_idx support functions and should not define
  a second command surface.
```

Notes:

```text
Keep command dispatch and usage text centralized in cmd_idx.cpp to avoid
  drift between the shell command and backend helper.
```

---

### IMAGE

Source: `src/cli/cmd_image_display.cpp`  
Owner: `DOT|IMAGE`  
Category: `shell`  
Status: `supported`  
Effect: `mixed`  
Mutates: `external-viewer`  
Usage access: `IMAGE USAGE`  

Purpose:

Inspect image file metadata or open a supported image file in the operating
  system viewer.

Usage contract:

```text
IMAGE USAGE
  IMAGE <file>
  IMAGE INFO <file>
```

Notes:

```text
IMAGE with no arguments prints usage.
  IMAGE USAGE prints usage and does not open a viewer.
  IMAGE INFO <file> prints file extension, size, and recognized-image status.
  IMAGE <file> opens the OS viewer on Windows.
  Non-Windows viewer launch is currently not implemented.
  IMAGE does not mutate table data.
```

Related:

```text
WEB
  BANG
```

---

### IMAGE

Source: `x64base/src/cli/cmd_image_display.cpp`  
Owner: `DOT|IMAGE`  
Category: `shell`  
Status: `supported`  
Effect: `mixed`  
Mutates: `external-viewer`  
Usage access: `IMAGE USAGE`  

Purpose:

Inspect image file metadata or open a supported image file in the operating
  system viewer.

Usage contract:

```text
IMAGE USAGE
  IMAGE <file>
  IMAGE INFO <file>
```

Notes:

```text
IMAGE with no arguments prints usage.
  IMAGE USAGE prints usage and does not open a viewer.
  IMAGE INFO <file> prints file extension, size, and recognized-image status.
  IMAGE <file> opens the OS viewer on Windows.
  Non-Windows viewer launch is currently not implemented.
  IMAGE does not mutate table data.
```

Related:

```text
WEB
  BANG
```

---

### IMPORT

Source: `src/cli/cmd_import.cpp`  
Owner: `DOT|IMPORT`  
Category: `io`  
Status: `supported`  
Effect: `import`  
Mutates: `table-data cursor`  
Usage access: `IMPORT USAGE`  

Purpose:

Import records from a CSV file into the current open table by matching CSV
  headers to field names case-insensitively.

Usage contract:

```text
IMPORT USAGE
  IMPORT <csvfile>
```

Notes:

```text
IMPORT requires an open table except for IMPORT USAGE.
  IMPORT appends .csv to the file name when the extension is omitted.
  The first CSV row is interpreted as headers.
  Headers are mapped to current table fields case-insensitively.
  Each data row appends a blank record, sets mapped fields, and writes the record.
  Unmapped CSV columns are ignored.
  IMPORT mutates table data by appending records.
```

Related:

```text
EXPORT
  APPEND
  APPEND_BLANK
  DDL
```

---

### IMPORT

Source: `x64base/src/cli/cmd_import.cpp`  
Owner: `DOT|IMPORT`  
Category: `io`  
Status: `supported`  
Effect: `import`  
Mutates: `table-data cursor`  
Usage access: `IMPORT USAGE`  

Purpose:

Import records from a CSV file into the current open table by matching CSV
  headers to field names case-insensitively.

Usage contract:

```text
IMPORT USAGE
  IMPORT <csvfile>
```

Notes:

```text
IMPORT requires an open table except for IMPORT USAGE.
  IMPORT appends .csv to the file name when the extension is omitted.
  The first CSV row is interpreted as headers.
  Headers are mapped to current table fields case-insensitively.
  Each data row appends a blank record, sets mapped fields, and writes the record.
  Unmapped CSV columns are ignored.
  IMPORT mutates table data by appending records.
```

Related:

```text
EXPORT
  APPEND
  APPEND_BLANK
  DDL
```

---

### IMPORTSQL / EXPORTSQL

Source: `src/cli/cmd_importsql.cpp`  
Owner: `DOT|IMPORTSQL`  
Category: `import-export`  
Status: `supported-stub-mixed`  
Effect: `import-export-preview-create`  
Mutates: `filesystem-or-table depending-on-subcommand`  
Usage access: `IMPORTSQL USAGE; EXPORTSQL USAGE`  

Purpose:

Preview, validate, infer schema, create/import table data from delimited
  files, and expose EXPORTSQL preview/file hooks.

Usage contract:

```text
IMPORTSQL USAGE
  IMPORTSQL PREVIEW <file> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL VALIDATE <file> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL SCHEMA <file> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL CREATE <file> TO <table> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL FILE <file> TO <table> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL MAP <subcommand> <mapfile>
  EXPORTSQL USAGE
  EXPORTSQL PREVIEW <table>
  EXPORTSQL FILE <table> TO <file>
```

Examples:

```text
IMPORTSQL PREVIEW data\students.psv
  IMPORTSQL VALIDATE data\students.csv DELIM COMMA
  IMPORTSQL CREATE data\students.psv TO students
  IMPORTSQL FILE data\students.psv TO students
  EXPORTSQL PREVIEW students
  EXPORTSQL FILE students TO tmp\students.sql
```

Notes:

```text
IMPORTSQL/EXPORTSQL USAGE returns before file/table work.
  IMPORTSQL PREVIEW/VALIDATE/SCHEMA read input files.
  IMPORTSQL CREATE/FILE may create tables and import records.
  EXPORTSQL hooks are currently preview/file command surfaces.
```

Related:

```text
USE
  COPY
  SQL
```

---

### IMPORTSQL / EXPORTSQL

Source: `x64base/src/cli/cmd_importsql.cpp`  
Owner: `DOT|IMPORTSQL`  
Category: `import-export`  
Status: `supported-stub-mixed`  
Effect: `import-export-preview-create`  
Mutates: `filesystem-or-table depending-on-subcommand`  
Usage access: `IMPORTSQL USAGE; EXPORTSQL USAGE`  

Purpose:

Preview, validate, infer schema, create/import table data from delimited
  files, and expose EXPORTSQL preview/file hooks.

Usage contract:

```text
IMPORTSQL USAGE
  IMPORTSQL PREVIEW <file> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL VALIDATE <file> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL SCHEMA <file> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL CREATE <file> TO <table> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL FILE <file> TO <table> [DELIM PIPE|TAB|COMMA]
  IMPORTSQL MAP <subcommand> <mapfile>
  EXPORTSQL USAGE
  EXPORTSQL PREVIEW <table>
  EXPORTSQL FILE <table> TO <file>
```

Examples:

```text
IMPORTSQL PREVIEW data\students.psv
  IMPORTSQL VALIDATE data\students.csv DELIM COMMA
  IMPORTSQL CREATE data\students.psv TO students
  IMPORTSQL FILE data\students.psv TO students
  EXPORTSQL PREVIEW students
  EXPORTSQL FILE students TO tmp\students.sql
```

Notes:

```text
IMPORTSQL/EXPORTSQL USAGE returns before file/table work.
  IMPORTSQL PREVIEW/VALIDATE/SCHEMA read input files.
  IMPORTSQL CREATE/FILE may create tables and import records.
  EXPORTSQL hooks are currently preview/file command surfaces.
```

Related:

```text
USE
  COPY
  SQL
```

---

### INDEX

Source: `src/cli/cmd_index.cpp`  
Owner: `DOT|INDEX`  
Category: `index`  
Status: `supported`  
Effect: `create`  
Mutates: `index-file filesystem order-metadata`  
Usage access: `INDEX USAGE`  

Purpose:

Build an INX index file from the current table using a field key,
  tag/file name, optional direction, and optional INX format.

Usage contract:

```text
INDEX USAGE
  INDEX ON <field> TAG <name>
  INDEX ON <field> TAG <name> ASC
  INDEX ON <field> TAG <name> DESC
  INDEX ON <field> TAG <name> 1INX
  INDEX ON <field> TAG <name> 2INX
  INDEX ON <field> TAG <name> ASC 1INX
  INDEX ON <field> TAG <name> DESC 2INX
```

Examples:

```text
INDEX ON LNAME TAG students
  INDEX ON LNAME TAG students DESC
  INDEX ON LNAME TAG students ASC 1INX
  INDEX ON LNAME TAG students DESC 2INX
```

Notes:

```text
INDEX requires an open table except for INDEX USAGE, INDEX HELP, and INDEX question-mark.
  Deleted records are excluded.
  Default direction is ASC.
  Default output format is 2INX, matching REINDEX.
  Optional direction and format tokens may appear in either order.
  Field-number tokens are also accepted by the parser, but omitted from mineable usage rows because hash syntax is a source-comment marker.
  2INX uses fixed-length keys, uppercases character fields, and writes a pos-by-recno table.
  TAG must name an INX file target; non-.inx extensions are refused.
  INDEX writes an index file through the INDEXES path resolver and does not mutate table records.
```

Related:

```text
REINDEX
  SET INDEX
  SET ORDER
  CDX
  CNX
```

Source comments:

```text
- Default output format: 2INX (matches REINDEX).
  - Optional direction token selects ASC or DESC.
  - Optional format token selects 1INX or 2INX.
Notes:
  - Deleted records are excluded (matches REINDEX).
  - 2INX uses fixed-length keys (field length), uppercased for character fields,
    and includes a pos-by-recno table for fast navigation.
Examples:
  INDEX ON LNAME TAG students
  INDEX ON LNAME TAG students DESC
  INDEX ON #2 TAG students ASC 1INX
  INDEX ON LNAME TAG students DESC 2INX
```

---

### INDEX

Source: `x64base/src/cli/cmd_index.cpp`  
Owner: `DOT|INDEX`  
Category: `index`  
Status: `supported`  
Effect: `create`  
Mutates: `index-file filesystem order-metadata`  
Usage access: `INDEX USAGE`  

Purpose:

Build an INX index file from the current table using a field key,
  tag/file name, optional direction, and optional INX format.

Usage contract:

```text
INDEX USAGE
  INDEX ON <field> TAG <name>
  INDEX ON <field> TAG <name> ASC
  INDEX ON <field> TAG <name> DESC
  INDEX ON <field> TAG <name> 1INX
  INDEX ON <field> TAG <name> 2INX
  INDEX ON <field> TAG <name> ASC 1INX
  INDEX ON <field> TAG <name> DESC 2INX
```

Examples:

```text
INDEX ON LNAME TAG students
  INDEX ON LNAME TAG students DESC
  INDEX ON LNAME TAG students ASC 1INX
  INDEX ON LNAME TAG students DESC 2INX
```

Notes:

```text
INDEX requires an open table except for INDEX USAGE, INDEX HELP, and INDEX question-mark.
  Deleted records are excluded.
  Default direction is ASC.
  Default output format is 2INX, matching REINDEX.
  Optional direction and format tokens may appear in either order.
  Field-number tokens are also accepted by the parser, but omitted from mineable usage rows because hash syntax is a source-comment marker.
  2INX uses fixed-length keys, uppercases character fields, and writes a pos-by-recno table.
  TAG must name an INX file target; non-.inx extensions are refused.
  INDEX writes an index file through the INDEXES path resolver and does not mutate table records.
```

Related:

```text
REINDEX
  SET INDEX
  SET ORDER
  CDX
  CNX
```

Source comments:

```text
- Default output format: 2INX (matches REINDEX).
  - Optional direction token selects ASC or DESC.
  - Optional format token selects 1INX or 2INX.
Notes:
  - Deleted records are excluded (matches REINDEX).
  - 2INX uses fixed-length keys (field length), uppercased for character fields,
    and includes a pos-by-recno table for fast navigation.
Examples:
  INDEX ON LNAME TAG students
  INDEX ON LNAME TAG students DESC
  INDEX ON #2 TAG students ASC 1INX
  INDEX ON LNAME TAG students DESC 2INX
```

---

### INDEXSEEK

Source: `src/cli/cmd_indexseek.cpp`  
Owner: `DOT|INDEXSEEK`  
Category: `navigation`  
Status: `supported`  
Effect: `seek`  
Mutates: `cursor-temporary`  
Usage access: `INDEXSEEK USAGE`  

Purpose:

Return the record number for a value using active CDX/LMDB order or legacy
  INX fallback, restoring the caller's cursor.

Usage contract:

```text
INDEXSEEK USAGE
  INDEXSEEK <value>
  INDEXSEEK <value> SOFT
  INDEXSEEK <value> TAG <tag-or-path>
  INDEXSEEK <value> SOFT TAG <tag-or-path>
```

Examples:

```text
INDEXSEEK "TAYLOR"
  INDEXSEEK "TAYLOR" SOFT
  INDEXSEEK "TAYLOR" TAG students.cdx
```

Notes:

```text
INDEXSEEK USAGE works without an open table.
  INDEXSEEK prints INDEXSEEK(): <recno> and restores the cursor best-effort.
  Active CDX/LMDB order is preferred when available; legacy INX fallback remains supported.
  SOFT returns the first >= key when an exact match is not found.
```

Related:

```text
SEEK
  FIND
  SET ORDER
```

Source comments:

```text
- TAG <file.cdx|path\file.cdx|file.cdx.d>: open that CDX/LMDB container and use the
  requested/current tag when possible.
- Legacy INX fallback remains supported ("1INX" / "2INX").
Output:
  INDEXSEEK(): <recno>
Behavior:
- Exact hit => matching recno
- Miss => 0, unless SOFT, where first >= key (by ordered scan) is returned.
Notes:
- For CDX/LMDB, this implementation uses the public cursor API actually present
  in the tree: first/last/next/prev.
- It does not move the caller's record pointer.
```

---

### INDEXSEEK

Source: `x64base/src/cli/cmd_indexseek.cpp`  
Owner: `DOT|INDEXSEEK`  
Category: `navigation`  
Status: `supported`  
Effect: `seek`  
Mutates: `cursor-temporary`  
Usage access: `INDEXSEEK USAGE`  

Purpose:

Return the record number for a value using active CDX/LMDB order or legacy
  INX fallback, restoring the caller's cursor.

Usage contract:

```text
INDEXSEEK USAGE
  INDEXSEEK <value>
  INDEXSEEK <value> SOFT
  INDEXSEEK <value> TAG <tag-or-path>
  INDEXSEEK <value> SOFT TAG <tag-or-path>
```

Examples:

```text
INDEXSEEK "TAYLOR"
  INDEXSEEK "TAYLOR" SOFT
  INDEXSEEK "TAYLOR" TAG students.cdx
```

Notes:

```text
INDEXSEEK USAGE works without an open table.
  INDEXSEEK prints INDEXSEEK(): <recno> and restores the cursor best-effort.
  Active CDX/LMDB order is preferred when available; legacy INX fallback remains supported.
  SOFT returns the first >= key when an exact match is not found.
```

Related:

```text
SEEK
  FIND
  SET ORDER
```

Source comments:

```text
- TAG <file.cdx|path\file.cdx|file.cdx.d>: open that CDX/LMDB container and use the
  requested/current tag when possible.
- Legacy INX fallback remains supported ("1INX" / "2INX").
Output:
  INDEXSEEK(): <recno>
Behavior:
- Exact hit => matching recno
- Miss => 0, unless SOFT, where first >= key (by ordered scan) is returned.
Notes:
- For CDX/LMDB, this implementation uses the public cursor API actually present
  in the tree: first/last/next/prev.
- It does not move the caller's record pointer.
```

---

### INIT

Source: `src/cli/cmd_init.cpp`  
Owner: `DOT|INIT`  
Category: `script`  
Status: `supported`  
Effect: `initialize`  
Mutates: `path-state lock-state delegates-command-effects`  
Usage access: `INIT USAGE`  

Purpose:

Initialize runtime paths, cleanup stale locks, and run system/user init
  scripts from the executable directory.

Usage contract:

```text
INIT
  INIT USAGE
```

Notes:

```text
INIT with no arguments initializes default paths when needed and reports path slots.
  INIT cleans stale DBF locks best-effort.
  INIT runs dottalkpp.ini and init.ini from the executable directory when present.
  INIT USAGE prints usage and does not initialize paths, cleanup locks, or run scripts.
  Script commands run through the shell command executor and may have their own side effects.
```

Related:

```text
SHUTDOWN
  SETPATH
  DOTSCRIPT
```

Source comments:

```text
src/cli/cmd_init.cpp
Initializes runtime environment before the REPL (paths, locks, init scripts)
```

---

### INIT

Source: `x64base/src/cli/cmd_init.cpp`  
Owner: `DOT|INIT`  
Category: `script`  
Status: `supported`  
Effect: `initialize`  
Mutates: `path-state lock-state delegates-command-effects`  
Usage access: `INIT USAGE`  

Purpose:

Initialize runtime paths, cleanup stale locks, and run system/user init
  scripts from the executable directory.

Usage contract:

```text
INIT
  INIT USAGE
```

Notes:

```text
INIT with no arguments initializes default paths when needed and reports path slots.
  INIT cleans stale DBF locks best-effort.
  INIT runs dottalkpp.ini and init.ini from the executable directory when present.
  INIT USAGE prints usage and does not initialize paths, cleanup locks, or run scripts.
  Script commands run through the shell command executor and may have their own side effects.
```

Related:

```text
SHUTDOWN
  SETPATH
  DOTSCRIPT
```

Source comments:

```text
src/cli/cmd_init.cpp
Initializes runtime environment before the REPL (paths, locks, init scripts)
```

---

### INSERT

Source: `src/cli/cmd_sql_insert.cpp`  
Owner: `DOT|INSERT`  
Category: `sql`  
Status: `supported`  
Effect: `insert-record`  
Mutates: `table-data`  
Usage access: `INSERT USAGE`  

Purpose:

Insert a new record into the current DBF work area using SQL-like syntax.

Usage contract:

```text
INSERT USAGE
  INSERT (<field-list>) VALUES (<value-list>)
  INSERT <field>=<value> [, <field>=<value> ...]
```

Examples:

```text
INSERT (SID,LNAME,FNAME) VALUES (999,"SMITH","JANE")
  INSERT SID=999, LNAME="SMITH", FNAME="JANE"
```

Notes:

```text
INSERT USAGE prints usage before open-table checks.
  INSERT appends a new record and writes supplied field values.
  Field/value count must match in VALUES form.
```

Related:

```text
SQL
  UPDATE
  SQLERASE
```

---

### INSERT

Source: `x64base/src/cli/cmd_sql_insert.cpp`  
Owner: `DOT|INSERT`  
Category: `sql`  
Status: `supported`  
Effect: `insert-record`  
Mutates: `table-data`  
Usage access: `INSERT USAGE`  

Purpose:

Insert a new record into the current DBF work area using SQL-like syntax.

Usage contract:

```text
INSERT USAGE
  INSERT (<field-list>) VALUES (<value-list>)
  INSERT <field>=<value> [, <field>=<value> ...]
```

Examples:

```text
INSERT (SID,LNAME,FNAME) VALUES (999,"SMITH","JANE")
  INSERT SID=999, LNAME="SMITH", FNAME="JANE"
```

Notes:

```text
INSERT USAGE prints usage before open-table checks.
  INSERT appends a new record and writes supplied field values.
  Field/value count must match in VALUES form.
```

Related:

```text
SQL
  UPDATE
  SQLERASE
```

---

### LAST

Source: `src/cli/cmd_last.cpp`  
Owner: `DOT|LAST`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `LAST USAGE`  

Purpose:

Move the current work-area cursor to the last visible/logical record.

Usage contract:

```text
LAST
  LAST USAGE
```

Notes:

```text
LAST with no arguments moves to the last visible/logical record.
  LAST requires an open table except for LAST USAGE.
  LAST uses the logical_nav last_recno helper.
  LAST mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

Source comments:

```text
src/cli/cmd_last.cpp
LAST = last visible record in current logical view
(active order + filter visibility).
```

---

### LAST

Source: `x64base/src/cli/cmd_last.cpp`  
Owner: `DOT|LAST`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `LAST USAGE`  

Purpose:

Move the current work-area cursor to the last visible/logical record.

Usage contract:

```text
LAST
  LAST USAGE
```

Notes:

```text
LAST with no arguments moves to the last visible/logical record.
  LAST requires an open table except for LAST USAGE.
  LAST uses the logical_nav last_recno helper.
  LAST mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

Source comments:

```text
src/cli/cmd_last.cpp
LAST = last visible record in current logical view
(active order + filter visibility).
```

---

### LIST

Source: `src/cli/cmd_list.cpp`  
Owner: `DOT|LIST`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `LIST USAGE`  

Purpose:

Display rows from the current work area using classic LIST-style output,
  honoring active order/index state and optional filtering modes.

Usage contract:

```text
LIST
  LIST USAGE
  LIST TOP
  LIST BOTTOM
  LIST ALL
  LIST <limit>
  LIST DELETED
  LIST FOR <predicate>
  LIST TOP <limit>
  LIST BOTTOM <limit>
```

Notes:

```text
LIST requires an open table except for LIST USAGE.
  LIST with no arguments displays from the current cursor position.
  LIST ALL starts at the top and removes the default output limit.
  TOP and BOTTOM move to an endpoint before listing.
  DELETED selects deleted records using physical traversal.
  FOR applies an expression predicate after normalization.
  Active order/index state is honored when possible; LIST falls back to physical order with a note.
  LIST is read-only for table data and restores cursor position best-effort.
```

Related:

```text
SMARTLIST
  SET ORDER
  SET INDEX
  COUNT
  LOCATE
```

Source comments:

```text
src/cli/cmd_list.cpp
```

---

### LIST

Source: `x64base/src/cli/cmd_list.cpp`  
Owner: `DOT|LIST`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `LIST USAGE`  

Purpose:

Display rows from the current work area using classic LIST-style output,
  honoring active order/index state and optional filtering modes.

Usage contract:

```text
LIST
  LIST USAGE
  LIST TOP
  LIST BOTTOM
  LIST ALL
  LIST <limit>
  LIST DELETED
  LIST FOR <predicate>
  LIST TOP <limit>
  LIST BOTTOM <limit>
```

Notes:

```text
LIST requires an open table except for LIST USAGE.
  LIST with no arguments displays from the current cursor position.
  LIST ALL starts at the top and removes the default output limit.
  TOP and BOTTOM move to an endpoint before listing.
  DELETED selects deleted records using physical traversal.
  FOR applies an expression predicate after normalization.
  Active order/index state is honored when possible; LIST falls back to physical order with a note.
  LIST is read-only for table data and restores cursor position best-effort.
```

Related:

```text
SMARTLIST
  SET ORDER
  SET INDEX
  COUNT
  LOCATE
```

Source comments:

```text
src/cli/cmd_list.cpp
```

---

### LIST_LMDB

Source: `src/cli/cmd_list_lmdb.cpp`  
Owner: `DOT|LIST_LMDB`  
Category: `index`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor order-state index-backend`  
Usage access: `LIST_LMDB USAGE`  

Purpose:

Enumerate records in active LMDB/CDX index order without in-memory sorting.

Usage contract:

```text
LIST_LMDB
  LIST_LMDB USAGE
  LIST_LMDB ALL
  LIST_LMDB <limit>
  LIST_LMDB DELETED
  LIST_LMDB NODELETED
  LIST_LMDB ASC
  LIST_LMDB DESC
  LIST_LMDB <tag>
  LL
  LL USAGE
  LL ALL
  LL <limit>
```

Notes:

```text
LIST_LMDB with no arguments lists records through the active LMDB order.
  LL is a shorthand alias for LIST_LMDB.
  Tokens are accepted in any order.
  A supplied tag becomes the active tag for the current area and updates order state.
  ASC and DESC override display direction for the command.
  LIST_LMDB requires an open table and active LMDB order except for LIST_LMDB USAGE.
  LIST_LMDB restores the original cursor best-effort after listing.
```

Related:

```text
LMDB
  SETLMDB
  SET ORDER
  LIST
```

Source comments:

```text
src/cli/cmd_list_lmdb.cpp
LIST_LMDB / LL
  Enumerates records in *LMDB index order* (no in-memory sorting).
Contract:
  DbArea -> IndexManager -> CdxBackend -> LMDB env
Usage (tokens in any order):
  LL [ALL] [<limit>] [DELETED|NODELETED] [<TAG>]
  LIST_LMDB ...same...
Notes:
- If <TAG> is provided, it becomes the active tag for this area (and updates orderstate).
- Descending order is supported: if the area's order is DESC, we iterate cursor via last/prev.
```

---

### LIST_LMDB

Source: `x64base/src/cli/cmd_list_lmdb.cpp`  
Owner: `DOT|LIST_LMDB`  
Category: `index`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor order-state index-backend`  
Usage access: `LIST_LMDB USAGE`  

Purpose:

Enumerate records in active LMDB/CDX index order without in-memory sorting.

Usage contract:

```text
LIST_LMDB
  LIST_LMDB USAGE
  LIST_LMDB ALL
  LIST_LMDB <limit>
  LIST_LMDB DELETED
  LIST_LMDB NODELETED
  LIST_LMDB ASC
  LIST_LMDB DESC
  LIST_LMDB <tag>
  LL
  LL USAGE
  LL ALL
  LL <limit>
```

Notes:

```text
LIST_LMDB with no arguments lists records through the active LMDB order.
  LL is a shorthand alias for LIST_LMDB.
  Tokens are accepted in any order.
  A supplied tag becomes the active tag for the current area and updates order state.
  ASC and DESC override display direction for the command.
  LIST_LMDB requires an open table and active LMDB order except for LIST_LMDB USAGE.
  LIST_LMDB restores the original cursor best-effort after listing.
```

Related:

```text
LMDB
  SETLMDB
  SET ORDER
  LIST
```

Source comments:

```text
src/cli/cmd_list_lmdb.cpp
LIST_LMDB / LL
  Enumerates records in *LMDB index order* (no in-memory sorting).
Contract:
  DbArea -> IndexManager -> CdxBackend -> LMDB env
Usage (tokens in any order):
  LL [ALL] [<limit>] [DELETED|NODELETED] [<TAG>]
  LIST_LMDB ...same...
Notes:
- If <TAG> is provided, it becomes the active tag for this area (and updates orderstate).
- Descending order is supported: if the area's order is DESC, we iterate cursor via last/prev.
```

---

### LMDB

Source: `src/cli/cmd_lmdb.cpp`  
Owner: `DOT|LMDB`  
Category: `index`  
Status: `developer`  
Effect: `mixed`  
Mutates: `index-backend order-state cursor`  
Usage access: `LMDB USAGE`  

Purpose:

Inspect and control the per-area LMDB backed CDX index backend through the
  current DbArea IndexManager.

Usage contract:

```text
LMDB USAGE
  LMDB INFO
  LMDB OPEN <container.cdx>
  LMDB OPEN <envdir.cdx.d>
  LMDB OPEN <stem>
  LMDB USE <tag>
  LMDB SEEK <key>
  LMDB DUMP
  LMDB DUMP <max>
  LMDB SCAN <low> <high>
  LMDB CLOSE
```

Notes:

```text
LMDB is a thin wrapper over the current area IndexManager and CDX backend.
  LMDB does not use LMDB_UTIL or any shared global LMDB environment.
  Bare stems are resolved through the INDEXES path slot.
  OPEN attaches the CDX container and updates legacy order state.
  USE selects an active tag and updates legacy active-tag state.
  SEEK searches the selected tag and reports the matching record number.
  DUMP and SCAN inspect the selected tag.
  CLOSE closes the current area index manager and clears order state.
  LMDB mutates index/order session state but not table records.
```

Related:

```text
CDX
  CNX
  SET INDEX
  SET ORDER
  LMDBDUMP
  LMDB_UTIL
```

Source comments:

```text
File: src/cli/cmd_lmdb.cpp
LMDB command (per-area, no global LMDB env).
Design:
  DbArea -> IndexManager -> CdxBackend -> MDB_env*
This command is intentionally a thin wrapper over DbArea::indexManager().
It does not touch LMDB_UTIL or any shared singleton state.
```

---

### LMDB

Source: `x64base/src/cli/cmd_lmdb.cpp`  
Owner: `DOT|LMDB`  
Category: `index`  
Status: `developer`  
Effect: `mixed`  
Mutates: `index-backend order-state cursor`  
Usage access: `LMDB USAGE`  

Purpose:

Inspect and control the per-area LMDB backed CDX index backend through the
  current DbArea IndexManager.

Usage contract:

```text
LMDB USAGE
  LMDB INFO
  LMDB OPEN <container.cdx>
  LMDB OPEN <envdir.cdx.d>
  LMDB OPEN <stem>
  LMDB USE <tag>
  LMDB SEEK <key>
  LMDB DUMP
  LMDB DUMP <max>
  LMDB SCAN <low> <high>
  LMDB CLOSE
```

Notes:

```text
LMDB is a thin wrapper over the current area IndexManager and CDX backend.
  LMDB does not use LMDB_UTIL or any shared global LMDB environment.
  Bare stems are resolved through the INDEXES path slot.
  OPEN attaches the CDX container and updates legacy order state.
  USE selects an active tag and updates legacy active-tag state.
  SEEK searches the selected tag and reports the matching record number.
  DUMP and SCAN inspect the selected tag.
  CLOSE closes the current area index manager and clears order state.
  LMDB mutates index/order session state but not table records.
```

Related:

```text
CDX
  CNX
  SET INDEX
  SET ORDER
  LMDBDUMP
  LMDB_UTIL
```

Source comments:

```text
File: src/cli/cmd_lmdb.cpp
LMDB command (per-area, no global LMDB env).
Design:
  DbArea -> IndexManager -> CdxBackend -> MDB_env*
This command is intentionally a thin wrapper over DbArea::indexManager().
It does not touch LMDB_UTIL or any shared singleton state.
```

---

### LMDBDUMP

Source: `src/cli/cmd_lmdb_dump.cpp`  
Owner: `DOT|LMDBDUMP`  
Category: `diagnostics`  
Status: `developer`  
Effect: `inspect`  
Mutates: `none`  
Usage access: `LMDBDUMP USAGE`  

Purpose:

Open an LMDB environment read-only and dump keys and values for diagnostics,
  with optional named DB, grep, limit, and start-key controls.

Usage contract:

```text
LMDBDUMP USAGE
  LMDBDUMP <env_path>
  LMDBDUMP <env_path> --db <name>
  LMDBDUMP <env_path> -db <name>
  LMDBDUMP <env_path> --grep <ascii>
  LMDBDUMP <env_path> -grep <ascii>
  LMDBDUMP <env_path> --trydb
  LMDBDUMP <env_path> --limit <n>
  LMDBDUMP <env_path> --start <key>
  LMDBDUMP <env_path> --starthex <hex>
```

Examples:

```text
LMDBDUMP indexes\students.cdx.d
  LMDBDUMP indexes\students.cdx.d --trydb
  LMDBDUMP indexes\students.cdx.d --grep MILLER --limit 50
  LMDBDUMP indexes\students.cdx.d --db lname --start M --limit 200
```

Notes:

```text
LMDBDUMP opens the supplied LMDB environment read-only.
  LMDBDUMP does not depend on the xindex backend or current work area.
  --start treats the key as ASCII unless it begins with 0x.
  --starthex accepts hex bytes.
  --trydb scans main DB keys and probes named DB candidates.
  LMDBDUMP is diagnostic and does not mutate table or index data.
```

Related:

```text
LMDB
  CDX
  CNX
```

Source comments:

```text
[--limit <N>]
      [--start <key>]        (ASCII unless prefixed with 0x...)
      [--starthex <hex...>]  (hex bytes; spaces OK)
Examples:
  LMDBDUMP indexes\students.cdx.d
  LMDBDUMP indexes\students.cdx.d --trydb
  LMDBDUMP indexes\students.cdx.d --grep MILLER --limit 50
  LMDBDUMP indexes\students.cdx.d --db lname --start M --limit 200
  LMDBDUMP indexes\students.cdx.d --starthex 4d 49 4c 4c 45 52
Notes:
- Standalone: opens LMDB env read-only from <env_path>. Does NOT depend on your xindex backend.
- Wire from your existing cmd_LMDB dispatcher (DO NOT define cmd_LMDB here).
```

---

### LMDBDUMP

Source: `x64base/src/cli/cmd_lmdb_dump.cpp`  
Owner: `DOT|LMDBDUMP`  
Category: `diagnostics`  
Status: `developer`  
Effect: `inspect`  
Mutates: `none`  
Usage access: `LMDBDUMP USAGE`  

Purpose:

Open an LMDB environment read-only and dump keys and values for diagnostics,
  with optional named DB, grep, limit, and start-key controls.

Usage contract:

```text
LMDBDUMP USAGE
  LMDBDUMP <env_path>
  LMDBDUMP <env_path> --db <name>
  LMDBDUMP <env_path> -db <name>
  LMDBDUMP <env_path> --grep <ascii>
  LMDBDUMP <env_path> -grep <ascii>
  LMDBDUMP <env_path> --trydb
  LMDBDUMP <env_path> --limit <n>
  LMDBDUMP <env_path> --start <key>
  LMDBDUMP <env_path> --starthex <hex>
```

Examples:

```text
LMDBDUMP indexes\students.cdx.d
  LMDBDUMP indexes\students.cdx.d --trydb
  LMDBDUMP indexes\students.cdx.d --grep MILLER --limit 50
  LMDBDUMP indexes\students.cdx.d --db lname --start M --limit 200
```

Notes:

```text
LMDBDUMP opens the supplied LMDB environment read-only.
  LMDBDUMP does not depend on the xindex backend or current work area.
  --start treats the key as ASCII unless it begins with 0x.
  --starthex accepts hex bytes.
  --trydb scans main DB keys and probes named DB candidates.
  LMDBDUMP is diagnostic and does not mutate table or index data.
```

Related:

```text
LMDB
  CDX
  CNX
```

Source comments:

```text
[--limit <N>]
      [--start <key>]        (ASCII unless prefixed with 0x...)
      [--starthex <hex...>]  (hex bytes; spaces OK)
Examples:
  LMDBDUMP indexes\students.cdx.d
  LMDBDUMP indexes\students.cdx.d --trydb
  LMDBDUMP indexes\students.cdx.d --grep MILLER --limit 50
  LMDBDUMP indexes\students.cdx.d --db lname --start M --limit 200
  LMDBDUMP indexes\students.cdx.d --starthex 4d 49 4c 4c 45 52
Notes:
- Standalone: opens LMDB env read-only from <env_path>. Does NOT depend on your xindex backend.
- Wire from your existing cmd_LMDB dispatcher (DO NOT define cmd_LMDB here).
```

---

### LMDB_UTIL

Source: `src/cli/cmd_lmdb_util.cpp`  
Owner: `DOT|LMDB_UTIL`  
Category: `diagnostics`  
Status: `deprecated`  
Effect: `report`  
Mutates: `none`  
Usage access: `LMDB_UTIL USAGE`  

Purpose:

Deprecated disabled LMDB utility command that points users to the per-area
  LMDB command.

Usage contract:

```text
LMDB_UTIL
  LMDB_UTIL USAGE
```

Notes:

```text
LMDB_UTIL is deprecated and disabled.
  LMDB_UTIL intentionally does not open LMDB environments or transactions.
  Use LMDB INFO, LMDB OPEN, LMDB USE, LMDB SEEK, LMDB DUMP, LMDB SCAN, and LMDB CLOSE instead.
  This avoids cross-area contamination and reader-slot conflicts.
```

Related:

```text
LMDB
  LMDBDUMP
  CDX
```

Source comments:

```text
The project has moved to the OO model:
  DbArea -> IndexManager -> CdxBackend -> MDB_env*
Use the per-area LMDB command instead:
  LMDB INFO
  LMDB OPEN <container.cdx | envdir.cdx.d | stem>
  LMDB USE  <TAG>
  LMDB SEEK <key>
  LMDB DUMP [<max>]
  LMDB SCAN <low> <high>
  LMDB CLOSE
This stub intentionally does NOT open any LMDB environments or transactions,
to avoid cross-area contamination and reader-slot conflicts.
```

---

### LMDB_UTIL

Source: `x64base/src/cli/cmd_lmdb_util.cpp`  
Owner: `DOT|LMDB_UTIL`  
Category: `diagnostics`  
Status: `deprecated`  
Effect: `report`  
Mutates: `none`  
Usage access: `LMDB_UTIL USAGE`  

Purpose:

Deprecated disabled LMDB utility command that points users to the per-area
  LMDB command.

Usage contract:

```text
LMDB_UTIL
  LMDB_UTIL USAGE
```

Notes:

```text
LMDB_UTIL is deprecated and disabled.
  LMDB_UTIL intentionally does not open LMDB environments or transactions.
  Use LMDB INFO, LMDB OPEN, LMDB USE, LMDB SEEK, LMDB DUMP, LMDB SCAN, and LMDB CLOSE instead.
  This avoids cross-area contamination and reader-slot conflicts.
```

Related:

```text
LMDB
  LMDBDUMP
  CDX
```

Source comments:

```text
The project has moved to the OO model:
  DbArea -> IndexManager -> CdxBackend -> MDB_env*
Use the per-area LMDB command instead:
  LMDB INFO
  LMDB OPEN <container.cdx | envdir.cdx.d | stem>
  LMDB USE  <TAG>
  LMDB SEEK <key>
  LMDB DUMP [<max>]
  LMDB SCAN <low> <high>
  LMDB CLOSE
This stub intentionally does NOT open any LMDB environments or transactions,
to avoid cross-area contamination and reader-slot conflicts.
```

---

### LOCATE

Source: `src/cli/cmd_locate.cpp`  
Owner: `DOT|LOCATE`  
Category: `navigation`  
Status: `supported`  
Effect: `locate`  
Mutates: `cursor locate-state continue-state`  
Usage access: `LOCATE USAGE`  

Purpose:

Locate the first record matching a predicate, using simple CDX fast-path
  when possible and selector-backed scanning otherwise.

Usage contract:

```text
LOCATE USAGE
  LOCATE FOR <expr>
  LOCATE <field> <op> <value>
```

Examples:

```text
LOCATE FOR LNAME = Smith
  LOCATE LNAME = Smith
  LOCATE FOR BALANCE > 100
```

Notes:

```text
LOCATE requires an open table except for LOCATE USAGE.
  LOCATE with no predicate shows usage.
  LOCATE clears previous LOCATE and CONTINUE bridge state before searching.
  Simple predicates on the active CDX tag may use the CDX fast path.
  Complex predicates are evaluated through the selector and expression path.
  LOCATE positions on the first matching record.
  LOCATE updates locate state and CONTINUE bridge state after a match.
  LOCATE is read-only for table data but mutates cursor/search state.
```

Related:

```text
CONTINUE
  FIND
  SEEK
  COUNT
  SET FILTER
```

Source comments:

```text
src/cli/cmd_locate.cpp
```

---

### LOCATE

Source: `x64base/src/cli/cmd_locate.cpp`  
Owner: `DOT|LOCATE`  
Category: `navigation`  
Status: `supported`  
Effect: `locate`  
Mutates: `cursor locate-state continue-state`  
Usage access: `LOCATE USAGE`  

Purpose:

Locate the first record matching a predicate, using simple CDX fast-path
  when possible and selector-backed scanning otherwise.

Usage contract:

```text
LOCATE USAGE
  LOCATE FOR <expr>
  LOCATE <field> <op> <value>
```

Examples:

```text
LOCATE FOR LNAME = Smith
  LOCATE LNAME = Smith
  LOCATE FOR BALANCE > 100
```

Notes:

```text
LOCATE requires an open table except for LOCATE USAGE.
  LOCATE with no predicate shows usage.
  LOCATE clears previous LOCATE and CONTINUE bridge state before searching.
  Simple predicates on the active CDX tag may use the CDX fast path.
  Complex predicates are evaluated through the selector and expression path.
  LOCATE positions on the first matching record.
  LOCATE updates locate state and CONTINUE bridge state after a match.
  LOCATE is read-only for table data but mutates cursor/search state.
```

Related:

```text
CONTINUE
  FIND
  SEEK
  COUNT
  SET FILTER
```

Source comments:

```text
src/cli/cmd_locate.cpp
```

---

### LOCK

Source: `src/cli/cmd_lock.cpp`  
Owner: `DOT|LOCK`  
Category: `concurrency`  
Status: `supported`  
Effect: `lock`  
Mutates: `lock-state`  
Usage access: `LOCK USAGE`  

Purpose:

Acquire record or table locks for the current table and inspect lock status
  or lock ownership.

Usage contract:

```text
LOCK USAGE
  LOCK
  LOCK <n>
  LOCK ALL
  LOCK TABLE
  LOCK STATUS
  LOCK WHO <n>
```

Notes:

```text
LOCK requires an open table except for LOCK USAGE.
  LOCK with no arguments locks the current record.
  LOCK <n> locks record n.
  LOCK ALL and LOCK TABLE lock the entire table.
  LOCK STATUS reports table and current-record lock state.
  LOCK WHO <n> reports the owner of record n when a lock is recorded.
  LOCK mutates lock state but does not mutate table data.
```

Related:

```text
UNLOCK
  DELETE
  COMMIT
```

Source comments:

```text
cmd_lock.cpp — owner-aware UI (works with the back-compat shims too)
```

---

### LOCK

Source: `x64base/src/cli/cmd_lock.cpp`  
Owner: `DOT|LOCK`  
Category: `concurrency`  
Status: `supported`  
Effect: `lock`  
Mutates: `lock-state`  
Usage access: `LOCK USAGE`  

Purpose:

Acquire record or table locks for the current table and inspect lock status
  or lock ownership.

Usage contract:

```text
LOCK USAGE
  LOCK
  LOCK <n>
  LOCK ALL
  LOCK TABLE
  LOCK STATUS
  LOCK WHO <n>
```

Notes:

```text
LOCK requires an open table except for LOCK USAGE.
  LOCK with no arguments locks the current record.
  LOCK <n> locks record n.
  LOCK ALL and LOCK TABLE lock the entire table.
  LOCK STATUS reports table and current-record lock state.
  LOCK WHO <n> reports the owner of record n when a lock is recorded.
  LOCK mutates lock state but does not mutate table data.
```

Related:

```text
UNLOCK
  DELETE
  COMMIT
```

Source comments:

```text
cmd_lock.cpp — owner-aware UI (works with the back-compat shims too)
```

---

### LOOP / ENDLOOP

Source: `src/cli/cmd_loop.cpp`  
Owner: `DOT|LOOP
DOT|ENDLOOP`  
Category: `script
script`  
Status: `supported
supported`  
Effect: `buffer
execute`  
Mutates: `loop-buffer loop-state
loop-buffer loop-state delegates-command-effects`  
Usage access: `LOOP USAGE
ENDLOOP USAGE`  

Purpose:

Start buffering commands for later replay by ENDLOOP, with optional quiet
  mode and numeric repetition labels.

  End the active LOOP block and replay buffered commands through the shell
  executor.

Usage contract:

```text
LOOP
  LOOP USAGE
  LOOP QUIET
  LOOP <n>
  LOOP <n> TIMES
  LOOP FOR <n>
  LOOP FOR <n> TIMES
  LOOP FOR <label>
  LOOP OVERRIDE <label>

  ENDLOOP
  ENDLOOP USAGE
```

Notes:

```text
LOOP with no arguments starts command buffering and replays once at ENDLOOP.
  LOOP <n>, LOOP <n> TIMES, and LOOP FOR <n> replay buffered commands n times.
  LOOP QUIET suppresses buffering and ENDLOOP status messages.
  LOOP FOR <label> stores a nonnumeric label and currently replays once.
  ENDLOOP executes buffered commands through the pluggable shell executor.
  The loop implementation skips buffered ENDLOOP lines during replay.
  Iteration count is clamped to the hard maximum when necessary.
  LOOP mutates script execution state and may indirectly mutate anything its buffered commands mutate.

  ENDLOOP with no arguments executes the active LOOP buffer.
  ENDLOOP requires an active LOOP block except for ENDLOOP USAGE.
  ENDLOOP clears active loop state before replay.
  ENDLOOP replays buffered commands through the registered loop executor.
  ENDLOOP reports when no LOOP is active.
  ENDLOOP may indirectly mutate data, session state, or files depending on buffered commands.
```

Related:

```text
ENDLOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL

  LOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL
```

Source comments:

```text
purpose: LOOP implementation with numeric repetition (N TIMES)
notes  :
  - LOOP
      buffer + replay once
  - LOOP <n>   | LOOP <n> TIMES
      buffer + replay n times
  - LOOP FOR <n> [TIMES]
      same as above (compat with "FOR" phrasing)
  - LOOP FOR <expr>
      currently acts as a label only if not numeric
  - hard default max iterations: 1000
============================================================================
```

---

### LOOP / ENDLOOP

Source: `x64base/src/cli/cmd_loop.cpp`  
Owner: `DOT|LOOP
DOT|ENDLOOP`  
Category: `script
script`  
Status: `supported
supported`  
Effect: `buffer
execute`  
Mutates: `loop-buffer loop-state
loop-buffer loop-state delegates-command-effects`  
Usage access: `LOOP USAGE
ENDLOOP USAGE`  

Purpose:

Start buffering commands for later replay by ENDLOOP, with optional quiet
  mode and numeric repetition labels.

  End the active LOOP block and replay buffered commands through the shell
  executor.

Usage contract:

```text
LOOP
  LOOP USAGE
  LOOP QUIET
  LOOP <n>
  LOOP <n> TIMES
  LOOP FOR <n>
  LOOP FOR <n> TIMES
  LOOP FOR <label>
  LOOP OVERRIDE <label>

  ENDLOOP
  ENDLOOP USAGE
```

Notes:

```text
LOOP with no arguments starts command buffering and replays once at ENDLOOP.
  LOOP <n>, LOOP <n> TIMES, and LOOP FOR <n> replay buffered commands n times.
  LOOP QUIET suppresses buffering and ENDLOOP status messages.
  LOOP FOR <label> stores a nonnumeric label and currently replays once.
  ENDLOOP executes buffered commands through the pluggable shell executor.
  The loop implementation skips buffered ENDLOOP lines during replay.
  Iteration count is clamped to the hard maximum when necessary.
  LOOP mutates script execution state and may indirectly mutate anything its buffered commands mutate.

  ENDLOOP with no arguments executes the active LOOP buffer.
  ENDLOOP requires an active LOOP block except for ENDLOOP USAGE.
  ENDLOOP clears active loop state before replay.
  ENDLOOP replays buffered commands through the registered loop executor.
  ENDLOOP reports when no LOOP is active.
  ENDLOOP may indirectly mutate data, session state, or files depending on buffered commands.
```

Related:

```text
ENDLOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL

  LOOP
  WHILE
  ENDWHILE
  UNTIL
  ENDUNTIL
```

Source comments:

```text
purpose: LOOP implementation with numeric repetition (N TIMES)
notes  :
  - LOOP
      buffer + replay once
  - LOOP <n>   | LOOP <n> TIMES
      buffer + replay n times
  - LOOP FOR <n> [TIMES]
      same as above (compat with "FOR" phrasing)
  - LOOP FOR <expr>
      currently acts as a label only if not numeric
  - hard default max iterations: 1000
============================================================================
```

---

### MAINT

Source: `src/cli/cmd_maint.cpp`  
Owner: `DOT|MAINT`  
Category: `maintenance`  
Status: `experimental`  
Mutates: `none`  

Purpose:

Inspect DotTalk++ maintenance lanes, cookbooks, status, and protected-system boundaries.

Usage contract:

```text
MAINT
MAINT USAGE
MAINT STATUS
MAINT LANES
MAINT COOKBOOK
MAINT BOUNDARY
MAINT BBOX
```

Related:

```text
BBOX
CMDHELP
DDICT
MANUAL
@dottalk.end
```

Source comments:

```text
cmd_maint.cpp
DotTalk++ native MAINT command
First-wave maintenance/SDLC inspection surface.
```

---

### MAINT

Source: `x64base/src/cli/cmd_maint.cpp`  
Owner: `DOT|MAINT`  
Category: `maintenance`  
Status: `experimental`  
Mutates: `none`  

Purpose:

Inspect DotTalk++ maintenance lanes, cookbooks, status, and protected-system boundaries.

Usage contract:

```text
MAINT
MAINT USAGE
MAINT STATUS
MAINT LANES
MAINT COOKBOOK
MAINT BOUNDARY
MAINT BBOX
```

Related:

```text
BBOX
CMDHELP
DDICT
MANUAL
@dottalk.end
```

Source comments:

```text
cmd_maint.cpp
DotTalk++ native MAINT command
First-wave maintenance/SDLC inspection surface.
```

---

### MANSTAR

Source: `src/cli/cmd_manstar.cpp`  

Source comments:

```text
cmd_manstar.cpp
MDO-279R repair: provide the global cmd_MANSTAR symbol expected by shell_commands.cpp.
```

---

### MANSTAR

Source: `x64base/src/cli/cmd_manstar.cpp`  

Source comments:

```text
cmd_manstar.cpp
MDO-279R repair: provide the global cmd_MANSTAR symbol expected by shell_commands.cpp.
```

---

### MANSTAR

Source: `x64base/src/cmd_manstar_candidate.cpp`  

Source comments:

```text
cmd_manstar_candidate.cpp
MDO-274E candidate only - do not copy into source tree without a later guarded apply package.
```

---

### MANUAL

Source: `src/cli/cmd_manual.cpp`  
Owner: `DOT|MANUAL`  
Category: `manualgen`  
Status: `experimental`  
Effect: `report`  
Mutates: `none`  
Usage access: `MANUAL USAGE`  

Purpose:

Inspect the accepted MAN* manualgen catalog from inside DotTalk++.

Usage contract:

```text
MANUAL
  MANUAL USAGE
  MANUAL STATUS
  MANUAL TABLES
  MANUAL COUNTS
  MANUAL RESOLVE <token>
  MANUAL CATALOG STATUS
  MANUAL CATALOG TABLES
  MANUAL CATALOG COUNTS
  MANUAL CATALOG RESOLVE <token>
  MANUAL SECTIONS
  MANUAL MEDIA
  MANUAL REVIEW
```

Notes:

```text
MANUAL is read-only.
  MANUAL reports manualgen catalog status, resolver behavior, and accepted MAN* evidence.
  MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source files, or publication artifacts.
  MANUAL is intentionally self-contained in src/cli so the existing src/cli glob can pick it up.
  Resolver/reader/formatter support modules are not registered commands.
```

Related:

```text
HELP
  DDICT
  MANSECTION
```

---

### MANUAL

Source: `x64base/src/cli/cmd_manual.cpp`  
Owner: `DOT|MANUAL`  
Category: `manualgen`  
Status: `experimental`  
Effect: `report`  
Mutates: `none`  
Usage access: `MANUAL USAGE`  

Purpose:

Inspect the accepted MAN* manualgen catalog from inside DotTalk++.

Usage contract:

```text
MANUAL
  MANUAL USAGE
  MANUAL CATALOG STATUS
  MANUAL CATALOG TABLES
  MANUAL CATALOG COUNTS
  MANUAL CATALOG RESOLVE <token>
  MANUAL SECTIONS
  MANUAL MEDIA
  MANUAL REVIEW
```

Notes:

```text
MANUAL is read-only.
  MANUAL reports manualgen catalog status, resolver behavior, and accepted MAN* evidence.
  MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source files, or publication artifacts.
  MANUAL is intentionally self-contained in src/cli so the existing src/cli glob can pick it up.
  Resolver/reader/formatter support modules are not registered commands.
```

Related:

```text
HELP
  DDICT
  MANSECTION
```

---

### MANUAL catalog reader support

Source: `src/manual/manual_catalog_reader.cpp`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL catalog reader support

Source: `src/manual/manual_catalog_reader.h`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL catalog reader support

Source: `x64base/src/manual/manual_catalog_reader.cpp`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL catalog reader support

Source: `x64base/src/manual/manual_catalog_reader.h`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL report formatter support

Source: `src/manual/manual_report_formatter.cpp`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL report formatter support

Source: `src/manual/manual_report_formatter.h`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL report formatter support

Source: `x64base/src/manual/manual_report_formatter.cpp`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL report formatter support

Source: `x64base/src/manual/manual_report_formatter.h`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL resolver support

Source: `src/manual/manual_catalog_resolver.cpp`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL resolver support

Source: `src/manual/manual_catalog_resolver.h`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL resolver support

Source: `x64base/src/manual/manual_catalog_resolver.cpp`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MANUAL resolver support

Source: `x64base/src/manual/manual_catalog_resolver.h`  
Status: `MDO-282 native MANUAL source skeleton implementation`  

---

### MCC

Source: `src/cli/cmd_mcc.cpp`  
Owner: `DOT|MCC`  
Category: `demo`  
Status: `supported`  
Effect: `onboarding`  
Mutates: `path-state workspace-state relation-state work-area-state cursor`  
Usage access: `MCC USAGE`  

Purpose:

Load the MCC v32 demo workspace as a one-command starter demo.

Usage contract:

```text
MCC
  MCC USAGE
```

Notes:

```text
MCC prepares and loads the MCC sample workspace for demonstration.
  MCC runs DotScript x32 to set the v32 DBF and INDEX paths.
  MCC then runs WORKSPACE LOAD mcc.dtschemas.
  Equivalent manual sequence is DOTSCRIPT x32, then WORKSPACE LOAD mcc.dtschemas.
  MCC is a convenience command and does not directly open tables or create relations itself.
  Table/session/relation restoration remains owned by WORKSPACE.
  Environment/path setup remains owned by DotScript.
  DO X32 is a command-surface shortcut for DotScript x32; MCC should be documented as using DotScript.

  - The extension requested here is .dtschemas, matching the current user
    request.  If the checked-in file is singular .dtschema, change the single
    constant below rather than changing the command logic.
  - This file intentionally avoids directly opening DBFs, indexes, relations,
    or memo files.  WORKSPACE remains the owner of live area/session restore.
```

Related:

```text
DOTSCRIPT
  WORKSPACE
  REL
  USE

cmd_mcc.cpp

Convenience command for the MCC demo workspace.
```

---

### MCC

Source: `x64base/src/cli/cmd_mcc.cpp`  
Owner: `DOT|MCC`  
Category: `demo`  
Status: `supported`  
Effect: `onboarding`  
Mutates: `path-state workspace-state relation-state work-area-state cursor`  
Usage access: `MCC USAGE`  

Purpose:

Load the MCC v32 demo workspace as a one-command starter demo.

Usage contract:

```text
MCC
  MCC USAGE
```

Notes:

```text
MCC prepares and loads the MCC sample workspace for demonstration.
  MCC runs DotScript x32 to set the v32 DBF and INDEX paths.
  MCC then runs WORKSPACE LOAD mcc.dtschemas.
  Equivalent manual sequence is DOTSCRIPT x32, then WORKSPACE LOAD mcc.dtschemas.
  MCC is a convenience command and does not directly open tables or create relations itself.
  Table/session/relation restoration remains owned by WORKSPACE.
  Environment/path setup remains owned by DotScript.
  DO X32 is a command-surface shortcut for DotScript x32; MCC should be documented as using DotScript.

  - The extension requested here is .dtschemas, matching the current user
    request.  If the checked-in file is singular .dtschema, change the single
    constant below rather than changing the command logic.
  - This file intentionally avoids directly opening DBFs, indexes, relations,
    or memo files.  WORKSPACE remains the owner of live area/session restore.
```

Related:

```text
DOTSCRIPT
  WORKSPACE
  REL
  USE

cmd_mcc.cpp

Convenience command for the MCC demo workspace.
```

---

### MEMO

Source: `src/cli/cmd_memo.cpp`  
Owner: `DOT|MEMO`  
Category: `memo`  
Status: `supported`  
Effect: `mixed`  
Mutates: `memo-storage filesystem`  
Usage access: `MEMO USAGE`  

Purpose:

Inspect and maintain x64 memo sidecar/object storage for the current work
  area or all open work areas.

Usage contract:

```text
MEMO USAGE
  MEMO STATUS
  MEMO STATUS ALL
  MEMO VERIFY
  MEMO VERIFY ALL
  MEMO GC
  MEMO GC ALL
  MEMO GC CONFIRM
  MEMO GC ALL CONFIRM
```

Notes:

```text
MEMO with no arguments prints usage.
  STATUS reports memo object/ref statistics.
  VERIFY scans memo references and reports missing/orphaned objects.
  GC without CONFIRM is a dry run.
  GC with CONFIRM may remove orphan memo objects and reclaim storage.
  ALL targets all open work areas; otherwise the current work area is used.
```

Related:

```text
CALCWRITE
  REPLACE
  PACK
```

---

### MEMO

Source: `x64base/src/cli/cmd_memo.cpp`  
Owner: `DOT|MEMO`  
Category: `memo`  
Status: `supported`  
Effect: `mixed`  
Mutates: `memo-storage filesystem`  
Usage access: `MEMO USAGE`  

Purpose:

Inspect and maintain x64 memo sidecar/object storage for the current work
  area or all open work areas.

Usage contract:

```text
MEMO USAGE
  MEMO STATUS
  MEMO STATUS ALL
  MEMO VERIFY
  MEMO VERIFY ALL
  MEMO GC
  MEMO GC ALL
  MEMO GC CONFIRM
  MEMO GC ALL CONFIRM
```

Notes:

```text
MEMO with no arguments prints usage.
  STATUS reports memo object/ref statistics.
  VERIFY scans memo references and reports missing/orphaned objects.
  GC without CONFIRM is a dry run.
  GC with CONFIRM may remove orphan memo objects and reclaim storage.
  ALL targets all open work areas; otherwise the current work area is used.
```

Related:

```text
CALCWRITE
  REPLACE
  PACK
```

---

### MSGMGR

Source: `src/cli/cmd_msgmgr.cpp`  
Owner: `DOT|MSGMGR`  
Category: `messaging`  
Status: `supported`  
Effect: `report|maintenance`  
Mutates: `yes (SEED PRIORITYA APPLY only)`  
Usage access: `MSGMGR USAGE`  

Purpose:

Message Manager command house for runtime messaging and locale-spine
  inspection surfaces.

Usage contract:

```text
MSGMGR
  MSGMGR USAGE
  MSGMGR STATUS
  MSGMGR CHECK
  MSGMGR SEED PRIORITYA CHECK
  MSGMGR SEED PRIORITYA APPLY
  MSGMGR SEED PRIORITYB CHECK
  MSGMGR SEED PRIORITYB APPLY
  MSGMGR SEED PRIORITYC CHECK
  MSGMGR SEED PRIORITYC APPLY
```

Notes:

```text
MSGMGR is the command house for Messaging manager surfaces.
  STATUS and top-level CHECK remain report-only surfaces.
  SEED PRIORITYA CHECK inspects the active runtime Messaging rows.
  SEED PRIORITYA APPLY upserts Priority A runtime Messaging rows into
  SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT and rebuilds the matching
  Messaging LMDB backends from existing CDX containers.
  MSGMGR does not mutate HELP DATA, CMDHELPCHK, manualgen, Data Dictionary,
  SelfDoc, or source-derived catalogs.
```

Related:

```text
SET MESSAGE CATALOG CHECK
  SET MESSAGE CATALOG GET
  SET LANGUAGE
  SET MESSAGE EMIT
  DDICT
```

Source comments:

```text
src/cli/cmd_msgmgr.cpp
```

---

### MSGMGR

Source: `x64base/src/cli/cmd_msgmgr.cpp`  
Owner: `DOT|MSGMGR`  
Category: `messaging`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `MSGMGR USAGE`  

Purpose:

Message Manager command house for runtime messaging and locale-spine
  inspection surfaces.

Usage contract:

```text
MSGMGR
  MSGMGR USAGE
  MSGMGR STATUS
  MSGMGR CHECK
```

Notes:

```text
MSGMGR is the command house for Messaging manager surfaces.
  This first house registration is intentionally read-only.
  STATUS and CHECK report that the command house is registered and that
  runtime Messaging catalog checks remain owned by SET MESSAGE CATALOG
  until later guarded wiring phases.
  MSGMGR does not mutate DBF, CDX, LMDB, HELP DATA, CMDHELPCHK, manualgen,
  Data Dictionary, SelfDoc, or source-derived catalogs.
```

Related:

```text
SET MESSAGE CATALOG CHECK
  SET MESSAGE CATALOG GET
  SET LANGUAGE
  DDICT
```

Source comments:

```text
src/cli/cmd_msgmgr.cpp
```

---

### NEXT

Source: `src/cli/cmd_next.cpp`  
Owner: `DOT|NEXT`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `NEXT USAGE`  

Purpose:

Move the current work-area cursor to the next visible/logical record.

Usage contract:

```text
NEXT
  NEXT USAGE
```

Notes:

```text
NEXT with no arguments moves to the next visible/logical record.
  NEXT requires an open table except for NEXT USAGE.
  NEXT uses the logical_nav next_recno helper.
  NEXT mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

Source comments:

```text
src/cli/cmd_next.cpp
NEXT = next visible record in current logical view
(active order + filter visibility).
```

---

### NEXT

Source: `x64base/src/cli/cmd_next.cpp`  
Owner: `DOT|NEXT`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `NEXT USAGE`  

Purpose:

Move the current work-area cursor to the next visible/logical record.

Usage contract:

```text
NEXT
  NEXT USAGE
```

Notes:

```text
NEXT with no arguments moves to the next visible/logical record.
  NEXT requires an open table except for NEXT USAGE.
  NEXT uses the logical_nav next_recno helper.
  NEXT mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number when movement succeeds.
```

Related:

```text
TOP
  BOTTOM
  FIRST
  LAST
  NEXT
  PRIOR
  SKIP
  GOTO
  GPS
```

Source comments:

```text
src/cli/cmd_next.cpp
NEXT = next visible record in current logical view
(active order + filter visibility).
```

---

### none

Source: `src/edu/edu_boyce_codd.cpp`  
Owner: `EDU|BOYCE_CODD_IMPL`  
Category: `education-placeholder`  
Status: `empty-placeholder`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered`  

Purpose:

Placeholder translation unit reserved for future Boyce-Codd normal form
  educational material.

Usage contract:

```text
This file currently exports no shell command.
  If a BCNF/Boyce-Codd command becomes user-facing, add the runtime command
  handler and full usage contract together.
```

Notes:

```text
Marker documents that this file was inspected and intentionally left
  behavior-neutral.
```

---

### none

Source: `src/edu/edu_dewey_decimal.cpp`  
Owner: `EDU|DEWEY_DECIMAL_IMPL`  
Category: `education-placeholder`  
Status: `empty-placeholder`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered`  

Purpose:

Placeholder translation unit reserved for future Dewey Decimal educational
  material.

Usage contract:

```text
This file currently exports no shell command.
  If a DEWEY/DEWEY_DECIMAL command becomes user-facing, add the runtime
  command handler and full usage contract together.
```

Notes:

```text
Marker documents that this file was inspected and intentionally left
  behavior-neutral.
```

---

### none

Source: `src/edu/edu_snx.cpp`  
Owner: `EDU|SNX_IMPL`  
Category: `education-placeholder`  
Status: `empty-placeholder`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered`  

Purpose:

Placeholder translation unit reserved for future SNX educational/index
  material.

Usage contract:

```text
This file currently exports no shell command.
  If an SNX command becomes user-facing, add the runtime command handler and
  full usage contract together.
```

Notes:

```text
Marker documents that this file was inspected and intentionally left
  behavior-neutral.
```

---

### none

Source: `x64base/src/edu/edu_boyce_codd.cpp`  
Owner: `EDU|BOYCE_CODD_IMPL`  
Category: `education-placeholder`  
Status: `empty-placeholder`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered`  

Purpose:

Placeholder translation unit reserved for future Boyce-Codd normal form
  educational material.

Usage contract:

```text
This file currently exports no shell command.
  If a BCNF/Boyce-Codd command becomes user-facing, add the runtime command
  handler and full usage contract together.
```

Notes:

```text
Marker documents that this file was inspected and intentionally left
  behavior-neutral.
```

---

### none

Source: `x64base/src/edu/edu_dewey_decimal.cpp`  
Owner: `EDU|DEWEY_DECIMAL_IMPL`  
Category: `education-placeholder`  
Status: `empty-placeholder`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered`  

Purpose:

Placeholder translation unit reserved for future Dewey Decimal educational
  material.

Usage contract:

```text
This file currently exports no shell command.
  If a DEWEY/DEWEY_DECIMAL command becomes user-facing, add the runtime
  command handler and full usage contract together.
```

Notes:

```text
Marker documents that this file was inspected and intentionally left
  behavior-neutral.
```

---

### none

Source: `x64base/src/edu/edu_snx.cpp`  
Owner: `EDU|SNX_IMPL`  
Category: `education-placeholder`  
Status: `empty-placeholder`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered`  

Purpose:

Placeholder translation unit reserved for future SNX educational/index
  material.

Usage contract:

```text
This file currently exports no shell command.
  If an SNX command becomes user-facing, add the runtime command handler and
  full usage contract together.
```

Notes:

```text
Marker documents that this file was inspected and intentionally left
  behavior-neutral.
```

---

### NORMALIZE

Source: `src/edu/edu_normalize.cpp`  
Owner: `EDU|NORMALIZE`  
Category: `education-normalization`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `NORMALIZE USAGE`  

Purpose:

Demonstrate field-value normalization rules for C/N/D/L field types.

Usage contract:

```text
NORMALIZE USAGE
  NORMALIZE <C|N|D|L> <len> [dec_if_N] <value...>
```

Examples:

```text
NORMALIZE C 20 "  Hello  "
  NORMALIZE N 10 0 1,234
  NORMALIZE N 10 2 1234.50
  NORMALIZE D 8 11/05/2025
  NORMALIZE L 1 yes
```

Notes:

```text
NORMALIZE USAGE prints usage before normalization work.
  This command does not touch the current work area.
```

Source comments:

```text
src/cli/edu_normalize.cpp
NORMALIZE command ? test harness for value_normalize.hpp + dt::predicate::Value
Usage:
  NORMALIZE <C|N|D|L> <len> [dec_if_N] <value...>
Examples:
  NORMALIZE C 20   "  Hello  "
  NORMALIZE N 10 0 1,234
  NORMALIZE N 10 2 1234.50
  NORMALIZE D 8    11/05/2025
  NORMALIZE L 1    yes
This does not touch the current work area; DbArea is accepted only
to match the CLI handler signature.
```

---

### NORMALIZE

Source: `x64base/src/edu/edu_normalize.cpp`  
Owner: `EDU|NORMALIZE`  
Category: `education-normalization`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `NORMALIZE USAGE`  

Purpose:

Demonstrate field-value normalization rules for C/N/D/L field types.

Usage contract:

```text
NORMALIZE USAGE
  NORMALIZE <C|N|D|L> <len> [dec_if_N] <value...>
```

Examples:

```text
NORMALIZE C 20 "  Hello  "
  NORMALIZE N 10 0 1,234
  NORMALIZE N 10 2 1234.50
  NORMALIZE D 8 11/05/2025
  NORMALIZE L 1 yes
```

Notes:

```text
NORMALIZE USAGE prints usage before normalization work.
  This command does not touch the current work area.
```

Source comments:

```text
src/cli/edu_normalize.cpp
NORMALIZE command ? test harness for value_normalize.hpp + dt::predicate::Value
Usage:
  NORMALIZE <C|N|D|L> <len> [dec_if_N] <value...>
Examples:
  NORMALIZE C 20   "  Hello  "
  NORMALIZE N 10 0 1,234
  NORMALIZE N 10 2 1234.50
  NORMALIZE D 8    11/05/2025
  NORMALIZE L 1    yes
This does not touch the current work area; DbArea is accepted only
to match the CLI handler signature.
```

---

### PACK

Source: `src/cli/cmd_pack.cpp`  
Owner: `DOT|PACK`  
Category: `destructive-table-structure`  
Status: `supported`  
Effect: `compact-table-file`  
Mutates: `table-file closes-table order-state memo-sidecar index-dirty-state`  
Usage access: `PACK USAGE`  

Purpose:

Physically remove deleted records by rewriting the current DBF; x64 memo
  tables rebuild both DBF and DTX sidecar with remapped memo ids.

Usage contract:

```text
PACK USAGE
  PACK
```

Examples:

```text
PACK
```

Notes:

```text
PACK USAGE prints usage before open-table checks.
  PACK rewrites the current DBF with only non-deleted records and closes the table on success.
  PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.
  Legacy memo tables are refused.
  Index containers must be rebuilt/rebound after PACK.
```

Related:

```text
TURBOPACK
  ZAP
  RECALL
```

Source comments:

```text
src/cli/cmd_pack.cpp
PACK — physically removes deleted records by rewriting the DBF to a temp file
        containing only non-deleted records, then atomically replaces the original.
Memo-aware extension:
  - legacy memo tables are still refused
  - x64 M(8) memo tables are packed by rebuilding BOTH the DBF and the DTX sidecar
  - x64 memo object ids are remapped to fresh ids in the new DTX
POLICY (2026):
  - Structural command (file-level operation)
  - Leaves table CLOSED on success
  - User must USE to reopen
  - Indexes must be rebuilt/rebound after
```

---

### PACK

Source: `x64base/src/cli/cmd_pack.cpp`  
Owner: `DOT|PACK`  
Category: `destructive-table-structure`  
Status: `supported`  
Effect: `compact-table-file`  
Mutates: `table-file closes-table order-state memo-sidecar index-dirty-state`  
Usage access: `PACK USAGE`  

Purpose:

Physically remove deleted records by rewriting the current DBF; x64 memo
  tables rebuild both DBF and DTX sidecar with remapped memo ids.

Usage contract:

```text
PACK USAGE
  PACK
```

Examples:

```text
PACK
```

Notes:

```text
PACK USAGE prints usage before open-table checks.
  PACK rewrites the current DBF with only non-deleted records and closes the table on success.
  PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.
  Legacy memo tables are refused.
  Index containers must be rebuilt/rebound after PACK.
```

Related:

```text
TURBOPACK
  ZAP
  RECALL
```

Source comments:

```text
src/cli/cmd_pack.cpp
PACK — physically removes deleted records by rewriting the DBF to a temp file
        containing only non-deleted records, then atomically replaces the original.
Memo-aware extension:
  - legacy memo tables are still refused
  - x64 M(8) memo tables are packed by rebuilding BOTH the DBF and the DTX sidecar
  - x64 memo object ids are remapped to fresh ids in the new DTX
POLICY (2026):
  - Structural command (file-level operation)
  - Leaves table CLOSED on success
  - User must USE to reopen
  - Indexes must be rebuilt/rebound after
```

---

### POLLING

Source: `src/cli/cmd_polling.cpp`  
Owner: `DOT|POLLING_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future POLLING command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If POLLING becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### POLLING

Source: `x64base/src/cli/cmd_polling.cpp`  
Owner: `DOT|POLLING_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future POLLING command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If POLLING becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### PRIOR

Source: `src/cli/cmd_prior.cpp`  
Owner: `DOT|PRIOR`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `PRIOR USAGE`  

Purpose:

Move to the previous visible record in the current logical view.

Usage contract:

```text
PRIOR
  PRIOR USAGE
```

Notes:

```text
PRIOR with no arguments moves to the previous visible record.
  Active order and filter visibility are honored through logical_nav.
  PRIOR USAGE prints usage before open-table checks or cursor movement.
```

Related:

```text
NEXT
  TOP
  BOTTOM
```

Source comments:

```text
src/cli/cmd_prior.cpp
PRIOR = previous visible record in current logical view
(active order + filter visibility).
```

---

### PRIOR

Source: `x64base/src/cli/cmd_prior.cpp`  
Owner: `DOT|PRIOR`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `PRIOR USAGE`  

Purpose:

Move to the previous visible record in the current logical view.

Usage contract:

```text
PRIOR
  PRIOR USAGE
```

Notes:

```text
PRIOR with no arguments moves to the previous visible record.
  Active order and filter visibility are honored through logical_nav.
  PRIOR USAGE prints usage before open-table checks or cursor movement.
```

Related:

```text
NEXT
  TOP
  BOTTOM
```

Source comments:

```text
src/cli/cmd_prior.cpp
PRIOR = previous visible record in current logical view
(active order + filter visibility).
```

---

### PRN

Source: `src/cli/cmd_prn.cpp`  
Owner: `DOT|PRN`  
Category: `output`  
Status: `supported`  
Effect: `configure`  
Mutates: `output-router`  
Usage access: `PRN USAGE`  

Purpose:

Report or configure the PRN output destination used by the output router.

Usage contract:

```text
PRN
  PRN USAGE
  PRN STATUS
  PRN SHOW
  PRN OFF
  PRN TO CONSOLE
  PRN TO SCREEN
  PRN TO FILE <path>
  PRN TO PRINTER
  PRN TO PRINTER <name>
  PRN TO NULL
```

Notes:

```text
PRN with no arguments reports current output routing status.
  PRN USAGE prints usage and does not change routing.
  PRN OFF and PRN TO NULL route PRN output to NULL.
  PRN TO FILE opens/truncates or creates the destination as owned by OutputRouter.
  PRN TO PRINTER is staged only; OS handoff is disabled.
  PRN does not mutate table data.
```

Related:

```text
ECHO
  SET ALTERNATE
  SET PRINTER
```

---

### PRN

Source: `x64base/src/cli/cmd_prn.cpp`  
Owner: `DOT|PRN`  
Category: `output`  
Status: `supported`  
Effect: `configure`  
Mutates: `output-router`  
Usage access: `PRN USAGE`  

Purpose:

Report or configure the PRN output destination used by the output router.

Usage contract:

```text
PRN
  PRN USAGE
  PRN STATUS
  PRN SHOW
  PRN OFF
  PRN TO CONSOLE
  PRN TO SCREEN
  PRN TO FILE <path>
  PRN TO PRINTER
  PRN TO PRINTER <name>
  PRN TO NULL
```

Notes:

```text
PRN with no arguments reports current output routing status.
  PRN USAGE prints usage and does not change routing.
  PRN OFF and PRN TO NULL route PRN output to NULL.
  PRN TO FILE opens/truncates or creates the destination as owned by OutputRouter.
  PRN TO PRINTER is staged only; OS handoff is disabled.
  PRN does not mutate table data.
```

Related:

```text
ECHO
  SET ALTERNATE
  SET PRINTER
```

---

### PROJECTS

Source: `src/cli/cmd_projects.cpp`  
Owner: `DOT|PROJECTS`  
Category: `project`  
Status: `supported`  
Effect: `mixed`  
Mutates: `project-filesystem`  
Usage access: `PROJECTS USAGE`  

Purpose:

List, create, inspect, tree, or delete project skeleton directories under
  the configured PROJECTS slot.

Usage contract:

```text
PROJECTS
  PROJECTS USAGE
  PROJECTS LIST
  PROJECTS CREATE <name> [DATA|FEATURE|HYBRID]
  PROJECTS INFO <name>
  PROJECTS TREE <name>
  PROJECTS DELETE <name> [CONFIRM]
```

Examples:

```text
PROJECTS
  PROJECTS CREATE demo DATA
  PROJECTS INFO demo
  PROJECTS TREE demo
  PROJECTS DELETE demo
  PROJECTS DELETE demo CONFIRM
```

Notes:

```text
PROJECTS with no arguments lists known projects.
  CREATE writes project skeleton folders and a manifest.
  DELETE is dry-run unless CONFIRM is supplied.
  PROJECTS USAGE prints usage and does not create/delete files.
```

Related:

```text
SETPATH
  SHOWINI
  WORKSPACE
```

---

### PROJECTS

Source: `x64base/src/cli/cmd_projects.cpp`  
Owner: `DOT|PROJECTS`  
Category: `project`  
Status: `supported`  
Effect: `mixed`  
Mutates: `project-filesystem`  
Usage access: `PROJECTS USAGE`  

Purpose:

List, create, inspect, tree, or delete project skeleton directories under
  the configured PROJECTS slot.

Usage contract:

```text
PROJECTS
  PROJECTS USAGE
  PROJECTS LIST
  PROJECTS CREATE <name> [DATA|FEATURE|HYBRID]
  PROJECTS INFO <name>
  PROJECTS TREE <name>
  PROJECTS DELETE <name> [CONFIRM]
```

Examples:

```text
PROJECTS
  PROJECTS CREATE demo DATA
  PROJECTS INFO demo
  PROJECTS TREE demo
  PROJECTS DELETE demo
  PROJECTS DELETE demo CONFIRM
```

Notes:

```text
PROJECTS with no arguments lists known projects.
  CREATE writes project skeleton folders and a manifest.
  DELETE is dry-run unless CONFIRM is supplied.
  PROJECTS USAGE prints usage and does not create/delete files.
```

Related:

```text
SETPATH
  SHOWINI
  WORKSPACE
```

---

### PSHELL

Source: `src/cli/cmd_pshell.cpp`  
Owner: `DOT|PSHELL_REF_IMPL`  
Category: `reference-helper`  
Status: `implementation-helper`  
Effect: `report`  
Mutates: `none`  
Usage access: `owned-by cmd_pshell_help.cpp`  

Purpose:

PowerShell reference catalog presentation helper used by the PSHELL command.

Usage contract:

```text
User-visible PSHELL usage is owned by cmd_pshell_help.cpp.
  This file provides show_pshell_help(...) and catalog formatting support.
```

Notes:

```text
PSHELL is read-only reference output; it does not execute PowerShell.
  Keep command dispatch/usage gating in cmd_pshell_help.cpp.
```

---

### PSHELL

Source: `src/cli/cmd_pshell_help.cpp`  
Owner: `DOT|PSHELL`  
Category: `reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `PSHELL USAGE`  

Purpose:

Display the PowerShell/PSHELL helper reference and search the curated
  PowerShell one-liner catalog.

Usage contract:

```text
PSHELL
  PSHELL USAGE
  PSHELL LIST-CATEGORIES
  PSHELL <category>
  PSHELL <term>
```

Examples:

```text
PSHELL
  PSHELL PYTHON
  PSHELL PY-VENV-CREATE
  PSHELL CLEAN
```

Notes:

```text
PSHELL with no arguments displays the grouped PSHELL reference.
  PSHELL USAGE prints command usage without searching the catalog.
  PSHELL is read-only and does not execute PowerShell commands.
```

Related:

```text
HELP
  SQLHELP
  PS
```

Source comments:

```text
cmd_pshell_help.cpp
```

---

### PSHELL

Source: `x64base/src/cli/cmd_pshell.cpp`  
Owner: `DOT|PSHELL_REF_IMPL`  
Category: `reference-helper`  
Status: `implementation-helper`  
Effect: `report`  
Mutates: `none`  
Usage access: `owned-by cmd_pshell_help.cpp`  

Purpose:

PowerShell reference catalog presentation helper used by the PSHELL command.

Usage contract:

```text
User-visible PSHELL usage is owned by cmd_pshell_help.cpp.
  This file provides show_pshell_help(...) and catalog formatting support.
```

Notes:

```text
PSHELL is read-only reference output; it does not execute PowerShell.
  Keep command dispatch/usage gating in cmd_pshell_help.cpp.
```

---

### PSHELL

Source: `x64base/src/cli/cmd_pshell_help.cpp`  
Owner: `DOT|PSHELL`  
Category: `reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `PSHELL USAGE`  

Purpose:

Display the PowerShell/PSHELL helper reference and search the curated
  PowerShell one-liner catalog.

Usage contract:

```text
PSHELL
  PSHELL USAGE
  PSHELL LIST-CATEGORIES
  PSHELL <category>
  PSHELL <term>
```

Examples:

```text
PSHELL
  PSHELL PYTHON
  PSHELL PY-VENV-CREATE
  PSHELL CLEAN
```

Notes:

```text
PSHELL with no arguments displays the grouped PSHELL reference.
  PSHELL USAGE prints command usage without searching the catalog.
  PSHELL is read-only and does not execute PowerShell commands.
```

Related:

```text
HELP
  SQLHELP
  PS
```

Source comments:

```text
cmd_pshell_help.cpp
```

---

### RBROWSE

Source: `src/cli/cmd_rbrowse.cpp`  
Owner: `DOT|RBROWSE`  
Category: `browser-alias`  
Status: `compatibility-alias`  
Effect: `launch-ui`  
Mutates: `delegated-to-ERSATZ`  
Usage access: `delegated-to ERSATZ/RBROWSE help surface`  

Purpose:

Compatibility spelling for the ERSATZ relational browser.

Usage contract:

```text
RBROWSE [ersatz-browser-options]
  RBROWSE USAGE is delegated to the ERSATZ browser command surface when supported.
```

Notes:

```text
Keep behavior centralized in cmd_ERSATZ so relation browser behavior cannot
  drift between ERSATZ and RBROWSE.
  This file should remain a thin wrapper.
```

Related:

```text
ERSATZ
  RELATIONS
  WORKSPACE

src/cli/cmd_rbrowse.cpp

RBROWSE is the compatibility spelling for the ERSATZ relational browser.
Keep the behavior centralized in cmd_ERSATZ so smart root/profile inference,
order-aware navigation, LOAD/SAVE/WLOAD, DELTA, and diagnostics cannot drift
between two command implementations.
```

---

### RBROWSE

Source: `x64base/src/cli/cmd_rbrowse.cpp`  
Owner: `DOT|RBROWSE`  
Category: `browser-alias`  
Status: `compatibility-alias`  
Effect: `launch-ui`  
Mutates: `delegated-to-ERSATZ`  
Usage access: `delegated-to ERSATZ/RBROWSE help surface`  

Purpose:

Compatibility spelling for the ERSATZ relational browser.

Usage contract:

```text
RBROWSE [ersatz-browser-options]
  RBROWSE USAGE is delegated to the ERSATZ browser command surface when supported.
```

Notes:

```text
Keep behavior centralized in cmd_ERSATZ so relation browser behavior cannot
  drift between ERSATZ and RBROWSE.
  This file should remain a thin wrapper.
```

Related:

```text
ERSATZ
  RELATIONS
  WORKSPACE

src/cli/cmd_rbrowse.cpp

RBROWSE is the compatibility spelling for the ERSATZ relational browser.
Keep the behavior centralized in cmd_ERSATZ so smart root/profile inference,
order-aware navigation, LOAD/SAVE/WLOAD, DELTA, and diagnostics cannot drift
between two command implementations.
```

---

### REBUILD

Source: `src/cli/cmd_rebuild.cpp`  
Owner: `DOT|REBUILD`  
Category: `index`  
Status: `supported`  
Effect: `rebuild`  
Mutates: `cnx-index table-stale-state`  
Usage access: `REBUILD USAGE`  

Purpose:

Rebuild a CNX container for the current table, using the active CNX or a
  supplied CNX name/path and clearing TABLE stale state on success.

Usage contract:

```text
REBUILD USAGE
  REBUILD
  REBUILD <name-or-path.cnx>
```

Notes:

```text
REBUILD with no arguments uses the current CNX or defaults to <table>.cnx.
  REBUILD requires an open table except for REBUILD USAGE.
  REBUILD prompts to COMMIT dirty TABLE buffers before rebuilding.
  REBUILD refuses to continue if the table remains dirty after COMMIT.
  REBUILD opens the CNX tag directory once for reporting.
  The CNX backend rebuilds all tags in the container in one rebuild call.
  On success, TABLE STALE is cleared for the current area when table buffering is enabled.
```

Related:

```text
REINDEX
  CNX
  COMMIT
  TABLE
```

Source comments:

```text
REBUILD [<name-or-path.cnx>]
CNX rebuild (legacy compound index)
Policy:
- Rebuilds the CNX container once
- CNX backend itself rebuilds all tags in the container
- Requires clean TABLE (or explicit COMMIT)
Architecture:
- Public CNX container resolves via INDEXES
- CNX remains a legacy/flat structure (no LMDB backend)
Relationship to REINDEX:
- REINDEX CNX -> calls REBUILD
- This file is the CNX execution engine / orchestrator
```

---

### REBUILD

Source: `x64base/src/cli/cmd_rebuild.cpp`  
Owner: `DOT|REBUILD`  
Category: `index`  
Status: `supported`  
Effect: `rebuild`  
Mutates: `cnx-index table-stale-state`  
Usage access: `REBUILD USAGE`  

Purpose:

Rebuild a CNX container for the current table, using the active CNX or a
  supplied CNX name/path and clearing TABLE stale state on success.

Usage contract:

```text
REBUILD USAGE
  REBUILD
  REBUILD <name-or-path.cnx>
```

Notes:

```text
REBUILD with no arguments uses the current CNX or defaults to <table>.cnx.
  REBUILD requires an open table except for REBUILD USAGE.
  REBUILD prompts to COMMIT dirty TABLE buffers before rebuilding.
  REBUILD refuses to continue if the table remains dirty after COMMIT.
  REBUILD opens the CNX tag directory once for reporting.
  The CNX backend rebuilds all tags in the container in one rebuild call.
  On success, TABLE STALE is cleared for the current area when table buffering is enabled.
```

Related:

```text
REINDEX
  CNX
  COMMIT
  TABLE
```

Source comments:

```text
REBUILD [<name-or-path.cnx>]
CNX rebuild (legacy compound index)
Policy:
- Rebuilds the CNX container once
- CNX backend itself rebuilds all tags in the container
- Requires clean TABLE (or explicit COMMIT)
Architecture:
- Public CNX container resolves via INDEXES
- CNX remains a legacy/flat structure (no LMDB backend)
Relationship to REINDEX:
- REINDEX CNX -> calls REBUILD
- This file is the CNX execution engine / orchestrator
```

---

### RECALL

Source: `src/cli/cmd_recall.cpp`  
Owner: `DOT|RECALL`  
Category: `table-mutation`  
Status: `supported`  
Effect: `undelete-records`  
Mutates: `table-data delete-flags index-entries`  
Usage access: `RECALL USAGE`  

Purpose:

Clear deleted flags on the current record or selected deleted records.

Usage contract:

```text
RECALL USAGE
  RECALL
  RECALL ALL
  RECALL REST
  RECALL NEXT <n>
  RECALL FOR <expr>
```

Examples:

```text
RECALL
  RECALL ALL
  RECALL REST
  RECALL NEXT 10
  RECALL FOR LNAME = "SMITH"
```

Notes:

```text
RECALL USAGE prints usage before open-table checks.
  RECALL with no arguments recalls the current record.
  RECALL target selection is deleted-only.
  RECALL rebuilds index entries for recalled records best-effort.
```

Related:

```text
ERASE
  PACK
  ZAP
```

Source comments:

```text
Incremental indexing behavior:
- Direct-write mode: if a CDX/LMDB backend is active, RECALL rebuilds index
  entries for all field-backed tags on the current record after the delete
  flag is cleared successfully.
- Buffered/table mode: unchanged here; COMMIT remains responsible for rebuild.
Traversal behavior:
- RECALL snapshots target recnos first, then recalls by recno.
- This avoids mutating an active index while simultaneously iterating it.
- RECALL target selection is explicitly deleted-only.
- Deleted-only traversal must use physical records, because active indexes
  normally contain only live records and would otherwise hide deleted rows.
- REST / NEXT preserve physical-scope semantics through the shared selector.
```

---

### RECALL

Source: `x64base/src/cli/cmd_recall.cpp`  
Owner: `DOT|RECALL`  
Category: `table-mutation`  
Status: `supported`  
Effect: `undelete-records`  
Mutates: `table-data delete-flags index-entries`  
Usage access: `RECALL USAGE`  

Purpose:

Clear deleted flags on the current record or selected deleted records.

Usage contract:

```text
RECALL USAGE
  RECALL
  RECALL ALL
  RECALL REST
  RECALL NEXT <n>
  RECALL FOR <expr>
```

Examples:

```text
RECALL
  RECALL ALL
  RECALL REST
  RECALL NEXT 10
  RECALL FOR LNAME = "SMITH"
```

Notes:

```text
RECALL USAGE prints usage before open-table checks.
  RECALL with no arguments recalls the current record.
  RECALL target selection is deleted-only.
  RECALL rebuilds index entries for recalled records best-effort.
```

Related:

```text
ERASE
  PACK
  ZAP
```

Source comments:

```text
Incremental indexing behavior:
- Direct-write mode: if a CDX/LMDB backend is active, RECALL rebuilds index
  entries for all field-backed tags on the current record after the delete
  flag is cleared successfully.
- Buffered/table mode: unchanged here; COMMIT remains responsible for rebuild.
Traversal behavior:
- RECALL snapshots target recnos first, then recalls by recno.
- This avoids mutating an active index while simultaneously iterating it.
- RECALL target selection is explicitly deleted-only.
- Deleted-only traversal must use physical records, because active indexes
  normally contain only live records and would otherwise hide deleted rows.
- REST / NEXT preserve physical-scope semantics through the shared selector.
```

---

### RECNO

Source: `src/cli/cmd_recno.cpp`  
Owner: `DOT|RECNO`  
Category: `navigation`  
Status: `supported`  
Effect: `mixed`  
Mutates: `cursor`  
Usage access: `RECNO USAGE`  

Purpose:

Report the current record number or navigate to an explicit record number.

Usage contract:

```text
RECNO
  RECNO USAGE
  RECNO <n>
```

Notes:

```text
RECNO with no arguments reports the current record number.
  RECNO <n> navigates to record n and prints the resulting record number.
  RECNO requires an open table except for RECNO USAGE.
  RECNO mutates cursor position only when a numeric record argument is supplied.
```

Related:

```text
GOTO
  GPS
  SKIP
```

Source comments:

```text
src/cli/cmd_recno.cpp
```

---

### RECNO

Source: `x64base/src/cli/cmd_recno.cpp`  
Owner: `DOT|RECNO`  
Category: `navigation`  
Status: `supported`  
Effect: `mixed`  
Mutates: `cursor`  
Usage access: `RECNO USAGE`  

Purpose:

Report the current record number or navigate to an explicit record number.

Usage contract:

```text
RECNO
  RECNO USAGE
  RECNO <n>
```

Notes:

```text
RECNO with no arguments reports the current record number.
  RECNO <n> navigates to record n and prints the resulting record number.
  RECNO requires an open table except for RECNO USAGE.
  RECNO mutates cursor position only when a numeric record argument is supplied.
```

Related:

```text
GOTO
  GPS
  SKIP
```

Source comments:

```text
src/cli/cmd_recno.cpp
```

---

### REFRESH

Source: `src/cli/cmd_refresh.cpp`  
Owner: `DOT|REFRESH`  
Category: `table`  
Status: `supported`  
Effect: `refresh`  
Mutates: `work-area cursor order-state`  
Usage access: `REFRESH USAGE`  

Purpose:

Reopen the current table from disk and restore cursor/order state best-effort.

Usage contract:

```text
REFRESH
  REFRESH USAGE
```

Notes:

```text
REFRESH with no arguments reopens the current DBF file.
  Cursor position is restored best-effort after reopen.
  Active order/container/tag/direction state is restored best-effort.
  REFRESH USAGE prints usage before open-table checks or reopening.
```

Related:

```text
USE
  REINDEX
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_refresh.cpp
```

---

### REFRESH

Source: `x64base/src/cli/cmd_refresh.cpp`  
Owner: `DOT|REFRESH`  
Category: `table`  
Status: `supported`  
Effect: `refresh`  
Mutates: `work-area cursor order-state`  
Usage access: `REFRESH USAGE`  

Purpose:

Reopen the current table from disk and restore cursor/order state best-effort.

Usage contract:

```text
REFRESH
  REFRESH USAGE
```

Notes:

```text
REFRESH with no arguments reopens the current DBF file.
  Cursor position is restored best-effort after reopen.
  Active order/container/tag/direction state is restored best-effort.
  REFRESH USAGE prints usage before open-table checks or reopening.
```

Related:

```text
USE
  REINDEX
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_refresh.cpp
```

---

### REINDEX

Source: `src/cli/cmd_reindex.cpp`  
Owner: `DOT|REINDEX`  
Category: `index`  
Status: `supported`  
Effect: `rebuild`  
Mutates: `index-files table-stale-state`  
Usage access: `REINDEX USAGE`  

Purpose:

Canonical rebuild dispatcher for INX, CNX, CDX/LMDB, and student index
  families, choosing a default family by table flavor when no family is given.

Usage contract:

```text
REINDEX USAGE
  REINDEX
  REINDEX INX
  REINDEX INX <tagfile>
  REINDEX CNX
  REINDEX CNX <name-or-path.cnx>
  REINDEX CDX
  REINDEX CDX YES
  REINDEX CDX AUTO
  REINDEX CDX NOPROMPT
  REINDEX CDX CLEAN
  REINDEX CDX FORCE
  REINDEX CDX QUIET
  REINDEX SIX
  REINDEX SIX <tagfile>
  REINDEX SCX
  REINDEX SCX <tagfile>
  REINDEX ALL
  REINDEX CUSTOM
  REINDEX <tagfile>
```

Notes:

```text
REINDEX with no arguments chooses the default family by open table flavor.
  v64-like tables default to CDX through BUILDLMDB.
  v32-like tables default to INX.
  With no table open, the fallback default is CDX.
  REINDEX INX rebuilds a legacy single-tag INX file.
  REINDEX CNX delegates to REBUILD.
  REINDEX CDX delegates to BUILDLMDB.
  REINDEX ALL excludes SIX and SCX by design.
  REINDEX CUSTOM runs SIX and SCX student families.
  REINDEX <tagfile> is treated as REINDEX INX <tagfile> for compatibility.
  Dirty TABLE buffers may prompt for COMMIT before supported rebuild paths.
```

Related:

```text
REBUILD
  BUILDLMDB
  INDEX
  CDX
  CNX
  COMMIT
```

Source comments:

```text
- REINDEX CUSTOM-> SIX + SCX
Default policy:
- REINDEX with no args chooses by open table flavor:
    v64-like table -> CDX
    v32-like table -> INX
- If no table is open, fallback default is CDX.
Notes:
- CUSTOM is the command token; the internal enum name avoids "CUSTOM"
  directly to dodge macro/name collisions on some builds.
- Console output is ASCII-only (CP437-safe).
- REINDEX ALL excludes student families by design.
  Student families are opt-in through REINDEX CUSTOM.
```

---

### REINDEX

Source: `x64base/src/cli/cmd_reindex.cpp`  
Owner: `DOT|REINDEX`  
Category: `index`  
Status: `supported`  
Effect: `rebuild`  
Mutates: `index-files table-stale-state`  
Usage access: `REINDEX USAGE`  

Purpose:

Canonical rebuild dispatcher for INX, CNX, CDX/LMDB, and student index
  families, choosing a default family by table flavor when no family is given.

Usage contract:

```text
REINDEX USAGE
  REINDEX
  REINDEX INX
  REINDEX INX <tagfile>
  REINDEX CNX
  REINDEX CNX <name-or-path.cnx>
  REINDEX CDX
  REINDEX CDX YES
  REINDEX CDX AUTO
  REINDEX CDX NOPROMPT
  REINDEX CDX CLEAN
  REINDEX CDX FORCE
  REINDEX CDX QUIET
  REINDEX SIX
  REINDEX SIX <tagfile>
  REINDEX SCX
  REINDEX SCX <tagfile>
  REINDEX ALL
  REINDEX CUSTOM
  REINDEX <tagfile>
```

Notes:

```text
REINDEX with no arguments chooses the default family by open table flavor.
  v64-like tables default to CDX through BUILDLMDB.
  v32-like tables default to INX.
  With no table open, the fallback default is CDX.
  REINDEX INX rebuilds a legacy single-tag INX file.
  REINDEX CNX delegates to REBUILD.
  REINDEX CDX delegates to BUILDLMDB.
  REINDEX ALL excludes SIX and SCX by design.
  REINDEX CUSTOM runs SIX and SCX student families.
  REINDEX <tagfile> is treated as REINDEX INX <tagfile> for compatibility.
  Dirty TABLE buffers may prompt for COMMIT before supported rebuild paths.
```

Related:

```text
REBUILD
  BUILDLMDB
  INDEX
  CDX
  CNX
  COMMIT
```

Source comments:

```text
- REINDEX CUSTOM-> SIX + SCX
Default policy:
- REINDEX with no args chooses by open table flavor:
    v64-like table -> CDX
    v32-like table -> INX
- If no table is open, fallback default is CDX.
Notes:
- CUSTOM is the command token; the internal enum name avoids "CUSTOM"
  directly to dodge macro/name collisions on some builds.
- Console output is ASCII-only (CP437-safe).
- REINDEX ALL excludes student families by design.
  Student families are opt-in through REINDEX CUSTOM.
```

---

### RELATIONS

Source: `src/cli/cmd_relations.cpp`  
Owner: `DOT|RELATIONS`  
Category: `relation`  
Status: `supported`  
Effect: `mixed`  
Mutates: `relation-graph`  
Usage access: `RELATIONS USAGE`  

Purpose:

Inspect and manage active relation definitions, relation files, and relation
  enumeration helpers.

Usage contract:

```text
RELATIONS
  RELATIONS USAGE
  RELATIONS ALL
  SET RELATIONS
  SET RELATIONS USAGE
  SET RELATIONS ADD <parent> <child> ON f1[,f2...] [TO child_f1[,child_f2...]]
  SET RELATIONS CLEAR <parent|ALL>
```

Examples:

```text
RELATIONS
  RELATIONS ALL
  SET RELATIONS ADD STUDENTS ENROLL ON SID
  SET RELATIONS CLEAR ALL
```

Notes:

```text
RELATIONS USAGE prints usage and does not inspect or mutate relation state.
  SET RELATIONS USAGE prints usage and does not mutate the relation graph.
  SET RELATIONS ADD/CLEAR mutate relation definitions.
  RELATIONS ALL reports a recursive tree rooted at the current parent.
```

Related:

```text
RBROWSE
  TUPLE
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_relations.cpp
```

---

### RELATIONS

Source: `x64base/src/cli/cmd_relations.cpp`  
Owner: `DOT|RELATIONS`  
Category: `relation`  
Status: `supported`  
Effect: `mixed`  
Mutates: `relation-graph`  
Usage access: `RELATIONS USAGE`  

Purpose:

Inspect and manage active relation definitions, relation files, and relation
  enumeration helpers.

Usage contract:

```text
RELATIONS
  RELATIONS USAGE
  RELATIONS ALL
  SET RELATIONS
  SET RELATIONS USAGE
  SET RELATIONS ADD <parent> <child> ON f1[,f2...] [TO child_f1[,child_f2...]]
  SET RELATIONS CLEAR <parent|ALL>
```

Examples:

```text
RELATIONS
  RELATIONS ALL
  SET RELATIONS ADD STUDENTS ENROLL ON SID
  SET RELATIONS CLEAR ALL
```

Notes:

```text
RELATIONS USAGE prints usage and does not inspect or mutate relation state.
  SET RELATIONS USAGE prints usage and does not mutate the relation graph.
  SET RELATIONS ADD/CLEAR mutate relation definitions.
  RELATIONS ALL reports a recursive tree rooted at the current parent.
```

Related:

```text
RBROWSE
  TUPLE
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_relations.cpp
```

---

### REPLACE

Source: `src/cli/cmd_replace.cpp`  
Owner: `DOT|REPLACE`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data table-buffer memo stale-state index`  
Usage access: `REPLACE USAGE`  

Purpose:

Replace one field in the current record by field name or field index,
  preserving RHS expression evaluation, type validation, memo conversion,
  and table-buffer semantics.

Usage contract:

```text
REPLACE USAGE
  REPLACE <field_index> WITH <value>
  REPLACE <field_name> WITH <value>
```

Examples:

```text
REPLACE LNAME WITH "Smith"
  REPLACE 3 WITH TODAY
  REPLACE NOTES WITH "updated memo text"
```

Notes:

```text
REPLACE requires an open table and a current record.
  REPLACE resolves fields by standard field index/name rules.
  RHS values pass through the expression/RHS evaluator and legacy string/date function handling.
  X64 memo text is converted into stored object-id text before DBF storage.
  Field values are validated and normalized before storage.
  When TABLE buffering is ON, REPLACE records a buffered field change and marks the field stale/dirty.
  When TABLE buffering is OFF, REPLACE writes immediately through DbArea storage.
  COMMIT owns durable application of buffered table changes.
  REPLACE is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
REPLACE_MULTI
  TABLE
  COMMIT
  ROLLBACK
  STRUCT
  FIELDS
```

Source comments:

```text
REPLACE <field_index> WITH <value>
  REPLACE <field_name>  WITH <value>
Contract (current iteration):
- TABLE ON: writes are buffered into the table buffer change list.
  No OS record locking occurs here; COMMIT owns locking.
- TABLE OFF: REPLACE locks + writes immediately.
- CLI remains responsible for:
    * parsing
    * RHS evaluation
    * x64 memo text -> stored object-id conversion
    * field-level validation of the stored value
    * table-buffer dirty/stale bookkeeping
```

---

### REPLACE

Source: `x64base/src/cli/cmd_replace.cpp`  
Owner: `DOT|REPLACE`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data table-buffer memo stale-state index`  
Usage access: `REPLACE USAGE`  

Purpose:

Replace one field in the current record by field name or field index,
  preserving RHS expression evaluation, type validation, memo conversion,
  and table-buffer semantics.

Usage contract:

```text
REPLACE USAGE
  REPLACE <field_index> WITH <value>
  REPLACE <field_name> WITH <value>
```

Examples:

```text
REPLACE LNAME WITH "Smith"
  REPLACE 3 WITH TODAY
  REPLACE NOTES WITH "updated memo text"
```

Notes:

```text
REPLACE requires an open table and a current record.
  REPLACE resolves fields by standard field index/name rules.
  RHS values pass through the expression/RHS evaluator and legacy string/date function handling.
  X64 memo text is converted into stored object-id text before DBF storage.
  Field values are validated and normalized before storage.
  When TABLE buffering is ON, REPLACE records a buffered field change and marks the field stale/dirty.
  When TABLE buffering is OFF, REPLACE writes immediately through DbArea storage.
  COMMIT owns durable application of buffered table changes.
  REPLACE is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
REPLACE_MULTI
  TABLE
  COMMIT
  ROLLBACK
  STRUCT
  FIELDS
```

Source comments:

```text
REPLACE <field_index> WITH <value>
  REPLACE <field_name>  WITH <value>
Contract (current iteration):
- TABLE ON: writes are buffered into the table buffer change list.
  No OS record locking occurs here; COMMIT owns locking.
- TABLE OFF: REPLACE locks + writes immediately.
- CLI remains responsible for:
    * parsing
    * RHS evaluation
    * x64 memo text -> stored object-id conversion
    * field-level validation of the stored value
    * table-buffer dirty/stale bookkeeping
```

---

### REPLACE_MULTI

Source: `src/cli/cmd_replace_multi.cpp`  
Owner: `DOT|REPLACE_MULTI`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data memo index stale-state`  
Usage access: `REPLACE_MULTI USAGE`  

Purpose:

Replace multiple fields in the current record with one record lock and
  one physical write, preserving RHS evaluation, validation, memo handling,
  and direct index maintenance.

Usage contract:

```text
REPLACE_MULTI USAGE
  REPLACE_MULTI <field> WITH <value>[, <field> WITH <value>]...
```

Examples:

```text
REPLACE_MULTI LNAME WITH "Smith", FNAME WITH "John"
  REPLACE_MULTI DOB WITH 20000101, ACTIVE WITH .T.
```

Notes:

```text
REPLACE_MULTI requires an open table and a current record.
  REPLACE_MULTI validates all assignments before applying the physical write.
  RHS values are evaluated/dequoted before validation and storage.
  Memo fields are written through the memo backend before storing the memo token.
  REPLACE_MULTI writes directly to the DBF and does not mark the table buffer DIRTY.
  REPLACE_MULTI captures before/after index snapshots and applies direct index maintenance.
  If index maintenance fails, changed fields are marked STALE.
  Buffering/COMMIT/ROLLBACK integration remains deferred for this direct-write command.
  REPLACE_MULTI is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
REPLACE
  TABLE
  COMMIT
  ROLLBACK
  STRUCT
  FIELDS
```

Source comments:

```text
bool cmd_REPLACE_MULTI(xbase::DbArea& A,
                         const std::vector<FieldUpdate>& updates,
                         std::string* error)
Rule (current direct-write phase):
  - Writes directly to DBF => does NOT mark DIRTY.
  - If a field actually changes, attempt immediate index maintenance through
    IndexManager simple-field tag logic.
  - Only mark field-level STALE if index maintenance fails for that changed field.
Notes:
  - Buffering/COMMIT/ROLLBACK are deferred.
  - Compound/computed tags are deferred.
  - Simple first-pass policy: field-name == tag-name via IndexManager.
```

---

### REPLACE_MULTI

Source: `x64base/src/cli/cmd_replace_multi.cpp`  
Owner: `DOT|REPLACE_MULTI`  
Category: `data`  
Status: `supported`  
Effect: `mutate`  
Mutates: `table-data memo index stale-state`  
Usage access: `REPLACE_MULTI USAGE`  

Purpose:

Replace multiple fields in the current record with one record lock and
  one physical write, preserving RHS evaluation, validation, memo handling,
  and direct index maintenance.

Usage contract:

```text
REPLACE_MULTI USAGE
  REPLACE_MULTI <field> WITH <value>[, <field> WITH <value>]...
```

Examples:

```text
REPLACE_MULTI LNAME WITH "Smith", FNAME WITH "John"
  REPLACE_MULTI DOB WITH 20000101, ACTIVE WITH .T.
```

Notes:

```text
REPLACE_MULTI requires an open table and a current record.
  REPLACE_MULTI validates all assignments before applying the physical write.
  RHS values are evaluated/dequoted before validation and storage.
  Memo fields are written through the memo backend before storing the memo token.
  REPLACE_MULTI writes directly to the DBF and does not mark the table buffer DIRTY.
  REPLACE_MULTI captures before/after index snapshots and applies direct index maintenance.
  If index maintenance fails, changed fields are marked STALE.
  Buffering/COMMIT/ROLLBACK integration remains deferred for this direct-write command.
  REPLACE_MULTI is a table-data mutation command; do not classify it as read-only.
```

Related:

```text
REPLACE
  TABLE
  COMMIT
  ROLLBACK
  STRUCT
  FIELDS
```

Source comments:

```text
bool cmd_REPLACE_MULTI(xbase::DbArea& A,
                         const std::vector<FieldUpdate>& updates,
                         std::string* error)
Rule (current direct-write phase):
  - Writes directly to DBF => does NOT mark DIRTY.
  - If a field actually changes, attempt immediate index maintenance through
    IndexManager simple-field tag logic.
  - Only mark field-level STALE if index maintenance fails for that changed field.
Notes:
  - Buffering/COMMIT/ROLLBACK are deferred.
  - Compound/computed tags are deferred.
  - Simple first-pass policy: field-name == tag-name via IndexManager.
```

---

### RETRO

Source: `src/cli/cmd_retro.cpp`  
Owner: `DOT|RETRO`  
Category: `display`  
Status: `supported`  
Effect: `display`  
Mutates: `console-output`  
Usage access: `RETRO USAGE`  

Purpose:

Display ASCII-safe retro computer/system splash screens.

Usage contract:

```text
RETRO USAGE
  RETRO LIST
  RETRO SHOW <system>
  RETRO <system>
  RETRO HELP
```

Notes:

```text
RETRO with no arguments prints usage.
  RETRO LIST lists available retro screen identifiers.
  RETRO SHOW <system> and RETRO <system> display a matching screen.
  RETRO writes console output only and does not mutate table data.
```

Related:

```text
ABOUT
  TVISION
```

Source comments:

```text
src/cli/cmd_retro.cpp
RETRO command
Stable ASCII-safe edition.
UTF-8/Unicode rendering can come later as polish.
Usage:
  RETRO LIST
  RETRO SHOW <system>
  RETRO <system>
  RETRO HELP
```

---

### RETRO

Source: `x64base/src/cli/cmd_retro.cpp`  
Owner: `DOT|RETRO`  
Category: `display`  
Status: `supported`  
Effect: `display`  
Mutates: `console-output`  
Usage access: `RETRO USAGE`  

Purpose:

Display ASCII-safe retro computer/system splash screens.

Usage contract:

```text
RETRO USAGE
  RETRO LIST
  RETRO SHOW <system>
  RETRO <system>
  RETRO HELP
```

Notes:

```text
RETRO with no arguments prints usage.
  RETRO LIST lists available retro screen identifiers.
  RETRO SHOW <system> and RETRO <system> display a matching screen.
  RETRO writes console output only and does not mutate table data.
```

Related:

```text
ABOUT
  TVISION
```

Source comments:

```text
src/cli/cmd_retro.cpp
RETRO command
Stable ASCII-safe edition.
UTF-8/Unicode rendering can come later as polish.
Usage:
  RETRO LIST
  RETRO SHOW <system>
  RETRO <system>
  RETRO HELP
```

---

### ROLLBACK

Source: `src/cli/cmd_rollback.cpp`  
Owner: `DOT|ROLLBACK`  
Category: `table-buffer`  
Status: `supported`  
Effect: `discard-buffered-changes`  
Mutates: `buffer-state dirty-stale-flags`  
Usage access: `ROLLBACK USAGE`  

Purpose:

Discard buffered/uncommitted table changes for the current area or all areas.

Usage contract:

```text
ROLLBACK USAGE
  ROLLBACK
  ROLLBACK ALL
```

Examples:

```text
ROLLBACK
  ROLLBACK ALL
```

Notes:

```text
ROLLBACK USAGE returns before modifying buffer state.
  ROLLBACK without arguments clears buffered state for the current area.
  ROLLBACK ALL clears buffered state across all areas.
```

Related:

```text
COMMIT
  TABLE BUFFER
```

Source comments:

```text
src/cli/cmd_rollback.cpp
```

---

### ROLLBACK

Source: `x64base/src/cli/cmd_rollback.cpp`  
Owner: `DOT|ROLLBACK`  
Category: `table-buffer`  
Status: `supported`  
Effect: `discard-buffered-changes`  
Mutates: `buffer-state dirty-stale-flags`  
Usage access: `ROLLBACK USAGE`  

Purpose:

Discard buffered/uncommitted table changes for the current area or all areas.

Usage contract:

```text
ROLLBACK USAGE
  ROLLBACK
  ROLLBACK ALL
```

Examples:

```text
ROLLBACK
  ROLLBACK ALL
```

Notes:

```text
ROLLBACK USAGE returns before modifying buffer state.
  ROLLBACK without arguments clears buffered state for the current area.
  ROLLBACK ALL clears buffered state across all areas.
```

Related:

```text
COMMIT
  TABLE BUFFER
```

Source comments:

```text
src/cli/cmd_rollback.cpp
```

---

### RPG

Source: `src/cli/cmd_rpg.cpp`  
Owner: `DOT|RPG_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future RPG command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If RPG becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### RPG

Source: `x64base/src/cli/cmd_rpg.cpp`  
Owner: `DOT|RPG_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future RPG command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If RPG becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### RULE

Source: `src/cli/cmd_rule.cpp`  
Owner: `DOT|RULE`  
Category: `validation`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `RULE USAGE`  

Purpose:

Inspect rule catalog paths, bindings, and field constraints for the current
  work area.

Usage contract:

```text
RULE
  RULE USAGE
  RULE STATUS
  RULE SHOW <field|ALL>
  RULE LIST
  RULE PATHS
```

Examples:

```text
RULE
  RULE STATUS
  RULE SHOW GPA
  RULE SHOW ALL
  RULE LIST
  RULE PATHS
```

Notes:

```text
RULE with no arguments reports rule status.
  RULE USAGE prints usage and does not require an open table.
  RULE is diagnostic/read-only; it does not create, edit, or bind rules.
```

Related:

```text
VALIDATE
  WHERE
```

Source comments:

```text
cmd_rule.cpp
DotTalk++ RULE diagnostics command.
Public surface:
  RULE
  RULE STATUS
  RULE SHOW <field|ALL>
  RULE LIST
  RULE PATHS
Notes:
  - SHOW / STATUS / LIST / PATHS are internal subcommands of RULE.
  - This file is diagnostic/read-only. It does not create, edit, or bind rules.
  - Validation still flows through field_constraints.cpp and rule_catalog.cpp.
```

---

### RULE

Source: `x64base/src/cli/cmd_rule.cpp`  
Owner: `DOT|RULE`  
Category: `validation`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `RULE USAGE`  

Purpose:

Inspect rule catalog paths, bindings, and field constraints for the current
  work area.

Usage contract:

```text
RULE
  RULE USAGE
  RULE STATUS
  RULE SHOW <field|ALL>
  RULE LIST
  RULE PATHS
```

Examples:

```text
RULE
  RULE STATUS
  RULE SHOW GPA
  RULE SHOW ALL
  RULE LIST
  RULE PATHS
```

Notes:

```text
RULE with no arguments reports rule status.
  RULE USAGE prints usage and does not require an open table.
  RULE is diagnostic/read-only; it does not create, edit, or bind rules.
```

Related:

```text
VALIDATE
  WHERE
```

Source comments:

```text
cmd_rule.cpp
DotTalk++ RULE diagnostics command.
Public surface:
  RULE
  RULE STATUS
  RULE SHOW <field|ALL>
  RULE LIST
  RULE PATHS
Notes:
  - SHOW / STATUS / LIST / PATHS are internal subcommands of RULE.
  - This file is diagnostic/read-only. It does not create, edit, or bind rules.
  - Validation still flows through field_constraints.cpp and rule_catalog.cpp.
```

---

### SCAN

Source: `src/cli/cmd_scan.cpp`  
Owner: `DOT|SCAN`  
Category: `script`  
Status: `supported`  
Effect: `loop`  
Mutates: `scan-state cursor delegates-command-effects`  
Usage access: `SCAN USAGE`  

Purpose:

Buffer and execute a SCAN...ENDSCAN record loop over the current logical rowset.

Usage contract:

```text
SCAN
  SCAN USAGE
  SCAN FOR <expr>
  ENDSCAN
  ENDSCAN USAGE
```

Notes:

```text
SCAN with no arguments starts buffering a scan block on the current area.
  SCAN FOR <expr> adds a predicate to the scan loop.
  ENDSCAN executes buffered body lines through the canonical command executor.
  Deleted records and active SET FILTER visibility are honored by the scan gate.
  Active order traversal uses shared order_iterator when available, with physical fallback.
  ENDSCAN restores the user's cursor best-effort after execution.
```

Related:

```text
WHILE
  UNTIL
  FOR
  LOOP
```

Source comments:

```text
- Active order: use shared order_iterator (INX/CNX/CDX).
  - If ordered traversal fails, fall back to physical order.
Re-entrancy / nesting policy:
  - Only one SCAN block may be buffered at a time.
  - Nested SCAN during ENDSCAN execution is not allowed.
  - Recursive ENDSCAN is not allowed.
  - Buffering lines during ENDSCAN execution is not allowed.
Execution policy:
  - SCAN control verbs inside the SCAN body are ignored.
  - ENDSCAN preserves the user's current cursor position on exit.
  - Buffered body lines replay through the canonical loop executor so
    shell shortcuts (e.g. TUP -> TUPLE) work the same as at the prompt.
```

---

### SCAN

Source: `x64base/src/cli/cmd_scan.cpp`  
Owner: `DOT|SCAN`  
Category: `script`  
Status: `supported`  
Effect: `loop`  
Mutates: `scan-state cursor delegates-command-effects`  
Usage access: `SCAN USAGE`  

Purpose:

Buffer and execute a SCAN...ENDSCAN record loop over the current logical rowset.

Usage contract:

```text
SCAN
  SCAN USAGE
  SCAN FOR <expr>
  ENDSCAN
  ENDSCAN USAGE
```

Notes:

```text
SCAN with no arguments starts buffering a scan block on the current area.
  SCAN FOR <expr> adds a predicate to the scan loop.
  ENDSCAN executes buffered body lines through the canonical command executor.
  Deleted records and active SET FILTER visibility are honored by the scan gate.
  Active order traversal uses shared order_iterator when available, with physical fallback.
  ENDSCAN restores the user's cursor best-effort after execution.
```

Related:

```text
WHILE
  UNTIL
  FOR
  LOOP
```

Source comments:

```text
- Active order: use shared order_iterator (INX/CNX/CDX).
  - If ordered traversal fails, fall back to physical order.
Re-entrancy / nesting policy:
  - Only one SCAN block may be buffered at a time.
  - Nested SCAN during ENDSCAN execution is not allowed.
  - Recursive ENDSCAN is not allowed.
  - Buffering lines during ENDSCAN execution is not allowed.
Execution policy:
  - SCAN control verbs inside the SCAN body are ignored.
  - ENDSCAN preserves the user's current cursor position on exit.
  - Buffered body lines replay through the canonical loop executor so
    shell shortcuts (e.g. TUP -> TUPLE) work the same as at the prompt.
```

---

### SCHEMAS

Source: `src/cli/cmd_schemas.cpp`  
Owner: `DOT|SCHEMAS`  
Category: `compatibility`  
Status: `deprecated-compat`  
Effect: `workspace`  
Mutates: `workspace-through-routed-command`  
Usage access: `SCHEMAS USAGE`  

Purpose:

Deprecated compatibility shim that routes old SCHEMAS commands to WORKSPACE.

Usage contract:

```text
SCHEMAS
  SCHEMAS USAGE
  SCHEMAS OPEN <arg>
  SCHEMAS CLOSE
```

Notes:

```text
SCHEMAS with no arguments still routes to WORKSPACE list behavior.
  SCHEMAS OPEN <arg> routes to WORKSPACE OPEN <arg>.
  SCHEMAS CLOSE routes to WORKSPACE CLOSE.
  SCHEMAS USAGE prints compatibility guidance and does not route to WORKSPACE.
  WORKSPACE owns live area/session behavior; DDL owns schema/definition work.
```

Related:

```text
WORKSPACE
  DDL
  WSREPORT
```

Source comments:

```text
src/cli/cmd_schemas.cpp
SCHEMAS is now a legacy compatibility command.
Canonical command ownership:
  WORKSPACE / WS : live work-area/session open/close/list/save/load
  DDL            : schema/definition work
  WSREPORT       : workspace diagnostics/reporting
This file intentionally contains only a shim so old DTS scripts keep
working while new scripts move to WORKSPACE.
```

---

### SCHEMAS

Source: `x64base/src/cli/cmd_schemas.cpp`  
Owner: `DOT|SCHEMAS`  
Category: `compatibility`  
Status: `deprecated-compat`  
Effect: `workspace`  
Mutates: `workspace-through-routed-command`  
Usage access: `SCHEMAS USAGE`  

Purpose:

Deprecated compatibility shim that routes old SCHEMAS commands to WORKSPACE.

Usage contract:

```text
SCHEMAS
  SCHEMAS USAGE
  SCHEMAS OPEN <arg>
  SCHEMAS CLOSE
```

Notes:

```text
SCHEMAS with no arguments still routes to WORKSPACE list behavior.
  SCHEMAS OPEN <arg> routes to WORKSPACE OPEN <arg>.
  SCHEMAS CLOSE routes to WORKSPACE CLOSE.
  SCHEMAS USAGE prints compatibility guidance and does not route to WORKSPACE.
  WORKSPACE owns live area/session behavior; DDL owns schema/definition work.
```

Related:

```text
WORKSPACE
  DDL
  WSREPORT
```

Source comments:

```text
src/cli/cmd_schemas.cpp
SCHEMAS is now a legacy compatibility command.
Canonical command ownership:
  WORKSPACE / WS : live work-area/session open/close/list/save/load
  DDL            : schema/definition work
  WSREPORT       : workspace diagnostics/reporting
This file intentionally contains only a shim so old DTS scripts keep
working while new scripts move to WORKSPACE.
```

---

### SCX

Source: `src/cli/cmd_scx.cpp`  
Owner: `DOT|SCX`  
Category: `index`  
Status: `supported`  
Effect: `mixed`  
Mutates: `scx-index-file`  
Usage access: `SCX USAGE`  

Purpose:

Student/local SCX index-file lab command for creating, tagging, building,
  listing, and inspecting SCX index files.

Usage contract:

```text
SCX USAGE
  SCX CREATE <file>
  SCX ADDTAG <file> <name> FIELD <n>
  SCX ADDTAG <file> <name> FIELD <n> DESC
  SCX BUILD <file>
  SCX TAGS <file>
  SCX INFO <file>
```

Notes:

```text
SCX with no arguments prints usage.
  CREATE writes a new SCX container/file.
  ADDTAG mutates SCX tag metadata.
  BUILD builds SCX contents from the current area.
  TAGS and INFO inspect SCX metadata.
  SCX is separate from the ordinary command-surface CNX/CDX/LMDB abstractions.
```

Related:

```text
IDX
  INDEX
  REINDEX
```

---

### SCX

Source: `x64base/src/cli/cmd_scx.cpp`  
Owner: `DOT|SCX`  
Category: `index`  
Status: `supported`  
Effect: `mixed`  
Mutates: `scx-index-file`  
Usage access: `SCX USAGE`  

Purpose:

Student/local SCX index-file lab command for creating, tagging, building,
  listing, and inspecting SCX index files.

Usage contract:

```text
SCX USAGE
  SCX CREATE <file>
  SCX ADDTAG <file> <name> FIELD <n>
  SCX ADDTAG <file> <name> FIELD <n> DESC
  SCX BUILD <file>
  SCX TAGS <file>
  SCX INFO <file>
```

Notes:

```text
SCX with no arguments prints usage.
  CREATE writes a new SCX container/file.
  ADDTAG mutates SCX tag metadata.
  BUILD builds SCX contents from the current area.
  TAGS and INFO inspect SCX metadata.
  SCX is separate from the ordinary command-surface CNX/CDX/LMDB abstractions.
```

Related:

```text
IDX
  INDEX
  REINDEX
```

---

### SECURITY

Source: `src/cli/cmd_security.cpp`  
Owner: `DOT|SECURITY`  
Category: `diagnostics`  
Status: `supported`  
Effect: `mixed`  
Mutates: `none`  
Usage access: `SECURITY USAGE`  

Purpose:

Display x64Base security policy/runtime diagnostics or run built-in security
  self-tests.

Usage contract:

```text
SECURITY USAGE
  SECURITY SHOW
  SECURITY SELFTEST
  SECURITY RUNTIME
```

Notes:

```text
SECURITY with no arguments prints usage.
  SHOW displays the active policy and profile roots.
  SELFTEST runs built-in security tests.
  RUNTIME describes runtime enforcement rules.
  SECURITY does not mutate table data.
```

Related:

```text
ERROR_TEST
  VALIDATE
```

---

### SECURITY

Source: `x64base/src/cli/cmd_security.cpp`  
Owner: `DOT|SECURITY`  
Category: `diagnostics`  
Status: `supported`  
Effect: `mixed`  
Mutates: `none`  
Usage access: `SECURITY USAGE`  

Purpose:

Display x64Base security policy/runtime diagnostics or run built-in security
  self-tests.

Usage contract:

```text
SECURITY USAGE
  SECURITY SHOW
  SECURITY SELFTEST
  SECURITY RUNTIME
```

Notes:

```text
SECURITY with no arguments prints usage.
  SHOW displays the active policy and profile roots.
  SELFTEST runs built-in security tests.
  RUNTIME describes runtime enforcement rules.
  SECURITY does not mutate table data.
```

Related:

```text
ERROR_TEST
  VALIDATE
```

---

### SEEK

Source: `src/cli/cmd_seek.cpp`  
Owner: `DOT|SEEK`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor seek-trace-state`  
Usage access: `SEEK USAGE`  

Purpose:

Seek a value through the active order/tag or by scanning a specified field.

Usage contract:

```text
SEEK USAGE
  SEEK <value> IN <field> [TRACE ON|OFF]
  SEEK <field> = <value> [TRACE ON|OFF]
  SEEK <field> <value> [TRACE ON|OFF]
  SEEK <value>
  SEEK TRACE ON
  SEEK TRACE OFF
```

Notes:

```text
SEEK USAGE works without an open table.
  Bare SEEK with no open table preserves existing behavior and prints (empty).
  SEEK <value> uses the active order/tag when one is set.
  SET NEAR affects near-match reporting policy.
  SEEK may temporarily move the cursor while searching and leaves the cursor on a found/near match.
```

Related:

```text
FIND
  INDEXSEEK
  SET ORDER
  SET NEAR
```

Source comments:

```text
SEEK <field> <value>
  SEEK TRACE ON|OFF
Notes:
- SEEK USAGE is a usage-contract probe and works without an open table.
- Bare SEEK with no open table preserves current behavior: "(empty)".
- Exact-match semantics by default.
- SET NEAR ON allows active-order SEEK to land on the first near key
  in the current index direction when no exact key exists.
- Comparison is case-insensitive trimmed character comparison,
  matching the previous dev-tool behavior.
- When routed through CDX, iteration follows the current active direction
  and returns the first exact record encountered in that order.
```

---

### SEEK

Source: `x64base/src/cli/cmd_seek.cpp`  
Owner: `DOT|SEEK`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor seek-trace-state`  
Usage access: `SEEK USAGE`  

Purpose:

Seek a value through the active order/tag or by scanning a specified field.

Usage contract:

```text
SEEK USAGE
  SEEK <value> IN <field> [TRACE ON|OFF]
  SEEK <field> = <value> [TRACE ON|OFF]
  SEEK <field> <value> [TRACE ON|OFF]
  SEEK <value>
  SEEK TRACE ON
  SEEK TRACE OFF
```

Notes:

```text
SEEK USAGE works without an open table.
  Bare SEEK with no open table preserves existing behavior and prints (empty).
  SEEK <value> uses the active order/tag when one is set.
  SET NEAR affects near-match reporting policy.
  SEEK may temporarily move the cursor while searching and leaves the cursor on a found/near match.
```

Related:

```text
FIND
  INDEXSEEK
  SET ORDER
  SET NEAR
```

Source comments:

```text
SEEK <field> <value>
  SEEK TRACE ON|OFF
Notes:
- SEEK USAGE is a usage-contract probe and works without an open table.
- Bare SEEK with no open table preserves current behavior: "(empty)".
- Exact-match semantics by default.
- SET NEAR ON allows active-order SEEK to land on the first near key
  in the current index direction when no exact key exists.
- Comparison is case-insensitive trimmed character comparison,
  matching the previous dev-tool behavior.
- When routed through CDX, iteration follows the current active direction
  and returns the first exact record encountered in that order.
```

---

### SELECT

Source: `src/cli/cmd_select.cpp`  
Owner: `DOT|SELECT`  
Category: `workspace`  
Status: `supported`  
Effect: `select`  
Mutates: `current-area`  
Usage access: `SELECT USAGE`  

Purpose:

Select the current work area by numeric slot or by work-area/table name.

Usage contract:

```text
SELECT USAGE
  SELECT <n>
  SELECT <name>
  SELECT <table.dbf>
```

Notes:

```text
SELECT with no arguments prints usage with the current valid slot range.
  SELECT USAGE prints usage and does not change the current area.
  Numeric selection uses the current workarea slot count.
  Name selection matches workarea labels and open DBF base names case-insensitively.
  SELECT mutates current-area/session state but does not mutate table data.
```

Related:

```text
AREA
  DBAREA
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_select.cpp ? SELECT <area#|name>
Supports selecting by numeric slot (0..N-1) or by name/label (case-insensitive).
Name matching checks workareas::name(i) and the DBF base name from DbArea::filename().
Output style (matches your UX):
  Selected area 9.
  Current area: 9
    File: <path>  Recs: <count>  Recno: <current>
Deps: workareas.hpp, xbase.hpp
```

---

### SELECT

Source: `x64base/src/cli/cmd_select.cpp`  
Owner: `DOT|SELECT`  
Category: `workspace`  
Status: `supported`  
Effect: `select`  
Mutates: `current-area`  
Usage access: `SELECT USAGE`  

Purpose:

Select the current work area by numeric slot or by work-area/table name.

Usage contract:

```text
SELECT USAGE
  SELECT <n>
  SELECT <name>
  SELECT <table.dbf>
```

Notes:

```text
SELECT with no arguments prints usage with the current valid slot range.
  SELECT USAGE prints usage and does not change the current area.
  Numeric selection uses the current workarea slot count.
  Name selection matches workarea labels and open DBF base names case-insensitively.
  SELECT mutates current-area/session state but does not mutate table data.
```

Related:

```text
AREA
  DBAREA
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_select.cpp ? SELECT <area#|name>
Supports selecting by numeric slot (0..N-1) or by name/label (case-insensitive).
Name matching checks workareas::name(i) and the DBF base name from DbArea::filename().
Output style (matches your UX):
  Selected area 9.
  Current area: 9
    File: <path>  Recs: <count>  Recno: <current>
Deps: workareas.hpp, xbase.hpp
```

---

### SET

Source: `src/cli/cmd_set.cpp`  
Owner: `DOT|SET`  
Category: `settings`  
Status: `supported`  
Effect: `mixed`  
Mutates: `settings output-routing table-buffer order-state filter-state relation-state path-state`  
Usage access: `SET USAGE`  

Purpose:

General SET dispatcher for session settings, output routing, table buffering,
  paths, case/near behavior, and index/order/filter/relation subcommands.

Usage contract:

```text
SET
  SET USAGE
  SET TABLE BUFFER ON
  SET TABLE BUFFER OFF
  SET TABLE BUFFER ON ALL
  SET TABLE BUFFER OFF ALL
  SET CONSOLE ON
  SET CONSOLE OFF
  SET PRINT ON
  SET PRINT OFF
  SET PRINT TO <file>
  SET DEVICE TO SCREEN
  SET DEVICE TO FILE <path>
  SET DEVICE TO PRINTER
  SET DEVICE TO NULL
  SET ALTERNATE ON
  SET ALTERNATE OFF
  SET ALTERNATE TO <file>
  SET TALK ON
  SET TALK OFF
  SET ECHO ON
  SET ECHO OFF
  SET PAGING ON
  SET PAGING OFF
  SET WRAP ON
  SET WRAP OFF
  SET DELETED ON
  SET DELETED OFF
  SET CASE ON
  SET CASE OFF
  SET NEAR ON
  SET NEAR OFF
  SET EDITOR TO <value>
  SET EDITOR TO DEFAULT
  SET EDITOR TO OFF
  SET LANGUAGE
  SET LANGUAGE TO <locale|DEFAULT>
  SET LOCALE
  SET LOCALE TO <locale|DEFAULT>
  SET LANGUAGE CHECK
  SET LANGUAGE REPORT
  SET LOCALE CHECK
  SET LOCALE REPORT
  SET PATH <slot> <path>
  SET INDEX <args>
  SET ORDER <args>
  SET FILTER <args>
  SET RELATION <args>
  SET CNX <args>
  SET CDX <args>
  SET LMDB <args>
```

Notes:

```text
SET with no arguments shows usage.
  SET USAGE shows usage without mutating settings.
  SET PATH, INDEX, ORDER, FILTER, RELATION, CNX, CDX, and LMDB delegate to their command handlers.
  Output routing settings mutate session output behavior only.
  TABLE BUFFER toggles table buffering state for the current area or all open areas.
  SET CASE and SET NEAR mutate expression/search behavior settings.
  SET may mutate table-buffer, order, path, relation, filter, and output state depending on the option.
```

Related:

```text
SETPATH
  SETINDEX
  SETORDER
  SETFILTER
  SET_RELATION
  SETCASE
  SETNEAR
```

Source comments:

```text
src/cli/cmd_set.cpp
FoxPro-style SET command router for DotTalk++
```

---

### SET

Source: `x64base/src/cli/cmd_set.cpp`  
Owner: `DOT|SET`  
Category: `settings`  
Status: `supported`  
Effect: `mixed`  
Mutates: `settings output-routing table-buffer order-state filter-state relation-state path-state`  
Usage access: `SET USAGE`  

Purpose:

General SET dispatcher for session settings, output routing, table buffering,
  paths, case/near behavior, and index/order/filter/relation subcommands.

Usage contract:

```text
SET
  SET USAGE
  SET TABLE BUFFER ON
  SET TABLE BUFFER OFF
  SET TABLE BUFFER ON ALL
  SET TABLE BUFFER OFF ALL
  SET CONSOLE ON
  SET CONSOLE OFF
  SET PRINT ON
  SET PRINT OFF
  SET PRINT TO <file>
  SET DEVICE TO SCREEN
  SET DEVICE TO FILE <path>
  SET DEVICE TO PRINTER
  SET DEVICE TO NULL
  SET ALTERNATE ON
  SET ALTERNATE OFF
  SET ALTERNATE TO <file>
  SET TALK ON
  SET TALK OFF
  SET ECHO ON
  SET ECHO OFF
  SET PAGING ON
  SET PAGING OFF
  SET WRAP ON
  SET WRAP OFF
  SET DELETED ON
  SET DELETED OFF
  SET CASE ON
  SET CASE OFF
  SET NEAR ON
  SET NEAR OFF
  SET EDITOR TO <value>
  SET EDITOR TO DEFAULT
  SET EDITOR TO OFF
  SET LANGUAGE
  SET LANGUAGE TO <locale|DEFAULT>
  SET LOCALE
  SET LOCALE TO <locale|DEFAULT>
  SET LANGUAGE CHECK
  SET LANGUAGE REPORT
  SET LOCALE CHECK
  SET LOCALE REPORT
  SET PATH <slot> <path>
  SET INDEX <args>
  SET ORDER <args>
  SET FILTER <args>
  SET RELATION <args>
  SET CNX <args>
  SET CDX <args>
  SET LMDB <args>
```

Notes:

```text
SET with no arguments shows usage.
  SET USAGE shows usage without mutating settings.
  SET PATH, INDEX, ORDER, FILTER, RELATION, CNX, CDX, and LMDB delegate to their command handlers.
  Output routing settings mutate session output behavior only.
  TABLE BUFFER toggles table buffering state for the current area or all open areas.
  SET CASE and SET NEAR mutate expression/search behavior settings.
  SET may mutate table-buffer, order, path, relation, filter, and output state depending on the option.
```

Related:

```text
SETPATH
  SETINDEX
  SETORDER
  SETFILTER
  SET_RELATION
  SETCASE
  SETNEAR
```

Source comments:

```text
src/cli/cmd_set.cpp
FoxPro-style SET command router for DotTalk++
```

---

### SET CASE

Source: `src/cli/cmd_setcase.cpp`  
Owner: `DOT|SET CASE`  
Category: `settings`  
Status: `supported`  
Effect: `configure`  
Mutates: `case-sensitivity-setting`  
Usage access: `SET CASE USAGE`  

Purpose:

Report or set predicate/expression case-sensitivity behavior.

Usage contract:

```text
SET CASE
  SET CASE USAGE
  SET CASE ON
  SET CASE OFF
  SETCASE
  SETCASE USAGE
  SETCASE ON
  SETCASE OFF
```

Notes:

```text
SET CASE with no arguments reports current case sensitivity.
  SETCASE with no arguments reports current case sensitivity.
  ON, TRUE, and 1 enable case-sensitive predicate behavior.
  OFF, FALSE, and 0 disable case-sensitive predicate behavior.
```

Related:

```text
SET
  SET NEAR
  LOCATE
  FIND
```

Source comments:

```text
src/cli/cmd_setcase.cpp
```

---

### SET CASE

Source: `x64base/src/cli/cmd_setcase.cpp`  
Owner: `DOT|SET CASE`  
Category: `settings`  
Status: `supported`  
Effect: `configure`  
Mutates: `case-sensitivity-setting`  
Usage access: `SET CASE USAGE`  

Purpose:

Report or set predicate/expression case-sensitivity behavior.

Usage contract:

```text
SET CASE
  SET CASE USAGE
  SET CASE ON
  SET CASE OFF
  SETCASE
  SETCASE USAGE
  SETCASE ON
  SETCASE OFF
```

Notes:

```text
SET CASE with no arguments reports current case sensitivity.
  SETCASE with no arguments reports current case sensitivity.
  ON, TRUE, and 1 enable case-sensitive predicate behavior.
  OFF, FALSE, and 0 disable case-sensitive predicate behavior.
```

Related:

```text
SET
  SET NEAR
  LOCATE
  FIND
```

Source comments:

```text
src/cli/cmd_setcase.cpp
```

---

### SET CDX

Source: `src/cli/cmd_setcdx.cpp`  
Owner: `DOT|SET CDX`  
Category: `index`  
Status: `supported`  
Effect: `attach`  
Mutates: `order-state`  
Usage access: `SET CDX USAGE`  

Purpose:

Attach a CDX index container to the current area order state, using an explicit
  name/path or the current table default.

Usage contract:

```text
SET CDX USAGE
  SET CDX
  SET CDX <name-or-path>
  SETCDX
  SETCDX USAGE
  SETCDX <name-or-path>
```

Notes:

```text
SET CDX with no arguments resolves the default <table>.cdx container.
  Relative names resolve through the INDEXES path slot.
  The target file must exist.
  Attachment is owned by the order subsystem.
  This mutates order/session state but not table records.
```

Related:

```text
SET INDEX
  SET ORDER
  CDX
```

Source comments:

```text
src/cli/cmd_setcdx.cpp
SET CDX [<name-or-path>]
Resolve CDX using SET PATH INDEXES slot via cli/path_resolver.
```

---

### SET CDX

Source: `x64base/src/cli/cmd_setcdx.cpp`  
Owner: `DOT|SET CDX`  
Category: `index`  
Status: `supported`  
Effect: `attach`  
Mutates: `order-state`  
Usage access: `SET CDX USAGE`  

Purpose:

Attach a CDX index container to the current area order state, using an explicit
  name/path or the current table default.

Usage contract:

```text
SET CDX USAGE
  SET CDX
  SET CDX <name-or-path>
  SETCDX
  SETCDX USAGE
  SETCDX <name-or-path>
```

Notes:

```text
SET CDX with no arguments resolves the default <table>.cdx container.
  Relative names resolve through the INDEXES path slot.
  The target file must exist.
  Attachment is owned by the order subsystem.
  This mutates order/session state but not table records.
```

Related:

```text
SET INDEX
  SET ORDER
  CDX
```

Source comments:

```text
src/cli/cmd_setcdx.cpp
SET CDX [<name-or-path>]
Resolve CDX using SET PATH INDEXES slot via cli/path_resolver.
```

---

### SET CNX

Source: `src/cli/cmd_setcnx.cpp`  
Owner: `DOT|SET CNX`  
Category: `index`  
Status: `supported`  
Effect: `attach`  
Mutates: `order-state`  
Usage access: `SET CNX USAGE`  

Purpose:

Attach a CNX index container to the current area order state, using an explicit
  name/path or the current table default.

Usage contract:

```text
SET CNX USAGE
  SET CNX
  SET CNX <name-or-path>
  SETCNX
  SETCNX USAGE
  SETCNX <name-or-path>
```

Notes:

```text
SET CNX with no arguments resolves the default <table>.cnx container.
  Relative names resolve through the INDEXES path slot.
  The target file must exist.
  Attachment is owned by the order subsystem.
  This mutates order/session state but not table records.
```

Related:

```text
SET INDEX
  SET ORDER
  CNX
```

Source comments:

```text
src/cli/cmd_setcnx.cpp
SET CNX [<name-or-path>]
Resolve CNX using SET PATH INDEXES slot via cli/path_resolver.
```

---

### SET CNX

Source: `x64base/src/cli/cmd_setcnx.cpp`  
Owner: `DOT|SET CNX`  
Category: `index`  
Status: `supported`  
Effect: `attach`  
Mutates: `order-state`  
Usage access: `SET CNX USAGE`  

Purpose:

Attach a CNX index container to the current area order state, using an explicit
  name/path or the current table default.

Usage contract:

```text
SET CNX USAGE
  SET CNX
  SET CNX <name-or-path>
  SETCNX
  SETCNX USAGE
  SETCNX <name-or-path>
```

Notes:

```text
SET CNX with no arguments resolves the default <table>.cnx container.
  Relative names resolve through the INDEXES path slot.
  The target file must exist.
  Attachment is owned by the order subsystem.
  This mutates order/session state but not table records.
```

Related:

```text
SET INDEX
  SET ORDER
  CNX
```

Source comments:

```text
src/cli/cmd_setcnx.cpp
SET CNX [<name-or-path>]
Resolve CNX using SET PATH INDEXES slot via cli/path_resolver.
```

---

### SET FILTER

Source: `src/cli/cmd_setfilter.cpp`  
Owner: `DOT|SET FILTER`  
Category: `query`  
Status: `supported`  
Effect: `configure`  
Mutates: `filter-state`  
Usage access: `SET FILTER USAGE`  

Purpose:

Set or clear the per-area filter expression used by selector-backed scans.

Usage contract:

```text
SET FILTER USAGE
  SET FILTER TO <expr>
  SET FILTER TO
  SETFILTER USAGE
  SETFILTER TO <expr>
  SETFILTER TO
```

Notes:

```text
SET FILTER with no arguments shows usage.
  SET FILTER TO with no expression clears the filter.
  SET FILTER TO <expr> validates and activates the filter expression.
  Filter state is keyed by DbArea pointer and also registered with the shared filter registry.
  SET FILTER mutates selection/session state but not table records.
```

Related:

```text
COUNT
  LOCATE
  LIST
  SET
```

---

### SET FILTER

Source: `x64base/src/cli/cmd_setfilter.cpp`  
Owner: `DOT|SET FILTER`  
Category: `query`  
Status: `supported`  
Effect: `configure`  
Mutates: `filter-state`  
Usage access: `SET FILTER USAGE`  

Purpose:

Set or clear the per-area filter expression used by selector-backed scans.

Usage contract:

```text
SET FILTER USAGE
  SET FILTER TO <expr>
  SET FILTER TO
  SETFILTER USAGE
  SETFILTER TO <expr>
  SETFILTER TO
```

Notes:

```text
SET FILTER with no arguments shows usage.
  SET FILTER TO with no expression clears the filter.
  SET FILTER TO <expr> validates and activates the filter expression.
  Filter state is keyed by DbArea pointer and also registered with the shared filter registry.
  SET FILTER mutates selection/session state but not table records.
```

Related:

```text
COUNT
  LOCATE
  LIST
  SET
```

---

### SET INDEX

Source: `src/cli/cmd_setindex.cpp`  
Owner: `DOT|SET INDEX`  
Category: `index`  
Status: `supported`  
Effect: `attach`  
Mutates: `order-state index-backend cursor`  
Usage access: `SET INDEX USAGE`  

Purpose:

Flavor-aware SET INDEX command that attaches INX, CNX, or CDX containers and
  can seed an active tag immediately.

Usage contract:

```text
SET INDEX USAGE
  SET INDEX TO <container>
  SET INDEX TO <container> TAG <tag>
  SET INDEX TO <container> <tag>
  SETINDEX USAGE
  SETINDEX TO <container>
  SETINDEX TO <container> TAG <tag>
  SETINDEX TO <container> <tag>
```

Notes:

```text
SET INDEX requires an open table except for usage.
  Explicit extensions are validated by table flavor.
  v32 tables accept INX or CNX.
  v64 tables require CDX.
  Bare container names resolve through the INDEXES path slot.
  CDX attachment also requires the LMDB environment to exist.
  Container attach and tag activation are treated as related but separate decisions.
  INX is single-order; supplied tag names are accepted but ignored.
  On hard failure, active index/order state is cleared to avoid stale ordering.
```

Related:

```text
SET ORDER
  INDEX
  REINDEX
  CDX
  CNX
```

Source comments:

```text
- SET INDEX TO <container>
    attach container only (current behavior preserved)
- SET INDEX TO <container> TAG <tag>
    attach container and seed the active tag immediately
- SET INDEX TO <container> <tag>
    shorthand form for the same
Behavioral rule:
- Container attach and tag activation are treated as two related decisions.
- If container attach succeeds but tag activation cannot be honored, the
  container should still remain attached.
- For .inx, trailing TAG / bare tag is accepted but ignored, because INX is
  effectively a single-order container.
```

---

### SET INDEX

Source: `x64base/src/cli/cmd_setindex.cpp`  
Owner: `DOT|SET INDEX`  
Category: `index`  
Status: `supported`  
Effect: `attach`  
Mutates: `order-state index-backend cursor`  
Usage access: `SET INDEX USAGE`  

Purpose:

Flavor-aware SET INDEX command that attaches INX, CNX, or CDX containers and
  can seed an active tag immediately.

Usage contract:

```text
SET INDEX USAGE
  SET INDEX TO <container>
  SET INDEX TO <container> TAG <tag>
  SET INDEX TO <container> <tag>
  SETINDEX USAGE
  SETINDEX TO <container>
  SETINDEX TO <container> TAG <tag>
  SETINDEX TO <container> <tag>
```

Notes:

```text
SET INDEX requires an open table except for usage.
  Explicit extensions are validated by table flavor.
  v32 tables accept INX or CNX.
  v64 tables require CDX.
  Bare container names resolve through the INDEXES path slot.
  CDX attachment also requires the LMDB environment to exist.
  Container attach and tag activation are treated as related but separate decisions.
  INX is single-order; supplied tag names are accepted but ignored.
  On hard failure, active index/order state is cleared to avoid stale ordering.
```

Related:

```text
SET ORDER
  INDEX
  REINDEX
  CDX
  CNX
```

Source comments:

```text
- SET INDEX TO <container>
    attach container only (current behavior preserved)
- SET INDEX TO <container> TAG <tag>
    attach container and seed the active tag immediately
- SET INDEX TO <container> <tag>
    shorthand form for the same
Behavioral rule:
- Container attach and tag activation are treated as two related decisions.
- If container attach succeeds but tag activation cannot be honored, the
  container should still remain attached.
- For .inx, trailing TAG / bare tag is accepted but ignored, because INX is
  effectively a single-order container.
```

---

### SET LMDB

Source: `src/cli/cmd_setlmdb.cpp`  
Owner: `DOT|SET LMDB`  
Category: `index`  
Status: `developer`  
Effect: `configure`  
Mutates: `order-state index-backend`  
Usage access: `SET LMDB USAGE`  

Purpose:

Select LMDB-backed CDX ordering per area without touching global LMDB state.

Usage contract:

```text
SET LMDB
  SET LMDB USAGE
  SET LMDB 0
  SET LMDB <stem>
  SET LMDB <container.cdx>
  SET LMDB <envdir.cdx.d>
  SET LMDB <stem> <tag>
  SET LMDB <stem> <tag> --asc
  SET LMDB <stem> <tag> --desc
  SETLMDB
  SETLMDB USAGE
  SETLMDB 0
  SETLMDB <stem> <tag>
```

Notes:

```text
SET LMDB with no arguments reports current LMDB/order state.
  SET LMDB 0 clears ordering and closes the current index manager.
  Bare stems resolve through the INDEXES path slot as <stem>.cdx.
  .cdx.d environment directory tokens normalize back to the public .cdx container.
  Default tag is LNAME when no tag is supplied.
  This command opens the per-area CDX backend and never uses a global LMDB singleton.
```

Related:

```text
LMDB
  SET INDEX
  SET ORDER
  CDX
```

Source comments:

```text
src/cli/cmd_setlmdb.cpp
SETLMDB: select LMDB-backed ordering (container/tag/asc/desc) per area.
Ownership rule enforced here:
  DbArea -> IndexManager -> CdxBackend -> LMDB env
No global LMDB singleton is touched from this command.
Behavior:
  SETLMDB 0                      -> clear ordering (physical)
  SETLMDB                        -> report state
  SETLMDB <stem|cdx|envdir>      -> default tag selection
  SETLMDB <...> <TAG> [--asc|--desc]
```

---

### SET LMDB

Source: `x64base/src/cli/cmd_setlmdb.cpp`  
Owner: `DOT|SET LMDB`  
Category: `index`  
Status: `developer`  
Effect: `configure`  
Mutates: `order-state index-backend`  
Usage access: `SET LMDB USAGE`  

Purpose:

Select LMDB-backed CDX ordering per area without touching global LMDB state.

Usage contract:

```text
SET LMDB
  SET LMDB USAGE
  SET LMDB 0
  SET LMDB <stem>
  SET LMDB <container.cdx>
  SET LMDB <envdir.cdx.d>
  SET LMDB <stem> <tag>
  SET LMDB <stem> <tag> --asc
  SET LMDB <stem> <tag> --desc
  SETLMDB
  SETLMDB USAGE
  SETLMDB 0
  SETLMDB <stem> <tag>
```

Notes:

```text
SET LMDB with no arguments reports current LMDB/order state.
  SET LMDB 0 clears ordering and closes the current index manager.
  Bare stems resolve through the INDEXES path slot as <stem>.cdx.
  .cdx.d environment directory tokens normalize back to the public .cdx container.
  Default tag is LNAME when no tag is supplied.
  This command opens the per-area CDX backend and never uses a global LMDB singleton.
```

Related:

```text
LMDB
  SET INDEX
  SET ORDER
  CDX
```

Source comments:

```text
src/cli/cmd_setlmdb.cpp
SETLMDB: select LMDB-backed ordering (container/tag/asc/desc) per area.
Ownership rule enforced here:
  DbArea -> IndexManager -> CdxBackend -> LMDB env
No global LMDB singleton is touched from this command.
Behavior:
  SETLMDB 0                      -> clear ordering (physical)
  SETLMDB                        -> report state
  SETLMDB <stem|cdx|envdir>      -> default tag selection
  SETLMDB <...> <TAG> [--asc|--desc]
```

---

### SET NEAR

Source: `src/cli/cmd_setnear.cpp`  
Owner: `DOT|SET NEAR`  
Category: `settings`  
Status: `supported`  
Effect: `configure`  
Mutates: `near-search-setting`  
Usage access: `SET NEAR USAGE`  

Purpose:

Report or set SEEK/FIND near-match behavior.

Usage contract:

```text
SET NEAR
  SET NEAR USAGE
  SET NEAR ON
  SET NEAR OFF
  SETNEAR
  SETNEAR USAGE
  SETNEAR ON
  SETNEAR OFF
```

Notes:

```text
SET NEAR with no arguments reports current NEAR state.
  ON, TRUE, and 1 enable nearest greater-or-equal match behavior.
  OFF, FALSE, and 0 require exact matches.
  This mutates search behavior settings only.
```

Related:

```text
SEEK
  FIND
  SET CASE
```

Source comments:

```text
src/cli/cmd_setnear.cpp
```

---

### SET NEAR

Source: `x64base/src/cli/cmd_setnear.cpp`  
Owner: `DOT|SET NEAR`  
Category: `settings`  
Status: `supported`  
Effect: `configure`  
Mutates: `near-search-setting`  
Usage access: `SET NEAR USAGE`  

Purpose:

Report or set SEEK/FIND near-match behavior.

Usage contract:

```text
SET NEAR
  SET NEAR USAGE
  SET NEAR ON
  SET NEAR OFF
  SETNEAR
  SETNEAR USAGE
  SETNEAR ON
  SETNEAR OFF
```

Notes:

```text
SET NEAR with no arguments reports current NEAR state.
  ON, TRUE, and 1 enable nearest greater-or-equal match behavior.
  OFF, FALSE, and 0 require exact matches.
  This mutates search behavior settings only.
```

Related:

```text
SEEK
  FIND
  SET CASE
```

Source comments:

```text
src/cli/cmd_setnear.cpp
```

---

### SET ORDER

Source: `src/cli/cmd_setorder.cpp`  
Owner: `DOT|SET ORDER`  
Category: `index`  
Status: `supported`  
Effect: `configure`  
Mutates: `order-state index-backend cursor`  
Usage access: `SET ORDER USAGE`  

Purpose:

FoxPro-style SET ORDER command with CNX and CDX-aware tag activation.

Usage contract:

```text
SET ORDER
  SET ORDER USAGE
  SET ORDER 0
  SET ORDER PHYSICAL
  SET ORDER NATURAL
  SET ORDER PHYS
  SET ORDER <tag>
  SET ORDER TAG <tag>
  SET ORDER TAG <tag> IN <alias>
  SET ORDER <container> <tag>
  SET ORDER <container> <tag> ASC
  SET ORDER <container> <tag> DESC
  SETORDER
  SETORDER USAGE
  SETORDER <tag>
```

Notes:

```text
SET ORDER with no arguments reports the active order or physical order.
  SET ORDER 0, PHYSICAL, NATURAL, and PHYS clear active order.
  Bare tag forms prefer an already-attached compatible container.
  If no suitable container is attached, fallback is flavor-aware.
  v32 tables default to CNX.
  v64 tables default to CDX.
  IN <alias> modifies the target area without changing the selected area.
  INX activation is intentionally not handled by SET ORDER.
```

Related:

```text
SET INDEX
  SET CDX
  SET CNX
  INDEX
  REINDEX
```

Source comments:

```text
v64 -> <table>.cdx
- For IN <alias>, target area is modified without changing the selected area.
- Numeric tag-number orders remain reserved/minimal for now.
Policy:
- v32: CNX is the tag-container path.
- v64: CDX (LMDB-backed) is the tag-container path.
- INX remains valid for SET INDEX attachment, but tag activation via
  SET ORDER is intentionally not handled here.
CDX policy:
- Public CDX container resolves under INDEXES.
- LMDB backend resolves under LMDB.
- This command validates both paths before attempting backend activation.
```

---

### SET ORDER

Source: `x64base/src/cli/cmd_setorder.cpp`  
Owner: `DOT|SET ORDER`  
Category: `index`  
Status: `supported`  
Effect: `configure`  
Mutates: `order-state index-backend cursor`  
Usage access: `SET ORDER USAGE`  

Purpose:

FoxPro-style SET ORDER command with CNX and CDX-aware tag activation.

Usage contract:

```text
SET ORDER
  SET ORDER USAGE
  SET ORDER 0
  SET ORDER PHYSICAL
  SET ORDER NATURAL
  SET ORDER PHYS
  SET ORDER <tag>
  SET ORDER TAG <tag>
  SET ORDER TAG <tag> IN <alias>
  SET ORDER <container> <tag>
  SET ORDER <container> <tag> ASC
  SET ORDER <container> <tag> DESC
  SETORDER
  SETORDER USAGE
  SETORDER <tag>
```

Notes:

```text
SET ORDER with no arguments reports the active order or physical order.
  SET ORDER 0, PHYSICAL, NATURAL, and PHYS clear active order.
  Bare tag forms prefer an already-attached compatible container.
  If no suitable container is attached, fallback is flavor-aware.
  v32 tables default to CNX.
  v64 tables default to CDX.
  IN <alias> modifies the target area without changing the selected area.
  INX activation is intentionally not handled by SET ORDER.
```

Related:

```text
SET INDEX
  SET CDX
  SET CNX
  INDEX
  REINDEX
```

Source comments:

```text
v64 -> <table>.cdx
- For IN <alias>, target area is modified without changing the selected area.
- Numeric tag-number orders remain reserved/minimal for now.
Policy:
- v32: CNX is the tag-container path.
- v64: CDX (LMDB-backed) is the tag-container path.
- INX remains valid for SET INDEX attachment, but tag activation via
  SET ORDER is intentionally not handled here.
CDX policy:
- Public CDX container resolves under INDEXES.
- LMDB backend resolves under LMDB.
- This command validates both paths before attempting backend activation.
```

---

### SET PATH

Source: `src/cli/cmd_setpath_command.cpp`  
Owner: `DOT|SET PATH`  
Category: `settings`  
Status: `supported`  
Effect: `configure`  
Mutates: `path-state`  
Usage access: `SET PATH USAGE`  

Purpose:

Report, reset, or configure DotTalk++ path slots.

Usage contract:

```text
SETPATH
  SETPATH USAGE
  SETPATH RESET
  SETPATH DATA <path>
  SETPATH DBF <path>
  SETPATH XDBF <path>
  SETPATH INDEXES <path>
  SETPATH LMDB <path>
  SETPATH WORKSPACES <path>
  SETPATH SCHEMAS <path>
  SETPATH PROJECTS <path>
  SETPATH SCRIPTS <path>
  SETPATH TESTS <path>
  SETPATH HELP <path>
  SETPATH LOGS <path>
  SETPATH TMP <path>
  SET PATH <slot> <path>
  SET PATH <slot> TO <path>
  SET PATH <slot> = <path>
```

Notes:

```text
SETPATH with no arguments reports all path slots.
  RESET restores defaults based on the current DATA root.
  SET PATH forms route through SETPATH.
  DATA resolves relative to the application root.
  Other top-level slots resolve relative to the current DATA root.
  Validation is non-blocking; missing or wrong-kind paths warn but assignment still succeeds.
```

Related:

```text
SET
  DDL
  USE
  WORKSPACE
```

Source comments:

```text
SET PATH DBF = xdbf
  SET PATH DBF TO xdbf
  SET PATH DBF TO = xdbf
  SET PATH DBF = TO xdbf
Relative path behavior:
  - DATA resolves relative to the application root (parent of current DATA),
    not the process working directory.
  - All other top-level slots resolve relative to the current DATA root.
  - Validation is non-blocking: missing/wrong-kind paths warn, but assignment
    still succeeds.
Slots:
  DATA DBF XDBF INDEXES LMDB WORKSPACES SCHEMAS PROJECTS SCRIPTS TESTS HELP LOGS TMP
```

---

### SET PATH

Source: `x64base/src/cli/cmd_setpath_command.cpp`  
Owner: `DOT|SET PATH`  
Category: `settings`  
Status: `supported`  
Effect: `configure`  
Mutates: `path-state`  
Usage access: `SET PATH USAGE`  

Purpose:

Report, reset, or configure DotTalk++ path slots.

Usage contract:

```text
SETPATH
  SETPATH USAGE
  SETPATH RESET
  SETPATH DATA <path>
  SETPATH DBF <path>
  SETPATH XDBF <path>
  SETPATH INDEXES <path>
  SETPATH LMDB <path>
  SETPATH WORKSPACES <path>
  SETPATH SCHEMAS <path>
  SETPATH PROJECTS <path>
  SETPATH SCRIPTS <path>
  SETPATH TESTS <path>
  SETPATH HELP <path>
  SETPATH LOGS <path>
  SETPATH TMP <path>
  SET PATH <slot> <path>
  SET PATH <slot> TO <path>
  SET PATH <slot> = <path>
```

Notes:

```text
SETPATH with no arguments reports all path slots.
  RESET restores defaults based on the current DATA root.
  SET PATH forms route through SETPATH.
  DATA resolves relative to the application root.
  Other top-level slots resolve relative to the current DATA root.
  Validation is non-blocking; missing or wrong-kind paths warn but assignment still succeeds.
```

Related:

```text
SET
  DDL
  USE
  WORKSPACE
```

Source comments:

```text
SET PATH DBF = xdbf
  SET PATH DBF TO xdbf
  SET PATH DBF TO = xdbf
  SET PATH DBF = TO xdbf
Relative path behavior:
  - DATA resolves relative to the application root (parent of current DATA),
    not the process working directory.
  - All other top-level slots resolve relative to the current DATA root.
  - Validation is non-blocking: missing/wrong-kind paths warn, but assignment
    still succeeds.
Slots:
  DATA DBF XDBF INDEXES LMDB WORKSPACES SCHEMAS PROJECTS SCRIPTS TESTS HELP LOGS TMP
```

---

### SET RELATION

Source: `src/cli/cmd_set_relation.cpp`  
Owner: `DOT|SET RELATION`  
Category: `relations`  
Status: `supported`  
Effect: `configure`  
Mutates: `relation-state`  
Usage access: `SET RELATION USAGE`  

Purpose:

FoxPro-compatible SET RELATION parser that configures parent-to-child
  relations through the relations_api backend.

Usage contract:

```text
SET RELATION USAGE
  SET RELATION TO <expr> INTO <child>
  SET RELATION TO <expr> INTO <child>, <expr> INTO <child>
  SET RELATION ADDITIVE TO <expr> INTO <child>
  SET RELATION OFF ALL
  SET RELATION OFF INTO <child>
```

Notes:

```text
SET RELATION with no arguments shows usage.
  SET RELATION requires a current parent area except for usage.
  ADDITIVE preserves existing relations and adds more clauses.
  Non-additive SET RELATION clears current parent relations before adding clauses.
  OFF ALL clears all relations for the current parent.
  OFF INTO <child> removes one child relation.
  Expressions are currently field-list strings reused through relations_api field semantics.
```

Related:

```text
REL
  RELATION
  WORKSPACE
  ERSATZ
```

Source comments:

```text
FoxPro-compatible SET RELATION parser
Supported syntax:
  SET RELATION TO <expr> INTO <child>
  SET RELATION TO <expr> INTO <child>, <expr> INTO <child> ...
  SET RELATION ADDITIVE TO <expr> INTO <child>
  SET RELATION OFF ALL
  SET RELATION OFF INTO <child>
Notes:
- Uses the existing relations_api backend from set_relations.cpp.
- Does not synthesize REL text and re-parse it.
- Current implementation treats <expr> as a field list string and reuses
  split_fields_csv semantics via comma splitting if needed later.
```

---

### SET RELATION

Source: `x64base/src/cli/cmd_set_relation.cpp`  
Owner: `DOT|SET RELATION`  
Category: `relations`  
Status: `supported`  
Effect: `configure`  
Mutates: `relation-state`  
Usage access: `SET RELATION USAGE`  

Purpose:

FoxPro-compatible SET RELATION parser that configures parent-to-child
  relations through the relations_api backend.

Usage contract:

```text
SET RELATION USAGE
  SET RELATION TO <expr> INTO <child>
  SET RELATION TO <expr> INTO <child>, <expr> INTO <child>
  SET RELATION ADDITIVE TO <expr> INTO <child>
  SET RELATION OFF ALL
  SET RELATION OFF INTO <child>
```

Notes:

```text
SET RELATION with no arguments shows usage.
  SET RELATION requires a current parent area except for usage.
  ADDITIVE preserves existing relations and adds more clauses.
  Non-additive SET RELATION clears current parent relations before adding clauses.
  OFF ALL clears all relations for the current parent.
  OFF INTO <child> removes one child relation.
  Expressions are currently field-list strings reused through relations_api field semantics.
```

Related:

```text
REL
  RELATION
  WORKSPACE
  ERSATZ
```

Source comments:

```text
FoxPro-compatible SET RELATION parser
Supported syntax:
  SET RELATION TO <expr> INTO <child>
  SET RELATION TO <expr> INTO <child>, <expr> INTO <child> ...
  SET RELATION ADDITIVE TO <expr> INTO <child>
  SET RELATION OFF ALL
  SET RELATION OFF INTO <child>
Notes:
- Uses the existing relations_api backend from set_relations.cpp.
- Does not synthesize REL text and re-parse it.
- Current implementation treats <expr> as a field list string and reuses
  split_fields_csv semantics via comma splitting if needed later.
```

---

### SET UNIQUE

Source: `src/cli/cmd_setunique.cpp`  
Owner: `DOT|SET UNIQUE`  
Category: `constraints`  
Status: `supported`  
Effect: `configure`  
Mutates: `unique-field-registry`  
Usage access: `SET UNIQUE USAGE`  

Purpose:

Report or configure per-table unique-field registry entries.

Usage contract:

```text
SET UNIQUE
  SET UNIQUE USAGE
  SET UNIQUE FIELD <name> ON
  SET UNIQUE FIELD <name> OFF
```

Notes:

```text
SET UNIQUE with no arguments lists current unique fields.
  FIELD <name> ON marks a field as unique in the registry.
  FIELD <name> OFF clears the unique marker.
  This mutates uniqueness metadata only; it does not rewrite table records.
```

Related:

```text
SET
  FIELDMGR
  CREATE
```

Source comments:

```text
SET UNIQUE FIELD <name> ON|OFF
Lists current unique fields if called without args.
```

---

### SET UNIQUE

Source: `x64base/src/cli/cmd_setunique.cpp`  
Owner: `DOT|SET UNIQUE`  
Category: `constraints`  
Status: `supported`  
Effect: `configure`  
Mutates: `unique-field-registry`  
Usage access: `SET UNIQUE USAGE`  

Purpose:

Report or configure per-table unique-field registry entries.

Usage contract:

```text
SET UNIQUE
  SET UNIQUE USAGE
  SET UNIQUE FIELD <name> ON
  SET UNIQUE FIELD <name> OFF
```

Notes:

```text
SET UNIQUE with no arguments lists current unique fields.
  FIELD <name> ON marks a field as unique in the registry.
  FIELD <name> OFF clears the unique marker.
  This mutates uniqueness metadata only; it does not rewrite table records.
```

Related:

```text
SET
  FIELDMGR
  CREATE
```

Source comments:

```text
SET UNIQUE FIELD <name> ON|OFF
Lists current unique fields if called without args.
```

---

### SETPATH

Source: `src/cli/cmd_setpath.cpp`  
Owner: `DOT|SETPATH_PATHS_IMPL`  
Category: `environment-helper`  
Status: `implementation-helper`  
Effect: `path-slot-support`  
Mutates: `path-slots-through-api`  
Usage access: `owned-by cmd_setpath_command.cpp`  

Purpose:

Path-slot support implementation used by SETPATH and related commands.

Usage contract:

```text
This file does not export cmd_SETPATH.
  Runtime SETPATH usage is owned by the command handler in cmd_setpath_command.cpp.
```

Notes:

```text
This file owns path-slot normalization, defaults, and dump/report support.
  Do not add shell dispatch here unless SETPATH ownership is moved deliberately.
```

---

### SETPATH

Source: `x64base/src/cli/cmd_setpath.cpp`  
Owner: `DOT|SETPATH_PATHS_IMPL`  
Category: `environment-helper`  
Status: `implementation-helper`  
Effect: `path-slot-support`  
Mutates: `path-slots-through-api`  
Usage access: `owned-by cmd_setpath_command.cpp`  

Purpose:

Path-slot support implementation used by SETPATH and related commands.

Usage contract:

```text
This file does not export cmd_SETPATH.
  Runtime SETPATH usage is owned by the command handler in cmd_setpath_command.cpp.
```

Notes:

```text
This file owns path-slot normalization, defaults, and dump/report support.
  Do not add shell dispatch here unless SETPATH ownership is moved deliberately.
```

---

### SFTP

Source: `src/cli/cmd_sftp.cpp`  
Owner: `DOT|SFTP`  
Category: `network`  
Status: `supported`  
Effect: `network-or-file`  
Mutates: `optional-filesystem remote-filesystem`  
Usage access: `SFTP USAGE`  

Purpose:

Wrap the system OpenSSH sftp client for LS, GET, and PUT file transfer.

Usage contract:

```text
SFTP USAGE
  SFTP LS <user@host:/remote/path>
  SFTP GET <user@host:/remote/file> TO <local-file>
  SFTP PUT <local-file> TO <user@host:/remote/file>
```

Examples:

```text
SFTP LS derald@example.com:/home/derald/data
  SFTP GET derald@example.com:/home/derald/data/students.dbf TO students.dbf
  SFTP PUT students.dbf TO derald@example.com:/home/derald/data/students.dbf
```

Notes:

```text
SFTP USAGE prints usage and does not start the sftp client.
  This command stages a temporary sftp batch file and invokes the system sftp client.
  Password embedding in URLs is deliberately not supported.
```

Related:

```text
WEB
  PSHELL
```

Source comments:

```text
SFTP LS user@host:/remote/path
  SFTP GET user@host:/remote/file TO local-file
  SFTP PUT local-file TO user@host:/remote/file
Also accepted:
  SFTP LS sftp://user@host/remote/path
  SFTP GET sftp://user@host/remote/file TO local-file
  SFTP PUT local-file TO sftp://user@host/remote/file
Notes:
  - Port selection is deliberately deferred.
  - Password embedding in URLs is deliberately not supported.
  - This module stages a temporary sftp batch file and invokes:
      sftp -b <batch-file> <user@host>
```

---

### SFTP

Source: `x64base/src/cli/cmd_sftp.cpp`  
Owner: `DOT|SFTP`  
Category: `network`  
Status: `supported`  
Effect: `network-or-file`  
Mutates: `optional-filesystem remote-filesystem`  
Usage access: `SFTP USAGE`  

Purpose:

Wrap the system OpenSSH sftp client for LS, GET, and PUT file transfer.

Usage contract:

```text
SFTP USAGE
  SFTP LS <user@host:/remote/path>
  SFTP GET <user@host:/remote/file> TO <local-file>
  SFTP PUT <local-file> TO <user@host:/remote/file>
```

Examples:

```text
SFTP LS derald@example.com:/home/derald/data
  SFTP GET derald@example.com:/home/derald/data/students.dbf TO students.dbf
  SFTP PUT students.dbf TO derald@example.com:/home/derald/data/students.dbf
```

Notes:

```text
SFTP USAGE prints usage and does not start the sftp client.
  This command stages a temporary sftp batch file and invokes the system sftp client.
  Password embedding in URLs is deliberately not supported.
```

Related:

```text
WEB
  PSHELL
```

Source comments:

```text
SFTP LS user@host:/remote/path
  SFTP GET user@host:/remote/file TO local-file
  SFTP PUT local-file TO user@host:/remote/file
Also accepted:
  SFTP LS sftp://user@host/remote/path
  SFTP GET sftp://user@host/remote/file TO local-file
  SFTP PUT local-file TO sftp://user@host/remote/file
Notes:
  - Port selection is deliberately deferred.
  - Password embedding in URLs is deliberately not supported.
  - This module stages a temporary sftp batch file and invokes:
      sftp -b <batch-file> <user@host>
```

---

### SHOW

Source: `src/cli/cmd_sql_show.cpp`  
Owner: `DOT|SHOW`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor-temporary`  
Usage access: `SHOW USAGE`  

Purpose:

Show table, column, or active order/index information for the current work
  area.

Usage contract:

```text
SHOW
  SHOW USAGE
  SHOW COLUMNS
  SHOW TABLE
  SHOW INDEX
```

Examples:

```text
SHOW
  SHOW COLUMNS
  SHOW TABLE
  SHOW INDEX
```

Notes:

```text
SHOW with no arguments displays columns.
  SHOW TABLE scans records to count deleted rows and restores cursor best-effort.
  SHOW INDEX reports physical/order/tag state when available.
  SHOW USAGE prints usage before open-table checks or cursor movement.
```

Related:

```text
STRUCT
  DISPLAY
  SET ORDER
```

Source comments:

```text
src/cli/cmd_sql_show.cpp
SHOW family: SHOW TABLE | SHOW COLUMNS | SHOW INDEX
- SHOW TABLE   : one-screen summary of current work area
- SHOW COLUMNS : column layout (similar to FIELDS/STRUCT but compact)
- SHOW INDEX   : order/index summary (graceful on non-order builds)
```

---

### SHOW

Source: `x64base/src/cli/cmd_sql_show.cpp`  
Owner: `DOT|SHOW`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor-temporary`  
Usage access: `SHOW USAGE`  

Purpose:

Show table, column, or active order/index information for the current work
  area.

Usage contract:

```text
SHOW
  SHOW USAGE
  SHOW COLUMNS
  SHOW TABLE
  SHOW INDEX
```

Examples:

```text
SHOW
  SHOW COLUMNS
  SHOW TABLE
  SHOW INDEX
```

Notes:

```text
SHOW with no arguments displays columns.
  SHOW TABLE scans records to count deleted rows and restores cursor best-effort.
  SHOW INDEX reports physical/order/tag state when available.
  SHOW USAGE prints usage before open-table checks or cursor movement.
```

Related:

```text
STRUCT
  DISPLAY
  SET ORDER
```

Source comments:

```text
src/cli/cmd_sql_show.cpp
SHOW family: SHOW TABLE | SHOW COLUMNS | SHOW INDEX
- SHOW TABLE   : one-screen summary of current work area
- SHOW COLUMNS : column layout (similar to FIELDS/STRUCT but compact)
- SHOW INDEX   : order/index summary (graceful on non-order builds)
```

---

### SHOWINI

Source: `src/cli/cmd_showini.cpp`  
Owner: `DOT|SHOWINI`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `SHOWINI USAGE`  

Purpose:

Display a table-specific .ini file, either derived from the current table or
  from an explicit file/path.

Usage contract:

```text
SHOWINI
  SHOWINI USAGE
  SHOWINI <table-or-ini>
  SHOWINI PATH <ini-file>
```

Examples:

```text
SHOWINI
  SHOWINI students
  SHOWINI students.ini
  SHOWINI PATH d:\data\students.ini
```

Notes:

```text
SHOWINI with no arguments derives the .ini path from the current table.
  SHOWINI USAGE prints usage before open-table checks or file reads.
  SHOWINI reads .ini files and prints parsed sections/keys; it does not write files.
```

Related:

```text
SHOWINI
  SETPATH
  STATUS
```

Source comments:

```text
cmd_showini.cpp
DotTalk++ SHOWINI command
Displays table.ini contents
```

---

### SHOWINI

Source: `x64base/src/cli/cmd_showini.cpp`  
Owner: `DOT|SHOWINI`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `SHOWINI USAGE`  

Purpose:

Display a table-specific .ini file, either derived from the current table or
  from an explicit file/path.

Usage contract:

```text
SHOWINI
  SHOWINI USAGE
  SHOWINI <table-or-ini>
  SHOWINI PATH <ini-file>
```

Examples:

```text
SHOWINI
  SHOWINI students
  SHOWINI students.ini
  SHOWINI PATH d:\data\students.ini
```

Notes:

```text
SHOWINI with no arguments derives the .ini path from the current table.
  SHOWINI USAGE prints usage before open-table checks or file reads.
  SHOWINI reads .ini files and prints parsed sections/keys; it does not write files.
```

Related:

```text
SHOWINI
  SETPATH
  STATUS
```

Source comments:

```text
cmd_showini.cpp
DotTalk++ SHOWINI command
Displays table.ini contents
```

---

### SHUTDOWN

Source: `src/cli/cmd_shutdown.cpp`  
Owner: `DOT|SHUTDOWN`  
Category: `script`  
Status: `supported`  
Effect: `execute`  
Mutates: `delegates-command-effects session filesystem`  
Usage access: `SHUTDOWN USAGE`  

Purpose:

Run the optional shutdown.ini script from the executable directory.

Usage contract:

```text
SHUTDOWN
  SHUTDOWN USAGE
```

Notes:

```text
SHUTDOWN with no arguments looks for shutdown.ini beside the executable and executes it when present.
  SHUTDOWN USAGE prints usage and does not execute shutdown.ini.
  Each non-empty shutdown.ini line is executed through the shell command executor.
  UTF-8 BOM and trailing carriage returns are handled.
  SHUTDOWN may indirectly mutate data, session state, or files depending on script contents.
```

Related:

```text
INIT
  TEST
  DOTSCRIPT
```

Source comments:

```text
src/cli/cmd_shutdown.cpp
Runs optional shutdown script from bin/shutdown.ini
```

---

### SHUTDOWN

Source: `x64base/src/cli/cmd_shutdown.cpp`  
Owner: `DOT|SHUTDOWN`  
Category: `script`  
Status: `supported`  
Effect: `execute`  
Mutates: `delegates-command-effects session filesystem`  
Usage access: `SHUTDOWN USAGE`  

Purpose:

Run the optional shutdown.ini script from the executable directory.

Usage contract:

```text
SHUTDOWN
  SHUTDOWN USAGE
```

Notes:

```text
SHUTDOWN with no arguments looks for shutdown.ini beside the executable and executes it when present.
  SHUTDOWN USAGE prints usage and does not execute shutdown.ini.
  Each non-empty shutdown.ini line is executed through the shell command executor.
  UTF-8 BOM and trailing carriage returns are handled.
  SHUTDOWN may indirectly mutate data, session state, or files depending on script contents.
```

Related:

```text
INIT
  TEST
  DOTSCRIPT
```

Source comments:

```text
src/cli/cmd_shutdown.cpp
Runs optional shutdown script from bin/shutdown.ini
```

---

### SIMPLEBROWSE

Source: `src/cli/cmd_simple_browser.cpp`  
Owner: `DOT|SIMPLEBROWSE`  
Category: `browser`  
Status: `supported`  
Effect: `launch-ui-or-report`  
Mutates: `cursor-or-ui-state interactive-edit-optional`  
Usage access: `SIMPLEBROWSE USAGE`  

Purpose:

Canonical single-table DBF browser/editor, order-aware through the shared
  order iterator.

Usage contract:

```text
SIMPLEBROWSE
  SIMPLEBROWSE USAGE
  SIMPLEBROWSE [FOR <expr>] [RAW|PRETTY] [PAGE <n>] [ALL] [TOP|BOTTOM]
  SIMPLEBROWSE [START KEY <literal>] [QUIET] [EDIT|SESSION]
```

Examples:

```text
SIMPLEBROWSE
  SIMPLEBROWSE PAGE 20
  SIMPLEBROWSE FOR GPA >= 3.0
  SIMPLEBROWSE START KEY SMITH
  SIMPLEBROWSE EDIT
```

Notes:

```text
SIMPLEBROWSE USAGE prints usage before open-table checks or UI launch.
  Non-interactive listing restores the cursor best-effort.
  Interactive edit/session mode intentionally leaves cursor at final position.
  Table mutation occurs only through explicit interactive edit/save/delete actions.
```

Related:

```text
WORKSPACE
  RBROWSE
  SMARTBROWSE
```

Source comments:

```text
R refresh order  |  ? help         | Q quit
Notes:
- Respects active order through shared order_iterator (INX/CNX/CDX).
- START KEY uses existing SEEK (respects current order).
- FOR supports:
    * classic  FOR <field> <op> <value>
    * richer boolean/algebraic expressions via where_eval
- Deleted rows are hidden by default (future: wire to SET DELETED).
- Interactive edit uses DbArea::set(1-based) + writeCurrent(); staging per-record.
- After SAVE/DEL/RECALL, we rebuild the order vector and re-sync the cursor.
- Non-interactive listing restores the original cursor position on exit.
-----------------------------------------------------------------------------
```

---

### SIMPLEBROWSE

Source: `x64base/src/cli/cmd_simple_browser.cpp`  
Owner: `DOT|SIMPLEBROWSE`  
Category: `browser`  
Status: `supported`  
Effect: `launch-ui-or-report`  
Mutates: `cursor-or-ui-state interactive-edit-optional`  
Usage access: `SIMPLEBROWSE USAGE`  

Purpose:

Canonical single-table DBF browser/editor, order-aware through the shared
  order iterator.

Usage contract:

```text
SIMPLEBROWSE
  SIMPLEBROWSE USAGE
  SIMPLEBROWSE [FOR <expr>] [RAW|PRETTY] [PAGE <n>] [ALL] [TOP|BOTTOM]
  SIMPLEBROWSE [START KEY <literal>] [QUIET] [EDIT|SESSION]
```

Examples:

```text
SIMPLEBROWSE
  SIMPLEBROWSE PAGE 20
  SIMPLEBROWSE FOR GPA >= 3.0
  SIMPLEBROWSE START KEY SMITH
  SIMPLEBROWSE EDIT
```

Notes:

```text
SIMPLEBROWSE USAGE prints usage before open-table checks or UI launch.
  Non-interactive listing restores the cursor best-effort.
  Interactive edit/session mode intentionally leaves cursor at final position.
  Table mutation occurs only through explicit interactive edit/save/delete actions.
```

Related:

```text
WORKSPACE
  RBROWSE
  SMARTBROWSE
```

Source comments:

```text
R refresh order  |  ? help         | Q quit
Notes:
- Respects active order through shared order_iterator (INX/CNX/CDX).
- START KEY uses existing SEEK (respects current order).
- FOR supports:
    * classic  FOR <field> <op> <value>
    * richer boolean/algebraic expressions via where_eval
- Deleted rows are hidden by default (future: wire to SET DELETED).
- Interactive edit uses DbArea::set(1-based) + writeCurrent(); staging per-record.
- After SAVE/DEL/RECALL, we rebuild the order vector and re-sync the cursor.
- Non-interactive listing restores the original cursor position on exit.
-----------------------------------------------------------------------------
```

---

### SIX

Source: `src/edu/edu_six.cpp`  
Owner: `EDU|SIX`  
Category: `education-index`  
Status: `implementation-present`  
Effect: `create-build-inspect-index-stub`  
Mutates: `filesystem index-stub`  
Usage access: `SIX USAGE`  

Purpose:

Educational SIX/local-index stub command for create/build/info operations.

Usage contract:

```text
SIX USAGE
  SIX CREATE <file> TAG <name> FIELD <n>
  SIX BUILD <file>
  SIX INFO <file>
```

Examples:

```text
SIX CREATE students.six TAG LNAME FIELD 2
  SIX BUILD students.six
  SIX INFO students.six
```

Notes:

```text
SIX USAGE/HELP/? returns before creating, building, or reading index files.
  This file defines cmd_SIX but does not itself register the command.
```

---

### SIX

Source: `x64base/src/edu/edu_six.cpp`  
Owner: `EDU|SIX`  
Category: `education-index`  
Status: `implementation-present`  
Effect: `create-build-inspect-index-stub`  
Mutates: `filesystem index-stub`  
Usage access: `SIX USAGE`  

Purpose:

Educational SIX/local-index stub command for create/build/info operations.

Usage contract:

```text
SIX USAGE
  SIX CREATE <file> TAG <name> FIELD <n>
  SIX BUILD <file>
  SIX INFO <file>
```

Examples:

```text
SIX CREATE students.six TAG LNAME FIELD 2
  SIX BUILD students.six
  SIX INFO students.six
```

Notes:

```text
SIX USAGE/HELP/? returns before creating, building, or reading index files.
  This file defines cmd_SIX but does not itself register the command.
```

---

### SKIP

Source: `src/cli/cmd_skip.cpp`  
Owner: `DOT|SKIP`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `SKIP USAGE`  

Purpose:

Move the current work-area cursor forward or backward using filter-aware
  navigation selection.

Usage contract:

```text
SKIP
  SKIP USAGE
  SKIP <n>
```

Notes:

```text
SKIP with no arguments moves forward one logical record.
  SKIP <n> moves forward when n is positive and backward when n is negative.
  SKIP 0 rereads the current record.
  SKIP requires an open table except for SKIP USAGE.
  Navigation uses the shared filter-aware selector.
  SKIP mutates cursor position but does not mutate table data.
```

Related:

```text
GOTO
  TOP
  BOTTOM
  GPS
```

---

### SKIP

Source: `x64base/src/cli/cmd_skip.cpp`  
Owner: `DOT|SKIP`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `SKIP USAGE`  

Purpose:

Move the current work-area cursor forward or backward using filter-aware
  navigation selection.

Usage contract:

```text
SKIP
  SKIP USAGE
  SKIP <n>
```

Notes:

```text
SKIP with no arguments moves forward one logical record.
  SKIP <n> moves forward when n is positive and backward when n is negative.
  SKIP 0 rereads the current record.
  SKIP requires an open table except for SKIP USAGE.
  Navigation uses the shared filter-aware selector.
  SKIP mutates cursor position but does not mutate table data.
```

Related:

```text
GOTO
  TOP
  BOTTOM
  GPS
```

---

### SMARTLIST

Source: `src/cli/cmd_smartlist.cpp`  
Owner: `DOT|SMARTLIST`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `SMARTLIST USAGE`  

Purpose:

Filter-aware, order-aware table listing with optional projections, tuple
  output, debug tracing, deleted-record modes, and predicate filtering.

Usage contract:

```text
SMARTLIST
  SMARTLIST USAGE
  SMARTLIST <fields>
  SMARTLIST ALL
  SMARTLIST <limit>
  SMARTLIST NEXT <n>
  SMARTLIST FIRST <n>
  SMARTLIST DELETED
  SMARTLIST DEBUG
  SMARTLIST TUPLES
  SMARTLIST FOR <pred>
```

Notes:

```text
SMARTLIST requires an open table except for SMARTLIST USAGE.
  SMARTLIST with no arguments preserves existing behavior and prints usage before continuing with default listing.
  Field projections are comma-separated.
  ALL removes the output limit.
  NEXT and FIRST limit scan scope.
  DELETED selects deleted records.
  TUPLES emits tuple bridge output.
  DEBUG emits order/filter diagnostics.
  FOR applies predicate filtering.
  SMARTLIST restores the original cursor best-effort after listing.
  SMARTLIST is read-only for table data.
```

Related:

```text
LIST
  COUNT
  LOCATE
  DUMP
```

Source comments:

```text
src/cli/cmd_smartlist.cpp
SMARTLIST — LIST-style output honoring current order with classic or AST-based FOR filtering.
Usage:
  SMARTLIST [ALL | <limit> | DELETED] [DEBUG] [TUPLES] [FOR <pred>]
Notes:
  • Ordering: respects current INX/CNX/CDX/LMDB (ASC/DESC) like LIST.
  • Deletion visibility: default hides deleted unless ALL; "DELETED"
    shows only deleted; "FOR !DELETED" also supported.
  • Filtering: supports classic FOR <field> <op> <value> and AST-style expressions.
    SQL-ish input is normalized via sql_to_dottalk_where before compile.
  • DEBUG: prints a couple of diagnostics.
```

---

### SMARTLIST

Source: `x64base/src/cli/cmd_smartlist.cpp`  
Owner: `DOT|SMARTLIST`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `cursor`  
Usage access: `SMARTLIST USAGE`  

Purpose:

Filter-aware, order-aware table listing with optional projections, tuple
  output, debug tracing, deleted-record modes, and predicate filtering.

Usage contract:

```text
SMARTLIST
  SMARTLIST USAGE
  SMARTLIST <fields>
  SMARTLIST ALL
  SMARTLIST <limit>
  SMARTLIST NEXT <n>
  SMARTLIST FIRST <n>
  SMARTLIST DELETED
  SMARTLIST DEBUG
  SMARTLIST TUPLES
  SMARTLIST FOR <pred>
```

Notes:

```text
SMARTLIST requires an open table except for SMARTLIST USAGE.
  SMARTLIST with no arguments preserves existing behavior and prints usage before continuing with default listing.
  Field projections are comma-separated.
  ALL removes the output limit.
  NEXT and FIRST limit scan scope.
  DELETED selects deleted records.
  TUPLES emits tuple bridge output.
  DEBUG emits order/filter diagnostics.
  FOR applies predicate filtering.
  SMARTLIST restores the original cursor best-effort after listing.
  SMARTLIST is read-only for table data.
```

Related:

```text
LIST
  COUNT
  LOCATE
  DUMP
```

Source comments:

```text
src/cli/cmd_smartlist.cpp
SMARTLIST — LIST-style output honoring current order with classic or AST-based FOR filtering.
Usage:
  SMARTLIST [ALL | <limit> | DELETED] [DEBUG] [TUPLES] [FOR <pred>]
Notes:
  • Ordering: respects current INX/CNX/CDX/LMDB (ASC/DESC) like LIST.
  • Deletion visibility: default hides deleted unless ALL; "DELETED"
    shows only deleted; "FOR !DELETED" also supported.
  • Filtering: supports classic FOR <field> <op> <value> and AST-style expressions.
    SQL-ish input is normalized via sql_to_dottalk_where before compile.
  • DEBUG: prints a couple of diagnostics.
```

---

### SMART_BROWSER

Source: `src/cli/cmd_smart_browser.cpp`  
Owner: `DOT|SMART_BROWSER`  
Category: `browser`  
Status: `supported`  
Effect: `browse`  
Mutates: `cursor`  
Usage access: `SMART_BROWSER USAGE`  

Purpose:

Interactive tuple-stream smart browser with paging, relation child browsing,
  schema/json display toggles, filtering, navigation, and breadcrumbs.

Usage contract:

```text
SMART_BROWSER
  SMART_BROWSER USAGE
  SMART_BROWSER <spec>
  SMART_BROWSER <spec> FOR <expr>
  SMART_BROWSER <spec> PAGESIZE <n>
  SMART_BROWSER <spec> SHOW SCHEMA
  SMART_BROWSER <spec> SHOW JSON
  SMART_BROWSER <spec> STATUS VERBOSE
  SMARTBROWSER
  SMARTBROWSER USAGE
```

Notes:

```text
SMART_BROWSER with no arguments opens the interactive browser using default spec.
  SMARTBROWSER is an alias entrypoint.
  The browser is read-only for table data but traverses tuple streams and may move cursors.
  Work-area cursors are restored best-effort when the browser exits.
  Interactive pager commands include TOP, BOTTOM, SKIP, GOTO, FOR, CLEAR FOR, ORDER, SPEC, SHOW, OPEN CHILD, BACK, STATUS, HELP, and QUIT.
```

Related:

```text
SMARTLIST
  TUPLE
  RBROWSE
```

Source comments:

```text
src/cli/cmd_smart_browser.cpp
```

---

### SMART_BROWSER

Source: `x64base/src/cli/cmd_smart_browser.cpp`  
Owner: `DOT|SMART_BROWSER`  
Category: `browser`  
Status: `supported`  
Effect: `browse`  
Mutates: `cursor`  
Usage access: `SMART_BROWSER USAGE`  

Purpose:

Interactive tuple-stream smart browser with paging, relation child browsing,
  schema/json display toggles, filtering, navigation, and breadcrumbs.

Usage contract:

```text
SMART_BROWSER
  SMART_BROWSER USAGE
  SMART_BROWSER <spec>
  SMART_BROWSER <spec> FOR <expr>
  SMART_BROWSER <spec> PAGESIZE <n>
  SMART_BROWSER <spec> SHOW SCHEMA
  SMART_BROWSER <spec> SHOW JSON
  SMART_BROWSER <spec> STATUS VERBOSE
  SMARTBROWSER
  SMARTBROWSER USAGE
```

Notes:

```text
SMART_BROWSER with no arguments opens the interactive browser using default spec.
  SMARTBROWSER is an alias entrypoint.
  The browser is read-only for table data but traverses tuple streams and may move cursors.
  Work-area cursors are restored best-effort when the browser exits.
  Interactive pager commands include TOP, BOTTOM, SKIP, GOTO, FOR, CLEAR FOR, ORDER, SPEC, SHOW, OPEN CHILD, BACK, STATUS, HELP, and QUIT.
```

Related:

```text
SMARTLIST
  TUPLE
  RBROWSE
```

Source comments:

```text
src/cli/cmd_smart_browser.cpp
```

---

### SORT

Source: `src/cli/cmd_sort.cpp`  
Owner: `DOT|SORT`  
Category: `data`  
Status: `supported`  
Effect: `create`  
Mutates: `filesystem dbf-output cursor`  
Usage access: `SORT USAGE`  

Purpose:

Create a sorted DBF copy from the current table using expression keys,
  optional filters, projection fields, deleted-record selection, and UNIQUE.

Usage contract:

```text
SORT USAGE
  SORT TO <outdbf> ON <expr>
  SORT TO <outdbf> ON <expr> ASC
  SORT TO <outdbf> ON <expr> DESC
  SORT TO <outdbf> ON <expr>, <expr>
  SORT ALL TO <outdbf> ON <expr>
  SORT DELETED TO <outdbf> ON <expr>
  SORT OVERWRITE TO <outdbf> ON <expr>
  SORT TO <outdbf> ON <expr> FOR <expr>
  SORT TO <outdbf> ON <expr> WHILE <expr>
  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>
  SORT TO <outdbf> ON <expr> UNIQUE
```

Notes:

```text
SORT requires an open table except for SORT USAGE.
  SORT creates a DBF output file and refuses existing output unless OVERWRITE is supplied.
  ALL includes deleted records; DELETED selects only deleted records.
  ON accepts one or more key expressions.
  ASC and DESC can be attached to key expressions.
  FOR and WHILE filter selected records.
  FIELDS projects selected fields into the output table.
  UNIQUE suppresses duplicate adjacent key sets after sorting.
  SORT scans the source table and writes a new DBF; it does not mutate source table records.
```

Related:

```text
INDEX
  REINDEX
  COPY TO
  EXPORT
```

---

### SORT

Source: `x64base/src/cli/cmd_sort.cpp`  
Owner: `DOT|SORT`  
Category: `data`  
Status: `supported`  
Effect: `create`  
Mutates: `filesystem dbf-output cursor`  
Usage access: `SORT USAGE`  

Purpose:

Create a sorted DBF copy from the current table using expression keys,
  optional filters, projection fields, deleted-record selection, and UNIQUE.

Usage contract:

```text
SORT USAGE
  SORT TO <outdbf> ON <expr>
  SORT TO <outdbf> ON <expr> ASC
  SORT TO <outdbf> ON <expr> DESC
  SORT TO <outdbf> ON <expr>, <expr>
  SORT ALL TO <outdbf> ON <expr>
  SORT DELETED TO <outdbf> ON <expr>
  SORT OVERWRITE TO <outdbf> ON <expr>
  SORT TO <outdbf> ON <expr> FOR <expr>
  SORT TO <outdbf> ON <expr> WHILE <expr>
  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>
  SORT TO <outdbf> ON <expr> UNIQUE
```

Notes:

```text
SORT requires an open table except for SORT USAGE.
  SORT creates a DBF output file and refuses existing output unless OVERWRITE is supplied.
  ALL includes deleted records; DELETED selects only deleted records.
  ON accepts one or more key expressions.
  ASC and DESC can be attached to key expressions.
  FOR and WHILE filter selected records.
  FIELDS projects selected fields into the output table.
  UNIQUE suppresses duplicate adjacent key sets after sorting.
  SORT scans the source table and writes a new DBF; it does not mutate source table records.
```

Related:

```text
INDEX
  REINDEX
  COPY TO
  EXPORT
```

---

### SQL

Source: `src/cli/cmd_sql.cpp`  
Owner: `DOT|SQL`  
Category: `sql`  
Status: `supported`  
Effect: `query`  
Mutates: `cursor-temporary`  
Usage access: `SQL USAGE`  

Purpose:

Evaluate SQL-like COUNT/FOR predicates over the current DBF work area.

Usage contract:

```text
SQL USAGE
  SQL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>] [VERBOSE]
```

Examples:

```text
SQL COUNT
  SQL COUNT ALL
  SQL COUNT DELETED
  SQL COUNT FOR GPA >= 3.0
  SQL LNAME = "SMITH"
  SQL VERBOSE COUNT FOR GPA >= 3.0
```

Notes:

```text
SQL USAGE prints usage before open-table checks.
  SQL reads records and may temporarily move the cursor.
  SQL does not mutate table data.
```

Related:

```text
SQLSEL
  WHERE
  WHERECACHE
```

Source comments:

```text
src/cli/cmd_sql.cpp
SQL command ? COUNT with optional ALL|DELETED and FOR <expr>.
Uses shared DotTalk evaluator + LRU cache (DOTTALK_WHERECACHE, default 256).
Change: Suppress "false" per-record logs by default. Print per-record lines
only for matches (ok==true). Use VERBOSE to print all (true/false) details.
```

---

### SQL

Source: `x64base/src/cli/cmd_sql.cpp`  
Owner: `DOT|SQL`  
Category: `sql`  
Status: `supported`  
Effect: `query`  
Mutates: `cursor-temporary`  
Usage access: `SQL USAGE`  

Purpose:

Evaluate SQL-like COUNT/FOR predicates over the current DBF work area.

Usage contract:

```text
SQL USAGE
  SQL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>] [VERBOSE]
```

Examples:

```text
SQL COUNT
  SQL COUNT ALL
  SQL COUNT DELETED
  SQL COUNT FOR GPA >= 3.0
  SQL LNAME = "SMITH"
  SQL VERBOSE COUNT FOR GPA >= 3.0
```

Notes:

```text
SQL USAGE prints usage before open-table checks.
  SQL reads records and may temporarily move the cursor.
  SQL does not mutate table data.
```

Related:

```text
SQLSEL
  WHERE
  WHERECACHE
```

Source comments:

```text
src/cli/cmd_sql.cpp
SQL command ? COUNT with optional ALL|DELETED and FOR <expr>.
Uses shared DotTalk evaluator + LRU cache (DOTTALK_WHERECACHE, default 256).
Change: Suppress "false" per-record logs by default. Print per-record lines
only for matches (ok==true). Use VERBOSE to print all (true/false) details.
```

---

### SQLERASE

Source: `src/cli/cmd_sql_erase.cpp`  
Owner: `DOT|SQLERASE`  
Category: `sql`  
Status: `supported`  
Effect: `delete-records`  
Mutates: `table-data`  
Usage access: `SQLERASE USAGE`  

Purpose:

Mark records deleted using SQL-like ERASE FROM <table> WHERE <expr> syntax.

Usage contract:

```text
SQLERASE USAGE
  SQLERASE FROM <table> WHERE <expr>
```

Examples:

```text
SQLERASE FROM STUDENTS WHERE SID = 1001
  SQLERASE FROM STUDENTS WHERE GPA < 1.0
```

Notes:

```text
SQLERASE USAGE prints usage before open-table checks.
  WHERE is required to reduce accidental destructive operations.
  SQLERASE mutates table data by marking matching records deleted.
```

Related:

```text
ERASE
  RECALL
  ZAP
```

---

### SQLERASE

Source: `x64base/src/cli/cmd_sql_erase.cpp`  
Owner: `DOT|SQLERASE`  
Category: `sql`  
Status: `supported`  
Effect: `delete-records`  
Mutates: `table-data`  
Usage access: `SQLERASE USAGE`  

Purpose:

Mark records deleted using SQL-like ERASE FROM <table> WHERE <expr> syntax.

Usage contract:

```text
SQLERASE USAGE
  SQLERASE FROM <table> WHERE <expr>
```

Examples:

```text
SQLERASE FROM STUDENTS WHERE SID = 1001
  SQLERASE FROM STUDENTS WHERE GPA < 1.0
```

Notes:

```text
SQLERASE USAGE prints usage before open-table checks.
  WHERE is required to reduce accidental destructive operations.
  SQLERASE mutates table data by marking matching records deleted.
```

Related:

```text
ERASE
  RECALL
  ZAP
```

---

### SQLHELP

Source: `src/cli/cmd_sql_help.cpp`  
Owner: `DOT|SQLHELP`  
Category: `reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `SQLHELP USAGE`  

Purpose:

Display or search the SQL helper/reference catalog.

Usage contract:

```text
SQLHELP
  SQLHELP USAGE
  SQLHELP LIST-CATEGORIES
  SQLHELP <category>
  SQLHELP <term>
```

Examples:

```text
SQLHELP
  SQLHELP INDEXING
  SQLHELP CREATE-INDEX
  SQLHELP LIST-CATEGORIES
```

Notes:

```text
SQLHELP with no arguments displays the grouped SQL reference.
  SQLHELP USAGE prints command usage without searching the catalog.
  SQLHELP is read-only and does not execute SQL.
```

Related:

```text
SQL
  SHOW
  PSHELL
```

Source comments:

```text
cmd_sql_help.cpp
```

---

### SQLHELP

Source: `x64base/src/cli/cmd_sql_help.cpp`  
Owner: `DOT|SQLHELP`  
Category: `reference`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `SQLHELP USAGE`  

Purpose:

Display or search the SQL helper/reference catalog.

Usage contract:

```text
SQLHELP
  SQLHELP USAGE
  SQLHELP LIST-CATEGORIES
  SQLHELP <category>
  SQLHELP <term>
```

Examples:

```text
SQLHELP
  SQLHELP INDEXING
  SQLHELP CREATE-INDEX
  SQLHELP LIST-CATEGORIES
```

Notes:

```text
SQLHELP with no arguments displays the grouped SQL reference.
  SQLHELP USAGE prints command usage without searching the catalog.
  SQLHELP is read-only and does not execute SQL.
```

Related:

```text
SQL
  SHOW
  PSHELL
```

Source comments:

```text
cmd_sql_help.cpp
```

---

### SQLITE

Source: `src/cli/cmd_sqlite.cpp`  
Owner: `DOT|SQLITE`  
Category: `sql`  
Status: `supported`  
Effect: `mixed`  
Mutates: `sqlite-connection external-sqlite-db`  
Usage access: `SQLITE USAGE`  

Purpose:

Thin SQLite command wrapper for status, connection management, Bible seed
  helpers, metadata inspection, SELECT queries, and EXEC statements.

Usage contract:

```text
SQLITE
  SQLITE USAGE
  SQLITE STATUS
  SQLITE CWD
  SQLITE PWD
  SQLITE VERSION
  SQLITE OPEN <file>
  SQLITE OPEN :memory:
  SQLITE DB <file>
  SQLITE DB :memory:
  SQLITE BIBLE
  SQLITE BIBLECHECK
  SQLITE BIBLECHK
  SQLITE BOOKS
  SQLITE VERSE <ref>
  SQLITE SEARCH <phrase>
  SQLITE LIST <table>
  SQLITE LIST <table> <limit>
  SQLITE COLUMNS <table>
  SQLITE CLOSE
  SQLITE TABLES
  SQLITE SCHEMA
  SQLITE SCHEMA <table-or-view>
  SQLITE EXEC <sql>
  SQLITE SELECT <sql>
```

Notes:

```text
SQLITE with no arguments reports connection status and brief usage.
  SQLITE USAGE, HELP, and question mark print detailed usage.
  OPEN and DB connect to a SQLite database and create it if needed.
  BIBLE and BIBLECHECK open/check the canonical Bible seed database when found.
  EXEC runs non-SELECT SQL and may mutate the external SQLite database.
  SELECT prints query rows and caps output for CLI responsiveness.
  SQLITE is independent of DBF open/order state.
```

Related:

```text
SQLVER
  IMPORT
  EXPORT
```

Source comments:

```text
SQLITE LIST <table> [limit]    -> quick table preview
  SQLITE COLUMNS <table>         -> show table columns
  SQLITE CLOSE                   -> close
  SQLITE TABLES                  -> list user tables/views
  SQLITE SCHEMA [name]           -> show schema rows; optional table/view name
  SQLITE EXEC <sql...>           -> execute non-SELECT SQL
  SQLITE SELECT <sql...>         -> run a SELECT and print rows
Notes:
  - Independent of DBF open/order state.
  - SQLite is an external SQL/RDBMS backend surface, not native DbArea storage.
  - EXEC/SELECT/TABLES/SCHEMA require an explicit SQLITE OPEN first.
  - SELECT output is capped (MAX_SELECT_ROWS) to keep CLI responsive.
```

---

### SQLITE

Source: `x64base/src/cli/cmd_sqlite.cpp`  
Owner: `DOT|SQLITE`  
Category: `sql`  
Status: `supported`  
Effect: `mixed`  
Mutates: `sqlite-connection external-sqlite-db`  
Usage access: `SQLITE USAGE`  

Purpose:

Thin SQLite command wrapper for status, connection management, Bible seed
  helpers, metadata inspection, SELECT queries, and EXEC statements.

Usage contract:

```text
SQLITE
  SQLITE USAGE
  SQLITE STATUS
  SQLITE CWD
  SQLITE PWD
  SQLITE VERSION
  SQLITE OPEN <file>
  SQLITE OPEN :memory:
  SQLITE DB <file>
  SQLITE DB :memory:
  SQLITE BIBLE
  SQLITE BIBLECHECK
  SQLITE BIBLECHK
  SQLITE BOOKS
  SQLITE VERSE <ref>
  SQLITE SEARCH <phrase>
  SQLITE LIST <table>
  SQLITE LIST <table> <limit>
  SQLITE COLUMNS <table>
  SQLITE CLOSE
  SQLITE TABLES
  SQLITE SCHEMA
  SQLITE SCHEMA <table-or-view>
  SQLITE EXEC <sql>
  SQLITE SELECT <sql>
```

Notes:

```text
SQLITE with no arguments reports connection status and brief usage.
  SQLITE USAGE, HELP, and question mark print detailed usage.
  OPEN and DB connect to a SQLite database and create it if needed.
  BIBLE and BIBLECHECK open/check the canonical Bible seed database when found.
  EXEC runs non-SELECT SQL and may mutate the external SQLite database.
  SELECT prints query rows and caps output for CLI responsiveness.
  SQLITE is independent of DBF open/order state.
```

Related:

```text
SQLVER
  IMPORT
  EXPORT
```

Source comments:

```text
SQLITE LIST <table> [limit]    -> quick table preview
  SQLITE COLUMNS <table>         -> show table columns
  SQLITE CLOSE                   -> close
  SQLITE TABLES                  -> list user tables/views
  SQLITE SCHEMA [name]           -> show schema rows; optional table/view name
  SQLITE EXEC <sql...>           -> execute non-SELECT SQL
  SQLITE SELECT <sql...>         -> run a SELECT and print rows
Notes:
  - Independent of DBF open/order state.
  - SQLite is an external SQL/RDBMS backend surface, not native DbArea storage.
  - EXEC/SELECT/TABLES/SCHEMA require an explicit SQLITE OPEN first.
  - SELECT output is capped (MAX_SELECT_ROWS) to keep CLI responsive.
```

---

### SQLSEL

Source: `src/cli/cmd_sql_select.cpp`  
Owner: `DOT|SQLSEL`  
Category: `sql`  
Status: `supported`  
Effect: `query`  
Mutates: `cursor-temporary`  
Usage access: `SQLSEL USAGE`  

Purpose:

Evaluate SQL-like selection predicates over the current DBF work area.

Usage contract:

```text
SQLSEL USAGE
  SQLSEL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>]
```

Examples:

```text
SQLSEL COUNT
  SQLSEL COUNT ALL
  SQLSEL COUNT FOR GPA >= 3.0
  SQLSEL LNAME = "SMITH"
```

Notes:

```text
SQLSEL USAGE prints usage before open-table checks.
  SQLSEL reads records and may temporarily move the cursor.
  SQLSEL does not mutate table data.
```

Related:

```text
SQL
  WHERE
```

Source comments:

```text
src/cli/cmd_sql.cpp
```

---

### SQLSEL

Source: `x64base/src/cli/cmd_sql_select.cpp`  
Owner: `DOT|SQLSEL`  
Category: `sql`  
Status: `supported`  
Effect: `query`  
Mutates: `cursor-temporary`  
Usage access: `SQLSEL USAGE`  

Purpose:

Evaluate SQL-like selection predicates over the current DBF work area.

Usage contract:

```text
SQLSEL USAGE
  SQLSEL [COUNT] [ALL|DELETED] [FOR <expr> | <expr>]
```

Examples:

```text
SQLSEL COUNT
  SQLSEL COUNT ALL
  SQLSEL COUNT FOR GPA >= 3.0
  SQLSEL LNAME = "SMITH"
```

Notes:

```text
SQLSEL USAGE prints usage before open-table checks.
  SQLSEL reads records and may temporarily move the cursor.
  SQLSEL does not mutate table data.
```

Related:

```text
SQL
  WHERE
```

Source comments:

```text
src/cli/cmd_sql.cpp
```

---

### SQLVER

Source: `src/cli/cmd_sqlver.cpp`  
Owner: `DOT|SQLVER`  
Category: `sql`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `SQLVER USAGE`  

Purpose:

Report whether SQLite support is available and print the linked SQLite
  library version when available.

Usage contract:

```text
SQLVER
  SQLVER USAGE
```

Notes:

```text
SQLVER with no arguments reports SQLite availability/version.
  SQLVER is read-only and does not open SQLite databases.
```

Related:

```text
SQLITE
```

Source comments:

```text
src/cli/cmd_sqlver.cpp
```

---

### SQLVER

Source: `x64base/src/cli/cmd_sqlver.cpp`  
Owner: `DOT|SQLVER`  
Category: `sql`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `SQLVER USAGE`  

Purpose:

Report whether SQLite support is available and print the linked SQLite
  library version when available.

Usage contract:

```text
SQLVER
  SQLVER USAGE
```

Notes:

```text
SQLVER with no arguments reports SQLite availability/version.
  SQLVER is read-only and does not open SQLite databases.
```

Related:

```text
SQLITE
```

Source comments:

```text
src/cli/cmd_sqlver.cpp
```

---

### STATUS

Source: `src/cli/cmd_status.cpp`  
Owner: `DOT|STATUS`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `STATUS USAGE`  

Purpose:

Report current or all open work-area status, including workspace occupancy,
  DBF flavor, active order/index state, tags, records, and optional structure details.

Usage contract:

```text
STATUS
  STATUS USAGE
  STATUS ALL
  STATUS VERBOSE
  STATUS ALL VERBOSE
```

Notes:

```text
STATUS with no arguments reports the current work area.
  STATUS ALL reports all open work areas.
  STATUS VERBOSE includes field structure details.
  STATUS is read-only; it reports session/work-area/index state and does not mutate table data.
```

Related:

```text
AREA
  DBAREA
  DBAREAS
  STRUCT
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_status.cpp
```

---

### STATUS

Source: `x64base/src/cli/cmd_status.cpp`  
Owner: `DOT|STATUS`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `STATUS USAGE`  

Purpose:

Report current or all open work-area status, including workspace occupancy,
  DBF flavor, active order/index state, tags, records, and optional structure details.

Usage contract:

```text
STATUS
  STATUS USAGE
  STATUS ALL
  STATUS VERBOSE
  STATUS ALL VERBOSE
```

Notes:

```text
STATUS with no arguments reports the current work area.
  STATUS ALL reports all open work areas.
  STATUS VERBOSE includes field structure details.
  STATUS is read-only; it reports session/work-area/index state and does not mutate table data.
```

Related:

```text
AREA
  DBAREA
  DBAREAS
  STRUCT
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_status.cpp
```

---

### STRUCT

Source: `src/cli/cmd_struct.cpp`  
Owner: `DOT|STRUCT`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `STRUCT USAGE`  

Purpose:

Report DBF field structure and index/container information for the current
  area or all open areas.

Usage contract:

```text
STRUCT
  STRUCT USAGE
  STRUCT INDEX
  STRUCT FIELDS
  STRUCT ALL
  STRUCT ALL INDEX
  STRUCT ALL VERBOSE
```

Notes:

```text
STRUCT with no arguments reports field and index information for the current area.
  STRUCT INDEX is explicit index-info mode; index info is included by default.
  STRUCT FIELDS suppresses index info and reports fields only.
  STRUCT ALL reports all open areas.
  STRUCT ALL VERBOSE includes verbose CNX tag information where available.
  STRUCT is read-only; it reports structure/index metadata and does not mutate table data.
```

Related:

```text
AREA
  DBAREA
  FIELDS
  STATUS
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_struct.cpp
STRUCT / STRUCT INDEX: prints DBF fields + index container info.
Supports:
  STRUCT                -> current area (fields + index info)
  STRUCT INDEX          -> same (explicit index mode)
  STRUCT ALL            -> all open areas
  STRUCT ALL INDEX      -> all open areas + index info
  STRUCT ALL VERBOSE    -> adds CNX tag table where available
```

---

### STRUCT

Source: `src/cli/cmd_struct_basic.cpp`  
Owner: `DOT|STRUCT_BASIC_IMPL`  
Category: `structure-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by STRUCT`  

Purpose:

Minimal translation unit reserved for future STRUCT helper code.

Usage contract:

```text
This file intentionally does not export cmd_STRUCT().
  STRUCT command behavior and usage are owned by the actual STRUCT command implementation.
```

Notes:

```text
Keeping this file minimal avoids duplicate cmd_STRUCT definitions.
  Future shared STRUCT helpers may live here without adding command dispatch.
```

---

### STRUCT

Source: `x64base/src/cli/cmd_struct.cpp`  
Owner: `DOT|STRUCT`  
Category: `workspace`  
Status: `supported`  
Effect: `report`  
Mutates: `no`  
Usage access: `STRUCT USAGE`  

Purpose:

Report DBF field structure and index/container information for the current
  area or all open areas.

Usage contract:

```text
STRUCT
  STRUCT USAGE
  STRUCT INDEX
  STRUCT FIELDS
  STRUCT ALL
  STRUCT ALL INDEX
  STRUCT ALL VERBOSE
```

Notes:

```text
STRUCT with no arguments reports field and index information for the current area.
  STRUCT INDEX is explicit index-info mode; index info is included by default.
  STRUCT FIELDS suppresses index info and reports fields only.
  STRUCT ALL reports all open areas.
  STRUCT ALL VERBOSE includes verbose CNX tag information where available.
  STRUCT is read-only; it reports structure/index metadata and does not mutate table data.
```

Related:

```text
AREA
  DBAREA
  FIELDS
  STATUS
  WORKSPACE
```

Source comments:

```text
src/cli/cmd_struct.cpp
STRUCT / STRUCT INDEX: prints DBF fields + index container info.
Supports:
  STRUCT                -> current area (fields + index info)
  STRUCT INDEX          -> same (explicit index mode)
  STRUCT ALL            -> all open areas
  STRUCT ALL INDEX      -> all open areas + index info
  STRUCT ALL VERBOSE    -> adds CNX tag table where available
```

---

### STRUCT

Source: `x64base/src/cli/cmd_struct_basic.cpp`  
Owner: `DOT|STRUCT_BASIC_IMPL`  
Category: `structure-helper`  
Status: `implementation-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by STRUCT`  

Purpose:

Minimal translation unit reserved for future STRUCT helper code.

Usage contract:

```text
This file intentionally does not export cmd_STRUCT().
  STRUCT command behavior and usage are owned by the actual STRUCT command implementation.
```

Notes:

```text
Keeping this file minimal avoids duplicate cmd_STRUCT definitions.
  Future shared STRUCT helpers may live here without adding command dispatch.
```

---

### STUDENTECHO / SECHO

Source: `src/ext/cmd/cmd_student_echo.cpp`  
Owner: `EXT|STUDENTECHO`  
Category: `extension-example`  
Status: `sample-extension`  
Effect: `report`  
Mutates: `none`  
Usage access: `STUDENTECHO USAGE; SECHO USAGE`  

Purpose:

Student/custom extension sample that echoes the rest of the command line.

Usage contract:

```text
STUDENTECHO USAGE
  STUDENTECHO <text>
  SECHO USAGE
  SECHO <text>
```

Examples:

```text
STUDENTECHO hello
  SECHO hello
```

Notes:

```text
Usage/help/? prints usage before echo output.
  This is a self-registering extension example, not a protected built-in.
```

---

### STUDENTECHO / SECHO

Source: `x64base/src/ext/cmd/cmd_student_echo.cpp`  
Owner: `EXT|STUDENTECHO`  
Category: `extension-example`  
Status: `sample-extension`  
Effect: `report`  
Mutates: `none`  
Usage access: `STUDENTECHO USAGE; SECHO USAGE`  

Purpose:

Student/custom extension sample that echoes the rest of the command line.

Usage contract:

```text
STUDENTECHO USAGE
  STUDENTECHO <text>
  SECHO USAGE
  SECHO <text>
```

Examples:

```text
STUDENTECHO hello
  SECHO hello
```

Notes:

```text
Usage/help/? prints usage before echo output.
  This is a self-registering extension example, not a protected built-in.
```

---

### STUDENTHELLO / SHELLO

Source: `src/ext/cmd/cmd_student_hello.cpp`  
Owner: `EXT|STUDENTHELLO`  
Category: `extension-example`  
Status: `sample-extension`  
Effect: `report`  
Mutates: `none`  
Usage access: `STUDENTHELLO USAGE; SHELLO USAGE`  

Purpose:

Student/custom extension sample that greets a supplied name or message.

Usage contract:

```text
STUDENTHELLO USAGE
  STUDENTHELLO <name-or-message>
  SHELLO USAGE
  SHELLO <name-or-message>
```

Examples:

```text
STUDENTHELLO Derald
  SHELLO class
```

Notes:

```text
Usage/help/? prints usage before greeting output.
  No-argument behavior keeps the existing sample greeting plus usage.
  This is a self-registering extension example, not a protected built-in.
```

---

### STUDENTHELLO / SHELLO

Source: `x64base/src/ext/cmd/cmd_student_hello.cpp`  
Owner: `EXT|STUDENTHELLO`  
Category: `extension-example`  
Status: `sample-extension`  
Effect: `report`  
Mutates: `none`  
Usage access: `STUDENTHELLO USAGE; SHELLO USAGE`  

Purpose:

Student/custom extension sample that greets a supplied name or message.

Usage contract:

```text
STUDENTHELLO USAGE
  STUDENTHELLO <name-or-message>
  SHELLO USAGE
  SHELLO <name-or-message>
```

Examples:

```text
STUDENTHELLO Derald
  SHELLO class
```

Notes:

```text
Usage/help/? prints usage before greeting output.
  No-argument behavior keeps the existing sample greeting plus usage.
  This is a self-registering extension example, not a protected built-in.
```

---

### TEST

Source: `src/cli/cmd_test.cpp`  
Owner: `DOT|TEST`  
Category: `test`  
Status: `supported`  
Effect: `execute`  
Mutates: `delegates test commands session filesystem`  
Usage access: `TEST USAGE`  

Purpose:

Run a DotTalk++ test or script file through the shell command executor,
  with optional log output and verbose echoing.

Usage contract:

```text
TEST USAGE
  TEST <scriptfile>
  TEST <scriptfile> VERBOSE
  TEST <scriptfile> <logfile>
  TEST <scriptfile> <logfile> VERBOSE
```

Examples:

```text
TEST smoke.dts
  TEST smoke.dts VERBOSE
  TEST smoke.dts smoke.log
```

Notes:

```text
TEST with no arguments shows usage.
  TEST resolves the script path through the shell script resolver.
  TEST strips supported inline comments before execution.
  TEST supports line continuation for accumulated logical commands.
  TEST executes accumulated logical commands through the shell command executor.
  TEST reports per-command failures and final processed/error counts.
  TEST can write or truncate a logfile when a logfile argument is supplied.
  TEST delegates side effects to commands in the test file and is not read-only.
```

Related:

```text
DOTSCRIPT
  CMDHELP
  WORKSPACE
  CREATE
  USE
```

Source comments:

```text
src/cli/cmd_test.cpp
```

---

### TEST

Source: `x64base/src/cli/cmd_test.cpp`  
Owner: `DOT|TEST`  
Category: `test`  
Status: `supported`  
Effect: `execute`  
Mutates: `delegates test commands session filesystem`  
Usage access: `TEST USAGE`  

Purpose:

Run a DotTalk++ test or script file through the shell command executor,
  with optional log output and verbose echoing.

Usage contract:

```text
TEST USAGE
  TEST <scriptfile>
  TEST <scriptfile> VERBOSE
  TEST <scriptfile> <logfile>
  TEST <scriptfile> <logfile> VERBOSE
```

Examples:

```text
TEST smoke.dts
  TEST smoke.dts VERBOSE
  TEST smoke.dts smoke.log
```

Notes:

```text
TEST with no arguments shows usage.
  TEST resolves the script path through the shell script resolver.
  TEST strips supported inline comments before execution.
  TEST supports line continuation for accumulated logical commands.
  TEST executes accumulated logical commands through the shell command executor.
  TEST reports per-command failures and final processed/error counts.
  TEST can write or truncate a logfile when a logfile argument is supplied.
  TEST delegates side effects to commands in the test file and is not read-only.
```

Related:

```text
DOTSCRIPT
  CMDHELP
  WORKSPACE
  CREATE
  USE
```

Source comments:

```text
src/cli/cmd_test.cpp
```

---

### TEXT

Source: `src/edu/edu_text.cpp`  
Owner: `EDU|TEXT`  
Category: `utility-editor`  
Status: `supported`  
Effect: `launch-editor`  
Mutates: `filesystem-or-memo-stub depending-on-mode`  
Usage access: `TEXT USAGE`  

Purpose:

Open the text editor with an empty buffer, literal text, a file, or a memo
  field target stub.

Usage contract:

```text
TEXT USAGE
  TEXT
  TEXT <literal text>
  TEXT FILE <path>
  TEXT MEMO <field>
```

Examples:

```text
TEXT
  TEXT hello world
  TEXT FILE notes.txt
  TEXT MEMO NOTES
```

Notes:

```text
TEXT USAGE/HELP/? returns before entering editor mode.
  TEXT with no arguments preserves the existing empty-buffer editor behavior.
  TEXT MEMO remains an integration stub until memo editor wiring is complete.
```

Source comments:

```text
TEXT command.
Current scope:
- TEXT                    -> open editor with empty buffer
- TEXT <literal text>     -> open editor preloaded with literal text
- TEXT FILE <path>        -> edit file contents in-place
- TEXT MEMO <field>       -> validate memo target, leave stub for later wiring
Notes:
- FILE mode now reads the full remaining path, so paths with spaces work.
- MEMO mode remains a deliberate integration stub until memo editor wiring
  is finished.
- Engine truth remains in xbase.hpp / DbArea; this command stays in CLI layer.
==============================
```

---

### TEXT

Source: `x64base/src/edu/edu_text.cpp`  
Owner: `EDU|TEXT`  
Category: `utility-editor`  
Status: `supported`  
Effect: `launch-editor`  
Mutates: `filesystem-or-memo-stub depending-on-mode`  
Usage access: `TEXT USAGE`  

Purpose:

Open the text editor with an empty buffer, literal text, a file, or a memo
  field target stub.

Usage contract:

```text
TEXT USAGE
  TEXT
  TEXT <literal text>
  TEXT FILE <path>
  TEXT MEMO <field>
```

Examples:

```text
TEXT
  TEXT hello world
  TEXT FILE notes.txt
  TEXT MEMO NOTES
```

Notes:

```text
TEXT USAGE/HELP/? returns before entering editor mode.
  TEXT with no arguments preserves the existing empty-buffer editor behavior.
  TEXT MEMO remains an integration stub until memo editor wiring is complete.
```

Source comments:

```text
TEXT command.
Current scope:
- TEXT                    -> open editor with empty buffer
- TEXT <literal text>     -> open editor preloaded with literal text
- TEXT FILE <path>        -> edit file contents in-place
- TEXT MEMO <field>       -> validate memo target, leave stub for later wiring
Notes:
- FILE mode now reads the full remaining path, so paths with spaces work.
- MEMO mode remains a deliberate integration stub until memo editor wiring
  is finished.
- Engine truth remains in xbase.hpp / DbArea; this command stays in CLI layer.
==============================
```

---

### TEXT/EDIT/COBOL shim aliases

Source: `src/edu/edu_missing_shims.cpp`  
Owner: `EDU|MISSING_SHIMS`  
Category: `education-shim`  
Status: `compatibility-shim`  
Effect: `report`  
Mutates: `none`  
Usage access: `owned-by real TEXT/EDIT/COBOL implementations`  

Purpose:

Fallback shim implementations used only when real EDU command
  implementations are not linked.

Usage contract:

```text
This file is not the canonical owner of TEXT, EDIT, or COBOL behavior.
  User-visible usage belongs to the real command implementations:
    edu_text.cpp
    edu_edit.cpp
    edu_cobol.cpp
```

Notes:

```text
Remove shims one at a time when real implementations provide the same
  symbols. Do not add new command behavior here unless deliberately creating
  a fallback.
```

Source comments:

```text
src/cli/edu_missing_shims.cpp
Temporary education-command shims for registry symbols that were declared
in shell_commands.hpp but are not currently linked into this build.
These shims are intentionally honest: they do not pretend to implement the
full TEXT, EDIT, or COBOL subsystems. They keep the shell command registry
linkable while the real educational modules are restored/refactored.
Remove one shim at a time when a real implementation provides the same
edu_* entrypoint.
```

---

### TEXT/EDIT/COBOL shim aliases

Source: `x64base/src/edu/edu_missing_shims.cpp`  
Owner: `EDU|MISSING_SHIMS`  
Category: `education-shim`  
Status: `compatibility-shim`  
Effect: `report`  
Mutates: `none`  
Usage access: `owned-by real TEXT/EDIT/COBOL implementations`  

Purpose:

Fallback shim implementations used only when real EDU command
  implementations are not linked.

Usage contract:

```text
This file is not the canonical owner of TEXT, EDIT, or COBOL behavior.
  User-visible usage belongs to the real command implementations:
    edu_text.cpp
    edu_edit.cpp
    edu_cobol.cpp
```

Notes:

```text
Remove shims one at a time when real implementations provide the same
  symbols. Do not add new command behavior here unless deliberately creating
  a fallback.
```

Source comments:

```text
src/cli/edu_missing_shims.cpp
Temporary education-command shims for registry symbols that were declared
in shell_commands.hpp but are not currently linked into this build.
These shims are intentionally honest: they do not pretend to implement the
full TEXT, EDIT, or COBOL subsystems. They keep the shell command registry
linkable while the real educational modules are restored/refactored.
Remove one shim at a time when a real implementation provides the same
edu_* entrypoint.
```

---

### TOP

Source: `src/cli/cmd_top.cpp`  
Owner: `DOT|TOP`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `TOP USAGE`  

Purpose:

Move the current work-area cursor to the first visible/logical record using
  the shared filter-aware navigation selector.

Usage contract:

```text
TOP
  TOP USAGE
```

Notes:

```text
TOP with no arguments moves to the first visible record.
  TOP requires an open table except for TOP USAGE.
  TOP mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number.
```

Related:

```text
BOTTOM
  SKIP
  GOTO
  GPS
```

---

### TOP

Source: `x64base/src/cli/cmd_top.cpp`  
Owner: `DOT|TOP`  
Category: `navigation`  
Status: `supported`  
Effect: `navigate`  
Mutates: `cursor`  
Usage access: `TOP USAGE`  

Purpose:

Move the current work-area cursor to the first visible/logical record using
  the shared filter-aware navigation selector.

Usage contract:

```text
TOP
  TOP USAGE
```

Notes:

```text
TOP with no arguments moves to the first visible record.
  TOP requires an open table except for TOP USAGE.
  TOP mutates cursor position but does not mutate table data.
  TALK ON prints the resulting record number.
```

Related:

```text
BOTTOM
  SKIP
  GOTO
  GPS
```

---

### TRIGGER

Source: `src/cli/cmd_trigger.cpp`  
Owner: `DOT|TRIGGER_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future TRIGGER command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If TRIGGER becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### TRIGGER

Source: `x64base/src/cli/cmd_trigger.cpp`  
Owner: `DOT|TRIGGER_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future TRIGGER command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If TRIGGER becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### TTESTAPP

Source: `src/cli/cmd_ttestapp.cpp`  
Owner: `DOT|TTESTAPP_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future TTESTAPP command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If TTESTAPP becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### TTESTAPP

Source: `x64base/src/cli/cmd_ttestapp.cpp`  
Owner: `DOT|TTESTAPP_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future TTESTAPP command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If TTESTAPP becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### TUPEXPORT

Source: `src/cli/cmd_tupexport.cpp`  
Owner: `DOT|TUPEXPORT`  
Category: `tuple`  
Status: `supported`  
Effect: `export`  
Mutates: `filesystem`  
Usage access: `TUPEXPORT USAGE`  

Purpose:

Export tuple graph rows to a CSV file using a tuple spec, optional field
  list, and optional FOR predicate.

Usage contract:

```text
TUPEXPORT USAGE
  TUPEXPORT CSV <path>
  TUPEXPORT CSV <path> <tuple-spec>
  TUPEXPORT CSV <path> FIELDS <field-list>
  TUPEXPORT CSV <path> * FOR <expr>
```

Examples:

```text
TUPEXPORT CSV tmp\students.csv
  TUPEXPORT CSV tmp\students_names.csv FIELDS LNAME,FNAME
  TUPEXPORT CSV tmp\students_major.csv STUDENTS.*,MAJORS.* FOR MAJORS.NAME = "CS"
```

Notes:

```text
TUPEXPORT USAGE prints usage before open-table checks or file writes.
  TUPEXPORT writes/truncates the requested CSV file.
  Tuple cursor/workspace cursor state is restored best-effort.
```

Related:

```text
TUPLE
  TUPTALK
```

---

### TUPEXPORT

Source: `x64base/src/cli/cmd_tupexport.cpp`  
Owner: `DOT|TUPEXPORT`  
Category: `tuple`  
Status: `supported`  
Effect: `export`  
Mutates: `filesystem`  
Usage access: `TUPEXPORT USAGE`  

Purpose:

Export tuple graph rows to a CSV file using a tuple spec, optional field
  list, and optional FOR predicate.

Usage contract:

```text
TUPEXPORT USAGE
  TUPEXPORT CSV <path>
  TUPEXPORT CSV <path> <tuple-spec>
  TUPEXPORT CSV <path> FIELDS <field-list>
  TUPEXPORT CSV <path> * FOR <expr>
```

Examples:

```text
TUPEXPORT CSV tmp\students.csv
  TUPEXPORT CSV tmp\students_names.csv FIELDS LNAME,FNAME
  TUPEXPORT CSV tmp\students_major.csv STUDENTS.*,MAJORS.* FOR MAJORS.NAME = "CS"
```

Notes:

```text
TUPEXPORT USAGE prints usage before open-table checks or file writes.
  TUPEXPORT writes/truncates the requested CSV file.
  Tuple cursor/workspace cursor state is restored best-effort.
```

Related:

```text
TUPLE
  TUPTALK
```

---

### TUPLE

Source: `src/cli/cmd_tuple.cpp`  
Owner: `DOT|TUPLE`  
Category: `tuple`  
Status: `supported`  
Effect: `report`  
Mutates: `relation-refresh-state cursor`  
Usage access: `TUPLE USAGE`  

Purpose:

Build and print a tuple row from the canonical tuple builder using a tuple
  field specification and optional output flags.

Usage contract:

```text
TUPLE
  TUPLE USAGE
  TUPLE <spec>
  TUPLE <spec> --HEADER
  TUPLE <spec> --AREA-PREFIX
  TUPLE <spec> --NO-ECHO
  TUPLE <spec> --STRICT
  TUPLE <spec> --HEADER-ONLY
  TUPLE <spec> --VALUES-ONLY
  TUPLE <spec> DEBUG
  TUPLE <spec> --DEBUG
  TUPLE <spec> --NULL <token>
```

Examples:

```text
TUPLE
  TUPLE LNAME,FNAME
  TUPLE STUDENTS.LNAME,STUDENTS.FNAME
  TUPLE * --HEADER
  TUPLE * --VALUES-ONLY
```

Notes:

```text
TUPLE with no arguments uses the default star spec.
  TUPLE delegates tuple truth to tuple_builder.
  TUPLE can print formatted output, raw unit-separated values, or both.
  --HEADER prints a header row before values.
  --AREA-PREFIX prefixes header columns with area context.
  --NO-ECHO preserves legacy raw-only scripting behavior.
  --VALUES-ONLY prints raw unit-separated values only.
  DEBUG and --DEBUG print the raw unit-separated row before formatted output.
  --STRICT asks the tuple builder to reject loose field matches.
  TUPLE is read-only for table data.
```

Related:

```text
SMARTLIST
  TUPVALIDATE
  TUPTALK
  ERSATZ
```

Source comments:

```text
src/cli/cmd_tuple.cpp
cmd_TUPLE delegates tuple assembly to the canonical builder (tuple_builder.*).
Printing and CLI flags remain here; data truth lives in the builder.
```

---

### TUPLE

Source: `x64base/src/cli/cmd_tuple.cpp`  
Owner: `DOT|TUPLE`  
Category: `tuple`  
Status: `supported`  
Effect: `report`  
Mutates: `relation-refresh-state cursor`  
Usage access: `TUPLE USAGE`  

Purpose:

Build and print a tuple row from the canonical tuple builder using a tuple
  field specification and optional output flags.

Usage contract:

```text
TUPLE
  TUPLE USAGE
  TUPLE <spec>
  TUPLE <spec> --HEADER
  TUPLE <spec> --AREA-PREFIX
  TUPLE <spec> --NO-ECHO
  TUPLE <spec> --STRICT
  TUPLE <spec> --HEADER-ONLY
  TUPLE <spec> --VALUES-ONLY
  TUPLE <spec> DEBUG
  TUPLE <spec> --DEBUG
  TUPLE <spec> --NULL <token>
```

Examples:

```text
TUPLE
  TUPLE LNAME,FNAME
  TUPLE STUDENTS.LNAME,STUDENTS.FNAME
  TUPLE * --HEADER
  TUPLE * --VALUES-ONLY
```

Notes:

```text
TUPLE with no arguments uses the default star spec.
  TUPLE delegates tuple truth to tuple_builder.
  TUPLE can print formatted output, raw unit-separated values, or both.
  --HEADER prints a header row before values.
  --AREA-PREFIX prefixes header columns with area context.
  --NO-ECHO preserves legacy raw-only scripting behavior.
  --VALUES-ONLY prints raw unit-separated values only.
  DEBUG and --DEBUG print the raw unit-separated row before formatted output.
  --STRICT asks the tuple builder to reject loose field matches.
  TUPLE is read-only for table data.
```

Related:

```text
SMARTLIST
  TUPVALIDATE
  TUPTALK
  ERSATZ
```

Source comments:

```text
src/cli/cmd_tuple.cpp
cmd_TUPLE delegates tuple assembly to the canonical builder (tuple_builder.*).
Printing and CLI flags remain here; data truth lives in the builder.
```

---

### TUPLEDELTA

Source: `src/cli/cmd_tupledelta.cpp`  
Owner: `DOT|TUPLEDELTA`  
Category: `tuple`  
Status: `experimental`  
Effect: `inspect`  
Mutates: `none`  
Usage access: `TUPLEDELTA USAGE`  

Purpose:

Compare two named tuple streams and report insert, delete, and update
  deltas. The loader remains a skeleton until tuple stream storage is finalized.

Usage contract:

```text
TUPLEDELTA USAGE
  TUPLEDELTA <baseline-stream> <current-stream>
```

Notes:

```text
TUPLEDELTA requires two stream names except for TUPLEDELTA USAGE.
  Tuple stream loading is not implemented in this skeleton.
  REC_ID or PRIMARY UNIQUE is intended to be the identity key.
  Field-level diffing is intentionally stubbed for now.
  TUPLEDELTA is diagnostic and does not mutate table or index data.
```

Related:

```text
TUPLE
  SMARTLIST
  ERSATZ
```

Source comments:

```text
cmd_tupledelta.cpp
DotTalk++ tuple delta command skeleton.
Purpose:
  Compare two tuple streams and report INSERT / DELETE / UPDATE changes.
Command surface:
  TUPLEDELTA <baseline-stream> <current-stream>
Notes:
  - REC_ID / PRIMARY UNIQUE should be the identity key.
  - Field-level diffing is intentionally stubbed.
  - Stream loading is intentionally abstracted until tuple stream storage
    format is finalized.
```

---

### TUPLEDELTA

Source: `x64base/src/cli/cmd_tupledelta.cpp`  
Owner: `DOT|TUPLEDELTA`  
Category: `tuple`  
Status: `experimental`  
Effect: `inspect`  
Mutates: `none`  
Usage access: `TUPLEDELTA USAGE`  

Purpose:

Compare two named tuple streams and report insert, delete, and update
  deltas. The loader remains a skeleton until tuple stream storage is finalized.

Usage contract:

```text
TUPLEDELTA USAGE
  TUPLEDELTA <baseline-stream> <current-stream>
```

Notes:

```text
TUPLEDELTA requires two stream names except for TUPLEDELTA USAGE.
  Tuple stream loading is not implemented in this skeleton.
  REC_ID or PRIMARY UNIQUE is intended to be the identity key.
  Field-level diffing is intentionally stubbed for now.
  TUPLEDELTA is diagnostic and does not mutate table or index data.
```

Related:

```text
TUPLE
  SMARTLIST
  ERSATZ
```

Source comments:

```text
cmd_tupledelta.cpp
DotTalk++ tuple delta command skeleton.
Purpose:
  Compare two tuple streams and report INSERT / DELETE / UPDATE changes.
Command surface:
  TUPLEDELTA <baseline-stream> <current-stream>
Notes:
  - REC_ID / PRIMARY UNIQUE should be the identity key.
  - Field-level diffing is intentionally stubbed.
  - Stream loading is intentionally abstracted until tuple stream storage
    format is finalized.
```

---

### TUPTALK

Source: `src/cli/cmd_tuptalk.cpp`  
Owner: `DOT|TUPTALK`  
Category: `tuple`  
Status: `supported`  
Effect: `mixed`  
Mutates: `tuptalk-buffer filesystem`  
Usage access: `TUPTALK USAGE`  

Purpose:

Tuple-based normalization test harness and live DBF capture tool for
  building, normalizing, dumping, exporting, and pushing tuple entries.

Usage contract:

```text
TUPTALK
  TUPTALK USAGE
  TUPTALK RESET
  TUPTALK ADD <type> <len> <raw>
  TUPTALK ADD <type> <len> <dec> <raw>
  TUPTALK LIST
  TUPTALK NORMALIZE
  TUPTALK DUMP
  TUPTALK EXPORT CSV
  TUPTALK EXPORT TSV
  TUPTALK EXPORT CSV <path>
  TUPTALK EXPORT TSV <path>
  TUPTALK PUSH <field>
  TUPTALK PUSH ALL
  TUPTALK PUSH ALL FILTER <mask>
  TUPTALK PUSH FILTER <mask>
  TUPTALK PUSH ROW
```

Examples:

```text
TUPTALK PUSH LASTNAME
  TUPTALK PUSH 3
  TUPTALK PUSH ALL
  TUPTALK PUSH ALL FILTER CND
  TUPTALK PUSH ROW
```

Notes:

```text
TUPTALK with no arguments shows usage/help and buffer status.
  TT is wired as a shell alias for TUPTALK.
  ADD creates a test entry from raw text and schema type metadata.
  NORMALIZE fills normalized values using value_normalize.
  PUSH captures fields or rows from the current DBF record.
  EXPORT writes CSV or TSV when a path is supplied or uses default behavior.
  TUPTALK mutates its process-local scratch buffer and may write export files.
```

Related:

```text
TUPLE
  TUPVALIDATE
  FIELDS
```

Source comments:

```text
TUPTALK NORMALIZE
  TUPTALK DUMP
  TUPTALK EXPORT CSV|TSV [<path>]
  TUPTALK PUSH <fieldName|#>          # capture one field (schema type/len/dec + current record value)
  TUPTALK PUSH ALL [FILTER <mask>]    # capture all fields; optional mask (e.g., CND)
  TUPTALK PUSH FILTER <mask>          # alias of: PUSH ALL FILTER <mask>
  TUPTALK PUSH ROW                    # capture entire fixed-width padded row as one entry
  TUPTALK HELP
Notes:
- Field lookup is forgiving: exact (case-insensitive) ? unique prefix ? unique substring.
- PUSH ROW builds a single fixed-width, schema-aligned row (good for round-trip tests).
- When printing schema lengths/decimals we cast to int (avoid unsigned-char/control-char issues).
```

---

### TUPTALK

Source: `x64base/src/cli/cmd_tuptalk.cpp`  
Owner: `DOT|TUPTALK`  
Category: `tuple`  
Status: `supported`  
Effect: `mixed`  
Mutates: `tuptalk-buffer filesystem`  
Usage access: `TUPTALK USAGE`  

Purpose:

Tuple-based normalization test harness and live DBF capture tool for
  building, normalizing, dumping, exporting, and pushing tuple entries.

Usage contract:

```text
TUPTALK
  TUPTALK USAGE
  TUPTALK RESET
  TUPTALK ADD <type> <len> <raw>
  TUPTALK ADD <type> <len> <dec> <raw>
  TUPTALK LIST
  TUPTALK NORMALIZE
  TUPTALK DUMP
  TUPTALK EXPORT CSV
  TUPTALK EXPORT TSV
  TUPTALK EXPORT CSV <path>
  TUPTALK EXPORT TSV <path>
  TUPTALK PUSH <field>
  TUPTALK PUSH ALL
  TUPTALK PUSH ALL FILTER <mask>
  TUPTALK PUSH FILTER <mask>
  TUPTALK PUSH ROW
```

Examples:

```text
TUPTALK PUSH LASTNAME
  TUPTALK PUSH 3
  TUPTALK PUSH ALL
  TUPTALK PUSH ALL FILTER CND
  TUPTALK PUSH ROW
```

Notes:

```text
TUPTALK with no arguments shows usage/help and buffer status.
  TT is wired as a shell alias for TUPTALK.
  ADD creates a test entry from raw text and schema type metadata.
  NORMALIZE fills normalized values using value_normalize.
  PUSH captures fields or rows from the current DBF record.
  EXPORT writes CSV or TSV when a path is supplied or uses default behavior.
  TUPTALK mutates its process-local scratch buffer and may write export files.
```

Related:

```text
TUPLE
  TUPVALIDATE
  FIELDS
```

Source comments:

```text
TUPTALK NORMALIZE
  TUPTALK DUMP
  TUPTALK EXPORT CSV|TSV [<path>]
  TUPTALK PUSH <fieldName|#>          # capture one field (schema type/len/dec + current record value)
  TUPTALK PUSH ALL [FILTER <mask>]    # capture all fields; optional mask (e.g., CND)
  TUPTALK PUSH FILTER <mask>          # alias of: PUSH ALL FILTER <mask>
  TUPTALK PUSH ROW                    # capture entire fixed-width padded row as one entry
  TUPTALK HELP
Notes:
- Field lookup is forgiving: exact (case-insensitive) ? unique prefix ? unique substring.
- PUSH ROW builds a single fixed-width, schema-aligned row (good for round-trip tests).
- When printing schema lengths/decimals we cast to int (avoid unsigned-char/control-char issues).
```

---

### TUPVALIDATE

Source: `src/cli/cmd_tupvalidate.cpp`  
Owner: `DOT|TUPVALIDATE`  
Category: `tuple`  
Status: `supported`  
Effect: `validate`  
Mutates: `cursor`  
Usage access: `TUPVALIDATE USAGE`  

Purpose:

Validate tuple graph rows for the current table using the tuple graph cursor
  and relation-aware tuple validation layer.

Usage contract:

```text
TUPVALIDATE
  TUPVALIDATE USAGE
  TUPVALIDATE *
  TUPVALIDATE <tuple-spec>
  TUPVALIDATE * FOR <expr>
  TUPVALIDATE * FOR <expr> MAX <n>
  TUPVALIDATE * FOR <expr> TRACE
```

Examples:

```text
TUPVALIDATE LNAME,FNAME
  TUPVALIDATE STUDENTS.*,MAJORS.* FOR MAJORS.NAME = CS
```

Notes:

```text
TUPVALIDATE with no arguments validates the default star tuple spec.
  TUPVALIDATE USAGE prints usage and does not require an open table.
  The tuple graph cursor uses active ordering and relation context.
  Validation checks tuple cells against their source work areas when available.
  Cursor restoration is reported after validation.
  TUPVALIDATE is read-only for table data but moves cursors during validation.
```

Related:

```text
TUPLE
  TUPTALK
  ERSATZ
  REL
```

---

### TUPVALIDATE

Source: `x64base/src/cli/cmd_tupvalidate.cpp`  
Owner: `DOT|TUPVALIDATE`  
Category: `tuple`  
Status: `supported`  
Effect: `validate`  
Mutates: `cursor`  
Usage access: `TUPVALIDATE USAGE`  

Purpose:

Validate tuple graph rows for the current table using the tuple graph cursor
  and relation-aware tuple validation layer.

Usage contract:

```text
TUPVALIDATE
  TUPVALIDATE USAGE
  TUPVALIDATE *
  TUPVALIDATE <tuple-spec>
  TUPVALIDATE * FOR <expr>
  TUPVALIDATE * FOR <expr> MAX <n>
  TUPVALIDATE * FOR <expr> TRACE
```

Examples:

```text
TUPVALIDATE LNAME,FNAME
  TUPVALIDATE STUDENTS.*,MAJORS.* FOR MAJORS.NAME = CS
```

Notes:

```text
TUPVALIDATE with no arguments validates the default star tuple spec.
  TUPVALIDATE USAGE prints usage and does not require an open table.
  The tuple graph cursor uses active ordering and relation context.
  Validation checks tuple cells against their source work areas when available.
  Cursor restoration is reported after validation.
  TUPVALIDATE is read-only for table data but moves cursors during validation.
```

Related:

```text
TUPLE
  TUPTALK
  ERSATZ
  REL
```

---

### TURBOPACK

Source: `src/cli/cmd_turbo_pack.cpp`  
Owner: `DOT|TURBOPACK`  
Category: `destructive-table-structure`  
Status: `supported`  
Effect: `fast-compact-plain-dbf`  
Mutates: `table-file closes-table order-state`  
Usage access: `TURBOPACK USAGE`  

Purpose:

Fast byte-oriented compaction for plain non-memo, non-x64 DBF tables.

Usage contract:

```text
TURBOPACK USAGE
  TURBOPACK
```

Examples:

```text
TURBOPACK
```

Notes:

```text
TURBOPACK USAGE prints usage before open-table checks.
  TURBOPACK is a fast path for plain DBF tables only.
  Memo tables and x64 tables are refused; use PACK instead.
  TURBOPACK closes the table on success.
  Index containers must be rebuilt/rebound after TURBOPACK.
```

Related:

```text
PACK
  ZAP
  RECALL
```

Source comments:

```text
src/cli/cmd_turbo_pack.cpp
TURBOPACK — fast, low-level DBF compaction (byte-oriented)
Removes physically deleted records (* flag) by rewriting only live ones.
Scope / contract:
  - Fast path for plain DBF tables only.
  - Memo tables are explicitly refused.
  - X64 tables are explicitly refused for now.
POLICY (2026):
  - Structural command (file-level operation)
  - Leaves table CLOSED on success
  - User must USE to reopen
  - Indexes should be rebuilt/rebound after
```

---

### TURBOPACK

Source: `x64base/src/cli/cmd_turbo_pack.cpp`  
Owner: `DOT|TURBOPACK`  
Category: `destructive-table-structure`  
Status: `supported`  
Effect: `fast-compact-plain-dbf`  
Mutates: `table-file closes-table order-state`  
Usage access: `TURBOPACK USAGE`  

Purpose:

Fast byte-oriented compaction for plain non-memo, non-x64 DBF tables.

Usage contract:

```text
TURBOPACK USAGE
  TURBOPACK
```

Examples:

```text
TURBOPACK
```

Notes:

```text
TURBOPACK USAGE prints usage before open-table checks.
  TURBOPACK is a fast path for plain DBF tables only.
  Memo tables and x64 tables are refused; use PACK instead.
  TURBOPACK closes the table on success.
  Index containers must be rebuilt/rebound after TURBOPACK.
```

Related:

```text
PACK
  ZAP
  RECALL
```

Source comments:

```text
src/cli/cmd_turbo_pack.cpp
TURBOPACK — fast, low-level DBF compaction (byte-oriented)
Removes physically deleted records (* flag) by rewriting only live ones.
Scope / contract:
  - Fast path for plain DBF tables only.
  - Memo tables are explicitly refused.
  - X64 tables are explicitly refused for now.
POLICY (2026):
  - Structural command (file-level operation)
  - Leaves table CLOSED on success
  - User must USE to reopen
  - Indexes should be rebuilt/rebound after
```

---

### TVISION

Source: `src/cli/cmd_tvision.cpp`  
Owner: `DOT|TVISION`  
Category: `diagnostics`  
Status: `stub`  
Effect: `report`  
Mutates: `none`  
Usage access: `TVISION USAGE`  

Purpose:

Confirm Turbo Vision/TUI support is linked; this is currently a stub.

Usage contract:

```text
TVISION
  TVISION USAGE
```

Examples:

```text
TVISION
```

Notes:

```text
TVISION with no arguments prints the current TUI support status.
  TVISION USAGE prints usage.
  This command does not launch a TUI yet.
```

Related:

```text
RBROWSE
  SMARTBROWSER
```

Source comments:

```text
src/cli/cmd_tvision.cpp
```

---

### TVISION

Source: `x64base/src/cli/cmd_tvision.cpp`  
Owner: `DOT|TVISION`  
Category: `diagnostics`  
Status: `stub`  
Effect: `report`  
Mutates: `none`  
Usage access: `TVISION USAGE`  

Purpose:

Confirm Turbo Vision/TUI support is linked; this is currently a stub.

Usage contract:

```text
TVISION
  TVISION USAGE
```

Examples:

```text
TVISION
```

Notes:

```text
TVISION with no arguments prints the current TUI support status.
  TVISION USAGE prints usage.
  This command does not launch a TUI yet.
```

Related:

```text
RBROWSE
  SMARTBROWSER
```

Source comments:

```text
src/cli/cmd_tvision.cpp
```

---

### UNLOCK

Source: `src/cli/cmd_unlock.cpp`  
Owner: `DOT|UNLOCK`  
Category: `locking`  
Status: `supported`  
Effect: `release-lock`  
Mutates: `lock-state`  
Usage access: `UNLOCK USAGE`  

Purpose:

Release the current record lock, a specified record lock, or the table lock.

Usage contract:

```text
UNLOCK USAGE
  UNLOCK
  UNLOCK <recno>
  UNLOCK ALL
  UNLOCK TABLE
```

Examples:

```text
UNLOCK
  UNLOCK 10
  UNLOCK ALL
  UNLOCK TABLE
```

Notes:

```text
UNLOCK USAGE returns before open-table checks.
  UNLOCK with no arguments unlocks the current record.
  UNLOCK ALL and UNLOCK TABLE release the table lock.
```

Related:

```text
LOCK
  RLOCK
  FLOCK
```

---

### UNLOCK

Source: `x64base/src/cli/cmd_unlock.cpp`  
Owner: `DOT|UNLOCK`  
Category: `locking`  
Status: `supported`  
Effect: `release-lock`  
Mutates: `lock-state`  
Usage access: `UNLOCK USAGE`  

Purpose:

Release the current record lock, a specified record lock, or the table lock.

Usage contract:

```text
UNLOCK USAGE
  UNLOCK
  UNLOCK <recno>
  UNLOCK ALL
  UNLOCK TABLE
```

Examples:

```text
UNLOCK
  UNLOCK 10
  UNLOCK ALL
  UNLOCK TABLE
```

Notes:

```text
UNLOCK USAGE returns before open-table checks.
  UNLOCK with no arguments unlocks the current record.
  UNLOCK ALL and UNLOCK TABLE release the table lock.
```

Related:

```text
LOCK
  RLOCK
  FLOCK
```

---

### UNTIL

Source: `src/cli/cmd_until.cpp`  
Owner: `DOT|UNTIL`  
Category: `script`  
Status: `supported`  
Effect: `loop`  
Mutates: `until-state cursor delegates-command-effects`  
Usage access: `UNTIL USAGE`  

Purpose:

Buffer and execute an UNTIL...ENDUNTIL loop from the current record until a
  boolean expression becomes true.

Usage contract:

```text
UNTIL USAGE
  UNTIL <bool-expr> [QUIET]
  ENDUNTIL
  ENDUNTIL USAGE
```

Examples:

```text
UNTIL EOF()
      TUPLE LNAME,FNAME,GPA
  ENDUNTIL
```

Notes:

```text
UNTIL USAGE and ENDUNTIL USAGE do not start or execute a loop.
  UNTIL starts buffering; the shell must route body lines to UNTIL_BUFFER.
  ENDUNTIL executes buffered body lines through the canonical loop executor.
  Execution starts at the current record and advances one record per iteration.
  Buffered body command effects are owned by those commands.
```

Related:

```text
IF
  WHILE
  SCAN
```

Source comments:

```text
============================================================================
path: src/cli/cmd_until.cpp
purpose: UNTIL / ENDUNTIL with private buffering (no loop_state deps)
usage:
  UNTIL <bool-expr> [QUIET]  -> begin buffering; shell routes lines to UNTIL_BUFFER
  ENDUNTIL                   -> execute body until <expr> becomes true
notes:
  - Starts from the CURRENT record (does NOT force TOP).
  - Advances with A.skip(1); stops hard at EOF/BOF or empty tables.
  - Buffer persists after ENDUNTIL (mirrors ENDLOOP).
============================================================================
```

---

### UNTIL

Source: `x64base/src/cli/cmd_until.cpp`  
Owner: `DOT|UNTIL`  
Category: `script`  
Status: `supported`  
Effect: `loop`  
Mutates: `until-state cursor delegates-command-effects`  
Usage access: `UNTIL USAGE`  

Purpose:

Buffer and execute an UNTIL...ENDUNTIL loop from the current record until a
  boolean expression becomes true.

Usage contract:

```text
UNTIL USAGE
  UNTIL <bool-expr> [QUIET]
  ENDUNTIL
  ENDUNTIL USAGE
```

Examples:

```text
UNTIL EOF()
      TUPLE LNAME,FNAME,GPA
  ENDUNTIL
```

Notes:

```text
UNTIL USAGE and ENDUNTIL USAGE do not start or execute a loop.
  UNTIL starts buffering; the shell must route body lines to UNTIL_BUFFER.
  ENDUNTIL executes buffered body lines through the canonical loop executor.
  Execution starts at the current record and advances one record per iteration.
  Buffered body command effects are owned by those commands.
```

Related:

```text
IF
  WHILE
  SCAN
```

Source comments:

```text
============================================================================
path: src/cli/cmd_until.cpp
purpose: UNTIL / ENDUNTIL with private buffering (no loop_state deps)
usage:
  UNTIL <bool-expr> [QUIET]  -> begin buffering; shell routes lines to UNTIL_BUFFER
  ENDUNTIL                   -> execute body until <expr> becomes true
notes:
  - Starts from the CURRENT record (does NOT force TOP).
  - Advances with A.skip(1); stops hard at EOF/BOF or empty tables.
  - Buffer persists after ENDUNTIL (mirrors ENDLOOP).
============================================================================
```

---

### UPDATE

Source: `src/cli/cmd_sql_update.cpp`  
Owner: `DOT|UPDATE`  
Category: `sql`  
Status: `supported`  
Effect: `update-records`  
Mutates: `table-data`  
Usage access: `UPDATE USAGE`  

Purpose:

Update records in the current DBF work area using SQL-like SET/WHERE syntax.

Usage contract:

```text
UPDATE USAGE
  UPDATE SET <field>=<value>[, ...] [WHERE <expr>]
```

Examples:

```text
UPDATE SET GPA=3.5 WHERE SID = 1001
  UPDATE SET MAJOR="CSCI" WHERE MAJOR = "CS"
```

Notes:

```text
UPDATE USAGE prints usage before open-table checks.
  UPDATE without WHERE may update all visible records depending on implementation.
  Use WHERE intentionally.
```

Related:

```text
SQL
  INSERT
  SQLERASE
```

---

### UPDATE

Source: `x64base/src/cli/cmd_sql_update.cpp`  
Owner: `DOT|UPDATE`  
Category: `sql`  
Status: `supported`  
Effect: `update-records`  
Mutates: `table-data`  
Usage access: `UPDATE USAGE`  

Purpose:

Update records in the current DBF work area using SQL-like SET/WHERE syntax.

Usage contract:

```text
UPDATE USAGE
  UPDATE SET <field>=<value>[, ...] [WHERE <expr>]
```

Examples:

```text
UPDATE SET GPA=3.5 WHERE SID = 1001
  UPDATE SET MAJOR="CSCI" WHERE MAJOR = "CS"
```

Notes:

```text
UPDATE USAGE prints usage before open-table checks.
  UPDATE without WHERE may update all visible records depending on implementation.
  Use WHERE intentionally.
```

Related:

```text
SQL
  INSERT
  SQLERASE
```

---

### USE

Source: `src/cli/cmd_use.cpp`  
Owner: `DOT|USE`  
Category: `workspace`  
Status: `supported`  
Effect: `session`  
Mutates: `session area order memo index`  
Usage access: `USE USAGE`  

Purpose:

Open a DBF table into the current work area, with duplicate-open guard,
  memo auto-attach, optional index auto-attach, and NOINDEX physical-order mode.

Usage contract:

```text
USE USAGE
  USE <table>
  USE <table.dbf>
  USE <path\table.dbf>
  USE <table> NOINDEX
  USE <table> NOIDX
```

Notes:

```text
USE requires a table name or path; no usable argument shows usage.
  Relative logical names resolve through the configured DBF path slot.
  USE prevents duplicate opens of the same DBF path across work areas.
  USE clears stale order/tag/container state and closes the current area before opening the new DBF.
  USE opens the target DBF and populates DbArea metadata.
  USE auto-attaches memo storage when memo fields are present.
  USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is specified.
  USE prefers the configured INDEXES slot and falls back to the DBF directory.
  NOINDEX/NOIDX opens the table in physical order and skips index auto-attach.
  USE is a session/area mutation command; it changes the current work area binding but should not mutate table records.
```

Related:

```text
CLOSE
  WORKSPACE
  SETPATH
  SET ORDER
  SET INDEX
  STRUCT
  DBAREA
```

Source comments:

```text
src/cli/cmd_use.cpp
DotTalk++ USE command (open DBF in a work area) — duplicate-open guard, NOINDEX, auto-attach
```

---

### USE

Source: `x64base/src/cli/cmd_use.cpp`  
Owner: `DOT|USE`  
Category: `workspace`  
Status: `supported`  
Effect: `session`  
Mutates: `session area order memo index`  
Usage access: `USE USAGE`  

Purpose:

Open a DBF table into the current work area, with duplicate-open guard,
  memo auto-attach, optional index auto-attach, and NOINDEX physical-order mode.

Usage contract:

```text
USE USAGE
  USE <table>
  USE <table.dbf>
  USE <path\table.dbf>
  USE <table> NOINDEX
  USE <table> NOIDX
```

Notes:

```text
USE requires a table name or path; no usable argument shows usage.
  Relative logical names resolve through the configured DBF path slot.
  USE prevents duplicate opens of the same DBF path across work areas.
  USE clears stale order/tag/container state and closes the current area before opening the new DBF.
  USE opens the target DBF and populates DbArea metadata.
  USE auto-attaches memo storage when memo fields are present.
  USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is specified.
  USE prefers the configured INDEXES slot and falls back to the DBF directory.
  NOINDEX/NOIDX opens the table in physical order and skips index auto-attach.
  USE is a session/area mutation command; it changes the current work area binding but should not mutate table records.
```

Related:

```text
CLOSE
  WORKSPACE
  SETPATH
  SET ORDER
  SET INDEX
  STRUCT
  DBAREA
```

Source comments:

```text
src/cli/cmd_use.cpp
DotTalk++ USE command (open DBF in a work area) — duplicate-open guard, NOINDEX, auto-attach
```

---

### USE

Source: `x64base/src/cli/cmd_vuse.cpp`  
Owner: `DOT|USE`  
Category: `table`  
Status: `supported`  
Effect: `open-table`  
Mutates: `current-work-area order-state memo-attachment`  
Usage access: `USE USAGE`  

Purpose:

Open a DBF table in the current work area, with duplicate-open protection,
  optional NOINDEX, and best-effort memo/index attachment.

Usage contract:

```text
USE USAGE
  USE <table-or-path> [NOINDEX]
  VUSE USAGE
  VUSE <table-or-path> [NOINDEX]
```

Examples:

```text
USE students
  USE students NOINDEX
  USE d:\data\students.dbf
```

Notes:

```text
USE with no arguments preserves existing behavior and reports a missing table name.
  USE USAGE prints usage and does not close/open tables or mutate order state.
  USE resets current-area runtime state before opening a new table.
  NOINDEX skips auto-attach and leaves the work area in physical order.
```

Related:

```text
CLOSE
  WORKSPACE
  SETPATH
  SET ORDER
```

Source comments:

```text
src/cli/cmd_use.cpp
DotTalk++ USE command (open DBF in a work area) — duplicate-open guard, NOINDEX, auto-attach
```

---

### VALIDATE

Source: `src/cli/cmd_validate.cpp`  
Owner: `DOT|VALIDATE`  
Category: `validation`  
Status: `supported`  
Effect: `validate`  
Mutates: `delegated-subcommand`  
Usage access: `VALIDATE USAGE`  

Purpose:

Route validation subcommands such as VALIDATE UNIQUE to their handlers.

Usage contract:

```text
VALIDATE USAGE
  VALIDATE UNIQUE USAGE
  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
```

Examples:

```text
VALIDATE UNIQUE FIELD SID
  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
  VALIDATE UNIQUE FIELD SID REPAIR
  VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt
```

Notes:

```text
VALIDATE with no arguments prints usage.
  VALIDATE USAGE prints usage and does not scan or repair records.
  VALIDATE UNIQUE is delegated to the UNIQUE validator.
  REPAIR may mutate field values; use it intentionally.
```

Related:

```text
RULE
  WHERE
```

Source comments:

```text
src/cli/cmd_validate.cpp -- VALIDATE router
Forwards subcommands like "VALIDATE UNIQUE ..." to their handlers.
```

---

### VALIDATE

Source: `x64base/src/cli/cmd_validate.cpp`  
Owner: `DOT|VALIDATE`  
Category: `validation`  
Status: `supported`  
Effect: `validate`  
Mutates: `delegated-subcommand`  
Usage access: `VALIDATE USAGE`  

Purpose:

Route validation subcommands such as VALIDATE UNIQUE to their handlers.

Usage contract:

```text
VALIDATE USAGE
  VALIDATE UNIQUE USAGE
  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
```

Examples:

```text
VALIDATE UNIQUE FIELD SID
  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
  VALIDATE UNIQUE FIELD SID REPAIR
  VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt
```

Notes:

```text
VALIDATE with no arguments prints usage.
  VALIDATE USAGE prints usage and does not scan or repair records.
  VALIDATE UNIQUE is delegated to the UNIQUE validator.
  REPAIR may mutate field values; use it intentionally.
```

Related:

```text
RULE
  WHERE
```

Source comments:

```text
src/cli/cmd_validate.cpp -- VALIDATE router
Forwards subcommands like "VALIDATE UNIQUE ..." to their handlers.
```

---

### VALIDATE UNIQUE

Source: `src/cli/cmd_validate_unique.cpp`  
Owner: `DOT|VALIDATE_UNIQUE`  
Category: `validation`  
Status: `supported`  
Effect: `validate`  
Mutates: `optional-table-data`  
Usage access: `VALIDATE UNIQUE USAGE`  

Purpose:

Scan the current work area for duplicate/blank values in a field, optionally
  repairing numeric/autokey-style duplicate values.

Usage contract:

```text
VALIDATE UNIQUE USAGE
  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
```

Examples:

```text
VALIDATE UNIQUE FIELD SID
  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
  VALIDATE UNIQUE FIELD SID REPAIR
  VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt
```

Notes:

```text
VALIDATE UNIQUE USAGE prints usage before open-table checks.
  REPAIR currently supports numeric/autokey-style fields only.
  REPORT TO writes a duplicate report file.
  Without REPAIR this command scans and reports only.
```

Related:

```text
VALIDATE
  RULE
```

Source comments:

```text
VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
Scans current work area and reports duplicates for the given field.
REPAIR is intended for numeric unique/autokey-style fields:
  - blank values are assigned new numbers
  - duplicate values keep the first occurrence
  - later duplicates are assigned new numbers
```

---

### VALIDATE UNIQUE

Source: `x64base/src/cli/cmd_validate_unique.cpp`  
Owner: `DOT|VALIDATE_UNIQUE`  
Category: `validation`  
Status: `supported`  
Effect: `validate`  
Mutates: `optional-table-data`  
Usage access: `VALIDATE UNIQUE USAGE`  

Purpose:

Scan the current work area for duplicate/blank values in a field, optionally
  repairing numeric/autokey-style duplicate values.

Usage contract:

```text
VALIDATE UNIQUE USAGE
  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
```

Examples:

```text
VALIDATE UNIQUE FIELD SID
  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
  VALIDATE UNIQUE FIELD SID REPAIR
  VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt
```

Notes:

```text
VALIDATE UNIQUE USAGE prints usage before open-table checks.
  REPAIR currently supports numeric/autokey-style fields only.
  REPORT TO writes a duplicate report file.
  Without REPAIR this command scans and reports only.
```

Related:

```text
VALIDATE
  RULE
```

Source comments:

```text
VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]
Scans current work area and reports duplicates for the given field.
REPAIR is intended for numeric unique/autokey-style fields:
  - blank values are assigned new numbers
  - duplicate values keep the first occurrence
  - later duplicates are assigned new numbers
```

---

### VAR

Source: `src/cli/cmd_var.cpp`  
Owner: `DOT|VAR`  
Category: `scripting`  
Status: `supported`  
Effect: `parse`  
Mutates: `none-currently`  
Usage access: `VAR USAGE`  

Purpose:

Validate and accept DotScript variable assignment syntax.

Usage contract:

```text
VAR USAGE
  VAR <name> = <expression>
```

Examples:

```text
VAR threshold = 3.0
  VAR label = UPPER(LNAME)
  VAR today = DATE()
```

Notes:

```text
VAR with no arguments prints usage.
  VAR USAGE prints usage and does not validate/accept an assignment.
  Current implementation validates the variable name and expression presence,
  then reports the accepted assignment.
```

Related:

```text
DOTSCRIPT
  CALC
```

---

### VAR

Source: `src/cli/cmd_var_integration_example.cpp`  
Owner: `DOT|VAR_INTEGRATION_EXAMPLE`  
Category: `example-helper`  
Status: `documentation-example`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by VAR`  

Purpose:

Example-only integration sketch for DotScript variable-name validation.

Usage contract:

```text
This file is not a shell command handler.
  User-visible VAR behavior and usage are owned by cmd_var.cpp.
```

Notes:

```text
Keep this file as a reference/example only unless intentionally wiring a
  real command path. Do not register cmd_VAR_example as a user command.
```

---

### VAR

Source: `x64base/src/cli/cmd_var.cpp`  
Owner: `DOT|VAR`  
Category: `scripting`  
Status: `supported`  
Effect: `parse`  
Mutates: `none-currently`  
Usage access: `VAR USAGE`  

Purpose:

Validate and accept DotScript variable assignment syntax.

Usage contract:

```text
VAR USAGE
  VAR <name> = <expression>
```

Examples:

```text
VAR threshold = 3.0
  VAR label = UPPER(LNAME)
  VAR today = DATE()
```

Notes:

```text
VAR with no arguments prints usage.
  VAR USAGE prints usage and does not validate/accept an assignment.
  Current implementation validates the variable name and expression presence,
  then reports the accepted assignment.
```

Related:

```text
DOTSCRIPT
  CALC
```

---

### VAR

Source: `x64base/src/cli/cmd_var_integration_example.cpp`  
Owner: `DOT|VAR_INTEGRATION_EXAMPLE`  
Category: `example-helper`  
Status: `documentation-example`  
Effect: `none`  
Mutates: `none`  
Usage access: `owned-by VAR`  

Purpose:

Example-only integration sketch for DotScript variable-name validation.

Usage contract:

```text
This file is not a shell command handler.
  User-visible VAR behavior and usage are owned by cmd_var.cpp.
```

Notes:

```text
Keep this file as a reference/example only unless intentionally wiring a
  real command path. Do not register cmd_VAR_example as a user command.
```

---

### VERSION

Source: `src/cli/cmd_version.cpp`  
Owner: `DOT|VERSION`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `VERSION USAGE`  

Purpose:

Report the DotTalk++ version label and build date/time.

Usage contract:

```text
VERSION
  VERSION USAGE
```

Notes:

```text
VERSION with no arguments reports version and build information.
  VERSION USAGE prints usage.
  VERSION is read-only and does not mutate table data or session state.
```

Related:

```text
ABOUT
  SQLVER
```

---

### VERSION

Source: `x64base/src/cli/cmd_version.cpp`  
Owner: `DOT|VERSION`  
Category: `report`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `VERSION USAGE`  

Purpose:

Report the DotTalk++ version label and build date/time.

Usage contract:

```text
VERSION
  VERSION USAGE
```

Notes:

```text
VERSION with no arguments reports version and build information.
  VERSION USAGE prints usage.
  VERSION is read-only and does not mutate table data or session state.
```

Related:

```text
ABOUT
  SQLVER
```

---

### VMWARE

Source: `src/cli/cmd_vmware.cpp`  
Owner: `DOT|VMWARE_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future VMWARE command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If VMWARE becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### VMWARE

Source: `x64base/src/cli/cmd_vmware.cpp`  
Owner: `DOT|VMWARE_IMPL`  
Category: `integration-stub`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future VMWARE command/integration work.

Usage contract:

```text
This file currently does not export a command handler.
  If VMWARE becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### VT200

Source: `src/cli/cmd_vt200.cpp`  
Owner: `DOT|VT200_IMPL`  
Category: `terminal-helper`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future VT200 terminal support.

Usage contract:

```text
This file currently does not export a command handler.
  If VT200 becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### VT200

Source: `x64base/src/cli/cmd_vt200.cpp`  
Owner: `DOT|VT200_IMPL`  
Category: `terminal-helper`  
Status: `placeholder-shim`  
Effect: `none`  
Mutates: `none`  
Usage access: `not-registered-here`  

Purpose:

Placeholder translation unit for future VT200 terminal support.

Usage contract:

```text
This file currently does not export a command handler.
  If VT200 becomes user-facing, add the runtime command handler and full usage contract together.
```

Notes:

```text
Contract marker documents that this file was inspected and intentionally left behavior-neutral.
```

---

### WA

Source: `src/cli/cmd_wamreport.cpp`  
Owner: `DOT|WA`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `WA USAGE`  

Purpose:

Print the WorkAreaManager/engine bridge report and pointer identity checks.

Usage contract:

```text
WA
  WA USAGE
```

Examples:

```text
WA
  WA USAGE
```

Notes:

```text
WA with no arguments prints the full WAM report.
  WA USAGE prints usage without inspecting the WorkAreaManager bridge.
  WA is read-only and does not mutate table data.
```

Related:

```text
WSREPORT
  AREA
  WORKSPACE
```

---

### WA

Source: `x64base/src/cli/cmd_wamreport.cpp`  
Owner: `DOT|WA`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `WA USAGE`  

Purpose:

Print the WorkAreaManager/engine bridge report and pointer identity checks.

Usage contract:

```text
WA
  WA USAGE
```

Examples:

```text
WA
  WA USAGE
```

Notes:

```text
WA with no arguments prints the full WAM report.
  WA USAGE prints usage without inspecting the WorkAreaManager bridge.
  WA is read-only and does not mutate table data.
```

Related:

```text
WSREPORT
  AREA
  WORKSPACE
```

---

### WEB

Source: `src/cli/cmd_web.cpp`  
Owner: `DOT|WEB`  
Category: `network`  
Status: `supported`  
Effect: `network-or-file`  
Mutates: `optional-filesystem`  
Usage access: `WEB USAGE`  

Purpose:

Open, fetch, or inspect web URLs using the default handler or WinHTTP.

Usage contract:

```text
WEB USAGE
  WEB OPEN <url>
  WEB LAUNCH <url>
  WEB GET <url>
  WEB HEAD <url>
  WEB FETCH <url> TO <file>
```

Examples:

```text
WEB OPEN https://example.com
  WEB HEAD https://example.com
  WEB GET https://example.com
  WEB FETCH https://example.com/data.csv TO tmp\data.csv
```

Notes:

```text
WEB USAGE prints usage and does not launch a browser, make a network request, or write files.
  WEB OPEN/LAUNCH use the OS default URL handler.
  WEB GET/HEAD use HTTP request support where implemented.
  WEB FETCH writes the response body to the requested file.
```

Related:

```text
SFTP
  PSHELL
```

---

### WEB

Source: `x64base/src/cli/cmd_web.cpp`  
Owner: `DOT|WEB`  
Category: `network`  
Status: `supported`  
Effect: `network-or-file`  
Mutates: `optional-filesystem`  
Usage access: `WEB USAGE`  

Purpose:

Open, fetch, or inspect web URLs using the default handler or WinHTTP.

Usage contract:

```text
WEB USAGE
  WEB OPEN <url>
  WEB LAUNCH <url>
  WEB GET <url>
  WEB HEAD <url>
  WEB FETCH <url> TO <file>
```

Examples:

```text
WEB OPEN https://example.com
  WEB HEAD https://example.com
  WEB GET https://example.com
  WEB FETCH https://example.com/data.csv TO tmp\data.csv
```

Notes:

```text
WEB USAGE prints usage and does not launch a browser, make a network request, or write files.
  WEB OPEN/LAUNCH use the OS default URL handler.
  WEB GET/HEAD use HTTP request support where implemented.
  WEB FETCH writes the response body to the requested file.
```

Related:

```text
SFTP
  PSHELL
```

---

### WHERE

Source: `src/cli/cmd_where.cpp`  
Owner: `DOT|WHERE`  
Category: `filter`  
Status: `supported`  
Effect: `filter`  
Mutates: `where-state filter-state`  
Usage access: `WHERE USAGE`  

Purpose:

Show, set, debug, or clear the WHERE predicate state bound into SET FILTER.

Usage contract:

```text
WHERE
  WHERE USAGE
  WHERE <expr>
  WHERE <expr> DEBUG
  WHERE CLEAR
  WHERE OFF
```

Notes:

```text
WHERE with no arguments reports current WHERE state.
  WHERE <expr> compiles the predicate, probes the current record for diagnostics, and delegates to SET FILTER.
  WHERE CLEAR and WHERE OFF clear WHERE state and the associated SET FILTER path.
  WHERE DEBUG prints compile/field diagnostics for the expression.
  WHERE USAGE prints usage without changing filter state.
```

Related:

```text
SETFILTER
  COUNT
  LIST
  SMARTLIST
```

Source comments:

```text
===============================
src/cli/cmd_where.cpp
WHERE expression state + shared evaluator + optional DEBUG plan dump
WHERE is bound into the runtime SET FILTER path.
===============================
```

---

### WHERE

Source: `x64base/src/cli/cmd_where.cpp`  
Owner: `DOT|WHERE`  
Category: `filter`  
Status: `supported`  
Effect: `filter`  
Mutates: `where-state filter-state`  
Usage access: `WHERE USAGE`  

Purpose:

Show, set, debug, or clear the WHERE predicate state bound into SET FILTER.

Usage contract:

```text
WHERE
  WHERE USAGE
  WHERE <expr>
  WHERE <expr> DEBUG
  WHERE CLEAR
  WHERE OFF
```

Notes:

```text
WHERE with no arguments reports current WHERE state.
  WHERE <expr> compiles the predicate, probes the current record for diagnostics, and delegates to SET FILTER.
  WHERE CLEAR and WHERE OFF clear WHERE state and the associated SET FILTER path.
  WHERE DEBUG prints compile/field diagnostics for the expression.
  WHERE USAGE prints usage without changing filter state.
```

Related:

```text
SETFILTER
  COUNT
  LIST
  SMARTLIST
```

Source comments:

```text
===============================
src/cli/cmd_where.cpp
WHERE expression state + shared evaluator + optional DEBUG plan dump
WHERE is bound into the runtime SET FILTER path.
===============================
```

---

### WHERECACHE

Source: `src/cli/cmd_wherecache.cpp`  
Owner: `DOT|WHERECACHE`  
Category: `diagnostics`  
Status: `supported`  
Effect: `mixed`  
Mutates: `where-cache`  
Usage access: `WHERECACHE USAGE`  

Purpose:

Inspect or tune the shared WHERE expression evaluation cache.

Usage contract:

```text
WHERECACHE
  WHERECACHE USAGE
  WHERECACHE STATS
  WHERECACHE CLEAR
  WHERECACHE CAP <n>
```

Examples:

```text
WHERECACHE
  WHERECACHE STATS
  WHERECACHE CAP 256
  WHERECACHE CLEAR
```

Notes:

```text
WHERECACHE with no arguments reports cache stats and usage.
  WHERECACHE USAGE prints usage and does not clear or resize the cache.
  CLEAR empties the cache; CAP changes the cache capacity.
  WHERECACHE does not mutate table data.
```

Related:

```text
WHERE
  SET FILTER
```

Source comments:

```text
===============================================
src/cli/cmd_wherecache.cpp
Developer command: WHERECACHE STATS | CLEAR | CAP <n>
===============================================
```

---

### WHERECACHE

Source: `x64base/src/cli/cmd_wherecache.cpp`  
Owner: `DOT|WHERECACHE`  
Category: `diagnostics`  
Status: `supported`  
Effect: `mixed`  
Mutates: `where-cache`  
Usage access: `WHERECACHE USAGE`  

Purpose:

Inspect or tune the shared WHERE expression evaluation cache.

Usage contract:

```text
WHERECACHE
  WHERECACHE USAGE
  WHERECACHE STATS
  WHERECACHE CLEAR
  WHERECACHE CAP <n>
```

Examples:

```text
WHERECACHE
  WHERECACHE STATS
  WHERECACHE CAP 256
  WHERECACHE CLEAR
```

Notes:

```text
WHERECACHE with no arguments reports cache stats and usage.
  WHERECACHE USAGE prints usage and does not clear or resize the cache.
  CLEAR empties the cache; CAP changes the cache capacity.
  WHERECACHE does not mutate table data.
```

Related:

```text
WHERE
  SET FILTER
```

Source comments:

```text
===============================================
src/cli/cmd_wherecache.cpp
Developer command: WHERECACHE STATS | CLEAR | CAP <n>
===============================================
```

---

### WHILE

Source: `src/cli/cmd_while.cpp`  
Owner: `DOT|WHILE`  
Category: `script`  
Status: `supported`  
Effect: `loop`  
Mutates: `while-state cursor delegates-command-effects`  
Usage access: `WHILE USAGE`  

Purpose:

Buffer and execute a WHILE...ENDWHILE loop from the current record while a
  boolean expression remains true.

Usage contract:

```text
WHILE USAGE
  WHILE <bool-expr> [QUIET]
  ENDWHILE
  ENDWHILE USAGE
```

Examples:

```text
WHILE GPA >= 3.0
      TUPLE LNAME,FNAME,GPA
  ENDWHILE
```

Notes:

```text
WHILE USAGE and ENDWHILE USAGE do not start or execute a loop.
  WHILE starts buffering; the shell must route body lines to WHILE_BUFFER.
  ENDWHILE executes buffered body lines through the canonical loop executor.
  Execution starts at the current record and advances one record per iteration.
  Buffered body command effects are owned by those commands.
```

Related:

```text
IF
  UNTIL
  SCAN
```

Source comments:

```text
============================================================================
path: src/cli/cmd_while.cpp
purpose: WHILE / ENDWHILE with private buffering (no loop_state deps)
usage:
  WHILE <bool-expr> [QUIET]  -> begin buffering; shell must route lines to WHILE_BUFFER
  ENDWHILE                   -> execute buffered body while <expr> remains true
notes:
  - Boolean evaluator is provided by shell via while_set_condition_eval(...).
  - Starts from the CURRENT record (does NOT force TOP).
  - Advances with A.skip(1) and stops hard at EOF/BOF or empty tables.
  - Buffer persists after ENDWHILE (mirrors ENDLOOP behavior).
============================================================================
```

---

### WHILE

Source: `x64base/src/cli/cmd_while.cpp`  
Owner: `DOT|WHILE`  
Category: `script`  
Status: `supported`  
Effect: `loop`  
Mutates: `while-state cursor delegates-command-effects`  
Usage access: `WHILE USAGE`  

Purpose:

Buffer and execute a WHILE...ENDWHILE loop from the current record while a
  boolean expression remains true.

Usage contract:

```text
WHILE USAGE
  WHILE <bool-expr> [QUIET]
  ENDWHILE
  ENDWHILE USAGE
```

Examples:

```text
WHILE GPA >= 3.0
      TUPLE LNAME,FNAME,GPA
  ENDWHILE
```

Notes:

```text
WHILE USAGE and ENDWHILE USAGE do not start or execute a loop.
  WHILE starts buffering; the shell must route body lines to WHILE_BUFFER.
  ENDWHILE executes buffered body lines through the canonical loop executor.
  Execution starts at the current record and advances one record per iteration.
  Buffered body command effects are owned by those commands.
```

Related:

```text
IF
  UNTIL
  SCAN
```

Source comments:

```text
============================================================================
path: src/cli/cmd_while.cpp
purpose: WHILE / ENDWHILE with private buffering (no loop_state deps)
usage:
  WHILE <bool-expr> [QUIET]  -> begin buffering; shell must route lines to WHILE_BUFFER
  ENDWHILE                   -> execute buffered body while <expr> remains true
notes:
  - Boolean evaluator is provided by shell via while_set_condition_eval(...).
  - Starts from the CURRENT record (does NOT force TOP).
  - Advances with A.skip(1) and stops hard at EOF/BOF or empty tables.
  - Buffer persists after ENDWHILE (mirrors ENDLOOP behavior).
============================================================================
```

---

### WORKSPACE

Source: `src/cli/cmd_workspace.cpp`  
Owner: `DOT|WORKSPACE`  
Category: `workspace`  
Status: `supported`  
Effect: `session`  
Mutates: `session`  
Usage access: `WORKSPACE USAGE`  

Purpose:

Report and manage live work-area/session layout.

Usage contract:

```text
WORKSPACE
  WORKSPACE USAGE
  WORKSPACE ALL
  WORKSPACE OPEN DBF
  WORKSPACE OPEN <dir>
  WORKSPACE OPEN <file.dbf>
  WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]
  WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]
  WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]
  WORKSPACE CLOSE
  WORKSPACE CLOSE <n> [m ...]
  WORKSPACE CLOSE <name|file|stem|alias>[,...]
  WORKSPACE SAVE <file>
  WORKSPACE LOAD <file>
  WORKSPACE TUPLES [LIMIT <n>] [OFFSET <n>] [AREA <n>]
```

Notes:

```text
WORKSPACE with no arguments is a report: it lists current open work areas.
  WORKSPACE ALL lists all area slots, including closed slots.
  WORKSPACE OPEN DBF scans the configured DBF path slot and opens tables into work areas.
  WORKSPACE OPEN <dir> scans a specific directory and opens DBFs into work areas.
  WORKSPACE OPEN <file.dbf> opens a single table into the current work area.
  WORKSPACE CLOSE closes all open work areas and clears relation/session state.
  WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.
  DDL owns schema/definition work; WORKSPACE owns live session/work-area state.
```

Related:

```text
DBAREA
  DBAREAS
  DDL
  REL
  STATUS
```

Source comments:

```text
IMPORTANT SYNTAX RULE:
- The directory/target is always the first argument after OPEN.
  Examples:
    WORKSPACE OPEN dbf TABLE
    WORKSPACE OPEN dbf CNX TABLE
    WORKSPACE OPEN table TABLE
    WORKSPACE OPEN DBF CNX TABLE
PATH RULE:
- Relative OPEN targets are resolved against the configured path slots,
  primarily the DBF slot established by INIT / SETPATH.
- Common shorthand such as `WORKSPACE OPEN dbf` and `WORKSPACE OPEN students`
  are treated as DBF-slot-relative requests.
```

---

### WORKSPACE

Source: `x64base/src/cli/cmd_workspace.cpp`  
Owner: `DOT|WORKSPACE`  
Category: `workspace`  
Status: `supported`  
Effect: `session`  
Mutates: `session`  
Usage access: `WORKSPACE USAGE`  

Purpose:

Report and manage live work-area/session layout.

Usage contract:

```text
WORKSPACE
  WORKSPACE USAGE
  WORKSPACE ALL
  WORKSPACE OPEN DBF
  WORKSPACE OPEN <dir>
  WORKSPACE OPEN <file.dbf>
  WORKSPACE OPEN <target> CNX [FALLBACK] [recursive] [TABLE]
  WORKSPACE OPEN <target> INX [FALLBACK] [recursive] [TABLE]
  WORKSPACE OPEN <target> CDX [FALLBACK] [recursive] [TABLE]
  WORKSPACE CLOSE
  WORKSPACE CLOSE <n> [m ...]
  WORKSPACE CLOSE <name|file|stem|alias>[,...]
  WORKSPACE SAVE <file>
  WORKSPACE LOAD <file>
  WORKSPACE TUPLES [LIMIT <n>] [OFFSET <n>] [AREA <n>]
```

Notes:

```text
WORKSPACE with no arguments is a report: it lists current open work areas.
  WORKSPACE ALL lists all area slots, including closed slots.
  WORKSPACE OPEN DBF scans the configured DBF path slot and opens tables into work areas.
  WORKSPACE OPEN <dir> scans a specific directory and opens DBFs into work areas.
  WORKSPACE OPEN <file.dbf> opens a single table into the current work area.
  WORKSPACE CLOSE closes all open work areas and clears relation/session state.
  WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.
  DDL owns schema/definition work; WORKSPACE owns live session/work-area state.
```

Related:

```text
DBAREA
  DBAREAS
  DDL
  REL
  STATUS
```

Source comments:

```text
IMPORTANT SYNTAX RULE:
- The directory/target is always the first argument after OPEN.
  Examples:
    WORKSPACE OPEN dbf TABLE
    WORKSPACE OPEN dbf CNX TABLE
    WORKSPACE OPEN table TABLE
    WORKSPACE OPEN DBF CNX TABLE
PATH RULE:
- Relative OPEN targets are resolved against the configured path slots,
  primarily the DBF slot established by INIT / SETPATH.
- Common shorthand such as `WORKSPACE OPEN dbf` and `WORKSPACE OPEN students`
  are treated as DBF-slot-relative requests.
```

---

### WSREPORT

Source: `src/cli/cmd_wsreport.cpp`  
Owner: `DOT|WSREPORT`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `WSREPORT USAGE`  

Purpose:

Print a workspace/status report covering open areas, LMDB/order summary,
  and table-buffer state.

Usage contract:

```text
WSREPORT
  WSREPORT USAGE
  WSREPORT ALL
```

Notes:

```text
WSREPORT with no arguments reports the current workspace and current area.
  WSREPORT ALL includes all open work areas in the area/index summary.
  WSREPORT USAGE prints usage and does not inspect areas.
  WSREPORT is read-only.
```

Related:

```text
AREA
  STATUS
  WORKSPACE
```

Source comments:

```text
================================
FILE: src/cli/cmd_wsreport.cpp
================================
```

---

### WSREPORT

Source: `x64base/src/cli/cmd_wsreport.cpp`  
Owner: `DOT|WSREPORT`  
Category: `diagnostics`  
Status: `supported`  
Effect: `report`  
Mutates: `none`  
Usage access: `WSREPORT USAGE`  

Purpose:

Print a workspace/status report covering open areas, LMDB/order summary,
  and table-buffer state.

Usage contract:

```text
WSREPORT
  WSREPORT USAGE
  WSREPORT ALL
```

Notes:

```text
WSREPORT with no arguments reports the current workspace and current area.
  WSREPORT ALL includes all open work areas in the area/index summary.
  WSREPORT USAGE prints usage and does not inspect areas.
  WSREPORT is read-only.
```

Related:

```text
AREA
  STATUS
  WORKSPACE
```

Source comments:

```text
================================
FILE: src/cli/cmd_wsreport.cpp
================================
```

---

### ZAP

Source: `src/cli/cmd_zap.cpp`  
Owner: `DOT|ZAP`  
Category: `destructive-table`  
Status: `supported`  
Effect: `remove-all-records`  
Mutates: `table-file closes-table order-state`  
Usage access: `ZAP USAGE`  

Purpose:

Remove all records from the current non-memo DBF while preserving structure.

Usage contract:

```text
ZAP USAGE
  ZAP
```

Examples:

```text
ZAP
```

Notes:

```text
ZAP USAGE prints usage before open-table checks.
  ZAP rewrites the current DBF with zero records and closes the table on success.
  ZAP currently refuses memo tables.
  Index containers must be rebuilt/rebound afterward.
```

Related:

```text
ERASE
  PACK
  RECALL
```

Source comments:

```text
src/cli/cmd_zap.cpp
ZAP — removes ALL records from the current DBF, preserving structure (header + field descriptors).
      Rewrites the file with record count = 0, updated timestamp, and EOF marker.
POLICY (2026):
  - Structural command (file-level operation)
  - Leaves table CLOSED on success
  - User must USE to reopen
  - Indexes must be rebuilt/rebound after
```

---

### ZAP

Source: `x64base/src/cli/cmd_zap.cpp`  
Owner: `DOT|ZAP`  
Category: `destructive-table`  
Status: `supported`  
Effect: `remove-all-records`  
Mutates: `table-file closes-table order-state`  
Usage access: `ZAP USAGE`  

Purpose:

Remove all records from the current non-memo DBF while preserving structure.

Usage contract:

```text
ZAP USAGE
  ZAP
```

Examples:

```text
ZAP
```

Notes:

```text
ZAP USAGE prints usage before open-table checks.
  ZAP rewrites the current DBF with zero records and closes the table on success.
  ZAP currently refuses memo tables.
  Index containers must be rebuilt/rebound afterward.
```

Related:

```text
ERASE
  PACK
  RECALL
```

Source comments:

```text
src/cli/cmd_zap.cpp
ZAP — removes ALL records from the current DBF, preserving structure (header + field descriptors).
      Rewrites the file with record count = 0, updated timestamp, and EOF marker.
POLICY (2026):
  - Structural command (file-level operation)
  - Leaves table CLOSED on success
  - User must USE to reopen
  - Indexes must be rebuilt/rebound after
```

---

### ZIP

Source: `src/cli/cmd_zip.cpp`  
Owner: `DOT|ZIP`  
Category: `archive`  
Status: `supported`  
Effect: `archive-file-operation`  
Mutates: `filesystem`  
Usage access: `ZIP USAGE`  

Purpose:

List, create, or extract ZIP archives through the configured ZIP backend.

Usage contract:

```text
ZIP USAGE
  ZIP LIST <archive.zip>
  ZIP CREATE <archive.zip> <path>
  ZIP EXTRACT <archive.zip> [target_dir]
```

Examples:

```text
ZIP LIST backups.zip
  ZIP CREATE source_bundle.zip src
  ZIP EXTRACT source_bundle.zip tmp\source_bundle
```

Notes:

```text
ZIP USAGE prints usage and does not touch archive files.
  ZIP LIST reads an archive and prints entries.
  ZIP CREATE writes an archive, adding .zip when needed.
  ZIP EXTRACT writes files under the target directory or current directory.
```

Related:

```text
COPY
  EXPORT
```

---

### ZIP

Source: `x64base/src/cli/cmd_zip.cpp`  
Owner: `DOT|ZIP`  
Category: `archive`  
Status: `supported`  
Effect: `archive-file-operation`  
Mutates: `filesystem`  
Usage access: `ZIP USAGE`  

Purpose:

List, create, or extract ZIP archives through the configured ZIP backend.

Usage contract:

```text
ZIP USAGE
  ZIP LIST <archive.zip>
  ZIP CREATE <archive.zip> <path>
  ZIP EXTRACT <archive.zip> [target_dir]
```

Examples:

```text
ZIP LIST backups.zip
  ZIP CREATE source_bundle.zip src
  ZIP EXTRACT source_bundle.zip tmp\source_bundle
```

Notes:

```text
ZIP USAGE prints usage and does not touch archive files.
  ZIP LIST reads an archive and prints entries.
  ZIP CREATE writes an archive, adding .zip when needed.
  ZIP EXTRACT writes files under the target directory or current directory.
```

Related:

```text
COPY
  EXPORT
```

---

