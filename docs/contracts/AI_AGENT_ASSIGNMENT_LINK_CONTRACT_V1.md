# AI Agent Assignment Link Contract v1

Status: source-defined; runtime proof is limited to disposable X64 table creation.

Owning lifecycle: AI Systems Integration / LabTalk AI Portal. Change class: C2.

AIF lane: `AIF-086`. This artifact was added by `member.ai.codex.local` as a
contributing agent; current lane stewardship remains with
`member.ai.claude.cowork` and final authority remains with `member.derald`.

## Purpose and row grain

`SYSCHATLNK` is the durable crosswalk between an AI agent, its governed team
assignment, a provider conversation, the local project/work context, and an
optional AI-BBS thread. One row means:

> one `SYSASSIGN` assignment participating in one locally identified conversation

The table does not replace `SYSMEMBER`, `SYSASSIGN`, `SYSTHREAD`, `SYSPOST`, or
`ai_runs`. It joins them. An external agent must have a `SYSMEMBER` member and a
`SYSASSIGN` assignment before a link row is authoritative.

## Identity invariants

1. `LINKKEY` is the globally unique, immutable identifier for the
   agent-assignment/conversation binding. Use an opaque locally minted value such
   as `alink:v1:<uuid>`; never derive it from a display name, path, email address,
   or mutable provider title.
2. `CONVKEY` is the immutable local conversation identifier. Every participating
   agent gets a separate row with a different `LINKKEY` and the same `CONVKEY`.
3. `(ASSIGNID, CONVKEY)` is unique. Reassigning work creates a new link row; it
   does not rewrite the historical assignment.
4. `MEMBERID` and `MKEY` identify the agent through `SYSMEMBER`. `ASSIGNID`
   identifies its role/work/permission context through `SYSASSIGN`. `MEMBERID`
   must agree with `SYSASSIGN.MEMBERID`; `WORKID` is the observed
   `SYSASSIGN.WORK` value and must agree when both are nonzero.
5. `PROVIDER`, `PRODUCT`, and `MODEL` describe the agent endpoint. They are
   attributes, not identity. This supports Codex, ChatGPT, Copilot, Claude, local
   models, and later providers without changing the key model.
6. `SRCPROJ`, `SRCCHAT`, and `SRCTHREAD` are provider-native identifiers.
   Provider values may be absent or change representation; `LINKKEY` and
   `CONVKEY` remain stable.
7. `TITLE`, `CWD`, `UISECT`, `UIPOS`, `PINPOS`, `PINNED`, and `ARCHIVED` are a UI
   observation. They must never be used as a primary or foreign key.

## Multilingual and time contract

The X64 table is UTF-8. `LOCALE` carries a BCP 47 natural-language tag such as
`en-US`, `fr-CA`, or `ja-JP`. `CODELANG` carries the primary implementation or
task language such as `cpp`, `python`, `sql`, `dotscript`, or `mixed`.

`CREATEDAT`, `MODAT`, and `OBSAT` are UTC Unix epoch seconds:

- `CREATEDAT`: provider conversation creation time, or the first observed time
  when the provider does not expose creation time;
- `MODAT`: provider conversation last-modified time, never earlier than
  `CREATEDAT`;
- `OBSAT`: time the UI/provider snapshot in this row was observed.

`VFROM`, `VTHRU`, and `ROWVER` preserve the identity subsystem's bitemporal row
convention. Zero `VTHRU` means current. `STATUS` is `0=active`, `1=closed`,
`2=invalidated`. `SENSCLASS` is required because titles, paths, and external IDs
may be internal even when the schema is publishable.

## Join map

| From `SYSCHATLNK` | To | Meaning |
| --- | --- | --- |
| `MEMBERID` | `SYSMEMBER.ID` | governed AI/member identity |
| `ASSIGNID` | `SYSASSIGN.ID` | role, permission set, work, and reporting context |
| `PROJKEY` | `projects.yaml:projects[].id` | portal project family |
| `RUNID` | `ai_runs.yaml:runs[].run_id` | evidence/run record |
| `BBSBOARD` | `SYSBOARD.BKEY` | human-readable BBS board route |
| `BBSTHRID` | `SYSTHREAD.ID` | pseudo-chat/worklog thread |
| `CONVKEY` | other `SYSCHATLNK.CONVKEY` rows | all agent assignments in one conversation |

Relations are initially `SOFT`: writers validate them before persistence and
audits report drift. No cascade delete is allowed across identity, conversation,
or BBS history.

## AI Portal, BBS, and pseudo-chat placement

The LabTalk portal exposes the contract, schema, and explicit-run proof through
`portal.agent_assignment_links`. This puts the crosswalk beside AI Portal work,
before general projects and reports, so an agent can resolve identity and
assignment before opening a BBS or pseudo-chat route.

For a BBS handoff, retain `SYSPOST.RUNID` and include `LINKKEY` and `CONVKEY` in
the structured handoff metadata. `BBSTHRID` maps the provider conversation to
the existing `SYSTHREAD`; it must not create a second BBS conversation object.
Pseudo-chat reads all link rows for a `CONVKEY`, resolves the BBS thread when
present, then orders `SYSPOST` records by `POSTAT` and `ID`.

UI order is deliberately observational. A rename, pin, archive, drag, project
move, or provider-side sort may update the UI fields and `MODAT`/`OBSAT` without
changing either unique link identifier.

## Physical schema and proof

- Schema: `dottalkpp/data/schemas/syschatlnk_v1.schema.json`
- Explicit-run proof: `dottalkpp/data/scripts/ddl/syschatlnk_x64_regression.dts`
- Portal registry: `labtalk/registries/agent_assignment_links.yaml`
- Process flow: `labtalk/diagrams/ai_agent_assignment_link_pfd_v1.mmd`
- Data flow: `labtalk/diagrams/ai_agent_assignment_link_dfd_v1.mmd`

The schema declares CDX lookup plans. DDL sidecar emission proves declared
index intent; it does not by itself prove production index materialization or a
live identity/BBS writer. Those remain later integration gates.
