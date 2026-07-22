---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260722-004
  recorded_at_utc: 2026-07-22T22:45:30Z
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
    baseline_commit: eba9a7012
    head_commit: 6b350ffed
  authorization:
    requested_by: maintainer
    scope: implement AI-agent local security — accept agents through DotTalk++'s own identity/RBAC, wire enforcement into real chokepoints, and update the AI portal protocol
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_IDENTITY_2C_AGENT_SECURITY_2026-07-22.md
    kind: session_closeout
---

# Session Closeout — Identity 2c: AI-agent local security (2026-07-22)

Owning lifecycle: DotTalk++ SDLC (`project.x64base.identity` AIF-045).
Operating mode: `development`.
Change class: `C2` (mutable persistent identity + admin command surface + enforcement wiring).
Build target: `dottalkpp_runtime`.
Truth state: proven in-engine across every milestone and g++-proven standalone before each build.
Promotion state: committed to `homegrown-cnx-20251112-branch` (`0d4b9b407`, `be021e8b7`, `cf977b160`, `6b350ffed`); pushed by the maintainer. Staging (`C:\x64base`) not touched.

## Outcome

DotTalk++ now **implements security with AI agents and accepts them locally through its
own identity/RBAC**, enforced at real chokepoints. The complete lifecycle:

1. **Admit** — `USER ADD member.ai.<name> AI role.ai_partner` registers an AI agent as a
   real member, persisted to x64base.
2. **Ask for limited permission** — `USER REQUEST <perm> FOR <member> <reason>` (the AI
   portal protocol) creates a pending request; `USER REQUESTS` lists them.
3. **Owner approves** — `USER APPROVE <id> [HOURS n]` (or direct `USER GRANT <perm> TO
   <member>`) mints a scoped `ALLOW` override (eligibility) + a time-boxed authorization
   grant (default 24h). Owner decision 2026-07-22: approval mints eligibility+authorization.
4. **Resolve + enforce** — `agent_permitted()` is the single enforcement entry; the
   resolver flips `authorize()` to ALLOW for a granted agent and back to DENY on
   `USER UNGRANT` / `USER REVOKE` / expiry. Owner-class is exempt.
5. **Withdraw / retire** — `USER UNGRANT`, `USER REVOKE`, `USER DELETE` (owner-guarded).

## Milestones (all committed + in-engine proven)

| Milestone | Delivered | Commit |
| --- | --- | --- |
| 2c-1 | Mutable + persistent store, epoch clock, read-only guard, id allocation | `0d4b9b407` |
| 2c-2 | `USER ADD` admission (AI/human/service), persisted | `0d4b9b407` |
| 2c-3 | Grant lifecycle: `USER REQUEST / APPROVE / DENY / REVOKE` | `0d4b9b407` |
| 2c-4 | Enforcement bridge `agent_permitted()` + acting member (`USER AS/WHOAMI/ENFORCE`); dev-tools gate consults identity; AI_PORTAL protocol names the real commands | `be021e8b7` |
| 2c-5a | Direct `USER GRANT/UNGRANT`, `USER DELETE`; repeatable `IDENTITY_ACCEPT` regression | `cf977b160` |
| 2c-5b | Host-shell enforcement in the `!` (BANG) command | `6b350ffed` |

## Enforcement points wired

- **AI dev-tools gate** (`src/cli/ai_devtools_policy.cpp`) — `DEFCMD`/`DEFFN` consult the
  acting member's authorization; owner exempt, granted agent permitted, ungranted agent
  declined under `DOTTALK_DEVTOOLS_REQUIRE_PERMISSION` (dormant-permit default preserved).
- **Host shell-out** (`src/cli/cmd_bang.cpp`) — the `!` command refuses a non-owner acting
  member without a live `host.shell` grant, additive to `DOTTALK_ALLOW_HOST_COMMANDS`.

## Method note

Every milestone was g++-proven against the real engine code in the sandbox before the MSVC
build (`AGSEC-ACCEPT-FLOW`, `AGSEC-ENFORCE`, `AGSEC-5A-CYCLE`, `AGSEC-5B-HOSTSHELL` — all
PASS), so each build was confirmation, not discovery.

## Durable records

| Surface | Change |
| --- | --- |
| `include/identity/identity_admin.{hpp}`, `src/identity/identity_admin.cpp` | Admin + grant + direct-grant + enforcement API. |
| `include/identity/identity_bootstrap.{hpp}`, `src/identity/identity_bootstrap.cpp` | Mutable store, persist, clock, id allocation, `find_role_by_key`. |
| `src/cli/cmd_user.cpp` | `USER ADD/REQUEST/REQUESTS/GRANTS/APPROVE/DENY/REVOKE/GRANT/UNGRANT/DELETE/AS/WHOAMI/ENFORCE`. |
| `include/cli/ai_devtools_policy.hpp`, `src/cli/ai_devtools_policy.cpp` | Identity-aware dev-tools gate. |
| `src/cli/cmd_bang.cpp` | Host-shell identity enforcement. |
| `src/cli/cmd_regression.cpp`, `identity_accept_regression.dts` | `IDENTITY_ACCEPT` (repeatable). |
| `AI_PORTAL.md` | Ask-for-limited-permission protocol names the real commands + live enforcement. |
| `docs/maintenance/IDENTITY_RBAC_MANAGEMENT_LANE_V1.md`, `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | Status + Session Log. |

## Boundaries preserved / open

- Owner behavior unchanged: acting member defaults to the owner (exempt), host commands still off by default.
- The written `SYS*` catalogs + throwaway demo/regression members under `data/metadata/identity/` are runtime data, not committed.
- **Open (next):** the SFTP host-command surface (`cmd_sftp`) not yet gated; the acting
  member (`USER AS`) is **unauthenticated** — real session authentication is the next
  security frontier; M4 registry import (org units / work nodes) not started.

## Validation

- In-engine: `REGRESSION RUN IDENTITY_ACCEPT` (DENY→ALLOW→DENY, agent removed); `USER ENFORCE`
  owner-ALLOW / agent-DENY; `! echo` owner-runs / agent-refused / granted-agent-runs.
- Sandbox g++ proofs against real xbase code: all four AGSEC harnesses PASS.
- Every commit passed `tools/staging/prepush_gate.py`.

## Review gate

Human review may confirm the acceptance model (approval mints eligibility+authorization,
24h default) matches intent, and decide sequencing of the SFTP gate, session authentication,
and M4 registry import.
