# AIF-165 -- Regression grading hardening lane V1

Status: runtime-proven; review-needed.

Owner: `member.derald`

Steward: `member.ai.codex`

Claim: `coordination/aif/AIF-165.claim`

Run: `CODEX-20260915-AIF165-REGGRADE-001`

Follow-up run: `CODEX-20260915-AIF165-REGGRADE-002`

Opened: 2026-09-15

Baseline: `4c219c0be`

## 1. Problem

The 2026-09-15 `REGRESSION ALL` capture ran 31 specs and printed `PASS` while
19 specs were explicitly reported as `not graded`. Those specs ran and printed
transcripts, but no executable validator could turn their behavior red.

That footer collapsed two different states:

- every executed claim was checked and passed;
- execution completed, but some claims were not checked.

The first state may be `PASS`. The second is incomplete evidence.

## 2. Owner ruling

After the steward recommended a separate hardening lane, a `PARTIAL` suite
verdict, and validators for the seven workspace-family specs exposed by the
capture, the owner directed: `do all`.

This authorizes the bounded implementation in this charter. It does not
authorize AIF-136 M5-B physical reclaim or any push. The initial boundary left
the seven DotScript bodies unchanged; section 6 records why two path spellings
had to be repaired after the new validators made their existing false greens
visible.

## 3. Rules

1. `PASS` means every spec run by the suite was graded and passed, and both
   isolation arms passed.
2. `FAIL` means a validator failed, an instrument was unmeasured, or an
   isolation arm failed.
3. `PARTIAL` means the completed run has no measured failure but at least one
   spec remains ungraded.
4. `PARTIAL` sets the engine command error context to non-success. Automation
   must read the verdict or `ERROR_STATUS`; the interactive executable's outer
   process still exits zero, and this lane does not redefine process shutdown.
   `PARTIAL` is not a softer spelling of `PASS`.
5. An explicit run of an ungraded spec is also non-success.

## 4. First grading tranche

The following default-suite specs already emit named FORMULA assertions and
are the first tranche:

| Spec | Marker prefix | Exact count |
| --- | --- | ---: |
| `WORKSPACE_SCOPE` | `WS_` | 8 |
| `WSMULTI` | `WSM_` | 11 |
| `WSLADDER` | `WSL_` | 13 |
| `RELSCOPE2` | `RS_` | 5 |
| `MWXSHAKE` | `MWX_` | 48 |
| `OPENJOIN` | `OJC_` | 7 |
| `WSENV` | `RSE_` | 9 |

Each validator requires the complete named sequence exactly once, in order,
with every value `.T.`. Missing, duplicate, renamed, unexpected, reordered, or
false markers fail. This count discipline matters because an errored FORMULA
line can disappear instead of printing `.F.`.

## 5. Expected transition

On the captured baseline, the seven contracts are complete and true. If the
engine and fixtures remain unchanged, wiring them into the grader should move
the suite from 12 graded passes and 19 ungraded specs to 19 graded passes and
12 ungraded specs. The correct overall verdict remains `PARTIAL` until the
remaining twelve receive validators or leave the default suite.

## 6. Verification and evidence

Required before closeout:

- build the active DotTalk++ executable;
- run `REGRESSION ALL` through the rebuilt executable;
- confirm all seven workspace validators report their exact counts;
- confirm the summary reports no measured failure and `VERDICT: PARTIAL`;
- confirm the command status is non-success;
- run the scoped repository gate over this lane's exact paths.

Runtime results are appended here after measurement. No future session should
infer them from this plan.

### 6.1 First instrumented run

The rebuilt 2026-09-15 run proved the validator path and found two real reds:

- `MWXSHAKE`: `MWX_T1` and `MWX_T2` were false;
- `OPENJOIN`: `OJC_G3` and `OJC_T1..T3` were false.

Both reproduced in isolated single-spec runs, so suite order was exonerated.
The commands resolved `DBF/SANDBOX/...` underneath an already configured DBF
slot, producing `.../DBF/DBF/SANDBOX/...`. Older green evidence had depended
on starting the process in `dottalkpp/data`, where the same spelling happened
to exist relative to the process directory. The canonical capture starts in
`dottalkpp`, as `tools/staging/run_capture.ps1` requires.

The correction changes no expected behavior: `OPENJOIN` now uses paths relative
to the configured DBF slot, and `MWXSHAKE` opens the configured DBF slot through
the existing `DBF` shorthand. This removes working-directory dependence rather
than retuning an assertion. A second full run is required.

### 6.2 Corrected proof

The second isolated runs passed:

- `MWXSHAKE`: 48 exact markers, all true and in order;
- `OPENJOIN`: 7 exact markers, all true and in order.

The corrected full run then reported:

- specs run: 31;
- graded passes: 19;
- failures: 0;
- unmeasured: 0;
- not graded: 12;
- isolation: BEFORE ok, AFTER ok;
- verdict: `PARTIAL`;
- zero `.F.` marker lines.

All seven new validators printed their exact counts and passed. A same-process
follow-up `ERROR_STATUS` read severity `error`, facility `general`, number `2`,
message `Invalid argument`, proving `PARTIAL` is non-success in the engine
command context. The outer capture process still exited zero; that boundary is
declared in rule 4 rather than hidden.

Local reconstructible captures under `tmp/`:

| Capture | Bytes | SHA-256 |
| --- | ---: | --- |
| `aif165_regression_all.txt` | 723183 | `5b77306bc02ee0e4198f860c076b96ab81c6ab227c04ac1276588b81491a6e5c` |
| `aif165_mwxshake_single.txt` | 49936 | `c29177a05125f8355f706234a2f3be7910e0c3504077d695029a5a7d1c50b13e` |
| `aif165_openjoin_single.txt` | 16412 | `829b2118b422fc6a7c04f13802263606d7cc7577958bef4f6e60190da60abbeb` |
| `aif165_mwxshake_single_fixed.txt` | 49137 | `ddce8c4a77956a9625ba29301c8e70462fddd897a87822e5770cbf2206aa1062` |
| `aif165_openjoin_single_fixed.txt` | 15793 | `d05586029781652500c0cb6aa4d15e7e210bfbb061e22f6573db680da2c0db4f` |
| `aif165_regression_all_fixed.txt` | 721732 | `d4050372737f62dddb42dd67786e838d9ee3834186927be1e9906778d3447bc9` |
| `aif165_regression_all_status2.txt` | 721868 | `bb71766cda5269d20a617b73987b08ae7b0109c46fcff9cf987bf0c6bc113039` |

These captures are evidence, not authorities. They are intentionally in the
reconstructible scratch tier; the durable facts and hashes are recorded here.

## 7. Good Neighbor boundary

`src/cli/cmd_regression.cpp` also contains active AIF-160 work stewarded by
Claude/Cowork. This lane changes only the grading enum/dispatch, the seven
workspace registry entries, the exact marker validator, and suite-status
semantics. The durable board notice identifies the overlap and the exact
verification surface. Commit staging must isolate these hunks from unrelated
work in the same file.

## 8. Rulings ledger

| Date | Ruling | Authority |
| --- | --- | --- |
| 2026-09-15 | Implement the full bounded recommendation: M5-A closeout, no M5-B reclaim, and the separate regression-grading hardening lane described above. | Owner in session: `do all` |
| 2026-09-15 | Continue from the 19/31 checkpoint and grade every remaining default-suite spec. | Owner in session: `do so` |

## 9. Second grading tranche

The follow-up run graded all twelve remaining default-suite specs. It reused the
strict true-marker contract where the script already carried discriminating
markers, and added the smallest missing evidence surface where it did not.

| Spec | Executable contract |
| --- | --- |
| `NONDESTRUCTIVE` | 17 routed section checkpoints, completion fence, and no exercised `Unknown command:` line |
| `INDEX_X32` | 14 exact, ordered, true markers |
| `X64_METRICS` | 8 exact, ordered, true markers |
| `LANGUAGE` | 18 exact localized `USAGE` labels in each of five locale fences, green catalog, restored locale, stable result payload |
| `RELJOIN` | 9 exact result blocks covering ONE, JOIN/ENUM parity, DISTINCT, LIMIT, projection, and relation-tree shape |
| `DOTSCRIPT_EXPR` | 16 ordered lines; the deliberate out-of-range arm accepts only the two evaluator error renderings measured in isolated and inherited-suite state |
| `DOTSCRIPT_PARITY` | 5 exact ordered lines |
| `LEXING` | 1 exact fenced survivor line |
| `USE_ARGS` | 8 exact, ordered, true markers |
| `NAME_AMBIG` | 3 exact markers plus the rename announcement and zero-resolution ledger |
| `NAV_NATURAL` | 12 exact, ordered, true markers |
| `NULLASSERT` | 21 exact, ordered, true markers; its three `NL_P*` probes remain deliberately outside the graded prefix contract |

The script changes are evidence-only. Five scripts gained marker or result
fences; seven already carried sufficient assertions. No command syntax, HELP,
metadata, storage format, publication surface, or M5-B reclaim behavior changed.

## 10. Complete proof

The first complete-suite run with the second tranche went red, rather than
hiding a mismatch:

- specs run: 31;
- passed: 30;
- failed: 1 (`DOTSCRIPT_EXPR`);
- unmeasured: 0;
- not graded: 0;
- isolation: BEFORE ok, AFTER ok;
- verdict: `FAIL`.

The isolated expression run emitted `scalar evaluation failed`; the inherited
full-suite run emitted `unable to evaluate expression`. Both named the same
deliberate `$a[9]` out-of-range arm, while all other 15 fenced lines were exact.
The validator now accepts only those two measured renderings at that one line.
This is a bounded semantic oracle, not a broad substring exemption.

After that correction, the rebuilt full run reported:

- specs run: 31;
- passed: 31;
- failed: 0;
- unmeasured: 0;
- not graded: 0;
- isolation: BEFORE ok, AFTER ok;
- verdict: `PASS`.

All twelve second-tranche specs were also run separately on the same final
build. Reconstructible local captures use the pattern
`tmp/aif165_final_<spec>.txt`. The durable full-suite evidence is:

| Capture | Bytes | SHA-256 | Reading |
| --- | ---: | --- | --- |
| `aif165_regression_all_graded.txt` | 724691 | `c39e1e6195fda8523f52359ff1114dd337ece5484de7429dab7ca409eeae3490` | 30/31, zero ungraded, deliberate validator red |
| `aif165_regression_all_graded_v3.txt` | 724758 | `a09fbc077308c0a71f38072b571b7e9a86b83a9cbcd6e66996643c3e38e4eeac` | final build: 31/31, zero ungraded, isolation green, `PASS` |

The captures remain scratch-tier evidence. The counts, readings, and hashes in
this charter are the durable record.
