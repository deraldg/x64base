---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-002
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session
    scope: >
      AIF-112 Phase-1 Step 0 (discover) and Step 1 (reuse audit), executed against
      the live runtime and then verified at source level with src/ and include/
      mounted read-only. Scopes the I5 lock-release defect against this lane.
      No source mutation. No registry mutation. No ledger created.
  report:
    path: docs/maintenance/AIF112_SOURCE_REUSE_AUDIT_AND_I5_SCOPING_V1.md
    kind: evidence_note
  amends: AIPR-20260815-COWORK-001
  primary_topics:
    - "AIF-112"
    - "reuse audit"
    - "xbase_locks"
    - "I5 scoping"
    - "documentation drift"
---

# AIF-112 -- Source-Level Reuse Audit and I5 Scoping

**Report id:** AIPR-20260815-COWORK-002
**Date:** 2026-08-15
**Author:** member.ai.claude.cowork (scribe, local tree access)
**Owner:** member.derald
**Lane:** AIF-112
**Status:** review-needed; evidence note
**Amends:** AIPR-20260815-COWORK-001 (prior-art inventory) -- see section 4, which
corrects that report's framing of I5.

**Evidence class:** `source-defined` for every claim below (file:line quoted from a
read-only mount), plus `runtime-observed` for the Step 0 command surface (live
instance, CLI session 2026-08-15). The Step 2 live probe has NOT been run.

ASCII only. No src/** mutation.

---

## 0. Headline

Three findings, in descending order of consequence for this lane.

1. **I5 does not block AIF-112.** The defect applies to locks held across
   operations by the user-facing `LOCK` command. The inventory ledger holds no
   such lock -- it takes a transient table FLOCK around a check-and-append and
   releases it in the same scope, via a destructor. This corrects COWORK-001,
   which promoted the I5 probe to the Phase-1 headline.
2. **The recovery story is worse than I5 states, in a different lane.**
   I5 says a leaked lock is clearable by "nothing but `FORCE UNLOCK`."
   `force_unlock_table` and `force_unlock_record` exist in the engine and are
   called by nothing. Neither is reachable from any command. Together with
   `release_held`, that is **three dead recovery functions**.
3. **Seven published SET options do not exist.** `SET EXCLUSIVE`,
   `SET MULTILOCKS`, `SET SAFETY`, `SET EXACT`, `SET ESCAPE`, `SET CARRY`,
   `SET CONFIRM` are documented on the live public site as "current documented
   surfaces" and are absent from both the runtime and `src/cli/cmd_set*.cpp`.

Findings 2 and 3 are outside AIF-112 and are recorded here for routing.

---

## 1. Step 0 -- runtime surface (runtime-observed)

Live CLI, instance banner `dottalk++ v0.6 (2026-08-15, fb7106e0 dirty)`, built
`Aug 15 2026 10:20:17`, SQLite 3.50.4.

```
LOCK            LOCK <n>        LOCK ALL
LOCK STATUS     LOCK TABLE      LOCK WHO <n>

UNLOCK          UNLOCK <recno>  UNLOCK ALL      UNLOCK TABLE
```

`LOCK STATUS` reports table and current-record lock state. `LOCK WHO <n>`
reports the owner of record n when a lock is recorded. `LOCK` requires an open
table except for `LOCK USAGE`.

**Baseline note.** The binary is stamped `fb7106e0 dirty`, which is neither the
branch tip nor a clean tree. Evidence runs must record the banner stamp, not
`git rev-parse HEAD`.

**Not present:** `SET EXCLUSIVE`, `SET MULTILOCKS` -- both fell through to the
generic SET usage listing. See section 5.

---

## 2. Step 1 -- the lock API (source-defined)

`include/xbase_locks.hpp`. Owner-aware API plus back-compat shims:

```
try_lock_table  (DbArea&, const Owner&, std::string* err)
unlock_table    (DbArea&, const Owner&, std::string* err)
is_table_locked (const DbArea&, std::string* owner_out)

try_lock_record (DbArea&, uint64_t recno, const Owner&, std::string* err)
unlock_record   (DbArea&, uint64_t recno, const Owner&, std::string* err)
is_record_locked(const DbArea&, uint64_t recno, std::string* owner_out)

force_unlock_table (DbArea&, std::string* err)      // admin / recovery
force_unlock_record(DbArea&, uint64_t, std::string* err)
release_held       (DbArea&)                        // "cleanup any locks
                                                    //  created by this process"
```

Record numbers are 64-bit (RECNO64 lane). Back-compat shims behave as
`current_owner`.

**There is exactly one locking surface.** `src/cli/cmd_security.cpp` (329 lines)
contains zero occurrences of `lock`, `FLOCK`, or `RLOCK`; its header declares
`command: SECURITY`, `category: diagnostics`, `mutates: none`. `FLOCK` and
`RLOCK` appear only as `RELATED:` comment lines in `cmd_unlock.cpp` -- they are
not commands. Nothing to reconcile; no Rule-of-Three conflict.

---

## 3. The two classes of lock acquisition

Every call site outside `xbase_locks.cpp` falls into one of two classes. This
distinction is the whole of the I5 scoping question.

### Class A -- transient, released in the same operation

| Site | Shape |
|---|---|
| `src/bbs/bbs_store.cpp:95,99` | RAII `TableLock`, destructor unlocks |
| `src/cli/cmd_workspace.cpp:2112,2117` | RAII `WsLock`, destructor unlocks |
| `src/cli/append_support.cpp:326/364, 416/427, 450/472, 500/525` | paired acquire/release |
| `cmd_calcwrite.cpp:712/717`, `cmd_commit.cpp:233/283`, `cmd_delete.cpp:216/259`, `cmd_recall.cpp:234/260`, `cmd_replace.cpp:773/778`, `cmd_replace_multi.cpp:697/862` | paired acquire/release around one write |

These acquire and release within a single operation. **I5 cannot leak them on a
normal path.** The RAII two (`bbs_store`, `cmd_workspace`) are additionally
exception-safe; the paired ones are not, so an early return or throw between
acquire and release would leak. That is a narrower, separate hardening item.

### Class B -- deliberately held across operations

| Site | Shape |
|---|---|
| `src/cli/cmd_lock.cpp:161, 175, 199` | owner-aware acquire, **no release anywhere in the file** |

`grep -n unlock src/cli/cmd_lock.cpp` returns nothing. That is correct by
design: `LOCK` exists to hold a lock. The only release path is the `UNLOCK`
command.

**Class B is the entire I5 exposure surface.** A user issues `LOCK`, then closes
the area without `UNLOCK`. The lock sidecar survives with a live pid. Nothing
in-process releases it (`release_held` is never called); the stale reaper does
not fire (`if (!is_pid_alive(meta.pid))`, `xbase_locks.cpp:244`); and the
owner-aware `unlock_table` will refuse a non-matching owner.

---

## 4. I5 scoping -- and a correction to COWORK-001

### 4.1 I5 is verified, exactly as written

All three limbs confirmed at source:

- `release_held` -- declared `include/xbase_locks.hpp:59`, defined
  `src/xbase/xbase_locks.cpp:407`, and **called from nowhere in the tree**
  (two total occurrences).
- `current_owner()` is a process singleton:
  ```cpp
  const Owner& current_owner() {
      static Owner g_owner{ make_owner_string() };
      return g_owner;
  }
  ```
  Owner string is `host:pid:ms`.
- The stale reaper fires only on a dead pid:
  ```cpp
  // Stale lock: owner process is gone.
  if (!is_pid_alive(meta.pid)) {      // xbase_locks.cpp:244
  ```
  Same test at `:315` and `:321` on the table path.

The design doc's line numbers were exact.

### 4.2 But it does not block this lane -- COWORK-001 was wrong on this

COWORK-001 promoted the I5 probe to "the Phase-1 headline" and said the defect
"means exclusive check-out cannot be made recoverable without an engine change."

That reasoning assumed a check-out might be expressed as a **held engine lock**
-- a Class B acquisition. It should not be, and under the amended D1 it is not.
A check-out is an `INVCHKOUT` row. The engine lock is used only as the write
primitive around the check-and-append: acquire, scan, append, release, all in
one scope. That is Class A, and Class A is not exposed to I5.

Concretely: `WsLock`'s destructor calls `unlock_table` explicitly rather than
relying on area close. The pattern already routes around I5 instead of depending
on a fix. `INVCHKOUT` inherits that for free.

**Revised position.** I5 is real, verified, and worth a lane. It is not an
AIF-112 blocker, and Step 2 should be demoted from "headline that outranks the
proof bar" to "useful evidence, collected opportunistically, routed elsewhere."

### 4.3 The recovery story is worse than I5 states

I5 says a leaked lock is clearable by "nothing but `FORCE UNLOCK`." Measured:

- `force_unlock_table` (`xbase_locks.cpp:386`) and `force_unlock_record`
  (`:393`) exist and are **called by nothing** -- the only other occurrences are
  their declarations at `xbase_locks.hpp:55-56`.
- `cmd_unlock.cpp` handles `ALL` and `TABLE` (`:114`) and routes both to the
  owner-aware `unlock_table`. There is no `FORCE` verb.

So a leaked live-pid lock owned by another process is clearable by **no exposed
command**. Recovery requires killing the owning process or removing the sidecar
by hand. Three engine functions -- `release_held`, `force_unlock_table`,
`force_unlock_record` -- are dead code that together constitute the entire
designed recovery path.

That belongs in the engine lane with I5, not here.

---

## 5. Documentation drift (routing item, not AIF-112)

`content/docs/dottalk/set-family.mdx` publishes, under the heading
"Data and editing behavior -- Current documented surfaces include:", a plain
code block containing eleven settings. Measured against
`src/cli/cmd_set*.cpp`:

| Setting | In source |
|---|---|
| `SET TABLE BUFFER`, `SET DELETED`, `SET CASE`, `SET NEAR` | present |
| `SET SAFETY` | ABSENT |
| `SET EXACT` | ABSENT |
| `SET ESCAPE` | ABSENT |
| `SET CARRY` | ABSENT |
| `SET CONFIRM` | ABSENT |
| `SET EXCLUSIVE` | ABSENT |
| `SET MULTILOCKS` | ABSENT |

Seven of eleven do not exist, with no status qualifier on the block. This is
live on the public site. It is the `VDISK CEIL` pattern named in
`BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md` ("a config surface exists but whose
enforcement is ABSENT"), one rung thinner -- here there is not even a config
surface, only a published claim.

---

## 6. The template AIF-112 copies

`src/cli/cmd_workspace.cpp`, runtime-proven 2026-08-11.

### 6.1 The guard (`:2105-2121`)

```cpp
// RAII whole-table lock; the bbs_store idiom (cross-process FLOCK,
// pid-stamped, stale-owner recovering). Appends grow the header, so
// whole-table granularity is correct.
struct WsLock {
    xbase::DbArea& a; bool held = false;
    WsLock(xbase::DbArea& area, std::string& err) : a(area) {
        held = xbase::locks::try_lock_table(a, &lerr);
        ...
    }
    ~WsLock() { if (held) xbase::locks::unlock_table(a); }
};
```

`InvLock` is the same three lines against the inventory catalog.

### 6.2 The atomic check-and-append (`:2336-2360`)

One scan under the FLOCK does two jobs: allocate `max(WS_ID)+1`, and supersede
any prior live row of the same name while remembering its id as `PREV_ID`.

For `INVCHKOUT` the analogue is exact: under the FLOCK, scan for `max(ID)` and
for any row with this `ITEMID` where `STATE=Held`; refuse if one exists and the
request is exclusive; otherwise append. **The refusal is enforced because the
check and the insert share one lock scope.** A SELECT-then-insert without the
FLOCK is the weak form; this is the strong one, and it needs no new locking code.

### 6.3 A live engine gap this pattern documents

From the same comment block: the x64 header slot `autoq_next` exists
(`xbase_64.hpp:52`, init 1 at create, hydrated at open `:530`) but is
**load-only** -- no append consumer, no increment, no store path back to the
header. Wiring those three is described as "a chartered engine lane." Until it
lands, `max(id)+1` under the FLOCK is the sanctioned pattern, "self-healing
after any manual edit and forward-compatible with the autoq wiring."

`INVCHKOUT` should use `max(id)+1` under the FLOCK and inherit the eventual fix.

### 6.4 Attribution

```cpp
static std::string author_stamp() {
    std::uint64_t id = 0; int kind = 0;
    try { dottalk::identity::current_member(id, kind); } catch (...) {}
    return "member#" + std::to_string(id) + "/kind" + std::to_string(kind);
}
```

Note this is a **string stamp**, not a foreign key. The `INVITEM.CREATEDBY` /
`INVCHKOUT.MEMBERID` proposal in COWORK-001 used `N(20)` FK to `SYSMEMBER`,
which is stricter than the existing precedent. Owner ruling needed: match the
precedent or normalize and be first.

---

## 7. Permission gating -- the template

`src/cli/cmd_net.cpp` is the model for `inv.break`:

```cpp
#include "identity/identity_admin.hpp"   // agent_permitted, acting_member_key
constexpr const char* kPerm = "host.network.egress";
```

Header contract: "OPEN/CLOSE require RBAC permission `host.network.egress`
(Critical, requires_approval) AND `DOTTALK_ALLOW_HOST_COMMANDS`. Owner
(role.maintainer) is exempt; AI members are denied."

Swap the constant to `inv.break` and the shape is done.

**Status caveat.** `USER` (`src/cli/cmd_user.cpp`, 485 lines) is
`status: experimental`; `BBS` and `NET` are `status: supported`. AIF-112 binds
attribution and permission gating to the identity stack, which means binding a
would-be supported feature to an experimental surface. Name this at the next
gate rather than discovering it at promotion.

---

## 8. A projection precedent worth adopting

`src/cli/cmd_bbs.cpp` header: "The read-only `board.governance` **projects the
identity SYSGRANT request/approve loop as posts**."

That is projection-not-migration already in production: a durable catalog
rendered onto the board as a read-only view. `INVCHKOUT` can project the same
way, making "who holds what" visible over existing transport with no new
surface. It also partly answers the `PROOF_CURATION_LANE_V1` objection quoted
in COWORK-001 section 7.

---

## 9. Revised Phase-1 questions

Superseding the COWORK-001 ordering:

1. Does check-and-append under a table FLOCK correctly refuse a second exclusive
   acquire on a held `ITEMID`? (Expected yes -- the `WsLock` supersede path is
   the same shape and is runtime-proven.)
2. Does `EXPAT` lease reclaim work without any force path? (Sharper now that
   `force_unlock_*` is confirmed unreachable -- the ledger must not need one.)
3. Does `REF` carry a capsule identifier with nothing downstream assuming a
   filesystem path?
4. Does the SQLite oracle agree with the final `INVCHKOUT` state?

**Demoted:** the I5 probe. Still worth running, but as evidence for the engine
lane, not as an AIF-112 gate.

---

## 10. Open -- owner ruling required

Carried from COWORK-001, plus new:

1. Ratify or reject the D1 amendment (SQLite carrier -> DBF carrier).
2. Ratify or reject the D3 clarification.
3. Confirm the ledger is runtime state, excluded from Git.
4. Confirm `inv.break` is maintainer-only, on the `cmd_net.cpp` model.
5. **New:** attribution as string stamp (match `WORKSPACES`) or `N(20)` FK to
   `SYSMEMBER` (normalize)?
6. **New:** open an engine lane for the three dead recovery functions
   (`release_held`, `force_unlock_table`, `force_unlock_record`) plus the
   `LOCK`-command leak. Not AIF-112.
7. **New:** open a documentation lane for the seven non-existent SET options
   published on the live site. Not AIF-112.
8. **New:** accept or amend the demotion of the I5 probe (section 4.2).

---

Lane: AIF-112. Owner: `member.derald`. Author: `member.ai.claude.cowork`.
Evidence class: `source-defined` (file:line quoted) + `runtime-observed`
(Step 0 only). Risk class: low (read-only survey; no mutation).
Next gate: owner ruling on items 1-8, then the revised Phase-1 run.
