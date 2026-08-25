# AIF-126 -- FINDING: 2,757 HELP_LINE rows carry no topic key, and the store has
# been reporting it in plain sight since at least 2026-08-05

    Run      : COWORK-20260824-001 (member.ai.claude.cowork), for member.derald
    Claimed  : coordination/aif/AIF-126.claim
    Evidence : direct DBF reads of dottalkpp/data/help and five backup stores,
               plus fullstack_post_refresh_runtime_v2_20260824.txt
    Tier     : MEASURED. Every number below is a row count off a live table,
               not a transcript summary and not an inference.
    Status   : **review-needed.** The author does not self-approve.
    NOT DONE : nothing was written, rebuilt, or repaired. Read-only throughout.
               `src/cli/cmdhelp.cpp` and the help DBFs belong to a CONCURRENT
               session; this run only read them.

---

## 1. The one-line finding

**`SHARED_MSG` is 2,637 HELP_LINE rows with a blank `TOPICKEY`. Every row. No
topic reaches any of them.** Add the 120 blank-key rows of `MINER:SOURCE` and
the store holds **2,757 unreachable lines -- 9.4% of 29,206.**

Their headers are not missing. All 139 of them sit in `HELP_TOPIC` with correct
`SECTIONS` and `LINES` counters. It is the line side of the join that is blank.

## 2. The store has been saying so out loud

This line is in `CMDHELP SOURCE` in every capture this lane has taken:

    SHARED_MSG  [lines=2637, topics=0]

A bucket with two thousand six hundred lines and **zero topics**. It is printed
next to seven buckets that all report a positive topic count. It was in the
2026-08-13 baseline, in the 2026-08-21 capture, and in the 2026-08-24 capture.
Three of my own validation records quote the table it appears in. I read past it
three times because I was reading the number I came for.

The instrument was never missing. Nobody asked it the question it was answering.

## 3. How it was found, and what the wrong answers looked like on the way

I twice mis-explained the same gap before measuring it:

    reported by CMDHELP TOPICS ....... 526
    rows in HELP_TOPIC.dbf ........... 665
    difference ....................... 139

- **First answer (2026-08-24, wrong): "a units error."** Row count versus
  engine-reported topic count, two different things, move on. That is a
  dismissal wearing the clothes of an explanation. It named no mechanism and
  predicted nothing.
- **Second answer (this run, wrong): "139 stale rows from an older key
  grammar, fossils no rebuild deletes."** Better -- it had a mechanism -- but it
  was built on the assumption that `print_current_help_topics` reads
  `HELP_TOPIC`. It reads `HELP_LINE` (`cmdhelp.cpp:1157`,
  `load_help_line_table`). One `sed` of the actual function killed it.
- **Third answer (measured, and it reconciles to the row):** the 139 headers are
  real and current; their lines are real and present; the key that joins them is
  blank on the line side.

The reconciliation is exact, which is why I believe this one:

    HELP_TOPIC no-pipe rows, sum of LINES ... 2,574 (COMMAND:*) + 183 (SYSTEM) = 2,757
    HELP_LINE rows with blank TOPICKEY ..................................... 2,757

Two independently computed numbers off two tables, equal to the row. Neither of
the first two answers predicted anything at all.

## 4. The measurements

`HELP_LINE.dbf`, generation stamp 2026-08-24, 29,206 rows:

    distinct TOPICKEY, non-blank ..... 526   <- this is what "topics : 526" counts
    rows with blank TOPICKEY ......... 2,757
      by SOURCE : SHARED_MSG 2,637   SOURCE_MINER 120
      by CATALOG: SYSTEM     2,637   DOT          120
    SHARED_MSG rows with a key ....... 0 of 2,637

`HELP_TOPIC.dbf`, generation stamp 2026-08-24, 665 rows, 0 deleted:

    TOPICKEY containing '|' .......... 526   exactly the HELP_LINE key set
    TOPICKEY without '|' ............. 139   zero rows in HELP_LINE
      COMMAND:<name> ................. 130   CATALOG=SYSTEM, TOPICTYPE=TOPIC,
                                             STATUS=pending, CONFID=AUTHORITATIVE,
                                             TOPIC blank on all 130
      SUBSYSTEM:<name> ............... 8
      GLOBAL ......................... 1

Largest headers with no reachable lines:

    COMMAND:SET        24 sections  151 lines
    COMMAND:ABOUT      37 sections  138 lines
    COMMAND:MAINT       7 sections   79 lines
    COMMAND:DDICT      66 sections   76 lines
    MINER:SOURCE       40 sections  120 lines

`STATUS=pending` and `CONFID=AUTHORITATIVE` on the same row, 130 times: the
store simultaneously says this content is authoritative and says it is not
written yet.

## 5. It is not drift. It is frozen, across five rebuilds.

    store                        gen         TOPICrows  pipe  no-pipe  LINEkeys
    help.bak-20260805-125259     2026-08-05      664     525     139      525
    help.bak-20260813            2026-08-12      666     527     139      527
    help.bak-20260821-100525     2026-08-12      666     527     139      527
    help.bak-20260821-101225     2026-08-12      666     527     139      527
    help.bak-v5                  2026-08-12      666     527     139      527
    help.bak-20260824-172457     2026-08-24      665     526     139      526
    help  (live)                 2026-08-24      665     526     139      526

The pipe column tracks `LINEkeys` exactly in all seven stores -- that half of the
table is regenerated and correct. The no-pipe column is **139 in every one of
them**, through three months and at least five full rebuilds. This is not a
race, not a partial write, and not a stale backup. It is a reproducible property
of the export.

## 6. Why nothing looked broken

`print_current_help_topics` (`cmdhelp.cpp:1176-1180`) does:

    std::set<std::string> topics;
    for (const auto& r : tbl.rows) {
        const std::string topic = dbf_cell(r, ix_topic_key);
        if (!topic.empty()) topics.insert(topic);
    }

The guard is right. Given a blank key there is nothing else it could do. It
drops 2,757 rows in silence because silence is the only thing an empty key can
be turned into. **This is R6: absent is not distinguishable from present.** The
2,757 rows are present in the table and absent from every surface, and no count
anywhere reports the difference -- except `topics=0`, which reports it perfectly
and reads like a formatting quirk.

`CMDHELPCHK` says `OK no structural issues found` over this store. It does not
check that a HELP_LINE row can name its topic.

## 7. What is NOT claimed

- **Not claimed: which writer leaves the key blank.** `SHARED_MSG` comes from
  the shared message table and `MINER:SOURCE` from the source miner; both reach
  `helpdata_export_dbf.cpp`. I did not read the writer and will not guess at it
  in a document that is otherwise measured.
- **Not claimed: that the 139 headers are correct.** Their counters reconcile to
  the blank-key rows, which is strong, but a per-topic attribution of which 2,757
  lines belong to which header has not been done and cannot be done from the
  line side while the key is blank.
- **Not claimed: that this is a regression.** It is at least as old as
  2026-08-05, which is as far back as the backups reach.
- **Not claimed: any fix.** No repair is proposed here. This is a finding.

## 8. What it costs -- CORRECTED 2026-08-25, my first statement was inflated

**What I first wrote, and why it was wrong.** I wrote that "nine percent of the
help store cannot be retrieved by any operator" and pointed at `COMMAND:SET`
(151 lines) and `COMMAND:ABOUT` (138) as "the two commands most likely to be
the first thing a new operator types." That reads as though a hundred and fifty
lines of SET *documentation* were missing. **They are not.** I wrote the
sentence before sampling a row, and the sample refutes it:

    STATUS | SET_MESSAGE_CATALOG_VALIDATION_GREEN_LAB | green
    STATUS | SET_MESSAGE_CATALOG_VALIDATION_STATUS_TE | Message catalog validation: {status}

That is the runtime MESSAGE CATALOG -- the strings the engine prints, carrying
`{placeholder}` substitution slots. `COMMAND:SET`'s 151 rows are 80 STATUS and
71 MESSAGE, and both kinds are excluded from rendering **on purpose**
(`cmdhelp.cpp:1705` drops STATUS as "validator material"; MESSAGE is not in
`render_kind_default`'s allow-list at all). Raw `{status}` templates in a help
page would be noise. The renderer is not a second bug.

**What actually holds up, measured after the fix:**

    owner-keyed rows ...... 2,757
    renderable ............ 530    ERROR 478, WARNING 32, HINT 19, DEPRECATION 1
    blocked by policy ..... 2,227  STATUS 1,098, MESSAGE 1,009, SOURCE_FACT 120
    topics with content ... 83 of 139

So the honest cost is **530 operator-facing rows -- every error, warning and
hint those 83 topics can emit -- unreachable by any means**, plus a broken join
that made 2,757 rows unaddressable in the data layer regardless of what the
renderer would have done with them. That is a real defect and worth fixing. It
is not nine percent of the operator's help.

**The distinction that makes it concrete.** `CMDHELP COMMAND:SET` renders
nothing even now, correctly -- its payload is all message-catalog templates.
`CMDHELP COMMAND:AUTODBF` renders 35 lines, and they are exactly what an
operator wants:

    ERROR
    -----
    Cannot open {path} for read.
    MAXCHAR must be between 1 and 254.
    line {line}: expected {expected} column(s), found {found}
    long text requires {bytes} bytes; AUTODBF does not auto-promote to memo yet
    target exists: {path}
    ... 30 more

Every failure AUTODBF can report, on one page, reachable by name. That is the
win, and it is smaller and sharper than the one I claimed.

**A new question this exposes, for a ruling.** 56 of the 139 owner topics have
ZERO renderable rows. They can never render anything, by design. That is
`topics=0` inverted -- a topic that exists and can never answer. They look like
`MSGMGR`'s surface rather than `CMDHELP`'s, and the boundary should be decided
before it calcifies.

## 9. Owed

1. Read `helpdata_export_dbf.cpp` and name the writer that omits the key.
2. Rule on the 139: repair the key, or delete the headers. They must not
   continue to claim `AUTHORITATIVE` content that nothing can reach.
3. `CMDHELPCHK` should fail, not pass, on a HELP_LINE row with a blank
   `TOPICKEY`. That check is one predicate and it would have caught this in
   August 2025 had it existed.
4. `topics=0` in a `CMDHELP SOURCE` bucket should be an error line, not a
   number in a column.

---

## Good Neighbor note

    WHAT CHANGED   : two new files -- coordination/aif/AIF-126.claim and this
                     finding. Nothing else. No source, no data, no store, no
                     rebuild, no git mutation.
    WHOSE AREA     : the HELP lane. `src/cli/cmdhelp.cpp` and
                     `dottalkpp/data/help/*` belong to a CONCURRENT session and
                     were READ ONLY here -- this run opened the DBFs for reading
                     and read the source at file:line. Nothing was written to
                     either.
    AUTHORIZATION  : the standing "Full-Stack SelfDoc push v5" request plus the
                     steward's instruction to triage and keep the pass moving
                     rather than stop on a blocked item. AIF-126 was allocated
                     by tools/coordination/next_aif.py, not chosen by hand.
    VERIFY OR UNDO : every figure re-derives from a read of
                     dottalkpp/data/help/HELP_LINE.dbf and HELP_TOPIC.dbf and
                     the six help.bak-* stores beside them; the method is a
                     plain DBF header/record walk, no engine needed. Undo is
                     deleting these two files.
