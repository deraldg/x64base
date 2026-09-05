# AIF-155 -- RUNTIME_DEF_FAMILY: a custom function is a STUDENT surface

**Status:** chartered. Identity ruled by the owner 2026-09-05. Findings and
registration only -- one milestone is named below and NOTHING is proposed as
syntax.
**Claim:** `coordination/aif/AIF-155.claim` (run `COWORK-20260905-002`,
`member.ai.claude.cowork`, lane `runtime-def-family`).
**Owner:** `member.derald`  **Author:** `member.ai.claude.cowork`
**Freshness:** 2026-09-05.

---

## 0. The ruling, and how thin it is

The owner named the surface while asking about it:

> "we have an aif or other project number for **custom function for students**,
> see if how it is wired in, it might self-register"

and then, on being shown that the facility has no number and that its lane doc
describes a different audience:

> "i am the owner -- promote and activate"

**That is ONE naming, not a pattern**, and this charter says so rather than
dressing a single phrase as a settled doctrine. AIF-153 recorded BROWSETUI's
identity off three separate statements; this one has one. What it settles is the
AUDIENCE. It does not settle syntax, sequencing, or whether the facility is
ready to be taught with -- section 4 argues it is not.

**The tree said something else.** `RUNTIME_DEF_FAMILY_LANE_V1.md` (2026-07-21)
opens: *"give an AI (or developer) a way to mint throwaway, session-only
commands, functions, and field types at runtime."* No occurrence of student,
teaching, lesson or campus anywhere in its 164 lines. `DEFFN`'s own usage block
files it `category: diagnostics`, `status: experimental`. So the identity
recorded here is a CHANGE of audience, not a transcription of one.

## 1. What the facility is

| Unit | Surface | State | Seam |
|---|---|---|---|
| DEFCMD / UNDEFCMD | commands | shipped (`77ee573a3`) | `dli::registry()` live map |
| `fn_custom` hook | functions (infra) | shipped | new live registry |
| DEFFN / UNDEFFN (text body) | functions | shipped | `fn_custom` |
| DEFFN formula / DotScript body | functions | **planned** | -- |
| Mini-memo generic codec | field types | PARKED 2026-07-21 | `register_codec` |
| DEFTYPE | field types | PARKED 2026-07-21 | `register_codec` |

The parking is a real decision with a retrieval trigger, not neglect: runtime
custom field types wait until the type system can make a custom type MEAN
something rather than dress a blob as a field.

## 2. It had no number, and four files said so in the same place

Before this AIF: a lane doc, shipped code in four files, a regression spec,
dotref entries, and a governing security doctrine -- and **no AIF, no R number,
no claim file.** Measured: no `AIF-`, no `R\d+`, no `OI-` anywhere in the lane
doc. The only register mention is **AIF-109** (DotScript product-gap umbrella),
which lists `cmd_deffn.cpp` and `cmd_defcmd.cpp` under *bears on* -- it does not
own them.

And the `@dottalk.file` header of `cmd_deffn.cpp`, `cmd_defcmd.cpp`,
`fn_custom.cpp` and `fn_custom.hpp` each named RUNTIME_DEF_FAMILY **in a prose
comment** while leaving the machine-readable `lane:` slot **blank** -- four of
the 1003 blanks measured across `src/` and `include/`. The identity was written
where only a human reads and omitted where a tool does. Now
`lane: runtime-def-family` (`02abe2f76`), matching the slug form already used by
`dbf-vfp-type-support` and `application-ui-dsl`.

## 3. "It might self-register" -- three senses, one true

The owner's hypothesis, answered by measurement:

- **The FILE self-registers into the BUILD. TRUE.** `fn_custom.cpp` rides the
  recursive glob in `src/CMakeLists.txt` with no explicit entry; the lane doc
  section 3 states this deliberately.
- **The COMMANDS do not. FALSE.** `shell_commands.cpp:506-509` is four
  hand-written `registry().add` lines for DEFCMD / UNDEFCMD / DEFFN / UNDEFFN.
- **A DEFINED FUNCTION registers nowhere durable. FALSE BY DESIGN.** `store()`
  in `fn_custom.cpp:40` is a function-local `static std::map`: process lifetime,
  never written to disk. Section 6 of the lane doc makes it a safety rule --
  *"Never persist -- session-only; everything vanishes on EXIT."*

The word being remembered is probably the regression entry's own: DEF_FAMILY is
described as **"Self-bootstrapping"**, meaning the spec mints its own
definitions and cleans them up.

**Consequence for a student surface, stated because it is not obvious:** a
function a student defines reaches NO authority. Not SYSFUNC, not `dotref`, not
`foxref`, not help. `DEFFN LIST` is the only place it appears. (The DEFFN
*command* is catalogued -- three `dotref` entries. The student's *function* is
not, and cannot be.) That is correct for a session-only definition and it means
discoverability is zero by construction.

## 4. The gap that decides whether this is teachable

**A DEFFN body cannot use its arguments.** `DEFFN GREET = hello` then
`? GREET()` returns `hello`; `? GREET("world")` also returns `hello`. Arguments
are accepted up to `kCustomFnMaxArgs = 16` and dropped. The lane doc calls the
formula body `DEFFN NAME(a,b) = <expression>` a follow-up, "not MVP".

Everything shipped so far makes the facility PROVABLE. None of it makes it
TEACHABLE. A custom function that ignores its parameters demonstrates a
registration seam; it does not let a student write a function. **This is the
milestone this AIF exists to name**, and it is the only work item here with a
claim on being first.

## 5. Five insertion points, not four

The lane doc section 3 lists four (`value_eval.cpp` twice, `rhs_eval.cpp`
twice). There is a fifth: **`src/cli/expr/eval.cpp:122`** consults
`find_custom_fn` in the PREDICATE AST -- the same AST where `ISNULL` lives. So a
custom function resolves in a `FOR` clause as well as in `?` / CALC / WHERE.
More reach than the doc claims, recorded nowhere until now. Not a defect; a doc
that stopped being complete.

## 6. The doctrine collision, which is the owner's to rule on

`DEFFN` and `DEFCMD` are governed by
`docs/maintenance/AI_DEV_TOOLS_SECURITY_DOCTRINE_V1.md`, whose section 0 reads:

> "Any agent -- AI or human -- must obtain *limited*, scoped permission before
> using the AI-friendly dev-tools. This requirement is global. The project owner
> is the sole exemption."

The gate is REAL and CALLED -- `cmd_deffn.cpp:96`, `cmd_defcmd.cpp:106`, both
`devtools_permitted()` -- and currently DORMANT: it permits unless
`DOTTALK_DEVTOOLS_REQUIRE_PERMISSION` is set.

**Students are exactly the population that gate declines the day it is armed.**
Harmless today. It stops being harmless the moment the doctrine's technical
enforcement is switched on, and at that point one of the two documents is wrong.
This charter does not resolve it. It records that the two rulings now point in
opposite directions and that the collision was created by this AIF, not found by
it.

## 7. Coverage, and what today's commits changed

`DEF_FAMILY` -- the lane's regression spec -- **had no grader until 2026-09-05.**
It carried `DEF-FAMILY-REGRESSION-BEGIN` / `-END`, the exact affordance
`require_exact_transcript_block` consumes, and nothing consumed them. Measured:
`REGRESSION RUN DEF_FAMILY` printed its transcript and returned no verdict at
all -- not PASS, not FAIL, not a count -- while both L3 arms reported 6/6. A
spec in that state cannot go red, so the promotion the owner asked for would
have added a permanently green line to `REGRESSION ALL`.

`02abe2f76` supplies `RegressionValidator::DefFamilyV1`: a 22-line exact
transcript block, in order, on the routed channel. Green on its first run, with
the block transcribed from a `std::cout` console paste and matched against the
`SET ALTERNATE` file line for line -- which also measured, rather than quoted,
the claim that the two channels share one capture.

## 8. NOT CLAIMED

Stated rather than implied, so a reader does not credit this charter with more
than it did:

1. **That the student ruling has a curriculum behind it.** It has one sentence
   from the owner and no lesson, no LabTalk entry, no sequence.
2. **That the facility is ready to teach with.** Section 4 argues the opposite.
3. **That DEFTYPE is in scope.** It is parked with a retrieval trigger that has
   not fired.
4. **That anything here proposes syntax.** AIF-109's five owner rulings on the
   DotScript function surface are still pending and this charter does not
   pre-empt any of them.
5. **That `DEF_FAMILY` green means custom functions take parameters.** It does
   not; see section 4. The validator's own comment says so at the point of use.
6. **That the dev-tools collision is resolved.** Section 6 names it and stops.

## 9. Work items, unordered

- **The formula body** -- `DEFFN NAME(a,b) = <expression>` with args bound.
  The milestone; blocked on AIF-109's pending rulings about the parameter
  surface, which is where it should be blocked.
- **Promote `DEF_FAMILY`** to the default suite now that it can fail: flag,
  rebuild, read `REGRESSION LIST` for the `[default]` tag, then `REGRESSION ALL`,
  then record the in-suite paragraph.
- **Reconcile the metadata with the audience** -- `category: diagnostics` and
  `status: experimental` describe a dev-tool, not a student surface.
- **Correct the lane doc's "four insertion points" to five** (section 5).
- **Rule on the dev-tools collision** (section 6). Steward/owner.
- **Decide whether a student function needs any discoverability at all** beyond
  `DEFFN LIST` (section 3), given it can never persist.
