# BROWSETUI is a teaching artifact, and the tree has never said so -- charter (v1)

Status: **charter, review-needed. The lane is PARKED by owner ruling.** This
document exists so that the next reader finds a decision instead of a screenshot.
Nothing here is a work order.

Owner of record: `member.derald`
Lane owner / author: `member.ai.claude.cowork`
Lane / ticket: **AIF-153** (lane `browsetui-student-app`, claimed 2026-09-05 via
`tools/coordination/session_coordinator.py claim-aif`, run_id `COWORK-20260905-001`;
ledger `coordination/aif/AIF-153.claim`).

Measured 2026-09-05 against build `Sep 05 2026 09:20:12` and the sources at
`22c748381`. Every claim below is either a line citation or a string measured in a
built binary; where it is neither, it says so.

## 1. What BROWSETUI is

It has an identity, and until this document that identity existed only in
conversation. The owner stated it three times on 2026-09-05, in his own words:

> "browsetui should be a student app, it is a primitive tui crud example"

> "early style ibm type function key crud"

> "it is not a priority to me, it needs some more work, it was doing pretty good,
> but needs screen geometry tweaks"

So: **BROWSETUI is a teaching artifact in the early-IBM function-key CRUD idiom.**
Not an engine surface. Not a product feature. An example a student reads and
operates in order to learn what create, read, update, delete and append mean
against a real table.

**THIS IS A REVIEW STANDARD, NOT A LABEL.** It says which defects matter. A
teaching artifact is judged on whether the thing it teaches is true, and only then
on whether it is correct engine code. The two standards disagree in both
directions, and this lane has an instance of each -- see sections 3 and 4.

## 2. THE FINDING: two BROWSETUIs, and a guard that does not look where they are

`src/cli/cmd_browsetui.cpp` -- 808 lines, `cmd_BROWSETUI` at :555.
`src/tv/cmd_browsetui.cpp` -- 882 lines, `cmd_BROWSETUI` at :629.

They are near-identical forks: the same `Key` enum, the same
`" F1:Create | F2:Read | F3:Update | F4:Delete | F5:Append "` menu string, the same
F6 fullscreen toggle, the same Ctrl+S staged save. The tv copy still carries
`// src/cli/cmd_browsetui.cpp` as its own header path -- the fork showing through.

**WHICH ONE RUNS IS DECIDED BY LINK ORDER, NOT BY ANYONE.** `src/CMakeLists.txt`
globs `src/` into the `dottalkpp` executable and excludes `src/tv` from that glob
("TV isolated, not globbed"); `src/tv/CMakeLists.txt` builds the same file into
`dottalk_tvui`, which is then linked into the exe. The exe's own object wins over a
static-library member, so the CLI fork is live and the tv fork's `cmd_BROWSETUI` is
never reached.

**MEASURED IN THE BUILT ARTIFACTS RATHER THAN REASONED ABOUT.** The two forks have
different status strings, which makes them separable by grep:

```
build/src/Release/dottalkpp.exe         "E/F3: Edit"      PRESENT   "L list | E edit"  absent
build/src/tv/Release/dottalk_tvui.lib   "E/F3: Edit"      absent    "L list | E edit"  PRESENT
```

`src/CMakeLists.txt` DOCUMENTS this exact hazard at length, for `dbf_create.cpp`,
and carries a duplicate-basename shadow guard that raises `FATAL_ERROR` on it. The
guard builds its stem list from a glob of `xbase`, `xindex`, `xexpr`, `sqlsel`,
`value` and `memo`. **It does not glob `src/tv`.** So the guard written to prevent
a CLI object shadowing a library object cannot see this pair.

**AND IT HAS ALREADY COST SOMETHING.** `699e6ec60` (2026-09-05) fixed F5, which had
never appended a record: the call site passed a stream positioned at zero, so
`cmd_APPEND`'s first token was the word `APPEND` and it printed its usage block into
the TUI. That fix landed in the CLI fork only. `src/tv/cmd_browsetui.cpp:778-779`
still reads:

```cpp
std::istringstream s("APPEND BLANK");
cmd_APPEND(area, s);
```

The author of that fix -- me -- did not know the second fork existed. It is
harmless *today* only because the code is unreachable, and that is precisely what
makes it worth writing down: anyone who reorders the link, trims the CLI glob, or
promotes the tv build gets a silently broken F5 back, while a commit message
elsewhere in the history says F5 was fixed.

**WHAT IS NOT DECIDED HERE:** which fork should survive, or whether the tv one
should be deleted, promoted, or left. That is a steward ruling. What this section
claims is only that the choice is currently being made by the linker.

## 3. What the idiom commits to

Recorded because the idiom's conventions are load-bearing on a teaching artifact,
and because at least one of them reads as a defect if you do not know the lineage.

**THE FIXED PANEL IS CORRECT, NOT DEAD SPACE.** `build_browse_lines`
(`src/cli/browse_lines.cpp`) pads its output to `inner_height` with blank lines and
clips every line to `inner_width`, so the frame is the same size on every record.
That is the point of the idiom: the same field sits at the same coordinates
whatever record you are on, so the eye learns the form and the hand learns the tab
order. A panel that resized to its content would break the one property the style
exists for. **This document's author called that dead space on first reading, and
was wrong**; it is recorded rather than quietly corrected, because it is the exact
mistake a reader without the lineage will make next.

**THE PF-KEY LEGEND'S POSITION IS THE ONE OPEN DESIGN QUESTION.** The IBM split is
an action bar at the top and the function-key legend on the last line, with the
message line above it -- 3270 CICS put PF keys at the bottom and CUA kept them
there. The current screen has the title bar top, the legend directly beneath it,
and the status bar at the bottom. That is defensible and it is also the decision
everything else lays out from, so it should be made deliberately rather than
inherited. **Not ruled here.**

**GEOMETRY HAS ONE HOME EVEN THOUGH THE DRIVER HAS TWO.** `build_browse_lines` is
declared in `include/dli/browsetui.hpp` and defined once in
`src/cli/browse_lines.cpp` -- 84 lines -- and BOTH forks call it. So the "screen
geometry tweaks" the owner named are a single-file change, whatever section 2 is
eventually resolved to. Its current rules: label column is
`max(6, min(longest_name, inner_w / 3, 32))`; the record header is line 1; unused
rows are blank-filled.

## 4. The null gap, and why it is worse here than in the engine

`FieldView` (`include/dli/browsetui.hpp`) is:

```cpp
struct FieldView {
    std::string name;
    std::string value;
};
```

Two strings. **There is nowhere to put "this cell is NULL."** The state is
structurally unrepresentable in the browse renderer, so an empty cell and an absent
cell render identically as trailing spaces.

As of `11b40895a`, `LIST`, `SMARTLIST` and `DISPLAY` all print `.NULL.`, and
`include/cli/null_display.hpp` carries both the marker and the width rule. The
record panel does not, so the product now answers the same question two ways
depending on which surface asks -- the same shape as AIF-123 (SET DELETED) and
AIF-091's own value-versus-bit split.

**ON AN ENGINE SURFACE THAT IS A GAP. ON A TEACHING SURFACE IT IS A FALSE LESSON.**
A student reading a blank `NOTES` field learns that empty and absent are the same
thing, which is the single idea a database example must not teach. The idiom
already has the vocabulary for it: 3270 forms showed a field's EXTENT, so an empty
field still looked like a field.

This is the "review standard, not a label" claim of section 1 made concrete, and it
cuts both ways in this lane: F5 was a real engine defect and got engine attention
inside a day, while the false lesson -- which matters more to what this artifact is
FOR -- has been sitting in a two-member struct.

## 5. What this charter does NOT claim

- **That the live fork works.** F5 is fixed in source and has not been exercised at
  runtime; BROWSETUI is parked and no proof was taken. `699e6ec60` is
  source-correct and runtime-unproven.
- **That the tv fork is dead code in general.** Only its `cmd_BROWSETUI` is
  measured unreachable. `src/tv/CMakeLists.txt` lists eleven other units in the same
  library and none of them were examined.
- **Any behaviour of the Turbo Vision path** (`TVISION`, `FOXTALK`, `BROWSETV`).
  Not looked at.
- **That the screenshot's geometry is a defect.** Section 3 argues part of it is
  the idiom working. The outer alignment (the panel indented while the text above
  starts at column 0) and the status bar stopping short of the right edge are the
  parts that look unintended, and neither was traced to a line.

## 6. Work items, unordered, none started

1. Rule on the two forks (section 2). Steward.
2. Extend the duplicate-basename shadow guard in `src/CMakeLists.txt` to cover
   `src/tv`, or state why it should not. Independent of item 1 -- the guard is
   wrong about its own coverage either way.
3. Port or discard the F5 fix in `src/tv/cmd_browsetui.cpp:778`, following item 1.
4. Rule on legend placement (section 3), then do the geometry pass in
   `src/cli/browse_lines.cpp`.
5. Give `FieldView` a null flag and render through `include/cli/null_display.hpp`
   (section 4). One struct, one renderer, one call site.
6. Prove F5 at runtime, once BROWSETUI is unparked.

## 7. Why this is parked, and what would unpark it

Parked by owner ruling, quoted in section 1. It became visible only because F5
blocked an unrelated lane on 2026-09-05, got fixed as engine, and was then set down
without anyone writing what it was.

**THAT IS THE TRANSFERABLE PART.** An artifact whose purpose lives only in
conversation gets reviewed against whatever standard the next reader happens to
bring. This one was read as engine three times in one day -- by the fix, by the
parking note, and by this author calling a deliberate fixed panel dead space -- and
each reading was locally reasonable and aimed at the wrong target.
