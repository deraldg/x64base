# DotTalk++ Contract Registry v1

Status: active registry.

## Purpose

This registry lists contracts that are meant to constrain future DotTalk++ work.
It is not a full inventory of every note in the repository. It is the map for
contracts that should not be rediscovered from chat history.

## Evidence Classes

Use the governance evidence classes:

- Runtime-proven
- Report-proven
- Source-defined
- HELP-documented
- Metadata-staged
- Design-intended
- Deferred
- Historical
- Unknown
- Rejected

No contract may claim a stronger evidence class than the available proof.

## Active Contracts

| Contract | Kind | Evidence | Owner area | Source |
| --- | --- | --- | --- | --- |
| AI Agent Assignment Link Contract | Identity/integration/persistence | Source-defined + disposable X64 creation proof | identity, AI Portal, BBS | `docs/contracts/AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md`; `dottalkpp/data/schemas/syschatlnk_v1.schema.json` |
| Repository Role and Promotion Contract | Publication/governance/safety | Source-defined + mechanically guarded | governance, staging | `docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md`; `tools/staging/repository_role_guard.py` |
| Authority Order | Publication/governance | Source-defined | governance | `docs/governance/authority_order.md` |
| Evidence Classes | Publication/governance | Source-defined | governance | `docs/governance/01_evidence_classes.md` |
| Contract Shelf | Contract governance | Design-intended | contracts | `docs/contracts/README.md` |
| Contract Lane Manifest | Contract governance | Design-intended | contracts | `docs/contracts/CONTRACT_LANE_MANIFEST_V1.md` |
| Contract Lane Workflow | Contract governance | Design-intended | contracts | `docs/contracts/CONTRACT_LANE_WORKFLOW_V1.md` |
| Contract Manager Mode | Contract governance/runtime surface | Source-defined first wave | contracts, maintenance | `docs/contracts/CONTRACT_MANAGER_MODE_V1.md` |
| Sidecar Retention and Aging Contract | Development hygiene/retention/safety | Report-proven M0 | maintenance, repository hygiene | `docs/maintenance/SIDECAR_RETENTION_AND_AGING_CONTRACT_V1.md` |
| Website SelfDoc Publication Contract | Publication/full-stack/education | Design-intended | contracts, selfdoc, manualgen, website | `docs/contracts/WEBSITE_SELFDOC_PUBLICATION_CONTRACT_V1.md` |
| Contract Scan Baseline | Contract governance/report | Report-proven | contracts | `docs/contracts/reports/CONTRACT_SCAN_BASELINE_V1.md` |
| Metadata System Registry Contract | Metadata/governance/safety | Source-defined + report-proven | selfdoc, full-stack documentation | `docs/maintenance/lanes/full_stack_documentation/METADATA_SYSTEM_REGISTRY_CONTRACT_V1.md` |
| Reference Identity Authority Contract | Metadata/HELP/runtime identity | Source-defined + report-proven | runtime help, metadata, selfdoc, full-stack documentation | `docs/maintenance/lanes/full_stack_documentation/REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1.md` |
| Metacollect SYSCMD Candidate Contract | Metadata/runtime command projection | Source-defined | metadata, full-stack documentation | `docs/maintenance/lanes/full_stack_documentation/METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md` |
| CMDHELPCHK v2 Canonical Path Contract | HELP validation/tool lineage | Source-defined + report-proven | help, selfdoc, full-stack documentation | `docs/maintenance/lanes/full_stack_documentation/CMDHELPCHK_V2_CANONICAL_PATH_CONTRACT_V1.md` |
| Source Contract Vocabulary Contract | Source contract/classifier lineage | Source-defined + report-proven | selfdoc, comments, full-stack documentation | `docs/maintenance/lanes/full_stack_documentation/SOURCE_CONTRACT_VOCABULARY_CONTRACT_V1.md` |
| Messaging Exporter Lineage Contract | Messaging/tool lineage | Source-defined + report-proven | messaging, selfdoc, full-stack documentation | `docs/maintenance/lanes/full_stack_documentation/MESSAGING_EXPORTER_LINEAGE_CONTRACT_V1.md` |
| Language and Region Seams | Data/publication | Design-intended + source evidence | locale, metadata, messaging | `docs/LANGUAGE_AND_REGION_SEAMS_v1.md` |
| Usage Contract Harvesting | Usage | Source-defined | metadata/help | `src/meta/metacollect.cpp` |
| Source Contract Annotation | Source/provenance | Source-defined | include/source headers | `@dottalk.contract` annotations |
| Core UI Principles | UI | Design-intended | UI lanes | `docs/ui/CORE_UI_PRINCIPLES_V1.md` |
| Open Architecture GUI Plan | UI/authority/reuse | Design-intended + source skeleton | GUI core, wx, Python, CLI bridge | `docs/gui/OPEN_ARCH_GUI_PLAN_V1.md` |
| Unified GUI Core | UI/runtime facade | Design-intended + source skeleton | GUI core | `docs/gui/UNIFIED_GUI_CORE_V1.md` |
| GUI Threading/Event Model | UI/threading | Design-intended + source skeleton | GUI core, wx, Python | `docs/gui/GUI_THREADING_EVENT_MODEL_V1.md` |
| GUI Threading and RAII Contract | UI/threading/lifecycle | Design-intended + source skeleton | GUI core, wx, Python, TUI | `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md` |
| GUI Localization Message Contract | UI/localization | Source skeleton | GUI core, wx, Python | `docs/gui/GUI_LOCALIZATION_MESSAGE_CONTRACT_V1.md` |
| Windowed Application Contract | UI/windowed app | Design-intended | wx, Python GUI | `docs/gui/WINDOWED_APP_CONTRACT_V1.md` |
| Value/Locale/Collation Contract | Data/value/index | Design-intended | xbase, index, GUI core | `docs/database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md` |
| Database Safety Contract | Data/safety | Design-intended | database runtime, GUI, CLI maintenance | `docs/database/DATABASE_SAFETY_CONTRACT_V1.md` |
| wx Frontend Plan | UI/build | Source skeleton | wx GUI | `docs/gui/WX_FRONTEND_PLAN_V1.md` |
| Python Frontend Plan | UI/build | Source skeleton | Python GUI | `docs/gui/PYTHON_FRONTEND_PLAN_V1.md` |
| DotTalk Extension Exit Contract | Runtime/usage/safety/document-control | Design-intended + source-policy annotation | extension layer, CLI dispatcher, contract lane | `docs/contracts/DOTTALK_EXTENSION_EXIT_CONTRACT_V1.md` |
| Index Key Is A Field, Not An Expression | Usage/data | **Runtime-proven** | xindex, cdx, cnx, cli | `src/cli/cmd_index.cpp` usage contract; `INDEX USAGE` runtime readback 2026-07-14 |
| Index Lane Split (CNX x32 / CDX x64) | Data/index/safety | **Runtime-proven** | xindex, cdx, cnx, xbase | `src/cli/cmd_reindex.cpp`; `USE USAGE`, `CNX USAGE`, `CDX USAGE`, `BUILDLMDB USAGE` runtime readback 2026-07-14 |

## Usage Contract Lane

Usage contracts currently have the strongest existing extraction path.

Known shape:

- Source comments describe command usage.
- Runtime `USAGE`/`HELP`/`?` branches print usage.
- `metacollect` parses usage contracts.
- Metadata/help/manual lanes can promote the result.

Key source:

- `src/meta/metacollect.cpp`

Important fields already inferred or harvested include:

- command,
- category,
- status,
- noargs,
- mutates,
- usage-access,
- summary,
- usage lines,
- examples,
- notes,
- related topics.

This lane should become the model for other contract kinds.

## Gaps

The following contract kinds exist informally but need stronger registry entries
or extraction paths:

- file format contracts,
- index collation contracts,
- DBF/memo safety contracts,
- GUI event contracts,
- Python/C++ binding contracts,
- build option/dependency contracts,
- destructive command safety contracts,
- import/export locale contracts,
- test fixture contracts,
- sidecar metadata contracts.

### KNOWN ISSUE: 15 contracts live outside `docs/contracts/`, untracked and unregistered

**Raised 2026-08-16 (AIF-118), owner-assigned. Report only; nothing moved.**

Measured on `development`:

| Location | `*CONTRACT*.md` | Tracked | Named in this registry |
| --- | ---: | ---: | ---: |
| `docs/contracts/` | 15 `.md` | **14** | yes |
| `docs/maintenance/lanes/full_stack_documentation/` | 15 | **0** | 6 of 15 |

None of the 15 is gitignored. They were authored into the lane folder and never
promoted, so they exist on the maintainer's disk and in no commit: **a fresh
clone has none of them.**

**The registry half is worse than absent, it is CONFIDENTLY WRONG.** Six of the
15 are not merely mentioned -- they are **rows in the Active Contracts table
above**, carrying evidence classes: `METADATA_SYSTEM_REGISTRY` and
`REFERENCE_IDENTITY_AUTHORITY` and `CMDHELPCHK_V2_CANONICAL_PATH` and
`SOURCE_CONTRACT_VOCABULARY` and `MESSAGING_EXPORTER_LINEAGE` are all listed
`Source-defined + report-proven`, and `METACOLLECT_SYSCMD_CANDIDATE` as
`Source-defined`. Each row's Source column gives a full path into the lane
folder. **Those paths do not exist in any commit.** So this registry asserts a
proven evidence class for six contracts that a clone cannot open, and the rule
at the top of this file -- "no contract may claim a stronger evidence class than
the available proof" -- is violated by the table below it. A reader following
those paths gets a missing file, not a warning.

The other nine are neither tracked nor listed, including
`MANUAL_AUTHORITY_RECONCILIATION_CONTRACT_V1.md`, which governs which Developer
Manual copy is "current".

**`docs/contracts/` is not clean either:**
`DOTTALK_SOURCE_OBJECT_AND_LOCATION_CONTRACT_V1.md` sits in the right directory
and is UNTRACKED, so the correct location is necessary but not sufficient.

**Location is the whole defect.** `docs/contracts/` is tracked and registered by
convention; the lane folder is neither. A contract's authority is not in its
filename, so an active contract in the wrong directory is invisible to every
agent and every clone while still reading as authoritative to anyone who opens it.

**The same shape one level down, found first and now understood as a symptom.**
`docs/manuals/developer/dev/` holds 22 files, **21 untracked, none gitignored**,
carrying `DRAFT`, `DRAFT_PATCHED`, or `DRAFT_WITH_TEMPORARY_EVIDENCE_LANES`
(7 of the 22 are the last). The single tracked file,
`dev-20-semantic-field-hooks-and-pronouns.md`, makes the state inconsistent
rather than deliberate. The manual genuinely ships in two other places --
`developer-manual.mdx` on the website, and the dottalkpp HELP tables -- but
`HELP_TOPIC.CATALOG = 'DEV'` holds **1 row** (`HIER`) against DOT 301, FOX 170,
SYSTEM 138, ED 29, so that copy does not carry these chapters either. Three
locations: one uncommitted, one nearly empty, one shipping.
`MANUAL_AUTHORITY_RECONCILIATION_CONTRACT_V1.md` names six manual authority
roles and `docs/manuals/developer/dev/` is none of them.

**How it surfaced, because the method is the reusable part.** AIF-118 pointed
recall-graph nodes at `dev-08/09/10` as the Tier 1 answer for "about to read or
write DBF, memos, or indexes". The coverage gate passed in the working tree and
FAILED against a fresh `git archive` of the same commit -- the files resolve on
one machine and nowhere else. The gate had asserted `path.is_file()`, the
author's filesystem rather than the artifact that ships; it now asserts
membership in `git ls-files`
(`labtalk/portal/tests/test_recall_coverage.py`), and the nodes were retargeted
onto tracked files.

**Not claimed here:** whether these 15 contracts should move to
`docs/contracts/`, be tracked in place, or be retired. That is an owner decision
and the promotion rule below governs it. What is claimed is narrower and
measured: **they are unreachable from any clone, and this registry does not know
they exist.**

## Promotion Rule

A contract graduates only when its evidence changes:

| From | To | Required proof |
| --- | --- | --- |
| Chat-intended | Design-intended | contract doc added to repo |
| Design-intended | Source-defined | code/API/source comments implement the contract |
| Source-defined | Runtime-proven | executable test or runtime command proves behavior |
| Runtime-proven | HELP-documented | HELP/CMDHELP documents the same behavior |
| HELP-documented | Publication-ready | CMDHELPCHK/manualgen/selfdoc evidence is aligned |

## Review Triggers

Review this registry when:

- adding a new command,
- changing command `USAGE`,
- adding a file format or sidecar,
- changing index/search behavior,
- adding GUI-visible database behavior,
- adding a new UI lane,
- adding write/edit behavior,
- changing locale/language behavior,
- changing build dependencies or platform support.

## Lane Tooling

Current read-only scanner:

```powershell
python tools\contracts\contract_scan.py
```

The scanner inventories contract-like docs and source markers. It is an intake
aid, not a final validator.
