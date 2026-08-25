# AIF-126 -- the writer is found. One key, computed two ways, in one file.

    Run    : COWORK-20260824-001 (member.ai.claude.cowork), for member.derald
    Tier   : SOURCE-EVIDENCED at file:line, and corroborated by the live tables.
    Status : **review-needed. APPLIED and RUNTIME-PROVEN 2026-08-25** on the
             steward's explicit go ("Apply the one line now"). Built, store
             rebuilt, verified clean. NOT committed. See section 8.

---

## 1. The cause

`src/help/helpdata_export_dbf.cpp` builds three tables from one artifact list.
Two of them derive the topic key through a helper. The third assigns a raw field.

    line 291   static std::string topic_key_for(const Artifact& artifact)
               {
                   if (!artifact.cmdkey.empty())            return artifact.cmdkey;
                   if (!catalog.empty() && !command.empty()) return catalog + "|" + command;
                   if (!artifact.command.empty())            return artifact.command;
                   return owner_to_string(artifact.owner);          <-- the fallback
               }

    line 346   HELP_TOPIC    const std::string key = topic_key_for(artifact);
    line 419   HELP_SECTION  const std::string key = topic_key_for(artifact);
    line 630   HELP_LINE     row.topickey = artifact.cmdkey;        <-- raw field

For a shared message, `artifact_from_message` (`helpdata_artifacts.cpp:75-88`)
deliberately clears both identity fields and puts the identity in the owner:

    artifact.catalog = "SYSTEM";
    artifact.command.clear();
    artifact.cmdkey.clear();
    artifact.owner = owner_from_string(message.owner ? message.owner : "GLOBAL");

So for every shared message and every miner artifact:

    topic_key_for(a)  ->  owner_to_string(a.owner)   -- a real key
    a.cmdkey          ->  ""                         -- nothing

HELP_TOPIC and HELP_SECTION get the key. HELP_LINE gets the empty string. The
join breaks between two lines of the same function's neighbours.

## 2. It is not a guess -- the tables already show the answer

`owner_to_string` (`helpdata_model.cpp:36-49`) returns exactly four shapes:

    GLOBAL          COMMAND:<name>      SUBSYSTEM:<name>      MINER:<name>

Those are **exactly** the 139 orphan header keys measured in the live store:

    COMMAND:*      130        SUBSYSTEM:*      8
    GLOBAL           1        MINER:SOURCE     1

HELP_TOPIC is a written record of what `topic_key_for` returned for these
artifacts. So the fix's output is not predicted, it is already on disk: give
HELP_LINE the same expression and its 2,757 blank keys become those 139 keys.

This is **R5** -- one question ("what is this artifact's topic key?") with two
answers in one file -- and the defect is the second answer existing at all.

## 3. The patch

`src/help/helpdata_export_dbf.cpp`, line 630, inside
`append_line_rows_for_role`:

    -            row.topickey = artifact.cmdkey;
    +            row.topickey = topic_key_for(artifact);

`topic_key_for` is declared at 291, in the same translation unit, above the use.
Nothing else changes. Note the first branch of `topic_key_for` returns
`artifact.cmdkey` when it is non-empty, so **every row that has a key today
keeps the identical key**. The change can only fill blanks.

## 4. What it does to the store, and to behaviour

    HELP_LINE rows with a blank TOPICKEY .... 2,757 -> 0
    CMDHELP TOPICS ......................... 526 -> 665
    HELP_TOPIC headers with no lines ....... 139 -> 0
    rows whose key CHANGES ................. 0

Retrieval, traced through `resolve_topic_keys_from_lines`
(`cmdhelp.cpp:2173-2217`), for a query with no `|`:

- **Exact match is unaffected.** `topic_suffix("COMMAND:SET")` returns the whole
  key, `"COMMAND:SET"`, which does not equal `"SET"`; and these rows carry an
  empty `TOPIC`, so the `topicU == q` branch cannot fire either. `CMDHELP SET`
  still resolves `DOT|SET` exactly, and `exact` short-circuits before the
  fallback is consulted.
- **`CMDHELP COMMAND:SET` starts working.** Query has no `|`, `suffU` is the
  whole key, so it matches exactly. 151 lines that no operator could reach
  become reachable by name.
- **The SET-family canonical branch is unaffected** -- `"COMMAND:SET INDEX"`
  does not equal `"SET INDEX"`.
- **One real behaviour change, named:** the substring fallback. `suffU.find(q)`
  now also searches these keys, so a query with NO exact match anywhere can
  surface a `COMMAND:*` topic it would previously have missed. That fallback
  only runs when `exact` is empty, so it cannot displace an existing answer --
  it can only add a result where there was none. I read this as the point of the
  fix rather than a cost of it, but it is a change and it is the steward's to
  weigh, not mine to wave through.

## 5. What this does NOT settle

- **Whether `COMMAND:SET` is the right key.** It is the key the store already
  believes in, and making one table agree with two others is the smallest
  correct change. Whether shared messages should instead hang off `DOT|SET` is a
  separate ruling and should not ride along on a defect fix.
- **The 130 blank `TOPIC` cells.** `row.topic = artifact.command` is empty for
  these rows in HELP_LINE and in HELP_TOPIC alike -- consistent, and out of
  scope here. One defect at a time.
- **`STATUS=pending` with `CONFID=AUTHORITATIVE`** on 130 rows. Untouched.
- **That it builds.** The sandbox cannot compile. Nothing may be recorded
  `runtime-proven` until a build and a `CMDHELP BUILD LEGACY` have run and
  `help_store_check.py` reports clean.

## 6. Ownership and authorization

    src/help/helpdata_export_dbf.cpp   owner member.derald, subsystem help,
                                       no lane, status supported
    worktree blob == HEAD blob         CLEAN -- no concurrent session is
                                       holding it (theirs is src/cli/cmdhelp.cpp)

This is engine code and it changes a published data surface, so it wanted an
explicit go. **Granted by member.derald 2026-08-25, in session, for this one
line and nothing else.**

## 7. How to verify it worked, before and after

    $py12 tools\coordination\help_store_check.py

Today it exits 1 on two defect classes. After a rebuild it must exit 0. The
topic-set diff will show +139 GAINED and 0 LOST -- and that is the assertion,
not the count.

## 8. VERIFIED. The store is clean.

Built 2026-08-24 17:59:50 by member.derald. Store rebuilt. Measured with
`tools/coordination/help_store_check.py` against the pre-fix snapshot
`dottalkpp/data/help.bak-20260824-175951`:

    reachable topics ......... 526 -> 665
    blank TOPICKEY rows ...... 2,757 -> 0
    headers with no lines .... 139 -> 0
    line rows ................ 29,206 -> 29,262
    topic-set diff ........... +139 GAINED, **0 LOST**
    exit code ................ 1 -> 0    RESULT: clean

**Zero LOST is the load-bearing half.** It proves no row that already had a key
lost or changed it -- which is what `topic_key_for`'s first branch guarantees and
what would have falsified the reasoning in section 3 had it failed.

The 139 gained keys are the owner forms named in section 2: 130 `COMMAND:*`,
8 `SUBSYSTEM:*`, `GLOBAL`, and `MINER:SOURCE`. The exact spellings come from the
freshly regenerated HELP_TOPIC rather than the stale one, so a few differ from
the pre-fix orphan list (`COMMAND:REL JOIN`, `COMMAND:ERSATZ DELTA`,
`COMMAND:SET DEVDIAG` and similar are current commands whose old headers had
drifted). The COUNT is 139 either way, which is the assertion.

### The one thing this run did NOT do

`CMDHELP BUILD LEGACY` and `CMDHELP BUILD . <src>` were passed as a TWO-ELEMENT
`-CommandLines` array, and **only the first ran**. HELP_LINE and HELP_TOPIC did
not move; only COMMANDS.dbf and CMD_ARGS.dbf did. This is finding 3 of
GATE4_REFRESH_VALIDATION_V1.md -- `--script` is stdin redirection
(`main.cpp:195-213`), so a nested `std::cin` read inside the first command eats
the following line. It is the same failure that cost v5 a cycle on 2026-08-12,
and my apply script inherited the two-in-one form from the package without
questioning it.

**Rule: one `datarun.ps1` invocation per HELP-mutating command.** Never an array.
The package's section 7 step "5 + 6" should be split. Caught here only because
the checker read mtimes and said the tables had not moved -- a transcript alone
would have looked fine.

## 8a. Applied -- exact extent

    src/help/helpdata_export_dbf.cpp   1 line removed, 14 added
                                       (the assignment plus a WHY comment)
                                       verified: diff against HEAD shows one
                                       hunk at line 630 and nothing else

All four verification steps ran and passed (section 8), and the retrieval proof
ran too -- see 8b. What is still owed:

1. ~~A retrieval proof.~~ **DONE, see section 8b.**
2. **Commit.** Nothing here is committed.
3. **The binding is still dirty.** The exe is `c39d966c dirty` plus this edit
   plus the concurrent session's uncommitted `src/cli/cmdhelp.cpp`. The store is
   still not reproducible from a commit.
4. **The 167 `STATUS=pending` + `CONFID=AUTHORITATIVE` rows** are now the
   loudest thing the checker says. Untouched here, and next.

## 8b. Retrieval proof -- and a correction to the finding's cost claim

`CMDHELP COMMAND:SET` renders NOTHING, and that is correct:

    CMDHELP COMMAND:SET
    (topic exists, but no renderable help sections were found)

The topic RESOLVES -- the key reaches it, as section 4 predicted. What stops it
is a second, deliberate gate. `should_render_topic_line` (`cmdhelp.cpp:1705`)
drops `STATUS` outright as "validator material", and `MESSAGE` is not in
`render_kind_default`'s allow-list (`:1580`). `COMMAND:SET`'s 151 rows are 80
STATUS and 71 MESSAGE. Both blocked.

**That gate is policy, not a bug**, because of what the rows are:

    STATUS | SET_MESSAGE_CATALOG_VALIDATION_STATUS_TE | Message catalog validation: {status}

Runtime message-catalog strings with `{placeholder}` slots. Rendering those into
an operator help page would be noise.

`CMDHELP COMMAND:AUTODBF` is the topic that proves the fix:

    COMMAND:AUTODBF
    ===============
    ERROR
    -----
    Cannot open {path} for read.
    MAXCHAR must be between 1 and 254.
    line {line}: expected {expected} column(s), found {found}
    long text requires {bytes} bytes; AUTODBF does not auto-promote to memo yet
    target exists: {path}
    ... 35 rows

Every failure AUTODBF can emit, on one page, reachable by name, where before the
fix none of it was addressable at all. **Data layer to screen, end to end.**

The measured split:

    owner-keyed rows ...... 2,757
    renderable ............ 530    ERROR 478, WARNING 32, HINT 19, DEPRECATION 1
    blocked by policy ..... 2,227  STATUS 1,098, MESSAGE 1,009, SOURCE_FACT 120
    topics with content ... 83 of 139

**The finding's section 8 has been corrected.** It claimed nine percent of the
operator's help was unreachable and named SET and ABOUT as the headline losses.
The true figure is 530 operator-facing rows across 83 topics, plus a broken join
that made 2,757 rows unaddressable in the data layer regardless. Real, and
smaller than claimed. The correction is written into the finding rather than
edited over.

**Open, and NOT ruled here:** 56 of the 139 owner topics have zero renderable
rows and can never render. That is `topics=0` inverted -- a topic that exists
and can never answer. They look like `MSGMGR`'s surface, not `CMDHELP`'s.

---

## Good Neighbor note

    WHAT CHANGED   : this document, and ONE line of
                     src/help/helpdata_export_dbf.cpp (line 630, plus a WHY
                     comment above it). No other source, no data, no store, no
                     rebuild, no commit.
    WHOSE AREA     : subsystem help, owner member.derald. The file was CLEAN
                     against HEAD before the edit -- no concurrent session was
                     holding it.
    AUTHORIZATION  : member.derald, in session 2026-08-25, answering "have
                     you/can we resolve shared msg" with "Apply the one line
                     now". Scope granted: that one line. Nothing else was
                     touched under it.
    VERIFY OR UNDO : every claim re-reads from helpdata_export_dbf.cpp:291/346/
                     419/630, helpdata_artifacts.cpp:75-88,
                     helpdata_model.cpp:36-49, cmdhelp.cpp:2173-2217, and the
                     live tables via help_store_check.py. Undo is restoring
                     line 630 to `row.topickey = artifact.cmdkey;` and deleting
                     this file -- the change is one hunk and reverts cleanly.
