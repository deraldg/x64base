# Team Member / Role / Permission / Assignment / Authorization — Contract V1

**Status:** design (M0). No code. This is the entity/behavior contract that gates M1+.
**Project:** `project.x64base.identity` (AIF-045). Lane doc: `IDENTITY_RBAC_MANAGEMENT_LANE_V1.md`.
Source plan: `docs/## AI Portal re-examination.txt` (evaluated + endorsed with caveats).
**Freshness:** 2026-07-21.

This contract must be complete and accepted **before** M1 code and **before** any APH-3
guarded-execution expansion. Two things it exists to resolve up front: the **`USERS` ↔
profile-home binding** (§5) and the **authentication decision** (§6).

---

## 1. Layered model (the whole point)

```text
USERS             identity / account            who can have a session
TEAM_MEMBER       participation                 durable org/project actor (human, AI, service)
ROLE              function                      what a member does
PERMISSION        eligibility                   what operation MAY be considered
SCOPE             bounds                        where a role/permission applies (org + work)
AUTHORIZATION     the grant                     who approved THIS action, for how long
SECURITY POLICY   hard final limit              what the runtime permits under ANY circumstance
```

**Rule:** *Permission establishes eligibility; authorization permits the current action.*
A role is never standing authority to mutate. `TEAM_MEMBER` does not replace `USERS`; the
management schema does not replace the security policy; the security policy can deny even when
role + authorization would allow (it is the last word).

---

## 2. Strong ID types (no interchangeable integers)

Each is a distinct 64-bit strong type — a `UserId` must never be passable where a `RoleId` is
expected. Every entity also carries a **portable string key** (`MemberKey` etc.) for YAML
bootstrap/export; the numeric ID is authoritative inside x64base, the key is the stable
human/portable handle.

```text
UserId  TeamMemberId  RoleId  PermissionId  PermissionSetId
AssignmentId  AuthorizationId  OrgUnitId  WorkNodeId  EventId
```

---

## 3. Entities

### 3.1 USERS (identity — NEW; does not exist today)
```text
UserId          strong id (authoritative)
UserKey         portable, e.g. user.derald
LoginName       account handle
DisplayName
AuthKind        LOCAL_TRUSTED | OS_BOUND | PASSWORD | TOKEN | HUMAN_ASSERTED   (see §6)
CredentialRef   opaque ref to credential store (NULL until real auth; never a plaintext secret)
Status          ACTIVE | SUSPENDED | RETIRED
ProfileHomeKey  binds to the on-disk profile home (see §5)
ValidFrom / ValidThrough / RowVersion
```
USERS owns identity/account state only — never role, project, permission vectors, or session.

### 3.2 TEAM_MEMBER (participation)
```text
TeamMemberId
UserId              -> USERS (NULL allowed for pure SERVICE identities)
MemberKey           e.g. member.derald, member.ai.claude.cowork
MemberKind          HUMAN | AI | SERVICE | EXTERNAL
DefaultRoleId       optional
DefaultPermissionSetId optional
Status              ACTIVE | SUSPENDED | RETIRED
ValidFrom / ValidThrough / RowVersion
```
**Do NOT put in TEAM_MEMBER:** manager id, project id, department id, a permission vector,
current session id, current task authorization. Those are context — they live in assignments and
authorizations. One member has different roles/managers/permissions in different projects.

### 3.3 ROLE (function)
```text
RoleId  RoleKey  RoleName  RoleKind  Description  Status
```
Seed roles: `MAINTAINER, DEVELOPER, REVIEWER, TEACHER, STUDENT, AI_DEVELOPMENT_PARTNER,
PUBLICATION_OPERATOR`. (Bridges the current hard-coded `DEVELOPER/TEACHER/STUDENT`.)

### 3.4 PERMISSION (eligibility)
```text
PermissionId  PermissionKey  ResourceClass  Action  RiskClass  RequiresApproval  Status
```
Seed catalog (`resource.action`): `source.read, source.propose, source.mutate, database.read,
database.mutate, help.mutate, metadata.mutate, staging.promote, git.commit, git.push,
website.publish, branch.change, user.manage, role.assign, authorization.grant`.
`RequiresApproval=true` for every high-risk mutate/publish/promote/git/branch permission.

### 3.5 Crosswalks
```text
ROLE_PERMISSION            (RoleId, PermissionId)
MEMBER_ROLE               (TeamMemberId, RoleId, scope: OrgUnitId?, WorkNodeId?)   -- scoped
MEMBER_PERMISSION_OVERRIDE (TeamMemberId, PermissionId, Effect: ALLOW|DENY, scope) -- DENY wins
PERMISSION_SET / PERMISSION_SET_ITEM   -- named reusable bundles (deferrable to a later phase)
```

### 3.6 ORG_UNIT (containment) / WORK_NODE (work decomposition)
Two separate hierarchies (never one overloaded tree):
```text
ORG_UNIT:  UnitId UnitKey ParentUnitId UnitType(ORGANIZATION|DIVISION|DEPARTMENT|TEAM|COMMITTEE|CLASS|LAB) Name Status ...
WORK_NODE: WorkId WorkKey ParentWorkId WorkType(PROJECT|LANE|GATE|MILESTONE|EPIC|TASK|PROOF|PUBLICATION)
           ProjectKey Title Status Priority OwnerAssignmentId NextGate TruthState ProofState RiskClass ...
```
`WORK_NODE` is the managed form of today's YAML (`projects.yaml` projects/lanes, `ai_portal.yaml`
`aph0..6` gates). Import preserves the portable keys, adds numeric IDs.

### 3.7 TEAM_ASSIGNMENT (the central crosswalk)
```text
AssignmentId  MemberId  OrgUnitId  WorkId  RoleId  PermissionSetId
ReportsToAssignmentId   -- reporting lives on the ASSIGNMENT, not on the member
AssignmentKind  Status  ValidFrom  ValidThrough
```
Supervisory reporting is the third relationship (distinct from org containment and work
decomposition) and is context-scoped: the same person reports to different leads on different
assignments.

### 3.8 AUTHORIZATION_GRANT (the durable approval)
```text
AuthorizationId  RequestedByMemberId  GrantedToMemberId  RoleAssignmentId  WorkId
ResourceScope  ActionScope  RiskClass  GrantedAt  ExpiresAt  Status  Reason  SourceReportId
```
Answers, machine-verifiably: *who authorized whom, to do what, against which project/lane/files/
database, for how long, under which role + permission set.*

### 3.9 MANAGEMENT_EVENT (audit journal)
Append-only record of every create/assign/grant/revoke/login/logout with actor, before/after,
and references (`actor_user_id, actor_member_id, assignment_id, authorization_id,
permission_snapshot_id`). Names stay in exported YAML for portability; IDs are authoritative.

---

## 4. Effective-permission resolution (pure, tested function)

```text
effective(action, member, work, session) =
      base   = union(role_permissions for member's in-scope MEMBER_ROLEs)
    + grants = scoped MEMBER_PERMISSION_OVERRIDE Effect=ALLOW
    - denials= scoped MEMBER_PERMISSION_OVERRIDE Effect=DENY          (DENY precedence)
    ∩ task_authorization  (a current AUTHORIZATION_GRANT covering action+scope, unexpired)
    ∩ session_capabilities
    ∩ runtime_security_policy                                         (final, independent)
```
Result is `ALLOW` only if the action survives every stage. Must be a **pure function** (no I/O)
over a resolved snapshot, so it is unit-testable and reproducible — and doubles as the APH-6
teaching artifact. For any `PERMISSION.RequiresApproval=true`, eligibility (base+grants−denials)
is necessary but **not sufficient**: a live `AUTHORIZATION_GRANT` is required.

### 4.1 Worked examples
```text
A) derald / MAINTAINER on project.x64base.runtime, action=git.push
   base: MAINTAINER has git.push (RequiresApproval=true)
   grants/denials: none ; task_auth: owner standing grant ; session: interactive ; policy: allows
   => ALLOW

B) member.ai.claude.cowork / AI_DEVELOPMENT_PARTNER, action=source.mutate
   base: partner has source.read + source.propose, NOT source.mutate
   => DENY at base (eligibility fails) -- can propose a patch, cannot mutate authority tree

C) member.ai.claude.cowork / AI_DEVELOPMENT_PARTNER, action=source.propose, but no grant
   base: has source.propose ; RequiresApproval=false -> eligible
   => ALLOW to propose; a subsequent staging.promote/git.commit needs a grant (A/B rules)

D) student / STUDENT in a CLASS org unit, action=database.mutate on a lesson DB
   base: STUDENT lacks database.mutate ; grant: scoped ALLOW for that one WorkNode
   => ALLOW only within that scope; DENY elsewhere (scope intersection)

E) any member, action=host shell via a scratch command, security policy = host commands OFF
   base+grant+auth may all say ALLOW
   => DENY -- runtime security policy is the last word (DOTTALK_ALLOW_HOST_COMMANDS off)
```

---

## 5. USERS ↔ profile-home binding (resolved)

A `USERS` row **owns** an on-disk profile home; identity is the managed layer over the existing
hierarchy found at `dottalkpp/user/<key>/`:
```text
USERS.ProfileHomeKey = derald   <->   dottalkpp/user/derald/
                                         logs/ prefs/ scripts/ security/ storage/ tmp/ workspaces/
```
- `MemberKey` (`member.derald`) → `UserKey` (`user.derald`) → `ProfileHomeKey` (`derald`).
- Existing profiles `default`, `public`, `user`, `derald` **seed** the first `USERS` rows.
- `USER` management **provisions/retires the whole tree**, not just a DB row (create home with the
  standard subdirs; retire archives/removes it).
- The per-user `security/` dir is the on-disk anchor for a user's **local** security state; the
  **central** RBAC tables live in x64base. Local dir ≠ authority; the DB is authoritative.
- `public` maps to shared/anonymous scope; `default` is the fallback home.

---

## 6. Authentication decision (resolved: model now, credential later)

Design the identity *model* in V1; **defer the credential mechanism** — but do so honestly.

- **`SECURITY LOGIN` today is selection, not authentication.** V1 keeps the command but binds the
  session to a real `USERS` row via `MemberKey`, and records `authenticated=false` until a
  credential mechanism lands. No feature pretends to authenticate.
- **`AuthKind` per user** names how identity *will* be established: `LOCAL_TRUSTED` (the person at
  the console is the owner — the alpha default for `derald`), `OS_BOUND` (bind to the OS user),
  `PASSWORD`/`TOKEN` (future credential store via `CredentialRef`), `HUMAN_ASSERTED` (AI members).
- **AI members are `HUMAN_ASSERTED`.** An AI session's identity is not self-proven; it is asserted
  by the operating human. So an AI `RUN` records provider/product/model/external-session-id **and**
  the authorizing human's `AuthorizationId`. The AI's "authentication" *is* the human's grant.
- **Never store plaintext secrets** (aligns with the security policy); `CredentialRef` is opaque.

Deferred to a later milestone (explicitly, not silently): real credential verification, password
hashing/rotation, token issuance, session expiry semantics.

---

## 7. AI members vs sessions

Do not mint a `TEAM_MEMBER` per conversation. Member = durable actor
(`member.ai.claude.cowork`, `member.ai.codex.local`, `member.ai.chatgpt.partner`); the individual
conversation is an `AI_SESSION`/`RUN` beneath it:
```text
AI_SESSION/RUN: provider product model external_session_id access_mode baseline_commit
                start/end authorization_id transcript_hash actor_member_id
```

---

## 8. Invariants

1. A role grants eligibility, never standing authority to mutate/stage/commit/publish/delete/
   reset/branch.
2. DENY overrides ALLOW in overrides.
3. `RequiresApproval` permissions need a live `AUTHORIZATION_GRANT`, not just eligibility.
4. Runtime security policy is independent and final — it can deny anything.
5. Numeric IDs authoritative inside x64base; portable string keys survive YAML round-trip.
6. Reporting is on the assignment, not the member.
7. Owner (`derald`) is the sole exemption to the ask-for-permission protocol (per the dev-tools
   security doctrine); everyone else — human or AI — requests scoped authorization.

---

## 9. Scope of V1 vs deferred

**In V1 (this contract):** entity fields, strong ID types, the resolution algorithm + worked
examples, the profile-home binding, the authentication model + defer decision, invariants.
**Deferred (named, not silent):** `PERMISSION_SET` normalization, credential verification,
`ORG_UNIT`/`WORK_NODE` *import* mechanics (M4), degraded read-only bootstrap proof (M5).

---

## 10. Open questions to close before M1

1. Credential store shape for the eventual `PASSWORD`/`TOKEN` `AuthKind` (out of V1, but name the
   target so `CredentialRef` is designed once).
2. Where the resolved permission **snapshot** is persisted for audit (`permission_snapshot_id`) —
   inline in `MANAGEMENT_EVENT` vs a snapshot table.
3. Whether `AI_SESSION`/`RUN` is a `WORK_NODE` subtype or its own entity (leaning own entity).
4. Exact `OrgUnit`/`WorkNode` seed set to import first (candidate: `project.x64base.*` +
   `aiportal.gate.aph0..6`).

Acceptance of this contract (owner sign-off) is the M0 exit gate.
