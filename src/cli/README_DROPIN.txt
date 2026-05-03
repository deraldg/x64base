DotTalk++ Tuple Graph Diagnostics Drop-In
=========================================

Purpose
-------
Diagnostic-only update for the relation-aware tuple augment path.
It does not change traversal policy. It only exposes root-record accounting so
we can identify why STUDENTS recCount=210 produces 208 tuple root records.

Files
-----
include/tuple/root_recno_source.hpp
src/tuple/root_recno_source.cpp
include/tuple/tuple_graph_cursor.hpp
src/tuple/tuple_graph_cursor.cpp
src/cli/cmd_tupvalidate.cpp
src/cli/cmd_tupexport.cpp

Also included for completeness if needed:
include/cli/workarea_cursor_restore.hpp
src/cli/workarea_cursor_restore.cpp
include/tuple/tuple_command_spec.hpp
src/tuple/tuple_command_spec.cpp
src/cli/cmd_tupvalidate.hpp
src/cli/cmd_tupexport.hpp

Expected new output
-------------------
TUPVALIDATE / TUPEXPORT now report:

  Root input  : table <recCount>, candidates <N>, collected <N>
  Root skips  : read <N>, deleted <N>, out-of-range <N>
    skipped read recnos      : ...
    skipped deleted recnos   : ...
    skipped out-of-range recnos: ...

The skipped-recno vectors are capped at 256 entries to avoid excessive output on
large tables. For the current STUDENTS 210/208 issue, this cap is sufficient.

Install
-------
Copy the files over the existing relation-aware tuple augment files, then build:

  cmake --build build --config Release --target dottalkpp

Suggested test
--------------
  do sandbox
  workspace close
  workspace open dbf
  select students

  tupvalidate
  tupexport csv tmp\tupexport_students_diag.csv

  set order to tag lname
  tupvalidate
  tupexport csv tmp\tupexport_students_lname_diag.csv

Interpretation
--------------
If candidates=210 and collected=208, the skip counters should identify whether
RootRecnoSource skipped two records because goto/read failed, deleted filtering
excluded them, or recnos were out of range.

If candidates=208 and table=210 under ordered traversal, the order/index provider
is returning only 208 candidate recnos.
