---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260722-003
  recorded_at_utc: 2026-07-22T21:35:00Z
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
    baseline_commit: 685e67d26
    head_commit: b44a32fe2
  authorization:
    requested_by: maintainer
    scope: build identity 2b-ii DBF persistence and 2b-iii boot adoption, prove APH-5 round-trip and degraded read-only startup, commit and publish
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_IDENTITY_2BII_2BIII_PERSISTENCE_2026-07-22.md
    kind: session_closeout
---

# Session Closeout — Identity persistence: 2b-ii DBF + 2b-iii boot adoption (2026-07-22)

Owning lifecycle: DotTalk++ SDLC (`project.x64base.identity` AIF-045), APH-5 self-hosting.
Operating mode: `development`.
Change class: `C2` (new persistence layer + startup-path change + new command surfaces).
Build target: `dottalkpp_runtime`.
Truth state: proven in-engine (round-trip + SEED→DBF boot flip) and g++-proven standalone against the real xbase code.
Promotion state: **published** to `origin homegrown-cnx-20251112-branch` (`9922505e9..b44a32fe2`). Staging (`C:\x64base`) not touched.

## Outcome

Identity now self-hosts in x64base and boots from it. The nine `InMemoryIdentityStore`
vectors persist to nine `SYS*` tables under `data/metadata/identity/`, preserving the
authoritative 64-bit IDs and the portable string keys (Contract Invariant 5).

- **2b-ii — DBF persistence + APH-5 round-trip.** `identity_schema.hpp` (nine tables, 70
  fields), `identity_dbf_store.{hpp,cpp}` (`save` via `dbf_create` + `DbArea` append; `load`
  via `DbArea` read), and `USER SAVE/LOAD/VERIFY`. `VERIFY` is the in-engine APH-5 proof:
  counts + user id/key/profile + **every member × permission `authorize()` verdict** must
  match after a save→reload. In-engine result: `USER VERIFY: PASS — 20/20 decisions agree`.
- **2b-iii — boot adoption + degraded read-only startup.** `identity_store()` is now
  DBF-authoritative: `boot_identity_store()` loads from DBF if present, seeds-and-persists if
  absent, and falls back to a **read-only** seed if the tables are corrupt (without
  overwriting them). Added `StoreOrigin` reporting and `USER STORE`. In-engine result: first
  launch `SEED (persisted)`, restart `DBF (authoritative)` — the SEED→DBF flip is the
  adoption proof. The corrupt→`DEGRADED (read-only seed)` path is g++-proven in-sandbox.

## Method note — sandbox proof before build

Both milestones were proven against the **real** `dbf_create` + `DbArea` + identity code
compiled under g++ in the sandbox *before* the MSVC build, so each build was confirmation
rather than a guess. This caught the one real bug directly: **`findFieldCI` is 0-based and
returns `-1` for not-found, while `DbArea::get/set` are 1-based (slot 0 unused).** The store
used the raw index and rejected index 0 — every table's first column, `ID`. Fix: `+1` with a
`< 0` not-found test. A g++ harness dumping `DbArea` field state made this unambiguous.

## Durable records

| Surface | Change |
| --- | --- |
| `include/identity/identity_schema.hpp` | Nine `SYS*` table schemas (pure data). |
| `include/identity/identity_dbf_store.{hpp,cpp}` | Save/load + `default_identity_dir()`. |
| `include/identity/identity_bootstrap.{hpp,cpp}` | `boot_identity_store()` + `StoreOrigin` + provenance accessors. |
| `src/cli/cmd_user.cpp` | `USER SAVE/LOAD/VERIFY/STORE`. |
| `src/cli/cmd_regression.cpp` | `IDENTITY_PERSIST` regression registered (array 20→21). |
| `dottalkpp/data/scripts/dotscript/identity_persistence_regression.dts` | Round-trip proof script. |
| `docs/maintenance/IDENTITY_RBAC_MANAGEMENT_LANE_V1.md` | Milestone status block. |
| `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | This Session Log row. |

## Boundaries preserved

- Boot path change is contained to `identity_bootstrap.cpp`; no other subsystem's startup changed.
- The written `SYS*.dbf` catalogs under `data/metadata/identity/` are runtime data, not committed.
- Mutation of identity at runtime (`USER ADD` / `ROLE ASSIGN` / `GRANT`) is **not** yet built — the store is writable but the admin surface is the next burn.
- `C:\x64base`, the website, and x64base.com were not touched.

## Validation

- In-engine `REGRESSION RUN IDENTITY_PERSIST`: `USER VERIFY: PASS (20/20 decisions agree)`.
- In-engine `USER STORE`: `SEED (persisted)` (first boot) → `DBF (authoritative)` (restart), identical counts 4/4/7/14/34/4/0/0/1.
- Sandbox g++ proofs against real xbase code: `IDENTITY-2BII-ROUNDTRIP:PASS`, `IDENTITY-2BIII-BOOT:PASS` (missing→SEED, present→DBF, corrupt→DEGRADED read-only).
- Each commit passed `tools/staging/prepush_gate.py`.

## Review gate

APH-5 is closed for the DBF round-trip and degraded read-only startup. The `x64base → YAML →
x64base` portable-export leg (M5) and the runtime mutation surface remain for review/next
milestones.
