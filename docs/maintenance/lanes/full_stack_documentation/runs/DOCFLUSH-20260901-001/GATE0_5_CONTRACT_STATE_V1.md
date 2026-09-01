# DOCFLUSH-20260901-001 -- Gate 0.5, the contract state

    run       : DOCFLUSH-20260901-001 (v7)
    baseline  : 2d26612b9  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    posture   : REPORT-ONLY. Measurement, no source edited.
    motto     : normalize -- smooth -- improve

## THE FINDING OF THIS GATE IS AN INSTRUMENT, NOT A CONTRACT

**`tools/fullstack_docs/stack_audit_v1.py` is the contract authority. This
session spent hours re-deriving its output with a weaker second instrument,
`tools/selfdoc/audit_contracts.py`, and got several numbers wrong doing it.**

That is a north-star violation in the tooling itself. The lane's own rule:

> *"A fact is entered once, at the source, and carried across the span derived --
> never re-typed on the far bank."*
> *"If a fact is wrong in more than one place at once, you are not looking at a
> bug. You are looking at a missing plank -- a fact that was copied instead of
> crossed."*

The contract inventory is derived twice, by two tools, and the copy is wrong.
That is the plank v7 drives.

## How the copy was wrong -- three conflations, each named by the authority

`audit_contracts.py` keys on the literal `@dottalk.usage`. That substring also
matches two OTHER vocabularies and one non-declaration:

1. **`@dottalk.usage.voluntary`** -- 15 command files. These say of themselves
   *"NOT UNDER CONTRACT -- voluntary description, offered not promised. Nothing
   verifies this block and nothing may fail because of it."* They use
   `documents:` rather than `command:` **deliberately**, so they do not
   double-bind against the SET ladder's `@dottalk.subusage`.
   `tools/fullstack_docs/convert_subcmd_to_voluntary.py` is the tool that
   demoted them. Counting them as contracts inflates the population and lets a
   block that disclaims verification satisfy a check.
2. **`@dottalk.subusage`** -- 14 files. The SET ladder's binding identity.
3. **Prose mentions.** `cmd_rpg`, `cmd_trigger`, `cmd_ttestapp`, `cmd_vmware`,
   `cmd_vt200` carry no contract at all. They matched because a comment says
   *"...and a @dottalk.usage contract IN THE SAME COMMIT as the handler."*

`stack_audit_v1.py` reports this class directly, and its wording is the epitaph
for the second instrument:

    CONTRACT_QA/MENTION_ONLY: 27 file(s) mention @dottalk.usage with no
    parseable contract -- naive marker counts are inflated by these

**Corrected population: 188 contracted command files, not 203.**

## What the authority reports that this session would otherwise have missed

Run at baseline `2d26612b9`:

    BANNER_CENSUS/DERIVED_ONLY
      1023/1079 (94.8%) @dottalk.file banners carry ZERO authored fields --
      backfill defaults, not collected knowledge.
      Do not treat status/owner/project as authority.

**This retires "coverage" as a quality measure.** Gate 0.5 first reported
`@dottalk.file` at 99.9% as though that were near-done. Nearly all of it is
empty scaffolding. The E3 target of "100 percent" measures presence of a banner,
not presence of knowledge, and the two were being conflated.

    DEAD_REG/MULTIWORD_KEY
      5 registry key(s) contain a space and can never be dispatched --
      ERROR CLEAR, ERROR STATUS, ERROR TEST, SET RELATION, SET UNIQUE

    DOTREF_COV/SUBCOMMAND_ONLY
      4 dotref entries are subcommands of a registered parent -- typeable, but
      never independently registered, so no contract, no SYSCMD row and no HELP
      topic: BUILD INFO, REL ENUM, SET VAR, SET VAR!

    CSV_VS_TABLE/STALE_CSV
      SYSCMD: table=212 csv=203 (table AHEAD of csv)

    REG_POLICY/SPLIT_REGISTRATION
      9 built-in commands registered both in shell_commands.cpp and in their own
      TU, against that file's own stated policy. Last writer wins, no diagnostic.

    REG_POLICY/WRAPPER_ASYMMETRY
      DELETE and RECALL are registered twice with handlers that DIFFER in whether
      they call relations_api::refresh_if_enabled(). Which one is live depends on
      static-init order, not on any rule.

## AIF-134 was already known, and must be corrected

`DEAD_REG/MULTIWORD_KEY` reports the ERROR family on every run of the authority.
AIF-134 opened a lane, wrote a charter, and captured a runtime proof for a
finding this tool already emits -- the "re-derived a ruling already recorded"
failure `CLAUDE.md` opens by warning about.

The lane is not worthless: the runtime proof (`Unknown command: ERROR` beside a
green `ERROR_STATUS`, one process, 2026-08-27) is evidence the WARN line does not
carry, and the AIF-131 sibling analysis stands. But the charter must:

- credit `stack_audit_v1.py DEAD_REG/MULTIWORD_KEY` as the discovering authority;
- **widen from three keys to five.** `SET RELATION` and `SET UNIQUE` were
  dismissed in this session's analysis because bare `SET` is registered. The
  authority draws the finer line: the KEY is dead even where the FUNCTION stays
  reachable through the router, so the registration is still a lie about how the
  command is reached;
- record that `BUILD INFO`, added to dotref earlier in this session, is itself
  flagged `SUBCOMMAND_ONLY` -- typeable via the router, but with no contract, no
  SYSCMD row and no HELP topic.

## Small true things, retained

    ALL THREE MEASURED 2026-09-01 AT BASELINE 2d26612b9 -- not inherited from v6.

    @dottalk.file uncovered : 1   include/dottalk/scratch_sidecar.hpp
    E4 refcheck_v1          : PASS (0 guarded phantoms)
    E4 normcheck_v1         : PASS (0 findings in fail-severity lanes)

Dated deliberately. v6's E3 and E4 both read PASS on 2026-08-26 and E3 had
regressed by this baseline; a PASS with no measurement date cannot be told from
an inherited one, and that is the whole reason this run re-ran them.

E4 is worth noting as the counter-example: `refcheck` and `normcheck` are house
tools, run directly, and their answers held. The session went wrong only where it
substituted its own instrument for one that existed.

## RETRACTED from the first draft of this gate

- *"208 of 303 DOT commands have no worked example -- the single largest contract
  deficit in the tree."* **Wrong, and corrected by the owner: "help has plenty of
  samples."** 795 EXAMPLE rows exist; they are concentrated, not absent. The
  ~26-31% figure is documented house knowledge (the `.dts` corpus, ~734 files, is
  the teaching surface), matched here to within a point. A recorded design was
  relabelled a defect.
- *"20 usage contracts missing `command:`."* **Wrong.** 15 are `.voluntary` and
  correctly use `documents:`; 5 are prose mentions with no contract. Editing the
  15 would have re-created the exact double-binding
  `convert_subcmd_to_voluntary.py` exists to remove.
- *"@dottalk.file coverage 99.9%, nearly done."* **Misleading.** 94.8% of banners
  are empty backfill.
- The v6 run described as having FAILED. It did not; the final stage was
  postponed deliberately. See the Gate 0 envelope.

## The two tools compared, measured rather than asserted

The first draft of this gate called `stack_audit_v1.py` superior and
`audit_contracts.py` a copy to retire. Owner asked which is actually superior,
or whether the functions differ. **Measured: they differ, by exactly one check,
and it runs the OTHER WAY along the same span.**

| question | stack_audit_v1 | verdict |
| --- | --- | --- |
| `@dottalk.file` present? | `BANNER_CENSUS`, plus `DERIVED_ONLY` (authored vs backfill) | authority is superior |
| `@dottalk.usage` present? | `CONTRACT_QA`, plus `MENTION_ONLY`, `NON_CANONICAL_DIALECT`, `INVALID_IDENTITY`, `DUPLICATE_IDENTITY` | authority is superior |
| contract-declared command reaches dotref? | `DOTREF_COV` runs **dotref -> live SYSCMD** | **not covered** |

Empirical test, not inference: **`stack_audit_v1.py` does not report `TRANSACTION`
at any severity.** `src/cli/cmd_transaction.cpp` declares `command: TRANSACTION`
in a usage contract, no dotref entry exists, so the command can never receive a
help page. `DOTREF_COV` cannot see it because that check enumerates dotref
entries -- an entry never written is invisible to a check that starts from the
entries.

    stack_audit : dotref entry  -> does it resolve to a live command?   (PHANTOMS)
    audit_contracts : contract  -> does it reach dotref?                (ORPHANS)

A phantom is an entry with no command. An orphan is a command with no entry.
Both directions are needed to prove the span is complete; today only one is
checked, and the uncovered direction is the one that hides a command from HELP.

**No tool was changed. Owner declined the merge at this time.** The gap is
recorded here so the next run does not have to re-derive it -- which is the
whole point of this lane, and the failure this session repeated three times.

Two cautions for whoever does land it:

1. Build it inside `stack_audit_v1.py` on that file's already-correct parser. A
   second parser is how `audit_contracts.py` acquired the substring bug that
   counted `.voluntary` blocks and prose mentions as contracts.
2. Do NOT port `audit_contracts.py`'s exemption logic. Its `helpers=10` count
   comes from `layer: helper` / `status: implementation-helper`, and the
   `layer: helper` arm is UNRULED -- it took the missing-usage count from 7 to 1
   on 2026-08-26 with no documentation written. An unruled exemption does not
   belong in the authority.

## The pylon, in the motto's terms

**Normalize.** One contract authority. `stack_audit_v1.py` is it.
`audit_contracts.py` answers one question the authority does not (orphans), and
that question should move INTO the authority rather than justify a second tool.
Until it does, `audit_contracts.py` is retained for that single check and must
not be cited for the other two, where it is measurably wrong.

**Smooth.** Correct AIF-134 to cite the authority and widen to five keys. Put
`stack_audit_v1.py` in the Gate 0.5 path of the cookbook so the next run starts
from the authority instead of re-deriving it.

**Improve.** The authority's own baseline moved this run
(`CONTRACT_QA 9 -> 7`, `BANNER_CENSUS 1 -> 2`, `SRCFILE_DRIFT 0 -> 2`,
`counts.WARN 18 -> 22`). That delta is the real contract state, it is already
tracked, and no second instrument is needed to see it.
