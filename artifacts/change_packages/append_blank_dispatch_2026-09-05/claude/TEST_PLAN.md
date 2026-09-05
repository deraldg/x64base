# TEST_PLAN -- APPEND BLANK dispatch

## 1. Checks actually performed

**Checks 1-8 are source reading. Check 9 ran a program. NOTHING WAS COMPILED
AND THE ENGINE WAS NOT RUN.**

| # | check | result |
|---|---|---|
| 1 | The registry holds `APPEND_BLANK` and no two-word key | confirmed, `shell_commands.cpp:242`, and a tree-wide grep for the string found no other registration |
| 2 | `shell_dispatch()` hands the command a stream positioned AFTER the verb | confirmed, `shell_api.cpp:296-300` -- `std::istringstream tok(line); tok >> cmd;` then `registry().run(area, U, tok)` |
| 3 | `cmd_APPEND` falls through to usage on an unrecognised first token | confirmed, `cmd_append.cpp` -- the final statement of the function is `print_append_usage()` |
| 4 | `APPEND BLANK USAGE` still reaches the usage path after the rewrite | traced by hand: `APPEND_BLANK USAGE` -> `is_append_blank_usage_request` strips the `APPEND_BLANK ` prefix -> `USAGE` |
| 5 | Bare `APPEND BLANK` reaches `dottalk_append_blank_core` after the rewrite | traced by hand: `APPEND_BLANK ` -> not USAGE/HELP/? -> core |
| 6 | `APPEND`, `APPEND 5`, `APPEND RAW`, `APPEND MANY 3` are unaffected | `starts_with_tokens_ci` requires the literal token `BLANK`; none match |
| 7 | The three target files are clean at baseline | `git ls-files -m` returned empty; sha256 recorded in MANIFEST.md |
| 8 | `cmd_APPEND_BLANK` is declared for the browsetui call site | it is not -- `cmd_browsetui.cpp` uses local `extern` declarations, so the patch adds one. Caught by reading; it would otherwise have been a link error |
| 9 | **the patch applies cleanly to the tree at baseline** | **actually executed**: `patch -p1 --dry-run --forward` against `D:\code\ccode` at `4aac03540` -- all three files check, exit 0 |

**Check 9 is the only one in this table that ran a program.** It proves the patch
is well-formed and lines up with the files it claims to patch. It proves nothing
about whether the result compiles or behaves.

**Check 8 is the reason this section exists.** Reading found a real omission in
the patch before the patch was written -- a missing declaration that would
otherwise have surfaced as a link error at the steward's build. It does not make
checks 1-7 into runtime evidence, and neither does check 9.

## 2. Checks recommended but NOT performed

### 2.1 Build

Not run. Expected clean: the change adds one `if` using a static helper already
defined in the same translation unit, one `extern` declaration, and one call.

**The most likely build failure is check 8's** -- a missing declaration of
`cmd_APPEND_BLANK` -- which the patch addresses, unverified.

### 2.2 The runtime check that actually settles it

One `.\datarun.ps1` session. This is the whole proof for hunk 1:

```
CREATE VFP abtest (id N(4), plain C(5))
USE abtest
COUNT
APPEND BLANK
COUNT
REPLACE plain WITH "AB"
LIST ALL
APPEND BLANK USAGE
APPEND BLANK GARBAGE
COUNT
APPEND 2
LIST ALL
CLOSE
```

`COUNT` before and after is Grok's framing and it is better than reading `LIST`:
it asks the one question the defect makes hard, **did the record count move**, and
it is the check that would have caught this in the first place.

**PASS, fixed in advance:**

- the first `APPEND BLANK` prints **no usage block** and reports a record;
- `REPLACE` does **not** answer `no current record`;
- `LIST ALL` shows **one** record, `plain = AB`;
- `APPEND BLANK USAGE` prints the **APPEND_BLANK usage text**, not the APPEND
  usage text, and appends nothing;
- **`APPEND BLANK GARBAGE` prints usage and appends NOTHING** -- the `COUNT`
  after it must equal the `COUNT` before. This is Grok's arm. Without it the
  repair would have swallowed `GARBAGE` in silence, which is the defect it was
  written to cure wearing different clothes;
- `APPEND 2` still works -- **the regression arm.** If the rewrite were too
  greedy this is what would break;
- final `LIST ALL` shows **three** records (one from `APPEND BLANK`, two from
  `APPEND 2`; `APPEND BLANK GARBAGE` contributed none).

**FAIL** is any usage block after the first `APPEND BLANK`, any
`no current record`, or a final count other than three.

`abtest.dbf` is scratch. Delete it or leave it; it is not evidence and must not
be tracked.

### 2.3 F5 in the BROWSE TUI -- the unverified half

**The claim that F5 has never worked is INSPECTION.** It follows from the same
fall-through as the shell path plus the position-zero stream, but it was not
observed. Verify by hand:

```
USE abtest
BROWSETUI
```

Press **F5**. Before the patch: expect the APPEND usage block to appear and the
row count not to change. After: expect a new blank row and no usage text.

**If F5 behaves correctly BEFORE the patch, hunk 2 is wrong and this package
should be returned.** That outcome is stated here so it can falsify the claim
rather than be explained away afterwards.

### 2.4 Regression

`REGRESSION ALL`. Expected: no change.

**One place deserves a reader's eye rather than a green tick.** The WSLADDER
spec was bitten by this exact hazard and was rewritten to use bare `APPEND`. It
should be unaffected. But **a spec that has been silently appending nothing will
now append**, and that is a behaviour change a green suite can hide -- if a spec
asserts shape rather than content, it passes either way. That is the AIF-110
finding, and it is the specific thing to look for.

## 3. Fixtures and mutation safety

- No fixture is read, written, or regenerated by this change.
- No format, catalog, index, memo or schema change.
- The scratch table in 2.2 is created by the tester and is not part of the
  package.
- `APPEND_BLANK` is classified `mutates: table-data index memo record-pointer`.
  **After this change that classification fires on a spelling where it
  previously did not**, because the spelling previously did nothing. Anything
  that reached `APPEND BLANK` and appeared harmless was appearing harmless by
  being broken.

## 4. Rollback / non-promotion conditions

Return or revert if:

- the build fails in a way the patch does not obviously explain;
- `APPEND 2`, `APPEND RAW`, or `APPEND MANY 3` change behaviour -- the rewrite
  is too greedy;
- `APPEND BLANK USAGE` appends a record -- the usage path was swallowed;
- F5 worked before the patch -- hunk 2 is a fix for a defect that was not there;
- `REGRESSION ALL` reds anywhere, or a spec changes what it writes.

Rollback is `git checkout` of the three files. The change is additive within one
preprocessor function and one key handler; nothing else depends on it.

## 5. What this package does not claim

It does not claim to compile. It does not claim to run. It does not claim F5 is
broken as a measured fact. It does not claim the two-word spelling is used
anywhere except the one TUI call site and the two documented incidents.

**Every runtime statement in this package is a prediction written before the
run**, so the run can contradict it.
