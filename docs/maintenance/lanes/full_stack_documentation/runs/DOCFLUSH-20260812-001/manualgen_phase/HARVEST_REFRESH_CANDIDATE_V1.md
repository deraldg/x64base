# The harvest refresh, built and measured -- promotion still the owner's

    Run    : DOCFLUSH-20260812-001 (flush v5), Phase 6 / manualgen
    Lane   : **AIF-068 `manualgen-harvest-feeder`**. No new AIF.
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : review-needed. **The candidate is built. NOTHING was promoted.**

---

## 1. What was done, and why it is not the gated action

`MANUALGEN_HELP_META_HARVEST_INPUT_CONTRACT_V1.md` separates two things that are
easy to conflate:

- **Selecting a harvest** for a run, via `--harvest-workspace <dir>`. Any valid
  14-file workspace may be selected. Not gated.
- **Replacing `docs/manuals/developer/manualgen/harvested/`.** Named explicitly
  in the contract's authority boundary as a separately authorized gate.

**Only the first was done.** A fresh candidate workspace now exists at

    .../runs/DOCFLUSH-20260812-001/manualgen_phase/harvest_candidate_20260825/

built by `tools/fullstack_docs/export_help_meta_harvest.py` -- **prior art, not a
new tool.** It already existed, is owned by member.derald, is read-only over the
source DBFs, writes only into `--out`, and says in its own header that it does
not touch the canonical snapshot. Finding it first is the whole lesson of the
duplicate `docpush_preflight.py`.

The comparison is `tools/fullstack_docs/compare_help_meta_harvest.py`, also
prior art. Its own output records `promotion_performed: 0`.

## 2. The candidate

    14 tables, 62,538 rows, plus HELP_META_EXPORT_MANIFEST_v0.csv

    HELP_COMMANDS          460     META_SYSARGS       249
    HELP_CMD_ARGS        2,358     META_SYSCMD        212
    HELP_HELP_ARTIFACTS 14,595     META_SYSSUBCMD      31
    HELP_HELP_LINE      29,262     META_SYSFUNC        75
    HELP_HELP_SECTION   14,595     META_SYSFLDDIC      16
    HELP_HELP_TOPIC        665     META_SYSENTVAR      12
                                   META_SYSHELP         8
                                   META_SYSMSG          0

**This read is only possible because AIF-127 was fixed earlier today.** The
exporter goes through `dbfread`, and eight of the fourteen sources are x64.

## 3. The delta against the canonical May harvest

    required files        14        missing            0
    unchanged              1        header changed     2
    compatible content    11        promotion          0
    rows          21,979 -> 62,538   (+40,559, +185%)

### 3a. The two header changes are PURELY ADDITIVE

    META_SYSARGS   13 -> 15 columns   ADDED: DEF_LOCALE, REGION_ID   REMOVED: none
    META_SYSFUNC   19 -> 21 columns   ADDED: DEF_LOCALE, REGION_ID   REMOVED: none

**Nothing was removed and the existing column order is preserved in both.** The
same two columns appear in both tables, which reads as one coordinated
locale/region addition rather than two drifts -- consistent with AIF-066's
locale spine. A consumer that reads columns BY NAME is unaffected; one that
reads by position is not, and that distinction should be checked before
promotion rather than assumed.

### 3b. Two authorities that were empty are now populated, and the emptiness was SANCTIONED

Three of the fourteen canonical files are header-only:

    META_SYSARGS.csv    0 rows  ->  249
    META_SYSFUNC.csv    0 rows  ->   75
    META_SYSMSG.csv     0 rows  ->    0   (still empty, correctly)

**This is not a defect that was hiding.** The contract says so in as many words:

    Zero rows remain valid for META_SYSARGS, META_SYSFUNC, and META_SYSMSG;
    their semantics belong to the separate metadata-contract mission and must
    not be fabricated to satisfy a count.

So the manual has been assembled against an empty function authority BY
PERMISSION, not by accident. What changed is that two of the three no longer
need the permission. **`META_SYSMSG` stays legitimately empty**: the source
table is a 1,020-byte header-only shell, superseded on 2026-07-27 -- the same
supersession recorded by `SYSMSG.SUPERSEDED_20260727.txt`.

Stating this carefully because the tempting version -- "the manual was built
against an empty authority" -- is true and misleading in the same breath.

### 3c. Where the row growth is

    HELP_HELP_LINE        8,094 -> 29,262   +21,168
    HELP_HELP_ARTIFACTS   5,428 -> 14,595    +9,167
    HELP_HELP_SECTION     5,428 -> 14,595    +9,167
    HELP_HELP_TOPIC         474 ->    665      +191
    HELP_COMMANDS           403 ->    460       +57

The topic growth includes the **+139 owner topics recovered by AIF-126**, whose
2,757 blank-key HELP_LINE rows had no reachable owner until yesterday.

## 4. What promotion would and would not do

**Would:** close the 34-command re-harvest debt measured in
`PHASE6_REHARVEST_DEBT_V1.md`, and retire the three stale renames
(`SETNEAR`->`SET NEAR`, `SIMPLEBROWSE`->`SIMPLEBROWSER`,
`SMARTBROWSE`->`SMARTBROWSER`).

**Would NOT:** write a single line of manual prose. The contract is explicit --

    A passing assembly dry run still proves which evidence was selected, not
    that every changed row appears in the existing 25 sections.

and the 21 written-debt commands in section 3a of the debt document are
untouched by any harvest.

## 5. What was NOT done

- **`harvested/` was not replaced, moved, or written to.** Verify: its files
  still carry their May hashes, recorded in the comparison output.
- No manualgen run was executed against the candidate. Selecting it with
  `--harvest-workspace` is the next step and is a separate decision.
- No prose, no pointer, no publication, no accepted catalog touched.
- The candidate is **untracked** and sits under the run directory. It is
  evidence, not a promotion.

## 6. Good Neighbour

    What changed      : one new candidate workspace (15 files) and its
                        comparison output, both under this run's directory, plus
                        this record. The canonical harvest is byte-identical.
    Whose area        : reports into AIF-068. Both tools used are prior art
                        owned by member.derald and were run, not modified. The
                        HELP store belongs to a concurrent session and was read
                        through the shared reader only.
    What authorization: flush v5 Phase 6; the contract's own distinction between
                        selecting a harvest and replacing one.
    How to verify     : `compare_help_meta_harvest.py --baseline
                        docs/manuals/developer/manualgen/harvested --candidate
                        <this dir>` reproduces 14/11/1/2/0 and
                        `promotion_performed: 0`.
    How to undo       : delete the candidate directory. Nothing else moved.
