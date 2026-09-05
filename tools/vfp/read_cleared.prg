* ============================================================
* read_cleared.prg -- AIF-091 CLEAR-A-NULL ACCEPTANCE CRITERION
*
* THE ONE DIRECTION VISUAL FOXPRO HAS NEVER BEEN ASKED ABOUT.
*
* Every acceptance script in this folder asks the same question:
* given a null WE wrote, does VFP's ISNULL() say .T. Not one of
* them asks the inverse -- given a cell we UN-NULLED, does VFP
* say .F. That asymmetry is not a stylistic gap. It is exactly
* where a defect hid for five commits: until 22c748381 a value
* write stored the value AND re-committed the null bit, so a
* cell read "restored" to our own expression evaluator and
* .NULL. to our own LIST, and no instrument in the lane pointed
* the right way to notice.
*
* A FEATURE PROVEN IN ONE DIRECTION IS NOT PROVEN.
*
* dottalkpp_vfp_set_null_test arm E already grades our cleared
* bytes against bytes VFP wrote on row 1 of nullfix.DBF, which
* is real evidence -- but OUR engine did the writing in that
* comparison. This is the outside witness.
* ------------------------------------------------------------
* THE FIXTURE IS PRODUCED BY THE REGRESSION SPEC, NOT BY HAND.
*
* In the DotTalk++ shell (datarun.ps1):
*
*   DOTSCRIPT "D:\code\ccode\dottalkpp\data\scripts\vfp_null_assertions.dts"
*
* That spec rebuilds NULLSPEC from scratch every run and leaves
* it in the state this script judges. Re-running the spec is
* how you refresh the fixture; this script never writes, so it
* can be re-run against one fixture as often as you like.
*
* THE TABLE, AS THE SPEC LEAVES IT:
*
*   rec 1  ID 1  VNAME "alpha"     PLAIN "control"  nothing nulled
*   rec 2  ID 2  VNAME <blank>     PLAIN "blankvn"  never written
*   rec 3  ID 3  VNAME "restored"  PLAIN "nullvn"   NULLED, THEN CLEARED
*   rec 4  ID .NULL.  VNAME "delta"    PLAIN "nullid"
*   rec 5  ID 5  VNAME .NULL.     PLAIN "nulltwo"  nulled via .NULL.
* ------------------------------------------------------------
* WHAT PASS LOOKS LIKE, FIXED IN ADVANCE
*
*   row 1   ISNULL:  ID .F.   VNAME .F.
*   row 2   ISNULL:  ID .F.   VNAME .F.   <- BLANK IS NOT NULL
*   row 3   ISNULL:  ID .F.   VNAME .F.   <- THE WITNESS
*   row 4   ISNULL:  ID .T.   VNAME .F.
*   row 5   ISNULL:  ID .F.   VNAME .T.
*
*   row 3 VNAME reads "restored" -- value AND bit agree
*   row 5 VNAME is .NULL.       -- the bit we did NOT clear
*
* ROWS 3 AND 5 ARE THE PAIR THAT MATTERS. Same field, same
* table, one cleared and one not. A build that cannot clear a
* bit makes them read alike, and VFP is the one reader with no
* stake in our answer.
*
* ROW 2 IS THE SECOND DISCRIMINATOR and it grades our BLANK
* encoding rather than our null encoding: VNAME there was never
* written, so our writer emitted a zero length byte with the
* varlength bit set and the null bit clear. If VFP reads that
* as .NULL. then blank and null are the same byte pattern to
* the other engine, and the whole distinction this lane is
* built on is wrong. It has never been checked either.
*
* ANY VFP ERROR AT ALL IS A FAILURE, including one this script
* traps and prints. ON ERROR exists because a malformed DBF can
* raise a MODAL dialog that halts the VFP session until someone
* clicks it -- that happened on 2026-09-04 with a Locate
* Database box.
* ============================================================
* ------------------------------------------------------------
* WRONG-SHELL BANNER. `DO <path>` IS A LEGAL COMMAND IN BOTH
* SHELLS: Visual FoxPro runs a .prg with it, and DotTalk++
* resolves DO to DOTSCRIPT (shortcut_resolver.hpp). So a handover
* that names the window in prose and shows a DO line can be run
* in the wrong one and produce plausible output rather than a
* refusal -- measured twice on 2026-09-05. DotTalk++ accepts ?,
* IF, USE, GOTO, LIST and DISPLAY STRUCTURE, and parses
* ISNULL(id) well enough to fail with "unknown field" rather
* than "unknown function".
*
* The banner cannot HALT DotTalk++ -- RETURN is not a command
* there -- so it does the one thing it can: it is the FIRST
* thing printed, and it names the shell this file belongs to.
* ------------------------------------------------------------
? "read_cleared.prg -- THIS IS A VISUAL FOXPRO SCRIPT."
? "If you see Unknown command below, you are in DotTalk++."

PUBLIC gcErr, gnErrs, gnBad
gcErr  = ""
gnErrs = 0
gnBad  = 0
ON ERROR gcErr = "VFP ERROR " + LTRIM(STR(ERROR())) + ": " + MESSAGE() + " [line " + LTRIM(STR(LINENO())) + "]"

SET SAFETY OFF
SET TALK OFF
SET DELETED OFF
CLOSE TABLES ALL

? "============================================================"
? "AIF-091 -- does VFP agree a cell we UN-NULLED is not null?"
? "============================================================"
?

? "-- C1: USE --"
gcErr = ""
USE d:\code\ccode\dottalkpp\data\DBF\SANDBOX\NULLSPEC.dbf EXCLUSIVE
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   ? "  VFP could not open the file. Nothing below is meaningful."
   gnErrs = gnErrs + 1
   ON ERROR
   RETURN
ENDIF
? "  ok -- opened, RECCOUNT() = " + LTRIM(STR(RECCOUNT()))
IF RECCOUNT() <> 5
   ? "  FAIL -- expected 5 records. Re-run vfp_null_assertions.dts"
   ? "         to rebuild the fixture; every check below is void."
   gnErrs = gnErrs + 1
   USE
   ON ERROR
   RETURN
ENDIF
?

? "-- C2: DISPLAY STRUCTURE (ID and VNAME must read Nulls Yes) --"
gcErr = ""
DISPLAY STRUCTURE
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ENDIF
?

? "-- C3: LIST -- .NULL. must appear on rows 4 and 5 ONLY --"
gcErr = ""
LIST
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ENDIF
?

? "-- C4: ISNULL(), cell by cell --"
GOTO 1
? "  row 1 (control -- nothing was ever nulled)"
? "    ID    = " + IIF(ISNULL(id),    ".T. <- WRONG", ".F. ok")
? "    VNAME = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
IF ISNULL(id) OR ISNULL(vname)
   gnBad = gnBad + 1
ENDIF

GOTO 2
? "  row 2 (VNAME NEVER WRITTEN -- blank must not be null)"
? "    ID    = " + IIF(ISNULL(id),    ".T. <- WRONG", ".F. ok")
? "    VNAME = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
IF ISNULL(id) OR ISNULL(vname)
   ? "    ^ IF VNAME READS .T. HERE, our BLANK encoding is our NULL"
   ? "      encoding to VFP, and the distinction this lane rests on"
   ? "      is wrong. That would be the finding, not a test failure."
   gnBad = gnBad + 1
ENDIF

GOTO 3
? "  row 3 (WE NULLED IT, THEN WROTE A VALUE OVER IT -- the witness)"
? "    ID    = " + IIF(ISNULL(id),    ".T. <- WRONG", ".F. ok")
? "    VNAME = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
IF ISNULL(id) OR ISNULL(vname)
   gnBad = gnBad + 1
ENDIF
? "    VNAME value = [" + IIF(ISNULL(vname), "<null>", ALLTRIM(vname)) + "]   (want restored -- value and bit must agree)"
IF NOT ISNULL(vname) AND ALLTRIM(vname) <> "restored"
   ? "    ^ WRONG -- the bit cleared but the value did not land."
   gnBad = gnBad + 1
ENDIF

GOTO 4
? "  row 4 (we nulled the NUMERIC)"
? "    ID    = " + IIF(ISNULL(id),    ".T. ok",       ".F. <- WRONG")
? "    VNAME = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
IF NOT ISNULL(id) OR ISNULL(vname)
   gnBad = gnBad + 1
ENDIF
? "    VNAME value = [" + IIF(ISNULL(vname), "<null>", ALLTRIM(vname)) + "]   (want delta -- the neighbour field did not move)"

GOTO 5
? "  row 5 (nulled with the DOTTED spelling, never cleared)"
? "    ID    = " + IIF(ISNULL(id),    ".T. <- WRONG", ".F. ok")
? "    VNAME = " + IIF(ISNULL(vname), ".T. ok",       ".F. <- WRONG")
IF ISNULL(id) OR NOT ISNULL(vname)
   gnBad = gnBad + 1
ENDIF
?

? "-- C5: THE PAIR. Rows 3 and 5 are the same field, one cleared. --"
GOTO 3
gcErr = IIF(ISNULL(vname), "NULL", "not null")
GOTO 5
? "    row 3 VNAME is " + gcErr
? "    row 5 VNAME is " + IIF(ISNULL(vname), "NULL", "not null")
? "    (want: row 3 not null, row 5 NULL. If they read alike, the"
? "     engine cannot tell a cleared bit from a set one.)"
?

USE
ON ERROR

? "============================================================"
IF gnErrs = 0 AND gnBad = 0
   ? "PASS -- VFP agrees. A cell we un-nulled reads .F., a cell we"
   ? "left null reads .T., and a blank cell is neither. This is the"
   ? "first outside witness the CLEAR direction has ever had."
ELSE
   ? "FAIL -- VFP errors: " + LTRIM(STR(gnErrs)) + "   wrong rows: " + LTRIM(STR(gnBad))
ENDIF
? "Read C2's Nulls column and C3's .NULL. placement by eye too."
? "============================================================"
