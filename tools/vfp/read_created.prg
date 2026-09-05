* ============================================================
* read_created.prg -- AIF-091 M2 ACCEPTANCE CRITERION
*
* WRITTEN BEFORE THE CODE IT JUDGES, ON PURPOSE. Every proof in
* this lane so far graded our READER against a file Visual
* FoxPro wrote. CREATE inverts that: WE produce the file. A
* create-then-read test in our own engine would be our encoder
* agreeing with our decoder -- the exact closed loop that let
* dbf_create.cpp and the reader share a wrong byte offset for
* the life of this project.
*
* THE ONLY NON-CIRCULAR CHECK IS THE OTHER IMPLEMENTATION.
* This program opens a table OUR CREATE wrote and asks Visual
* FoxPro what it sees. VFP is the authority the format belongs
* to; if it disagrees with us, we are wrong.
*
* IT ALSO CLOSES THE LOOP IN BOTH DIRECTIONS. Section 4 has VFP
* APPEND a row into our table, with a NULL and a short Varchar.
* Then the engine reads that row back. Three legs:
*
*   we write  -> VFP reads      (sections 2 and 3)
*   VFP writes -> VFP reads     (section 4)
*   VFP writes -> we read       (run the dump after this)
*
* No leg is our code talking to itself.
* ------------------------------------------------------------
* WHAT PASS LOOKS LIKE, FIXED IN ADVANCE
*
* S1  USE succeeds. No error, no modal dialog.
* S2  DISPLAY STRUCTURE shows FOUR user fields and NOT the
*     hidden _NullFlags column -- VFP hides its own system
*     column, and if ours shows up as a field we built it
*     wrong. The "Nulls" column must read:
*        ID     N   4      Nulls Yes
*        VNAME  V  10      Nulls Yes
*        VFULL  V  10      Nulls No
*        PLAIN  C   5      Nulls No
* S3  LIST prints the rows our CREATE path wrote, with .NULL.
*     shown for null cells and Varchar values NOT padded with
*     a stray length byte.
* S4  VFP can APPEND and REPLACE, including WITH .NULL., and
*     ISNULL() then reads .T. for those cells.
* S5  RECCOUNT() rises by exactly one.
*
* ANY VFP ERROR AT ALL IS A FAILURE, including one this script
* traps and prints. A trapped error is still a file VFP could
* not use.
* ------------------------------------------------------------
* ERRORS ARE TRAPPED, NOT DISPLAYED. A malformed DBF can raise
* a MODAL dialog, which halts the VFP session and blocks this
* whole conversation until somebody clicks it -- that happened
* on 2026-09-04 with a Locate Database box. ON ERROR turns that
* into a printed line instead.
* ------------------------------------------------------------
* HOW nullnew.dbf IS PRODUCED, BEFORE THIS SCRIPT IS RUN
*
* This program opens a file it does not create. Make it in the
* DotTalk++ shell (datarun.ps1) first:
*
*   SET PATH DBF d:\code\ccode\tools\vfp\fixtures
*   CREATE VFP nullnew (id N(4) NULL, vname V(10) NULL,
*                       vfull V(10), plain C(5))
*   USE nullnew
*   APPEND
*   REPLACE id WITH 1
*   REPLACE vname WITH "AB"
*   REPLACE vfull WITH "0123456789"
*   REPLACE plain WITH "PP"
*   APPEND
*   REPLACE id WITH 2
*   REPLACE vname WITH "0123456789"
*   REPLACE vfull WITH "0123456789"
*   REPLACE plain WITH "QQ"
*   CLOSE
*
* (the CREATE is one line in the shell -- it is wrapped here
* only to fit this comment column)
*
* ROW 1 IS SHORT AND ROW 2 IS FULL WIDTH ON PURPOSE. The
* varlength bit is SET when a Varchar is NOT full, so one row
* alone can only ever exercise one polarity.
*
* THE VERB IS BARE `APPEND`. NOT `APPEND BLANK`. Measured
* 2026-09-05: the shell registry holds `APPEND_BLANK` with an
* underscore and nothing routes the two-word spelling, so
* `APPEND BLANK` reaches cmd_APPEND, reads BLANK as an
* unrecognized argument, prints the usage block, and appends
* NOTHING -- after which every REPLACE answers "no current
* record" and the table is silently left EMPTY. This hazard was
* already recorded in the WSLADDER regression entry and it was
* repeated here anyway. `CLOSE`, not bare `USE`, closes it.
*
* Once this script has run clean, PRESERVE THE RESULT as
* fixtures/nullwrote.DBF -- that copy is the evidence
* dottalkpp_vfp_foreign_write_test reads, and nullnew.dbf stays
* the regenerable scratch path this script writes into.
* ============================================================
PUBLIC gcErr, gnErrs
gcErr  = ""
gnErrs = 0
ON ERROR gcErr = "VFP ERROR " + LTRIM(STR(ERROR())) + ": " + MESSAGE() + " [line " + LTRIM(STR(LINENO())) + "]"

SET SAFETY OFF
SET TALK OFF
SET DELETED OFF
CLOSE TABLES ALL

? "============================================================"
? "AIF-091 M2 -- can Visual FoxPro read a table OUR CREATE wrote?"
? "============================================================"
?

* ---------- S1: does it open at all --------------------------
? "-- S1: USE --"
gcErr = ""
USE d:\code\ccode\tools\vfp\fixtures\nullnew.dbf EXCLUSIVE
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   ? "  VFP could not open the file. Nothing below is meaningful."
   gnErrs = gnErrs + 1
   ON ERROR
   RETURN
ENDIF
? "  ok -- opened, RECCOUNT() = " + LTRIM(STR(RECCOUNT()))
?

* ---------- S2: what does VFP think the structure is ---------
? "-- S2: DISPLAY STRUCTURE (read the Nulls column) --"
gcErr = ""
DISPLAY STRUCTURE
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ENDIF
?
? "  FCOUNT() = " + LTRIM(STR(FCOUNT())) + "   (want 4 -- _NullFlags must NOT be counted)"
?

* ---------- S3: what does VFP read in our rows ---------------
? "-- S3: LIST the rows our CREATE path wrote --"
gcErr = ""
LIST
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   gnErrs = gnErrs + 1
ENDIF
?

* ---------- S4: let VFP write into our table -----------------
? "-- S4: VFP APPENDs a row with a NULL and a short Varchar --"
gcErr = ""
LOCAL lnBefore
lnBefore = RECCOUNT()
APPEND BLANK
REPLACE id    WITH .NULL.
REPLACE vname WITH "VFPW"
REPLACE vfull WITH "0123456789"
REPLACE plain WITH "VF"
IF NOT EMPTY(gcErr)
   ? "  FAIL " + gcErr
   ? "  VFP refused to write into our table."
   gnErrs = gnErrs + 1
ELSE
   ? "  ok -- appended"
ENDIF
?
? "-- S4b: VFP's own ISNULL() on the row it just wrote --"
? "  ISNULL(id)    = " + IIF(ISNULL(id),    ".T. <- want .T.", ".F. <- WRONG")
? "  ISNULL(vname) = " + IIF(ISNULL(vname), ".T. <- WRONG",    ".F. <- want .F.")
? "  LEN(ALLTRIM(vname)) = " + LTRIM(STR(LEN(ALLTRIM(vname)))) + "   (want 4)"
? "  vfull = [" + vfull + "]   (want the full 10 chars)"
?
? "-- S5: record count --"
? "  before = " + LTRIM(STR(lnBefore)) + "   after = " + LTRIM(STR(RECCOUNT()))
?
? "-- the whole table as VFP now sees it --"
LIST
?

USE
ON ERROR

? "============================================================"
IF gnErrs = 0
   ? "VFP RAISED NO ERRORS. Read S2's Nulls column and S4b by eye --"
   ? "a clean run is necessary, not sufficient."
ELSE
   ? "FAILURES: " + LTRIM(STR(gnErrs)) + " -- the file is not one VFP can use."
ENDIF
? "NEXT LEG: read nullnew.DBF back with the engine and compare the"
? "bitmap against what VFP just wrote. That is the third direction"
? "and the one no single tool can fake."
? "============================================================"
