# DEV-05 Command System

```yaml
page_id: DEV-05
title: Command System
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Scope

This is the command-system architecture and workflow chapter. It is not a
replacement for the generated command reference, but it no longer needs to wait
for a hypothetical future crosswalk before describing the real current system.

## Current command authority stack

For a command that exists today, authority flows in this order:

1. runtime behavior
2. source command implementation and usage contract
3. HELP surfaces built from those contracts
4. `dotref.hpp` / `foxref.hpp` catalog layers
5. manuals and website prose

Practical meaning:

- runtime proves that a command exists and behaves a certain way
- source owns the usage contract and implementation truth
- HELP explains the command to users
- `dotref.hpp` and `foxref.hpp` are curated reference-header catalogs, not the
  implementation layer
- manuals summarize and connect the lanes; they do not invent command truth

## Reference-header policy

`dotref.hpp` is the canonical DotTalk++ command catalog layer for commands that
are implemented and intentionally surfaced in the current system.

`foxref.hpp` is the historical/classic support catalog layer. When a Fox-family
command has a real `cmd_*.cpp` implementation, its `foxref.hpp` entry should be
kept aligned with DotTalk++ reality rather than pretending to be an untouched
FoxPro clone.

Working rule:

- if a command has real code, the relevant reference-header entry should match
  current supported syntax and intent
- if source and reference headers disagree, source/runtime win until the header
  is repaired
- if manuals disagree with source/help/reference, manuals are wrong and must be
  repaired

## Command manual pipeline

```text
source usage contract / runtime registration
  -> HELP command/topic/artifact evidence
  -> META semantic catalog where seeded
  -> CMDHELPCHK validation
  -> source handler/build verification
  -> runtime proof
  -> command crosswalk
  -> Developer Manual
  -> User/Student derivations
  -> Website derivations
```

## Surface classes

`PUBLIC`, `DEV_ONLY`, `TRANSITIONAL`, `INTERNAL`, `SCAFFOLD`, `EDUCATIONAL`, `APP`, `ALIAS`, `LEGACY`, `UNKNOWN`.

## Current HELP rebuild rule

Current documented operator order:

1. If `dotref.hpp` changed, run `CMDHELP BUILD LEGACY` first.
2. Run `CMDHELP BUILD . d:\code\ccode\src`.
3. Run `CMDHELPCHK`.
4. Use plain `CMDHELP BUILD` only as the lighter refresh when the source root is
   already implied and no explicit source-root proof is needed.

Reason:

- `CMDHELP BUILD LEGACY` refreshes the classic `commands.dbf` / `cmd_args.dbf`
  path that still depends on the reference-header catalog
- `CMDHELP BUILD . d:\code\ccode\src` is now the richer current HELP DATA pass;
  it harvested `USAGE_CONTRACT` and `SOURCE_MINER` rows in addition to
  `REGISTRY`, `DOTREF`, `FOXREF`, `EDREF`, and `SHARED_MSG`
- `CMDHELPCHK` is the structural validation gate after rebuild

Observed verified run on 2026-07-07:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Observed outcome from that verified run:

- legacy report wrote `447` command rows and `2294` arg rows
- current HELP DATA reported `10846` line rows and `473` topics
- structural checks passed with `OK no structural issues found`

## Current command-family practical rule

The current command family is no longer waiting for a future crosswalk before
it can be described. The real state today is:

- command implementations live in `src/cli`
- command registration binds them into the shell/runtime
- source usage contracts are harvested into HELP
- `REGRESSION` provides curated top-layer shakedown entrypoints
- manuals explain the family after build/runtime/help evidence are in place

## Built-in versus extension doctrine

The command system has two different responsibilities:

1. protect the centrally governed built-in surface
2. leave controlled room for student, local, and experimental extension work

Working rule:

- built-in commands should remain centrally registered and reviewed
- extension commands should declare their ownership clearly and should not
  silently replace built-in truth
- manuals must distinguish canonical built-ins from educational, local,
  compatibility, or experimental surfaces

Examples of open command-architecture pressure:

- `SCX` and `SIX` show that index-lab commands can exist beside the ordinary
  CNX/CDX/LMDB command family
- educational commands may live outside the main everyday command surface while
  still being real supported study tools
- custom/student hooks are valid, but they belong to controlled extension lanes
  rather than ad hoc shadow registration

## Function and command bridge

The system also has a deliberate bridge between command surfaces and scalar
function surfaces.

That means the command architecture must allow for:

- verb-style command dispatch
- scalar function lookup
- command/function ambiguity canaries
- future metadata organization through `SYSFUNC`, `SYSCMD`, `SYSENTVAR`, and
  `SYSARGS`

The manual should preserve this as an architecture property, not treat it as an
isolated parser quirk.

## Lifecycle and diagnostics hooks

Command execution is not only a parser problem. It also exposes lifecycle
seams.

Relevant seams include:

- pre-poll and post-poll observation
- diagnostics gates and dev-gated tracing
- trigger and maintenance follow-on work
- messaging and locale-aware command reporting

Those seams belong in the command-system chapter because they shape how command
truth is observed, extended, and taught.

## Reflection report interpretation

`CMDHELPCHK` reflection reports are not all the same layer.

Working interpretation:

- `Subcommand Inventory` reflects curated `SET` family subcommands from the
  reference/command-catalog lane
- `Command Inventory` reflects the canonical `command_catalog` slice, not every
  registered shell token
- full command breadth still appears in `CMDHELP BUILD LEGACY`, current HELP
  DATA, shell registration, and reference-header lanes

Practical meaning:

- a short `Command Inventory` report is not automatically a bug
- a mismatched public/internal flag in reflection is a real catalog-policy issue
- if a command is in runtime/help/reference but missing from the canonical
  reflection slice, decide whether that is intentional curation or unharvested
  promotion

## Regression rule for command surfaces

Regression scripts must bootstrap their own environment.

That means a script should begin with lane setup such as:

```text
DO x64
```

or:

```text
DO cmdhelp
```

before it opens tables, workspaces, schemas, or ERSATZ paths.

Working rule:

- if an older script still has value but assumes a caller-owned environment,
  fix it
- if it no longer has value, retire it

## Manual and website derivation rule

The manual and website command prose should both harvest from the same evidence
spine:

- source usage contracts
- runtime proof
- HELP builds
- CMDHELPCHK
- reviewed canaries

Do not copy command truth back from the website into the manual when the source
project already owns that truth.
