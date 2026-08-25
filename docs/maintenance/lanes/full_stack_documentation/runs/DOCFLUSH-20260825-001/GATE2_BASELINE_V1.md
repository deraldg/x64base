# v6 Gate 2 -- baseline captured, with the store's own generation stamp

    Run      : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Captured : 2026-08-25, immediately after the Gate 0 store rebuild
    Store    : dottalkpp/data/help, built by exe 2026-08-25 10:57:03
    Preflight: PASS (Gate 0 green; two WARNs carried, see section 4)
    Status   : review-needed

## 1. Generation stamps, read from the DBF headers rather than the filesystem

      CMD_ARGS.dbf               2026-08-25   (year byte 26)
      COMMANDS.dbf               2026-08-25   (year byte 26)
      HELP_ARTIFACTS.dbf         2026-08-25   (year byte 26)
      HELP_ARTIFACT_LOCALE.dbf   2026-06-11   (year byte 126)
      HELP_LINE.dbf              2026-08-25   (year byte 26)
      HELP_LINE_LOCALE.dbf       2026-06-11   (year byte 126)
      HELP_SECTION.dbf           2026-08-25   (year byte 26)
      HELP_SECTION_LOCALE.dbf    2026-06-11   (year byte 126)
      HELP_TOPIC.dbf             2026-08-25   (year byte 26)
      HELP_TOPIC_LOCALE.dbf      2026-06-11   (year byte 126)

    by KIND
      ALIAS                 53
      ARGUMENT             495
      DEPRECATION            1
      ERROR                478
      EXAMPLE             1078
      HINT                  19
      MESSAGE             1009
      NOTE                3743
      RELATED             1980
      SOURCE_FACT         4302
      STATUS              1559
      SUMMARY             2390
      SYNTAX              6082
      USAGE               6031
      WARNING               45
    by SOURCE
      CURATED_DOC          868
      DOTREF              1004
      EDREF                786
      FOXREF               667
      REGISTRY             461
      SHARED_MSG          2637
      SOURCE_MINER        7644
      USAGE_CONTRACT     15198

## 2. The topic SET, not a topic count

    HELP_TOPIC rows   : 666
    distinct TOPICKEY : 666       (no duplicate keys, no blank keys)
    the SET itself is not stored here -- it is derived in one pass from
    HELP_TOPIC.TOPICKEY, so a stored copy could only go stale

Gate 4 assertion 6' compares this SET against the post-run store. It replaces
the topic-count FLOOR, which on 2026-08-24 scored a REPAIR as a regression when
five expression functions correctly stopped being invented as commands and the
total fell 530 -> 526.

**And the count is blind in the other direction too, measured this run.** The
`include/dotref.hpp` repair committed in `c8aa6a583` changed two rows from
`supported=no` with a placeholder to `supported=yes` with a real summary, and
the row count was 461 before and 461 after. A count cannot see a substitution.
Both directions now have a recorded incident; the SET diff sees both.

## 3. Cross-checked against an independent build

The same source was built in a Linux container (g++ 13, DEVELOPMENT + LMDB) and
its store compared row-for-row against the Windows MSVC store:

    line rows      29265  =  29265
    topics           666  =  666
    usage contracts 3503 from 207 files  =  3503 from 207 files
    previews shortened  65  =  65
    DOTREF 1004, FOXREF 667, EDREF 786, REGISTRY 461, CURATED_DOC 868,
    SHARED_MSG 2637, SOURCE_MINER 7644, USAGE_CONTRACT 15198  -- all identical

Two independent toolchains producing an identical store is a stronger baseline
than one store measured twice. **It took two attempts to get there, and the
first attempt is the more useful record:** the container's first store differed
by exactly 2 DOTREF rows, because its binary had been rebuilt for an A/B and the
catalog header restored afterwards WITHOUT recompiling. An exe older than its
own catalog -- the exact defect Gate 0 check 2 exists to catch, reproduced in
the rehearsal rig on the same day. The container has no preflight wired to it.
Cheapest guard, and it is already prescribed by the sandbox handoff:

    grep -c '<a string only your change introduces>' <the binary>

## 4. Carried forward, deliberately not fixed here

- **`binding` WARN, 46 tracked files modified at `c8aa6a583`.** Cannot reach
  zero and must be EXPLAINED, not fixed: most are not this lane's and some are
  ten days old. Any store built from this tree is runtime-proven against a
  WORKTREE, never against HEAD.
- **`status coherence` WARN, 167 rows `STATUS=pending` and
  `CONFID=AUTHORITATIVE` at once.** AIF-126 open item, unchanged by this run.
- **The banner cannot support Gate 4 assertion 1'.** `CMakeLists.txt:59` reads
  git inside `execute_process`, which runs at CONFIGURE time, so `cmake --build`
  never refreshes it. The banner reads `c39d966c dirty` for a binary that
  provably contains `c8aa6a583`. Worse in the other direction: configure clean,
  then edit and build, and it reports clean while carrying uncommitted code --
  a false green on the assertion adopted to catch exactly that. **1' is not
  usable until the stamp is a build-time step.** v7.
- **Two year encodings in one store.** The HELP tables stamp the year byte as
  `26` (year mod 100); the four `*_LOCALE` tables stamp `126` (years since
  1900). Both decode to 2026 only if the reader handles both. Consistent with
  AIF-126's finding that the exporter hand-rolls its own DBF writer instead of
  using the engine's -- the writer, not the format, is the divergence. v7.
- **Usage contracts moved 3499 -> 3503 across the same 207 files** since the
  v5 capture of 2026-08-21. Four rows, unattributed. Noted, not chased. v7.
- **LEGACY arg rows differ by build location** -- container 2609, host 2363 --
  which points at `./src` in the switch miner resolving against the process
  working directory rather than the source root. `datarun.ps1` runs from
  `dottalkpp/`. Noted, not chased. v7.

## Good Neighbor

    What changed  : one new document in this run's own directory, plus a
                    scratch topic-set file under the gitignored tmp/. No source,
                    no data, no store, no rebuild.
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
    Authorization : the owner's instruction of 2026-08-25 to keep going through
                    the phases and note minor items for v7 rather than stopping.
    Verify        : $py12 tools\fullstack_docs\docpush_preflight.py --root .
                    expect PREFLIGHT PASS with the two WARNs named in section 4.
    Undo          : delete this document; it asserts nothing the store does not.
