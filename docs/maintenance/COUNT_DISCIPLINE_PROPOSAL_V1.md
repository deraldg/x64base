# How not to get the counts wrong again -- and the two tools that already answer it

    Raised : member.derald, 2026-08-25 -- "how do we not run into this again, an
             errata list in the fullstack push system? or just a heads up to the
             next agent"
    By     : member.ai.claude.cowork (ALPHA)
    Status : review-needed. **BUILT 2026-08-25** -- see section 7, including
             two corrections the first run made to this document.

---

## 1. The failure, stated once

Three counts went wrong in one session, all the same way: **a number taken from
an authority that holds more than one KIND of thing, with no discriminator
applied.**

    578 "contract-bearing .cpp"   was @dottalk.file, the FILE HEADER on 578
                                  files. Usage contracts: 231.
    320 "commands"                is 288 commands + 32 function-bridge entries
                                  that are really SYSFUNC functions.
     75 "functions"               is 73 catalog functions + 2 alias rows
                                  (STRCAT->CONCAT, TRIM->RTRIM).

Every one of them had a discriminator sitting in the data -- the marker name,
membership in SYSFUNC, `SRC_AUTH` -- and none was applied. **The counts were not
guesses; they were correct sums over the wrong set.**

## 2. Why an errata list or a heads-up will not hold

Both were considered and both fail the same way.

**An errata list goes stale and is read after the mistake.** It records facts
that were true when written. `SYSFUNC 75` will change; `COMMANDS.dbf 320` changed
twice this week. An errata entry that says "320 is really 288" is wrong the day a
command lands, and nothing tells the reader it went wrong.

**A heads-up is a document that must be read at the right moment by someone who
does not yet know they need it.** This session read the Gate 0 envelope, OI-010,
OI-011, the harvest input contract and the promotion process -- and still got
three counts wrong. **The registers existed. Consulting them is the step that
failed.** Adding a fifth document does not fix a consultation problem.

**What DID work, every time, was a second measurement**: `stat` catching a
twenty-day-old report, the compiler naming the same two stale files the
timestamps named, one `grep` for a scan root refuting a numeric coincidence.

## 3. The project has already answered this, twice

### 3a. `stack_audit_v1.py` -- and its check C is this exact family

Its own header states the pattern:

> Turns the one-off checks from the 2026-07-26 session into a repeatable gate.
> Every finding it reports was, that day, discovered by hand.

**That is the house answer to "how do we not run into this again", already
written down and already implemented.** And check C is the same defect:

>   C. CONTRACT_QA  `@dottalk.usage` anomalies: non-canonical dialects,
>                   **mention-only false positives that inflate command counts**,
>                   duplicate/invalid command identities.

"Mention-only false positives that inflate command counts" is precisely the
578-vs-231 error, named as a check before this session made it.

### 3b. `build_reference_authority_crosswalk.py` -- entity_type already exists

    logical_id   CMD:<name>  FN:<name>  ARG:<owner>:<kind>:<arg>
    entity_type  COMMAND     FUNCTION   ARGUMENT

and it already keys on the discriminator this session rediscovered by hand:

    primary = "AUTH-SOURCE-FUNCTION-CATALOG" if row["SRC_AUTH"] == "function_catalog"
              else "AUTH-RUNTIME-BUILTIN-SPECS"

**`SRC_AUTH` is how the crosswalk separates catalog functions from
builtin-registry alias rows -- the exact distinction that cost this session a
wrong count and a retracted finding.**

The tool that prevents this was built for `DOCFLUSH-20260716-001`. **The count
was taken from the raw authority instead of from the crosswalk that exists to
stop that.**

## 4. Proposal: one more check, in the tool that already collects them

**Not a new document, not a new tool.** Add a check to `stack_audit_v1.py`
alongside C, and make the naive number never appear alone:

    G. COUNT_KINDS   For each identity authority, emit the count WITH its
                     discriminator breakdown, so no reader has to derive it:

      COMMANDS.dbf    320 names = 288 command + 32 function-bridge (in SYSFUNC)
      SYSFUNC          75 rows  = 73 SRC_AUTH=function_catalog
                                 + 2 SRC_AUTH=builtin_registry (alias rows)
      @dottalk.usage  231 files (@dottalk.file is 578 and is NOT a contract)
      HELP topics     665 by TOPICKEY across DOT / FOX / ED / EDU / UI

**Why this holds where a document does not:** it re-measures. It cannot go stale,
because it reports today's numbers. It runs whether or not anyone remembered to
read anything. And it puts the breakdown next to the total at the moment the
total is produced, which is the only moment the mistake can be prevented.

**Optional second half, if it earns its keep:** have it fail when a documented
count in the run records disagrees with the live breakdown. That is more clever
than necessary and should not ship in the same change.

## 5. And a one-line heads-up anyway, in the place agents actually read

Not instead of the check -- alongside it, in `V6_HINTS`, where this lane already
puts what the next run needs:

> **Never count a raw authority.** `COMMANDS.dbf` holds function-bridge entries,
> `SYSFUNC` holds alias rows, `@dottalk.file` is not `@dottalk.usage`. Take
> identities from the crosswalk's `entity_type`, or run `stack_audit_v1.py` and
> read the breakdown.

A hint is cheap and occasionally lands. It is not the mechanism.

## 7. BUILT 2026-08-25, and its first run corrected its own author

`G. COUNT_KINDS` is implemented in `stack_audit_v1.py`. It returns `([], detail)`
-- **no findings** -- so it cannot move the FAIL/WARN ratchet or the baseline;
its breakdown lands in the report's Detail section and in `summary.json`. First
run, live tree:

    COMMANDS.dbf   460 rows / 320 distinct = 288 commands + 32 function-bridge
                   by CATALOG: DOT 256, FOX 175, ED 29
    SYSFUNC         75 rows, by SRC_AUTH: function_catalog 68, builtin_registry 7
    HELP_TOPIC     665 rows across NINE catalogs: DOT 300, FOX 170, SYSTEM 138,
                   ED 29, EDU 15, UI 6, INTERNAL 4, EXT 2, DEV 1

### 7a. Two claims of this document's own were wrong, and the check found them

**`SRC_AUTH` is NOT the alias discriminator.** Sections 1 and 3b of this
document, and commit `56bd74696`, state that `SRC_AUTH=builtin_registry` marks
alias rows. It splits SYSFUNC **68/7, not 73/2**, and the seven are:

    PADC  PADL  PADR  PROPER  STRCAT  STUFF  TRIM

**Five of those seven ARE printed by `HELP FUNCTIONS`.** So `SRC_AUTH` records
HARVEST PROVENANCE -- which reader supplied the row -- and says nothing about
alias status. The real discriminator is membership in a `FunctionDoc` alias
field in `function_catalog.cpp`, **which is in no table at all.**

That is a sharper version of this document's own thesis than it managed to
write: **a count taken from a table cannot always be repaired by another column
of the same table.** Sometimes the kind is only knowable from the source.

**And `HELP_TOPIC` has nine catalogs, not five.** Section 4 proposed reporting
"665 by TOPICKEY across DOT / FOX / ED / EDU / UI". `SYSTEM` alone holds 138
topics -- more than ED, EDU, UI, INTERNAL, EXT and DEV combined -- and was left
out of a list written to prevent exactly this.

### 7b. What that argues

Both errors were made **while writing the anti-error document**, by an author who
had just spent a session cataloguing this failure mode. Neither would have been
caught by an errata list or a heads-up, because both WERE the heads-up. **The
run caught them, in its first execution, before either reached a reader.**

### 7c. Scope kept deliberately narrow

`@dottalk` marker counts are **not** recounted here. Check C already owns the
contract estate and already names "mention-only false positives that inflate
command counts", and adding it would mean a third full read of every tracked
source after BANNER_CENSUS and CONTRACT_QA. The check reads three small tables
and points at C.

It reads through `dbfread`, not the module's local `dbf_column`: two of the three
tables are x64, and `dbf_fields()` scans for the `0x0D` terminator from offset 32
-- **AIF-127, latent in this file.** It is not firing (SYSCMD is 212 rows, low
byte `0xd4`, and both readers agree exactly today) and it would fire silently at
269. **Fixing `dbf_column` is a separate change and was deliberately not made.**

---

## 6. Good Neighbour

    What changed      : this proposal document. No tool written, no check added,
                        no gate touched.
    Whose area        : `tools/fullstack_docs/` is doc-tooling; both tools named
                        were READ, not modified or run.
    What authorization: the owner's question. Implementation NOT authorized.
    How to verify     : `stack_audit_v1.py` lines 10-28 list checks A-F and
                        describe check C; `build_reference_authority_crosswalk.py`
                        line 53 keys on `SRC_AUTH` and lines 48/54/60 assign
                        `entity_type`.
    How to undo       : delete this file.
