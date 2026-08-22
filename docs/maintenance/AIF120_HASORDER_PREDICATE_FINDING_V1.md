---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-103
  recorded_at_utc: 2026-08-22T01:49:42Z
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
    baseline_commit: b521465f4
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- surfaced by
      his own REGRESSION ALL run on the 8aca9ef1 build, then written up at his
      direction after the R111/R112 push. Report only; no fix authorised.
  report:
    path: docs/maintenance/AIF120_HASORDER_PREDICATE_FINDING_V1.md
    kind: finding
---

# AIF-120 -- R113: DESCEND reports a direction it cannot apply

Status: **finding, review-needed. REPORTED, NOT FIXED. NO BUILD AUTHORISED.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `b521465f4`.

**Area:** engine (`src/cli/order_state.cpp`, `include/cli/order_report.hpp`,
`src/cli/cmd_descend.cpp`, `src/cli/cmd_ascend.cpp`). **Not this lane's code**;
this is a report to the steward, not a change.

`orderstate::hasOrder()` answers *"is a container attached"*. Four callers use it
to ask *"is an order in effect"*. Those are different questions, and they give
different answers in exactly one situation -- a container attached with no tag
selected -- which is the situation `REGRESSION ALL` walked into.

---

## 1. What the regression printed

`REGRESSION ALL` on the `8aca9ef1` build, NONDESTRUCTIVE section 13. Not a red;
the suite has no marker here. Found by reading the transcript.

    SET CDX: attached "...\INDEXES\x64\STUDENTS.cdx"
    SET ORDER: CDX '...\INDEXES\x64\STUDENTS.cdx' (ASC)
    Order: ASCENDING.
         1 50000000 Taylor    ...
         2 50000001 Martin    ...          <- physical order
         3 50000002 Ramirez   ...
    Order: DESCENDING.
         1 50000000 Taylor    ...
         2 50000001 Martin    ...          <- IDENTICAL. Nothing reversed.
         3 50000002 Ramirez   ...
    Current area: 8
      Order: DESCEND
      Active tag  :

`SET ORDER TO <container>` was given **no TAG**. There is therefore no ordering
to reverse, and none was reversed -- correctly. What is wrong is that the engine
**said** it had reversed one, and then `STATUS` **repeated the claim** beside an
empty `Active tag`.

### 1a. The counter-case, from the same run -- and it kills the obvious fix

INDEX_X32, same transcript. An **INX** container, no tag, and DESCEND works:

    SET INDEX: INX attached
      students_x32_idxtest_lname.inx
      Order: ASCEND
      Index file  : ...students_x32_idxtest_lname.inx (LNAME)
      Active tag  : (none)              <- no tag here either
    ...
    Order: ASCENDING.
    50000020 | Anderson | Taylor | ...  <- first row
    Order: DESCENDING.
    50000156 | Wilson   | Quinn  | ...  <- DIFFERENT first row. It reversed.

**So "no tag" does not mean "no order".** An INX is a single-tag container and is
an ordering by itself; a CDX or CNX container is a *collection* of tags and is
not an ordering until one is chosen. Both render `Active tag` as none/empty.

This is why the fix is **not** "guard on the tag instead" -- that would start
refusing `DESCEND` on INX, which the steward's own run proves works today and
genuinely reverses real rows. Sec 6 was rewritten after finding this.

## 1b. The input state is undocumented in every help source

`SET ORDER` as **HELP DATA** knows it, across three independent sources
(`dottalkpp/data/help/HELP_LINE.dbf`, topic `SET ORDER`, 117 rows):

    SET ORDER TO <tag>                        DOTREF
    SET ORDER TO TAG <tag> [IN <alias>]       CURATED_DOC
    SET ORDER TO 0 / SET ORDER TO PHYSICAL    CURATED_DOC
    SET ORDER TO TAG <tag> | <tag> | 0        FOXREF

**Every documented form carries a tag or returns to physical. There is no
documented `SET ORDER TO <container>` form in any of the three.**
`cmd_setorder.cpp`'s own header comment lists
`SET ORDER <container> <tag> [ASC|DESC|...]` -- container **with** tag.

The transcript reached `SET ORDER: CDX '<container>' (ASC)` with no tag. So the
state that makes the report lie is reachable through an input form that HELP does
not describe, that the command's own header describes only in its tagged variant,
and that the runtime accepts anyway.

That reframes this finding. It is not only "a predicate is too broad". It is **an
undocumented input state, unguarded, that makes the engine describe itself
incorrectly.** A fix that only corrects the predicate leaves the undocumented
form still accepted and still silent.

## 2. Why -- the predicate

`cmd_descend.cpp:87` does guard, and the guard did not fire:

```cpp
if (!orderstate::hasOrder(A)) {
    cli::cmdout::print_message(MessageId::NoActiveIndex);
    return;
}
orderstate::setAscending(A, false);
cli::cmdout::print_message(MessageId::OrderDescendingSet);
```

Because (`src/cli/order_state.cpp:71-75`):

```cpp
bool hasOrder(const xbase::DbArea& area) {
    std::lock_guard<std::mutex> lk(g_mtx);
    State* st = find_state_unlocked(area);
    return st && !st->container.empty();     // <- CONTAINER, not tag
}
```

`SET ORDER TO <container>` fills `container` and leaves the tag empty, so
`hasOrder` is **true**, the guard passes, the direction flag flips, and the
message prints. `cmd_ascend.cpp:88-93` is the exact mirror.

## 2a. HELP repeats the claim, because HELP is mined FROM the guard's comment

The DESCEND help rows are not an independent description. They carry
`SOURCE=USAGE_CONTRACT` and cite their origin:

    NOTE     DOT|USAGE_CO  DESCEND requires an active order except for DESCEND USAGE.
    NOTE     DOT|USAGE_CO  D:/code/ccode/src/cli/cmd_descend.cpp:10 pattern=usage_contract version=v1
    SUMMARY  DOT|DOTREF    Set descending sort direction for the active order/tag.

The `NOTE` is the `@dottalk.usage` block of `cmd_descend.cpp`, projected into
HELP DATA by the source miner. **So the wrong contract is stated twice from one
source** -- once as the comment above the guard, once as published help -- and
correcting the code alone leaves HELP asserting the old contract until the block
is edited and re-mined.

Two consequences:

- **The usage block IS the documentation.** A fix must edit
  `cmd_descend.cpp` / `cmd_ascend.cpp` **comment text**, not just their guards,
  or the help surface will contradict the new behaviour.
- The DOTREF summary hedges -- *"the active order/tag"*. The slash is the tell:
  whoever wrote it knew the two were not the same and wrote both.

**Coverage is otherwise clean.** All 26 index and navigation commands carry HELP
rows (ASCEND 53, DESCEND 53, SEEK 130, BUILDLMDB 287, ...); none is a help widow.
One authority disagreement worth recording separately: `cmd_seek.cpp`,
`cmd_find.cpp` and `cmd_indexseek.cpp` declare `category: navigation` in their
usage blocks, while the runtime Command Inventory prints their family as
**index** from `command_catalog`.

## 3. The report contradicts itself inside one function

`include/cli/order_report.hpp:151-171`, `print_area_one_line`:

```cpp
if (!hasOrder(a)) { os << "  Order: NATURAL\n"; return; }

const std::string tag = activeTag(a);            // <- the truth, in hand
...
os << "  Order: " << (asc ? "ASCEND" : "DESCEND") << "\n";
...
os << "  Active tag  : " << (tag.empty() ? "(none)" : tag) << "\n";
```

It computes the tag, prints `DESCEND` without consulting it, and then prints
`(none)` for the tag two lines later. **The contradiction is three lines apart in
one function**, and the information needed to avoid it is already in a local.

The neighbouring comment (`:177-180`) shows the insight was already had and the
predicate was the miss:

> "Important: direction is not the same thing as active order. `isAscending(a)`
> deliberately defaults true when no order state exists; **therefore STATUS must
> test `hasOrder(a)` before printing ASCEND/DESCEND.**"

The first sentence is right. The conclusion names a predicate that does not test
what the sentence describes.

**Minor, same neighbourhood:** the two renderers disagree on how to say
"no tag" -- `print_area_one_line` prints `(none)`, `print_status_block` prints
empty. Both appear in the same transcript (section 08 vs section 13).

## 4. The tree already has the right rule -- one layer down, written inline

**`order_nav.hpp` already implements exactly the distinction sec 1a describes**,
per container format, inside `order_first_recno`:

| line | branch | guard |
|---|---|---|
| `include/cli/order_nav.hpp:745-746` | `case CDX:` | `const std::string tagName = activeTag(area); if (tagName.empty()) return false;` |
| `:765-766` | `case CNX:` | same -- **fails closed with no tag** |
| `:775-783` | `case INX:` | **no tag check at all** -- reads first/last from the container's own metadata and applies `isAscending(area)` directly |

That INX branch is the code that makes the sec 1a listing reverse. So the engine
already knows that CDX and CNX need a tag and INX does not. **The navigation
layer has the rule; the direction and report layer does not.**

Separately, the commands that genuinely require a tag also check for one:

| file:line | guard |
|---|---|
| `src/cli/cmd_seek.cpp:255` | `... \|\| im.activeTag().empty()` |
| `src/cli/cmd_find.cpp:304` | `... \|\| im.activeTag().empty()` |
| `src/cli/cmd_indexseek.cpp:503` | `... \|\| im.activeTag().empty()` |
| `src/cli/cmd_lmdb.cpp:341,386` | `if (im->activeTag().empty())` |

So the distinction is understood in the tree. SEEK asks whether a **tag** is
active; DESCEND asks whether a **container** is attached. Note these read
`IndexManager::activeTag()` while the report path reads
`orderstate::activeTag()` -- two parallel notions of the same fact, which is
worth knowing before anyone unifies them.

## 5. Scope -- measured, and deliberately not measured

**Measured:** the DESCEND/ASCEND message and both report renderers. Transcript
plus source, above.

**Measured after the first draft, and it came out the other way:** `hasOrder`
also guards four navigation paths -- `order_nav.hpp:735` (`order_first_recno`),
`:800` (`order_last_recno`), `:886` (`order_skip`), `:1035`
(`order_nav_invalidate`). The first draft of this finding listed them as an
unmeasured risk. **They are not a risk.** Each dispatches on container format and
then applies the correct per-format rule inline (sec 4): CDX and CNX return false
on an empty tag, INX needs none. The over-broad `hasOrder` guard is harmless
there precisely because a correct guard follows it.

That inverts the shape of the finding. This is not "a bad predicate used in eight
places". It is **one rule, correctly implemented in the navigation layer and
absent from the reporting layer** -- so the engine navigates correctly and
describes itself incorrectly.

**Scale, for whoever fixes it:** `hasOrder` has **85 call sites across 45
files**. Changing its meaning is not a two-line edit.

## 6. Recommendation -- rewritten after sec 1a

**Rejected: `hasActiveTag()`.** The first draft of this finding recommended
adding a tag-emptiness predicate and repointing DESCEND/ASCEND at it. **That
would have broken INX**, where the steward's own transcript shows DESCEND
reversing real rows with `Active tag : (none)`. Recorded rather than quietly
replaced, because it is the same error the finding is about -- reaching for a
predicate that answers a nearby question.

**Rejected: redefining `hasOrder()`.** It is correct for what it says, and plenty
of its **85 call sites across 45 files** legitimately want "is a container
attached" -- `REINDEX`, `BUILDLMDB`, the CDX/CNX inspectors. Redefining it
changes all 85 silently.

**Proposed: hoist the rule that already exists.** `order_nav.hpp` computes
"does this container yield an ordering" correctly, per format, inline (sec 4).
Give it a name and share it:

1. Add `orderstate::hasEffectiveOrder(area)` -- container attached **AND**
   (format is INX, **or** `activeTag()` is non-empty). This is not new logic; it
   is the `order_first_recno` switch, named.
2. Repoint the **three** sites this finding measures: `cmd_descend.cpp:87`,
   `cmd_ascend.cpp:88`, and the direction line in `order_report.hpp` -- which
   then reports `NATURAL` for a tagless CDX and `ASCEND/DESCEND` for an INX,
   both correct.
3. **Leave the four `order_nav.hpp` guards alone.** Sec 5 measured them; they
   already do the right thing. Replacing their inline checks with the new
   predicate is a tidiness change, not a fix, and should not ride this commit.
4. **Edit the `@dottalk.usage` NOTE in `cmd_descend.cpp` and `cmd_ascend.cpp`
   in the same commit** (sec 2a) -- "requires an active order" becomes what the
   new predicate actually tests -- and re-mine HELP DATA, or the published help
   will contradict the fixed behaviour.
5. Decide whether `SET ORDER TO <container>` with no tag should be accepted at
   all (sec 1b). If it stays, document it; if it does not, refuse it at the
   parse and the whole class disappears. **This is the steward's call, not a
   detail of the fix.**
6. Settle `(none)` vs empty between the two renderers while in there.

The value of step 1 is that the rule stops being tacit. Today it lives only as
three `case` branches, which is why the layer that did not read them got it
wrong.

Steps 1-2 are small and self-contained. Step 3 is a separate question and should
not ride the same commit.

**Suggested regression, if one is wanted:** attach a container with no TAG,
issue DESCEND, and assert **by field value** that the first row is unchanged --
not by reading the message back, which would only prove a string was printed.
That is the UA_T6 lesson from `USE_AGAIN` applied here.

## 7. Evidence tier

**Source-evidenced:** sec 1 (steward's own transcript), sec 2, sec 3, sec 4 --
every file:line verified at `b521465f4`.

**Measured after the first draft and reported as a reversal:** sec 1a (the INX
counter-case, from the same transcript) and sec 5 (the navigation guards, which
turned out to be correct). Both changed the recommendation; both are recorded as
corrections rather than silently folded in.

**Chat/AI output:** sec 6. No code was written under this note.

## 8. Good Neighbor note

- **What changed.** One new file,
  `docs/maintenance/AIF120_HASORDER_PREDICATE_FINDING_V1.md`. **No source file
  was edited.** Nothing was fixed.
- **Whose area.** Engine -- `src/cli/order_state.cpp`, `cmd_descend.cpp`,
  `cmd_ascend.cpp`, `include/cli/order_report.hpp`. Not AIF-120's to change
  without an explicit go. This reports; it does not touch.
- **What authorization.** Steward, in session 2026-08-22: write it up after the
  push. Report only. Ships `review-needed`; the author does not self-approve.
- **How to verify, both halves.** The defect: `USE STUDENTS`,
  `SET CDX TO students.cdx` (container, **no TAG**), `LIST 5`, `DESCEND`,
  `LIST 5` -- the two listings match while `DESCEND` reports success and
  `STATUS` reports `DESCEND` beside an empty `Active tag`. The counter-case that
  constrains the fix: `USE dbf\x32\students.dbf`,
  `SETINDEX indexes\x32\students.inx`, `LIST 1`, `DESCEND`, `LIST 1` -- the
  first row **changes**, with `Active tag : (none)`. Then read
  `order_state.cpp:71-75`, `cmd_descend.cpp:87-93`,
  `order_report.hpp:151-171`, and `order_nav.hpp:745-746` against `:775-783`.
- **How to undo.** Delete this one file. Nothing else was touched and no
  behaviour changed.
