# Database Literacy Starter Lab v0

Status: runtime observed starter slice
Lab ID: `lab.database_literacy.starter`
Audience: student, self-learner, instructor

## Purpose

This is the first runnable LabTalk lab path. It starts with concepts that are
already exposed by DotTalk++ EDREF, then links those concepts to later live data
work.

## Learning Objectives

- Understand DotTalk++ as command layer, data layer, logic layer, and projection
  layer.
- Define table, record, and field.
- Understand that an index changes access order without changing table data.
- Understand `SCAN` as a record-aware data loop.

## Runtime Script

Use:

```text
labs/database_literacy_starter/database_literacy_starter_v0.dts
```

The script is read-only. It asks DotTalk++ for educational reference topics:

```text
HELP /ED MODEL
HELP /ED TABLE_RECORD_FIELD
HELP /ED INDEX
HELP /ED SCAN
```

## Proof Rule

The lab is not yet `student_ready`. The first portal-driven runtime transcript is:

```text
D:/code/ccode/labtalk/proofs/runs/20260702_155913_runtime_database_literacy_starter.txt
```

It becomes student-ready after the portal can:

```text
open this lab
-> run the DTS script
-> capture a transcript
-> link the transcript as proof
-> attach follow-on data commands over STUDENTS/TEACHERS
```

## Next Runtime Expansion

The next version should add a table-backed section:

```text
USE STUDENTS
FIELDS
STRUCT
LIST
SET ORDER
SEEK
SCAN
```

Only add those commands after their invocation and dataset path are verified in
the current DotTalk++ runtime.
