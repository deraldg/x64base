# DOCFLUSH-20261013-002 DOTREF M3C review gate

Date: 2026-10-13. Run: `DOCFLUSH-20261013-002`. Lane: AIF-171.

Repository revision: `a48a709e968d8c208b6c19bd699028f0d25ade3e` on
`development` in `D:\code\ccode`.

Status: report-only candidate ready for owner review. No M3D candidate DBF,
generated header, live HELP/META mutation, manual generation, website staging,
commit, push, or publication is authorized by this record.

## Result

The fresh source harvest and M3B authority join pass G0-G2 with 231 canonical
commands and zero blocking finding. M3C then resolves the complete compiled DOT
member set:

| Entity kind | Rows |
| --- | ---: |
| Canonical command | 231 |
| Display alias | 23 |
| Subcommand | 12 |
| Implemented extension function | 2 |
| Total | 268 |
| Unresolved or silently carried | 0 |

The current header contributes migration membership and proposed DOT-native
wording only. It does not mint identities. Every member resolves through
SYSCMD, SYSSUBCMD, an explicit usage-contract alias, the shortcut/reference
registries, source syntax, registry-handler equivalence, or implemented
extension-function source.

## Hash-bound review package

| Artifact | SHA-256 |
| --- | --- |
| `include/dotref.hpp` migration input | `F1C30234AF8765BF5732BEF926928F9AF583B22AC9AC7F14DBA3DDD895AD33E5` |
| `dotref_m3/sysref_harvest_manifest_v2.json` | `10CFAA1BA5B15C773254424A752254283EFF60E3E9373369368575D3A9ED054E` |
| `dotref_m3/assembly_v3/reports/gate_results.json` | `88C5D4F16E63C113C1EC30212288D6DEFCF117BD7E7EA3719097F2C62DAD959F` |
| `dotref_m3/assembly_v3/reports/authority_join_report.json` | `B8472CCA2F3E407722E96C8E76B78AFADBB20EEEB4B27C07CD4FCB6FDDCA233D` |
| `dotref_m3/migration_closure_v3/reports/closure_summary.json` | `4EC17C2631F6193D17CC1E4F692E37D40828BE9971572CD199BDB38907E38A7E` |
| `dotref_m3/migration_closure_v3/candidate/refscope_candidate.csv` | `FBA1B3BED9A9B6EB8659D852AE911F7F4FA62CEFBC620E2B526380A98BCA2971` |
| `dotref_m3/migration_closure_v3/candidate/refaliases_candidate.csv` | `359011BEFEBA9FB3859026DDF230849B76F62AB3DC26D4113C0A236B0C5B2FE5` |
| `dotref_m3/migration_closure_v3/candidate/refvoice_proposed.csv` | `BAAB854D93C19AB2E7B2F31168A0B024F11ADD061227EECB66FB8C9DACDFB2C8` |

Paths in the table are relative to
`docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20261013-002/`
unless shown otherwise.

## Decisions required before M3D

1. Approve the 268-row source-resolved DOT membership scope and the 23 explicit
   display-alias edges.
2. Approve importing the 536 current syntax/summary fields as the initial
   `en-US/native` REFVOICE migration baseline, still source-hash guarded. This
   preserves deliberate concise DOT wording while ending steady-state reads
   from the hand-edited header.
3. Rule the `supported` vocabulary before emission. The provisional assembler
   currently treats only literal `status: supported` as supported. That creates
   44 true-to-false differences and is knowingly too narrow for statuses such
   as `supported-conditional`, `developer`, and `active`. Recommended rule:
   `supported` states whether the identity belongs on the usable DOT reference
   surface; maturity and audience remain separate fields. Map `supported`,
   `supported-conditional`, `developer`, `active`, `dev-canary`, `dev-tool`,
   `document-control-readonly`, `implementation-present`, and
   `compatibility-alias` to true. Map `experimental`, `sample-extension`,
   `stub`, `supported-stub`, `supported-stub-mixed`, `deprecated`,
   `deprecated-compat`, `reserved`, `review-needed`, helper/shim/supplemental,
   and rejected states to false.

After approval, M3D may encode that closed vocabulary as reviewed data, emit
candidate normalized tables plus DOTREF DBF/DTX and generated C++ data, and run
G0-G7 twice for determinism. M3E still requires a separate exact apply
authorization before touching the live header or rebuilding HELP/META.
