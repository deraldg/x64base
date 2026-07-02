# Blackbox Lanes v1

Blackbox is the educational and architectural model for DotTalk++ SelfDoc systems:

```text
DATA IN -> BLACKBOX PROCESS -> INFORMATION OUT
```

The Blackbox model is an ABC-of-computing teaching frame. It explains how data becomes information through named, repeatable processing.

## COMMENTS Blackbox

DATA IN

- C++ source files
- source comments
- `@dottalk.usage v1` contracts
- command-local usage text

BLACKBOX PROCESS

- scan
- harvest
- classify
- import
- validate
- compare against HELP coverage

Current runtime boundary

- preserve source evidence in the comments workspace
- support review, classifier disposition, and later regeneration work
- do not assume current `CMDHELP BUILD` reads `SRC*` DBFs back as its primary live input

INFORMATION OUT

- SRCFILE
- SRCBLOCK
- SRCLINE
- SRCUSAGE
- SRCCLASS
- SRCDISP
- SRCALIAS
- MEMO_LINES
- comments workspace

## HELP Blackbox

DATA IN

- command registry
- `dotref.hpp`
- `foxref.hpp`
- source usage contracts
- curated help rows
- source-mined facts

BLACKBOX PROCESS

- CMDHELP BUILD
- optional legacy comparison
- HELP DATA export
- coverage validation
- runtime smoke

Current proof layers

- `CMDHELP BUILD` collects from registry, source usage contracts, curated help, and direct source mining
- `CMDHELP` proves current HELP DATA visibility
- `DOTHELP` / `HELP /DOT` prove compiled DOTREF/router visibility
- these surfaces are related, but one green surface does not prove the others

INFORMATION OUT

- help_line.dbf
- help_topic.dbf
- help_artifacts.dbf
- commands.dbf
- cmd_args.dbf
- CMDHELP reports
- HELP runtime surface
- DOTHELP / HELP /DOT runtime surface

## MANUALGEN Blackbox

DATA IN

- manual sections
- appendices
- media anchors
- manifests
- review queues
- publication candidates

BLACKBOX PROCESS

- assemble
- normalize
- validate
- publish
- catalog
- smoke MANUAL runtime surface

INFORMATION OUT

- published manual
- MAN* catalog
- MANUAL runtime command output
- regeneration cookbook

## DATADICT Blackbox

DATA IN

- data dictionary manifests
- compact DD* catalog rows
- long x64 DATA_DICTIONARY_* physical tables
- schema, import, staging, promotion, and proof artifacts

BLACKBOX PROCESS

- candidate staging
- import
- DBF readback validation
- CDX tag build
- LMDB mirror build
- DDICT runtime smoke

INFORMATION OUT

- DD* catalog
- DATA_DICTIONARY_* physical artifacts
- DDICT STATUS/TABLES/OBJECTS/FIELDS/TAGS/REL/EVIDENCE
- manifests and boundary ledgers

## MESSAGING Blackbox

DATA IN

- hard-coded runtime text
- message identifiers
- message arguments
- locale/language selection
- language text rows

BLACKBOX PROCESS

- extract
- catalog
- localize
- validate placeholders
- replace source text gradually
- smoke language fallback

INFORMATION OUT

- x64base message catalog
- typed runtime messages
- localized command output
- reportable warnings/errors/status text

## MAINT relationship

BBOX teaches the model. MAINT governs the process. Runtime inspectors such as MANUAL and DDICT prove particular lanes.
