# DOCFLUSH-20260901-002 -- Gate 0.5, contract coverage

    run       : DOCFLUSH-20260901-002 (v8)
    baseline  : 45f699a23  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    posture   : one source edit, named below. Everything else is measurement.
    motto     : normalize -- smooth -- improve

    GATE STATE: CLEARED on its own terms. See "The FAIL that is not this gate's".

## Run order, as the cookbook writes it

`stack_audit_v1.py` first, before any hand analysis. That ordering was added to
the cookbook by v7 after v7 hand-derived three of its outputs and got two wrong.
v8 ran it first and did no hand analysis of the contract surface at all.

## 1. The authority -- `stack_audit_v1.py` at 45f699a23

    tracked source      : 1080
    FAIL / WARN         : 0 / 22
    baseline            : CHANGED (WARN 18 -> 22)

      BANNER_CENSUS 2   CONTRACT_QA 7   CSV_VS_TABLE 1   DEAD_REG 2
      DOTREF_COV 2      EXPECTATION 1   REG_POLICY 3     SRCFILE_DRIFT 2
      SUBCMD_COV 2

**Zero FAIL.** The 22 WARNs are the standing contract debt, and the delta against
its own stored baseline is the real contract state -- already tracked by the tool,
requiring no second instrument. New since the tool's baseline and worth naming:

    SUBCMD_COV/USAGE_TEXT_DRIFT  SET RECURSION dispatches but is absent from
                                 MessageId::SetUsageText -- it works and cannot be
                                 discovered from the product. The tool's own note
                                 is the useful part: the localization cost is
                                 PROSPECTIVE (SetUsageText is en-US only today),
                                 so the gap exists ONCE now and multiplies the
                                 first time it is translated. That is an argument
                                 for generating the string before the locale spine
                                 reaches it, not after.
    SUBCMD_COV/TABLE_DRIFT       RECURSION has no live SYSSUBCMD row; the table
                                 has not been reseeded from the contracts
                                 (generate_syssubcmd.py).
    EXPECTATION/STALE_EXPECTATION AIF-067 expected an UNCOLLECTED match on
                                 src/cli/cmd_area51.cpp and it no longer occurs.
                                 Either it was resolved -- delete the EXPECTED
                                 entry, and if it was the planted fixture, record
                                 the catch -- or the check stopped looking. This is
                                 the AIF-118 shape and the tool says so.

Carried, unchanged, and NOT re-derived here: `DEAD_REG/MULTIWORD_KEY` (five keys,
AIF-134, ruling open), `DOTREF_COV/SUBCOMMAND_ONLY` (four entries),
`REG_POLICY` (nine split registrations, two wrapper asymmetries, one in-hub
duplicate), `CONTRACT_QA/MENTION_ONLY` (27 files), `CSV_VS_TABLE/STALE_CSV`
(SYSCMD table=212 csv=203).

**`BANNER_CENSUS/DERIVED_ONLY` still governs how the next section is read.**
1023/1079 banners carry zero authored fields. Coverage measures banner PRESENCE.

## 2. E3 -- coverage closed, and closed with content

v7 measured `uncovered=1` and left it. v8 closed it, because the cookbook's Phase
0.5 says in its first line that every source file carries `@dottalk.file`, and a
file without one is invisible to the doc pass rather than merely undocumented.

    include/dottalk/scratch_sidecar.hpp    banner added

Authored, not backfilled. `owns:` names what the header actually owns (the
`__fldtmp` / `__fldbak` convention and the exclusion predicate) and `lane:`
carries AIF-133, read from the commit that introduced the file (`892245854`), not
guessed. `DERIVED_ONLY` is at 94.8% precisely because the default is to add an
empty one; adding a 1080th empty banner would have raised a number that measures
nothing.

    AFTER, measured:
      source_census : total 1080  census 1080  commands 231  uncovered 0
      coverage      : 100.0%
      preflight 1   : 100.0% (uncovered=0)
      preflight 1b  : file_missing=0  usage_missing=1  unregistered=1  helpers=10

`file_missing` 1 -> 0. **E3 PASS.** The authority agrees: re-running
`stack_audit_v1.py` after the edit shows `BANNER_CENSUS/UNCOVERED` gone and
`FAIL / WARN` at **0 / 21**, down from 0 / 22. Still zero FAIL.

The residual `usage_missing=1` / `unregistered=1` is advisory debt, and
`helpers=10` is the `layer: helper` exemption v7 measured and ruled legitimate --
whose spelling is AIF-129's to settle, not this lane's.

**And the banner did NOT clear the file from `SRCFILE_DRIFT/UNCOLLECTED`.** That
is correct behaviour and worth stating, because it is the distinction this whole
lane turns on: the contract now exists in SOURCE, and the SRCFILE table has not
COLLECTED it. Source defines; the table organizes what was collected from source.
Sixty tracked files sit in that gap and this one joined them. A run that measured
only `source_census` would call this closed and be wrong about the far bank.

**CORRECTED after Phase 4 ran.** The paragraph above originally ended "until
Phase 4 runs", asserting that the HELP rebuild would collect it. **It did not,
and could not.** Measured after the host's `CMDHELP BUILD LEGACY` +
`CMDHELP BUILD . <src>` on 2026-09-01 17:03: `SRCFILE_DRIFT/UNCOLLECTED` is still
60 and still names this file.

The reason is that they are different tables with different builders:

    dottalkpp/data/help/          CMDHELP BUILD          <- Phase 4
    dottalkpp/data/comments/      tools/comments/        <- the comments lane
      SRCFILE.dbf                 reharvest_source_comment_catalog.py

`CMDHELP BUILD` never writes `SRCFILE.dbf`. Clearing that drift is the comments
harvest, which is its own stage ("comments evidence" in the eleven-stage model,
`comments_audit/` and `comments_promotion_phase/` in the July run) and is not
reached by any command in the cookbook's Phase 4 block.

Recorded as a correction rather than edited away, because the wrong version was
the plausible one: two tables both derived from source, both called "collected",
one rebuilt in front of me. Assuming a rebuild covers a table it does not own is
the same error in a smaller frame as assuming a PASS carries forward.

## 3. The FAIL that is not this gate's

`docpush_preflight.py` exits 2. One of its two reasons is now gone; the other is
Phase 4's:

    source_census            CLEARED by the banner above
    help_build_order_check   FAIL -- and it is a BUILD-ORDER fact, not a contract fact

      store  2026-08-26 05:09:48  predates exe 2026-09-01 11:22:29
      LEGACY 2026-08-28 20:55:43  is 63h45m NEWER than the store

The store is a half-run: LEGACY was rebuilt on 08-28 and the current store was
not. No contract edit can clear this and no sandbox action can either -- it is
cleared by Phase 4 running `CMDHELP BUILD LEGACY` then `CMDHELP BUILD . <src>` on
the host, in that order, after a backup.

**Consequence for every HELP number in this run, stated once and inherited by
every later gate:** the store is 165+ commits stale, so anything read out of it
is a fact about 2026-08-26, not about this baseline. v7 read HELP numbers off this
same store without labelling them.

## 4. Two instruments disagree about whether the build is needed

Not a defect found by hand -- it is what the two tools printed side by side.

    docpush_preflight.py            FAIL  store predates exe -> build required
    prepare_help_refresh_package.py current_help_build_required: false
                                    legacy_build_trigger: REVIEW_REQUIRED
                                    "DOTREF is not currently dirty; timestamps
                                     alone do not prove whether it diverged"

They are asking different questions -- "did the help SOURCE inputs change" versus
"is the store older than the binary" -- and both are proxies for "is the store
stale". The preflight's is the stricter one and it is the one that gates.

Recorded, not resolved. It is the lane's own failure signature (one fact, two
places) and it belongs to whoever rules on `dotref_autogen.py`, since a generated
dotref makes the dirtiness question mechanical rather than inferred.

## 5. Catalog check -- not run here

    command_catalog_sync.py check   ->  "Python 3.12+ required"

The sandbox carries 3.10 only. This is a routing fact, not a finding, and it goes
in the host package with the rest. E6 is on HOLD regardless: the site tree's
branch relationship is unruled.
