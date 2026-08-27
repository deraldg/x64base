# AIF-142 -- A DELETED ROW IS ABSENT FROM AN ORDERED TRAVERSAL AND MERELY FILTERED FROM A PHYSICAL ONE

    Number  : AIF-142, claimed 2026-08-27 with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001, lane
              'deleted-row-absent-from-order'). Claim file verified present
              at `coordination/aif/AIF-142.claim` before this number was
              cited anywhere.
    Found   : 2026-08-27, while proving the repaired GPS. GPS was made to
              distinguish the reasons a record has no logical row; the first
              deleted-record test returned the reason nobody predicted, and
              this finding is what that reason turned out to mean.
    Lane    : engine traversal / deletion semantics. Not AIF-078. The
              behaviour predates the multi-workspace work.
    Status  : review-needed. The author does not self-approve.
    Basis   : MIXED, and the split is load-bearing.
              Sections 1-4 and 6 are RUNTIME-PROVEN plus source-cited.
              Section 5 is SOURCE-EVIDENCED ONLY -- a prediction about
              `SET DELETED OFF`, which was NOT run. Every runtime datum in
              this document was taken with `SET DELETED` at its default ON.
    Shape   : R5 -- two answers to one question. With the aggravation that
              one of the two answers cannot be corrected by changing the
              policy that appears to govern it.

## 1. THE SAME RECORD, THE SAME STATE, TWO DIFFERENT REASONS

Measured 2026-08-27 at the dottalkpp prompt against
`dottalkpp/data/DBF/x64/STUDENTS.dbf` (200 records) with
`INDEXES/x64/STUDENTS.cdx`. Record 21 -- surname `Anderson` -- in both halves.

Under an active CDX order:

    . SET ORDER TO TAG LNAME
    . GO TOP
    . RECNO
    21
    . DELETE
    1 deleted
    . GPS
    ... Physical Recno 21, Logical Row none (record not present in the active order)

Under physical order, same record, same deletion:

    . SET ORDER TO 0
    . GO 21
    . DELETE
    1 deleted
    . GPS
    ... Physical Recno 21, Logical Row none (record is filtered out)

One record, one state, two different engine facts. The user-visible outcome is
the same -- there is no logical row -- and the REASON is not the same, and
until this week nothing in the system could tell them apart.

**REPRODUCIBILITY CAVEAT, stated because it is not optional.** Those two lines
come from a GPS carrying the repair described in the same day's work, which
landed in this same session. A stock GPS cannot produce them: it printed one number for both cases, and that number was the
count of visible records, which reads as a valid position at the end of the
table. Anyone reproducing this must build the repaired `src/cli/cmd_gps.cpp`.

## 2. WHY -- DELETE REMOVES THE KEYS

`src/cli/cmd_delete.cpp` does not merely set the deletion flag. Its own usage
block declares:

    mutates: table-data deletion-flag index stale-state cursor

and its notes say:

    Direct-write mode captures index keys before delete and applies index
    delete snapshots after delete.

The code at `:224-239` does exactly that -- `// Capture all relevant index keys
BEFORE delete, while the row is live.`, then `apply_delete_snapshot(...)`.

So under an active index the record's entries are REMOVED. Recno 21 was not
hidden from the LNAME walk. It was not in the LNAME walk.

RECALL puts them back: after `RECALL`, GPS under LNAME reported `Logical Row 1`
again. That is the same measurement run in reverse and it is why section 6
matters.

## 3. THE ORDER WALK ITSELF DOES NOT FILTER

`src/cli/order_iterator.cpp` contains NO deleted handling of any kind -- no
`isDeleted`, no visibility test, nothing. It yields record numbers. This was
measured by grep over the whole file and the absence is the point: the
traversal layer has no opinion about deletion, so every difference in what a
consumer sees comes from either the index contents or the consumer's own
filter.

That places the two outcomes in section 1 at two DIFFERENT LAYERS:

- ordered path  -- the index no longer contains the key. Nothing downstream
                   gets a chance to decide.
- physical path -- the record is yielded, and the CONSUMER's filter rejects it.

A consumer can change its filter. A consumer cannot change what is not there.

## 4. THE ENGINE ALREADY KNOWS THIS AND FILED IT AS ONE COMMAND'S PRIVATE PROBLEM

`src/cli/cmd_recall.cpp:22-23`, in its own words:

    Deleted-only traversal must use physical records, because active indexes
    normally contain only live records and would otherwise hide deleted rows.

That is this finding's central fact, already written down -- inside RECALL, as
RECALL's local workaround for its own target selection. It is not recorded
anywhere that a reader of LIST, COUNT, GPS, BROWSE or a future consumer would
look. RECALL solved it for RECALL and the property stayed private.

This is worth naming as a general shape: **a system property discovered while
fixing one command tends to get documented as that command's problem.** The
comment is correct, useful, and in the wrong scope.

## 5. WHAT THIS DOES TO `SET DELETED` -- PREDICTED, NOT MEASURED

`include/cli/settings.hpp:70` -- `std::atomic<bool> deleted_on{true}; // SET
DELETED (ON => hide deleted)`. Written by `cmd_set.cpp:1490`. Read by
`browse_filters.cpp:26`, `cmd_count.cpp:437`, `filters/filter_registry.cpp:287`
and `:316`.

Every one of those is a FILTER. The setting's whole mechanism is to stop a
consumer from rejecting a record it has been handed.

**Prediction, from source only:** with `SET DELETED OFF`, the physical path can
show deleted rows, because the rows are still there to be yielded and the only
thing suppressing them was the filter. The ordered path cannot, because the
keys were removed at DELETE time and no setting reinstates them.

If that holds, `SET DELETED` is a policy control on one path and inert on the
other -- and inert in a way that reads as compliance, since an ordered LIST
with `DELETED OFF` returns a perfectly plausible result set that is simply
missing rows. The setting appears to govern both paths and governs one.

**THIS WAS NOT RUN.** It is one test and it belongs in section 8.

## 6. BEST-EFFORT RECALL, AND WHY GPS'S NEW ARM IS A DETECTOR

`src/cli/cmd_recall.cpp` declares, at `:59` and `:66`:

    RECALL rebuilds index entries for recalled records best-effort.
    mutates_index_entries: best-effort

`reindex_recalled_record_best_effort()` at `:174` is the implementation, and
`cmd_delete.cpp` carries the matching admission: *"If index snapshot or apply
fails, data delete may still succeed and a rebuild warning is emitted."*

So a reachable state exists in which a record is LIVE IN THE TABLE and ABSENT
FROM EVERY ORDERED TRAVERSAL. It is not deleted. It is not hidden. It is
unreachable by any consumer that walks an index, and present to any consumer
that walks physically.

Before this week the engine had no way to report that state. GPS printed a row
number -- specifically the count of visible records, indistinguishable from
"you are on the last row". The repaired GPS reports
`none (record not present in the active order)`.

**That arm is a detector for a failed best-effort reindex.** It was built to
satisfy R6 -- absent must not be representable among present -- and its first
run found a real mechanism nobody was looking for. It should be kept as a
permanent report line and not softened back into a number.

## 7. WHAT THIS FINDING DOES NOT CLAIM

- It does not claim removing keys at DELETE is wrong. Keeping a deleted row's
  keys in an index has its own costs and its own correctness problems. The
  defect recorded here is the SILENCE and the DIVERGENCE, not the mechanism.
- It does not claim `SET DELETED` is broken. Section 5 is a prediction and says
  so. An unmeasured claim asserted as a defect would be the exact error this
  register exists to catch.
- It does not claim anything about PACK. PACK was not examined.
- It does not claim RECALL's best-effort reindex fails in practice. Only that
  the contract permits it to, and that the resulting state is now observable.

## 8. HOW TO MEASURE THE REMAINING HALF

One test, and it closes section 5 either way:

    USE STUDENTS
    SET ORDER TO 0
    GO 21
    DELETE
    SET DELETED OFF
    LIST
    SET ORDER TO TAG LNAME
    LIST
    SET DELETED ON
    SET ORDER TO 0
    GO 21
    RECALL

If record 21 appears in the physical LIST and not in the ordered LIST, the
prediction holds and section 5 is promoted to runtime-proven. If it appears in
both, the index is retaining keys under some condition this finding did not
measure, and section 2 needs narrowing.

Either result is worth having. The current state -- a documented setting whose
reach across two traversal paths has never been measured -- is not.

## 9. GOOD NEIGHBOUR

- **What changed:** nothing executable. This document only.
- **Whose area:** the finding cites `src/cli/cmd_delete.cpp`,
  `src/cli/cmd_recall.cpp`, `src/cli/order_iterator.cpp`,
  `src/cli/cmd_set.cpp` and `include/cli/settings.hpp`. None were modified.
- **Authorization:** AIF-142 claimed and verified in the ledger before the
  number was written anywhere.
- **How to verify:** section 1 replays at the prompt against a build carrying
  the repaired `cmd_gps.cpp`. Section 8 is the outstanding measurement.
- **How to undo:** delete this file and release AIF-142 with
  `session_coordinator.py release-aif --number 142 --run COWORK-20260827-001`.
