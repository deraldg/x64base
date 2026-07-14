My Community College  FoxPro 2.6a Compatible DBFs (dBase III format)
---------------------------------------------------------------------
Tables (record counts approx.):
  TEACHERS  (20)
  STUDENTS  (200)
  COURSES   (100)
  CLASSES   (200)
  ENROLL    (~800)
  DEPT      (10)
  BUILDING  (8)
  ROOMS     (30)
  TERMS     (3)
  MAJORS    (12)
  STUD_MAJ  (200)
  TASSIGN   (200)

Notes:
- Files are written as dBase III (version 0x03) with no memo fields for
  maximum compatibility with FoxPro 2.6a.
- Field names are <=10 chars and uppercase; dates are YYYYMMDD.
- Indexes.

  HISTORICAL -- FoxPro 2.6a origin. Retained as provenance. NOT DotTalk++ syntax:
    STUDENTS:  INDEX ON SID TAG SID, INDEX ON UPPER(LNAME+FNAME) TAG NAME
    TEACHERS:  INDEX ON TID TAG TID, INDEX ON DEPT_ID TAG DEPT
    COURSES:   INDEX ON CID TAG CID, INDEX ON DEPT_ID TAG DEPT
    CLASSES:   INDEX ON CLS_ID TAG CLS, INDEX ON TERM+CID+STR(SEC,2) TAG TCSEC
    ENROLL:    INDEX ON SID TAG SID, INDEX ON CLS_ID TAG CLS
    ROOMS:     INDEX ON ROOM TAG ROOM
    MAJORS:    INDEX ON MAJOR TAG MAJOR
    DEPT:      INDEX ON DEPT_ID TAG DEPT
    TERMS:     INDEX ON TERM TAG TERM
    STUD_MAJ:  INDEX ON SID TAG SID
    TASSIGN:   INDEX ON CLS_ID TAG CLS

  DOTTALK++ -- current, contract-backed.

    DotTalk++ INDEX ON takes a FIELD KEY, not an expression. Per the usage
    contract in src/cli/cmd_index.cpp:

        INDEX ON <field> TAG <name>

    The two composite tags above -- NAME (UPPER(LNAME+FNAME)) and TCSEC
    (TERM+CID+STR(SEC,2)) -- are FoxPro expression indexes. They CANNOT be
    built in DotTalk++ and have no DotTalk++ equivalent. Do not copy them.

    Field-key tags for this dataset:

        STUDENTS:  SID
        TEACHERS:  TID, DEPT_ID
        COURSES:   CID, DEPT_ID
        CLASSES:   CLS_ID
        ENROLL:    SID, CLS_ID
        ROOMS:     ROOM
        MAJORS:    MAJOR
        DEPT:      DEPT_ID
        TERMS:     TERM
        STUD_MAJ:  SID
        TASSIGN:   CLS_ID
        BUILDING:  (none defined)

    This is the V32 help lane. V32 / MS-DOS tables use CNX -- a sorted index
    by tag, BATCH REBUILD ONLY. Runtime tag mutation is NOT supported here;
    that is a CDX (x64) capability.

        USE <table>
        CNX CREATE
        CNX ADDTAG <field>
        REINDEX CNX

    There is no BUILDLMDB on this lane. LMDB backs CDX containers, and CDX is
    the x64 lane. Per USE: "x32 tables prefer CNX, then INX."

    Reproducible build script: dottalkpp/data/scripts/mcc/mcc_build_x32.dts

  Corrected 2026-07-14. The FoxPro block had been read as DotTalk++ syntax by
  both humans and AI. It is not, and never was.

Sample relationships:
  STUDENTS.SID  -> ENROLL.SID, STUD_MAJ.SID
  COURSES.CID   -> CLASSES.CID
  CLASSES.CLS_ID-> ENROLL.CLS_ID, TASSIGN.CLS_ID
  TEACHERS.TID  -> CLASSES.TID, TASSIGN.TID
  DEPT.DEPT_ID  -> TEACHERS.DEPT_ID, COURSES.DEPT_ID, MAJORS.DEPT_ID
  BUILDING/ROOMS linked by ROOMS.BLDG
