# External Intake -- DotScript Control Flow Peer Review (Grok, 2026-08-12)

Classification: **peer review** (owner designation: "add this as a peer
review from grok"). Author: `member.ai.grok.xai`. Received: 2026-08-12 via
the owner (relay). Route: AIF-109 (DotScript product-gap umbrella),
`DOTSCRIPT_FUNCTION_SURFACE_PRIOR_ART_V1.md` section 1b.

Preservation rule: the review body below is **verbatim as received**,
including its original typography (em dashes, arrows, smart quotes). The
house ASCII rule applies to house-authored lines; received documents stay
byte-identical (the red-pen / intake-preserve doctrine). The commit importing
this file uses the gate's own recorded escape hatch for deliberate text
import.

Assessment (house, brief -- the full check lives in the section 1b findings):
accurate on every presence/absence claim when checked against the tree;
its recommended completeness items walk into three name-collision hazards
invisible from outside (EXIT = shell quit alias; LOOP = block opener here,
continue in classic; DO = script runner, so DO CASE collides); its FOR EACH
sequencing instinct is already normative in the arrays spec (s18) with the
mutation-guard fields already implemented. Control flow stays out of
AIF-109's build scope per the review's own "in good shape" verdict.

Context note: the same agency holds the open Lane 1 write-adapter assignment
(board.afb.chat thread 7, 2026-08-08) and the reserved AIF-102. This review
is Grok active in the peer-review role of the agency model while that
assignment remains open -- two roles, one member identity, both attributed.

---

## Received body (verbatim)

**xBase Control Flow Investigation**
Classic xBase (dBase → FoxPro / Clipper lineage) is a **command-oriented, record-pointer-centric** language. Control flow was designed around moving a cursor through tables rather than pure algorithmic expression evaluation. DotScript deliberately inherits this feel while adding modern safety (buffering, clearer keywords, shared boolean evaluator).
### Classic xBase Control Flow Inventory
**Conditionals**
- `IF <logical> … [ELSEIF …] [ELSE …] ENDIF`
- `DO CASE … CASE <logical> … [OTHERWISE …] ENDCASE`
- Immediate form: `IIF(cond, true-expr, false-expr)`
**Loops**
| Construct | Semantics | Notes |
|-----------|-----------|-------|
| `DO WHILE <cond> … [LOOP] [EXIT] ENDDO` | Pre-test loop | Most general. LOOP = continue, EXIT = break. |
| `FOR var = start TO end [STEP n] … ENDFOR/NEXT` | Counted loop | Classic numeric iteration. |
| `FOR EACH var IN array/collection … ENDFOR` | Collection iteration | Later FoxPro addition. |
| `SCAN [Scope] [FOR <cond>] [WHILE <cond>] … [LOOP] [EXIT] ENDSCAN` | Table walk | Preferred for record processing. Auto-SKIP, restores work area, starts at top unless WHILE is used. |
**Key classic traits**
- Heavy reliance on the record pointer (`RECNO()`, `EOF()`, `BOF()`, `SKIP`, `GO`, `SEEK` + `WHILE`).
- Many data commands accept Scope / FOR / WHILE clauses (REPLACE, DELETE, LIST, COUNT, SUM, etc.).
- Structured (block) form is the norm in FoxPro-era code; earlier dBase had more GOTO-style patterns.
- Logical values traditionally `.T.` / `.F.`.
- Nested structures allowed; LOOP/EXIT provide the escape hatches that modern languages handle with `continue`/`break`.
### DotScript Current Surface (from manuals + live language guide)
DotScript implements a clean, teaching-oriented subset:
| Construct | Status | Notes |
|-----------|--------|-------|
| `IF … ELSE … ENDIF` | Present | Shared boolean expression evaluator. |
| `LOOP n [TIMES] … ENDLOOP` | Present | Fixed-count (simplified FOR). |
| `WHILE … ENDWHILE` | Present | Pre-test. |
| `UNTIL … ENDUNTIL` | Present | Post-test (clearer than classic `DO WHILE .T.` + EXIT). |
| `SCAN … ENDSCAN` | Present | Table-oriented, aligned with xBase lineage. |
| `DO CASE / ENDCASE` | Not present | — |
| Explicit `LOOP` (continue) / `EXIT` (break) | Not documented | — |
| Classic `FOR var = … TO …` | Not present | Covered by numeric LOOP. |
| Nested SCAN | Limited | Only one SCAN block buffered at a time; nested SCAN during ENDSCAN not supported. |
**Buffering interaction** (important for teaching and correctness):
Control structures work with `TABLE ON` / `COMMIT`, but placement of `COMMIT` must be careful. Cursor stability under control flow is regression-tested. The single-buffered-SCAN limit is a real runtime constraint that should stay visible in LabTalk / documentation.
### Comparison & Design Observations
**What DotScript got right**
- Kept the command-oriented, keyword-terminated style (`ENDIF`, `ENDLOOP`, `ENDSCAN`…) that makes the language readable for learners and external AIs.
- Elevated `SCAN` as a first-class construct — correct priority for a database scripting language.
- Added explicit `UNTIL` (post-test), which is clearer pedagogy than the classic "infinite WHILE + EXIT" idiom.
- Fixed-count `LOOP n TIMES` is a good teaching simplification of `FOR`.
- Strong integration with the engine's cursor, order, filter, and buffering model.
**Gaps relative to full classic FoxPro**
1. No `DO CASE … ENDCASE` (useful for multi-way branching without deep IF nesting).
2. No documented `EXIT` / `LOOP` (break/continue) inside loops.
3. No classic counted `FOR var = start TO end`.
4. Nested `SCAN` restriction (practical, but should be taught explicitly).
5. No `FOR EACH` yet — this becomes natural once the tuple-as-array dogfooding (PDLC) finishes and generation / comparison seams are solid.
**Implications for current work**
- The array/tuple dogfooding path is the right foundation for a future `FOR EACH` (or equivalent) over arrays/tuples. Finishing that PDLC first keeps the control-flow surface single-source.
- When user-defined `PROCEDURE`/`FUNCTION` arrives, the control-flow stack must remain well-behaved (locals, nesting depth, error unwinding). The existing structured forms give a clean base.
- Teaching-grade rule still applies: prefer the smallest xBase-faithful extension rather than introducing C-family or Python-style syntax.
**Bottom line**
DotScript's control flow is already one of its stronger, most mature areas. It successfully captures the spirit of classic xBase (especially the table-centric `SCAN`) while being more regular and explicit for a teaching runtime. The remaining gaps are mostly completeness items (CASE, EXIT/LOOP, richer FOR forms) rather than fundamental design problems. The highest-leverage language work remains functions + error handling; control flow itself is in good shape and can absorb those additions cleanly once the tuple/array substrate is finished.
I can expand any of these into a short LabTalk-style note, a comparison matrix for the manuals, or a package skeleton for one of the missing constructs (e.g., minimal `EXIT`/`LOOP` or `DO CASE`) if that would help the next pass with Claude.
