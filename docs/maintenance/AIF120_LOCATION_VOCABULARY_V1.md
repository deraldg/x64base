---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-092
  recorded_at_utc: 2026-08-20T23:40:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: b7d745104
  authorization:
    requested_by: maintainer (member.derald), in-session -- "check cmd_setpath.cpp
      for consumption", then the owner ruling "Workspace only" on where a document
      states table location, and "Report to engine lane" on the drifting printers.
    scope: >
      Record the owner ruling that location is a workspace fact and not a document
      property, write it into contract section 10, and report what examining
      cmd_setpath.cpp found about section 10's existing rule. Writes docs/ only.
  report:
    path: docs/maintenance/AIF120_LOCATION_VOCABULARY_V1.md
    kind: ruling
---

# AIF-120 -- R82: location is a WORKSPACE fact, and the rule that already said so has never been enforced

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

Asked to check `src/cli/cmd_setpath.cpp` for consumption, I found a closed,
string-keyed vocabulary of 50 named path slots -- exactly the thing a portable UI
description needs to stop depending on ambient state. The owner ruled **not to use
it**: the workspace says where, the document says what. That is the right answer
and it matches R73 exactly. What makes this a ruling rather than a note is what
the same examination found underneath: **contract section 10 has ruled since
2026-08-19 that `Table` is document-relative and never resolved against ambient
state, no tool enforces it, the wx host resolves from an environment variable, and
every fixture in the corpus violates it.** A rule with no implementation and a
corpus that contradicts it is not a rule.

## 1. What `cmd_setpath.cpp` actually offers

The file itself is 118 lines of normalize, defaults and dump over
`include/common/path_state.hpp`, which is where the substance is:

| | |
|---|---|
| `slot_from_string` / `slot_name` | a CLOSED, checkable vocabulary with accepted spellings (`DBF_X64`, `DBFX64`) |
| the `Slot` enum | **50 distinct slots**, including `DBF_X32/X64` and `INDEXES_X32/X64` |
| `get_slot` / `set_slot` | one accessor per slot, and `SETPATH` mutates through it |

A closed set that can be validated at gate time is precisely what R73 wished it
had had when it closed `Order` at two values and got the survey wrong.

## 2. The owner ruling

> **Location is a WORKSPACE fact. A UIDEF document does not name a path slot.**

The document says WHAT -- which table, which alias, which relation. The workspace
says WHERE -- a `DTSHEMA 2` row already carries `dbf=`, `index=`, `indextype=` and
`tag=` per area. This is the same division R73 made for `Order` and the same one
R12 made for coordinates, and applying it a third time is a sign it is the actual
seam rather than three separate judgement calls.

**Recording what was declined and why matters as much as recording what was
chosen.** `Slot = DBF_X64` in `SOURCE` would make a document portable across
flavors on its own, and it was rejected because it puts a location fact in the
document -- the thing R12 and R73 both moved the other way. A later reader who
finds `slot_from_string` and thinks nobody noticed should find this paragraph.

## 3. A generated frontend must NOT resolve paths itself

`src/gui/core/session.cpp` -- the shipped GUI core, which this lane did not write
-- already resolves flavor-aware with fallback:

```
tables   : DBF_X64        -> DBF_X32        -> DBF
indexes  : INDEXES_X64/.cdx -> INDEXES/.cdx
           INDEXES_X32/.cnx -> INDEXES/.cnx -> INDEXES_X32/.inx
```

Two things follow. First, **it independently corroborates R73's flavor table** --
`.cdx` for x64, `.cnx`/`.inx` for x32 -- from a file written by someone with no
stake in that ruling, which is the R77 pattern. Second, a generated frontend that
grew its own candidate list would be **R70.5 exactly**: the generator
re-implementing `src/cli/shell.cpp:532-534` once per document. UIDEF resolves
nothing. It hands the engine a name and the engine resolves it.

## 4. What the examination found underneath

Contract section 10 has said since 2026-08-19, measured from VFP's own save
behaviour:

> `Table` is **relative to the UIDEF document's own location**, never absolute and
> never a bare name resolved against ambient state. [...] a document whose `Table`
> does not resolve is refused, never rendered unbound.

Three things are true about that rule today:

**4.1 Nothing enforces the refusal.** `manifest.py` cites section 10's
ambient-state reasoning to refuse a bare FIELD name (`manifest.py:307`), and
checks nothing at all about `Table`. The refusal the contract declares has no
implementation. That is the fifth declaration-nothing-acted-on this session, after
R33.4, R70.5, R74's placeholder frames and R73's unattached order.

**4.2 The wx host resolves from an environment variable.**
`gui/uidef/wx_host.cpp:121` reads `R70_DBF` and `UIDEF_TABLES` and builds
`dir + "/" + name + ".dbf"`. The file is honest about it in a comment -- *"the
demo's stand-in for what a real host reads out of the document's SOURCE"* -- which
is better than silence, but the CONTRACT does not record that its fourth backend
does not implement section 10. Conformance is a contract fact; a comment in one
file is not where a reader looks for it.

**4.3 Every fixture in the corpus contradicts it.** All 22 documents say
`Table = STUDENTS.DBF`. Section 10 reads a bare name as the ZERO-DISTANCE case --
the table beside the document -- and the tables live in
`dottalkpp/data/DBF/x64` while the documents live in `gui/uidef`. Strictly read,
every `SOURCE` line this lane has ever authored is a widow, and R70 only ran
because the host used `R70_DBF`.

None of this was visible while the rule had no enforcement. **A rule nothing
checks is indistinguishable from a rule nothing violates.**

## 5. What the owner ruling fixes

Section 10 forbade "a bare name resolved against ambient state" and that phrasing
is what makes 4.3 look like mass non-compliance. The owner's answer supplies the
distinction the section was missing:

> A **WORKSPACE row is not ambient state.** `SETPATH` and "whatever area happens
> to be current" are ambient -- unwritten, order-dependent, invisible in the
> document set. A `DTSHEMA 2` row is a DECLARED, per-area, readable statement of
> where a table is, and a bare `Table` name resolved through one is resolved
> against a document, just not against the UIDEF document.

So `Table = STUDENTS.DBF` plus a workspace row naming `DBF/x64` is conformant, and
`Table = STUDENTS.DBF` with nothing but `SETPATH` behind it is not. The corpus is
in the second state and needs to reach the first. Section 10 gains this clause;
the corpus change and the enforcement are named in section 7 and NOT done here,
because the ruling that makes them meaningful is the one being made now.

## 6. R82.1 -- reported to the engine lane

The 50-slot enum has **three hand-maintained printers and no two agree**:

| printer | slots shown |
|---|---|
| `src/cli/cmd_init.cpp:286` -- the startup banner | 13 |
| `src/cli/cmd_setpath.cpp` `dump()` | 18 |
| `src/common/path_state.cpp` `describe()` | 37 |

`slot_name()` already covers the enum; none of the three iterates it. The visible
cost: `DBF_X64` is set in `initialize()`, consumed by the shipped GUI core, and
absent from the startup banner -- so a maintainer reading `INIT: Paths` sees
`DBF` and has no way to know the flavor slots are live. Same shape as the commit
table this session had to delete from its own closeout: **a hand-written list
cannot stay true, and three of them cannot agree.** Owner ruled: report, do not
fix.

## 7. Open

- **Enforce section 10.** `manifest.py` should refuse a `SOURCE` whose `Table` does not resolve, which the contract has declared for a day and nothing has done.
- **Move the corpus to a declared workspace.** All 22 fixtures resolve through `R70_DBF` today. The `DTSHEMA 2` workspace the maintainer supplied is the shape; making the fixtures use it is a unit.
- **`wx_host.cpp` reads `SOURCE`** instead of `UIDEF_TABLES`. Its own comment already names this.
- **`Descending`** -- R73.6, still an owner decision.
- **MSVC** -- unchanged, and still the oldest.

## 9. R82.3 -- the correction, made the same day: I named the wrong format version

**`WORKSPACE OPEN`'s implementation contradicts section 5 of this ruling, and the
format I should have been pointing at already exists.**

### 9.1 What a DTSHEMA 2 row actually declares

Section 5 says a `DTSHEMA 2` row is "a DECLARED, per-area, readable statement of
where a table is." Measured in `src/cli/cmd_workspace.cpp`:

```cpp
static inline fs::path resolve_relative_to_root(const fs::path& p) {
    if (p.is_absolute()) return p;
    return fs::weakly_canonical(dbf_root() / p);      // dbf_root() == Slot::DBF
}
```

`dbf=BUILDING.dbf` is a BARE NAME resolved against `Slot::DBF`, which is what
`SETPATH` sets. And the shipped corpus proves it: `mcc_x64.dtschema` and
`mcc_x32.dtschema` have **identical `dbf=` lines** for all thirteen areas and
differ only in `index=`, `indextype=` and `tag=`.

**A v2 row declares WHICH table, not WHERE.** Location still comes from ambient
state -- the exact thing section 10 forbids and this ruling claimed the workspace
had solved.

### 9.2 DTSHEMA 3, owner-chartered 2026-08-11, nine days before I asserted otherwise

```cpp
// v3 declarative lines (owner-chartered 2026-08-11). Roots make the
// posture SELF-LOCATING: the v3 loader resolves relative dbf/index
// entries against these instead of demanding a pre-set environment.
out << "FLAVOR "   << fl << "\n";
out << "DBFROOT "  << s8(rootDbf)  << "\n";
out << "IDXROOT "  << s8(rootIdx)  << "\n";
out << "LMDBROOT " << s8(paths::get_slot(paths::Slot::LMDB)) << "\n";
```

That is this ruling's requirement, designed, chartered and implemented before this
ruling was written. It even records `FLAVOR` -- measured from the open areas --
which is the fact R73 spent a ruling establishing.

**Nothing uses it.** Every `.dtschema` on disk begins `DTSHEMA 2`; v3 is opt-in
through a trailing `V3` keyword on `WORKSPACE SAVE`, and v2 stays the default "so
every proven path is untouched."

So the ruling in section 2 stands unchanged -- **location is a workspace fact** --
and section 5's clause was pointing at the wrong version. The corpus unit in
section 7 shrinks accordingly: it is not a format change, it is

```
WORKSPACE SAVE mcc_x64 V3
```

### 9.3 The failure, named because it is now a pattern

This is the **third** time today I described a mechanism from its shape instead of
reading how it resolves. R79's backend table asserted capability from toolkits
(corrected by R80). R81.4 called a path "not on disk" when it had lost a `src/`
prefix (corrected by R81.5). Here I called a v2 workspace row a location statement
because the maintainer had pasted one and it had a `dbf=` field in it.

Every time, **the artifact I reasoned from was the one already in front of me**,
and the fuller thing was one file away. That is the house's own doctrine -- *a
search shaped by the object you have cannot find an object with a different
schema* -- and it applies to the object someone hands you as much as to a grep.
The house rule *always look for prior art* is the specific defence, and R82 did
not obey it: I cited a format version from a paste instead of reading the format.

### 9.4 Two things the same reading turned up

**R82.4, and it sharpens R73.7.** `mcc_x64.dtschema` declares `tag=none` for all
thirteen areas. `mcc_x32.dtschema` declares real tags -- `BLDG`, `CLS_ID`, `CID`,
`DEPT_ID` and so on. So "no active order on x64" is not only the directory-scan
door R73.7 found; **the shipped x64 workspace file itself declares no tags while
its x32 twin does.** That is an asymmetry between two files, not a design
decision, and it is why the maintainer's transcript showed `Order: ASCEND` with
`Active tag : (none)`. Reported to the workspace owner.

**The house already answered "name a slot instead of a path" -- at the invocation.**
`resolve_open_target` accepts ten slot names as command shorthand, so
`WORKSPACE OPEN DBF` means the configured slot and not a directory called `dbf`,
with a comment preserving `DO X64` + `WORKSPACE OPEN DBF`. The slot vocabulary is
real and it is spoken by the COMMAND. That is independent support for the owner
ruling in section 2: the document does not name a slot because the invocation
already does.

## 8. Good Neighbor

| | |
|---|---|
| What changed | This ruling incl. the same-day correction in section 9; contract section 10's clause, corrected to name DTSHEMA 3; ledger rows; the closeout's Owed table. **No code changed** |
| Whose area | AIF-120. `src/` untouched; R82.1 is reported to the engine lane, not fixed |
| Authorization | maintainer, in-session: "check cmd_setpath.cpp for consumption", then the two owner rulings |
| How to verify | `python3 -c "import re;print(len(re.findall(r'case Slot::', open('src/common/path_state.cpp').read())))"` for the enum coverage; `sed -n '286,297p' src/cli/cmd_init.cpp` and `dump()` in `src/cli/cmd_setpath.cpp` for the two shorter lists; `gui/uidef/wx_host.cpp:121` for the environment resolution |
| How to undo | `git revert`. Nothing executable moved |
| Risk | none to running code. The risk this ruling ADDRESSES is a contract section that has been true on paper and unimplemented in every backend |
