# R-NUMBER REGISTER V1

**The allocator of record for R-numbers.** Created 2026-08-24 after a near-miss:
a ruling was about to be stamped `R7` on the assumption that each AIF lane
carried its own R1..Rn series. It does not. **The R-space is one flat global
sequence**, and `R7` has been taken since 2026-08-06 -- the owner ruling on
AIF-090 ("CONVERT -- develop and document, it is our thesis").

Nothing detected that. There was no register, no allocator, and no gate; the
number was checked only because someone happened to grep. That is the same
shape this project keeps naming: **a claim that decays without ever going red.**

Run the allocator. Do not pick a number by eye. This file records WHAT each
number means; it deliberately does not record which number is next, because a
document cannot stay correct about that and the tool cannot be wrong about it.

```
$py12 tools\coordination\next_r.py
```

---

## THE ONE RULE THAT SURPRISES PEOPLE

**Doctrine and rulings share the sequence.** `R1` ("derivation runs downward
only"), `R6` ("an absent value must not be representable among present ones")
and `R7` (an owner ruling converting a single lane) are all in the same series.
Two different kinds of thing, one number space.

That was ruled deliberate rather than fixed. Splitting the space retroactively
would renumber citations that are already compiled into code comments, and a
citation that silently means something new is worse than an untidy sequence.
**So the KIND is a column here, not a range.** Read the column; do not infer
the kind from the magnitude.

| kind | meaning |
|---|---|
| `doctrine` | a general rule, expected to be cited far from where it was made |
| `ruling` | a decision about one lane or one artifact |
| `reserved` | cited somewhere in the tree, not yet attributed -- **burned, never reusable** |

**And one marker, which the gate reads:** a row that records what an
ALREADY-PASSED number meant must contain the token **`backfill`**. A row that
ALLOCATES a number now must be above the register's declared high-water and
needs no marker, because taking max+1 *is* the statement. This is the only
thing separating "R7 is a new ruling I just made" from "R7 is what that old
number always meant" -- citation evidence is identical in both cases, so the
human states it once, here.

---

## ALLOCATION RULES

1. **NEXT FREE IS max + 1, NEVER the lowest gap.** Gaps are reported by the
   allocator so a human can rule on them; they are never handed out. A reused
   number makes two decisions share an identity in a permanent record.
2. **A citation burns a number even when nobody can say what it meant.** If
   `R44` appears in the tree and no row here explains it, it is `reserved`, not
   free. You cannot safely reuse a number whose meaning you cannot find.
3. **Padding is display, not identity.** `R095` and `R95` are the SAME number.
   The register's earliest rows are zero-padded and later ones are not; the
   allocator normalises `R0*(\d+)` for exactly this reason. A tool that missed
   it would report a taken number as free -- the AIF-118 shape (the same answer
   for "absent" and "fine") inside the instrument meant to prevent it.
4. **Back-filling a `reserved` row into a real one is always welcome** and
   never changes the number. Mark it `backfill` so the gate can tell it from
   an allocation.
5. **An allocation is above the high-water. A back-fill is at or below it.**
   The gate enforces exactly that and nothing more -- it cannot read meaning,
   so it asks you to declare intent instead of inferring it.

---

## DECLARED

| R | date | kind | lane | ruled by | what it says |
|---|---|---|---|---|---|
| R1 | -- | doctrine (backfill) | AIF-078 | `member.derald` | Derivation runs downward only. |
| R2 | -- | doctrine (backfill) | AIF-078 | `member.derald` | A RUNG needs a PRODUCER, a COMPARATOR and a PERSISTER. |
| R3 | -- | doctrine (backfill) | AIF-078 | `member.derald` | Failure travels in the return value. |
| R5 | -- | doctrine (backfill) | AIF-078 | `member.derald` | One tree, one ladder -- two answers to one question IS the defect. |
| R6 | -- | doctrine (backfill) | AIF-078 | `member.derald` | An absent value must not be representable among present ones. |
| R7 | 2026-08-06 | ruling (backfill) | AIF-090 | `member.derald` | CONVERT -- "develop and document, it is our thesis". Skill programme retired unbuilt after P0 falsified its premise; the four defects P0 found were repaired instead (`79888dfaa`). |
| R110 | -- | ruling (backfill) | AIF-120 | `member.derald` | Workspace path depth: keep `WorkspacePath`, and strike the reason given for keeping it. |
| R112 | -- | ruling (backfill) | AIF-120 | `member.derald` | The measured-zero gate; first-wins-plus-warning admissible ONLY as instrumented behaviour. |
| R113 | -- | ruling (backfill) | AIF-120 | `member.derald` | Order and functions (with R114). |
| R114 | -- | ruling (backfill) | AIF-120 | `member.derald` | Order and functions (with R113). |
| R120 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **The GUI's positional rung IS the engine slot.** Step 3 of the slot lane. The GUI's ordinal was the index into its own area list while the CLI's was the engine slot, so one area had two positional addresses and the posture line `AREA <n>` meant a different thing depending on which surface wrote it. The ordinal is now the slot: sparse, stable across another area's close, and the same number both surfaces print. Costs recorded rather than discovered: the survivor of a close KEEPS its number instead of being renumbered, the vacated slot becomes a hole the next open falls into, and GUI-written postures from before this change carry list indices that will now be read as slots. |
| R121 | 2026-08-24 | ruling | AIF-123 | `member.derald` | **ADDRESSING IS ABSOLUTE, TRAVERSAL IS FILTERED.** `GO <n>` names a record and must land on it under any setting: a `GO` that skipped forward would make the one command whose purpose is reaching a specific record unable to reach it, and would close the only door to navigating onto a flagged row to `RECALL` it singly. `SKIP` / `TOP` / `BOTTOM` name a POSITION IN A SET -- next, first, last -- and that set must be the visible one, so they honour `SET DELETED` as they already honoured `SET FILTER`. Ruled on principle and NOT on dialect precedent: the xBase family is honoured but not binding (steward, 2026-08-24), and the only document in the tree answering the `GO` question -- `include/foxpro_go.hpp` -- turned out to be unreviewed generated prose that contradicts itself. The defect was ONE PREDICATE: `navsel::resolve_mode` chose the logical view by asking only whether a SET FILTER was active, so `SET DELETED` -- the second reason the logical view differs from the raw order -- never reached traversal. Everything downstream was already wired. |
| R119 | 2026-08-24 | ruling | AIF-078 | `member.derald` | **`autoq_next` is RESERVED AND UNWIRED.** The x64 header sequence slot stays load-only; the catalog keeps `max(WS_ID)+1` under a FLOCK. Stamped R119 and not R7 because R7 was already taken -- the near-miss that caused this register to exist. |

R4, R8-R109 excluding those above, R111 and R115-R118 are **cited in the tree
and not yet attributed here.** They are reserved by rule 2. Back-fill them as
they are identified; the allocator reports them every run so they do not go
quiet.

---

## RESERVED BY CITATION

**This section deliberately states NO numbers.**

Every `Rnnn` citation anywhere in the scanned tree burns that number, whether or
not a row above explains it. The allocator derives that set on every run. It is
not copied here, and it must not be: a hand-copied population is a hardcoded
denominator, and this project has already paid for one --
`ENTRY_PATH_BASELINE = 127704` in `recall.py`, a frozen number that made a
metric flattering and made the bound written to catch it unable to fire
(AIF-090 D2).

The first draft of this file did exactly that. It stated "highest taken R118,
next free R119" and listed the gaps by hand. **The allocator's first run
contradicted all three claims** -- it found R0, R90, R91, R94, R97, R98, R100,
R104 and R106 cited, which the hand-count had called gaps. The instrument was
right and the document was wrong, roughly ninety seconds after the document was
written. That is the whole argument for deriving it, and it is left here rather
than quietly corrected.

To see the current population:

```
$py12 tools\coordination\next_r.py
```

**A known artifact, stated so nobody re-investigates it:** the scan matches
`\bR0*(\d{1,3})\b`, so `R0` and some low numbers may be incidental text
rather than real citations. They are still burned. Over-reserving costs
integers, which are free; under-reserving costs a collision in a permanent
record, which is not.

---

## GATE

`tools/coordination/r_collision_gate.py`, wired into the pre-push gate beside
the AIF collision gate.

- **HARD:** a duplicate R in the DECLARED table. Two rulings cannot share one
  identity.
- **HARD:** a newly declared number **at or below the register's own declared
  high-water with no `backfill` marker.** That is a decision made now claiming
  a number that has already passed -- the R7 shape exactly.
- **ADVISORY:** numbers cited in the tree with no declared row. There are
  roughly a hundred of these and they predate the register. A gate that blocked
  on them would be switched off within a day -- the same reasoning that keeps
  `check_open_items.py` advisory and that kept `check_aif_claimed.py` to ADDED
  rows only.

**The hard check was wrong twice before it was right, and both are recorded in
the gate's own docstring.** The first cut compared a new number against the
whole working tree, which would have failed the correct flow of declaring and
citing in one change. The second compared against files the change does not
touch -- and blocked this register's own seeding commit, because
**citation cannot separate theft from back-fill at all.** R7-declared-fresh and
R7-declared-historically produce identical evidence. The check was measuring
something that does not carry the answer. Hence the marker: the gate stopped
guessing and asked.

`tools/coordination/test_r_gate.py` -- 11 fixtures, five of which must go red
before their green means anything.

---

**Owner:** `member.derald` -- **steward:** `member.ai.claude.cowork`
**Status:** review-needed. The author does not self-approve.
