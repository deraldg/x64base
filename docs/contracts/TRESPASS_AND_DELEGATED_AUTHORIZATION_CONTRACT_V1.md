# Trespass and Delegated Authorization Contract v1

Status: **candidate; design-intended; no runtime enforcement claimed**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycle: **DotTalk++ SDLC**
Related owning project: `project.x64base.identity` (AIF-045)
Owner and final authority: `member.derald`
Initial author: `member.ai.codex.local`

## 1. Purpose

Define one actor-neutral rule for humans and AI entering another project, lane,
or protected resource, and define how a validated actor may later delegate a
narrower part of an established authorization.

The owner/admin is the sole structural exception to the ask-for-permission
protocol. The exemption removes the need to request authority; it does not
remove attribution, evidence, or responsibility for material actions.

## 2. Binding term: trespass

> **Trespass is a non-owner actor entering, directing, modifying, claiming,
> promoting, publishing, or occupying protected work within another project,
> lane, assignment, or resource without a valid authorization chain covering
> that actor, action, scope, and time.**

The rule is identical for human and AI actors.

Trespass is an authorization-boundary failure. Intent, usefulness, technical
quality, or a later decision to keep the work does not retroactively authorize
the original action.

## 3. Related terms kept distinct

| Term | Meaning |
| --- | --- |
| `transgression` | broader procedural or contract noncompliance; may occur inside an authorized task |
| `trespass` | action outside the actor's valid project/resource/action authorization |
| `collision` | two authorized actors interfere because coordination or isolation failed |
| `drift` | records or projections disagree over time without a current unauthorized actor action |
| `authorized intervention` | explicit entry into another scope through a valid grant; not trespass |

The historical AIF-021 phrase "constructive transgression" remains a procedural
classification. "Constructive" must never be used to excuse trespass.

## 4. Actions that are not trespass

Subject to sensitivity and read permissions, these are not trespass:

- prior-art discovery and authority lookup;
- read-only inspection authorized by the current review or diagnostic task;
- reporting a possible problem without mutating the protected scope;
- assistance explicitly authorized by the owner or a valid delegated grant;
- mechanically derived observations that do not change state;
- owner/admin action.

Claiming another lane, changing its status, editing its owned artifacts,
directing implementation, mutating runtime data, committing, promoting, or
publishing are protected actions and require scope-specific authority.

## 5. Current prior art and missing capability

The existing identity contract already distinguishes permission eligibility from
current authorization. `AUTHORIZATION_GRANT` already carries a recipient, work,
resource scope, action scope, risk, grant time, expiry, status, reason, and
source report.

The current runtime does not yet model safe delegated authorization:

- `authorization.grant` is a Critical permission seeded only to the maintainer;
- `AuthorizationGrant` has no granting actor, parent grant, delegation flag, or
  delegation-depth field;
- no resolver proves that a child grant is narrower than its parent;
- no revocation cascade or delegated-grant audit test exists.

Therefore this contract records requirements, not an implemented capability.

## 6. Validated actor

An actor may receive or issue delegated authority only when all are true:

1. it resolves to a durable `TEAM_MEMBER` identity;
2. the current session is authenticated and bound to that member;
3. its effective permission set makes it eligible for the proposed action;
4. a live authorization grant covers the current project and work scope;
5. independent security policy does not deny the action.

A model, advisor, chat response, username string, or open socket is not a
validated actor by itself.

## 7. Delegation chain

The owner creates a root authorization. A validated actor may create a child
authorization only when the parent explicitly permits delegation.

Every delegated grant must record at least:

```text
authorization_id:
parent_authorization_id:
grantor_member_id:
grantee_member_id:
project_id:
work_node_or_lane:
resource_scope:
action_scope:
maximum_risk:
valid_from:
expires_at:
may_delegate:
maximum_delegation_depth:
required_proof:
required_closeout:
reason:
status:
```

## 8. Attenuation invariants

A child grant:

- cannot contain an action absent from its parent;
- cannot cover a broader project, lane, path, database, branch, or publication
  target;
- cannot exceed the parent's maximum risk;
- cannot start before or expire after its parent;
- cannot delegate when the parent forbids delegation;
- cannot exceed the remaining delegation depth;
- becomes ineffective immediately when any ancestor expires or is revoked;
- cannot override an explicit denial or independent security policy;
- never inherits the owner's structural exemption.

The effective delegated scope is the intersection of every grant in the chain,
not the union.

## 9. Safeguards

Before a protected action:

1. resolve identity and authenticated session;
2. resolve the full authorization chain;
3. verify eligibility, action, resource, project, lane, time, risk, and depth;
4. check active claims, assignments, locks, and worktree ownership;
5. isolate mutable work when another actor has a live workspace;
6. record the authorization ID in the run.

Before commit, promotion, or publication:

1. compare the exact changed paths and effects with the resolved grant;
2. reject unscoped files and mixed-project changes;
3. require the named proof and closeout;
4. record grantor, grantee, authorization chain, and result in the audit event.

Revocation must prevent new protected actions and cascade through descendants.
It must not erase the historical audit record.

## 10. Trespass response states

| State | Meaning | Required response |
| --- | --- | --- |
| `attempted_prevented` | a gate blocked the action before mutation | record the denial and preserve no unauthorized change |
| `contained` | an unauthorized local change exists but was not committed, promoted, published, or applied to persistent data | stop, preserve exact evidence, notify the owner, and request disposition |
| `materialized` | unauthorized work crossed a durable boundary | contain further effects, identify impacted records and consumers, and require owner adjudication plus corrective closeout |
| `adopted_after_review` | the owner later accepts useful work | record adoption as a new authorized decision; do not rewrite the original event as authorized |

An agent must not silently clean, revert, publish, or legitimize another actor's
unauthorized work unless the owner authorizes that response.

## 11. Acceptance matrix

The contract is not runtime-proven until tests cover:

- human to human delegation;
- human to AI delegation;
- AI to human delegation under an explicitly delegable root grant;
- AI to AI delegation under an explicitly delegable root grant;
- unauthenticated and unknown actors;
- action, resource, project, and time mismatches;
- child scope amplification;
- forbidden subdelegation and depth exhaustion;
- parent expiry and parent revocation cascade;
- explicit denial and independent-policy precedence;
- worktree/claim collision between otherwise authorized actors;
- commit, promotion, and publication preflight;
- owner/admin exemption with preserved attribution.

Every allow and deny case must state the resolved identity, authorization chain,
scope comparison, and decisive rule.

## 12. Educational obligation

The implementation must become a LabTalk worked case using the actual schema,
resolver, denial tests, mistakes, and corrections produced by this SDLC. The
project will not teach delegation safeguards that its own authorization path
does not enforce.

## 13. Current authorization note

On 2026-08-03 the owner explicitly authorized continuation of the integration
and improvement work that created this candidate contract under AIF-086. The
initial authorization covered the governed documentation and registration
slice. The owner later authorized a bounded housekeeping pass plus exact-path
staging, commit, and push of that AIF-086 slice to `development`.

Neither authorization permits runtime RBAC changes, operative delegation,
promotion to `C:\x64base`, a push or merge to `main`, public website mutation,
publication, or changes to incorporated lanes outside the recorded slice.
