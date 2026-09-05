* ============================================================
* read_nulls.prg -- AIF-091 SET-TO-NULL ACCEPTANCE CRITERION
*
* WRITTEN BEFORE THE RUN IT JUDGES. The engine can now write a
* null; every test of that in our own suite compares our bytes
* to bytes Visual FoxPro wrote EARLIER, which is strong but
* still offline. This asks the live question: given a null WE
* wrote, does VFP's own ISNULL() say .T.
*
* IT MATTERS MORE HERE THAN ANYWHERE ELSE IN THIS LANE, and the
* reason is a gap rather than a doubt. NOTHING IN OUR CLI CAN
* DISPLAY A NULL. LIST, DISPLAY and SMARTLIST all render a
* field through get(), a null cell returns an empty string, and
* an empty string is what a blank cell returns too. So at our
* own prompt a successful REPLACE ... WITH NULL and a REPLACE
* ... WITH "" look identical. VFP prints .NULL. This script is
* the display we do not have.
* ------------------------------------------------------------
* HOW nullset.dbf IS PRODUCED, BEFORE THIS SCRIPT IS RUN
*
* In the DotTalk++ shell (datarun.ps1):
*
*   SET PATH DBF d:\code\ccode\tools\vfp\fixtures
*   CREATE VFP nullset (id N(4) NULL, vname V(10) NULL,
*                       vfull V(10) NULL, plain C(5))
*   USE nullset
*   APPEND
*   REPLACE id WITH 1
*   REPLACE vname WITH "AAA"
*   REPLACE vfull WITH "0123456789"
*   REPLACE plain WITH "P1"
*   APPEND
*   REPLACE id WITH 2
*   REPLACE vname WITH "BBB"
*   REPLACE vfull WITH "0123456789"
*   REPLACE plain WITH "P2"
*   REPLACE id WITH NULL
*   APPEND
*   REPLACE id WITH 3
*   REPLACE vname WITH "CCC"
*   REPLACE vfull WITH "0123456789"
*   REPLACE plain WITH "P3"
*   REPLACE vname WITH NULL
*   CLOSE
*
* (the CREATE is one line in the shell; wrapped here to fit)
*
* ROW 1 IS THE CONTROL AND IS NOT DECORATION. An engine that
* wrote the null bit for every field, or that corrupted the
* bitmap, passes rows 2 and 3 and fails row 1. Without it,
* "ISNULL is .T. where we asked" cannot be told apart from
* "ISNULL is .T. everywhere".
*
* THE NEIGHBOUR CHECKS ARE THE OTHER HALF. Row 3's VFULL must
* still read the full ten characters after VNAME beside it was
* nulled. A write that gets the target field right and quietly
* rewrites the rest passes every check that only reads the
* field under change -- the AIF-110 shape.
* ------------------------------------------------------------
* WHAT PASS LOOKS LIKE, FIXED IN ADVANCE
*
*   row 1   ISNULL:  ID .F.   VNAME .F.   VFULL .F.
*   row 2   ISNULL:  ID .T.   VNAME .F.   VFULL .F.
*   row 3   ISNULL:  ID .F.   VNAME .T.   VFULL .F.
*
*   row 2 VNAME still reads BBB
*   row 3 VFULL still reads 0123456789
*   PLAIN is NOT nullable and REPLACE PLAIN WITH NULL must have
*     been REFUSED at the prompt -- if row 3 PLAIN reads P3,
*     the refusal held.
*
* ANY VFP ERROR AT ALL IS A FAILURE, including one this script
* traps and prints. ON ERROR exists because a malformed DBF can
* raise a MODAL dialog that halts the VFP session until someone
* clicks it -- that happened on 2026-09-04 with a Locate
* Database box.
* ============================================================
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
? "AIF-091 -- does VFP read the NULLs our engine wrote?"
? "============================================================"
?

? "-- S1: USE --"
gcErr = ""
USE d:\code\ccode\tools\vfp\fixtures\nullset.dbf EXCLUSIVE
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   ? "  VFP could not open the file. Nothing below is meaningful."
   gnErrs = gnErrs + 1
   ON ERROR
   RETURN
ENDIF
? "  ok -- opened, RECCOUNT() = " + LTRIM(STR(RECCOUNT()))
IF RECCOUNT() <> 3
   ? "  FAIL -- expected 3 records. The fixture is not the one this"
   ? "         script was written against; every check below is void."
   gnErrs = gnErrs + 1
   USE
   ON ERROR
   RETURN
ENDIF
?

? "-- S2: DISPLAY STRUCTURE (Nulls must read Yes/Yes/Yes/No) --"
gcErr = ""
DISPLAY STRUCTURE
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ENDIF
?

? "-- S3: LIST -- VFP prints .NULL. where our own CLI prints blank --"
gcErr = ""
LIST
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ENDIF
?

? "-- S4: ISNULL(), cell by cell, against the table above --"
GOTO 1
? "  row 1 (control -- nothing was nulled)"
? "    ID    = " + IIF(ISNULL(id),    ".T. <- WRONG", ".F. ok")
? "    VNAME = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
? "    VFULL = " + IIF(ISNULL(vfull), ".T. <- WRONG", ".F. ok")
IF ISNULL(id) OR ISNULL(vname) OR ISNULL(vfull)
   gnBad = gnBad + 1
ENDIF

GOTO 2
? "  row 2 (we nulled ID)"
? "    ID    = " + IIF(ISNULL(id),    ".T. ok",       ".F. <- WRONG")
? "    VNAME = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
? "    VFULL = " + IIF(ISNULL(vfull), ".T. <- WRONG", ".F. ok")
IF NOT ISNULL(id) OR ISNULL(vname) OR ISNULL(vfull)
   gnBad = gnBad + 1
ENDIF
? "    VNAME value = [" + IIF(ISNULL(vname), "<null>", ALLTRIM(vname)) + "]   (want BBB -- the neighbour did not move)"

GOTO 3
? "  row 3 (we nulled VNAME)"
? "    ID    = " + IIF(ISNULL(id),    ".T. <- WRONG", ".F. ok")
? "    VNAME = " + IIF(ISNULL(vname), ".T. ok",       ".F. <- WRONG")
? "    VFULL = " + IIF(ISNULL(vfull), ".T. <- WRONG", ".F. ok")
IF ISNULL(id) OR NOT ISNULL(vname) OR ISNULL(vfull)
   gnBad = gnBad + 1
ENDIF
? "    VFULL value = [" + IIF(ISNULL(vfull), "<null>", vfull) + "]   (want the full ten characters)"
? "    PLAIN value = [" + ALLTRIM(plain) + "]   (want P3 -- the NOT NULL refusal held)"
?

? "-- S5: can VFP still WRITE to the table after our nulls? --"
gcErr = ""
GOTO 3
REPLACE vname WITH "VFPW"
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ELSE
   ? "  ok -- VFP replaced the null VNAME with [" + ALLTRIM(vname) + "]"
   ? "  ISNULL(vname) now = " + IIF(ISNULL(vname), ".T. <- WRONG", ".F. ok")
   IF ISNULL(vname)
      gnBad = gnBad + 1
   ENDIF
ENDIF
?

USE
ON ERROR

? "============================================================"
IF gnErrs = 0 AND gnBad = 0
   ? "PASS -- VFP reads .NULL. exactly where our engine wrote one,"
   ? "and nowhere else. Read S2's Nulls column by eye as well."
ELSE
   ? "FAIL -- VFP errors: " + LTRIM(STR(gnErrs)) + "   wrong rows: " + LTRIM(STR(gnBad))
ENDIF
? "NOTE: our own CLI cannot show a null. That is why this script"
? "exists and why a green LIST at our prompt proves nothing here."
? "============================================================"
