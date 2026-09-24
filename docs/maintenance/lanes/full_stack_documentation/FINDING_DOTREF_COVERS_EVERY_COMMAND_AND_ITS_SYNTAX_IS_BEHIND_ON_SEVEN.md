# dotref.hpp covers every command, and its SYNTAX is behind on seven of them

    Measured : 2026-09-24, HEAD 5a69fec5a
    By       : member.ai.claude.cowork, for member.derald
    Lane     : full_stack_documentation (AIF-068)
    Asked    : "verify dotref.hpp is current from the new cmd_files and changes"
    Answer   : COVERAGE is current and gated. SYNTAX is not, and is not gated.
               One entry (AUTODBF) is not merely incomplete -- it is BACKWARDS.
    Status   : review-needed. Nothing was changed; this is a read.

## 1. The two questions "is dotref current" can mean

A `dotref.hpp` entry is a tuple: **name, syntax, summary, supported**. Those age
independently and only ONE of them is checked by anything.

    COVERAGE  does every registered command have an entry?        GATED
    SYNTAX    does the entry's syntax string describe what the
              handler now accepts?                                NOT GATED

`refcheck_v1.py` answers the first and does it well. **Nothing answers the
second**, and that is where a month of handler work has gone.

## 2. COVERAGE -- current, and the gate agrees

    dotref.hpp last changed   2026-09-13  (b6dabae63)
    src/cli/shell_commands.cpp 2026-09-11  -- OLDER, so no central registration
                                              has been added since
    registry distinct tokens  247
    dotref.hpp entries        268

    registered but NOT in dotref.hpp : 1   -> `!`
    in dotref.hpp but NOT registered : 22  -> spaced spellings of registered
                                             commands (SET CASE, SET CDX,
                                             BUILD VECTORS, REL ENUM, ...)

`!` is a punctuation-only token, which the METACOLLECT SYSCMD contract already
rules is an ENTRY VARIANT and does not get a canonical row. The 22 are the
spaced-spelling catalog entries the parent commands serve.

    refcheck_v1.py:  dotref 268 entries -- 252 cmd, 2 fn, 14 sub-forms,
                     0 PHANTOM.  PASS.

**So on coverage the answer is yes, and it is yes because a gate keeps it yes.**

## 3. SYNTAX -- behind on seven, wrong on one

24 `cmd_*.cpp` files have changed since dotref.hpp was last touched. Comparing
each command's dotref syntax string against the `@dottalk.usage v1` header in its
own handler -- declaration 3 of the three the x64base skill names:

    command      header usage forms    dotref syntax string
    ---------    ------------------    --------------------------------------
    WORKSPACE            55            5 verbs of the 21 the dispatcher accepts
    SET                  53            SET [<option> [<value>]]     (BY DESIGN)
    DOTSCRIPT            12            DOTSCRIPT <file.dts>
    USE                  10            USE <table> [ALIAS <name>] [NOINDEX]
    AUTODBF               9            AUTODBF [USAGE|<source> [TO <dbf>]]
    IMPORTSQL             7            IMPORTSQL [USAGE|<args...>]
    COPY                  5            COPY <source> TO <target>

**SET is not a defect and should not be counted as one.** Its dotref syntax is
deliberately generic because its sub-forms are 17 SEPARATE dotref entries
(`SET CASE`, `SET CDX`, ...). That is the designed pattern, and refcheck's
"14 sub-forms" is it working.

The other six are real. Named:

    AUTODBF    dotref: AUTODBF <source> TO <dbf>
               handler: AUTODBF <table> FROM <csvfile> [HEADER|NOHEADER|AUTO]
               ** TO versus FROM. THE DIRECTION IS INVERTED. **
    COPY       dotref: COPY <source> TO <target>
               handler: COPY TO <DBF> [WITH SIDECARS] [OVERWRITE]
                        COPY TO <DBF> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64>
                                      [KEY DROP] [OVERWRITE]
                        COPY TO <DBF> AS X64 VECTOR [KEY DROP] [OVERWRITE]
                        COPY FILE <SRC> TO <DST> [OVERWRITE]
    DOTSCRIPT  TRACE / TRACE ON / TRACE OFF and 6 more forms absent
    IMPORTSQL  PREVIEW, VALIDATE, SCHEMA, CREATE, FILE all absent
    USE        AGAIN, FREE, and the no-argument CLOSE form absent
    WORKSPACE  absent: NEW SWITCH REGISTRY DESTROY DELETE PURGE CATALOG ADD VIEW
               present: OPEN CLOSE SAVE LOAD WRITEBACK

**AUTODBF is the one that costs an operator a failed command**, not just a thin
page. Everything else under-describes; AUTODBF mis-describes.

## 4. WHY it happened, and it is not neglect

**dotref.hpp WAS edited after the handler work landed.** `b6dabae63` on 09-13 is
newer than the AIF-078 workspace lane. The WORKSPACE verbs still are not there.

That is the whole mechanism, and it is worth stating as a rule:

> **dotref.hpp is a MANUAL SEED LIST. Editing it for one reason does not make it
> current for another. A dotref EDIT is not a dotref REFRESH.**

The owner said as much on 2026-08-21 -- *"dotref.hpp is a manual collection of
commands that we add to dotref.hpp to start the harvest"* -- and the consequence
is that coverage stays current (because a new command is noticed when it is
added) while SYNTAX silently rots (because nothing notices when an EXISTING
command grows a verb).

## 5. The gap, stated so it can be closed

`refcheck_v1.py` asks *"does this entry resolve to something?"* For WORKSPACE the
answer is yes -- WORKSPACE exists -- and the check passes while the syntax names
five verbs of twenty-one. **It is a membership check, exactly like Gate 4's 6',
and it has the same blind spot: it cannot see a SUBSTITUTION or an
UNDER-DESCRIPTION.**

The runnable form of the missing check, and it is cheap because both sides are
already machine-readable:

    for each dotref entry whose owning handler declares an `@dottalk.usage v1`
    `usage:` block, compare the VERB SET in the dotref syntax string against the
    verb set in the header block. Report every verb the header declares and the
    syntax omits.

That is a `--syntax-drift` flag on `refcheck_v1.py`, not a new tool, and it would
have printed all six of section 3 today. **It cannot be a HARD gate** -- a
generic parent like SET must be allowed to delegate to its sub-entries -- so it
wants an allow-list of delegating parents, in the R127 shape.

## 6. What was NOT measured

- **The dispatcher was not compared to the header.** Section 3 compares dotref to
  the HEADER, and takes the header as current because it is maintained beside the
  code it documents. The x64base skill records a four-day window in which the
  header was six verbs behind the dispatcher on WORKSPACE, so the header is
  EVIDENCE, not authority. A full three-way diff is the next measurement.
- **The store was not rebuilt.** These are source-side facts. What the HELP store
  currently publishes for these seven commands follows from the exe that built it,
  and dotref is COMPILED IN, so the store cannot be ahead of `b6dabae63`.
- **No repair is proposed.** dotref is the owner's curated catalog; editing seven
  entries is a source change that requires a rebuild and a store refresh, and the
  choice of wording is his.

## 7. Portal state, read the same session

    TIER0_STATE generated 2026-09-24T03:02:09Z, HEAD e0a558774
    -- already one commit stale: 5a69fec5a landed at 02:48 the same morning.
    Two standing staleness warnings it raises itself:
      * SESSION_CLOSEOUT_EVIDENCE_TRACKING_AND_PORTAL_2026-09-20.md is on disk
        and NOT TRACKED -- a session's record that never landed.
      * the newest tracked closeout is 9 commits behind HEAD.
    Claimed lanes now run to AIF-168 (AIF-131 was the newest in August).

## Good Neighbor

    What changed  : one new document. No source, no catalog, no store, no tool.
    Whose area    : lane full_stack_documentation / AIF-068. Section 3 concerns
                    include/dotref.hpp, which is the owner's curated catalog --
                    reported, not edited.
    Authorization : member.derald, 2026-09-24 -- "verify dotref.hpp is current
                    from the new cmd_files and changes".
    How to verify : refcheck_v1.py -- expect dotref 268 / 0 PHANTOM / PASS.
                    find src -name 'cmd_*.cpp' -newer include/dotref.hpp  -> 24.
                    grep -oE 'sub_command == "[a-z_?]+"' src/cli/cmd_workspace.cpp
                      | sort -u | wc -l  -> 21.
                    sed -n '24,30p' src/cli/cmd_copy.cpp for COPY's five forms;
                    grep -n '"WORKSPACE"' include/dotref.hpp for its five.
    How to undo   : delete this document.
