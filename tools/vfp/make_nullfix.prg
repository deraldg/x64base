* ============================================================
* make_nullfix.prg -- AIF-091 M1, R1a fixture
*
* Builds a VFP table whose _NullFlags bitmap DISCRIMINATES the
* bit-assignment order. VNAME is the load-bearing field: it is
* both NULLABLE and VARLENGTH, so it gets TWO bits, and the
* format says the FULL bit is the LOWER of the two.
*
* Predicted bit layout (physical field order):
*   ID      null = bit 0
*   VNAME   full = bit 1, null = bit 2
*   VFULL   full = bit 3
*   PLAIN   no bits
*   -> 4 bits, so _NullFlags is 1 byte wide
*
* Predicted _NullFlags byte per row:
*   row 1   0x08   VFULL is exactly 10 chars, so FULL
*   row 2   0x05   ID null (bit 0) + VNAME null (bit 2)
*   row 3   0x02   VNAME is exactly 10 chars and NOT null
*
* If the order is flipped, rows 2 and 3 read 0x03 and 0x04.
*
* ------------------------------------------------------------
* MEASURED 2026-09-04 PM. THE THREE PREDICTIONS ABOVE ARE WRONG
* AND ARE LEFT STANDING AS THE RECORD OF WHY.
*
*   row 1   0x02      row 2   0x0F      row 3   0x08
*
* The BIT POSITIONS above are right. The POLARITY is not. I wrote
* "full -> bit set"; the format says the opposite, and so does the
* header this file was meant to test -- vfp_null_bits.hpp quotes
* Microsoft two inches above where I got it wrong:
*
*   "If a bit contains 0, the length of the value in a field equals
*    the field size (the field is full). If the bit contains 1, the
*    length of the value is less than the field size."
*
* So the bit is set when the field is NOT full -- when the trailing
* length byte is in use. Row 2 is what settles it: both V fields
* carry a length byte there and BOTH bits are set. assign_null_bits()
* and varlength_value_length() were already right; the prediction in
* this comment was typed from memory and inverted.
*
* SECOND MISS: _NullFlags carries 0x05 at descriptor byte 18 --
* system AND BINARY -- not the 0x01 the M1 design doc tells the
* CREATE path to write.
*
* THIS FIXTURE IS BUILT WRONG IN ONE PLACE. Row 2 nulls ID and VNAME
* TOGETHER, so bits 0 and 2 are never seen apart and which one
* belongs to ID is still inference. R1c needs a row with ID null and
* VNAME short but NOT null: 0x03 if the shipped rule holds, 0x06 if
* it does not. Do not add it by editing rows -- append a fourth.
*
* ------------------------------------------------------------
* R1c ROWS APPENDED 2026-09-05. THE THREE ROWS ABOVE ARE
* UNTOUCHED -- they carry the R1a result and must keep producing
* 0x02, 0x0F, 0x08 when this runs again. If they do not, the
* problem is this script, not the format.
*
* THE GAP. Row 2 nulls ID and VNAME at once, so bits 0 and 2 are
* only ever observed SET AS A PAIR. Exchanging them fits the file.
* assign_null_bits() says bit 0 is the FIRST field's, from physical
* field order -- inference, not measurement.
*
* THE TWO NEW ROWS ARE MIRRORS OF EACH OTHER. One nulls only ID,
* the other nulls only VNAME. Under the shipped rule they read
* 0x03 and 0x06; under the swap they read 0x06 and 0x03. So the
* PAIR discriminates twice over, and it also forces the two bytes
* to come back DIFFERENT -- which rules out any rule that collapses
* the two null bits into one.
*
* PREDICTED (shipped rule -- bit0 ID null, bit1 VNAME varlength,
* bit2 VNAME null, bit3 VFULL varlength; a bit is SET when the
* field is NOT full):
*
*   row 4  (.NULL., "AB", "0123456789", "RR")
*     bit0 ID null          = 1
*     bit1 VNAME not full   = 1   ("AB" + 7 spaces + CHR(2))
*     bit2 VNAME not null   = 0
*     bit3 VFULL is FULL    = 0   (exactly 10 chars, no length byte)
*     -> 0x03      swap would give 0x06
*
*   row 5  (3, .NULL., "0123456789", "SS")
*     bit0 ID not null      = 0
*     bit1 VNAME not full   = 1   (null varchar stored with CHR(0))
*     bit2 VNAME null       = 1
*     bit3 VFULL is FULL    = 0
*     -> 0x06      swap would give 0x03
*
* Last time the predictions in this header were WRONG and the code
* was right. Read the measurement, not this comment.
*
* MEASURED 2026-09-05. row 4 = 0x03   row 5 = 0x06.
* Both predictions correct. Rows 1-3 came back 0x02, 0x0F, 0x08
* unchanged -- truncating the new file to three records reproduces
* the committed R1a blob byte for byte, sha256 3c43b26e...46b34a3,
* so appending rows did not quietly re-base the R1a measurement.
*
* R1c IS CLOSED. Bit 0 is the FIRST field's null bit, measured.
* ============================================================
SET SAFETY OFF
CLOSE TABLES ALL

CREATE TABLE d:\code\ccode\tools\vfp\fixtures\nullfix ;
    (id N(4) NULL, vname V(10) NULL, vfull V(10), plain C(5))

INSERT INTO nullfix VALUES (1, "ABC", "0123456789", "XY")
INSERT INTO nullfix VALUES (.NULL., .NULL., "AB", "ZZ")
INSERT INTO nullfix VALUES (2, "0123456789", "C", "QQ")

* ---- R1c: appended 2026-09-05. Do not reorder or edit the three above. ----
INSERT INTO nullfix VALUES (.NULL., "AB", "0123456789", "RR")
INSERT INTO nullfix VALUES (3, .NULL., "0123456789", "SS")

LIST
USE
SET SAFETY ON

? "nullfix written to d:\code\ccode\tools\vfp\fixtures"
