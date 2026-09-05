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
* ============================================================
SET SAFETY OFF
CLOSE TABLES ALL

CREATE TABLE d:\code\ccode\tools\vfp\fixtures\nullfix ;
    (id N(4) NULL, vname V(10) NULL, vfull V(10), plain C(5))

INSERT INTO nullfix VALUES (1, "ABC", "0123456789", "XY")
INSERT INTO nullfix VALUES (.NULL., .NULL., "AB", "ZZ")
INSERT INTO nullfix VALUES (2, "0123456789", "C", "QQ")

LIST
USE
SET SAFETY ON

? "nullfix written to d:\code\ccode\tools\vfp\fixtures"
