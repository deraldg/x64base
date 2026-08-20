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

## 8. Good Neighbor

| | |
|---|---|
| What changed | This ruling; contract section 10 gains the workspace-is-not-ambient clause; ledger rows; the closeout's Owed table gains R82.1. **No code changed** |
| Whose area | AIF-120. `src/` untouched; R82.1 is reported to the engine lane, not fixed |
| Authorization | maintainer, in-session: "check cmd_setpath.cpp for consumption", then the two owner rulings |
| How to verify | `python3 -c "import re;print(len(re.findall(r'case Slot::', open('src/common/path_state.cpp').read())))"` for the enum coverage; `sed -n '286,297p' src/cli/cmd_init.cpp` and `dump()` in `src/cli/cmd_setpath.cpp` for the two shorter lists; `gui/uidef/wx_host.cpp:121` for the environment resolution |
| How to undo | `git revert`. Nothing executable moved |
| Risk | none to running code. The risk this ruling ADDRESSES is a contract section that has been true on paper and unimplemented in every backend |
