# Phase 1 Gate-1 Reference Disposition Record V1

Status: reviewed baseline (report-only) - lane: AIF-067 / full_stack_documentation
Generated: 2026-08-05 (full-stack doc flush v4)
Pipeline: `build_reference_identity_inventory` -> `build_reference_authority_crosswalk`
-> `validate_reference_identity_authority` -> `reference_disposition_recommend` (new)
Authority: `REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1.md` (authority order + entity namespaces)

## What this is

Phase 1 inventories dotref/foxref/edref against the registry, usage contracts, and
SYSFUNC, and classifies every difference. The crosswalk deliberately stops at review
rows (the contract forbids silent replacement); `reference_disposition_recommend.py`
attaches a recommended disposition + evidence to each. This record captures the
reviewed dispositions so the next run auto-accepts the deliberate ones and surfaces
only genuinely new disagreement.

## Classification (crosswalk + recommender)

```
ALIGNED_COMMAND            215
CURATED_REF_ONLY            51   (reference-only: subforms, FoxPro functions, aliases)
EDUCATIONAL_TOPIC           24
REGISTERED_REF_MISSING_USAGE 26  (aliases / subusage arms -- documented, not gaps)
REGISTERED_ONLY              2   (BUILD INFO / BUILD VECTORS -- BUILDVECTORS syntax variants)
duplicate identities        16
```

Recommender auto-dispositioned the review set (deliberate, no action):
FUNCTION_AUTHORITY 24, DELIBERATE_SUBFORM 19, DELIBERATE_ALIAS 12,
DELIBERATE_DUAL_HOME 7, FOXPRO_COMPAT_REFERENCE 7, EDUCATION_SURFACE/TOPIC 6.

## Verdict

Zero source defects in the presence-gap axis; zero curated-reference gaps. All
presence-gap review rows resolve to deliberate structure (aliases, subforms,
dual-home wording, FoxPro functions, education surface). The genuine findings are in
the duplicate-identity axis, below.

## Residual dispositions (the review that remained)

| Identity | Disposition | Evidence | Action |
| --- | --- | --- | --- |
| DDICT | CONTRACT_FORMAT_NORMALIZE | `/* @dottalk.usage surface: */` block the harvester could not read | DONE 2026-08-05: converted to `// @dottalk.usage`; catalog fallback 1 -> 0 |
| ERROR CLEAR / STATUS / TEST | DELIBERATE_ENTRY_VARIANT | also registered as `ERROR_CLEAR` etc. (spaced + underscore forms) | accept; no action |
| ERP, IDX | DELIBERATE_CLI_EDU_VARIANT | contract in `src/cli/cmd_*.cpp` and `src/edu/edu_*.cpp` | accept; one CMD identity, two contract sources (cli command + education surface); primary = registry per authority order |
| BBS, NET | TOOL_FALSE_POSITIVE | second "registration" is a `// Registered in shell_commands.cpp: registry().add(...)` comment | accept; crosswalk registry-scan matched inside a comment (see process note) |
| PSHELL | DUPLICATE_CONTRACT | two `// command: PSHELL` blocks (cmd_pshell.cpp + cmd_pshell_help.cpp) | FOLLOW-UP: reclassify the help block as `command: PSHELL HELP` (subcommand) |
| EXAMPLE | REGISTERED_DUPLICATE_DEFECT | `registry().add("EXAMPLE", ...)` twice in `shell_commands.cpp` (L475, L564) | FOLLOW-UP (source preflight): remove one registration |
| SQLHELP | REGISTERED_DUPLICATE_DEFECT | `dli::registry().add("SQLHELP", ...)` in `cmd_sql_help.cpp:209` and `shell_commands.cpp:424` | FOLLOW-UP (source preflight): confirm `dli::` is a distinct intentional registry, else remove the redundant add |

## Follow-ups this Gate opened

- Source preflight (own contract + build + regression) for the two duplicate
  registrations: EXAMPLE (in-file duplicate) and SQLHELP (self-register + central).
  Gate 1 names them with evidence; it does not edit registration itself.
- Contract dedup: PSHELL help block -> `PSHELL HELP` subcommand form.
- Process note (crosswalk improvement): `build_reference_authority_crosswalk` /
  the inventory registry-scan matches `registry().add("X", ...)` inside `//` comments,
  producing the BBS/NET false positives. Strip line comments before the scan so
  documentation references stop reading as second registrations.

## Tooling

- `tools/fullstack_docs/reference_disposition_recommend.py` -- the new Gate-1
  recommender. Report-only; consumes the crosswalk `entity_type` and the authority
  contract's compact-form rule; never resolves (no silent replacement).
- This record is the accepted disposition baseline. A future run compares its
  recommender output against this file; only new/changed dispositions need review.
