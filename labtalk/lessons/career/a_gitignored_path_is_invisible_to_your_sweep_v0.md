# A Gitignored Path Is Invisible to Your Sweep

Lane: career. Status: draft. Observed 2026-08-07 during the PLDC -> PDLC
vocabulary merge (`docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`,
commits `c0d3069c5` and `018bd0c9f`).

## The claim that was wrong

A tree-wide sweep replaced the retired acronym `PLDC` with `PDLC` across both
repositories. The session then reported, several times and with counts attached,
that **zero PLDC remained**. Every one of those reports was measured. Every one
of them was also scoped to a subset of the tree, and the report did not say so.

An independent session (AIF-092), asked by the maintainer to verify rather than
accept the report, found a live miss within minutes:
`docs/ai-friendly/gptbase_bundle_v1/05_process_and_roles.md` still carried a
dangling path to a renamed file, plus a whole section heading built on the
retired term.

## The mechanism

The sweep used ripgrep. **Ripgrep honors `.gitignore` by default.** Two entries
hid the misses:

```
.gitignore:323   docs/**/backups/
.gitignore:346   docs/ai-friendly/gptbase_bundle_v1/
```

Verify the mechanism yourself rather than trusting this file:

```
git check-ignore -v docs/ai-friendly/gptbase_bundle_v1/05_process_and_roles.md
rg --no-ignore <term> | wc -l      # compare against
rg <term> | wc -l
```

Nothing was broken, misconfigured, or unusual. The tool did exactly what it
documents. The defect was entirely in the claim built on top of it.

## Why it was not caught internally

The edit and the verification used the same tool. A verification that shares a
search path with the change it is checking cannot detect a scope error in that
path -- it will confirm, correctly and repeatedly, that the region it can see is
clean. Confidence rose with each pass while coverage never moved.

This is the part worth carrying: **the number of times a check passes says
nothing about what the check can see.** Only a differently-scoped check, or a
different agent, moves that.

## Gitignored does not mean unimportant

The reflex is to treat ignored paths as build residue. Here the opposite held.
`gptbase_bundle_v1/` is a bundle **packaged for an outside model** -- an agent
with no repository, no history, and no way to ask what the retired acronym meant.
The highest-stakes reader was sitting in the lowest-visibility directory. A
broken pointer there fails the reader least able to recover from it.

## Where the rule does NOT apply

`docs/manuals/developer/manualgen/backups/**` holds 23 files that still contain
`PLDC`. They were left alone deliberately. They are dated escrow snapshots, and
rewriting a preservation record to match current vocabulary would falsify it.

"Find everything" and "change everything you find" are separate decisions.
Widening the search does not license widening the edit. The sweep must reach
ignored paths; the edit must then stop at the ones that are records rather than
documents.

## The rule

1. Any tree-wide vocabulary, acronym, or path-rename sweep runs with
   `rg --no-ignore` (or enumerates the ignored directories explicitly). A sweep
   that has not done this is not tree-wide, whatever its counts say.
2. Report the scope alongside the count. "Zero remaining" is a different claim
   from "zero remaining in tracked, non-ignored files", and only the second one
   was ever measured.
3. Arrange for the verification to be scoped differently from the change, or
   performed by a different agent. Same-tool verification inherits the tool's
   blind spots and converts them into confidence.
4. Having found matches in ignored paths, classify before editing: documents get
   corrected, escrow and preservation records get left, generated artifacts get
   regenerated from their source rather than hand-patched.

## Companion

Sibling to `lesson.career.a_script_never_run_is_not_evidence` (2026-07-26).
There, absent evidence looked real. Here, absent scope looked complete. Both
produce confident records that are wrong in a direction nobody is checking.
