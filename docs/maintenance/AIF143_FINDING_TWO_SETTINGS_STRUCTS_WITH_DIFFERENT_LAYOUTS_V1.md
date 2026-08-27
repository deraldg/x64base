# AIF-143 -- TWO `cli::Settings` STRUCTS, DIFFERENT LAYOUTS, ONE NAMESPACE

    Number  : AIF-143, claimed 2026-08-27 with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001, lane
              'duplicate-settings-struct'). Claim file verified present at
              `coordination/aif/AIF-143.claim` before the number was cited.
    Found   : 2026-08-27, while enumerating the readers of `deleted_on` for
              AIF-142. The grep for that member returned hits in TWO headers.
    Lane    : engine/shell settings. Predates multi-workspace entirely.
    Status  : review-needed. The author does not self-approve.
    Basis   : SOURCE-EVIDENCED. NOT RUN, and it CANNOT be run without first
              committing the defect -- the failure requires adding an
              `#include` that nobody has added. See sec 8.
    Shape   : R5 -- two answers to one question. Aggravated by the mechanism:
              the language does not require the compiler to tell you. This is
              ill-formed, no diagnostic required.
    Severity: LATENT AND ARMED. Zero impact today. The first `#include` of the
              stale header is a silent wrong-answer bug with no build error.

## 1. THERE ARE TWO OF THEM

`include/cli/settings.hpp:16` opens `namespace cli` and declares
`struct Settings` at `:55`. It is the live one: `cmd_set.cpp` includes it at
`:129` and writes `deleted_on` through it at `:1490`.

`include/sessions.hpp:15` opens `namespace cli` and declares `struct Settings`
at `:30`. Same name. Same namespace. Not a forward declaration, not a
specialisation, not in a `detail` or versioned namespace -- a full second
definition of the same type.

Both carry `status: supported` in their `@dottalk.file` block.

Both define the singleton the same way:

    static Settings& instance() { static Settings s; return s; }

and both define `deletedOn()` / `setDeleted()` over it --
`settings.hpp:141-142`, `sessions.hpp:88-89`.

## 2. THE LAYOUTS DIFFER, AND THE DIFFERENCE IS UPSTREAM OF `deleted_on`

Three members exist in the live header and NOT in the stale one:

    settings.hpp:60   std::atomic<bool> passive_dev_diagnostics_on   // SET DEVDIAG
    settings.hpp:80   std::atomic<bool> index_txn_on                 // SET INDEXTXN
    settings.hpp:108  std::string       message_locale               // SET LANGUAGE

The first one is the dangerous one. It sits at `:60`, and `deleted_on` sits at
`:70` -- **the extra member comes BEFORE `deleted_on`**. In `sessions.hpp`,
`deleted_on` is at `:44` with no such member ahead of it.

So the two structs do not merely differ in size. **`deleted_on` and every
member declared after it sit at a different byte offset in the two
definitions.** This is not a case where the stale copy is a safe prefix of the
live one.

## 3. WHAT HAPPENS THE DAY SOMEONE INCLUDES IT

One definition rule: a class with external linkage may have multiple
definitions across translation units ONLY if they are token-for-token
identical. These are not. The program is then **ill-formed, no diagnostic
required** -- the standard explicitly does not oblige any tool to complain.

In practice, on every toolchain this project builds with:

1. It COMPILES. Each translation unit sees exactly one definition and is
   internally consistent.
2. It LINKS. `instance()` is an inline function; the linker keeps ONE body and
   discards the other, with no warning. There is now one singleton object,
   whose real layout is whichever definition won.
3. The translation unit compiled against the OTHER definition reads and writes
   `deleted_on` at the wrong offset -- landing on a different `atomic<bool>`
   member entirely.

The observable result is a setting that appears to work and silently governs
something else. `SET DELETED OFF` would toggle a neighbouring flag; a consumer
reading `deleted_on` would receive that neighbour's value. No compile error, no
link error, no runtime diagnostic, and nothing in the source of either file
looks wrong when read on its own.

This is the worst available failure mode: **wrong answers, silently, from code
that reads correctly.**

## 4. WHY IT IS INERT TODAY, AND WHY THAT IS NOT SAFETY

Measured: `git grep -l 'sessions\.hpp'` over `*.cpp` and `*.hpp` returns
NOTHING. No translation unit includes it. The file is tracked
(`ls-files --error-unmatch` succeeds) and NOT ignored (`check-ignore` finds no
rule), so it is a live, committed, indexed part of the tree that nothing
consumes.

That is the entire reason there is no bug today. The safety is not structural,
it is coincidental -- it rests on nobody having typed one line. And the line is
attractive to type: the file is called `sessions.hpp`, it sits in `include/`
next to headers people do include, its content is exactly what someone
searching for shell settings is looking for, and its `@dottalk.file` block says
`status: supported`.

A hazard whose only defence is that nobody has noticed the file is not
defended.

## 5. HOW IT ACQUIRED A SUPPORTED STAMP

`include/sessions.hpp` was last touched by `3706da78c` -- "AIF-050 M2/M3:
`@dottalk.file` full-tree backfill -- 1034 source files + schema upgrade" --
and before that by `fecc3951e`.

So the `status: supported` line was not a judgement anyone made about this
file. It was applied by a sweep that visited 1034 files and stamped each one.
The sweep asked "does this source file carry a header block?" and correctly
answered no, then supplied one. It did not ask, and was not built to ask, "is
this file reachable?"

**R75, in a new place: a gate sees the shape it was built to see, and its
silence about a class of thing is not evidence the class is clean.** The
backfill's output here is not merely uninformative -- it is an AFFIRMATION. The
file now asserts, in machine-readable metadata, that it is supported. The
sweep made the hazard more attractive, not less.

Recorded as a property of backfills generally, not as a criticism of AIF-050:
**a metadata sweep converts absence-of-metadata into presence-of-a-claim, and
the claim inherits the sweep's blindness.**

## 6. WHAT THIS FINDING DOES NOT CLAIM

- It does NOT claim a bug exists today. Nothing includes the header; sec 4
  measured that. The finding is about a reachable state, not a current one.
- It does NOT claim `sessions.hpp` is the older file. Which one forked from
  which was not determined, and it does not change the analysis.
- It does NOT claim the three missing members are the only differences. Member
  NAMES were compared. Default values, alignment and the `detail::` helpers
  behind two of the initialisers were not exhaustively diffed, so the layout
  difference is proven and its full extent is not.
- It does NOT propose a fix. See sec 7.

## 7. OPTIONS, NOT RULED

Recorded so the ruling is a choice between named alternatives rather than a
reflex.

1. **DELETE the file.** Nothing includes it; the tree loses nothing. Cheapest
   and most complete. Requires confirming no out-of-tree consumer (the GUI's
   own include paths, generated code, any sibling project under `D:\dev`).
2. **NEUTRALISE it in place** -- replace the contents with a `#error` or an
   `#include "cli/settings.hpp"` plus a comment saying where the real one
   lives. Keeps the path resolvable for anything that reaches for it by name
   and makes the mistake loud instead of silent. Costs a file that exists only
   to say it is not the file.
3. **Demote the metadata** -- set `status:` to something the tooling treats as
   dead, and rely on that. WEAKEST: it fixes the signpost and leaves the
   hazard, and a `#include` does not read the header block.

Option 3 is listed to be rejected explicitly, because it is the one that feels
like housekeeping and changes nothing about the failure mode.

`include/**` is engine and wants an explicit go regardless of which is chosen.

## 8. HOW TO VERIFY, AND WHY THERE IS NO RUNTIME ARM

Verify the finding:

    git grep -l "sessions\.hpp" -- "*.cpp" "*.hpp"      # expect: nothing
    git ls-files --error-unmatch include/sessions.hpp   # expect: tracked
    git check-ignore -v include/sessions.hpp            # expect: no rule
    grep -n "struct Settings" include/sessions.hpp include/cli/settings.hpp

**There is deliberately no runtime arm and there should not be one.** Producing
the failure requires adding the `#include` to a translation unit -- that is,
committing the defect in order to demonstrate it, in a shared worktree, for a
bug whose signature is silence. The source evidence is complete and the
mechanism is a language rule, not a behaviour to be discovered.

If a demonstration is ever wanted, it belongs in a scratch program outside this
tree, not in a spec.

## 9. GOOD NEIGHBOUR

- **What changed:** nothing executable. This document only. Neither header was
  modified.
- **Whose area:** `include/**` -- engine. No go was sought because none was
  needed to WRITE a finding; a fix under any option in sec 7 needs one.
- **Authorization:** AIF-143 claimed and verified in the ledger before the
  number appeared anywhere.
- **How to verify:** sec 8, four read-only commands.
- **How to undo:** delete this file and release AIF-143 with
  `session_coordinator.py release-aif --number 143 --run COWORK-20260827-001`.
