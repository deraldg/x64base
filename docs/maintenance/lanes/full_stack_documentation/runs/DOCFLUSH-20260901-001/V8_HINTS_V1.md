# V8 hints -- what v7 learned, and what v8 should decide

    from      : DOCFLUSH-20260901-001 (v7)
    baseline  : 2d26612b9  (2026-09-01)
    for       : the next full-stack run (v8)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    motto     : normalize -- smooth -- improve

v5 left `V6_HINTS_V1.md` and v6's plan opened by reading it. **v6 left no
V7_HINTS**, so v7 had to reconstruct its starting position out of a closeout and
a readiness review. This file exists so v8 does not repeat that. Leaving it is
the lane's own instruction: *"writes down what it learned so the next crossing
starts further along."*

---

## 1. THREE SPECIFIED DECISIONS FOR v8 -- EACH WITH ITS ACCEPTANCE TEST

**Not a backlog and not open questions.** Each is a closed specification whose
evidence step is named, handed to the run that can actually run it.

Owner ruling, 2026-09-01: **these are the kind of decision you make when the
mission is done and you can back-verify you were right.** v7 raised them mid-run,
off findings hours old, in a session that had been corrected three times that
day. The ruling is about SEQUENCE, not merit -- the findings stand; what they had
not yet earned was the right to change doctrine or a house tool.

Scope note, so v8 does not inherit an ambiguity: the owner's "no" on 2026-09-01
applied to ONE action -- v7 editing `stack_audit_v1.py` in that session. It did
not reject D1 as a question, and D2 and D3 had not been raised when it was given.

### D1. `CONTRACT_COV` -- probably a non-problem. Come at it from the generator side.

**The finding.** `stack_audit_v1.py` and `tools/selfdoc/audit_contracts.py`
differ by exactly one check, running opposite directions along one span:

    stack_audit     : dotref entry -> live command?   catches PHANTOMS
    audit_contracts : contract     -> reaches dotref?  catches ORPHANS

Empirically: `stack_audit_v1.py` reports `TRANSACTION` at no severity.
`src/cli/cmd_transaction.cpp` declares `command: TRANSACTION` with no dotref
entry, so it can never receive a help page. `DOTREF_COV` enumerates dotref
entries, and an entry never written is invisible to it.

**REFRAMED BEFORE IT WAS EVER SPECIFIED AS WORK. Owner, 2026-09-01: this "sounded like a
complication that will go away on its own when we come in from another angle --
it usually does."** That reading is right, and the other angle already exists in
the tree:

    tools/fullstack_docs/dotref_autogen.py     report-only; generates what
                                               include/dotref.hpp WOULD contain,
                                               derived from shell_commands.cpp +
                                               @dottalk.usage. Never writes it.
    tools/fullstack_docs/generate_syscmd.py    same shape, for SYSCMD, from the
                                               contracts (AIF-067)

**An orphan is only possible while dotref is STORED.** The moment dotref (or
SYSCMD) is GENERATED from the contracts, a contract-declared command is in the
catalog by construction and there is nothing for `CONTRACT_COV` to find. The
orphan/phantom asymmetry is not a missing check -- it is the shadow cast by a
hand-maintained catalog, and it disappears when the catalog is derived.

That is this lane's own thesis: *"moves one more stored fact to a measured one,
one more manual step to a gate."* Building a check to compare two stored things
is the opposite move -- it makes the copy permanent by monitoring it.

**So v8's question is not "build CONTRACT_COV?" It is "is dotref ready to be
generated?"** If yes, drive that pylon and D1 closes itself. If no, `TRANSACTION`
remains a known single orphan, recorded here, and is cheaper to fix by hand than
to build an instrument for.

**Only if v8 rules to build it anyway:** put it inside `stack_audit_v1.py`, on
that file's parser, and re-measure first -- the finding holds only if `stack_audit`
still misses a contract-declared command with no dotref entry at v8's baseline. A
second parser is exactly how `audit_contracts.py` acquired the substring bug that
counted `@dottalk.usage.voluntary` blocks and prose mentions as contracts.

### D2. The `layer: helper` exemption -- RESOLVED at v7. Legitimate; but see the overlap.

**The finding.** `c492d957d` ("Harden fullstack contract preflight") added an
exemption to `audit_contracts.py` keyed on `layer: helper` in the
`@dottalk.file` block, running BEFORE the usage check. Measured effect: files
reported as missing a usage contract went **7 -> 1**, with zero documentation
written.

**Why it needs a ruling rather than a revert.** A helper genuinely exports no
command, so exempting it may be right. But the pre-existing exemption was
`status: implementation-helper` INSIDE the usage block -- a field whose only
purpose is to declare that, which you had to author a contract to claim. The new
one repurposes an architectural field that was already present for another
reason, and 330 files repo-wide carry `layer: helper`.

**RESOLVED AT v7, 2026-09-01 -- owner approved acting on this one.** Measured at
baseline `2d26612b9`:

    layer: helper, repo-wide (all C++)          328
    layer: helper, cmd_*/app_* command files      7   <- stable, = v7's earlier count
      ...of those with NO real @dottalk.usage     7   <- exactly what it silences
    status: implementation-helper (earned form)   3
    files carrying BOTH markers                   0

**Verdict: the exemption is NOT being used as a free opt-out.** The count is
stable and the population is small and closed. By the test as written, it is
being used as intended, and no "require both markers" rule is warranted.

**But the measurement found what the test did not look for: the overlap is
ZERO.** Two exemption mechanisms exist for one concept and no file uses both --
`layer: helper` (an architectural field, 7 command files) and
`status: implementation-helper` (a declared in-contract field, 3 files). They are
disjoint populations. Neither references the other, and nothing decides which a
new file should use.

So the normalization is not "require both". It is **pick one**, and it belongs to
AIF-129 (`contract-subblock-vocabularies-uncontrolled`) rather than to this lane:
a third instance of one concept spelled two ways with no controlling authority.
v8 does not need to re-measure this; it needs AIF-129 to rule which spelling
survives.

The seven files, for whoever rules it: `app_army`, `app_erp`, `app_paxon`,
`cmd_order` (all `src/cli/`), `cmd_fox_palette_entry`, `cmd_palette_shim` (both
`src/palette/`), and `src/tv/cmd_browsetui.cpp`. Note that last path -- there are
TWO files named `cmd_browsetui.cpp` and the `src/cli/` one DOES carry a contract.

### D3. `stack_audit_v1.py` in the cookbook's Phase 0.5 -- DONE at v7.

**The finding.** v7 re-derived, by hand, three things the tool already reports:
the ERROR multiword-key family (`DEAD_REG`), the ~26% sample coverage (documented
house knowledge about the `.dts` corpus), and the contract census
(`CONTRACT_QA/MENTION_ONLY`, whose own wording is *"naive marker counts are
inflated by these"*). The cookbook's Phase 0.5 currently names
`docpush_preflight.py` and `command_catalog_sync.py check` and does not name
`stack_audit_v1.py`.

**DONE AT v7, 2026-09-01 -- owner approved acting on this one.**
`stack_audit_v1.py` now LEADS the Phase 0.5 command block in
`FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V1.md`, above `docpush_preflight.py`,
with a note recording why and with the two findings that change how the rest of
the phase is read (`BANNER_CENSUS/DERIVED_ONLY` -- do not cite coverage as a
quality figure; `CSV_VS_TABLE/STALE_CSV` -- the SYSCMD table can run ahead of its
CSV mirror).

**What v8 still owes on this:** the line was added on v7's reasoning, not on
evidence from a later run. v8 should note whether running it first actually
pre-empted anything it planned to investigate. If it did not, the line is
ceremony and should be cut.

---

## 2. WHAT v7 GOT WRONG, SO v8 DOES NOT REPEAT IT

Four retractions, all the same shape: **a measurement turned into a verdict
before the system was understood well enough to judge what the number meant.**

1. **"208 of 303 commands have no worked example -- the largest contract deficit
   in the tree."** Wrong. Owner: *"help has plenty of samples."* 795 EXAMPLE rows
   exist and are concentrated, not absent. The ~26-31% figure is recorded house
   knowledge -- the `.dts` corpus (~734 files) is the teaching surface. A
   documented design was relabelled a defect.
2. **"20 usage contracts are missing `command:`."** Wrong. 15 are
   `@dottalk.usage.voluntary` and correctly use `documents:` so they do not
   double-bind against the SET ladder; 5 are prose mentions with no contract at
   all. Editing the 15 would have rebuilt the collision
   `convert_subcmd_to_voluntary.py` exists to remove.
3. **"`@dottalk.file` coverage 99.9%, nearly done."** Misleading.
   `BANNER_CENSUS/DERIVED_ONLY` reports **1023/1079 (94.8%) banners carry zero
   authored fields** -- backfill defaults. Coverage measures banner presence, not
   knowledge, and E3's "100 percent" target conflates them. **v8 should not cite
   coverage as a quality figure.**
4. **"v6 failed its publication entry."** Wrong, and it came from reading a
   status field instead of the closeout. `current_fullstack_doc_push.yaml` says
   `closed_publication_entry_failed`; v6's own closeout says *"deliberately
   unrun. Gate 0 through Gate 6 all ran."* The final stage was POSTPONED until
   the rest of the work is saved, staged and proven.

**The registry field and the closeout disagree, and that is itself a lane
finding.** By the north star's own test -- *"if a fact is wrong in more than one
place at once, you are looking at a missing plank"* -- the run-state fact is
stored in two places and one is wrong. v8 should reconcile
`current_fullstack_doc_push.yaml` with the closeout, or derive the field from it.
Not edited by v7: that file is `maintenance_class: maintained_current`, stewarded
by `member.ai.codex`.

---

## 3. STATE AT v7's BASELINE, FOR v8's STARTING POSITION

    E1  close at Gate 7      v6 reached Gate 6; final stage postponed, not failed
    E2  CMDHELPCHK PASS      UNRUN. Host only -- a sandbox cannot claim it
    E3  contracts 100%       NOT MET: 1 uncovered banner, and see retraction 3
    E4  refcheck+normcheck   PASS, re-proven 2026-09-01 at this baseline
    E5  harvest after build  PARTIAL at v6; the cookbook names this the condition
                             runs usually fail
    E6  command-catalog.mdx  scoped out of v6; re-entry is an owner call
    E7  backup + rollback    v6's `help.bak-20260825-180609` exists, but does NOT
                             cover a build v8 performs; take a fresh one
    E8  per-mutation auth    NOT SOUGHT at v6; enumerate before asking

**E4 is the counter-example worth carrying.** `refcheck_v1` and `normcheck_v1`
are house tools, run directly, and their answers held. Every place v7 went wrong
was a place it substituted its own instrument for one that already existed.

---

## 4. THE ONE HABIT THIS RUN WOULD PASS ON

Run the authority before forming the question. v7's pattern was: measure, form a
verdict, write it down, get corrected. Three times. The tree already knew about
the ERROR family, already knew examples were ~26% by design, already knew naive
marker counts are inflated -- and said so, in tool output, in the house rules,
and in its own comments.

The cheapest possible protection is the first line of `CLAUDE.md`: walk the
portal before designing. `stack_audit_v1.py` is the walk for this lane.
