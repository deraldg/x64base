# Partner entities and amicus standing -- lane charter v1

status : review-needed. Schema + store + CLI landed and COMPILED (MSVC Release, 2026-09-04),
         and CONFIRMED IN A LINKED BINARY 2026-09-16: the Release objects postdate their
         sources, `dottalkpp.exe` (9,100,800 B) carries `USER ORG` x12, `ORGSCOPE` x3,
         `SYSORG`, `ORGUNIT` and `PARTNER` x2, and `REGRESSION ALL` passed on it -- 31 specs,
         0 failed. COMPILED AND LINKED IS STILL NOT RUN; none of the suite's 19 NOT GRADED
         specs is an identity spec, so that green says nothing about this lane.
         NOT seeded on the live catalog, NO runtime evidence. `USER ORG BACKFILL` is the
         owner-gated step that seeds it; nothing has run it yet.
AIF    : AIF-166, claimed 2026-09-16T16:00:55Z, run AIFGEN-20260916-090054, lane
         'partner-amicus-standing', member.derald, via `.\AIFgen.ps1` -> the one allocator.
         THE EARLIER GUESS IN THIS LINE WAS DEAD: it named AIF-112 from a 2026-08-14
         measurement, and the tree had reached 161 intake rows by the time the claim ran.
         A number measured is not a number claimed -- which is the rule this line now obeys.
owner  : member.derald
scope  : identity catalog (SYSORG), standing vocabulary (SYSASSIGN.AKIND), and the predicates
         that let PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1 check independence mechanically.

---

## 1. The problem in one line

The system has no way to say that two agents belong to different parties, so it cannot check
that a reviewer is independent of the work it reviews.

## 2. What already exists (measured, not assumed)

| Thing | Where | State |
|---|---|---|
| `role.ai_partner` | `identity_bootstrap.cpp:39`, RoleId 6 | **live.** `{source.read, source.propose, database.read, bbs.read, bbs.post, chat.invoke}`. Read + propose, never mutate. |
| `OrgUnit` / `OrgUnitType::Organization` | `identity_entities.hpp:98-110` | **declared, dead.** No store vector, no table in `all_tables()`, no CLI surface, never instantiated. |
| `SYSMEMROLE.ORGSCOPE`, `SYSOVERRIDE.ORGSCOPE`, `SYSASSIGN.ORGUNIT` | `identity_schema.hpp:95,103,112` | **persisted and round-tripping.** Written `identity_dbf_store.cpp:238`, read `:344/:352/:359`. |
| `applies()` org-scope check | `identity_repository.hpp:71` | **runs on every permission decision** -- and degenerates to "global always matches" because no org rows exist. |
| `SYSASSIGN.AKIND` C(24) | `identity_schema.hpp:113`, `schema_registry.py:133` | **wired both directions, never written.** Zero non-empty values in the tree. |
| `SYSASSIGN` bitemporal close policy | `schema_registry.py:135` | **live.** `VTHRU` / `ROWVER`. |
| `SYSRULING` | `ruling_schema.hpp:85-101` | authored, NOT built. A docket in all but name. |
| Peer review seats | `PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1.md` sec 3 | charter only, nothing armed. |
| PDR-001 conflicted-abstain rule | `peer_design_review/PDR-001_.../SESSION_V1.md` sec 0 | drafted, 0 turns filed. |

So the plumbing for partners is built, connected, and inert for want of one table.

## 3. The three axes

"Partner" is not one fact. It is three, and two of them already ship.

| Axis | Question it answers | Mechanism | State |
|---|---|---|---|
| **Party identity** | who does this agent answer to? | `SYSORG` + `ORGUNIT` | **missing** |
| **Leave to file** | admitted, revocable, time-boxed? | `SYSGRANT`, `USER REQUEST/APPROVE/DENY/REVOKE` | built |
| **Footing** | may argue, may not be granted relief | `role.ai_partner` = read + propose | built |

Only the first is absent. This lane is narrow on purpose.

## 4. The frame, and where it stops

*Amicus curiae* -- friend of the court -- is a non-party admitted to file a brief because it has
relevant expertise, not because it has a stake. It maps cleanly onto what the project already
says about reviewers: a verdict is a finding, not a decision; the owner rules; a report cannot
approve itself.

It is not an imported metaphor. `ruling_schema.hpp` is already a docket -- `RULEID`, `STEWARD`,
`PROPOSEDAT`, `DECIDEDBY`, `SUPERBY`, and a status ladder of proposed / ratified / rejected /
superseded / withdrawn with `0` glossed "filed, no decision." The court was half-built and
unnamed. Standing is the piece it was missing.

**The frame has a hard limit, and the limit is the useful part.** An amicus is *disinterested*.
Outside AI partners frequently are not: an agent filing a change package is proposing work it
authored. That is a party seeking relief, not a friend of the court. So "partner" splits:

- **amicus** -- adversary, precedent checker, naive reader, the hosted header-only auditor.
  No stake. Files findings. `concur` / `blocking_conflict` are opinions.
- **movant** -- change-package authors. Has a stake. Seeks a ruling. Must be recused from
  reviewing its own matter.

`EXTERNAL_AI_CHANGE_PACKAGE_V1.md` already gestures at this when it says the contract "does not
authorize the outside AI to ... approve its own patch." Today nothing in the data can tell you
whether a given seat authored the thing it is reviewing. That is the gap this lane closes.

## 5. Why not `MemberKind`, and why not a `SYSAMICUS` table

**Not `MemberKind`.** It answers what an actor is made of (Human/AI/Service/External), not whose
it is. Its `External` value is already load-bearing for `member.guest` at minimum privilege. And
`SYSPOST.AUTHKIND` (`bbs_schema.hpp:76`) freezes the raw ordinal into every historical BBS post,
so the enum is append-only forever and should not absorb an orthogonal concern.

**Not a `SYSAMICUS` table.** Standing is relational -- a property of *(party, matter)*, not of the
party. `member.ai.grok.xai` is a disinterested reviewer on PDR-001 and an interested author on
its own AIF-098 patches, simultaneously. A table of amici needs a row per matter, at which point
it has become an assignment table. One already exists and its classification column is empty.

**Not the abbreviation `AC`.** Inside `src/identity/`, adjacent to a permission resolver, `AC`
reads as **Access Control** -- the term of art that RBAC/ABAC/DAC/MAC are species of. Second
collision: the project's SDLC vocabulary (`next_gate`, `truth_state`, `proof_state`) puts
`AC` = **Acceptance Criteria** in the same documents. Rejected on both counts.

The word *amicus* stays in the glossary, where the project keeps its coined terms. The schema
uses plain nouns an external xBase/ODBC reader can decode cold.

## 6. The delta

Three changes. One new table, one column populated, one enum value appended.

**6.1 New header** -- `include/identity/org_schema.hpp` (authored, this lane).

```
SYSORG:  ID  OKEY  PARENT  OTYPE  NAME  STATUS  SORTORD  VFROM  VTHRU  ROWVER
```

Name is 6 chars, inside the <= 10 rule for classic browsability. Widths drawn from the existing
`w::` namespace. Bitemporal columns parallel `SYSMEMBER`.

**6.2 Append `OrgUnitType::Partner = 7`** at `identity_entities.hpp:98`.

Free *only while SYSORG is unseeded*. Once rows exist the ordinal is frozen exactly as
`SYSPOST.AUTHKIND` froze `MemberKind`. Append only; never insert, never reorder.

**6.3 Populate `SYSASSIGN.AKIND`** with the standing ladder:
`amicus` / `movant` / `steward` / `host` / `owner`, empty = no standing established.

No schema change -- the column is already there, already round-tripping, already in the Python
registry and the schema map. Nothing to migrate. This matters: `ensure_bbs_tables` tops up
missing *rows*, not missing *fields* (the gate catch recorded in `AIF098_BUILD_HANDOFF_V1.md`),
so there is no column-add path in this codebase. A lane that needed one would be blocked. This
one does not.

## 7. Predicates

```
independent(a, b) := a.ORGUNIT != 0 AND b.ORGUNIT != 0 AND a.ORGUNIT != b.ORGUNIT

recused(member, matter) := standing_of(member, matter) IN { movant, steward, host }

amicus_eligible(member, matter) :=
       standing_of(member, matter) == amicus
   AND NOT recused(member, matter)
   AND independent(member, steward_of(matter))
```

**Fail closed on zero, and this is the whole trap.** `ORGUNIT = 0` means "no org recorded," which
today is every row in `SYSASSIGN`. A naive `a != b` reads `0 != 0` as false and appears to
behave -- but the moment one row acquires an org while its counterpart stays 0, the pair reads as
independent on the strength of a missing value. Unset is not a party. Two unknowns are not two
different parties.

Same rule for `AKIND`: the empty string means no standing established, and must never be read as
amicus. Absence of a recorded stake is not evidence of disinterest.

## 8. What this unblocks

- **PDR-001 sec 0** -- the conflicted-abstain rule stops being a house convention the host is
  asked to honour and becomes a consequence of standing that a checker can evaluate.
- **`PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1` sec 3** -- seats become assignable from data. Two
  seats conflict iff they share an `ORGUNIT`; a seat is recused iff its `AKIND` is `movant`.
- **BETA-1 gate E1** (`BETA1_EXIT_GATE_V1.md:51`, currently NOT-YET) -- "peer-review pass
  complete (human + cross-AI)" needs cross-AI to be a checkable claim, not an assertion.
- **`applies()` org scoping** -- stops degenerating. Permissions can be scoped to a party.
- **`board.lounge`** ("Derald + AI partners") and `PSEUDO_CHAT_RETURN_LANE_V1` ("web-only AI
  partners") get a referent. Both currently say "partner" in prose with nothing underneath.

## 9. The load-path trap (read before touching all_tables())

`load_identity_tables` hard-failed if ANY `all_tables()` entry was absent from disk. The live
catalog at `data/metadata/identity/` holds exactly the original nine DBFs and no `SYSORG`
(measured 2026-09-04), so folding `sysorg()` in unguarded would have failed the whole identity
load at the next process start -- RBAC down, on real data.

Resolved by splitting the contract. The original nine stay fatal-if-absent: a store missing
`SYSUSER` IS corrupt. Tables added afterwards are tolerated-if-absent, because a store written
before the addition is OLD, not CORRUPT. `schema::is_additive_table()` carries that list, and
every future addition to `all_tables()` belongs in it until a migration has demonstrably reached
every store.

Absence is tolerated on the READ path only. Nothing is created during load, so load stays
side-effect free; the table appears on the next `save_identity_tables()` (`USER SAVE`).

## 10. Landed (2026-09-04)

Compiled clean, MSVC Release, `dottalkpp` + the GUI/test targets.

| File | Change |
|---|---|
| `identity_entities.hpp` | `OrgUnitType` += `Partner` (7), append-only note |
| `identity_schema.hpp` | `sysorg()`, folded into `all_tables()`; `is_additive_table()` |
| `identity_repository.hpp` | `std::vector<OrgUnit> org_units` |
| `identity_dbf_store.cpp` | SYSORG save + load arms; the additive-table guard |
| `identity_bootstrap.hpp/.cpp` | `find_org_by_key`, `apply_standard_orgs` (idempotent by key), called from `build_seed` |
| `identity_admin.hpp/.cpp` | `add_org`, `bind_member_org`, `backfill_orgs` -- owner-gated, persisted |
| `cmd_user.cpp` | `USER ORGS`, `USER ORG ADD|BIND|BACKFILL` |
| `schema_registry.py` | SYSORG TableSpec, bitemporal close policy |
| `org_schema.hpp` | doctrine + `standing::` helpers; table definition removed |

**Why a CLI backfill and not a boot-time top-up.** `boot_identity_store` only calls `build_seed()`
when `SYSUSER.dbf` is ABSENT. An existing catalog never sees the seed, so the roster needs a
second path. A boot-time top-up (the `ensure_bbs_tables` pattern) would have worked, but it adds a
write to the identity boot path, and org membership is policy rather than infrastructure -- it
should be an auditable owner decision, not a side effect of starting the program. One roster
function serves both paths so they cannot drift.

**Roster granularity is one org per vendor**: `org.house`, `org.anthropic`, `org.openai`,
`org.xai`. That is what makes the independence check useful -- Claude and Codex land in different
orgs and can therefore review each other. A single `org.external` would collapse independence to
house-vs-everyone. `member.guest` is deliberately unbound: `ORGUNIT` stays 0 and the predicate
fails closed, so a guest is never counted independent of anyone.

**What the backfill will NOT do:** touch `MemberRole::org_scope`. Setting that narrows a role
binding to one org and could start denying permissions that resolve today. A backfill does not get
to do that.

## 11. Still owed

1. `claim-aif` for this lane; replace the `unclaimed` placeholder here and in `org_schema.hpp`.
2. Snapshot `data/metadata/identity/` (the directory already carries `_pre_bbs_backup_*` and
   `_pre_guest_backup_*`; a `_pre_org_backup_*` matches the habit).
3. `USER LOGIN member.derald`, then `USER ORG BACKFILL`, then `USER ORGS` to read it back.
4. `USER VERIFY` -- the APH-5 round-trip now has a tenth table to carry.
5. Capture the transcript, register a proof. Only then does this file move off review-needed.
6. **Standing rows remain unbuilt.** `apply_standard_orgs` writes MEMBERSHIP assignments only
   (`org_unit` set, `work` unset, `AKIND` empty). Per-matter standing needs the work axis, and
   `WorkNode` is still a dead declaration exactly as `OrgUnit` was. So `independent()` is usable
   after step 3; `recused()` and `amicus_eligible()` are not, and the amicus half of this lane is
   vocabulary until `WorkNode` lands.

## 12. Open questions

- **OQ-1.** ~~Does `org.house` need to exist as a row?~~ **Settled 2026-09-04: yes, a row.**
  `apply_standard_orgs` seeds it as `OrgUnitType::Organization`; only outside parties get
  `Partner`. A row keeps `independent()` total and avoids a distinguished value.
- **OQ-2.** Should `AKIND` be promoted from free-text `C(24)` to a small `N` ladder once the
  vocabulary settles? Free text cannot be enforced; an ordinal cannot be extended without the
  freeze problem. Deferred deliberately -- do not decide this until a session has actually run.
- **OQ-3.** Do hosted advisors with no identity row (`AI_ROLES_TAXONOMY_V1`: Ollama, the GPTbase
  advisor) get an `ORGUNIT`? They cannot -- no member row to hang it on. Does that make them
  permanently ineligible as amicus, or does a session record carry standing for them out of band?
  The 2026-08-13 header-only review was exactly this case and it produced the most useful
  findings on record, so the answer matters.
- **OQ-4.** Does the `owner` standing value earn its place, given `is_owner_member()` already
  answers the enforcement question?

## 13. Related

- `docs/maintenance/PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1.md` -- seats, ballot, turn validity
- `docs/maintenance/peer_design_review/PDR-001_workspace_scanner_wbak_2026-08-12/SESSION_V1.md`
- `labtalk/proofs/PEER_REVIEW_HEADER_ONLY_FINDINGS_20260813_V1.md` -- the disinterest argument
- `labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md` -- the movant posture, unnamed
- `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md` -- "a report cannot approve itself"
- `labtalk/ai_portal/AI_GLOSSARY_V1.md` -- the Standing subsection added by this lane
- `include/portal/ruling_schema.hpp` -- the docket this vocabulary completes
- `docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md` -- where seat assignment comes from
