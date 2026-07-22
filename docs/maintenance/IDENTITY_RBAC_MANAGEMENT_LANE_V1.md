# Identity / RBAC / Authorization Management — Project Lane V1

**Status:** **ACTIVE — full-blast (owner decision 2026-07-21).** M0 contract drafted +
accepted; M1 started. Owner directive: this is a necessary project and integrating it later is
harder as it touches ownership of everything, so it runs now in parallel — additive new module
(`identity/`), low collision with BETA-1 regression, but must not destabilize the stabilization
sweep. Original "must not front-run BETA-1" caveat is superseded by owner priority.
**Project:** `project.x64base.identity` (AIF-045). Parent authority: `project.x64base.runtime`.
**Design authority:** the external-AI proposal, preserved at
`docs/## AI Portal re-examination.txt`, evaluated and endorsed with caveats (this doc).
**Freshness:** 2026-07-21.

The durable bridge the AI Portal is missing: **USERS → TEAM_MEMBER → TEAM_ASSIGNMENT →
{ROLE, PERMISSION, ORG_UNIT, WORK_NODE, AUTHORIZATION_GRANT}**, with the operational
security policy kept **independent** as the final runtime constraint.

---

## 0. Governing separation

```text
USERS             Who can have an account/session          (identity)
TEAM_MEMBER       Who participates in the org/project       (participation)
ROLE              What function that member performs        (function)
PERMISSION        What operation may be considered          (eligibility)
SCOPE             Where the role/permission applies         (org/work bounds)
AUTHORIZATION     Who approved THIS specific action         (the grant)
SECURITY POLICY   What the runtime permits under any        (hard final limit)
                  circumstances
```

> **Permission establishes eligibility; authorization permits the current action.**

`TEAM_MEMBER` does **not** replace `USERS`; the management hierarchy does **not** replace
the security module. A role is never standing authority to mutate — the portal's
explicit-approval doctrine (workflow knowledge ≠ permission to mutate/stage/commit/publish/
delete/reset/branch) holds.

---

## 1. Ground-truth (verified 2026-07-21)

| Plan claim | Verified? | Finding |
|---|---|---|
| `cmd_security.cpp` = session-role selector, hard-coded `DEVELOPER/TEACHER/STUDENT`, no credential check | **Yes** | `{logged_in, role, worker}`; `SECURITY LOGIN <role> [AS <worker>]`; hard-coded `*_ASSIGNMENTS.md` |
| Portal projects/gates are YAML, not managed hierarchy | **Yes** | `labtalk/registries/ai_portal.yaml` holds `aph0..6`; `projects.yaml` holds projects+inline lanes |
| Operational security policy is separate from RBAC | **Yes** | `xbase_security_policy` / host-shell block (`DOTTALK_ALLOW_HOST_COMMANDS`) is capability policy, independent of any role |
| **`USERS` is the existing identity authority** | **No** | **`USERS` is not implemented** — no table/struct in the tree, only a concept in docs. Step M0 must *define* `USERS`, not "retain" it. |
| A `cmd_user` / `USER` command exists | **No** | No `cmd_user.cpp` and no `USER` command registered — only `cmd_security` (`SECURITY`). A `cmd_user` surface for the `USERS` entity is **new scope** here (M3), paralleling `SECURITY`. |
| "user" already means something in-tree | **Yes — a real hierarchy** | `dottalkpp/user/<profile>/` is an existing per-user **home**: `logs/ prefs/ scripts/ security/ storage/ tmp/ workspaces/` (workspaces hold `.dtschema`/`.erz`). Profiles present: `default`, `public`, `user`, and the named **`derald`**. Note the **per-user `security/` dir already exists**. This is per-user *data/profile* isolation, not identity — but a `USERS` row must **own** a profile home, so `USERS`-as-identity is the missing managed layer over an existing on-disk hierarchy. |

---

## 2. Evaluation verdict — endorse the design

Strong and doctrine-aligned. Notable strengths:

- The seven-layer separation keeps the **security policy independent** — it can deny even
  when role + authorization permit. This is exactly the layering in
  `AI_DEV_TOOLS_SECURITY_DOCTRINE_V1.md` (dormant permission gate + host-shell block as the
  last word). Perfect fit.
- **Three separate hierarchies** — org containment (`ORG_UNIT`), work decomposition
  (`WORK_NODE`), supervisory reporting (`TEAM_ASSIGNMENT.REPORTS_TO`) — not one overloaded
  tree; `REPORTS_TO` lives on the assignment, not the member.
- **Member ≠ session/run** — durable actor vs per-conversation run (`member.ai.claude.cowork`
  + an `AI_SESSION`/`RUN` underneath); avoids a `TEAM_MEMBER` explosion, matches the audit
  contract.
- **Strong distinct ID types** (`UserId`/`RoleId`/`PermissionId`/…) + entity-vs-service split
  (domain `TeamMember`; a separate authorization service computes effective permissions).
  Teaching-grade (AIF-037), testable.
- **YAML round-trip proof before authoritative** matches APH-5 self-hosting doctrine.

---

## 3. Caveats (pinned — address in M0 contract)

1. **`USERS` is greenfield.** Define it (or explicitly name the identity anchor) — it does
   not exist today.
2. **Authentication is undesigned.** The plan migrates *resolution* but not *how* a login is
   authenticated — and for AI members identity is asserted by the operating human, not
   self-proven. Design auth or explicitly defer it and keep the session-selector honest.
3. **This is a PROJECT, not a lane, and must not front-run BETA-1 (AIF-041)** or engine work.
4. **Phase the schema.** Build the security-critical core first (identity / role / permission /
   member-role / authorization-grant); defer `ORG_UNIT`/`WORK_NODE` hierarchy and
   `PERMISSION_SET` normalization. Don't over-normalize an alpha.
5. **Self-hosting bootstrap is the sharp risk.** The RBAC tables live *inside* the DB they
   govern (chicken-and-egg). The answer — YAML portable bootstrap + degraded read-only startup
   (APH-5) — must be nailed, not sketched. The effective-permission resolver
   (`role perms + grants − denials ∩ task-auth ∩ session-caps ∩ security-policy`) must be a
   pure, tested function with worked examples (doubles as the APH-6 teaching artifact).

---

## 4. Milestones (phased)

- **M0 — Contract v1 (design, not code).** *Team Member / Role / Permission / Assignment /
  Authorization Contract v1*: entity fields, strong ID types, the permission-vs-authorization
  distinction, the effective-permission resolution algorithm with worked examples, and the auth
  decision (design or explicit defer). **Gate: complete before any APH-3 guarded-execution
  expansion.**
- **M1 — RBAC core (C++).** `TeamMember` domain entity (no DB access / no permission calc
  inside it) + repository/service interfaces; `ROLE`, `PERMISSION`, `ROLE_PERMISSION`,
  `MEMBER_ROLE`, `MEMBER_PERMISSION_OVERRIDE` (ALLOW/DENY, deny-precedence). Define `USERS`.
- **M2 — x64base management schema.** `ORG_UNIT`, `WORK_NODE`, `TEAM_ASSIGNMENT`,
  `AUTHORIZATION_GRANT`, `MANAGEMENT_EVENT` (audit journal).
- **M3 — Command surfaces: bridge `cmd_security` + add `cmd_user`.** Keep `SECURITY`
  (`LOGIN`/`WHOAMI`/`ASSIGNMENTS`/`LOGOUT`), replacing hard-coded roles/workers/assignments with
  entity lookups; add a new `cmd_user` (`USER …`) surface for `USERS` entity management
  (create/list/show/status), paralleling `SECURITY`. **A `USERS` row owns a profile home** at
  `dottalkpp/user/<key>/` (`logs/ prefs/ scripts/ security/ storage/ tmp/ workspaces/`), so
  `USER` management **provisions/retires the whole directory tree**, not just a DB row. The
  per-user `security/` dir is the on-disk anchor for a user's local security state (central RBAC
  tables live in x64base; the per-user dir holds local state). Existing profiles `default` /
  `public` / `user` / `derald` seed the initial `USERS` rows.
- **M4 — Import portal registries.** Ingest `projects.yaml` + `ai_portal.yaml` (`aph0..6`
  gates) into `WORK_NODE`; preserve portable string keys, add internal 64-bit IDs.
- **M5 — Round-trip proof.** x64base → YAML/JSON → x64base with stable IDs, parent links,
  assignments, authorizations unchanged; degraded read-only startup proven.
- **M6 — Teaching loop (APH-6).** Demonstrate RBAC + hierarchy + authorization + audit through
  DotTalk++ commands.

---

## 5. Portal gate contribution

APH-1 (typed registry graph): stable member/role/assignment/org/work IDs. APH-2 (context
compiler): owner + responsible member + authority chain. APH-3 (guarded execution): resolve
actor → permissions → authorization → scope → security policy, with prepare/approve/execute/
verify states and retained authorization decisions. APH-4: display hierarchy/ownership/
approvals. APH-5: x64base schemas + deterministic YAML import/export + recovery proof. APH-6:
teach the whole model.

---

## 6. Doctrine fit

Sibling of the methodology projects (AIF-039/040). Extends `AI_DEV_TOOLS_SECURITY_DOCTRINE_V1`
(independent security policy as last word). Registered as a project per AIF-040 tiering. The
first design artifact is Contract v1; the x64base schema follows it; neither front-runs
BETA-1 (AIF-041).
