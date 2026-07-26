# DD-001 Data Dictionary Control Plan v0

## Status

Mode: **REPORT_ONLY / ORGANIZING CONTINUATION**  
Repo package inspected: `ccode_homegrown_20260527-055727.zip`  
Protected mutations: **0**

## Current counts from corrected repo package

| Metric | Count |
|---|---:|
| Total files | 981 |
| C/C++-like files | 908 |
| Python files | 20 |
| JSON files | 5 |
| Schema JSON files | 3 |
| Parsed `@dottalk.usage v1` rows | 208 |
| Parsed registry entries | 223 |

## Controlling idea

The data dictionary should become the living catalog contract between:

- physical x64base data structures,
- DotTalk++ command/help/messaging/runtime surfaces,
- schema/rule/expression declarations,
- source-comment and MetaFact provenance,
- runtime and maintenance scripts,
- optional educational overlays.

## Critical boundary

The dictionary must support three profiles without collapsing them:

```text
ENGINE
  x64base core; no required student/LabTalk/case/media artifacts.

PROFESSIONAL
  DotTalk++ runtime, HELP, dictionary, scripting, metadata, reports;
  no visible student layer by default where possible.

EDUCATIONAL
  Optional LabTalk, cases, student commands, storyboards/media, teaching examples.
```

## First implementation stance

Do not begin by creating promoted DBFs. Begin by generating report-only candidate rows:

1. DD-001 physical table/field/index/memo scan.
2. DD-002 command/help/source-contract scan.
3. DD-003 script/runtime/maintenance registry.
4. DD-004 build profile and overlay boundary audit.
5. DD-005 MetaFact bridge extension plan.

The existing `dt::meta::MetaFact` model is the best bridge point. It already has domains for command, function, help text, message, field dictionary, and runtime proof. Extend or align with it before inventing a disconnected metadata system.
