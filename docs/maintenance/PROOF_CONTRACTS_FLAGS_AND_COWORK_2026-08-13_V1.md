# Proof: contracts, flags, and co-work -- what one day measured

    Steward   : member.ai.claude.cowork (host-mounted, Class A)
    Co-worker : member.ai.claude.hosted / HOSTED-20260813-001 (proposed, unratified)
    Owner     : member.derald
    Measured  : 2026-08-13, tree at 04fab111c
    Class     : proof of PROCESS, not of runtime. No engine behaviour is claimed
                here. Every number below was measured on the date shown and can
                be re-measured with the command beside it.

---

## 0. What this is, and the one rule it follows

Three subjects came up repeatedly in a single session and turned out to be the
same subject: **contracts** (what a file declares about itself), **flags** (what
a marker is allowed to mean), and **co-work** (what two agents with different
access can and cannot see). Each failed in the same shape, and the shape is
worth having written down.

The rule this document follows, because it is the rule the day taught:

> A measurement you did not finish is not a measurement. An empty result from a
> command that timed out is not evidence of absence.

Every count below carries its scope. Where two independent counts disagree, both
are given and neither is promoted.

---

## 1. CONTRACTS

### 1.1 How many exist, and where

    grep -rl "@dottalk.usage" --include=*.cpp src        -> 229
    grep -rl "@dottalk.usage" --include=*.cpp src/cli    -> 203
    grep -rl "@dottalk.file"  src tests tools            -> 732

The v5 harvest reported "3459 rows from 205 files." **205 is `src/cli`-shaped
(203), not tree-shaped (229).** So roughly 26 contract-bearing files outside
`src/cli` -- `src/edu`, `src/help`, `src/identity`, `src/xbase`, `src/security`
-- carry contracts that may never reach HELP.

NOT PROVEN: that those 26 are actually unmined. The miner may take an explicit
root list. What IS proven is that "contracts exist" and "contracts are
harvested" are different claims, and only the second reaches an operator.

### 1.2 A `risk:` block does not reach the operator. Measured.

    risk: blocks in source                  210
    loses_ephemeral_data in source            1
    loses_ephemeral_data in built HELP DATA   0

VDISK has carried `loses_ephemeral_data` for a long time. It scores **zero** in
the built store. So 210 risk blocks are documentation for source readers and
nothing else. That is a legitimate design -- but it is not what an author
writing one would assume, and nothing tells them.

### 1.3 The three surfaces drift by COMPLETENESS, not contradiction

Three separately-authored surfaces describe the same command: `dotref.hpp`, the
`@dottalk.usage` block in the `.cpp`, and the `HELP <verb>` topic renderer.
`refcheck` proves every dotref entry RESOLVES. Nothing proves the three AGREE.

Two independent counts of `WORKSPACE` forms, deliberately both reported:

    this steward   : 50 in the usage block vs 14 in dotref   (ratio 3.6)
    hosted session : ~20 in the usage block vs ~6 in dotref  (ratio 3.3)

Both greps are crude and neither is authoritative. **The ratio agrees.** The
finding is therefore the characterisation, not the number: the surfaces do not
contradict each other, they truncate each other. `WRITEBACK` is present in both
(1 occurrence each) -- the hosted session checked before asserting a divergence
and correctly found none.

### 1.4 The enforceable rule is narrower than the stated rule

House rule: no non-ASCII in scripts or docs. Enforcement: `check_house_style.py`
has `CHECKED_SUFFIXES = (".md",)` and inspects ADDED lines only.

    U+2500 occurrences in src/*.cpp        4943   (across 79 lines)
    U+2500 in built HELP DATA                 0

The harvester reads the CONTRACT BLOCK, not the file. So a gate can check
contract blocks precisely without touching ~4900 decorative separators. The rule
as stated is unenforceable and the rule as enforced is invisible; both were true
for months and nobody could tell, because nothing compares them.

    CORRECTED DURING VERIFICATION OF THIS DOCUMENT. The first draft cited
    "3556", carried forward from an earlier session summary and never
    re-measured. Re-measuring today gives 4943 occurrences across 79 lines --
    a different number AND a different metric, since the two figures were
    never counting the same thing. The direction of the finding is unchanged
    and the zero in the store is unchanged, but a proof that recycles an
    unverified number is not a proof. Caught only because the verification
    pass re-ran every figure instead of trusting the ones that felt settled.

---

## 2. FLAGS

### 2.1 A flag's honesty depends on something being able to falsify it

The memo challenge lane tags every idea:

    numbered ideas          115
    [NOW]                    69
    [WALKED green]            4
    [PROC] / [BUDGET]        17

These are honest because `WALKED green` is only written after a run, and a run
can fail. The tag is expensive to earn. Compare:

### 2.2 Chartered-empty and invented-empty look identical and are not

`ensure_catalog` creates `PAYLOAD_SHA`, `EST_HYD_B` and `VERIFIED_AT` empty, each
with a comment naming the milestone that fills them. An empty chartered column is
a **promise**.

`WORKSPACE CATALOG` shipped a CARRIER column that read a NUMERIC `WS_ID` looking
for a letter prefix that lives inside the payload. It rendered `-` for all 106
rows. An empty invented column is a **defect**.

**Both render as blank.** The hosted session read the second as the first and
wrote it up as "the catalog reporting its own chartered gap, out loud" -- elegant,
internally consistent, and false. The distinction survives only because
`ensure_catalog` DECLARES its charters in comments. Nothing enforces that; had
the declaration been missing, the two would be indistinguishable by inspection.

**Rule this produces:** a flag that cannot be falsified is decoration. Before
adding a column, ask what would have to be true for it to hold a different value.
If nothing in the writer can produce one, it is a fact about the table, not a
column in it.

### 2.3 Good-neighbour triggers: five defined, four fired

`GOOD_NEIGHBOR_POLICY_V1` section 2 lists five triggers. On 2026-08-13 four
fired, and this steward had noticed one before reading the policy:

| Trigger | Instance |
|---|---|
| promotion | committed another lane's `glue_xbase.cpp` work (`6634a5496`) |
| shared-file edit | added a doctrine section to AIF-050's protocol (`5283c6d49`) |
| audit restating numbers | the 83-file backlog triage (`e60b4a619`) |
| promotion | published the memo lane's material to a public site |

The policy's own line is the measurement: *"If in doubt, it fires."* Four of five
in one session suggests the default assumption should be that it fires, not that
it might.

---

## 3. CO-WORK: the ledger, both directions

Two agents, same tree, different access. The host-mounted session can compile,
run, grep and commit. The hosted session reads the public remote and cannot run
anything.

### 3.1 What the hosted session found that the host-mounted one could not

- **The path-traversal hole in `hydrate_minidb`.** `dst` built as
  `ramRoot / fs::path(rel)` with no normalisation, and the sidecar branch writes
  the real filesystem with `std::ios::trunc`. Found by reading breadth-first
  across the challenge list and the code together. **The host-mounted session had
  been editing that file all day and never looked at the loop.**
- **The field count.** 19 descriptors plus `SNAPSHOT`. The host session said 20
  plus the memo, twice.
- **The unreachable-pointer problem.** Five assignments issued by path to a
  reader who could open two of them, because `development` was 15 commits ahead
  of `origin`. The hosted session caught it; the host session had asserted
  reachability without measuring it.
- **The drift characterisation** (1.3): completeness, not contradiction. Not in
  the v6 hints, which say only that the three "render differently."
- **A teaching line that broke a host-session invariant.** "The map is drawn in
  the same ink as the territory" is why `WORKSPACES.dbf` is an ordinary table --
  which is exactly why "nothing else writes it" was false.

### 3.2 What the host-mounted session found that the hosted one could not

- **The CARRIER defect** (2.2), by grepping every writer and compiling a
  four-line probe for `operator/` semantics.
- **That the `0x64` DBF is unreadable by outside tools**, established by writing
  a naive parser and watching its field lengths sum to 893 against a 702-byte
  record, then discarding its output.
- **The sharper traversal case**: a platform-absolute member REPLACES the root
  outright, so there is no `..` pattern to detect. Measured, not reasoned.
- **The theme toggle root cause**: three component instances with three private
  `useState` values, found by reading the mechanism after three prior rounds had
  treated it as a visibility problem and each added a rendering site.

### 3.3 What each got WRONG

**Hosted session:**

- Rationalised the CARRIER blank as a chartered gap (2.2).
- Reported the `quip --ack` unlink defect as live. It was fixed in `036e311f1`
  on 2026-08-07, **an ancestor of their own baseline.** What they described was
  the fix's explanatory comment, which narrates the bug in enough detail to read
  as a report.
- Claimed `coordination/aif/AIF-087.claim` untracked. It is tracked, committed in
  `37f05130f`.
- Corrected a pointer to "V6_HINTS section 3" as wrong. Section 3 IS the drift
  note (lines 75-88); they read the section TITLE and concluded the content was
  elsewhere.
- Re-derived a recommendation written verbatim at line 87 of the file they were
  pointed at.

**Host-mounted session:**

- Shipped a column that could never hold a value, through every gate.
- Verified a load-bearing invariant by grepping ONE file.
- Asserted a protocol gap without reading the protocol; the pseudo-chat board had
  served hosted contributors all along.
- **Read timed-out greps as findings, three times**, twice telling the owner
  there was no "quantum" in a tree where it sits in `memo_zoo.cpp:10` and the
  charter's provenance line.
- Ran a phantom ruling (`dt_meta`) at the top of the priority list four times.
- Bundled three subjects into one commit, then could not cleanly back one out
  when its lane was reassigned.
- Claimed three site pages carried a stale writeback claim. It was one, and it
  was imprecise rather than false.

---

## 4. The two failure mechanisms, named

They are not the same failure and they do not respond to the same fix.

**Mechanism A -- an untestable hypothesis gets dressed rather than dropped.**
Belongs to the agent that cannot run anything. The better the writer, the more
convincing the result, and the harder for a later reader to spot. Fix: an anomaly
you cannot test is not a finding. Write "I could not determine why this is blank"
and hand it over.

**Mechanism B -- an unfinished command is read as evidence.** Belongs to the
agent that CAN run things, and is more dangerous precisely because it wears the
costume of measurement. An empty result feels like data. Fix is mechanical:
check `${PIPESTATUS[0]}`, not `$?` -- after a pipeline `$?` reports the last
stage, usually `sed`, and will read 0 while the grep that mattered was killed at
124.

Both mechanisms produce a confident false negative. Neither is caught by any gate
in this tree, because every gate checks CONSISTENCY -- does this agree with that
-- and both failures are disagreements with reality.

---

## 5. What this proves, and what it does not

**Proven** (measured, re-runnable): the harvest-scope shape (1.1); that `risk:`
blocks do not reach HELP (1.2); that the three surfaces truncate rather than
contradict, by two independent counts agreeing on ratio (1.3); that the ASCII
rule as stated and as enforced differ (1.4); the challenge lane's flag counts
(2.1); that four of five good-neighbour triggers fired in one session (2.3); and
every item in the co-work ledger (3), each traceable to a commit or a command.

**NOT proven:** that the 26 non-`src/cli` contract files are actually unmined;
that either WORKSPACE form-count is exact; that the pairing produces better work
than either agent alone -- one day is an anecdote, and this document is a record
rather than a study.

**Deliberately not claimed:** anything about engine behaviour. This is a proof
about process. The engine claims of the day live in their own commits with their
own evidence, and publication is not runtime proof.

---

## 6. The one-line version

Contracts, flags and co-work all failed the same way: **something declared what
it was, nothing checked, and the gap stayed invisible because the check that
would have caught it was never the check that ran.**
