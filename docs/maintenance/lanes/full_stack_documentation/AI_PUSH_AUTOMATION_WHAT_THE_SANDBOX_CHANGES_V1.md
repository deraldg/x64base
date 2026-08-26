# Automating the push: what changes once the sandbox can build, run, and choose an interpreter

    Recorded : 2026-08-26, from flush v6 (DOCFLUSH-20260825-001)
    By       : member.ai.claude.cowork, for member.derald
    Lane     : full_stack_documentation (AIF-068)
    Status   : review-needed. One tool BUILT AND WIRED (section 6); the rest is
               a ranked proposal, not a plan of record.
    Prompted : "what are we learning about automating this with an ai push, we
               can build and run the programs in the sandbox, we have access to
               sample data, we can use other versions of python all on the
               sandbox" -- and then: "you have all of the tools and access you
               need to streamline and harden this process."

## 1. The premise the whole process was designed around is false

Read `help_build_order_check.py`'s own docstring as it stood yesterday:

> This runs in about a second, reads only file times and DBF headers, needs no
> engine and no build, and works **in a sandbox that cannot compile**.

Every design choice in Gate 0 follows from that last clause. The gate reads
CLOCKS because it was assumed it could not read RESULTS. It is a good gate --
it caught the author's own change in v6's first minute -- and it is a gate built
for a constraint that does not exist.

**The sandbox compiles.** AIF-130 established it for the engine on 2026-08-12.
On 2026-08-26 it was established for the rest of the stack in one evening:

    dottalkpp        g++ 13.3 + ninja, ~9 minutes            (AIF-130)
    metacollect      g++ 11.4, -O0, -j4, UNDER 40 SECONDS    (v6 Phase 5)
    store rebuild    CMDHELP BUILD LEGACY + BUILD . <src>, 2.9 SECONDS
    manualgen        full inventory/validate/dry-run on 3.10
    page generator   identical output on 3.10, 3.11, 3.12, 3.13

The correction has been made in three places (`AI_README.md`, this lane's
`METACOLLECT_RUNBOOK_V1.md`, that docstring). **The process built on top of the
false premise has not been revisited, and that is the actual opportunity.**

## 2. The single biggest change: a gate can now be a REHEARSAL, not a clock

A clock answers "was A built before B". A rehearsal answers "what will B
CONTAIN". They are different questions and the second is the one every lost
cycle was really about.

This is not speculative -- it was measured on 2026-08-25, before the owner's run
was possible:

    CMDHELP BUILD LEGACY      461 command rows      owner: 461
    CMDHELP BUILD . <src>     2.9 seconds
      topics    666                                 owner: 666
      contracts 3503 / 207 f                        owner: 3503 / 207
      previews  65 shortened                        owner: 65
      line rows 29263                               owner: 29265   <- 2 apart

**Four of five headline numbers matched exactly, predicted in advance.** And the
fifth is the more valuable one, because a rehearsal that always agrees teaches
nothing. The two-row gap, and a larger one in LEGACY arg rows (container 2609,
owner 2363), point at `./src` resolving differently under `datarun.ps1`'s
working directory. **That is a real host/sandbox divergence and it is the reason
a rehearsal must be a COMPARISON, never a replacement.**

The shape:

    sandbox    build every program from the tree, run the full push,
               emit a PREDICTION file: every headline count, every topic-set
               delta, every candidate row count, hashed
    owner      run the real push on MSVC
    gate       diff actual against prediction; a difference is a FINDING, and
               so is a difference that was predicted and did not appear

**This turns the owner's run from a discovery into a verification**, which is
the difference between "run it and see" and "run it and check". Phase 5 already
worked this way tonight by hand: the prediction was written down before the
emit (SYSCMD "close to the 226 baseline; 245 is an upper bound"), and the actual
was 229. The prediction held, so the run confirmed rather than surprised.

## 3. Cheap running makes a class of check possible that was not before

Some checks are worthless unless you can run a program twice. The
`METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md` contract has this clause:

> Rows sort by `CAN_NAME`; repeated runs over unchanged source must be
> byte-identical. ... Determinism is proved by two byte-identical emissions.

**It is the strongest clause in that document and it had never been exercised**,
because running metacollect meant asking the maintainer. It was exercised on
2026-08-26 -- all three candidates byte-identical across two emissions -- and it
cost seconds. Determinism is what makes a re-run a CHECK rather than a
replacement, so this clause is load-bearing for the whole rehearsal idea.

Same category, same evening: four Python versions exercised in one command,
where the standing belief was a single pinned version.

## 4. What automation must NOT inherit: checks that cannot answer

v6 found SIX numbers that were true about one question and read as the answer to
another:

    IMPLEMENT             "is there a registration"  read as "can this be typed"
    a sha256              "same newline?"            read as "same manual?"
    the banner            two halves, two staleness  read as build freshness
                          mechanisms
    dispatch_reachable    false on all 1,083 rows    read as reachability
    pages=0               "what was written"         read as "what was selected"
    the DOT-only filter   silence                    read as "nothing to page"

**An automated push amplifies this rather than fixing it.** A human running by
hand notices that ABOUT cannot really be unreachable. A pipeline records
`dispatch_reachable=false` 1,083 times and moves on, and the next pipeline reads
that as data. So the ordering matters:

**Make each check answer the question it is named for BEFORE automating the
running of it.** Automation multiplies whatever it is given, signal or not.

The concrete rule this lane already pays for, promoted here: *before writing an
assertion, ask what OTHER world produces the same number. If the answer is "a
healthy one" or "a broken one", it is not measuring what it claims.*

## 5. The bottleneck tonight was DOCUMENTARY, not technical

Three items were filed blocked and none of them was:

    "metacollect is a Windows exe"          a fact about a FILE
    "requires Python 3.12"                  a fact about an INTERPRETER
    "not buildable in the mounted sandbox"  a fact about a sandbox that is gone

Cost: one phase filed blocked, one generator filed blocked, and a runbook
heading that agreed with both. Fix: forty seconds, and three tarballs.

**An automated push reads the same routing documents an agent does**, so this is
not a human-only failure -- it is the failure most likely to survive automation
intact, because a pipeline has even less inclination to test a stated
impossibility than a person does.

The discipline, which this lane already wrote down and did not follow
(`DOCFLUSH_V6_GATE.md` method note 3): **an item is blocked only when someone
has TRIED it and been stopped.** If the settling command can be written down,
the item is QUEUED. The automatable form of that rule is section 7's item 3.

## 6. BUILT AND WIRED TODAY: step 6, program freshness

From the owner's own structural note -- *"so step 1 is really compile all of the
programs first in the fullstack push"*. Gate 0 answered that for the ENGINE
only. The push runs `metacollect` too, a separate target, default OFF, and
nothing was checking its staleness; it was verified by hand during Phase 5, and
a hand check is not a gate.

    tools/coordination/program_freshness_check.py
    wired as docpush_preflight.py step 6 [HARD]

    COMPILED  is the binary newer than EVERY source that goes into it
    PYTHON    what version does it demand, and is the demand an EQUALITY
    COVERAGE  every add_executable() in the tree is DECLARED or EXCLUDED
              BY NAME with a reason -- so the manifest cannot go stale silently

**The hand check it replaces was measuring the wrong thing.** By hand, three
metacollect sources were compared. The target has THIRTEEN, and the newest is
`src/datadict/ddict_dbf_reader.cpp` at 2026-08-25 00:05 -- thirteen hours before
the binary was built. It passes, narrowly, and a change to that file would have
been invisible to the hand check entirely.

**Fault-injected before being trusted**, four paths on a synthetic root: healthy
PASS; one source touched newer -> FAIL naming the file; exe absent -> skip;
a new `add_executable` -> named, and an error under `--strict`.

**The injection found a defect in the tool itself, on its first run.** A
synthetic root with a genuinely stale exe returned 2 ("could not measure")
instead of 1 ("stale"), because an unrelated unreadable path was checked first
-- the AIF-128 shape exactly, a verdict arriving from a different question than
the message names. Fixed: both are reported, the harder verdict wins. **A gate
nobody has watched fail is not a gate, and this one failed usefully.**

## 7. The next three, ranked by what each would have caught

**1. A content-level assertion in the preflight.** 6' is a MEMBERSHIP check and
says so. The id-stripped content diff -- `COMMANDS` keyed on
`(CATALOG, COMMAND)`, `HELP_LINE` as a multiset of
`(TOPICKEY, KIND, SOURCE, ROLE, TEXT)` -- is what saw the substantive half of
tonight's cycle: seven rows moved, `5 - 2 = +3` reconciling exactly, while both
adopted assertions saw only `+1`. It is still a hand-run workaround. **Would
have caught: the `implemented yes -> no` flip, which nothing else could report.**

**2. The rehearsal harness of section 2.** Build every program outside the tree,
run the push, emit predictions, diff. **Would have caught: the stale-exe class
before the owner spent a run on it, and the two-row divergence would have been
a standing measurement instead of an unexplained note.**

**3. A stated-impossibility check.** Flag any routing document asserting
"cannot build / cannot run / not buildable" without an adjacent measurement
date. Advisory, cheap, and it would have fired on all three of tonight's
ceilings -- `AI_README.md:446` for thirteen days, `METACOLLECT_RUNBOOK_V1.md:23`
for a month, `help_build_order_check.py:44` for a day after its own correction
was written somewhere else.

## 8. What stays human, and it is small

    Gate 3   authorization to execute. Not automatable and should not be.
    Gate 5   binding candidates by SHA. A candidate emit is not an
             authorization, and tonight's emit is a candidate.
    Rulings  the five open ones. Reporting a defect is this lane's job;
             prescribing the repair belongs to the area that owns the code.

Everything else in v6 -- Gate 0, the store verification, Gate 4's set and
content diffs, Phase 5's emit and compare, Phase 6's harvest, dry run and page
selection -- was mechanical, and every one of them was performed from a sandbox
tonight.

**The honest caveat, which does not shrink with better tooling:** a sandbox
green is not a green on the maintainer's toolchain. MSVC and libstdc++ lay out
differently, the platforms differ on stack size, and the two-row divergence in
section 2 is a live example. **Name the platform every time.** The sandbox's job
is to PREDICT and to REFUTE. It is never the authority.

## Good Neighbor

    What changed  : this document; tools/coordination/program_freshness_check.py
                    (new); docpush_preflight.py (step 6 wired, docstring).
                    No source, no data, no store, no published workspace.
    Whose area    : lane full_stack_documentation / AIF-068.
    Authorization : the owner, 2026-08-26 -- "you have all of the tools and
                    access you need to streamline and harden this process."
    Verify        : $py tools\coordination\program_freshness_check.py --root . --strict
                      expect PROGRAM FRESHNESS PASS, coverage ok.
                    $py tools\fullstack_docs\docpush_preflight.py --root .
                      expect step 6 lines and PREFLIGHT PASS.
                    Section 6's injection reproduces on a synthetic root: the
                    thirteen declared paths, a fake exe, then touch one source.
    Undo          : revert the two tool changes; delete this document. Step 6 is
                    additive -- steps 1-5 are untouched.
