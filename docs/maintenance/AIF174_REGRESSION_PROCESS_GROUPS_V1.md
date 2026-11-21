# AIF-174: regression process groups and output

Owner authorization: current request, 2026-11-21.
Status: implemented and built in development; verification below. No publication requested.

## Contract

- `REGRESSION CURATED SUITE [QUIET] [LOG [path]]` replaces ALL.
- `REGRESSION GROUPS`, `REGRESSION SHOW GROUP name`, and
  `REGRESSION GROUP name [QUIET] [LOG [path]]` expose related process chains.
- Existing individual test commands accept the same output options.
- Full screen output remains the default. QUIET is per invocation only.
- Logging observes routed output independently of alternate captures. Ordinary
  cout/cerr and captured BANG child stdout/stderr join the same transcript.
- Log open failure refuses execution; write failure sets a non-success error.
- Group tests execute once in registry order, retaining existing fixture setup,
  catalog brackets and grading. Ungraded tests yield PARTIAL, never PASS.
- Group preflight refuses missing registered scripts; per-test setup checks
  continue to report unavailable fixtures as unmeasured.

## Process groups

WORKSPACE, INDEX_WRITEBACK, SQL_QUERY, SQL_DML, RELATIONS, LANGUAGE,
FIELD_TYPES, DURABILITY, WORKSPACE_PERSISTENCE. Membership and setup notes
are maintained in `src/cli/cmd_regression.cpp`, not duplicated here.
Durability requires host commands; persistence includes explicit-only fixtures.
No claim is made that every historical regression has been classified.

## Proof plan

Build the engine. Check syntax rejection before execution, group listing and
membership, paired full/quiet runs and verdict/evidence equality, routed output
in logs, captured child stdout/stderr, and restored output after failed runs.
Record results here after measurement.

## Good Neighbor note

WHAT CHANGED: regression command groups, naming, output capture; capture wrapper exit status.
WHOSE AREA: AIF-160/AIF-165 regression harness; CLI output and BANG maintainers.
AUTHORIZATION: owner request in current chat, 2026-11-21.
VERIFY OR UNDO: build dottalkpp; run REGRESSION USAGE and the checks above.
Undo only AIF-174 changes in the named source/tool files; preserve unrelated work.

## Verification, 2026-11-21

Windows MSVC Release build passed and local runtime was staged by datarun.ps1.
CTest dottalkpp_regression_output_capture_test passed, including child stdout
and stderr capture without quiet-screen leakage and a failing disk sink.

- CURATED SUITE: 34 run, 34 passed; zero failed/unmeasured/ungraded;
  BEFORE and AFTER isolation green.
- FIELD_TYPES: 5/5 in both modes. Screen lines: full 4477, quiet 76
  (includes startup); full logs 4424 and 4432 lines respectively. All 110
  marked evidence lines equal; the extra quiet log lines are progress reports.
- SQL_DML: 6/6 passed, including its explicit-only SQL DML test.
- FIXTURECHECK: passed; the log contains the real ROUTED open failure and
  FD_C0_channel_that_carried_it:ROUTED. Alternate grading still works.
- Invalid syntax and unopenable log paths refuse execution. Console output
  after a quiet run and after log-open refusal remains available.
- Capture wrapper: passed FIXTURECHECK using the canonical data working
  directory; propagates the engine process exit code.
- Source-derived registry reader remains 84 specs, 32 curated members.
- DURABILITY: 3/4 passed; PKDURABLE failed because member.ai.regression has
  no live host.shell grant. No child test ran, and no authorization was created.
  Its child capture mechanism was independently verified by the CTest above.
- Extended WORKSPACE_PERSISTENCE group was inspected but not runtime-validated.

Machine-readable observations and raw capture hashes:
`AIF174_REGRESSION_VERIFICATION.json`. Raw captures remain in repo tmp with
prefix regression174_. They are local evidence, not published artifacts.

## Closeout state

Housekeeping closeout prepares a bounded local commit; no push or publication performed.
Runtime exe was rebuilt and datarun refreshed the local bin copy. Host/data
permission environment variables used for tests were restored in finally blocks.
Regression scripts retain their normal scratch/capture artifacts under data/tmp;
no cleanup of unrelated runtime data was attempted. The test runs report both
production workspace-catalog isolation checks green.

Existing unrelated dirty work includes the fullstack documentation/manualgen,
metadata, dictionary, and help-refresh lanes. None was staged or reverted.
In the already-dirty prepush_gate.py, the only AIF-174 edit is the displayed
REGRESSION ALL spelling. Preserve every other hunk there. Generated HELP
catalogs, manuals, website output and publication staging were not modified.

## Usage-contract correction, 2026-11-21

Owner follow-up exposed incomplete contract updates: standalone regression arm
options and BANG capture behavior were missing. Corrected both source usage
contracts and live USAGE output; added group/option/error/overwrite semantics,
updated the command catalog, and replaced stale ALL invocations in the test menu.
Documented output-router and captured-process helper API contracts.

Build passed (including dottalk_tvui). Source audit confirms all nine execution
forms document QUIET/LOG. Live REGRESSION USAGE and BANG USAGE checks passed.
Evidence: local tmp/regression174_contract_usage.txt and contract build logs.
Generated HELP data/manual catalogs still have not been regenerated.
