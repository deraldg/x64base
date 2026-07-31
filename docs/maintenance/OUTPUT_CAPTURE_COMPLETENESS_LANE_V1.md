# Output Capture Completeness Lane V1

    lane        : AIF-081
    claim       : coordination/aif/AIF-081.claim
    run         : 2026-07-31_cowork_output_capture_completeness
    owner       : member.derald
    steward     : member.ai.claude.cowork
    opened      : 2026-07-31 (Cowork)
    status      : findings recorded, NO source change landed
    evidence    : F1 runtime-proven + source-evidenced
                  F2 source-evidenced
                  F3 source-evidenced (hazard, not observed)
                  F4 source-evidenced + runtime-observed
                  F5 source-evidenced (adjacent, OUT of lane)

---

## 1. Origin

The owner asked to stop pasting console output and instead route a script
through dottalkpp to a file the agent could read directly -- dogfooding the
engine's own capture facilities rather than shell redirection.

The first attempt worked mechanically and immediately exposed a defect in the
facility being used. That is the whole finding: the capture path that the
documentation system would naturally stand on is incomplete, and incomplete in
the direction that silently discards the most important lines.

This sits directly on the house thesis that the documentation process consumes
and proves the database, which in turn supports the documentation system. A
transcript IS the consumption step. A lossy transcript corrupts the loop while
appearing to feed it.

---

## 2. Measured result

Same script, same binary (`dottalkpp/bin-wsl-lean/dottalkpp`, built
2026-07-31 03:15:49, `v0.6 / b702b5a5 dirty`), two capture facilities:

| facility          | lines | E_* markers | trace lines | corrective warning |
|-------------------|-------|-------------|-------------|--------------------|
| `DOTSCRIPT ... OUT` |  42 |      6      |     26      | **ABSENT**         |
| `SET ALTERNATE`     |  89 |      6      |     26      | present            |

Set-differenced both directions. The ONLY line unique to `DOTSCRIPT OUT` is its
own banner (`DOTSCRIPT OUT: tmp/... (write)`), which the ALTERNATE run had no
occasion to emit.

**`SET ALTERNATE` is a strict superset. `DOTSCRIPT OUT` contributes nothing.**

The line that `DOTSCRIPT OUT` loses, and which the proof exists to demonstrate:

    REPLACE: record written, but index update failed; REINDEX/REBUILD needed.

Also lost: `Created`, `Opened`, `Appended blank record N`,
`REPLACE: Replaced field #N`, `CNX: created`, `CNX ADDTAG`, `REINDEX CNX`,
`REBUILD: done OK=1`, `SET ORDER: CNX TAG`, `Recno:`, `Found at 1.`, `Closed.`,
`ERASE:` -- that is, the entire user-facing command surface.

---

## 3. Mechanism

Four sites explain it completely.

**(a)** The router installs its own streambuf as `std::cout`'s buffer at
startup (`src/cli/output_router.cpp:503-504`):

    impl_->cout_redirect_stack.push_back(std::cout.rdbuf());
    std::cout.rdbuf(impl_->routed_stream.rdbuf());   // MultiBuf

**(b)** `MultiBuf::overflow` / `xsputn` tee to the alternate file AFTER
dispatching to the destination (`output_router.cpp:326`, `:360`):

    if (impl->alternate_on && impl->alt_file.is_open()) {
        impl->alt_file.write(s, n);
        impl->alt_file.flush();
    }

ALTERNATE therefore sits at the BOTTOM of the stack and sees everything that
reaches `MultiBuf`, by either route.

**(c)** `shell_transcript` tees one level HIGHER, at `std::cout`
(`src/cli/shell_transcript.cpp:87-89`):

    old_cout_ = std::cout.rdbuf();          // this is already MultiBuf
    cout_tee_ = ...(old_cout_, file_.rdbuf());
    std::cout.rdbuf(cout_tee_.get());

**(d)** `cmdout` never passes through `std::cout` at all.
`src/cli/command_output.cpp:47` writes to `OutputRouter::out()`, which returns
`impl_->routed_stream` (`output_router.cpp:386-388`), bound directly to
`MultiBuf`.

### The one-sentence statement

`routed_stream` is a SIBLING of `std::cout`, not a child of it. Both terminate
at the same `MultiBuf`; only one of them passes through the transcript tee.
Every message a user sees takes the sibling path and is lost.

---

## 4. Findings

### F1 -- DOTSCRIPT OUT discards all router output
Runtime-proven (section 2) and source-evidenced (section 3). Severity is set by
what is lost: corrective warnings, error text, and command confirmations are
exactly the content a proof asserts on.

### F2 -- the documented contract is false
`cmd_dotscript.cpp` help text and the DOTSCRIPT USAGE note both assert
"OUT/OUTPUT tees full command output to a transcript file." It does not.
`shell_transcript.cpp:20` is narrower and technically accurate -- "output
emitted through std::cout" -- but command output is not emitted through
`std::cout`, so the accurate comment and the false help text describe the same
code without either one catching the other.

This is the documentation loop propagating a wrong fact WITH provenance, which
is worse than an undocumented one because it arrives with authority.

### F3 -- two components mutate std::cout.rdbuf with independent bookkeeping
`OutputRouter` keeps a `cout_redirect_stack` (`output_router.cpp:503`, restored
at `:512`). `shell_transcript` keeps `old_cout_` (`:87`, restored at `:123`).
Each guards its OWN nesting; nothing guards interleaving between the two. A
router pop crossing an active transcript restores the wrong buffer. Not
observed in the wild; recorded before it is discovered the expensive way.

### F4 -- two diagnostic trace families are ON BY DEFAULT
`index_trace_enabled_()` (`src/xindex/index_manager.cpp:449-457`) returns TRUE
when `DOTTALK_INDEX_TRACE` is unset:

    if (!env) return true; // diagnostic drop-in: on by default

`append_trace_enabled()` (`src/cli/append_support.cpp:74-82`) is the same shape:
"Diagnostic drop-in: enabled by default so APPEND lifecycle evidence is
visible. Set DOTTALK_APPEND_TRACE=0 to silence after diagnosis."

Both are deliberate, both are temporary by their own wording, and the
diagnosis window they were opened for has closed. Consequences:

  - `[APPEND TRACE]` and `[INDEX TRACE]` print on ordinary user paths.
  - The AIF-079 IDXDIFF spec text (`cmd_regression.cpp:278`) instructs
    "run with DOTTALK_INDEX_TRACE=1", implying opt-in. The variable is
    opt-OUT. The instruction is not wrong in effect, but it teaches the
    inverse of the actual default.
  - These traces are why the broken transcript LOOKED populated. Set
    `DOTTALK_INDEX_TRACE=0` and `DOTTALK_APPEND_TRACE=0` and the same
    `DOTSCRIPT OUT` run yields six `E_*` lines and nothing else.

### F5 -- ADJACENT, EXPLICITLY OUT OF LANE: `;` overload in DotScript lexing
Recorded here only so it is not lost; it belongs to the lexing lane.

`;` is position-dependent: TRAILING and unquoted it is a line continuation
(`src/cli/script_reader.hpp:18`), LEADING it makes the line skippable
(`src/cli/dotscript_lexing.cpp:84`). A marker line that ends in an unquoted `;`
silently swallows the line beneath it -- an assertion disappearing into its
neighbour with no error.

There is also a split inside the module whose stated purpose
(`dotscript_lexing.hpp:15-20`) was to end five drifting copies of this logic:
`is_comment_or_blank()` treats leading `;` as skippable, `is_comment_line()`
does not list `;` at all. Callers reaching for `is_comment_line` alone will try
to execute a leading-`;` line. The copies were consolidated; the semantic split
survived consolidation.

---

## 5. Blast radius

A proof that asserts on engine messages, captured with `DOTSCRIPT OUT`, and run
with the trace families silenced, produces an evidence file containing no
evidence. The file exists, is non-empty, carries marker lines, and omits every
fact it was written to record.

That is the AIF-079 class one layer out. Instance 8 of that lane was a test that
reported success while not running. This is a CAPTURE that succeeds while
capturing nothing that matters. Same declared-vs-actual shape, relocated from
the harness to the transport.

---

## 6. Milestones

**M0 -- decide the seam.** The architecture already has the correct one and
ALTERNATE stands on it. `DOTSCRIPT OUT` should drive the router's alternate
sink, or register a second file sink in `MultiBuf`, instead of swapping
`std::cout.rdbuf()`. This DELETES code rather than adding it. Open question:
retire `shell_transcript` entirely, or keep it as the raw-stream capture for
cases that deliberately want pre-router bytes.

**M1 -- land the seam change plus the help-text correction in ONE commit.**
Correcting the code without correcting the string leaves the help catalog
teaching the old behaviour, and the catalog feeds manualgen.

**M2 -- retire or gate the default-on trace families (F4).** Requires an owner
ruling: flipping the default is a visible behaviour change to anyone currently
relying on the noise.

**M3 -- rdbuf ownership (F3).** Either one component owns `std::cout.rdbuf()`
or the two share a documented protocol. Cheapest correct answer is likely that
only the router touches it, once M0 removes the second mutator.

**NOT IN THIS LANE:** fixing F5, and any change to what the proof scripts
assert. Folding those in would destroy this lane's own evidence set.

---

## 7. Reproduction

Both runs were issued at top level via stdin, NOT from a wrapper script.
DOTSCRIPT nesting is capped at main plus one subscript
(`cmd_dotscript.cpp:61`, enforced at `:491` with `g_dotscript_depth >= 2`,
message "nesting limit reached (max 1 subscript)"). Depth is checked before
increment, so the proof runs at depth 1 and its `DO ..\X32` bootstrap at
depth 2. A wrapper would have pushed the bootstrap to depth 3 and been refused.

    cd /mnt/d/code/ccode/dottalkpp/data

    # A: DOTSCRIPT OUT
    echo 'DOTSCRIPT scripts/index_maintenance_failure_proof.dts OUT tmp/idxstale_transcript.log' \
      | ../bin-wsl-lean/dottalkpp

    # B: SET ALTERNATE
    printf '%s\n' \
      'SET ALTERNATE TO tmp/alt_probe.log' \
      'SET ALTERNATE ON' \
      'DOTSCRIPT scripts/index_maintenance_failure_proof.dts' \
      'SET ALTERNATE OFF' \
      | ../bin-wsl-lean/dottalkpp

Artifacts: `dottalkpp/data/tmp/idxstale_transcript.log` (42 lines),
`dottalkpp/data/tmp/alt_probe.log` (89 lines). Both are throwaway diagnostic
output under `tmp/` and are NOT proposed for commit.

---

## 8. Method note -- two corrections recorded against this session

Both are recorded because the reasoning error is instructive, not to pad the
record.

**Prediction was wrong.** Before measuring, the steward predicted that
ALTERNATE and DOTSCRIPT OUT would capture DISJOINT halves -- reasoning that
because ALTERNATE is router-level it would see only router traffic, and would
lose the raw `std::cout` traces. Measurement says strict superset. The error
was assuming a facility's LEVEL from its NAME instead of reading where it taps.
`SET ALTERNATE` is a classic xBase surface, which made it sound peer to
`SET PRINT`; it is in fact implemented below both.

**Claim about traces was wrong.** The steward asserted that traces appeared
"only because this script enables them" and that a default run would be quiet.
The script enables nothing (`grep -i trace` over it returns zero non-comment
hits) and both families default ON (F4). The blast-radius conclusion survives
but is reached by SETTING the variables to 0, not by leaving them alone.

Both errors were caught by checking source before writing this document rather
than after. The general rule this lane re-earns: a facility's coverage is a
property of where it taps the stream, and that is a fact to be read, never
inferred from its name or its documentation.
