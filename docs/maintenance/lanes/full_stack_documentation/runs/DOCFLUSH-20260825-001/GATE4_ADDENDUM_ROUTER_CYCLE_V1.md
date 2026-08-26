# v6 Gate 4 addendum -- the BUILD-router cycle, and the content diff earning its keep

    Run     : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Cycle   : the SECOND Gate 4 pass of v6. The first is GATE4_VALIDATION_V1.md
              (store 2026-08-25 15:36). This one covers the rebuild that followed
              `90e5dce0b  BUILD is a router, not an unknown command` (AIF-131).
    Store   : exe 2026-08-26 01:00:12 -> LEGACY 01:06:10 -> current 01:11:28
    Against : dottalkpp/data/help.bak-20260825-180609 (pre-run, taken by LEGACY
              at 01:06; it holds the 22:30/22:36 store)
    Status  : review-needed. Gate 0 GREEN. 6' GREEN. Content diff GREEN and it
              saw something 6' could not.

## 1. Gate 0 -- green, all four ordering sub-checks

    1. @dottalk.file coverage: 100.0%  (uncovered=0)
    4. PASS  exe newer than catalogs    exe 2026-08-26 01:00:12
    4. PASS  store newer than exe       store 01:11:28, 11m after exe
    4. PASS  legacy before store        LEGACY 01:06:10 -> store 01:11:28
    4. PASS  generation stamp           both tables 2026-08-25
    4. PASS  store integrity            667 topics reachable, every line row names one
    4. WARN  status coherence           167 rows pending + AUTHORITATIVE (AIF-126, carried)
    4. skip  binding                    could not read worktree state
    5. store join: RESULT: clean

    PREFLIGHT PASS

`legacy before store` is the sub-check that encodes v5's twice-paid array
failure, and this run is the first in which it PASSED on a rebuild driven the
way the resume state prescribed: **the two commands typed at the `.` prompt, one
at a time.** The owner's own note stands -- typing at the prompt has no stdin to
redirect, so the nested-`std::cin` trap cannot be re-armed by copying a line.

## 2. Assertion 6' -- topic SET diff. GREEN.

    topic-set diff against dottalkpp/data/help.bak-20260825-180609
              GAINED DOT|BUILD
              net +1  (666 -> 667)
    RESULT: clean

Zero lost. The single gain is `DOT|BUILD`, the router registration added in
`90e5dce0b`. Expected, named, dispositioned.

## 3. The content diff, run because 6' was declared a MEMBERSHIP check

`GATE4_VALIDATION_V1.md` section 2 recorded that a SET diff cannot see a
SUBSTITUTION, prescribed the id-stripped listing diff as the workaround, and
left the assertion for v7. **This cycle is the first time that workaround was
run, and it found a change both adopted assertions are blind to.**

Method: read the DBFs directly, key `COMMANDS` on `(CATALOG, COMMAND)` and
`HELP_LINE` on the multiset of `(TOPICKEY, KIND, SOURCE, ROLE, TEXT)`. Ids are
excluded because they renumber on insert -- a raw diff of the same change read
676 lines on 2026-08-25.

    COMMANDS (id-stripped)       pre=461   post=462
      ADDED    DOT|BUILD
      REMOVED  none
      CHANGED  DOT|BUILD VECTORS   implemented T -> F   (supported T -> T)
               DOT|BUILD INFO      implemented T -> F   (supported T -> T)

    HELP_LINE (id-stripped multiset)   pre=29265   post=29268   net +3
      +1  DOT|BUILD          STATUS   REGISTRY  implemented=yes; supported=yes
      +1  DOT|BUILD          SUMMARY  DOTREF    Router for the spaced spellings of BUILDVECTORS...
      +1  DOT|BUILD          SYNTAX   DOTREF    BUILD [VECTORS|INFO]
      +1  DOT|BUILD INFO     STATUS   REGISTRY  implemented=no; supported=yes
      +1  DOT|BUILD VECTORS  STATUS   REGISTRY  implemented=no; supported=yes
      -1  DOT|BUILD INFO     STATUS   REGISTRY  implemented=yes; supported=yes
      -1  DOT|BUILD VECTORS  STATUS   REGISTRY  implemented=yes; supported=yes

Seven rows moved, every one of them named, and 5 - 2 = +3 reconciles the total
exactly. Nothing else in 29,268 rows changed.

## 4. The finding: `implemented` went yes -> no, and that is a CORRECTION

Read as a number, two commands lost their implemented flag and that looks like a
regression. It is the opposite, and the source says so
(`src/cli/shell_commands.cpp:511-516`):

    // shell_dispatch keys on the FIRST TOKEN only, so "BUILD VECTORS" and
    // "BUILD INFO" were registered and could never be typed -- they read as
    // working registrations and were dead.

So the old `implemented=yes` was reporting a registry ROW, not a reachable
COMMAND. `BUILD VECTORS` typed at the prompt answered `Unknown command: BUILD`.
The new state -- `implemented=no; supported=yes` on the two spaced spellings,
`implemented=yes` on the `BUILD` router that actually serves them -- is the first
time the store has described what the dispatcher will do.

**This is the family that has now cost this lane four withdrawn or corrected
assertions: a proxy that cannot answer the question put to it.** `IMPLEMENT` was
answering "is there a registration" while being read as "can this be typed".
Those two questions had the same answer for every other command in the catalog,
which is why the divergence survived until a multiword key was added.

It also lands the methodological point squarely:

    the count floor     sees +1     (461 -> 462) and reads it as growth
    the topic SET diff  sees +1 key (GAINED DOT|BUILD) -- correct but partial
    the content diff    sees all 7  rows, including the two that flipped

Neither adopted assertion could have told the owner that two commands changed
their implemented status. **A content-level assertion is no longer a v7 nicety;
it is the only check in the set that saw the substantive half of this cycle.**

## 5. Assertion 1' -- still unusable, and this cycle shows a second reason

    dottalk++ v0.6 (2026-08-24, c39d966c dirty)  (Aug 25 2026 18:00:12)

The banner reports commit `c39d966c` from two days ago and a build time of
2026-08-25 18:00:12, while the binary on disk was written 2026-08-26 01:00:12 and
provably contains `90e5dce0b`. `GATE4_VALIDATION_V1.md` section 3 already
explains the commit half (`CMakeLists.txt:59` reads git at CONFIGURE time). The
build-time half is the withdrawn v5 assertion recurring: `__DATE__`/`__TIME__`
live in a translation unit that did not need recompiling, so the stamp reports
when that TU was last compiled, not when the binary was linked.

**Both halves of the banner are stale, in different ways, for different reasons.**
Neither is a freshness proxy. What was actually run instead, and what should be
run every time:

    md5sum build/src/Release/dottalkpp.exe dottalkpp/bin/dottalkpp.exe
      b5539746b3c1b350aea73d77a7475a6f   -- identical, so the staged runtime exe
                                            IS the one just built
    strings -a build/src/Release/dottalkpp.exe | grep -c 'Router for the spaced spellings'
      1                                  -- the change under test is in this binary

Two commands. They answer "is the exe I am about to run the one I just built"
and "is my change in it" directly, with no stamp in the path.

## Good Neighbor

    What changed  : one new document in this run's own directory. No source, no
                    data, no store, no rebuild. The store described here was
                    built by the owner at the `.` prompt.
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
                    The BUILD router itself is AIF-131, already committed.
    Authorization : the owner's standing instruction to run v6 through to the end.
    Verify        : $py12 tools\fullstack_docs\docpush_preflight.py --root .
                      expect PREFLIGHT PASS, status coherence the only WARN.
                    $py12 tools\coordination\help_store_check.py --against dottalkpp\data\help.bak-20260825-180609
                      expect RESULT: clean, GAINED DOT|BUILD, net +1.
                    Section 3's table reproduces from the two DBF directories
                    with dbfread; the seven rows are the whole delta.
    Undo          : delete this document. It asserts nothing the store does not.
