---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-076
  recorded_at_utc: 2026-08-20T19:30:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 8145e0880
  authorization:
    requested_by: maintainer (member.derald), in-session "what will it take to make
      x64 with an x32 fallback?? Use the engine for an example, the trinity headers
      xbase.hpp xbase_vfp.hpp and xbase_64.hpp in include".
  report:
    path: docs/maintenance/AIF120_X64_FALLBACK_V1.md
    kind: ruling
---

# AIF-120 -- R68: what an x64-with-x32-fallback costs, read out of the trinity, and the gate the house already wrote

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

**Short answer: about four files and twenty declarations, and no new design.** The
engine has done this exact migration once, wrote down its method, and left the piece
R67.3 found. The trinity is not three files -- it is six rules, and they are already
written in the headers.

## 1. The trinity's six rules, read out of the headers

**R1. The fallback is a LAYER, not a build switch.** The include direction is
one-way and names the authority: `xbase_64.hpp` includes `xbase_vfp.hpp` includes
`xbase.hpp`. The neutral core knows neither dialect. There is no `#ifdef X64`
anywhere in the three files. `xbase_64.hpp`'s own header comment states the division:

> *xbase.hpp remains neutral and stores only resolved runtime truth. xbase_vfp.hpp
> remains the classic/VFP descriptor bridge. xbase_64.hpp owns x64 extension
> structures, x64 vector metadata, fallback descriptor policy, and name resolution.*

**R2. The core stores resolved truth, in the widest type, unconditionally.**
`_crn64`, `_rec_count64`, `_record_length64`, `_data_start64` are all `uint64_t`
members of `DbArea`. **There is no 32-bit storage anywhere in the core.** Narrowness
appears only at an accessor, never at a member. That is the rule that makes the rest
cheap: there is one value, and the question is only who is allowed to look at it.

**R3. The narrow accessor SIGNALS; it does not clamp.** `recno()`, `recCount()`,
`recLength()` return **-1** past `INT32_MAX`, and `xbase.hpp` says why in prose:

> *the old saturating behavior returned INT_MAX, which reads as a valid record*

R63 measured what this buys: the wrong accessor wrote `.lock.-1` on disk, one
colliding file per record past 2^31, instead of a plausible `.lock.2147483647`.

**R4. The narrow ENTRY POINT is an adapter, not a second implementation.**

```cpp
bool gotoRec(int32_t recno);          // 32-bit compatibility adapter -> gotoRec64
bool gotoRec64(std::uint64_t recno);  // authoritative 64-bit record positioning
```

One implementation at the widest type; the narrow signature forwards. The code path
is never forked, so the fallback cannot drift from the primary.

**R5. Outward narrowing SATURATES and carries an agreement predicate.** Where a
narrow value must be written for a foreign reader, `xbase_64.hpp` pairs them:

```cpp
inline std::uint16_t x64_compatible_u16_mirror(std::uint64_t value);        // -> 0xFFFF
inline bool x64_compatible_u16_matches(std::uint16_t mirror, std::uint64_t wide);
```

with `mirror == 0` meaning *"not written, no claim"*. **So there are two narrowing
policies and the direction chooses:** inward to our own consumer, signal (R3);
outward to someone else's format, saturate and record whether it still agrees.

**R6. Fallback covers NAMES and METADATA. Never STRUCTURE.** Stated flatly:

> *Missing metadata falls back to descriptor tokens; invalid x64 structural headers
> still fail rather than pretending to be x32.*

`x64_resolve_field_name_or_fallback(flags, metadata_name, fallback_name)` takes the
metadata name only if the flag says it is there **and** it fits; otherwise the 10-byte
descriptor token. A flag test, never a guess.

And underneath all six, one detection: `detect_area_kind_from_version(uint8_t)` is
the **only** version-byte mapping, producing `AreaKind{Unknown, V32, V64, V128, Tup}`
with `AreaCapability` as a bitset. The enum was built with room, and it already
contains `Tup` and `TupleOps` -- the house anticipated a tuple area before there was
one.

## 2. The house has already answered this question

`docs/maintenance/RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md` is the migration,
M1 through M5, and its method line is the whole answer to "what will it take":

> *a controlled RECNO64 vertical, not a mechanical int->uint64 sweep*

Its canonical types:

```cpp
using RecordNo    = std::uint64_t;  // identity
using RecordDelta = std::int64_t;   // signed for backward movement
using FileOffset  = std::uint64_t;
```

And its fallback policy, in five words: **"One engine API, three capacities."**
Classic and VFP physical formats are unchanged and use the widened runtime API *at
their natural capacity*.

The x32 fallback is therefore **not a narrow code path**. It is a **capability
report**. M4-4 is the template: `IIndexBackend::maxRecordNumber()` defaults to
`UINT64_MAX`, `CnxBackend` overrides it to `UINT32_MAX` because classic CNX stores
recnos in four bytes, and `IndexManager` exposes `recordNumberFitsBackend(RecNo)`.
Nothing narrows. A backend states its ceiling and a caller asks.

## 3. R68.1 -- completion gate 3 is not met

**Finding, source-evidenced.** That document lists the gates for calling the work
end-to-end. The third is:

> *Relations/tuples preserve them; x64 indexes store/retrieve them.*

And its own audit list (plan item 3) names the consumers to check, including
*"SmartList/browsers, tuple + relation cursors"*. R67.3 measured those:

| site | width |
|---|---|
| `src/cli/db_tuple_stream.hpp` -- `skip`, `goto_pos`, `goto_recno`, `cur_recno_`, `max_recno_`, `last_emitted_recno_`, `order_pos_`, ... | **13 `long` declarations** -- 64-bit under gcc (LP64), **32-bit under MSVC (LLP64)**, and the shipping build is MSVC 1944 |
| `src/cli/db_tuple_stream.hpp:51` -- `order_recnos_` | `std::vector<uint32_t>` -- 32-bit on **both** platforms |
| `src/cli/tuple_types.hpp` -- `TupleFragment::recno` | `int` |
| `src/cli/app_smart_browser.cpp:78` -- the pager's cursor snapshot | `int32_t`, read via `recno()` |
| `src/cli/browse/browse_order.hpp:22,30` -- `recnos`, `goto_recno` | `std::vector<uint32_t>`, `uint32_t` |

The document's status line says *"M1-M5 implemented and proven END-TO-END (dev)"*.
It also says *"Not promoted"*, and M4-5's proof was about the **accessor**, which is
real and was proven. **The gate is a checklist and one item on it is measurably
open** -- and it is open in exactly the place the plan predicted it would be.

`long` is the tell, and it is worth naming on its own. The trinity never uses it:
`int32_t`, `uint64_t`, `uint32_t`, `int`, `std::size_t` -- every width is either
explicit or deliberately a small delta. `db_tuple_stream.hpp` is the only place a
platform-dependent type carries a record number, which is why it is the one file
whose behaviour differs between the WSL build and the shipped one.

## 4. What it takes, measured

Blast radius counted, not estimated:

| file | change | size |
|---|---|---|
| `src/cli/tuple_stream.hpp` | `skip(long)` -> `skip(RecordDelta)`; add `goto_recno64` (BETA-6.1 freezes GOTO for tuple iteration and the interface has none) | **1 interface, 5 methods, 2 implementers** |
| `src/cli/db_tuple_stream.hpp` and `src/cli/db_tuple_stream.cpp` | 13 `long` -> `RecordNo`/`RecordDelta`; keep `current_pos()`/`order_count()` as **R4 adapters** that signal `-1` | **13 declarations** |
| `src/cli/app_smart_browser.cpp` | `int32_t recno` -> `RecordNo`, `a->recno()` -> `recno64()`, `gotoRec` -> `gotoRec64` | **1 struct, 3 uses** |
| `src/cli/browse/browse_order.*` | `uint32_t` -> capability-reported (see below) | **3 declarations** |
| callers outside the stream | `app_smart_browser.cpp:265-266` only | **2 call sites** |
| `include/xbase.hpp` and the trinity | **nothing** -- `gotoRec64`, `recno64`, `recCount64` already exist | **0** |

`DbArea::skip(int delta)` stays `int` on purpose: it is a **delta**, not an identity,
and the RECNO64 plan separates `RecordNo` from `RecordDelta` for exactly that reason.

### The one real design decision: the order vector

`order_recnos_` is the only place where widening has a cost worth thinking about. At
pinocchio's 5,501,358 rows an ordered browse holds 22 MB as `uint32_t` and 44 MB as
`uint64_t`, and the overwhelming majority of tables will never need the second.

**R5 answers it, and R1 says where the answer lives.** Choose the width **once**, at
`refresh_bounds_and_order()`, from the resolved `AreaKind` -- exactly as
`detect_area_kind_from_version()` chooses once from the version byte -- not per
access:

- `AreaKind::V32`: the classic header's count is 32 bits, so `uint32_t` is
  **provably sufficient**, not a compromise. This is "three capacities" working as
  designed.
- `AreaKind::V64`: wide.
- `AreaKind::Unknown`: **fail** (R6 -- invalid structure does not get to pretend).

And expose the ceiling the way M4-4 already does for indexes:
`maxRecordNumber()` / `recordNumberFits(RecordNo)` on the stream, so a caller asks
instead of a cast truncating.

## 5. What it does NOT take

Worth stating, because each of these is the expensive way and none is what the
trinity did:

- **No `#ifdef`.** The fallback is a layer (R1) and a runtime capability (M4-4).
- **No forked implementation.** Narrow signatures are adapters (R4).
- **No mechanical `int` -> `uint64_t` sweep.** The house's own word for the right
  approach is *vertical*: follow record identity through one path at a time.
- **No engine change.** The trinity already exposes everything needed.
- **No change to classic behaviour.** V32 keeps its natural capacity and its
  formats.

## 6. The lane's own C++, audited against the six rules

Dogfooding the answer: `tools/uidef/uidef_xbase_locks.h` and `tools/uidef/uidef_rt.h`
carry **no `long`, no `uint32_t`, and no `int32_t` record identity**. Every record
number goes through `a->recno64()`, with the reason on the line
(*"recno64(), not recno(): the 32-bit adapter returns -1 rather than clamping"*), and
R63 proved it on disk. The lane is clean against R2, R3 and R4, and has no R5 or R6
surface because it writes no foreign format.

That is not luck -- it is R63 having been run. The lane found this rule the
expensive way and the answer above is the same rule stated generally.

## 7. Evidence tier

**source-evidenced**, and the counts are measured: the six rules are quoted from
`include/xbase.hpp`, `include/xbase_vfp.hpp` and `include/xbase_64.hpp`; the gate and
the method from `RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md`; the widths and call
sites counted in `src/cli/`.
**planned** for section 4's proposal. **Nothing was changed.** This is an answer to a
question, and `src/cli/` is not this lane's area.

## 8. Still open

- **R68.1 is a report to the RECNO64 lane's owner, not a claim that the work was
  wrong.** M4-5's boundary proof is real and R63 replicated it. One checklist item is
  open, in the place the plan named.
- The `V128` and `Tup` entries in `AreaKind`, and `TupleOps` in `AreaCapability`, are
  declared and (as far as this reading goes) unexercised. If a tuple area is intended
  to become a first-class `AreaKind`, section 4's stream widening is the natural
  moment.
- Unchanged: R67's open items (nothing constructs a stream yet), R64.1, R64.2,
  R65.3, R65.4, R55.2, R62.2.

## 9. Good Neighbor note

- **What changed.** One new document. **No code, in any area.**
- **Whose area.** The reading is of `include/` and `src/cli/`, both outside this
  lane; R68.1 is reported to the RECNO64 lane's owner. Section 6 audits this lane's
  own files and changes nothing.
- **What authorization.** Maintainer (member.derald), in-session question.
- **How to verify or undo.** Verify: every quotation is cited to a file, and the
  counts reproduce with
  `grep -c "long " src/cli/db_tuple_stream.hpp` (13) and
  `grep -n "int32_t" src/cli/app_smart_browser.cpp` (1 declaration, line 78).
  Undo: delete the one file.

## 10. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

R65, R66 and R67 are still uncommitted; their blocks are in their own documents.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_X64_FALLBACK_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R68 -- the trinity's six rules, and what an x32 fallback costs; RECNO64 completion gate 3 is open at the tuple stream"
```
