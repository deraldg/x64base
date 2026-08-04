---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260804-011
  recorded_at_utc: 2026-08-04T07:30:00Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: system schema map + normalization/dogfood direction
  project:
    id: project.ai_systems.integration
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 05f049b57
  authorization:
    requested_by: maintainer
    scope: inventory every subsystem schema and frame a normalize + dogfood direction (research/charter only)
  report:
    path: docs/maintenance/SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md
    kind: lane_charter
---

# System Schema Map + Normalization / Dogfood Direction (v1)

Status: research + proposed direction. No build. One place to see every schema
across the AI Portal, so a repeatable build/maintain process can be normalized on
top of it. The forward thesis: the AI Project should dogfood x64base for its own
governance state.

## Part 1 -- On-disk DBF schemas (the engine dogfooding itself)

These are real xBase tables the engine reads/writes. Conventions across all three:
physical names <= 10 chars (classic-browsable); 64-bit ids/epochs stored as
`N(20,0)` decimal text with `0` = unset; enums as small `N` codes; bools as `L`.

### 1A. Identity / Security -- `data/metadata/identity/` (lane AIF-045)

Nine SYS* tables (`include/identity/identity_schema.hpp`), one per
`InMemoryIdentityStore` vector. Enforced through `dottalk::identity::agent_permitted(perm)`
-> `Decision{allowed,reason}` (deny-precedence resolver); this is the same primitive
`USER`, `NET`, and the BBS daemon all call.

| Table | Purpose | Key fields |
|---|---|---|
| SYSUSER | human/AI accounts | ID, UKEY, LOGIN, DISPLAY, AUTHKIND, CRED (Argon2id PHC, 128), STATUS, PROFHOME, VFROM/VTHRU/ROWVER |
| SYSMEMBER | participants (peers) | ID, USERID, MKEY, KIND (0 Human/1 AI/2 Service/3 External), DEFROLE, DEFPSET, STATUS, VFROM/VTHRU/ROWVER |
| SYSROLE | roles | ID, RKEY, RNAME, RKIND, DESCR, STATUS |
| SYSPERM | permissions | ID, PKEY, RESCLASS, PACTION, RISK, REQAPPR (L), STATUS |
| SYSROLEPERM | role -> perm | ROLEID, PERMID |
| SYSMEMROLE | member -> role (scoped) | MEMBERID, ROLEID, ORGSCOPE, WORKSCOPE |
| SYSOVERRIDE | per-member allow/deny override | MEMBERID, PERMID, EFFECT, ORGSCOPE, WORKSCOPE |
| SYSASSIGN | org/work assignment | ID, MEMBERID, ORGUNIT, WORK, ROLE, PSET, REPORTSTO, AKIND, STATUS, VFROM/VTHRU/ROWVER |
| SYSGRANT | authorization requests + grants | ID, REQBY, GRANTTO, ROLEASN, WORK, RESSCOPE, ACTSCOPE, RISK, GRANTAT, EXPAT, STATUS, REASON, SRCREPORT |

Notes: bi-temporal validity (`VFROM/VTHRU`) + optimistic-concurrency (`ROWVER`) on
the durable tables; the request->approve->expire workflow is entirely SYSGRANT rows;
`USER SAVE/LOAD/VERIFY` is the APH-5 round-trip proof over this set.

### 1B. BBS / Pseudo-Chat -- `data/metadata/bbs/` (lane AIF-052)

Three tables (`include/bbs/bbs_schema.hpp`). This is the substrate for the AI-BBS
AND the Pseudo-Chat return lane (Pseudo-Chat is a read-by-visit / write-by-relay
usage pattern over these same tables, mirrored to the website Agent Sync page).

| Table | Purpose | Key fields |
|---|---|---|
| SYSBOARD | boards/rooms | ID, BKEY, NAME, KIND (0 governance/1 chat/2 notice), POSTPERM (-> SYSPERM.PKEY), STATUS, VFROM/VTHRU/ROWVER |
| SYSTHREAD | threads | ID, BOARDID (-> SYSBOARD), SUBJECT, OPENEDBY (-> SYSMEMBER, 0 unknown), OPENAT, STATE (0 open/1 answered/2 closed), LASTPOST |
| SYSPOST | posts (attributed, append-only) | ID, BOARDID, THREADID, AUTHORID (-> SYSMEMBER), AUTHKIND, KIND (0 post/1 reply/2 agent_prompt/3 agent_reply/4 system), BODY C(240), REFGRANT (-> SYSGRANT), RUNID (-> ai_runs), POSTAT, STATUS (0 posted/1 redacted) |

Recurring constraint: `BODY` is `C(240)` -- "memo upgrade deferred." The 64-bit memo
work is wanted by four lanes at once (AIF-070, AIF-082 6.10, AIF-083 F5, and the
ruling table below). That is a normalization pressure point, not a detail.

### 1C. Rulings -- (lane AIF-082, `include/portal/ruling_schema.hpp`)

`SYSRULING` -- APPEND-ONLY (a status change is a new row; current status = highest
`DECIDEDAT` per RULEID, exactly like SYSPOST). **Schema authored + source-evidenced;
NOT built, NOT seeded, NO runtime** -- a maintainer handoff
(`RULING_STATE_DOGFOOD_V1.md`).

| Table | Key fields |
|---|---|
| SYSRULING | ID, RULEID, LANE, RULEGROUP, STATUS (0 proposed/1 ratified/2 rejected/3 superseded/4 withdrawn), DECIDEDAT, DECIDEDBY (-> SYSMEMBER), PROPOSEDAT, STEWARD, SUPERBY, BLOCKS, NOTE (one line, NOT the argument), ROWVER |

Its header states the whole thesis of this document verbatim: *"state that is authored
drifts, state that is derived cannot. So ruling STATE moves into the store the project
already dogfoods, and the console derives from it."* Design rule: **sheet = argument,
table = decision.**

## Part 2 -- The tracking layer (authored YAML/MD -- the part that drifts)

Document / task / project / lane tracking lives OUTSIDE the engine, as authored
files under `labtalk/registries/`, `docs/ai-friendly/`, and `coordination/`:

| Artifact | Shape | Records |
|---|---|---|
| `labtalk/registries/projects.yaml` | `projects: [ {id,name,kind,status,root,lanes,docs,parent,...} ]` | projects (project.x64base.runtime, project.ai_systems.integration, project.bbs.cooperation, ...) |
| `labtalk/registries/ai_portal_tasks.yaml` | `schema: labtalk.ai_portal.tasks.v1` | tasks / documentation-flush state; public projection at /docs/labtalk/current-work |
| `labtalk/registries/ai_runs.yaml` | `runs: [...]`, `current_by_lane{}`, `current_by_project{}` | the five-role run records (AIF-050); the lane -> newest-run index the reports read |
| `labtalk/registries/proofs.yaml` | `proofs: [ {id,label,state,source,notes} ]` | the proof ledger (runtime_observed / source_defined / ...) |
| `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | markdown table: `ID \| Source \| Classification \| Candidate route \| Evidence anchor \| Status \| Notes` | every AIF lane (86 rows) |
| `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | markdown: Current Lane State + Session Log | dashboard + per-closeout log (AIF-006) |
| `coordination/aif/AIF-NNN.claim` | atomic O_EXCL claim file | lane-number ownership (AIF-050) |
| `@dottalk.file` / `@dottalk.usage` | per-source-file header block | subsystem/lane/owner/status + command usage contract (AIF-042) |
| session closeouts (`docs/maintenance/SESSION_CLOSEOUT_*`) | `ai_report_audit` envelope + prose | the durable per-session record |

## Part 3 -- The cross-link graph

Everything already points at the identity spine and the run registry:

- `SYSPOST.AUTHORID` / `SYSTHREAD.OPENEDBY` -> `SYSMEMBER.ID` (attribution)
- `SYSBOARD.POSTPERM` -> `SYSPERM.PKEY` (the RBAC check on POST)
- `SYSPOST.REFGRANT` -> `SYSGRANT.ID` ; `SYSRULING.DECIDEDBY` -> `SYSMEMBER.ID`
- `SYSPOST.RUNID` -> `ai_runs.yaml` run ; `ai_runs.current_by_lane[LANE]` -> the intake row + the report's active-lane table
- every source file -> `@dottalk.file` lane -> intake row -> claim file -> run -> closeout -> dashboard Session Log

The graph is coherent; the problem is that half of it is DBF (derived, cannot drift)
and half is authored markdown/YAML (drifts).

## Part 4 -- Normalization + dogfood thesis

**The divide is the whole finding.** Identity, BBS, and (schema'd) rulings live in
DBF -- the engine's own store -- so a report over them is DERIVED and cannot drift.
The lane/run/proof/task tracking lives in authored YAML/MD, and it DRIFTS. Measured
this session alone: the July-28 static report showed 15 lanes and neither AIF-086
nor AIF-087; AIF-087 has no run row so it never reaches the active table;
`CURRENT_TARGET.md` was 96% stale strata (AIF-082); the rulings sheet's hand-kept
total read 20 while parsing found 17. Same shape every time: authored state drifts.

**The precedent is already set.** `ruling_schema.hpp` explicitly moves authored
ruling state into the dogfooded DBF store so the console derives it. The dynamic
reports gateway (AIF-086) is the first derived surface -- it regenerates per request
instead of trusting a stale export. These are two halves of one move.

**The forward path (the dogfood).** Migrate the tracking layer into x64base tables --
SYS* analogues for LANE, RUN, PROOF, TASK (mirroring SYSMEMBER/SYSBOARD/SYSRULING) --
so the AI Project stores its OWN governance in the database it builds, and the
reports become derived views (the gateway already is one). Drift becomes
structurally impossible, because there is no authored copy to drift. This is the
same thesis the engine already applies to identity and boards, turned on the
project's own process.

**The repeatable process this normalizes to:**
`work -> record as a row (lane/run/proof/ruling) in the engine, attributed through
SYSMEMBER + gated by SYSPERM, announced on a SYSBOARD thread -> derive every view
(reports, dashboard, current-work) from those rows.` One lifecycle, one store, one
accountability spine (identity + BBS), zero hand-maintained totals.

## Part 5 -- Open decisions (owner) and next step

- The 64-bit memo ceiling (`C(240)`) blocks the argument/body fields for SYSPOST and
  SYSRULING; four lanes want it. Sequencing this is a prerequisite for a full
  DBF-native tracking layer (or the "table = decision, sheet = argument" split
  becomes the standing rule and prose stays in markdown).
- Which tracking tables to migrate first: LANE + RUN give the biggest anti-drift
  win (they drive the reports). PROOF and TASK follow.
- Governance: this is AIF-086 (AI Systems Integration SDLC) territory and must not
  claim M2 architecture without owner acceptance. This document is M1-level
  discovery + direction only.

Next step on owner direction: pick the first table to dogfood (recommend LANE ->
`SYSLANE`, deriving the active-lane table and closing the AIF-087-not-shown gap at
the root), and open it as a proper lane with a Phase-0 sign-off.
