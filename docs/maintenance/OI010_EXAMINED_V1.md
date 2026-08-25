# OI-010 examined -- it is not a decision, it is a stale promotion and an orphan

    Item   : OI-010 (raised 2026-08-17, next look 2026-09-29)
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Method : read-only. `git show` and `git grep` against `HEAD` and
             `origin/main`. No branch touched, no file moved.
    Status : review-needed. **The row's central question is already answered by
             the promotion manifest; its stated premise is wrong; the real
             defect is more urgent than the question; and section 9 widens it.**

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

## 9. WIDENED the same day -- the gate answered a question this document raised

Committing this examination put it in a change set, so `cited-paths` read its
citations and returned one the author had not looked for:

    WIDOW docs/getting-started/POSIX_WSL_QUICKSTART.md -- on disk, NOT tracked

**The whole `docs/getting-started/` tier is tracked on `main` and untracked on
`development`:**

    file                                      on development   on main
    DEVELOPER_CONSTANTS_AND_X64_METADATA.md   on disk, UNTRACKED   tracked
    FAQ.md                                    on disk, UNTRACKED   tracked
    POSIX_WSL_QUICKSTART.md                   on disk, UNTRACKED   tracked
    BUILDING.md                               NOT ON DISK AT ALL   tracked

None of the three is gitignored -- 12,623 bytes, plain markdown, zero non-ASCII,
source lane.

**And `development`'s own README links one of them**, at line 191:

    - [docs/getting-started/POSIX_WSL_QUICKSTART.md](docs/getting-started/POSIX_WSL_QUICKSTART.md)

**So a fresh clone of `development` gets a README with a broken link**, for the
same reason OI-011 recorded about the developer manual: untracked by omission,
invisible because nothing ever listed it.

### 9a. This is OI-010's shape, one directory wider

Section 3 concluded that `docs/getting-started/BUILDING.md` is a main-only
orphan. That was right about the file and too narrow about the cause.
**`docs/getting-started/` is a MAIN-ONLY TIER that `development` carries on disk
and not in git** -- BUILDING.md is simply the member that is not even on disk
here.

That reframes the second recommendation in section 6. Deleting
`docs/getting-started/BUILDING.md` on `main` still stands -- it is unreferenced
there and the manifest names root as canonical. But the tier around it is
referenced, is published, and is missing from the branch promotions come from.

### 9b. The decision this adds

**Either** track the three on `development` -- 12.6 KB, one `git add`, and the
README link resolves in a fresh clone -- **or** rule `docs/getting-started/` a
publication-only tier and stop linking it from `development`'s README. The
current state is neither, and it is the state that produces a broken link.

**Not proposed as done here.** The three files were not staged; this is a
publication-scope question sitting beside a promotion-scope one, and both belong
to the same call.

### 9c. Worth noticing about the instrument

This document argued in section 3 that `git grep` returning nothing is only
evidence when the instrument is checked, and used `POSIX_WSL_QUICKSTART` on
`main` as that check. **The same filename came back minutes later as a widow on
`development`** -- the file chosen to prove the tool works turned out to be the
next finding. The citation gate reads what a document cites, so writing about a
path is enough to have it checked.

---

## 10. ACTIONED 2026-08-25 -- and the manifest settles item 3

The owner authorized items 1, 2 and 3. Reading `PROMOTION_PROCESS.md` first
changed what each of them IS.

### 10a. Item 3 is decided by the manifest, not by preference

    PROMOTE.manifest:167    docs/getting-started/**

**The whole tier is already on the allow-list**, so it is INTENDED to publish
FROM `development`. Section 9's two options were not equally weighted after all:
"rule it publication-only and stop linking it" contradicts the manifest, which
promotes it from here.

**So: track the three on `development`.** That is the option the promotion
process already assumes.

**And it is not cosmetic.** `PROMOTION_PROCESS.md` section 5.2 overlays "every
`PROMOTE.manifest` match from development" -- which is how three untracked files
reached `main` in the first place. **A promotion run from a FRESH CLONE of
`development` would publish nothing for `docs/getting-started/`**, because a
fresh clone does not have them, and the drift audit would report GONE for a tier
the manifest says should publish. The current state works only because this
workstation happens to hold files git does not.

### 10b. Item 1 is not an edit, it is a promotion run

`BUILDING.md` is `PROMOTE.manifest:57`. Section 5.2 overlays every manifest
match. **So the corrected root `BUILDING.md` promotes itself the next time
staging is rebuilt** -- there is nothing to hand-apply, and hand-applying would
violate section 8: *"No change is hand-edited in both `development` and `main`.
Fix in `development`, then re-promote."*

The fix already exists in `development` (`cfb8aaebf`, 2026-08-17). **Item 1 is
"run the promotion", not "write a patch".**

### 10c. Item 2 is a purge inside the rebuild-review-commit window

The rebuild clones `github/main` as its baseline, so
`docs/getting-started/BUILDING.md` survives unless removed deliberately. Section
6 classifies it: present in staging, no development counterpart, off the
intent -- and section 7 gives the idiom (`git rm ... --cached` from `main`).
Section 9.1 records the same treatment already ruled for `WORKFLOW_X64BASE.md`:
*"Removal happens in the rebuild-review-commit window."*

**Neither 1 nor 2 can be run from here.** `PROMOTION_PROCESS.md` is
non-negotiable that only sterilized staging at `C:\x64base` may update `main`,
and `C:\x64base` is not a folder this session can reach at all.

### 10d. The note is recorded in FOUR places

    PROMOTE.manifest:75-76        "Reconcile to ONE canonical location..."
    PROMOTION_CHECKLIST.md:22-23  "Pick one location."
    PROMOTION_PROCESS.md:9.2      "Path mismatch ... Pick one."
    coordination/OPEN_ITEMS.md    OI-010

All four say the same thing and none of them has drifted -- yet. **Four copies of
one instruction is the shape the row itself cites from AIF-082 6.8**, "two shims
that restate will diverge, and have". When items 1 and 2 land, all four should be
retired in the same commit, not left as four independent reminders of a closed
question.

---

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
