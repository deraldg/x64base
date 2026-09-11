---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260911-COWORK-204
  recorded_at_utc: 2026-09-11T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260910-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 6e7804088
  authorization:
    requested_by: owner (member.derald), in-session 2026-09-11 -- observed that
      "like a lot of other things the pieces are there our job has been mining
      and consolidating them", then authorized writing the asymmetry up as a
      finding ("yes") and numbering and landing it under docs/ ("do it").
    scope: |
      Finding for AIF-161 (lane negative-claim-decay). METHODOLOGY ONLY. No source change is
      authorized by this document and none is proposed.
      Write access exercised for this report:
        docs/maintenance/AIF161_FINDING_A_NEGATIVE_CLAIM_IS_ONLY_TESTED_V1.md
        docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md (one row)
      NOT authorized here: any edit to src/cli/table_state.cpp to correct the
      comment at :468, any amendment to the AIF-159 intake row, and any gate
      change.
  report:
    path: docs/maintenance/AIF161_FINDING_A_NEGATIVE_CLAIM_IS_ONLY_TESTED_V1.md
    kind: finding
---

# AIF-161 -- a negative claim is only tested by someone who decides not to believe it

    lane      : AIF-161 (negative-claim-decay)
    claim     : coordination/aif/AIF-161.claim
    intake    : docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md
    owner     : member.derald
    steward   : member.ai.claude.cowork
    status    : SOURCE-EVIDENCED, three dated instances 2026-09-09..11.
                Methodology. No fix authorized, no gate proposed.
    opened    : 2026-09-11
    baseline  : 6e7804088

## 1. The observation, and whose it is

The owner, 2026-09-11: *"so like a lot of other things the pieces are there our
job has been mining and consolidating them."*

True, and one lane in one day produced six: the retained-edit versioning already
in the journal, the two-process harness, `xbase::durable_sync`, a DBF already
synced at a commit point, a contention refusal eight lines from the one being
read, and a shipped comment naming the journal it is waiting for.

**But the pieces were not hidden. Three of them were documented as ABSENT or
IMPOSSIBLE by text sitting beside them.** That is the finding: not that the house
forgets what it has, but that its record of what it *cannot* do decays in a way
its record of what it *can* do does not.

## 2. Why the asymmetry exists

**A positive claim is tested by use.** "`journal_begin_commit` writes a COMMIT
marker and fsyncs" is exercised on every buffered commit. If it were wrong,
something would break and someone would find out.

**A negative claim is never exercised.** Nobody runs *"there is no multi-process
harness."* Nothing calls *"a DBF cannot be synced."* It sits in the tree being
believed, and the only event that can falsify it is **someone deciding not to
believe it and doing the search the author did not.**

That event is rare, because the notes are good. A well-argued obstacle -- with
the reason, the measurement, the citation -- is more persuasive and more durable
than a vague one. **The better the note, the longer it outlives its own truth.**
This house's documentation discipline amplifies the problem it would otherwise
solve.

## 3. Three instances, and they are not the same defect

### 3.1 STALE: true when written, falsified later, never revisited

`src/cli/table_state.cpp:468-471`, at the line where the recovery log is
deleted:

```cpp
    // writeCurrent already flushed the DBF's fstream to the OS. A hardened DBF
    // fsync before removing the log is a follow-up (std::fstream does not expose
    // the OS handle portably). Remove the replayed log.
```

True when written (AIF-023, `docs/maintenance/TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`,
2026-07-19). **`xbase::durable_sync` shipped 2026-08-31** --
`include/xbase/durable.hpp`, `src/xbase/durable.cpp` -- and does exactly the
deferred thing, on both platforms. The comment has been steering
maintainers away from an available fix for **eleven days**, and it reads as
current because the sentence is still grammatically true.

### 3.2 UNVERIFIED NEGATIVE: false when written

The AIF-159 intake row, written **2026-09-09**:

> *"the tree's one multi-process harness is PKDURABLE, which is SEQUENTIAL BY
> CONSTRUCTION"*

`src/tests/test_lock_protocol.cpp:371` -- G6, two real processes behind one start
gate -- landed with AIF-150
(`docs/maintenance/AIF150_ATOMIC_LOCK_PUBLICATION_FINDING_V1.md`) on
**2026-09-03**. **The claim was already false by
six days when it was written**, and nothing caught it, because verifying it
would have required an exhaustive search for a thing believed not to exist.

**This is the more dangerous of the two shapes**, because staleness at least has
an honest origin. An unverified negative is a search that was never run,
reported in the same confident voice as a measurement.

### 3.3 INHERITED: a stale note propagated into new work

The AIF-160 charter (`docs/maintenance/AIF160_MULTI_AREA_ATOMIC_COMMIT_LANE_V1.md`),
**2026-09-10**, argued against a decision the owner had already taken, on the
strength of 3.1's sentence. The author **checked it**
against `include/xbase.hpp:767`, found the confirmation genuine, and stopped.

**The confirmation is what made the staleness invisible.** Verifying that an
obstacle is still literally true is not verifying that it is still binding.
Corrected in `6e7804088`, charter sections 3.4-3.8, after the owner asked *"why
are you afraid of b?"*

## 4. THE SHARPER LESSON: the barrier was phrased as a MECHANISM, the fix used another

This is the part worth carrying beyond these three.

*"`std::fstream` does not expose the OS handle portably"* is a true statement
about **one mechanism**. It was read -- by its author, by AIF-023's closeout, by
the charter -- as a statement about a **capability**: "a DBF cannot be synced."

`durable_sync` never touches the `fstream`'s handle. It opens **a second handle
by path**, and `src/cli/cmd_workspace.cpp` had been calling it on a DBF at a
commit point since the day it shipped. The barrier, as phrased, excludes that solution by construction: a
reader checking whether the obstacle still holds will re-confirm the
mechanism and never think to look for a different one.

**A barrier phrased around a mechanism is falsified by any other mechanism, and
re-verifying the mechanism actively hides that.**

## 5. The convention this suggests

**An obstacle note carries the condition that retires it, phrased as a
CAPABILITY, never as a mechanism.**

Not:

> `std::fstream` does not expose the OS handle portably.

But:

> **RETIRE WHEN:** any route exists to force this file's contents to durable
> media, by any means -- including a handle obtained other than from the
> `fstream`.

And not:

> The tree's one multi-process harness is PKDURABLE and it is sequential.

But:

> **RETIRE WHEN:** any test in the tree starts two processes against one
> resource. Check: search the test sources for `CreateProcess` or `fork(`.
> (Today the answer is `src/tests/test_lock_protocol.cpp:371`, which is why
> this note is retired.)

Both are checkable in one command by a reader who has no memory of the original
lane. **The first phrasing invites re-confirmation of the barrier; the second
invites a search for the capability.** That is the entire difference, and it is
the same move this house already made when it ruled that console-text claims
must become field-value markers: make the claim mechanically falsifiable and it
stops being able to outlive itself quietly.

**Cheapest first step, needing no ruling and no gate:** when writing a note that
says something cannot be done or does not exist, write the grep that would prove
you wrong. If you cannot write it, the claim is not ready to be recorded as a
fact.

## 6. What this does NOT say

- **NOT a proposal for a gate.** A scan for barrier-shaped comments is
  imaginable and is not proposed here; the convention is a writing habit first,
  and should earn a gate only if the habit proves insufficient.
- **NOT a claim that mining always works.** Three for three in one day is
  selection as much as evidence -- the author was looking for pieces.
  **AIF-160's group decision is the counterweight:** prepare/decide/apply exists
  nowhere in the tree, and no amount of mining will produce it. The failure mode
  of "the pieces are already there" is assuming every gap has one.
- **NOT a criticism of the notes.** All three were written in good faith, two of
  them were true when written, and the tree is better for having them. The
  defect is that nothing distinguishes a claim that gets tested by use from one
  that never will.
- **NOT measured beyond the three instances cited**, all from a single lane in a
  three-day window. Whether the pattern holds across the tree is unknown and
  would need a deliberate sweep.

## 7. The one-line version

**A positive claim is tested by use. A negative claim is only tested by someone
who decides not to believe it -- so write down what would prove it wrong, while
you still remember.**

Ships review-needed.
