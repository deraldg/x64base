---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260722-005
  recorded_at_utc: 2026-07-22T23:28:45Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.identity
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 969bd1582
    head_commit: bfa6bb0fd
  authorization:
    requested_by: maintainer
    scope: real session authentication — low-privilege default, login/credentials, owner-gated admin, and token auth for AI agents
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_IDENTITY_2D_SESSION_AUTH_2026-07-22.md
    kind: session_closeout
---

# Session Closeout — Identity 2d: session authentication + AI token auth (2026-07-22)

Owning lifecycle: DotTalk++ SDLC (`project.x64base.identity` AIF-045).
Operating mode: `development`.
Change class: `C2` (startup-trust change + credential/session model).
Build target: `dottalkpp_runtime`.
Truth state: proven in-engine and g++-proven standalone before each build.
Promotion state: committed (`2a89cc5c3`, `bfa6bb0fd`); maintainer pushes. Staging untouched.

## Outcome

Session authentication makes the whole identity model trustworthy. The console no longer
runs as owner by default — it boots **low-privilege (`member.public`, unauthenticated)** and
owner powers require `USER LOGIN`. A session has a **principal** (the authenticated identity)
and an **acting** member (the owner may sudo via `USER AS`); the acting member can only become
owner-class by authenticating, which closes the privilege-escalation hole.

- **2d — session auth (humans).** `USER LOGIN / LOGOUT / PASSWD`, salted local-hash credential
  (FNV-1a; honestly labeled obfuscation-grade) on `SYSUSER.CRED`; first-run bootstrap for a
  credential-less owner (the owner is the local reset/recovery authority — no email/SMS needed).
  `USER AS` is owner-sudo (authenticated owner only); `USER WHOAMI` shows principal/acting/auth.
  All admin mutations (`ADD/GRANT/UNGRANT/APPROVE/DENY/REVOKE/DELETE`) now require an
  authenticated owner.
- **2d-2 — token auth (AI agents).** AI/service members get a token-based service-User
  credential home (auto-created on `USER ADD`, seeded for the built-in AI members, self-healed
  by `USER TOKEN` on older stores). `USER TOKEN <member>` (owner-only) mints/rotates an opaque
  token, stores its salted hash, prints it once; re-issue invalidates the old one. Bootstrap
  login is owner-only, so an un-tokened agent cannot slip in. An agent logs in *as itself* with
  its token and holds only its own permissions.

## The recovery answer (design note)

"What if an AI forgets its password?" — it doesn't have one. Agents use **owner-issued tokens**;
a lost token has no recovery ceremony because the owner simply **reissues** (rotation invalidates
the old). Humans use passwords, and the owner is the local reset authority. Agents never use the
owner's password; the owner never learns theirs.

## Durable records

| Surface | Change |
| --- | --- |
| `include/identity/identity_admin.{hpp}`, `src/identity/identity_admin.cpp` | Session state (principal/acting/authenticated), `login`/`logout`/`set_password`/`act_as`/`issue_token`, salted-hash + token helpers, owner-gate on admin ops, service-User creation. |
| `include/identity/identity_bootstrap.{hpp}`, `src/identity/identity_bootstrap.cpp` | `next_user_id()`; seed AI members given token service-Users. |
| `src/cli/cmd_user.cpp` | `USER LOGIN/LOGOUT/PASSWD/TOKEN`; `USER AS` → owner-sudo; `USER WHOAMI` shows principal/acting/auth. |
| `dottalkpp/data/scripts/dotscript/identity_accept_regression.dts` | Logs in (bootstrap) before admin ops; logs out after. |

## Behavior change (intended)

Owner-by-default is gone: the console boots `member.public`. Admin commands **and** `!` host
commands now require `USER LOGIN member.derald` first. A password is optional for the owner
(bootstrap local trust covers a solo machine); it only matters to require the secret if the
console could be reached by an untrusted party.

## Validation

- In-engine: `WHOAMI` public/unauthenticated at boot; `ADD`/`AS` refused logged-out; `USER LOGIN
  member.derald` (bootstrap) → admin works; `IDENTITY_ACCEPT` regression green; `USER TOKEN
  member.ai.claude.cowork` → agent `USER LOGIN` with the token authenticates as itself.
- Sandbox g++ proofs against real code: `AGSEC-2D-AUTH`, `AGSEC-2D-GATE`, `AGSEC-2D2-TOKEN` — all PASS.
- Every commit passed `tools/staging/prepush_gate.py`.

## Open / next

- Fresh `data/metadata/identity` picks up the seed AI service accounts (existing stores self-heal
  via `USER TOKEN`).
- The `!` host gate is wired; the SFTP host surface (`cmd_sftp`) is not yet gated.
- M4 registry import (org units / work nodes) not started; M5 YAML portable-export leg remains.

## Review gate

Human review may confirm the low-privilege-until-login posture and the human-password /
AI-token split match intent, and sequence the SFTP gate, M4 import, and M5 YAML export.
