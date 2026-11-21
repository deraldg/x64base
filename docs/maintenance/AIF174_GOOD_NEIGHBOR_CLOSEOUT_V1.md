# AIF-174 Good Neighbor and housekeeping closeout

RE: AIF-160/AIF-165 regression harness and CLI output maintainers

WHAT CHANGED: CURATED SUITE replaces ALL; nine related process groups; optional
QUIET with full screen default; independent complete output capture; captured
child stdout/stderr; strict option parsing; usage contracts, command catalog and
menu synchronized. Capture wrapper uses canonical data cwd and returns process
status. New output-capture CTest covers failure and restoration behavior.

WHOSE AREA: regression harness AIF-160/AIF-165; CLI output/BANG; command catalog;
Turbo Vision test menu; source-derived report consumers. AIF-174 owns this change.

AUTHORIZATION: owner directed implementation, then contract correction, then
"house-keeping and good neighbor" in the current chat on 2026-11-21.

VERIFY OR UNDO: from D:\code\ccode, run
`cmake --build build --target dottalkpp dottalkpp_regression_output_capture_test --config Release`,
then `ctest --test-dir build -C Release -R dottalkpp_regression_output_capture_test --output-on-failure`.
In the runtime run `REGRESSION CURATED SUITE QUIET LOG` and
`REGRESSION GROUP SQL_DML QUIET LOG`. Require 34/34 and 6/6 respectively on
this fixture set. Use `git show <AIF-174-commit>` to review the bounded change;
if rollback is requested, use `git revert <AIF-174-commit>` after checking for
concurrent edits. Never reset/restore the shared tree wholesale.

## Evidence and handoff limits

Curated 34/34; FIELD_TYPES 5/5 in full and quiet with 110 identical marked
lines; SQL_DML 6/6; output-capture CTest passed including child stdout/stderr,
quiet isolation, failure reporting, and restoration. Source/runtime usage checks
passed. Detailed results are in AIF174_REGRESSION_VERIFICATION.json.

DURABILITY: PKDURABLE did not launch children because member.ai.regression had
no live host.shell grant. This remains a prerequisite, not a passing test.
WORKSPACE_PERSISTENCE was inspected, not run. Generated HELP tables and manual
catalogs need their normal governed refresh; only source contracts were updated.
No authorization grants were created. Temporary data/host environment variables
were restored by the test runners. No publication or staging-tree sync occurred.

## Shared-tree accounting

AIF174_CLOSEOUT_INVENTORY.json.gz records owned paths, every other dirty/untracked
entry at the pre-stage snapshot, and retained local artifact paths/hashes.
Other work was not staged, reset, or deleted. The shared prepush gate is staged
by a patch containing only our terminology change. Its unrelated new checks
remain in the working tree for their owner.

Build outputs and the local runtime bin were refreshed. Test captures under tmp
and normal regression residue under dottalkpp/data/tmp are retained. No broad
scratch cleanup was performed. There was no before-run inventory of every data
file, so this closeout does not claim to identify every runtime artifact's author.

The board requires maintainer transcription, so this RE note is the durable
handoff; the session coordinator also receives a notification. The repository's
commit hooks and scoped checks remain enabled.
