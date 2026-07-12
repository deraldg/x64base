# AI Friendly Workflow v1

Status: seed workflow.

## Purpose

Define the simplest durable workflow for AI-assisted DotTalk++ / LabTalk work:

```text
capture -> classify -> distill -> anchor -> route -> promote
```

## 1. Capture

Capture only material with reuse value:

- a decision that should constrain future work
- a successful repair or review pattern
- a good explanation of system behavior
- a reusable agent instruction
- a candidate source comment, contract, lab, or manual section
- a drift finding that may recur

Do not capture everything. Raw interaction volume is not the goal.

## 2. Classify

Use one or more tags:

```text
contract_candidate
source_comment_candidate
help_candidate
selfdoc_candidate
manualgen_candidate
labtalk_candidate
proof_candidate
agent_instruction
workflow_pattern
drift_or_risk
historical_note
archive_only
reject
```

## 3. Distill

Convert long material into a small project asset:

- decision record
- checklist
- source-comment patch candidate
- contract draft
- lab step
- proof note
- manual section candidate
- agent rule
- drift report

Keep the original retained material as source material only when it is useful.

## 4. Anchor

Every promoted item needs at least one anchor:

- source file
- runtime transcript
- test or smoke report
- HELP/CMDHELP output
- CMDHELPCHK result
- SelfDoc report
- contract registry row
- LabTalk registry row
- manualgen report
- explicit design-intent note

If no anchor exists, keep the item as `chat-intended`, `draft`, or
`review-needed`.

## 5. Route

Route to the existing system first:

| Finding | First route |
| --- | --- |
| future rule | contracts |
| command syntax or behavior | source usage block plus HELP/CMDHELPCHK |
| source documentation | SelfDoc/comment lane |
| publication candidate | MDO/manualgen |
| lesson/lab/case idea | LabTalk |
| runtime behavior claim | proof report or test |
| agent working rule | `docs/agents` |
| cleanup/noise issue | maintenance/repo hygiene |

## 6. Promote

Promotion is allowed only when the evidence class is honest.

Examples:

- A good chat explanation can become a `manualgen_candidate`.
- A repeated rule can become a `contract_candidate`.
- A command behavior claim can become `runtime-proven` only after source or
  runtime evidence exists.
- A teaching idea can become LabTalk `student_ready` only after proof and review.

## Simplification Rule

During every AI Friendly pass, look for consolidation:

- merge overlapping notes
- replace raw chat with a short anchored artifact
- update existing registries instead of creating new ones
- point to existing reports instead of regenerating equivalent reports
- retire stale drafts when a stronger artifact exists

## Report-Only Default

AI Friendly curation defaults to report-only.

Do not mutate DBFs, HELP tables, metadata catalogs, generated catalogs, manual
publication outputs, runtime fixtures, backups, or archive material unless the
current task explicitly authorizes that mutation.
