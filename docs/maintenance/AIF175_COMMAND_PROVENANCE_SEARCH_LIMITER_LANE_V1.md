# AIF-175 -- the search limiter, as columns the store already wants

    Number  : AIF-175. CLAIMED 2026-11-26 (coordination/aif/AIF-175.claim,
              run CLAUDE-20261126-ONBOARDING-FIXES). Renumbered from AIF-174:
              next_aif.py allocated 174 to this draft on 2026-11-14, but the
              draft was never claimed, and member.ai.codex claimed AIF-174 for
              regression-process-groups-output on 2026-11-21. Second time this
              charter lost its number while untracked (see Replaces).
    Owner   : member.derald. Steward: member.ai.claude.cowork.
    Replaces: a charter written 2026-09-25 citing AIF-170, which member.ai.codex
              claimed for ddict-data-repair on 2026-10-12 while that charter sat
              UNTRACKED. The number is gone; the measurement stands; the DESIGN
              changed and section 3 says why.
    Found   : 2026-09-25, DOCFLUSH-20260924-001, owner instruction: "we want the
              family categorized as an alternate ai search limiter, by narrowing
              related files in projects instead of requiring large timed out
              greps in the ai sandbox -- remember the ai portal is for you! and
              other ai agents, so make it ai friendly", then "they should be in
              x64base files -- dogfooding".
    Status  : CANDIDATE. Generator written and run. No table created, no store
              mutated.
    Basis   : MEASURED on 2026-11-14 at eef247ce4. Every number is reproducible
              by the command beside it.

## 1. The problem, measured twice seven weeks apart

    the same question, "where is the COPY usage contract declared?"

    grep -rln 'COPY USAGE' --include=*.cpp --include=*.h .
        TIMED OUT at 120,000 ms            (2026-09-25, and again 2026-11-14)
    the same grep scoped to src/ by GUESSING
        4,612 ms -- 2 files, one a false positive (helpdata_messages.cpp)
    a lookup in this index
        sub-millisecond -- 1 file, exact line, no false positive

`PORTAL_SEARCH_MAP_V1.md` line 8 has recorded the timeout since 2026-08-08.
`tools/search/verified_search.py` (2026-09-24) stops a timeout being reported as
an absence. **This removes the scan instead of making it honest**, and the two are
complementary: one keeps a search from lying, the other keeps it from happening.

## 2. PRIOR ART, WALKED PROPERLY THIS TIME -- AND IT CHANGED THE DESIGN

Four phrasings through `--prior-art` ("ai search limiter topic file index",
"search limiter", "contract provenance index", "topic to source file map") all
PASS over 33 sources. The four AIF lanes opened since September were read, and
none of them is this: AIF-170 ddict data repair, AIF-171 guarded HELP refresh,
AIF-172 the ten-copy memo predicate, AIF-173 repeatable demos.

**THE REAL PRIOR ART IS INSIDE THE METADATA STORE, and the first charter missed
it because it never looked there.** Measured:

    SYSSUBCMD    31 rows   SRC_FILE populated 31 of 31   -> 'cmd_set.cpp'
    SYSCMD      212 rows   NO source field at all

So subcommands already have a pointer and it is a BASENAME -- no directory, no
line. Top-level commands have nothing. The store has been half-answering this
question all along.

## 3. THEREFORE: NO NEW TABLE. This feeds the columns that exist.

The 2026-09-25 charter proposed a new `SYSCMDSRC` table. **That was wrong**, and
not marginally: the tree already carries four answers to "what commands exist" --
`REGISTRY 247, SYSCMD 212, HELP(*ref) 325, command_catalog 28`, printed by
normcheck on every commit that stages a tool -- and a fifth metadata table keyed
on commands is a fifth authority however carefully its boundary paragraph is
worded.

The owner's own framing for the normalization work is the answer: **"which can
merge or feed."** This lane FEEDS.

    SYSCMD      gains SRC_FILE and SRC_LINE. It has HANDLER already, so it
                already points INTO source; it just cannot say where.
    SYSSUBCMD   SRC_FILE goes from basename to repo-relative path, and gains
                SRC_LINE. The field exists and is populated; this makes it
                usable without a search.

Both are schema changes to governed tables and therefore owner-ruled, which is
why M1 below is a decision and not a task.

## 4. What the generator produces, measured

    tools/fullstack_docs/build_command_provenance_index.py --src-root src \
      --out docs/maintenance/lanes/full_stack_documentation/COMMAND_PROVENANCE_INDEX_CANDIDATE_V1.csv
      source files walked 765   rows 277   topics 276   distinct files 224
      @dottalk.usage            227
      @dottalk.subusage          34
      @dottalk.usage.voluntary   16
      blocks with NO @dottalk.end: 262 of 277
      multiword owners carried intact: 45
      elapsed: ~7.4 s

**IT READS THE SOURCE TREE, AND THAT IS A CORRECTION TOO.** The first version read
the PROVENANCE lines of the gated `CONTRACT_*` family out of a dated `help.bak-*`
store. Measured 2026-11-14, that was wrong twice:

    THE SOURCE WAS EVAPORATING. Only two stores ever carried that family
    (help.bak-20260825: 9,514 rows; help.bak-20260901: 9,990). The three AIF-171
    backups taken in October carry ZERO, because the family was gated at
    helpdata_source_miner.cpp:1770 on 2026-09-13. Ten backup directories were
    pruned between those two September dates. The index's only source was two
    aging directories in a tree with a demonstrated pruning habit.

    AND IT WAS ALREADY STALE BOTH WAYS. 21 topics existed in source that the
    backup never had; 5 topics in the backup are gone from source (DOT|CANARY,
    DOT|ELSE, DOT|ERP, EDU|IDX removed; DOT|SET PATH was a parser bug, below).

The source tree is what a provenance line was a RECORDING of. Reading it directly
removes the backup dependency, is current by construction, and makes a separate
freshness gate unnecessary: regenerating IS the check.

**THE CANDIDATE LIVES IN THE LANE, NOT IN A STORE PATH.**
`docs/maintenance/lanes/full_stack_documentation/COMMAND_PROVENANCE_INDEX_CANDIDATE_V1.csv`.
The first draft put it under `dottalkpp/data/scripts/metadata/` beside
`SYSCMD_IMPORT_v1.csv`, which is a path reserved for reviewed CREATE/IMPORT
packages -- and after section 3 there is no table to create. A candidate filed in
a store's import path reads as authorized.

## 5. Three things the generator found about the tree

**34 SUBUSAGE SURFACES WERE INVISIBLE TO THE FIRST VERSION.** A
`@dottalk.subusage` block carries `parent:` and `sub:`, never `owner:`. The house
key is their join -- `SYSSUBCMD.QUAL_NAME` reads "SET ALTERNATE" -- and this tool
now composes it that way rather than inventing a second spelling. The other 16 of
the 50 marker occurrences are PROSE references inside comment text, which the
line-start anchor correctly skips.

**ELEVEN SURFACES ARE DECLARED TWICE, AND THE TREE SAYS WHICH ONE BINDS.**

    SET CASE  SET CDX  SET CNX  SET FILTER  SET INDEX  SET LMDB
    SET NEAR  SET ORDER  SET PATH  SET RELATION  SET UNIQUE

Each has a `DOT|SET X` block in its own file AND a `SET X` subusage block on the
ladder arm in `cmd_set.cpp`. That is not drift: `cmd_setpath_command.cpp` says so
outright -- "The binding identity for this surface is the @dottalk.subusage
contract on its ladder arm in src/cli/cmd_set.cpp." So the index carries both
pointers and the MARKER column tells a caller which is binding. A limiter that
hid one would be incomplete; one that flattened them would be wrong.

**THE END-MARKER RULE IS 93 PERCENT UNMET.** 262 of 277 blocks carry no
`@dottalk.end`; tree-wide the census is 22 end markers against 318 usage-family
markers. The owner's rule is that every `@dottalk` block should end with an
`@dottalk` marker. That gap is what lets the source miner absorb post-contract
design commentary (cmd_rel.cpp: 3 contract notes became 32). **This lane counts
it and does not fix it** -- the fix is a source lane of its own, and HAS_END is
emitted so that lane starts with a list instead of a sweep.

## 6. Two defects in the steward's own tool, recorded

    `(\S+)` TRUNCATED EVERY MULTIWORD OWNER. `// owner: DOT|SET PATH` became
    `DOT|SET`, which would have collapsed eleven distinct surfaces into one key.
    That is the lane's own recorded trap -- "multiword registry keys are dead on
    arrival" -- inside the tool written to route around traps. Owners are now
    captured to end of line, and 45 multiword keys survive.

    THE BACKUP SOURCE, section 4. Written as a dependency on an artifact that the
    same run's own Gate 7 closeout recorded as unreliable.

## 7. Milestones

    M0  DONE 2026-11-26: claimed as AIF-175 (the AIF-174 allocation was
        lost to an unclaimed draft, exactly the failure this step warned of).
    M1  OWNER RULING, and it is the whole lane: extend SYSCMD with SRC_FILE and
        SRC_LINE, and widen SYSSUBCMD.SRC_FILE to a repo-relative path plus
        SRC_LINE -- or reject both and keep the index as a portal-side artifact
        outside the store. Nothing else proceeds until this is answered, because
        every remaining step writes into a governed table.
    M2  If M1 is yes: a reviewed create/import package per the
        SYSCMD_NATIVE_CREATE_IMPORT convention, schema contract first, and
        verify the x64 long names survived the write (AIF-141: an over-ceiling
        name is DROPPED, not truncated -- the ceiling is 256 and the longest
        field here is 8, so this should be clean, and "should" is why it is
        checked).
    M3  One row in PORTAL_SEARCH_MAP_V1.md, per that map's own maintenance rule
        ("a scan you did not record is a scan the next agent repeats"). One row,
        not 277: the map is hand-curated and generated rows would swamp it.
    M4  Hand HAS_END to whoever owns the end-marker rule. 262 rows, named.

## 8. NOT CLAIMED

    that any schema change is authorized -- M1 is exactly that question
    that the index is complete: 276 topics against REGISTRY's 247 commands and
        SYSCMD's 212 is not a coverage ratio, it is three different populations,
        and reconciling them is the normalization lane's job and not this one's
    that a pointer is current beyond the run that generated it
    that the CONTRACT_* family should be re-enabled -- it should not
    that the two source-miner defects are fixed -- they are gated, not fixed
    that HAS_END measures contract quality -- it measures one marker's presence
