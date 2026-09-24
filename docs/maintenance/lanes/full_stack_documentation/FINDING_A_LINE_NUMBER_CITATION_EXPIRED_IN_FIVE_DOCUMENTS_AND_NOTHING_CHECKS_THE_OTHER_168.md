# Finding: a line-number citation expired in five documents, and nothing checks the other 168

    Found     : 2026-09-24, DOCFLUSH-20260924-001 Gate 5, while confirming that
                the candidate CSVs really are ignored.
    Evidence  : runtime-proven (git, two revisions of `.gitignore`) for the one
                citation; source-evidenced (a text scan) for the population.
    Lane      : full_stack_documentation / AIF-068.
    Status    : the five sites are FIXED. The class is OPEN.

## The one that expired

Five documents in this lane cite the candidate-CSV ignore rule as
`.gitignore:342`. It was true when written and is false now:

    .gitignore at ad34e9145  (2026-08-26)   360 lines   rule at line 342
    .gitignore at HEAD       (2026-09-24)   573 lines   rule at line 545

**Nothing was edited near the rule.** The file grew by 213 lines in 29 days, 203
of them above the rule, which carried it from 342 to 545. The rule itself is
byte-for-byte unchanged:

    docs/maintenance/lanes/**/runs/**/*.csv

The failure mode is the bad kind. Line 342 today is not empty and not an error
-- it is a comment about where WRITEBACK puts observed payloads. A reader who
follows the citation lands on plausible prose about a different subject and has
no signal that they were sent to the wrong place. **A citation that resolves to
something wrong is worse than one that resolves to nothing.**

The five sites are corrected to quote the rule TEXT, which is greppable, unique,
and does not move.

## The class, measured

    lane .md documents scanned          333
    distinct `path:line` citations      168, across 49 documents
    distinct files cited                 91

The most-cited targets are the files that change most:

    src/cli/shell_commands.cpp   22 citations  (16 + 6 by bare name)
    CMakeLists.txt               14
    cmdhelp.cpp                  17 (13 + 4 with path)
    metacollect.cpp              10

**This is not a claim that 168 citations are stale.** It is the population at
risk, in one lane, and no gate in the suite looks at any of them. The one case
audited was 100% wrong after 29 days, which is a sample of one and is reported
as such.

## Why the drift gate cannot see it

The citation gate checks that a cited PATH exists. `check_cited_paths.py`'s
`cited()` matches the path with `PATH_RE` and strips trailing punctuation; the
`:342` never enters the set it returns. A path with a stale line number still
exists, so the check passes -- the same shape as the proxy family in the recipe book's Part 8a:
the check answers "does the file exist", the reader believes it answered "does
the citation point at the right thing".

## Rule, for anything written after today

**Cite text, not coordinates, when the text is unique.** A grep-able quotation
of the rule, the function signature, or the message string survives every edit
above it. Reserve `path:line` for the case where there is nothing quotable, and
when using it, quote the line as well so the citation carries its own check:

    metacollect.cpp:1087  `arg_id = "ARG_" + command + "_" + arg_name`

That form self-repairs: if the line moved, the quoted text still finds it.

## Cheap instrument, if the class is worth closing

For each `path:line` citation, compare the cited file's last-commit time with
the citing document's. A cited file committed AFTER the document that cites it
is a citation nobody has re-verified. That is not proof of staleness, but it is
the right worklist, and it costs one `git log -1` per distinct file. It is the
same trick `program_freshness_check.py` uses for binaries, applied to prose.

## Verify

    git show ad34e9145:.gitignore | grep -n "runs/\*\*/\*.csv"    ->  342
    grep -n "runs/\*\*/\*.csv" .gitignore                          ->  545
    sed -n '342p' .gitignore                                       ->  a WRITEBACK comment
