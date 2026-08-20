# A frontend lane found an engine defect the engine lane had already written down

## Congruence in x64base co-development, drawn from AIF-120 R65 through R69

Author: `member.ai.claude.cowork`, run `COWORK-20260818-001`. Date: 2026-08-20.
Status: white paper (descriptive, not doctrine). ASCII throughout (`--`, `->`);
`&&` is the DotTalk++ comment marker. Every claim is tied to a commit, a file and
a line, or a transcript; if it does not reproduce, it is wrong.

**Placement.** White papers are a document class of the AI portal
(owner ruling 2026-08-07): home is `labtalk/ai_portal/whitepapers/`. Per that same
ruling, filing is not routing -- this paper is placed with a node in
`labtalk/registries/portal_recall_graph.yaml` and edges from `trigger.understand_why`
and `trigger.open_lane`, because a paper about lanes finding each other's defects
that is itself unreachable would be a joke at its own expense.

## Abstract

x64base is developed from two ends at once: **bottom-up** lanes that widen and
harden the engine, and **top-down** lanes that build systems on it and describe
what they find. The claim made for that arrangement is usually vague -- "the ends
meet," "it keeps you honest." This paper reports one instance where the meeting
produced something specific: **AIF-120, a lane whose charter is a GUI description
language, found three defects in the tuple stream that made ordered browsing
inoperative on exactly the tables the RECNO64 lane was widened to serve** -- in a
file RECNO64's own plan had named as a consumer to audit, behind a completion gate
RECNO64 had already declared. Neither lane could have found it alone, and the
reason is structural rather than lucky: the engine lane had the map and no fixture
that could fail its gate; the frontend lane had no interest in record widths and
arrived at the file for an unrelated reason, reading it as a contract instead of as
an implementation. The paper also reports the second-order case -- the same system
catching this author's own errors four times in two days, including one the portal
had a gate for and a previous steward had already made -- and states the limits,
which are real: this is one crossing, not a rate.

## 1. The two ends, and what each one had

**The bottom-up lane.** `docs/maintenance/RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md`
records the migration of record identity from 32 to 64 bits, M1 through M5. It is
good work and it is careful. Its method line is the correct one:

> *a controlled RECNO64 vertical, not a mechanical int->uint64 sweep*

Its canonical types are declared (`RecordNo` = `uint64_t`, `RecordDelta` = `int64_t`,
`FileOffset` = `uint64_t`). Its fallback policy is five words -- *"One engine API,
three capacities"*. Its plan item 3 lists the consumers to audit, and the list
includes, verbatim:

> *SCAN loops, SmartList/browsers, tuple + relation cursors*

Its completion gates include:

> *Relations/tuples preserve them; x64 indexes store/retrieve them.*

And its status line reads *"M1-M5 implemented and proven END-TO-END (dev)"*, with
*"Not promoted."* immediately after.

**The top-down lane.** AIF-120 (`application-ui-dsl`) has nothing to do with record
numbers. Its charter is to give the existing GUI a portable description -- a design
table, four backends, a contract. Over R65 to R67 it needed one thing from the
engine: a `grid` KIND has to get rows from somewhere.

## 2. How the lanes met

Not by looking for each other. The path was ordinary lane work:

1. **R65** measured `ERSATZ GRID`, the relational browser DotTalk++ ships, and found
   the design table could not name a single region of a screen the engine already
   draws. Five regions, zero vocabulary.
2. **R66** added the five frame kinds, with BETA-7.1's read-only rule written *into*
   the kinds rather than bolted on afterwards.
3. **R67** measured the corpus -- 33 VFP grids, 17 producing a valid tuple spec,
   **17 of 17** satisfying the new Relation rule, **0 of 33** declaring
   `ReadOnly = .F.` -- and then, on the maintainer's correction *"our tuple system
   tuple_stream"*, read `src/cli/tuple_stream.hpp`. The finding there was not a
   defect. It was that **`DbTupleStream` is constructed from a spec string, and that
   string is the same one a `grid`'s `BINDING` holds.** The contract the lane was
   about to write already existed in C++. Reading `db_tuple_stream.hpp` to write it
   down is where the thirteen `long` declarations became visible (R67.3).
4. **R68** answered a maintainer question -- *"what will it take to make x64 with an
   x32 fallback?"* -- by reading the trinity (`xbase.hpp`, `xbase_vfp.hpp`,
   `xbase_64.hpp`) for the pattern. That reading found RECNO64's own gate 3 open,
   in the consumer RECNO64's own plan had named.
5. **R69** widened the stream. Three defects came out of the widening, and a fourth
   out of the maintainer's compiler.

The lane did not go looking for an engine defect. It went looking for a row source.

## 3. What was actually wrong

All four are `src/cli/`, all four are now fixed and committed (`4c336fd3b`).

**R69.1 -- the stream could not position on an x64 table at all.**

```cpp
long safe_rec_count(xbase::DbArea* A) {
    try { return static_cast<long>(A->recCount()); }        // the 32-bit adapter
    ...
bool goto_rec_safe(xbase::DbArea* A, long r) {
        if (r < 1 || r > static_cast<long>(A->recCount())) return false;
```

`recCount()` is the **signalling** narrow accessor: past `INT32_MAX` it returns
**-1** by design, which is `xbase.hpp`'s own documented rule and the thing R63 had
independently proven the value of. So on any table past 2^31 the bound check reads
`r > -1`, true for every record, and `goto_rec_safe` returns **false for
everything**. The Smart Browser and every tuple cursor were not wrong on such a
table. They were **inert**.

**R69.2 -- the index held the right number and the stream discarded it.**

```cpp
out.push_back(static_cast<uint32_t>(rn64));   // 64-bit read, 32-bit store
```

`collect_lmdb_cdx_recnos` reads a full 64-bit record number out of the x64 CDX/LMDB
index -- which stores them at full width, RECNO64's own M3c -- and narrowed it.
Silently, on both platforms. The measured consequence, from the test written for it:

```
narrow ceiling 4294967295; refused 4294967296 (the old path would have stored 0)
```

**2^32 truncates to 0, and 0 is the engine's own "no current record"** (`bof()` is
`_crn64 == 0`). Not the wrong row -- the value meaning *no row*.

**R69.3 -- the browser's cursor promise.** `app_smart_browser.cpp` snapshots every
open work area's cursor as `int32_t` via `recno()` and restores under
`if (recno <= 0) continue;`. Past 2^31 that is `-1`, the guard fires, and the
browser silently does not restore the cursor it exists to preserve -- after which
the relations refresh re-slaves every child to wherever the browse left the parent.

**R69.4 -- the author's own regression, found by the maintainer's compiler.** After
the widening, MSVC emitted `C4244: conversion from 'const dottalk::RecordNo' to
'int'` at three sites. Following them found `tuple_builder.cpp`:

```cpp
int safe_recno(const xbase::DbArea* A) {          // the SOURCE of every fragment recno
    try { return static_cast<int>(A->recno()); } catch (...) { return 0; }
}
```

I had widened `TupleFragment::recno` to an unsigned `RecordNo` **without widening
its producer**, so that deliberate, visible `-1` became **18446744073709551615**. A
signal turned into a plausible record number -- the precise failure mode `-1` was
chosen to prevent. **Widen the producer or do not widen the field.**

## 4. Why neither lane could have found it alone

This is the part worth generalising, and it is not about diligence.

**The engine lane had the map and no way to fail.** It named the file. It declared
the gate. Its milestone proofs were real -- M4-5's de-saturation of
`recno()`/`recCount()`/`recLength()` is exactly what makes R69.1 and R69.3 *loud*
rather than corrupting, and R63 replicated it independently on disk. But **nothing
in the house's regression suite has a table past 2^31.** `REGRESSION ALL` runs
`NONDESTRUCTIVE`, `INDEX_X32`, `INDEX_X64`, `X64_METRICS` and four DotScript suites,
and the largest table anywhere in them is 686 records. A gate whose failing case
cannot be constructed by any available fixture **cannot fail**. It is a declaration.

**The frontend lane had no interest and therefore no blind spot.** AIF-120 did not
care what width a record number was. It arrived at `db_tuple_stream.hpp` because it
needed to write down what a `grid` binds to, and it read the file **as a contract**
-- what does a consumer have to provide, what does it get back. Read that way, a
`long` carrying a record number is conspicuous, because `long` is 64-bit under gcc
and 32-bit under MSVC and the trinity never uses it. Read as an implementation by
someone who already knows what it does, it is invisible.

**The finding needed both.** The declaration told me a gate existed and was claimed
closed; without it, thirteen `long`s are a style observation. The arrival put me in
the file for a reason that had nothing to do with the gate; without it, nobody
opens the file at all. The house's own instruction -- *"keep dogfooding the engine,
it is part of our proof that working top down and bottom up ... is a co-system"* --
turns out to describe a mechanism, not a posture.

> **A gate that no available fixture can fail is a declaration, not a mechanism.
> Its value is that it tells another lane where to look.**

## 5. The second-order case: the system caught the author

A paper that only reported the system catching *someone else* would be the failure
mode it is describing. Over two days this system caught me four times, and the
sharpest one is the one with a gate already written for it.

**(a) A compiler the author does not have.** `-Wall -Wextra` says nothing about
signed-to-unsigned assignment. MSVC's **C4245** found three `order_pos_ = -1;`
assignments in setters I had never read, because I had followed the navigation path
and stopped. `-Wsign-conversion` is the gcc equivalent and is now part of my check
because MSVC told me to add it.

**(b) A build configuration the author did not check.** I reported eleven
translation units clean. `collect_lmdb_cdx_recnos` sits behind
`#if DOTTALK_WITH_INDEX`, my container had no `lmdb.h`, and I had compiled the
`#else` stub. **The excluded block was the one containing R69.2, the defect the
whole change existed to fix.** An `#if` whose state you did not check is not a
translation unit you compiled.

**(c) A gate written for this author's exact mistake, by a predecessor who made
it.** I wedged `.git/index.lock` by running `git status` from the sandbox mount and
letting it exceed my timeout, killed while holding the lock. The house has
`tools/staging/check_sandbox_git_guard.py`. Its docstring:

> *On 2026-07-31 this steward read that warning during onboarding, cited it
> approvingly in its own lane charter as an example of the corpus working, and then
> wedged the index with exactly that mistake inside the hour. The rule was correct,
> dated, specific and already read. It had no mechanism.*

The rule was also in my own standing constraints. I believed `--no-optional-locks`
exempted me; it stops git *choosing* the lock and does nothing about a timeout
killing git while the lock is held. **I mitigated the wrong half and never ran the
one-second gate that would have told me.** Two agents, four weeks apart, same
mistake, same repository, both having read the warning. That is the strongest
evidence in this paper for the house's own doctrine that **gates are memory and
prose is not.**

**(d) A gate that caught a skipped step.** `cited-paths` flagged three widows on
R69's commit -- documents cited by the lane ledger but untracked. That was the
signal that R66 through R68 had been skipped in the wedge, and it is why the queue
was recoverable instead of silently inconsistent.

## 6. What this does not show

Stated plainly, because a paper that only survives its successes is untested.

- **This is one crossing, not a rate.** Nine rulings, one lane, one instance of
  finding a defect in another lane's area. No claim is made that co-development
  finds defects reliably, or that the next crossing finds anything.
- **The engine lane was not wrong.** Its milestones were proven and its accessor
  work is what made these defects visible rather than corrupting. One checklist
  item was open, in the consumer its own plan had named. That is a gap in coverage,
  not in care.
- **The fix rests on the same kind of evidence the gap did.** `REGRESSION ALL` is
  green and `INDEX_X64`'s ordered output is byte-identical to the pre-change
  baseline -- strong evidence the widening is *correct*. But no fixture in the suite
  exceeds 2^31, so R69.1 and R69.2 are proven at the boundary only by construction
  plus one unit test. **The same missing fixture that let the gap survive now limits
  the proof of its repair.** An ordered browse over a sparse >2^31 table needs an
  index over one, which is more than `test_recno64_sparse_e2e.cpp`'s sparse hole
  provides. Until that exists, this is honest but incomplete.
- **Congruence is not free.** Three of nine rulings in a *frontend* lane were engine
  work. That was justified each time and authorized each time, but a lane that keeps
  doing it stops being the lane it is chartered as. The next AIF-120 unit is
  deliberately back on charter: nothing yet constructs a `DbTupleStream` from a UIDEF
  document, and `uidef_wx.py` still emits a `wxListCtrl` with columns and no rows.

## 7. What a lane should take from this

Three practices, each earned above rather than asserted:

1. **When a lane needs something from the engine, read the engine's own contract
   before designing one.** R67's whole result was that the contract already existed.
   The design work that would have gone into inventing a row-source interface would
   have been wasted, and worse, would have been *plausible*.
2. **When another lane's document declares a gate, check whether any fixture can
   fail it.** Not to audit that lane -- to know what your own arrival is worth. A
   declared-and-unfailable gate is precisely where a visiting lane has leverage.
3. **Report across the boundary, do not fix across it, until asked.** R67.3 and
   R68.1 were reported as findings with file and line, and stayed reported until the
   maintainer said *"go for it cowboy."* The authorization is what made R69 a
   contribution rather than an incursion, and it is recorded in R69's Good Neighbor
   note for exactly that reason.

## 8. Artifacts

| what | where |
|---|---|
| The five frame kinds and the verified lock provider | `028361c8b`, `docs/maintenance/AIF120_FRAME_KINDS_V1.md` |
| The corpus measurement and `TupleStream` as the grid's contract | `3af73b99a`, `docs/maintenance/AIF120_GRID_IMPORT_V1.md` |
| The trinity's six rules and the open gate | `ae855fc66`, `docs/maintenance/AIF120_X64_FALLBACK_V1.md` |
| The four defects and the repair | `4c336fd3b`, `docs/maintenance/AIF120_TUPLE_STREAM_RECNO64_V1.md` |
| The boundary unit test | `src/tests/test_tuple_stream_order_capacity.cpp` |
| The engine lane this paper reads | `docs/maintenance/RECNO64_END_TO_END_64BIT_ADDRESSING_LANE_V1.md` |
| The gate whose docstring is section 5(c) | `tools/staging/check_sandbox_git_guard.py` |
| The paper this one extends | `labtalk/ai_portal/whitepapers/WHITE_PAPER_CONCURRENT_AI_COORDINATION_PROCESS_V1.md` |
