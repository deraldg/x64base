# Cowork session handoff -- 2026-08-13

    Steward   : member.ai.claude.cowork (host-mounted, Class A)
    Owner     : member.derald
    Tree      : D:\code\ccode @ 04fab111c (pushed); site D:\dev\x64base-site (separate repo)
    Status    : handoff. Commits listed are landed and pushed unless marked otherwise.

---

## 1. What landed (ccode), in order

| Commit | Subject |
|---|---|
| `82c25ee7f` | WORKSPACE CATALOG: remove a column that could never have held a value |
| `f3526e895` | Record the two-session co-work case: same five characters, two readings |
| `5283c6d49` | Pointers not copies, and the brief that puts a hosted coworker on-channel |
| `e60b4a619` | Refine the carrier claim the coworker's own insight broke, and triage the backlog |
| `6634a5496` | RECCOUNT at the expression seam |
| `04fab111c` | RECNO is the symptom; the expression seam resolves every unknown name to silence |

Website work is uncommitted at time of writing: ECO route, MemoTalk product,
schemas/Quantum-Memo-Zoo hero, theme-toggle fix. Separate repo, separate push.

---

## 2. GOOD-NEIGHBOR NOTES

Per `GOOD_NEIGHBOR_POLICY_V1.md` section 3: which lane, what I touched, the
consequence, the action owed. The owners were not online, so these land here
rather than as quips.

### 2.1 To the `USE ... AGAIN` / expression-seam lane -- I COMMITTED YOUR WORK

**Touched:** `src/cli/expr/glue_xbase.cpp`, committed as `6634a5496`.

**What it was:** your uncommitted RECCOUNT special-symbol addition (all four
accessor paths, `recCount64()`), sitting in the shared working tree with a full
explanatory comment and no commit message.

**Consequence:** it is now landed and pushed under a message I wrote, describing
your reasoning as I read it from your comment. The owner directed "commit now,
or some other slob has to do it without knowing why." I did not alter the code.

**Action owed to you:** check that my commit message represents your intent. If
it misstates the reasoning, say so and I will correct the record rather than
leave a wrong explanation attached to a right change. I am a coworker on this
file, not its author.

**Related, and NOT taken:** the same four accessor paths end in
`if (idx <= 0) return std::string(); / return std::nullopt;` with no error path,
so any unknown identifier in any predicate resolves silently to empty across
roughly fourteen consumers. `RECNO` is the visible instance. Two candidate
responses are written up in `04fab111c` and section 3a of the backlog triage.
**Both are rulings, not edits, and I did not make either.** Your file, your call
or the owner's.

### 2.2 To AIF-050 (coordination) -- I added a doctrine section to your protocol

**Touched:** `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`, new
section "Pointers, not copies" (`5283c6d49`).

**What it was:** an owner ruling of 2026-08-13 -- coworkers sharing a platform
exchange pointers (`<tree path> + <sha read against> + <section anchor>`), never
shuffled copies -- plus the precondition that a pointer is only a pointer if the
referent is reachable by the reader.

**Consequence:** your protocol grew a section I authored. It sits between Quips
and Limits, and it cites the ladder you already defined rather than replacing
it.

**Action owed:** review the placement and wording. I did not touch the existing
mechanism, the quip subcommand, the doctrine section, or the enforcement
section. If the new material belongs in its own document rather than inside
yours, move it -- I will not be offended by a relocation of my own text.

### 2.3 To the lanes named in the backlog triage -- I RESTATED YOUR NUMBERS

**Touched:** nothing of yours. `docs/maintenance/BACKLOG_TRIAGE_2026-08-13_V1.md`
(`e60b4a619`) counts and classifies 83 modified tracked files, including work
belonging to `USE_AGAIN`, AIF-105 (`ERP RELATIONS`), the portal report
generators, and eleven lane documents I do not own.

**Consequence:** the triage states what your uncommitted work IS, groups it into
proposed slices, and in two cases recommends an order (S3 before the v6
harvest-scope measurement). Trigger: "an audit that restates its numbers."

**Action owed:** none from me, and nothing was staged. The triage explicitly
records that S4, S5 and S9 are not mine to commit. If a grouping misreads your
lane, correct the triage -- it is a proposal, not a ledger.

### 2.4 To AIF-070 / the memo lane -- I PUBLISHED your material

**Touched:** the website (separate repo). The Quantum Memo Zoo figures, the six
driver personas, the "byte-faithful cage" framing, and the memo challenge's ten
categories now appear on the x64base.com cover and a new MemoTalk product page.

**Consequence:** material that lived in your charter, source header and
whitepaper is now public-facing copy. I carried the honest limits with it: the
single-process caveat, M2 unrun, and payload ceilings above 64KB unmeasured.
I did NOT promote `.__wbak` -- its placement is under review in PDR-001 and a
safety net advertised while under review is the overclaim shape this house
hunts.

**Action owed:** review the public wording before the site publishes. Publication
is not runtime proof and this handoff does not claim it is.

---

## 3. Owner rulings recorded today

- **`dtshema` is a misspelling; in `dtschema(s)` the trailing `s` is optional.**
  So the CATALOG footer's extension list is complete, its count is right, and
  the two `.dtshema` files in the workspaces root are misnamed litter.
- **Pointers, not copies** (section 2.2 above).
- **Quantum Memo Zoo is the project name**, not a rename -- `memo_zoo` is the
  identifier and the source header has said so since it was written.
- **MemoTalk** hosts MiniDB, the Quantum Memo Zoo, and the memo challenge.
- **Curate in rapid dev or lose the work**, and **an agent with disk access must
  not park documents in scratch.** Both owed as enforced portal rules; filed,
  not built.

---

## 4. What this session got WRONG, for the next reader

Recorded because the pattern repeated and the next steward should expect it.

- **Shipped a column that could never hold a value.** `WORKSPACE CATALOG`'s
  CARRIER read a NUMERIC `WS_ID` looking for a letter prefix that lives inside
  the payload, and would have been a constant even corrected. Every gate passed
  it. The first run caught it in one line.
- **Verified a load-bearing claim by grepping ONE file.** "Only `save_to_memo`
  appends to the catalog" -- true of code paths, false as an invariant, because
  the catalog is an ordinary table and sixteen generic writers exist.
- **Asserted a protocol gap without reading the protocol.** The pseudo-chat
  board already served hosted contributors, and had all along.
- **Read timed-out greps as findings, three times.** Twice I told the owner
  there was no "quantum" anywhere in the tree. It is in `memo_zoo.cpp:10` and
  the charter's provenance line. **An empty result from a command that did not
  finish is not evidence of absence.** Check `${PIPESTATUS[0]}`, not `$?` --
  after a pipeline `$?` reports the last stage, which is usually `sed`.
- **Issued five assignments by path to a reader who could not open three of
  them**, because `development` was 15 commits ahead of `origin`. The coworker
  caught it; I did not.

---

## 5. Open, and who owns it

**Owner rulings queued:** unknown-identifier semantics in predicates (add
`RECNO`, or make an unresolvable identifier an error across ~14 consumers);
generated-output commit policy; built HELP-store commit policy; the five
expression functions publishing as unsupported DOT commands (plus `BUILD INFO`
and `BUILD VECTORS`, which are a separate and cheaper gap); ratification of
`member.ai.claude.hosted`.

**WITHDRAWN as a ruling:** the "`dt_meta` safety boundary" this steward ranked
first for most of the session does not exist as a written question. `dt_meta`
was a summary's rendering of the `dt::meta` namespace, whose boundary is already
declared in its own contract header. What remains is a build-target question.

**Proofs owed:** the corrected `WORKSPACE CATALOG` is computed, not observed --
width 92, AUTHOR 15, new footer, all arithmetic and no run. The MINIDB
member-path guard (task 30) is specified for the hosted coworker and unbuilt.

**v5 docflush:** LEGACY pass ran (462 command rows, 2368 arg rows) and the
rewritten dotref entries are confirmed publishing. `CMDHELP BUILD . <src>` was
still running at handoff -- 721 source files, 6.1 MB, and a build that prints
nothing for minutes is indistinguishable from a hang. That belongs in the v6
hints as a defect in its own right.

---

## 6. Housekeeping done

- Commit-message drafts remain in `dottalkpp/data/tmp/` (gitignored, invisible
  to the tree, harmless). Fifteen files, mine, left rather than deleted so the
  reasoning behind today's commits is recoverable beside the commits themselves.
- No `.git/index.lock` taken at any point; every git call read-only
  (`--no-optional-locks`), every mutation handed to the maintainer.
- Nothing staged that belongs to another session.
