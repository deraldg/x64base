# LANE -- Declared-Capability Validator

**Lane code:** `AIF-079`
**Lane name:** Declared-but-unreferenced capability detection (validator tier)
**Status:** `planned lane` *(not earned: no tool landed, no runtime evidence)*
**Owner:** Derald (engine) - drafting partner: Claude (Cowork, local repo access)
**Run:** `DECLARED-CAPABILITY-VALIDATOR-20260730` - claim `coordination/aif/AIF-079.claim`
**Baseline:** `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`
**Created:** 2026-07-30

> **Authority hierarchy.** Conventions suggest. Registration declares. Metadata records. Runtime proves. Validators enforce. This file *declares* the lane; status is earned per gate by proof artifacts.

---

## 1. One-line

Detect the class of defect where a capability is **declared at the interface and absent at the leaf**: the symbol exists, so the declaration reads as source-evidenced, while the behavior it promises was never implemented or never wired.

## 2. Why a lane

This class was found twice in one day, in two unrelated subsystems, by two separate investigations. Neither investigation was looking for it. Seven instances surfaced incidentally (section 4), spanning `xindex`, `cnx`, `cli`, and `memo`.

Each instance is individually defensible as a placeholder for planned work. Collectively they are a systematic gap in the evidence taxonomy:

| | Declaration | Behavior |
|---|---|---|
| Evidence tier as recorded | `source-evidenced` (symbol genuinely present) | -- |
| Evidence tier in reality | `source-evidenced` | `planned` |

The existing validator surface checks **documentation shape** (annotation coverage, HELP/CMDHELP agreement, contract field population). Nothing checks **capability reality**. A header can promise `bool wasStale()` on every backend, a config file can advertise `on_full = fail`, and both pass every current check while doing nothing.

This is the highest-yield validator available right now precisely because it is mechanical: every one of the seven instances is detectable by static rule, with no judgement call and no runtime.

## 3. Detector classes

| ID | Detector | Rule sketch |
|---|---|---|
| **D1** | Unreferenced public capability | A non-static function or method is declared and defined, and has zero call sites outside its own definition and its overrides. |
| **D2** | Unbranched enum value | An enum constant never appears in a `switch` case, comparison, or conditional outside a pure name-mapping function. |
| **D3** | Stub return | A function whose entire body sets an error string and returns failure, while its declaration promises an operation. |
| **D4** | Write-only state | A member or flag is assigned but never read in any decision. The signal is produced and nothing consumes it. |
| **D5** | Config key without enforcement | A configuration key is parsed into a struct and printed, but never read at the site that would enforce it. |

D1 and D4 are the two that caught the most instances and are the cheapest to implement. D3 is nearly free (pattern match on the body). D2 and D5 need slightly more context.

## 4. Seed instances (all source-verified at baseline)

These are the known-answer set. A v1 tool that does not find all seven has not earned M1.

| # | Instance | Detector | Anchor |
|---|---|---|---|
| 1 | `IIndexBackend::wasStale()` -- pure virtual plus seven overrides, zero call sites in `src/` or `include/` | D1 | `include/xindex/index_backend.hpp:45` and seven overrides |
| 2 | `CNX_HDRF_DIRTY` -- set and cleared, never tested; the torn-write recovery it exists for does not run | D4 | `include/cnx/cnx.hpp:26`; `src/cnx/cnx_file.cpp:192, 275-276` |
| 3 | `OnFull::Spill` / `OnFull::Fail` -- never branched on; only `on_full_name()` mentions them | D2 / D5 | `include/cli/vdisk_config.hpp:30`; `src/cli/vdisk_config.cpp:89-95` |
| 4 | `CnxDocument::save()` -- returns false, `"not implemented"` | D3 | `src/cnx/cnx_document.cpp:239-244` |
| 5 | `InxPayload::writeToStream` -- stub; `writeToFile` delegates to it, so the class can read a format it cannot write | D3 | `src/xindex/inx_payload.cpp` (`writeToStream`, `writeToFile`) |
| 6 | `set_persistence_mode` -- comment reads "Stub only"; sets state without opening the journal it describes | D3 | `src/cli/table_state.cpp:243-251` |
| 7 | `make_x64_memo_store` -- factory with no caller; the whole `X64MemoStore` class is unreachable | D1 | `src/memo/x64_memo_store.cpp:195` |

Instance 2 is the clearest illustration of why D4 matters: `set_dirty` **does** have callers (`cmd_pack`, `cmd_zap`), so a caller-count check passes. The defect is one level further in, at the consumer that never reads the flag.

## 5. Approach options (decide at M0)

- **Option A -- text/regex scanner in `tools/` (near-term).** Python, no toolchain dependency, runs inside `prepush_gate.py`. Cheap and portable; imprecise on overloads, macros, and templates. Report-only at first.
- **Option B -- compiler-assisted (target).** Drive a clang AST pass off `compile_commands.json`. Precise on overload resolution, virtual dispatch, and conditional compilation. Larger build and a toolchain dependency the pre-push gate does not currently carry.
- **Option C -- link-time symbol survey.** `nm` / `--gc-sections` style dead-symbol reporting on built artifacts. Cheap and precise for D1 on non-virtual symbols; blind to D2, D4, D5 and to anything the linker keeps for vtables.

**Recommended path:** A for v1, report-only, seeded with the section 4 known-answer set. B when precision demands it. C as an optional cross-check, not a primary.

## 6. Suppression, and why it should reuse the annotation system

The dominant risk is false positives (section 9). The tempting fix is a bespoke allowlist file, which rots.

**Better: reuse `@dottalk.contract` / `@dottalk.usage`.** Those blocks already carry a `status:` field. A capability legitimately declared ahead of implementation should say so there, and the validator should treat an explicit `status: planned` (or `stub`) as suppression.

That inverts the cost in the right direction. Instead of the validator carrying a growing exception list, an unimplemented capability is required to **declare itself unimplemented** -- which is exactly what the annotation system is for, and which makes the metadata more truthful rather than less. It also means the validator strengthens annotation coverage as a side effect instead of competing with it.

Open sub-question for M0: whether `status: planned` on a *file* block should suppress every symbol in that file, or whether symbol-level annotation is required. File-level is cheaper and probably too coarse.

## 7. Scope

**In:** a scanner under `tools/` implementing D1 and D4 at minimum; a report artifact; the section 4 known-answer fixture; suppression via annotation `status`; opt-in wiring into `tools/staging/prepush_gate.py` (warn, not block, in v1).

**Out:** fixing the seven instances (each belongs to its own lane: 1, 2, 4, 5 to `XIDX-TXN-02`; 3, 7 to `AIF-043`; 6 unassigned). Fixing them is not this lane's job and must not be folded in, or the validator's own proof set disappears before the validator lands.

## 8. Milestone gates (falsifiable exit conditions plus proof)

### M0 -- Approach locked -> readiness `source-evidenced`
**Exit:** Option A/B/C decided; D1-D5 rule semantics specified precisely enough to implement; suppression mechanism (section 6) ratified including the file-versus-symbol granularity question; false-positive categories (section 9) enumerated with a handling decision each.
**Proof:** M0 findings note appended to this lane.

### M1 -- Scanner lands, report-only -> `source-evidenced`
**Exit:** tool runs clean on the tree and **reports all seven section 4 instances**, with zero crashes and a written false-positive count. Runs on Windows/MSVC and WSL/Ubuntu checkouts. Does not block anything yet.
**Proof:** committed tool plus its output artifact checked in as a baseline report; both toolchains exercised; `git` sha.

### M2 -- Precision earned -> `runtime-evidenced`
**Exit:** false-positive rate low enough to be actionable, measured not asserted: every reported item is triaged into {true defect, legitimate-and-now-annotated, tool error}, and tool-error count is zero on the current tree. Suppression via annotation `status` demonstrated on at least one real symbol.
**Proof:** triage table with a disposition per finding; before/after report diff.

### M3 -- Gate wired -> `active beta`
**Exit:** `prepush_gate.py` runs the detector; **new** declared-but-unreferenced capability fails the gate while the existing baseline is grandfathered (ratchet, not big-bang). Ratchet baseline is a checked-in file.
**Proof:** a deliberate test commit introducing an unreferenced public function is blocked; an unrelated commit is not.

## 9. Risks / watch items

- **False positives, by category.** Symbols intended for external consumers (`bindings/pydottalk`, plugin surface, the public API a teaching tool is *supposed* to expose unused); test-only symbols; platform-conditional code behind `#if`; virtual overrides invoked polymorphically that a text scanner cannot see; symbols reached only from DotScript dispatch tables rather than C++ call sites. That last one is specific to this engine and is the likeliest source of noise -- the CLI dispatcher registers commands by name.
- **Teaching-tool tension.** x64base is deliberately a readable teaching engine. Some declared-and-unused surface is pedagogical scaffolding, not debt. The validator must not push toward deleting explanatory API. Suppression-by-annotation (section 6) is the pressure valve; the lane should not acquire a "delete the dead code" goal.
- **Ratchet or nothing.** Wired as a hard gate against the current tree it would block everything on day one. M3 exists as a ratchet for that reason.
- **Scanner rot.** A regex tool that drifts from the codebase becomes a source of false confidence, which is worse than no tool. M2's zero-tool-error bar is the guard.

## 10. Fallback

Report-only is the fallback. If M2 precision is not reached, the tool stays a manual `MAINT`-style audit command rather than a gate, and still pays for itself as a periodic sweep. Lane returns to `planned lane` for the gate portion only.

## 11. Register

- Lane code `AIF-079` -- claimed in `coordination/aif/AIF-079.claim`.
- Intake queue row: pending (see session README; held out deliberately per the scoped-slice rule).
- Related lanes: `XIDX-TXN-02` (owns instances 1, 2, 4, 5), `AIF-043` (owns instances 3, 7).
- Doctrine tie-in: this lane is the first validator that tests the **"Runtime proves"** rung rather than the **"Metadata records"** rung. Prior validators confirm that a description exists; this one confirms that the thing described is reachable.

## 12. Status ledger

| Date | Gate | Status | Evidence |
|---|---|---|---|
| 2026-07-30 | -- | `planned lane` | This declaration (source-read only, seven instances verified at `b702b5a5d`) |
| | M0 | pending | |
| | M1 | pending | |
| | M2 | pending | |
| | M3 | pending | |
