# OI-010 examined -- it is not a decision, it is a stale promotion and an orphan

    Item   : OI-010 (raised 2026-08-17, next look 2026-09-29)
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Method : read-only. `git show` and `git grep` against `HEAD` and
             `origin/main`. No branch touched, no file moved.
    Status : review-needed. **The row's central question is already answered by
             the promotion manifest; its stated premise is wrong; and the real
             defect is more urgent than the question.**

---

## 1. What the row asks, and what is actually there

The row asks: *"`main` carries TWO build documents and `development` carries
one; decide which is canonical before a third diverges."*

Measured today, four documents exist across the two branches:

    development  BUILDING.md                                   5,596 B  138 lines
    development  docs/manuals/developer/dev/dev-21-build-system.md
                                                              13,041 B  261 lines
    main         BUILDING.md                                   4,738 B  121 lines
    main         docs/getting-started/BUILDING.md              1,250 B   47 lines

**The third document the row feared already exists** -- DEV-21, authored
2026-08-17, the same day the row was written.

## 2. The canonical location is ALREADY DECIDED, in two places

    PROMOTE.manifest:57            BUILDING.md
    PROMOTE.manifest:75-76         # NOTE: main currently carries BUILDING.md at
                                   # docs/getting-started/BUILDING.md.
                                   # Reconcile to ONE canonical location before
                                   # the next promotion.
    PROMOTION_CHECKLIST.md:22-23   Manifest promotes it at repo root; main
                                   carries it at docs/getting-started/. Pick one.

**The manifest does not ask -- it promotes `BUILDING.md` at repo root.** The
"pick one" note is about cleaning up the other copy, not about choosing.

## 3. The row's premise is WRONG, and it changes the answer

The row states: *"the public README links the `docs/getting-started/` copy."*

    git grep -l -i 'getting-started/BUILDING' origin/main   ->  NOTHING
    git grep -l 'POSIX_WSL_QUICKSTART'        origin/main   ->  README.md

The second query is the instrument check: `git grep` against the ref works, so
the empty result is real. **Nothing on `main` references
`docs/getting-started/BUILDING.md` -- not the README, not any tracked file.**
The README links `docs/getting-started/POSIX_WSL_QUICKSTART.md` and a website
URL for "Getting Started", and never the BUILDING copy.

It is an **orphan**: last touched **2026-07-12**, six weeks ago, unreferenced on
its own branch and not in the promote list.

**The only files that reference it are on `development`** --
`PROMOTE.manifest`, `PROMOTION_CHECKLIST.md`, `PROMOTION_PROCESS.md`,
`coordination/OPEN_ITEMS.md` and one flush-v5 record -- which is why
`cited-paths` reports it MISSING on every commit touching those files. **The
citations are the reconciliation instructions; the file they name is on the
other branch.**

## 4. The urgent defect is not the location question

**`main`'s ROOT `BUILDING.md` -- the promoted one, the one GitHub renders --
tells readers that features present in their own checkout are absent.**

    main:BUILDING.md
      "## Editions (in development -- not yet in this repository)"
      "It is **not on the public repository yet** -- do not expect
       DOTTALK_PRODUCT or windows-lean-* presets in this clone."

Measured against `main`'s own `CMakePresets.json`:

    DOTTALK_PRODUCT occurrences        11
    windows-lean-* occurrences         10
    configure presets on main          14
    presets named by the denial        windows-lean-table, windows-lean-lmdb,
                                       windows-educational-lmdb,
                                       windows-development-lmdb, wsl-lean

**Five presets the page says not to expect are in the file beside it.**

`development` corrected this on **2026-08-17** (`cfb8aaebf`), in the same commit
that authored DEV-21, and did it well -- the correction is stated as a
correction, names what was wrong, and points to the reference chapter. `main`'s
copy was last refreshed **2026-08-14**, three days before the fix existed, and
has carried the false claim ever since.

**And the orphan does NOT repeat it.** The row suspected the getting-started copy
"may repeat" the claim; it does not. It is a clean 47-line quickstart -- four
preset recipes and the rule against personal paths in tracked CMake files.
**That suspicion is discharged.**

## 5. So the shape on `development` is already coherent

    root BUILDING.md   front door, 138 lines, corrected, and it POINTS onward:
                       "Full reference: docs/manuals/developer/dev/dev-21-build-system.md"
    DEV-21             reference tier, 261 lines, every target, option, preset,
                       entry-point script and platform status

**A front door that names its reference is not a divergence risk; it is the
split done properly.** The row's "three-way split is the live risk" was right to
raise and has resolved in the good direction on `development`. The unresolved
half is entirely on `main`.

## 6. Recommendation -- two actions, one of them not a decision

  1. **Promote `development`'s root `BUILDING.md` to `main`.** This is not a
     governance call; it replaces a false public statement with a corrected one
     that already exists, reviewed, on the branch promotions come from. It is
     what the next promotion would do anyway.
  2. **Delete `docs/getting-started/BUILDING.md` on `main`.** Unreferenced for
     six weeks, absent from the promote list, and the manifest already names
     root as canonical. This is the "reconcile to ONE canonical location" the
     manifest asks for, and it costs nothing because nothing points at it.

After both, OI-010 closes, the `cited-paths` MISSING advisory resolves **at its
cause**, and the promotion documents can drop their reconciliation notes.

**Neither can be done from `development`** -- the row says so and is right; this
is promotion scope. What has changed is that it is now a specified action rather
than an open question.

## 7. What was NOT done

- **No branch touched.** `origin/main` was read with `git show` and `git grep`
  only. Nothing staged, moved, deleted or promoted.
- The OI-010 row itself is **not edited** here; it belongs to the register and
  its correction should ride the decision, not precede it.
- DEV-21's content was not reviewed for accuracy -- only its existence, size and
  the fact that the front door names it.

## 8. Good Neighbour

    What changed      : this document. Nothing else.
    Whose area        : `coordination/OPEN_ITEMS.md` is shared and was READ.
                        `main` is publication scope and was READ ONLY.
    What authorization: the owner's "oi-010, let us examine it".
    How to verify     : `git grep -l -i 'getting-started/BUILDING' origin/main`
                        returns nothing while the same query for
                        `POSIX_WSL_QUICKSTART` returns README.md;
                        `git show origin/main:CMakePresets.json` contains
                        `windows-lean-table`; `git show origin/main:BUILDING.md`
                        contains "not on the public repository yet".
    How to undo       : delete this file.
