# Gate 2 -- runtime baseline review (flush v5)

    Run        : DOCFLUSH-20260812-001
    Recorded   : 2026-08-12
    Script     : runtime_baseline/fullstack_pre_refresh_runtime_v1.dts
    Transcript : runtime_baseline/fullstack_pre_refresh_runtime_v1.txt
    Runtime    : dottalk++ v0.6 (2026-08-12, 46bd9233 dirty), build Aug 12 2026 18:30:58
    Verdict    : BASELINE ACCEPTED as a record of the ad-hoc-rebuilt store.
                 NOT accepted as a clean pre-refresh line -- see section 1.

---

## 1. What this baseline is, and is not

It is the first gated reading since v4's Gate 4. It is NOT a pre-refresh capture:
the HELP store was rebuilt ad hoc earlier the same day, outside any run envelope,
with the documented dotref recipe half-skipped. This transcript therefore records
where that left the store, so the correct rebuild later in this run has an honest
comparison point. Any diff against v4's Gate 4 numbers is not like for like.

---

## 2. DECISIVE FINDING -- dotref.hpp is not in the running binary

`DOTHELP` renders `dotref::catalog()`, which is compiled INTO the exe. The
transcript shows the PRE-CHANGE entries:

    WORKSPACE [OPEN <DBF|dir>|CLOSE|SAVE <name>|LOAD <name>]
    ERASE <target>  "Erase a file or supported target..."
    REGRESSION [USAGE|LIST|SHOW <name>|RUN <name>|<name>|ALL]

None of `MEMO` / `MINIDB` / `RAM` / `PARTIAL` / `WRITEBACK` / `FIND` / `DIR`
appear. Cause, measured rather than inferred:

    git show HEAD:include/dotref.hpp | grep -c "MEMO [V3|MINIDB]"   -> 0
    grep -c "MEMO [V3|MINIDB]" include/dotref.hpp                   -> 1
    git status --short -- include/dotref.hpp                        -> " M"

**The contracts slice was never committed.** The 18:30:58 build compiled HEAD,
which predates the dotref rewrite. Nothing is wrong with the harvester and
nothing is wrong with the recipe.

A steward hypothesis is retracted here: an earlier reading of the built store
suggested "long dotref summaries are truncated by the harvest", because short
syntax strings matched a grep and long prose did not. That was wrong. The
matching strings came from the `@dottalk.usage` blocks in `cmd_workspace.cpp` and
`cmd_regression.cpp`, which ARE committed (`aa32edbc5`, `6f7e73e14`); the dotref
prose was simply absent from the binary. The lesson is not about the harvester:
**grepping a built artifact cannot attribute a hit to a source when two sources
carry similar wording.** The authoritative instrument was `DOTHELP`, and it
answered in one line.

Consequence for Gate 4: the rebuild sequence must be
(1) commit the dotref/contract slice, (2) REBUILD the engine, (3) back up
`dottalkpp/data/help`, (4) stop `DotTalkBBSD`, (5) `CMDHELP BUILD LEGACY`,
(6) `CMDHELP BUILD . <ABS src>`. Steps 2 and 5 are the ones this session has now
skipped once each.

---

## 3. Store state (accepted as the v5 entry line)

    line rows        28,731        (v4 Gate 4: 28,368;  +363)
    topics              527        (v4 Gate 4:     525;    +2)
    CMDHELPCHK       structural PASS -- "OK no structural issues found"
    MANUAL            8/8 MAN tables present (matches v4)
    mojibake          NONE in the transcript

By SOURCE: USAGE_CONTRACT 14,914 / SOURCE_MINER 7,503 / SHARED_MSG 2,637 /
DOTREF 896 / CURATED_DOC 868 / EDREF 786 / FOXREF 665 / REGISTRY 462.

**The clean transcript is itself a result.** v4 found mojibake here
(`cmd_buildvectors.cpp:21`, a U+2014 rendering as a CP437 garble). This capture
shows none, which independently confirms the em-dash sweep (`4c584ba8f`) reached
the HELP surface -- the outcome AIF-088's deferred task existed to produce.

---

## 4. `FILE()` -- present in the runtime, absent only from SYSFUNC

The transcript settles the scope of the remaining gap:

    Function Inventory : FILE  Logical  1  1  function_catalog  partial  fn_string.cpp
    HELP FUNCTIONS     : LOGICAL (3) -- EMPTY  FILE  LIKE
    CMDHELP TOPICS     : DOT|FILE present

So the engine, the reflection surface, and HELP all know `FILE`. The ONLY stale
authority is `SYSFUNC_IMPORT_v1.csv`, which is why `FN_COVERAGE` warns
`IMPLEMENTED 75 / CATALOG 74`. That remains blocked on the metacollect build
(Gate 0 precondition, section 3 of the envelope).

---

## 5. New finding -- ONE command, THREE descriptions, in one build

The transcript renders `WORKSPACE` from three different authorities, and they do
not agree:

1. **dotref** (`DOTHELP`): `WORKSPACE [OPEN <DBF|dir>|CLOSE|SAVE|LOAD]`, with a
   Usage block listing six forms.
2. **the `@dottalk.usage` contract** (source-mined): the current surface,
   including MEMO / MINIDB / RAM / WRITEBACK / PARTIAL.
3. **the `HELP WORKSPACE` topic renderer**: a THIRD wording --
   "Manage live work-area/session state", with its own Syntax block listing six
   forms and its own Notes.

Even after dotref is rebuilt, (1) and (3) will still be separately authored
texts describing the same verb. This is the drift surface the lane exists to
close, and it is not currently gated: `refcheck` proves every dotref entry
RESOLVES to a command, but nothing proves the three descriptions AGREE.

AIF-067 M2 is chartered as exactly this check ("flag dotref summaries that
drifted from the contract") and is deferred. Recorded here as a Phase 1 input:
the third surface (the HELP topic renderer) may not be in M2's scope, and should
be.

---

## 6. Minor defects observed in ABOUT (not blocking, not this lane's)

- **Two build stamps disagree in one binary.** Startup banner: `build Aug 12
  2026 18:30:58`. `ABOUT` page 2: `Build Date : Aug 12 2026 18:19:12`. Eleven
  minutes apart, so two different capture points are being reported as one fact.
- **Numeric formatting applied to version identifiers.** `Compiler : MSVC 1,944`
  (1944), `C++ Std : 202,002` (202002), `OS : Windows 6.1.7,600` (6.1.7600).
  Thousands separators on values that are not quantities.
- `Console Size : 0 x 0` under datarun, expected for a redirected run; noted so a
  later reader does not treat it as a defect.

Filed as observations with evidence, not as this run's work.

---

## 7. Gate 2 disposition

ACCEPTED as the v5 entry line, with section 1's caveat attached to every number
in section 3.

Blocking for Gate 4:

1. Commit the dotref/contract slice and REBUILD before any rebuild attempt.
2. Metacollect repair (Gate 0 precondition) before claiming SYSFUNC agreement.

Carried to Phase 1:

- The 205-vs-229 harvest-scope question (envelope section 4, Q1).
- foxref and `FILE()` (Q2).
- The three-descriptions finding (section 5 above), as a proposed extension to
  AIF-067 M2's scope.
