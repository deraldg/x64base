       IDENTIFICATION DIVISION.
       PROGRAM-ID. FIRST-COBOL-TEST.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
      *> REPAIRED 2026-07-26: the ASSIGN path was stale. It pointed at
      *> ...\dottalkpp\data\students_ro.dat, but COBOL EXPORT STUDENTS
      *> writes to ...\dottalkpp\data\projects\cobol\data\students_ro.dat
      *> Nothing had ever written to the old location, so OPEN INPUT failed
      *> with libcob status 35 immediately after a successful export.
      *> Found by tests/conversion/12_cobol_fixed_record_v1.dts.
           SELECT STUDENT-FILE
               ASSIGN TO
           "D:\code\ccode\dottalkpp\data\projects\cobol\data\students_ro.dat"
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
      *> THE COPYBOOK IS THE CROSSWALK. This FD sums to exactly 109 bytes,
      *> the record length of the source dBASE III STUDENTS.DBF, field for
      *> field:
      *>   X(8) SID N(8,0)  . X(20) LNAME C(20) . X(15) FNAME C(15)
      *>   X(8) DOB D(8)    . X(1)  GENDER C(1) . X(4)  MAJOR C(4)
      *>   X(8) ENROLL_D D(8) . X(5) GPA N(4,2) . X(40) EMAIL C(40)
      *> The export is 22,200 bytes = 200 x 111, where 111 = 109 + CRLF
      *> under LINE SEQUENTIAL. Exact division is the fidelity proof: a
      *> fixed-record file carries no header count, so it is the only
      *> evidence that every row crossed.
       FD  STUDENT-FILE.
       01  STUDENT-REC.
           05 SID-FLD        PIC X(8).
           05 LNAME-FLD      PIC X(20).
           05 FNAME-FLD      PIC X(15).
           05 DOB-FLD        PIC X(8).
           05 GENDER-FLD     PIC X(1).
           05 MAJOR-FLD      PIC X(4).
           05 ENROLL-D-FLD   PIC X(8).
           05 GPA-FLD        PIC X(5).
           05 EMAIL-FLD      PIC X(40).

       WORKING-STORAGE SECTION.
       01  EOF-FLAG          PIC X VALUE "N".
       01  REC-COUNT         PIC 9(7) VALUE 0.

       PROCEDURE DIVISION.
           OPEN INPUT STUDENT-FILE

           PERFORM UNTIL EOF-FLAG = "Y"
               READ STUDENT-FILE
                   AT END
                       MOVE "Y" TO EOF-FLAG
                   NOT AT END
                       ADD 1 TO REC-COUNT
                       DISPLAY SID-FLD "  "
                               LNAME-FLD "  "
                               FNAME-FLD "  "
                               GPA-FLD
               END-READ
           END-PERFORM

           CLOSE STUDENT-FILE
           DISPLAY "RECORDS READ: " REC-COUNT
           STOP RUN.
