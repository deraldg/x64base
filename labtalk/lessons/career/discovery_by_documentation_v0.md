# Discovery by Documentation

**Lane:** career · **Status:** draft · **AIF:** AIF-067 · **Run:** DOCFLUSH-20260722-001
**Observed:** 2026-07-27 · **Proof state:** runtime_observed

---

## The thesis under test

> Documentation improves and proves the code.

That is easy to assert and hard to evidence, because the usual claim is soft:
documentation *helps people understand* a system. This lesson records something
narrower and testable. **The act of writing documentation found defects that no
test, no user, and no crash had found**, and it did so repeatedly enough in one
session to be a method rather than luck.

## What one day produced

Every item below was found while WRITING a description of the system, not while
testing it, using it, or debugging a report.

| # | Defect | What was being documented at the time |
|---|---|---|
| 1 | `SET ERRORSTOP` and `SET INDEXTXN` dispatch correctly and are undiscoverable | writing contracts for the 33-arm SET ladder |
| 2 | `SYSSUBCMD` held 12 scratch rows; its 37-row harvest CSV had a 10-field schema against a 20-field table and could never have loaded | looking for where a subcommand identity would be recorded |
| 3 | `SetUsageText` exists TWICE (descriptor table + locale row); only one was being generated | generating the first copy |
| 4 | `SET DEVDIAG` claims relation diagnostics; there are none (7 call sites, none in a refresh path) | writing its contract from a neighbouring comment |
| 5 | 9 commands registered twice, 2 with handlers that DIFFER on relation maintenance; live one decided by static-init order, not by rule | reading `shell_commands.cpp` to describe the command surface |
| 6 | `SYSFUNC.dbf` unreadable by the doc toolchain for its entire life (phantom descriptor named `0x45` = `'E'`) | answering "what flavour of DBF is this?" |
| 7 | `MEMO_LINES.dbf` unreadable: `LINECONT` is `C(1024)`, classic width byte clamps at 255 | the same question |
| 8 | 8 registry keys are undispatchable dead code (`shell_dispatch` keys on the first token; `preprocess_for_dispatch` rewrites two more) | verifying a handler claim written into a contract |

Eight defects. Zero found by a failing test. One adjacent defect that session
(AIF-065) was found by a **disk filling up** -- which is the point of contrast:
that is what discovery looks like WITHOUT documentation pressure, and it costs a
99 GB tree and an aborted reload before anyone notices.

## Why documenting finds things testing does not

A test asks: *does this behave as I expect?* It can only fail where someone
already suspected something.

Documenting asks a different question: *what IS this, exactly, and where is that
written down?* That question has no expectation to satisfy, so it goes to places
no one suspected. And it has a property tests lack -- **it forces two
descriptions of one thing into the same field of view.** Every defect above is
the same shape:

- the ladder vs the usage text vs the table
- the descriptor copy vs the locale copy
- `shell_commands.cpp` vs the ten files that self-register
- the classic width byte vs the X64M width
- the registry key vs what the dispatcher can produce

Nothing was individually wrong. Each artifact was internally consistent, which
is exactly why no test failed. The defect lived in the RELATIONSHIP, and only an
activity that must reconcile both sides is positioned to see it.

## The counter-evidence, which matters more than the supporting evidence

Documentation is not automatically a truth-finding activity. The same day
produced the opposite:

**A wrong comment was copied into a contract and generated into two artifacts
within hours.** `SET DEVDIAG`'s source comment said "startup/shutdown/relation
diagnostics". That was slightly wrong. It was inherited into a
`@dottalk.subusage` summary, which generated into `SET USAGE` and seeded into
`SYSSUBCMD`. One inaccurate sentence became three inaccurate artifacts, faster
than any human review cycle, precisely BECAUSE the pipeline was working.

**Generation removes drift; it does not preserve intent.** The first generated
`SET USAGE` silently dropped four `SET LOCALE` lines. Nothing stopped
dispatching -- the option simply became undiscoverable. The hand-written text
had encoded a decision (advertise both spellings) that no contract field
expressed, and generation cannot preserve what was never written down.

So the honest thesis is not "documentation proves code". It is:

> **Documentation that is authored against SOURCE proves code.
> Documentation authored against neighbouring documentation propagates error at
> the speed of the pipeline.**

The discipline is the whole difference. Read the parser, not the comment above
the parser. Read the bytes, not the field name.

## The strongest single instance

The most productive question of the session was not an audit instruction. It was
the maintainer asking, in four words:

> what flavor of dbf?

Answering it required reading the actual header bytes. That produced: the X64M
extended header layout, two format versions, the true-width and logical-name
mechanism, the explanation for `LOCALIZE~1`, and two canonical tables that had
been unreadable by our own tooling without anyone knowing.

A plain factual question about the artifact, asked in earnest, outperformed
every deliberate audit that day. Worth remembering when planning the next pass:
**the audit finds what it was built to look for; the question finds what nobody
had thought to look for.**

## The strongest evidence: it contradicted a belief, not a gap

Every defect in the table above filled a gap -- nobody knew the thing. AIF-065 is
different and stronger, and member.derald named why:

> "You need to record it was you who first tagged a problem with the sizes, that
> I thought I had fixed."

**The maintainer believed the LMDB sizing was already fixed.** The documentation
work did not discover an unknown; it disproved a settled belief.

That is a harder result to obtain, because an absence eventually announces itself
-- something is missing, someone trips over it -- whereas a false belief is
self-silencing. Nothing prompts a re-check of a thing you are confident about.
`BUILDLMDB` reinforced the confidence every time it ran: it parsed the size,
echoed it, and wrote a file of exactly that size. Everything visible agreed with
the belief. Only the byte count of an environment that had been *used* disagreed,
and nothing was comparing those two facts.

### Attribution, precisely, because the steps had different authors

- member.derald **directed** the attention: *"check the usage contract in
  buildlmdb for TINY GIANT CUSTOM etc for size options."*
- member.ai.claude.cowork **found** that the ladder is parsed, echoed, written,
  and then overridden at attach; and proved it across three tables.
- member.derald **corrected the remedy** more than once: the unit is containers
  not tags, the vdisk consequence is fatal rather than wasteful, and archiving
  should not merely be reduced but removed from the operation entirely.
- The first proposed fix -- deleting the calls -- was **wrong**, and was caught
  by reading the vendored header rather than by either party's reasoning.

Being told where to look is not finding. Finding is not being right about the
remedy. Recording all three separately is the point of `AGENCY_MODEL_V1.md`,
which notes that git stamps one name where the truth had several.

### Why this counts as documentation PROVING code

The belief was "the sizes work". The proof that it was false came from the
documentation chain doing its ordinary job:

1. a usage contract that stated a ladder precisely enough to be checkable
2. a measurement of what the system actually produced
3. the two compared

Had the contract been vague -- "sets an appropriate size" -- there would have
been nothing to contradict, and the belief would have survived indefinitely. **A
contract specific enough to be wrong is what makes a system provable.** Vague
documentation cannot be violated, which is the same as saying it cannot be
trusted.

## The contract settled a design question it had already answered

The clearest single instance of the thesis in this run was not a defect found. It
was a DESIGN decision resolved by reading a contract that had been correct the
whole time.

The question was whether `BUILDLMDB CLEAN` should archive the environment it
replaces. Three rounds of reasoning narrowed it:

1. first answer -- keep archives, add a retention policy (`-Keep N`)
2. second answer -- discard by default, `ARCHIVE` opts in
3. actual answer -- **the operation has nothing to protect**

And the third answer was already written down, in the command's own risk block:

```
reads_cdx_container:     yes
writes_lmdb_environment: yes
```

`BUILDLMDB` reads the declaration and writes the derived artifact. A size change
alters nothing declarative, so no prior state is at risk, so there is nothing to
archive. The contract had stated that relationship since it was authored. Nobody
had asked it the question.

**This is documentation being generative rather than descriptive.** The risk
block was not a summary of behaviour written after the fact -- it was a statement
of what the command IS, and it was sufficient to decide what the command SHOULD
DO. Reading it replaced an argument.

It also produced the general rule, which no amount of reasoning about storage
would have reached:

> Archive the thing that CHANGES, at the command that CHANGES it. Size is not a
> reason to keep a copy; irrecoverability is.

Applied, it inverts the subsystem: `BUILDLMDB` archived a 1 GiB regenerable
environment, while `CDX CREATE` and `CDX ADDTAG` -- the only operations that
restructure the ~3 KB declaration, the one artifact no other file can rebuild --
archive nothing at all.

### The habit worth copying

Each of the three rounds was narrowed by the MAINTAINER pushing on the premise
rather than the implementation: *"we don't need to back up the .mdb files"*, then
*"why archive the cdx when changing sizes."* Both times the scope shrank and the
reasoning sharpened. The instinct to keep a copy survived three rounds of my own
analysis unexamined, because I kept asking HOW to retain safely instead of
WHETHER anything was at risk.

A design review that only interrogates the mechanism will refine a mechanism
nobody needs. The premise is the cheaper thing to attack, and the contract is
where the premise is usually already written.

## Where these defects come from

Everything above describes SHAPES. member.derald supplied the origin, and it
changes what the remedy has to be:

> "these type of problems can occur from unremedied dev tests, or one AI
> clobbering another. Which is why we are building the AI portal, a project
> derived from need."

### Cause 1 -- the unremedied dev test

An experiment is run, it works well enough, and the last wire is never
connected. The author knew what they intended; nothing else did. The signature
is a mechanism that is 90% built with a comment describing the missing 10%:

- `mapsize_explicit` computed, then `(void)`'d, with
  *"available if you later want to report preset/default distinction"*.
  "Later" is doing all the work in that sentence.
- `SOURCE_HASH` written into every `HELP_TOPIC_LOCALE` row, never read anywhere.
- `X64M` displacement declared in every descriptor, never checked by any reader.
- `edu_missing_shims.cpp` written to cover restricted builds, and excluded from
  restricted builds.
- `SYSSUBCMD` holding three identical batches of the same three rows -- an
  import tested three times and never cleaned up. That one is not inference;
  a scratch state was left as the table's contents for two months.

### Cause 2 -- one AI clobbering another

Multiple sessions on one branch and one working tree. The coordination protocol
records the founding incident: on 2026-07-22 four parallel sessions collided on
AIF-047 → 048 → 049 → 050 in a single sitting, caught only by reading `git log`.

The signature here is different and, once seen, hard to unsee: **a parallel
implementation instead of an edit.** An agent that cannot see, or does not
trust, another's work writes its own file beside it rather than modifying what
is there.

- `cmd_help.cpp` + `cmd_help_grouped.cpp`, both declaring `HELP`
- `cmd_struct.cpp` + `cmd_struct_basic.cpp`, both declaring `STRUCT`
- `cmd_pshell.cpp` + `cmd_pshell_help.cpp`, both declaring `PSHELL`
- `cmd_validate.cpp` + `cmd_validate_unique.cpp`
- nine commands registered in BOTH `shell_commands.cpp` and their own TU, two of
  them with handlers that DIFFER on relation maintenance
- `orderstate::` and `order_state::` -- two spellings of one namespace, the
  second surviving in a commented-out block

Suffixes like `_basic`, `_grouped`, `_help` are the tell. They are what
"I'll add mine next to yours" looks like in a file listing.

### Why the portal, and not more documentation

The distinction matters for what gets built. Documentation is the right remedy
for cause 1 -- a wire left unconnected is discoverable by describing the system,
which is what this lesson demonstrates eight times over.

**It is the wrong remedy for cause 2.** The coordination protocol says so
directly: *"Documentation cannot fix a coordination problem; an allocator and a
presence surface can."* Two agents writing accurate documentation about
incompatible changes produce two accurate documents and one broken tree.

Hence the AI portal and its machinery -- `session_coordinator.py` with atomic
`O_EXCL` claims, the AIF collision gate, the pre-push gate, the agency model
that binds a change to an accountable member, the git-lock lane (AIF-059) still
open. Derived from need, and specifically from a need that no amount of writing
things down was going to meet.

### The reading that follows

A defect's SHAPE tells you how to detect it. Its CAUSE tells you what to build.
This run detected span gaps well and, until this section, had nothing to say
about why they keep appearing -- which would have led to proposing more checks
where an allocator was wanted.

## The rule

1. When documenting, name the two things that describe the same fact, and
   compare them. If there is only one, ask why the other is not written down.
2. Author from the primary artifact. A comment is a claim, not a source.
3. When a description is derived, verify the derivation preserves INTENT and not
   only content -- ask what the hand-written version was doing on purpose.
4. Record what documenting found. The thesis is only demonstrable if the
   discoveries are attributed to the activity that produced them.

## Owed

- The eight dead registry keys and the dead `opt == "RELATIONS"` ladder arm are
  LABELLED, not removed. Removal is a behaviour change and wants its own lane.
- `CONTRACT_QA` stands at 13 findings and has never been worked.
- `cmd_area51.cpp` is held out of the SRC* catalog on purpose as an unplanted
  test for the next full-stack pass (lane doc sec 9a).
