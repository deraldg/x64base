---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260816-002
  recorded_at_utc: 2026-08-16T20:10:56Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: AI Portal BBS Pseudo-Chat relational schema plan
  project:
    id: project.ai_systems.integration
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 27ad6edc8ad6fb98a282bad4841eda7f8e71df8d
  authorization:
    requested_by: maintainer
    scope: Plan and diagram the relational integration around SYSCHATLNK; no production tables or runtime mutation
  report:
    path: docs/maintenance/AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md
    kind: architecture_plan
primary_topics:
  - ai_portal
  - bbs
  - pseudo_chat
  - relational_schema
  - syschatlnk
  - dottalk_bbsd
  - connector_provenance
---

# AI Portal, BBS, and Pseudo-Chat Relational Schema Plan V1

Status: M2 architecture and M3 design candidate; planning only; no production
table, catalog registration, writer, migration, staging, or publication.

Project: `project.ai_systems.integration`

AIF lane: `AIF-086`

Owner and final authority: `member.derald`

Current steward: `member.ai.claude.cowork`

Contributing agent for this plan: `member.ai.codex.local`

## 1. Decision and boundary

Keep `SYSCHATLNK` as the unique participation edge between one governed
`SYSASSIGN` row and one local conversation. Move data at other grains into
related tables. In particular:

- `SYSCONV` owns the shared local conversation identity;
- `SYSCHATLNK` owns assignment participation and its immutable `LINKKEY`;
- connector definitions distinguish durable carriers from execution adapters;
  runtime sessions then distinguish the interactive `dottalkpp` executable,
  its optional `BBS SERVE` host, the separate `dottalk_bbsd` daemon and its
  loopback connections, provider observers, human relay, and local-model
  transport without treating an executable as an agent;
- language, project/run/lane/task context, and UI history become child rows;
- BBS routing resolves to the existing `SYSTHREAD`; it does not create a second
  BBS thread object;
- message provenance points at `SYSPOST` or a provider message without copying
  the authoritative body into a second store.

This plan does not change the current 35-field
`dottalkpp/data/schemas/syschatlnk_v1.schema.json`. That schema remains the
source-defined compatibility candidate until this normalized model is reviewed.

If the physical family is approved, its recommended residence is
`dottalkpp/data/metadata/portal/`, beside the existing Portal tracking tables.
Identity and BBS remain external owning catalogs. No table or sidecar is created
there by this planning run. The authored plan and diagrams are discoverable
through the existing `portal.agent_assignment_links` registry section; a second
Portal section is neither needed nor allowed by this design.

The unique local join spine is:

```text
project/task/run key -> SYSCHCTX -> SYSCONV.CONVKEY
SYSCONV.ID -> SYSCHATLNK.LINKKEY -> SYSASSIGN.ID -> SYSMEMBER.MKEY
SYSCHATLNK.ID -> SYSCHPART -> SYSCHROUTE.ROUTEKEY -> carrier subtype
SYSCHPART.ID -> SYSCHATUI latest observation
SYSPOSTLNK.MSGKEY -> optional origin participant + route + actor + principal + writer session + BBS/provider message
```

An AIF number, title, provider ID, BBS subject, sidebar position, model name, or
executable name is never substituted for one of those local keys.

## 2. Scope calibration

```text
id: AIPR-20260816-002
title: AI Portal, BBS, and Pseudo-Chat relational schema plan
area: AI Systems Integration / LabTalk AI Portal
owning_lifecycle: AI Systems Integration SDLC
sdlc_lane: design
operating_mode: maintenance
change_class: C3
build_target: documentation_only
product_profile: not_applicable
index_profile: inherited
scope_reason: normalize the approved SYSCHATLNK relationship before any production persistence decision
truth_state: source_defined_design_candidate
proof_state: source_review_only_no_runtime
risk_class: documentation_only_cross_system_architecture
source_path: docs/maintenance/AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md
website_path: not_applicable_downstream_review_only
next_gate: owner and steward review of grains, keys, route types, locking, migration, and rollback
owner: member.derald
status: M2_candidate_no_M2_exit_claim
```

Planning subset:

```text
affected_authorities: AI Systems Integration SDLC; DotTalk++ identity and BBS contracts; LabTalk portal registries
minimum_gate_set: prior-art map; source-of-record matrix; ERD/DFD/PFD; ASCII/style; YAML/path audit
optional_educational_gates: later LabTalk worked case after runtime proof
deferred_gates_and_residual_risk: physical schemas, catalog, indexes, writer, WAL/recovery, migration, runtime proof, site publication
```

## 3. Current-state findings

The v1 `SYSCHATLNK` row mixes these independent grains:

| Grain | Current fields | Problem when kept on one row |
| --- | --- | --- |
| Assignment participation | `LINKKEY`, `ASSIGNID`, `MEMBERID`, `MKEY`, `WORKID`, `STATUS`, `VFROM`, `VTHRU`, `ROWVER` | Member and work duplicate facts already owned by `SYSASSIGN` and `SYSMEMBER`; row lifecycle belongs to the participation grain. |
| Shared conversation | `CONVKEY` | The shared key repeats once per participating assignment, but v1 carries no independent conversation-master lifecycle. |
| Provider route | `PROVIDER`, `PRODUCT`, `MODEL`, `SRCPROJ`, `SRCCHAT`, `SRCTHREAD`, provider `PARENTID`, `CREATEDAT`, `MODAT` | One conversation may use several providers or transports, each with its own source chronology. |
| Portal context | `PROJKEY`, `RUNID` | Conversations can span projects and runs; a run can span conversations. |
| BBS route | `BBSBOARD`, `BBSTHRID` | Board duplicates `SYSTHREAD.BOARDID`; one conversation may have several BBS routes. |
| Language | `LOCALE`, `CODELANG` | One scalar natural language and one scalar code language do not model multilingual work. |
| Security envelope | `SENSCLASS` | One row classification cannot be copied directly into a shared conversation without a fail-closed grouping rule. |
| UI observation | `TITLE`, `CWD`, `UISECT`, `UIPOS`, `PINPOS`, `PINNED`, `ARCHIVED`, `OBSAT` | Mutable per-participant UI state overwrites history and is not conversation identity. |

The current BBS relation is already normalized at its own boundary:

```text
SYSBOARD 1 -> N SYSTHREAD 1 -> N SYSPOST
```

`SYSTHREAD` remains the BBS thread authority. `SYSCONV` is a cross-transport
identity that can route to that thread, a provider chat, a document relay, or a
future live exchange.

## 4. Terms that must remain separate

| Term | Meaning | Persistence rule |
| --- | --- | --- |
| AI-BBS | Durable boards, threads, and posts in `SYSBOARD`, `SYSTHREAD`, and `SYSPOST`. | Existing BBS store remains authoritative. |
| `dottalkpp` BBS | Interactive CLI commands; it can also host `BBS SERVE`. | Separate process lifecycle from the daemon. |
| `dottalk_bbsd` | Standalone, long-lived executable using the same BBS service and data roots. | Record as a connector/writer, never as a member. |
| socket `CHAT` verb | Transient agent-to-Ollama bridge handled by `serve()`, hosted either by `dottalkpp BBS SERVE` or `dottalk_bbsd`. It is not an interactive `BBS CHAT` command. | Not durable today; only an explicit promotion creates a durable post/provenance row. |
| Website Pseudo-Chat | Human-relayed asynchronous return log on Agent Sync. | Document route; not real-time and not a system of record. |
| Future live PSEUDO | Proposed addressed, turn-based participant exchange. | Remains planned until implemented and runtime-proven. |
| Provider chat | Codex, ChatGPT, Copilot, Claude, or another provider-native conversation. | Route into the local conversation identity; provider IDs are not local identity. |

The name `Pseudo-Chat` remains an umbrella pattern. Every stored route names the
actual carrier.

## 5. Recommended relational model

All physical names below are at most ten characters. Stable opaque keys cross
process and export boundaries. Numeric IDs are local primary and foreign keys
inside the X64 store.

Timestamp rule: mutable identity, definition, relationship, and route/subtype
rows carry local `CREATEDAT` and `MODAT` as UTC epoch values. Runtime sessions
and transaction state machines use `STARTAT`/`ENDAT`, `APPLYAT`/`VERIFYAT`, or
`COMMITAT` plus `ROWVER`. Immutable observations carry `OBSAT`. Message content
and provenance carry `WRITTENAT` and remain immutable; only explicit lifecycle
state may advance `MODAT`/`ROWVER`. Provider chronology uses
`SRCCREAT` and `SRCMODAT` on the provider route so it cannot be confused with
local row audit time. `VFROM` and `VTHRU` describe business validity; they do
not replace audit timestamps.

### 5.1 Core tables

| Table | Row grain | Required key and relation |
| --- | --- | --- |
| `SYSCONV` | one local cross-transport conversation | `CONVKEY` unique; optional self-parent for a governed fork |
| `SYSCHATLNK` | one `SYSASSIGN` participating in one conversation | `LINKKEY` unique; `(ASSIGNID, CONVID)` unique |
| `SYSCHCONN` | one carrier, adapter, or writer definition | `CONNKEY` unique; `CONNROLE` prevents a process-specific writer from becoming a durable route identity |
| `SYSCHSESS` | one connector process, connection, observation, or relay session | `SESSKEY` unique; optional self-parent distinguishes a daemon process from its accepted connections |
| `SYSCHROUTE` | one durable carrier route for one conversation | `ROUTEKEY` unique; references `SYSCONV` and a carrier-role `SYSCHCONN` row |
| `SYSCHRPRV` | provider-native details for one provider route | `ROUTEID` primary/foreign key |
| `SYSCHRBBS` | BBS details for one BBS route | `ROUTEID` primary/foreign key; `THREADID -> SYSTHREAD.ID` |
| `SYSCHRDOC` | document-relay details for one asynchronous route | `ROUTEID` primary/foreign key; document/page identity and relay policy only |
| `SYSCHPART` | one assignment link using one route | `(LINKID, ROUTEID)` unique; model and route role are observations |
| `SYSCHLANG` | one language tag in a conversation or participant scope | multilingual natural/code tags with priority and validity |
| `SYSCHATUI` | one append-only UI snapshot for one participant-route | ordered by `(PARTID, OBSAT, ID)` |
| `SYSCHCTX` | one typed Portal context edge | project, lane, run, task, proof, or artifact key plus relation role |
| `SYSPOSTLNK` | one durable message/provenance envelope | maps BBS/provider message identity, origin link, acting member, principal, writer connector, and exact parent |
| `SYSCHTXN` | one multi-table write intent and result | `TXNKEY` unique; enables idempotent recovery across DBF files |
| `SYSCHTXITM` | one intended transaction step | complete ordered manifest of target keys, assertions, writes, and verification state |

### 5.2 `SYSCONV` candidate fields

| Field | Type | Meaning |
| --- | --- | --- |
| `ID` | N(20) | Local primary key. |
| `CONVKEY` | C(128) | Immutable portable conversation key. |
| `PARENTID` | N(20) | Optional parent `SYSCONV.ID` for a governed fork. |
| `KIND` | C(24) | Carrier-neutral purpose such as `work`, `review`, `support`, `handoff`, or `general`. |
| `STATUS` | N(2) | Active, closed, or invalidated. |
| `SENSCLASS` | C(24) | Fail-closed sensitivity class. |
| `CREATEDAT` | N(20) | Local conversation creation epoch. |
| `MODAT` | N(20) | Last semantic conversation change epoch. |
| `VFROM`, `VTHRU`, `ROWVER` | N(20) | Validity and optimistic row version. |

Indexes: unique `CONVKEY`; non-unique `(PARENTID, CREATEDAT, ID)`; current-state
lookup `(STATUS, MODAT, ID)`.

`SYSCONV.PARENTID` is a resolved local fork relation. It is not copied directly
from the v1 provider-native character `PARENTID`; unresolved provider ancestry
remains `SYSCHRPRV.PARENTREF`.

### 5.3 `SYSCHATLNK` v2 candidate fields

| Field | Type | Meaning |
| --- | --- | --- |
| `ID` | N(20) | Local primary key. |
| `LINKKEY` | C(128) | Immutable portable participation key. |
| `CONVID` | N(20) | `SYSCONV.ID`. |
| `ASSIGNID` | N(20) | `SYSASSIGN.ID`. |
| `STATUS` | N(2) | Active, closed, or invalidated. |
| `CREATEDAT`, `MODAT` | N(20) | Creation and last semantic modification epoch. |
| `VFROM`, `VTHRU`, `ROWVER` | N(20) | Validity and optimistic row version. |

`MEMBERID`, `MKEY`, and `WORKID` are resolved through
`SYSCHATLNK.ASSIGNID -> SYSASSIGN -> SYSMEMBER`. They are compatibility-view
columns, not repeated base facts. The writer must reject an assignment/member
disagreement before persistence.

Indexes: unique `LINKKEY`; unique `(ASSIGNID, CONVID)`; non-unique `CONVID`.

### 5.4 Connector, runtime-session, route, and participant tables

`SYSCHCONN` distinguishes carrier from actor:

| Field | Type | Meaning |
| --- | --- | --- |
| `ID` | N(20) | Primary key. |
| `CONNKEY` | C(96) | Stable key such as `conn.dottalk_bbsd.loopback`. |
| `CONNROLE` | C(16) | `carrier`, `writer`, `adapter`, `carrier_adapter`, or `adapter_writer`; roles are validated, not inferred. |
| `KIND` | C(24) | `interactive_cli`, `daemon`, `provider_ui`, `human_relay`, `local_model`. |
| `LABEL` | C(64) | Operator-facing adapter/connector label; descriptive, not identity. |
| `EXECNAME` | C(48) | `dottalkpp`, `dottalk_bbsd`, or blank for non-executable carriers. |
| `TRANSPORT` | C(24) | `in_process`, `loopback_socket`, `provider_ui`, `document_relay`. |
| `HOSTSCOPE` | C(24) | Local, hosted, browser, or reviewed extension. |
| `STATUS` | N(2) | Lifecycle state. |
| `CREATEDAT`, `MODAT` | N(20) | Definition creation and last semantic modification epoch. |
| `VFROM`, `VTHRU`, `ROWVER` | N(20) | Validity and optimistic row version. |

Initial connector examples are definitions, not process-instance claims:

- `conn.bbs.local` (`carrier` shared by every BBS writer/reader)
- `conn.dottalkpp.cli` (`writer`)
- `conn.dottalkpp.bbs_serve` (`adapter_writer` hosting the socket server)
- `conn.dottalk_bbsd.loopback` (`adapter_writer` hosting the socket server)
- `conn.codex.desktop` and `conn.chatgpt.web` (`carrier_adapter`)
- `conn.document.relay` (`carrier` for the asynchronous document/page route)
- `conn.human.relay` (`adapter_writer`)
- `conn.ollama.loopback` (`carrier`; transient until an explicit promotion)

`SYSCHSESS` records the runtime boundary that used a connector definition:
`ID`, `SESSKEY`, `CONNID`, optional self-parent `PARENTID`, `SESSKIND`, optional
`PRINCIPAL`, `PID`, `HOSTREF`, `RUNKEY`, `STARTAT`, `ENDAT`, `ENDREAS`,
`STATUS`, and `ROWVER`. Session close/status changes advance `ENDAT`, record a
typed end reason, and advance `ROWVER`; sessions are not general mutable
definition rows. `HOSTREF` is an opaque reviewed host key, not a raw credential
or private path.

- a `dottalk_bbsd` process has one `process_instance` row;
- each successfully authenticated accepted loopback connection has a child
  `connection` row whose `PRINCIPAL` is established by `connection_auth`;
- an interactive `dottalkpp` invocation has its own process/session row;
- `dottalkpp BBS SERVE` uses a distinct host-session definition from direct CLI
  commands;
- provider observation and human relay work use bounded observation/relay
  session rows.

This makes executable class, process lifetime, authenticated connection, and
governed member four different facts. A daemon process row never inherits an
authenticated principal merely because startup selected an operator; the
accepted connection carries that fact. A session never becomes the author.

`SYSCHROUTE` holds only route-common state: `ID`, `ROUTEKEY`, `CONVID`,
`CARRID`, `ROUTEKIND`, `STATUS`, `CREATEDAT`, `MODAT`, `VFROM`, `VTHRU`, and
`ROWVER`. Route-specific attributes live in one of these one-to-one subtype
tables:

- `SYSCHRPRV`: `ROUTEID`, `PROVIDER`, `PRODUCT`, `SRCPROJ`, `SRCCHAT`,
  `SRCTHREAD`, `PARENTREF`, `SRCCREAT`, `SRCMODAT`, `OBSAT`, `CREATEDAT`,
  `MODAT`, `VFROM`, `VTHRU`, `ROWVER`;
- `SYSCHRBBS`: `ROUTEID`, `THREADID`, `ROUTEROLE`; derive the board through
  `SYSTHREAD.BOARDID`; also carry local audit/validity/version fields;
- `SYSCHRDOC`: `ROUTEID`, `DOCREF`, `PAGEREF`, `RELAYPOL`, plus local
  audit/validity/version fields.

`CARRID` names the durable carrier, not the writer process. A BBS route always
uses `conn.bbs.local`; both `dottalkpp` and `dottalk_bbsd` may service it, and
the actual recorder remains message-specific through `WRITESESS`. Durable
`ROUTEKIND` values in v1 of this plan are `provider`, `bbs`, and `document`,
with exactly the corresponding subtype. A promoted Ollama exchange may use the
provider subtype with reviewed local-provider semantics. Transient socket
`CHAT` and future live PSEUDO create no durable route merely by occurring; an
explicit observation or promotion chooses a supported durable carrier.

Document question and reply identifiers are message-grain `SRCMSGID` and
`PARENTID` values in `SYSPOSTLNK`, never columns on the route row.

`SYSCHPART` joins a participant link to a route and carries `PARTROLE`, state,
`CREATEDAT`, `MODAT`, and validity. This supports many agents
on one provider or BBS route, and one assignment participating through several
routes. Provider/model selection is observation history, not mutable
participant-route identity.

### 5.5 Language, Portal context, and UI history

`SYSCHLANG` fields: `ID`, `CONVID`, optional `LINKID`, `LANGKIND`, `LANGTAG`,
`PRIORITY`, `CREATEDAT`, `MODAT`, `VFROM`, `VTHRU`, and `ROWVER`.

- `LANGKIND=0` is a BCP 47 natural-language tag.
- `LANGKIND=1` is an implementation-language tag such as `cpp`, `python`,
  `sql`, or `dotscript`; mixed-language work is several rows.
- a zero `LINKID` applies to the conversation; a populated `LINKID` is an
  assignment-participant override independent of carrier route.

`SYSCHCTX` fields: `ID`, `CONVID`, optional `LINKID`, `CTXKIND`, `CTXKEY`,
`RELKIND`, `PRIMARY`, `CREATEDAT`, `MODAT`, `VFROM`, `VTHRU`, and `ROWVER`.

`CTXKEY` is `C(128)` in this candidate. The current v1 `RUNID C(64)` and
`PROJKEY C(96)` do not match all Portal tracking key widths (`C(48)` in several
places). Physical design must either widen the owning keys or reject an
oversized reference before the write; it must never truncate a key and claim a
valid relation. Message/session `RUNKEY` remains `C(64)` during this transition.

Allowed initial context kinds and validators:

| `CTXKIND` | Validation target |
| --- | --- |
| `project` | `projects.yaml:projects[].id` until a reviewed project table becomes authoritative |
| `lane` | `SYSLANE.LKEY` or the authoritative AIF queue/claim during transition |
| `run` | `SYSRUN.RKEY` or `runs.d/*.yaml:run_id` during transition |
| `task` | `SYSTASK.TKEY` or the task registry during transition |
| `proof` | `SYSPROOF.PKEY` or `proofs.d/*.yaml:id` during transition |
| `artifact` | tracked path plus owning-record validation |

These are typed soft edges while their owning records remain split between DBF
and authored registries. `SYSCHCTX` never becomes authority for the referenced
object.

`SYSCHATUI` fields: `ID`, `PARTID`, `MODEL`, `TITLE`, `CWD`, `UISECT`, `UIPOS`,
`PINPOS`, `PINNED`, `ARCHIVED`, `OBSAT`, `OBSSESS`, optional `OBSPRINC`, and
`SNAPHASH`. `OBSSESS -> SYSCHSESS` identifies the capture adapter/session;
`OBSPRINC -> SYSMEMBER` identifies an observing principal only when one exists.
Snapshots are append-only. The Portal selects the highest `(OBSAT, ID)` per
participant. A title or position is never a key and never supplies chronology.

### 5.6 Message and writer provenance

`SYSPOSTLNK` is an envelope and crosswalk, not a second message-body store:

| Field | Meaning |
| --- | --- |
| `ID`, `MSGKEY` | Local row and portable message identity. |
| `CONVID`, optional `ORIGPART`, `ORIGKIND`, `ROUTEID` | Conversation, content-origin classification/participant, and carrier. `ORIGKIND` supports participant, system, external-unassigned, and legacy-unattributed history. |
| `TXNID` | `SYSCHTXN.ID` for the durable operation that committed the envelope. |
| `POSTID` | Optional `SYSPOST.ID` for a promoted durable BBS post. |
| `SRCMSGID` | Optional provider-native message ID. |
| `PARENTID` | Exact parent `SYSPOSTLNK.ID`; fixes the current lost reply-parent relation. |
| `ACTORID` | Acting `SYSMEMBER.ID` used for the domain write. |
| `PRINCIPAL` | Authenticated or transcribing `SYSMEMBER.ID`. |
| `WRITESESS` | `SYSCHSESS.ID`; the connector follows through `SYSCHSESS.CONNID`. |
| `ORIGRUN` | Optional content-origin run. The writer run follows through `WRITESESS -> SYSCHSESS.RUNKEY`. |
| `KIND`, `WRITTENAT`, `MODAT`, `STATUS`, `SENSCLASS`, `ROWVER` | Message classification, immutable write time, later lifecycle-change time, lifecycle, sensitivity, and optimistic version. |
| `PAYLOADREF`, `PAYHASH` | Pointer and digest for the authoritative payload carrier. |

`SYSPOST.AUTHORID` is strictly the acting member used by the current BBS write
and must equal `SYSPOSTLNK.ACTORID` for an attached/promoted post. It is never
inferred to be the content origin. `ORIGPART` identifies a governed origin
participant when one exists; it is nullable for system, external, and
legacy-unattributed content history. `ACTORID` and `PRINCIPAL` are mandatory on
every new envelope. Socket operations always require `ACTORID = PRINCIPAL`
because the socket protocol exposes no act-as verb. Direct CLI operations also
use equality unless a nonblank `DELEGREF` validates the current owner `USER AS`
or another approved delegation. Human relay may make `ORIGPART` differ, but
does not by itself make actor and principal differ. `WRITESESS` answers which
process or connection recorded the row; its parent connector answers whether
it was `dottalkpp`, `dottalk_bbsd`, a relay importer, or another approved
adapter.

Indexes: unique `MSGKEY`; unique nonzero `POSTID`; unique nonblank
`(ROUTEID, SRCMSGID)`; non-unique `(CONVID, WRITTENAT, ID)`, `PARENTID`,
`ACTORID`, `PRINCIPAL`, `WRITESESS`, and `ORIGRUN`. These constraints supply
idempotent provider ingestion and unambiguous BBS promotion.

`SYSCHTXN` fields are `ID`, `TXNKEY`, `INITSESS`, `PRINCIPAL`, `ACTORID`,
`DELEGREF`, `OPKIND`, `TARGETKEY`, `STATE`, `STARTAT`, `COMMITAT`, `LASTERR`,
and `ROWVER`. `TXNKEY` is the globally unique caller/retry idempotency key.
`(OPKIND, TARGETKEY)` is a non-unique business lookup and never substitutes for
`TXNKEY`.

`INITSESS` identifies the transaction initiator. For a normal domain
transaction it is the authenticated writer session. A typed
`process_bootstrap` transaction may use zero `INITSESS`, `PRINCIPAL`, and
`ACTORID`, but its manifest may target only `SYSCHCONN` and `SYSCHSESS` process
lifecycle rows. A typed `connection_auth` transaction uses the existing parent
process session as `INITSESS`, records the authenticated member as both
`PRINCIPAL` and `ACTORID`, and names the reserved child connection session in
its manifest. Commit requires the new child session's `PRINCIPAL` to equal the
transaction principal.

A typed `connection_close` transaction uses the authenticated child as
`INITSESS`, requires its principal/actor, and advances that child's `ENDAT`,
`ENDREAS`, `STATUS`, and `ROWVER` after `QUIT`, empty input, EOF/error, idle
timeout, or owner shutdown. A typed `process_stop` transaction uses the
principal-less process session as `INITSESS`, permits zero principal/actor, and
closes only that process row after all known children have closed. On restart,
a bounded `process_recovery` transaction uses the new process session as
initiator, permits zero principal/actor, and closes stale child/process rows
only after locked host/process-liveness and parent checks. These lifecycle
exceptions use the same global journal/allocation lock and connector/session
owning locks as every other transaction.

The socket state machine has two states. In `PREAUTH`, the first frame must be
`AUTH`; a failed `AUTH` or any other first frame closes the connection. Only
after the `connection_auth` transaction commits does the connection enter
`AUTHENTICATED`, where `CHAT`, `BBS READ`, `BBS POST`, `QUIT`, and owner-gated
`SHUTDOWN` are recognized. A repeated `AUTH`, another nonempty unknown command,
or a denied non-owner `SHUTDOWN` returns `ERR` and remains in the authenticated
loop. `QUIT`, empty input, EOF/error, and idle timeout close the connection;
successful owner `SHUTDOWN` also stops the hosting server/process. Every
post-auth command resolves that committed child session; no daemon startup
operator supplies pre-auth authority.

`SYSCHTXITM` supplies the recovery manifest: `ID`, `TXNID`, `SEQ`,
`TABLENAME`, `ROWID`, `ROWKEY`, `OPKIND`, `EXPECTVER`, `STATE`, `APPLYAT`,
`VERIFYAT`, `PAYLOADREF`, `PAYHASH`, `SENSCLASS`, `LASTERR`, and `ROWVER`.
It is unique on `(TXNID, SEQ)` and
`(TXNID, TABLENAME, ROWID, OPKIND)` for a numeric mutation with nonzero
`ROWID`, and `(TXNID, TABLENAME, ROWKEY, OPKIND)` for a soft assertion with
zero `ROWID`. `ROWKEY` is the canonical stable or composite business key used
for read-back; `ROWID` is the numeric row ID reserved under the owning table
lock. Assertion items record source
dependencies such as the expected `SYSASSIGN.ROWVER`; mutation items record
every intended row, allocation, and governed replay-payload reference before
the first domain write. Recovery can therefore forward-complete or append an
invalidation without guessing which tables or numeric BBS rows were reached.

Message bodies remain in their authoritative carrier. The BBS `BODY C(240)`
limit and a future long-body/memo design are separate gates; this plan does not
invent a second body store.

### 5.7 Cross-row invariants

The physical writer and audit must enforce constraints that a DBF file cannot
express by itself:

1. Every numeric `ID` is unique and allocated inside the owning allocation
   lock; transaction and manifest IDs are allocated inside the journal lock.
2. `SYSCHPART.LINKID` and `SYSCHPART.ROUTEID` resolve to the same `CONVID`.
3. Optional `SYSCHLANG.LINKID` and `SYSCHCTX.LINKID` resolve to their row's
   `CONVID`.
4. Optional `SYSPOSTLNK.ORIGPART`, `ROUTEID`, and `CONVID` agree when the
   origin is governed; `WRITESESS` identifies the recorder, not the origin.
   `ACTORID` is the acting member for that operation, and an attached BBS row
   must satisfy `SYSPOST.AUTHORID = SYSPOSTLNK.ACTORID`.
5. `SYSCHROUTE.CARRID` resolves a carrier-role connector. A route has only the
   subtype allowed by `ROUTEKIND`; provider, BBS, and document subtype rows are
   mutually exclusive.
6. `SYSCHRBBS.THREADID` resolves the board through `SYSTHREAD.BOARDID`. One
   active BBS thread cannot route to two local conversations.
7. A child `SYSCHSESS` uses the same connector definition as its parent and a
   daemon connection names a daemon process session as parent. Only the
   authenticated connection, not the daemon process, carries its principal.
8. Provider-native uniqueness is enforced by the nonblank source-message and
   route keys; opaque source IDs are never recast as local numeric IDs.
9. Typed Portal context must resolve through the owning registry/table and must
   fail closed on truncation, ambiguity, or a ticket used where a task key is
   required.
10. Source chronology, local audit time, event observation time, and validity
    time remain distinct and are monotonic within their own domains.
11. One active `SYSCHLANG` row exists per
    `(CONVID, LINKID, LANGKIND, LANGTAG)`; `PRIORITY=0` is the sole primary for
    one `(CONVID, LINKID, LANGKIND)` scope. One active `SYSCHCTX` row exists per
    `(CONVID, LINKID, CTXKIND, CTXKEY, RELKIND)`, with at most one `PRIMARY`
    row per scope/kind/relation.
12. Every normal domain transaction must satisfy
    `SYSCHTXN.PRINCIPAL = SYSCHSESS.PRINCIPAL` through
    `SYSCHTXN.INITSESS`. A transaction that creates `SYSPOSTLNK` must also
    satisfy `SYSCHTXN.INITSESS = SYSPOSTLNK.WRITESESS` and
    `SYSCHTXN.ACTORID = SYSPOSTLNK.ACTORID`. `ACTORID = PRINCIPAL` unless
    `DELEGREF` resolves current owner-sudo/delegation authority; current socket
    transactions always use equality.
13. Lifecycle exceptions are closed and typed: `process_bootstrap` is the only
    zero-initiator transaction; `connection_auth` is parent-initiated and
    reserves the child; `connection_close` is child-initiated; `process_stop`
    is principal-less and process-initiated; `process_recovery` is initiated by
    the new process and requires locked stale-process evidence. Their manifests
    may mutate only the declared connector/session lifecycle rows, and each
    committed child preserves principal equality from authentication through
    close.
14. After domain IDs are reserved under their owning locks, the complete
    `SYSCHTXITM` manifest is durable and read back before the first domain
    mutation. `SYSASSIGN.ROWVER`, active status, member, work, grants, and typed
    context are revalidated under the agreed locks immediately before mutation
    and again before commit when the owning store cannot hold a shared lock.

### 5.8 Physical index obligations

The M3 schema must materialize and reopen the physical CDX orders below; listing
them here is not runtime proof:

| Table | Required uniqueness and lookup order |
| --- | --- |
| `SYSCHCONN` | unique `CONNKEY`; `(CONNROLE, STATUS, ID)` |
| `SYSCHSESS` | unique `SESSKEY`; `PARENTID`; `(CONNID, STARTAT, ID)` |
| `SYSCHROUTE` | unique `ROUTEKEY`; `(CONVID, ROUTEKIND, STATUS, ID)`; `CARRID` |
| `SYSCHRPRV` | source tuple lookup by provider/product/project/chat/thread; active uniqueness enforced with the parent route carrier |
| `SYSCHRBBS` | `THREADID`; at most one active conversation route per thread |
| `SYSCHRDOC` | `(DOCREF, PAGEREF, ROUTEID)` |
| `SYSCHPART` | unique `(LINKID, ROUTEID)`; lookup `ROUTEID` |
| `SYSCHLANG` | active unique `(CONVID, LINKID, LANGKIND, LANGTAG)`; primary/priority scope lookup |
| `SYSCHATUI` | `(PARTID, OBSAT, ID)`; `OBSSESS` |
| `SYSCHCTX` | active unique `(CONVID, LINKID, CTXKIND, CTXKEY, RELKIND)`; primary scope lookup |
| `SYSPOSTLNK` | unique `MSGKEY`, nonzero `POSTID`, and nonblank `(ROUTEID, SRCMSGID)`; conversation/time, parent, actor, principal, writer session, origin run |
| `SYSCHTXN` | globally unique `TXNKEY`; non-unique `(OPKIND, TARGETKEY)`, `DELEGREF`, and `(STATE, STARTAT, ID)` |
| `SYSCHTXITM` | unique `(TXNID, SEQ)`; conditional unique numeric mutation `(TXNID, TABLENAME, ROWID, OPKIND)` or soft assertion `(TXNID, TABLENAME, ROWKEY, OPKIND)`; `(STATE, APPLYAT, ID)` |

Filtered/active uniqueness that cannot be expressed safely in one CDX key is a
writer plus audit invariant. No report-layer de-duplication may hide a physical
duplicate.

## 6. Source-of-record matrix

| Fact | Owning record | Relational role |
| --- | --- | --- |
| Human/AI/service identity | `SYSMEMBER` | referenced, never copied as connector identity |
| Governed role/work participation | `SYSASSIGN` | parent of `SYSCHATLNK` |
| Cross-transport conversation | `SYSCONV` | new local master candidate |
| Assignment participation | `SYSCHATLNK` | new link remains the unique participant edge |
| Connector definition and runtime session | `SYSCHCONN` / `SYSCHSESS` | carrier and process provenance; never agent identity |
| BBS room/thread/post | `SYSBOARD` / `SYSTHREAD` / `SYSPOST` | referenced by route/provenance tables |
| Provider chat identity | provider route subtype | locally observed external identity |
| Project/lane/run/task/proof | their existing owner | typed `SYSCHCTX` pointer only |
| UI name and position | `SYSCHATUI` snapshot | observation, never authority |
| Public website page | `D:/dev/x64base-site` after review | downstream projection only; never writes the store |

## 7. Compatibility map from the 35-field candidate

| Current v1 field group | Normalized destination |
| --- | --- |
| `LINKKEY`, `ASSIGNID`, `STATUS`, `VFROM`, `VTHRU`, `ROWVER` | `SYSCHATLNK` |
| `CONVKEY` | `SYSCONV`; initialize conversation status from an explicit versioned migration default or separate evidence, never from participant status |
| `MEMBERID`, `MKEY`, `WORKID` | derived through `SYSASSIGN` and `SYSMEMBER` |
| `PROVIDER`, `PRODUCT`, `SRCPROJ`, `SRCCHAT`, `SRCTHREAD`, provider `PARENTID`, `CREATEDAT`, `MODAT` | `SYSCHRPRV`, using `PARENTREF`, `SRCCREAT`, and `SRCMODAT` for the renamed fields; these timestamps retain the v1 contract's provider chronology |
| `MODEL` | latest applicable append-only `SYSCHATUI` observation |
| `PROJKEY`, `RUNID` | typed `SYSCHCTX` rows |
| `BBSBOARD`, `BBSTHRID` | `SYSCHRBBS`; board is derived from thread |
| `LOCALE`, `CODELANG` | one or more `SYSCHLANG` rows |
| title, CWD, section, position, pin/archive, `OBSAT` | append-only `SYSCHATUI`; provider-route `OBSAT` may mirror the same capture event |

A compatibility reader can reconstruct the v1 shape from the normalized
tables. It must declare how it chooses one primary project, run, BBS route,
language, provider route, and latest UI snapshot when more than one exists.

### 7.1 Deterministic v1 migration rules

The migration proof must be repeatable, idempotent, and fail closed:

1. Validate every source row before grouping. Blank or duplicate `LINKKEY`, a
   blank `CONVKEY`, an unresolved assignment, or assignment/member disagreement
   goes to a quarantine report and creates no normalized row.
2. Group valid source rows by exact `CONVKEY` and create exactly one `SYSCONV`
   per group. Preserve each source row's participation `STATUS`, `VFROM`,
   `VTHRU`, and `ROWVER` on its own `SYSCHATLNK`; do not promote those values
   to conversation master data.
3. Initialize `SYSCONV.STATUS` only from an explicit versioned migration
   default or separately evidenced conversation rule; v1 participation status
   is not conversation-master status. Initialize sensitivity only when every
   nonblank source value in the group agrees under the approved mapping.
   Conflicting sensitivity values quarantine the complete group; a missing
   value uses an explicit migration default recorded in the run, never a guess
   from UI text.
4. Deduplicate provider routes within one conversation only when `PROVIDER` and
   `PRODUCT` are nonblank and at least one of `SRCCHAT` or `SRCTHREAD` is
   nonblank, using the exact
   `(PROVIDER, PRODUCT, SRCPROJ, SRCCHAT, SRCTHREAD)` tuple. Within one such
   group, the nonblank `PARENTID`, `CREATEDAT`, and `MODAT` values must each
   collapse to one exact value; fill blanks from that agreed value, but
   quarantine the complete route group on any conflict. UI observations remain
   participant-specific and may differ.
5. When provider identity is incomplete but the row declares a provider,
   product, source ID, or provider UI observation, preserve one
   non-deduplicated observation route keyed from `LINKKEY`; never merge blank
   tuples. If UI fields exist with no declared carrier at all, quarantine the
   row rather than inventing one. Deduplicate BBS routes separately by validated
   `BBSTHRID`; `BBSBOARD` must agree with the owning `SYSTHREAD.BOARDID` or the
   row is quarantined. Provider and BBS remain distinct carriers even when one
   source row mentions both.
6. Create one `SYSCHPART` for each evidenced source link/route pair. Attach the
   source row's UI snapshot to that exact participant-route. If several routes
   are possible and the source cannot identify which one was observed, retain
   the source row in quarantine rather than choosing by title, position, or
   list order.
7. Expand locale and implementation-language values into deterministic
   `SYSCHLANG` rows and project/run values into typed `SYSCHCTX` rows. Reject
   truncation, malformed tags, and ambiguous authority matches.
8. Preserve source `CREATEDAT` and `MODAT` as provider `SRCCREAT` and
   `SRCMODAT`, as required by the v1 contract. Independently stamp each
   normalized row with the migration run's local creation/modification audit
   time; never substitute migration time for provider chronology.
9. Derive migration `TXNKEY`, stable keys, and source-row hashes from a
   versioned migration recipe. Rerunning the same recipe must read back the
   existing rows; any different payload for the same key is a hard conflict.

## 8. Writer, locking, and recovery design

`dottalkpp` and `dottalk_bbsd` are separate processes. Both may reach the same
BBS store. A shared table lock prevents header/record corruption, but a
multi-table normalized write also needs unique allocation and recovery.

Required writer contract:

1. Classify the host and operation first. A socket connection enforces the
   two-state rule above: its first frame is `AUTH` or the connection closes;
   only the committed authenticated state reaches command dispatch.
   Interactive `dottalkpp` supports its
   CLI `BOARDS`, `READ`, `POST`, `REPLY`, and `CLOSE` paths. The current socket
   grammar is `AUTH`, `CHAT`, `BBS READ`, `BBS POST`, `QUIT`, and owner-only
   `SHUTDOWN`; socket `BOARDS` and `REPLY` are not current protocol claims.
2. A socket connection must persist its authenticated child `SYSCHSESS`
   through a separately typed transaction using the one global journal lock.
   Every post-auth command resolves that child session before dispatch; all
   commands fail closed if the session write or read-back fails. `chat.invoke`,
   `bbs.read`, and the selected board's post permission are independent checks.
   Permission denial returns `ERR` and retains the authenticated command loop;
   it does not close a healthy connection.
   Normal and abnormal connection ends use `connection_close`; controlled
   process exit uses `process_stop`; startup repairs stale sessions through
   evidence-bound `process_recovery`.
3. Read-only queries and transient socket `CHAT` bypass the conversation
   mutation planner. `AUTH` never mints conversation, participation, or route
   keys. An explicit observation, promotion, BBS post/reply, or authorized close
   enters the shared domain service.
4. Every write adapter calls that one service. No provider, Portal, document
   relay, CLI, or daemon adapter writes DBFs directly. An independent BBS write
   remains valid without an AI assignment or conversation. Attaching or
   promoting it into the cross-transport graph is a separate explicit choice;
   only that branch requires `SYSCONV`, `SYSCHATLNK`, route, participant, and
   `SYSPOSTLNK` rows.
5. Resolve the writer `SYSCHSESS`, authenticated principal, acting member,
   grants, carrier, and stable target keys without mutating domain tables. For
   an attached operation, also resolve the assignment, context, and origin
   participant. Creating a connector/session is itself a separate journaled
   lifecycle operation.
6. Every lifecycle and domain transaction uses the same global
   journal/allocation lock. Under it, idempotently find or create the
   `SYSCHTXN` shell by globally unique `TXNKEY`. Allocate the transaction and
   manifest row IDs, but do not perform a domain mutation.
7. While retaining the journal lock, acquire remaining cooperating locks in one
   order: identity/assignment validation -> connector/session -> conversation
   -> assignment link -> carrier route/subtype/participant -> BBS thread/post
   -> message provenance -> context/language/UI.
8. Under those owning locks, reserve every required numeric domain ID, check all
   unique keys, then durably complete and read back the ordered `SYSCHTXITM`
   manifest with `ROWID`, canonical `ROWKEY`, payload hash/reference, and
   dependency assertions. The locks remain held. Every allocator must account
   for incomplete reservations before choosing an ID; never compute
   `max(ID)+1` outside the owning lock.
9. Revalidate principal, acting member, command/board grants, assignment and
   member agreement when applicable, typed context, target keys, and expected
   row versions. Apply each idempotent manifest item only after this check,
   read it back, and mark it verified.
10. For an attached/promoted message, persist `ACTORID`, `PRINCIPAL`, and
    `WRITESESS` atomically with `SYSPOSTLNK`; require
    `SYSPOST.AUTHORID = ACTORID`, `SYSCHTXN.ACTORID = ACTORID`, and
    `SYSCHTXN.PRINCIPAL = SYSCHSESS.PRINCIPAL`. Never infer writer, actor, or
    principal from `SYSPOST.KIND`, board, or `AUTHKIND`. A BBS-only write has no
    fabricated `SYSPOSTLNK`.
11. Revalidate any source whose owning catalog could not hold a cooperating
    lock, then mark the transaction committed only after all durable rows and
    indexes are readable.
12. Startup recovery obtains the same locks and either forward-completes
    verified manifest steps or appends explicit invalidations. It never deletes
    or rewrites an already durable BBS post to simulate rollback. A safely
    rejected/recovered socket command returns `ERR` to the authenticated loop;
    only a transport/session-fatal result runs `connection_close`.

No cascade delete is allowed. Invalidations append or close versions; BBS and
conversation history remains reviewable.

## 9. Portal read models

The normalized store should support these derived views without hand joins:

| View | Query path |
| --- | --- |
| Conversation roster | project context -> `SYSCONV` -> `SYSCHATLNK` -> `SYSASSIGN` -> `SYSMEMBER` |
| Provider/sidebar view | roster -> `SYSCHPART` -> provider route -> latest `SYSCHATUI` |
| BBS transcript | `SYSCONV` -> BBS route -> `SYSTHREAD` -> `SYSPOST`, ordered by `POSTAT, ID` |
| Cross-route transcript | `SYSCONV` -> `SYSPOSTLNK`, ordered by `WRITTENAT, ID`, resolving payloads by carrier |
| Run lineage | `SYSCONV` -> `SYSCHCTX(run)` -> `SYSRUN` / run fragment |
| Work queue | project/lane/task context -> active conversations and participants |
| Restricted/internal provenance candidate | message -> origin link/member, principal, writer connector, run, and source IDs; access control remains an implementation gate |

Names and positions resolve by owner, not by text equality:

| Display fact | Owning record | Relation into the Portal view |
| --- | --- | --- |
| Project name | project registry/project authority | `SYSCHCTX(project).CTXKEY` |
| Assignment role/work label | `SYSASSIGN` and its work authority | `SYSCHATLNK.ASSIGNID` |
| Provider chat title | latest `SYSCHATUI` snapshot | `SYSCHPART -> SYSCHROUTE -> SYSCHRPRV` |
| BBS thread subject | `SYSTHREAD.SUBJECT` | `SYSCHRBBS.THREADID` |
| Sidebar section, order, pin, archive | latest `SYSCHATUI` snapshot | highest `(OBSAT, ID)` for the participant-route |
| Website label | reviewed website projection | derived from the records above; never joined back by label |

None of these names is unique, and changing one never remints `CONVKEY`,
`LINKKEY`, `ROUTEKEY`, or `SESSKEY`.

The public or educational projection must exclude credentials, private paths,
unreviewed message bodies, and internal provider IDs by default.

## 10. Website AI-section findings

The website is a downstream projection, not the schema authority. At the
2026-08-16 review, `codex/lean-sites-publish` at `529668387` was dirty and six
commits ahead of its upstream, so the review was read-only. Its current AI
sections impose these design requirements and later repair gates:

- AI Portal and Agent Sync need a project -> conversation -> participant ->
  route -> latest UI projection;
- Agent Sync uses Pseudo-Chat for a human-relayed asynchronous document route;
- AI Portal and current-lanes content also use pseudo-chat wording and the
  label `BBS CHAT` for local Ollama inference, while the runtime implements a
  socket `CHAT` verb inside `serve()`;
- the future website projection must label those as distinct route kinds rather
  than presenting one ambiguous persisted chat system;
- existing website AI diagrams predate `SYSCHATLNK` and do not show the
  separate `dottalk_bbsd` executable;
- the generated AI Portal report predates the assignment-link run, while one
  authored page still calls reports localhost-only even though tracked public
  AI report pages exist;
- the Portal and Frontal Memory pages disagree on whether an Ollama-backed
  local model is only a service or already a governed member; the normalized
  design therefore keeps member, connector, runtime session, provider product,
  and model separate;
- `/portal` and `/memory` are unlisted and `noindex`, not access-controlled, so
  future sensitivity rules cannot treat those routes as private storage;
- `content/portal/*.mdx` is locally excluded/untracked while `app/portal/*` is
  tracked, so the current local output is not clean-clone reproducibility proof;
- a ticket or AIF number is not a task identity: current-work data already has
  multiple task rows sharing one AIF, so context binds to a task key and carries
  AIF only as lane context;
- the website's conceptual work node has no persisted backing table, so project
  and task edges remain typed soft references until a carrier and authority are
  approved;
- an older publication note recommends excluding `board.worklog`, while the
  current staging implementation deliberately includes it; a cited superseding
  owner ruling or a new ruling is required before any refreshed projection;
- any later site update must be generated or selectively maintained from an
  approved development design and pass a separate publication review.

No website source is changed by this plan.

## 11. Phased adoption plan

### P0 - Architecture review

- approve row grains, stable keys, table names, connector/session vocabulary,
  route subtypes, and source-of-record matrix;
- decide whether the physical v2 table retains `CONVKEY` beside `CONVID` for
  direct export convenience;
- decide the long-body carrier and whether it waits for the existing memo lane;
- confirm that AIF-086 remains the sole controlling lane.

### P1 - Disposable schema proof

- author X64 schema definitions under the reviewed schema/catalog path;
- create all tables only under configured TMP;
- prove field widths, UTF-8, unique keys, numeric FKs, subtype exclusivity, and
  physical indexes;
- remove every proof table and sidecar after accepted readback.

### P2 - Writer and recovery proof

- implement one adapter-neutral domain writer;
- replace hard-coded empty BBS run/grant context with a typed write request that
  carries acting member, origin participant, principal, route, run, and
  transaction identity without conflating them;
- prove `dottalkpp`, the separate `dottalk_bbsd` process, and multiple daemon
  connection sessions can contend safely;
- prove unauthenticated socket commands and authenticated-but-unauthorized
  `CHAT`, `BBS READ`, and `BBS POST` fail closed, and that a successful `AUTH`
  session is durable before a socket write;
- prove `QUIT`, EOF/error, idle timeout, and owner shutdown close the child
  session with end time/reason, denied shutdown and unknown commands remain in
  the authenticated loop, controlled stop closes the process session, and
  restart recovery closes only evidence-matched stale sessions;
- prove an independent guest/non-project BBS post remains valid without a
  fabricated assignment/conversation, while an explicit attach/promotion adds
  actor, principal, writer-session, route, and origin provenance;
- inject failure after each manifest step and table write and prove
  `SYSCHTXN`/`SYSCHTXITM` forward recovery or append-only invalidation;
- inject failure after BBS ID reservation and after BBS append and prove the
  manifest identifies the exact numeric thread/post row on restart;
- prove duplicate key, stale row version, mismatched assignment/member, and
  unauthorized write denial.

### P3 - Read-model parity

- seed disposable normalized rows from the current v1 proof fixture and selected
  registry/BBS fixtures;
- preserve system and legacy-unattributed BBS history in authoritative
  `SYSPOST` rows without fabricating `SYSPOSTLNK`, actor/principal provenance,
  or a governed assignment. Create an envelope with explicit `ORIGKIND` and
  null `ORIGPART` only when actor, principal, and writer-session evidence is
  independently available;
- compare compatibility output with the v1 shape;
- compare Portal roster, BBS transcript, run lineage, and UI order to source
  fixtures;
- keep authored registries authoritative until parity and owner review pass.

### P4 - Production catalog decision

- approve the recommended `dottalkpp/data/metadata/portal/` residence or record
  an explicit superseding location and authority boundary;
- register backup, restore, index rebuild, sensitivity, and single-writer rules;
- perform a dry-run migration and inverse export;
- activate the catalog only through a separately authorized implementation run.

### P5 - Portal and BBS cutover

- place DBF reads behind a feature flag;
- dual-read and report drift without silently overwriting either source;
- cut over one read model at a time;
- keep BBS, identity, run, and project ownership unchanged.

### P6 - Downstream projection

- revise website terminology and diagrams only after development proof;
- publish no message body, path, access map, or provider ID without explicit
  sensitivity and publication approval;
- validate the live page separately from development and staging success.

## 12. Rollback plan

Before production activation, prove:

1. writer stop and read-only freeze;
2. complete inverse export to the v1 compatibility shape plus typed edge files;
3. row counts and hashes by table and logical conversation;
4. removal of catalog registration without deleting table files;
5. restoration of the prior Portal read source;
6. BBS operation through both `dottalkpp` and `dottalk_bbsd` with no dependency
   on the disabled normalized catalog;
7. replay or explicit invalidation of every incomplete `SYSCHTXN` row.

Rollback never remints `LINKKEY` or `CONVKEY` and never rewrites BBS history.

## 13. Design gates still open

| Gate | Decision required |
| --- | --- |
| G1 | Approve the fifteen-table logical family or reduce it with an explicit normalization tradeoff. |
| G2 | Choose numeric-only internal FKs versus retained natural-key duplicates for export, and reconcile existing project/run/task key-width mismatches without truncation. |
| G3 | Approve route subtype vocabulary and connector definitions. |
| G4 | Choose payload carrier for long provider/pseudo-chat bodies. |
| G5 | Approve transaction journal, lock order, allocation strategy, and recovery semantics. |
| G6 | Reconcile `SYSPOST.AUTHKIND` reporting drift and principal-versus-actor provenance. |
| G7 | Approve production catalog location, writer ownership, backup, and rollback. |
| G8 | Approve downstream website terminology and sensitivity projection after runtime proof. |

M2 does not exit and M3 implementation does not begin merely because this plan
and its diagrams exist.
