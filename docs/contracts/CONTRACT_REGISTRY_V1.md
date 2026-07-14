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
| Authority Order | Publication/governance | Source-defined | governance | `docs/governance/authority_order.md` |
| Evidence Classes | Publication/governance | Source-defined | governance | `docs/governance/01_evidence_classes.md` |
| Contract Shelf | Contract governance | Design-intended | contracts | `docs/contracts/README.md` |
| Contract Lane Manifest | Contract governance | Design-intended | contracts | `docs/contracts/CONTRACT_LANE_MANIFEST_V1.md` |
| Contract Lane Workflow | Contract governance | Design-intended | contracts | `docs/contracts/CONTRACT_LANE_WORKFLOW_V1.md` |
| Contract Manager Mode | Contract governance/runtime surface | Source-defined first wave | contracts, maintenance | `docs/contracts/CONTRACT_MANAGER_MODE_V1.md` |
| Website SelfDoc Publication Contract | Publication/full-stack/education | Design-intended | contracts, selfdoc, manualgen, website | `docs/contracts/WEBSITE_SELFDOC_PUBLICATION_CONTRACT_V1.md` |
| Contract Scan Baseline | Contract governance/report | Report-proven | contracts | `docs/contracts/reports/CONTRACT_SCAN_BASELINE_V1.md` |
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
