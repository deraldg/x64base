# Coordinating and correcting concurrent AI agents in a shared repository

## The x64base process, drawn from a single day's evidence

Author: `member.ai.claude.cowork`. Date: 2026-08-07. Status: white paper (descriptive,
not doctrine). Authored outside the repository; the documentation system is frozen and
this is the maintainer's to place. ASCII throughout (`--`, `->`); `&&` is the DotTalk++
comment marker. Every claim is tied to an artifact or a command; if it does not
reproduce, it is wrong.

**Placement decision (owner, 2026-08-07).** White papers are a document class of the
**AI portal**, not generic docs: home is `labtalk/ai_portal/whitepapers/`. In the portal,
"filed" is not "reachable" -- an orphan avoids the fate this very paper documents only if
it is routed. So on placement it must also become a **node in `portal_recall_graph.yaml`**
with an edge from an entry-path node, plus a one-line pointer from `AI_PORTAL.md` (and, if
it earns seed space, the Tier 1 pointer table). Held on `D:\dev` until the documentation
system unfreezes; moving the file without adding the recall-graph node would file it and
orphan it in the same motion.

## Abstract

When several AI agents -- and a human maintainer -- work concurrently in one repository,
two failure modes dominate, and neither is the one version control is built to catch.
The first is the **quiet collision**: a session edits a file, restates a count, or
promotes an artifact another lane depends on, and moves on; the effect surfaces later as
drift the owner did not cause and cannot explain. The second is **false success**: a
tool or an agent reports a job done that was not -- a manifest that "regenerated"
without writing, a note that "filed" but was never read, an inbox that "acked" a message
it could not delete. The x64base process answers both with four cheap mechanisms: a
**channel ladder** matched to reach and durability, a **good-neighbor discipline** for
cross-lane courtesy, **gates and tests as memory** so correctness outlives the session
that wrote it, and a **measured self-correction** stance that verifies rather than
agrees. This paper draws each from events that occurred in a single day, including the
author's own errors, because a process that only survives its successes is untested.

## 1. The two failure modes

Concurrent sessions share exactly one medium reliably: the filesystem and the git tree.
Git coordinates *content* -- it will not let two commits silently overwrite the same
line -- but it is blind to *intent*. It cannot see that session A re-derived a count that
session B's lane depends on, or that a script printed success over a no-op. So the
process must add what git does not provide: visibility of cross-lane intent, and proof
that an action did what it claimed.

**Quiet collision (example, this day):** adding one allow-list pattern to `PROMOTE.manifest`
left `MANIFEST.txt` stale by one pattern. Git was content -- both files committed cleanly.
The staleness was invisible to the number-claim gate and would have surfaced later as an
unexplained count. It was caught only because the touching session left a note.

**False success (three examples, same day):** a manifest generator that "regenerated"
without its `--write` flag and reported no change; a good-neighbor note that filed
correctly and was never read, so a gate caught the staleness instead; and a message
inbox whose `--ack` printed `(acked 1)` while the file it claimed to delete was still
present, because the mount refused the unlink and the code swallowed the error. Three
instances of one shape: **reports success without doing its job.**

## 2. The channel ladder

Coordination is not one mechanism but a ladder, chosen by how far a message must reach
and how long it must survive:

| Rung | Reach | Persistence | Use |
| --- | --- | --- | --- |
| **quip** | co-sessions checked in *right now* | ephemeral (gitignored) | live heads-up / hand-off |
| **checkin / checkout** | any session | ledgered, transient | declare presence + claimed lanes |
| **claim** | any session | durable (tracked) | atomically own a lane number |
| **pseudo-chat / BBS post** | any tree-reading agent, any time | durable (tracked, addressed) | async message that must be received |

The rungs are not interchangeable, and choosing wrong is itself a failure. On this day
the author, having just built `quip`, reached for it to notify a co-session that was
**not checked in** -- so the message reached an empty room. The correct rung was
pseudo-chat: a durable, `TO:`-addressed, repo-side board the other session reads when it
next visits the tree, no concurrent presence required. The lesson generalizes: **a
message to an absent neighbor needs a durable channel; an ephemeral one addressed to a
run that is not live is a message to no one.** The ladder exists precisely so the sender
picks reach and persistence deliberately rather than by recency.

## 3. Good-neighbor discipline

Because git cannot see cross-lane intent, the process makes surfacing it a duty. The rule:
**when your work touches, promotes, audits, or bears on a lane you do not own, leave the
owner a pointer -- and never silently edit another owner's authoritative records.** The
note names four things: which lane, what you touched, the consequence, and the action the
owner needs. It lands on a rung from the ladder -- a quip for a live owner, a durable
board post or a handoff line for an absent one.

The discipline paid its first measured return the same day it was formalized: a
cross-lane note about the stale `MANIFEST.txt` is what prompted the owning lane to
regenerate the receipt. The pointer, not an edit, did the work -- the owner recorded the
truth from the signal. Courtesy is not politeness here; it is the only thing that
converts a silent cross-lane effect into a visible one before it becomes drift.

## 4. Gates and tests as memory

The process's deepest recurring finding is that **a correct artifact nothing routes you
to is not reached** -- "baked in is not reached." A rule written once in prose drifts,
because nothing re-presents it at the moment it applies. The countermeasure is to convert
a rule that keeps being forgotten into a **gate**: a check that fails closed at the
commit chokepoint, so the rule is enforced rather than remembered. "The gate is the
memory": a rule that earns a hard-failing gate demotes out of prose, because the gate now
carries it.

The same logic governs tests, and here the process caught itself. A coordination
primitive was given a test to guard it against silent rot -- but the test asserted the
happy path on a filesystem where the risky operation (unlink) works. It passed, and gave
false confidence, while the real deployment mount refused the unlink and the primitive
lied about it. **A guard that only exercises the path where the failure cannot occur has
the same blind spot as the code it guards.** The fix was not only to make the primitive
report the truth (`acked N of M`, and name the file it could not remove) but to make the
test *simulate the refusing mount* and assert the honest report. A test earns its keep by
exercising the failure, not the success.

## 5. The recurring defect shape, and its countermeasure

"Reports success without doing its job" appeared three times in one day across unrelated
tools. The shape is always the same: an operation whose failure is swallowed, and a
summary line that counts *attempts* rather than *effects*. The countermeasure is a
discipline, not a library:

- **Count effects, not intentions.** Report what was written, deleted, or promoted --
  never the number of items you looped over.
- **Surface the swallowed failure.** `except: pass` on a state-changing operation is the
  bug; name the exception and the object it acted on.
- **Verify against the world, not the return code.** A zero exit and a cheerful print are
  not proof; read the state back. The manifest that regenerated without writing, and the
  ack that deleted nothing, both returned zero.

This is the same instinct the engine's own tooling embodies -- simulate in a RAM
filesystem, diff, read back, and apply only on a clean prove -- lifted from data mutation
up to tool behavior.

## 6. Measured self-correction

The process treats agent judgement as fallible and instruments it. Three habits:

- **Verify rather than agree.** When a co-session accepted a claim, the response was to
  re-measure it, not adopt it. Agreement is the least useful review outcome; a plan that
  survives should survive an attempt to kill it.
- **Disclose the error record.** A session that made errors lists them, with how each
  surfaced, so a reader can weight its judgements. On this day the measurements held up
  and the recommendations built on them were wrong roughly a third of the time -- usually
  by proposing action before completing a count. Naming that rate is what lets the next
  reader calibrate.
- **Own the defect, route the fix.** When a co-session found a real bug in a primitive
  this author wrote, the correct move was to take the patch (it was the author's code),
  fix the test's blind spot, and credit the finder in the commit -- not to deflect to the
  environment that merely revealed it.

## 7. Case study: a coordination primitive in one day

The `quip` primitive is the process compressed into a day, two agent sessions cooperating:

1. **Define.** A term is coined and placed in the coordination protocol: an ephemeral note
   between co-sessions, the lightest rung of the ladder.
2. **Build.** Implemented in the coordinator with the same filesystem-atomic style as the
   claim allocator; one file per message, `O_EXCL`, gitignored inbox.
3. **Drift-proof.** A test guards it; a pointer in the auto-injected onboarding file makes
   it reachable, not just present.
4. **Dogfood, and miss.** Used to notify an absent co-session -- reached no one. Escalated
   to the durable pseudo-chat board, the correct rung.
5. **Receive and break.** The co-session, prompted by the board post, exercised `--ack`,
   found it claimed success while deleting nothing, and diagnosed the swallowed unlink and
   the miscounted summary -- the same defect the same file had already fixed in a sibling
   function months earlier and reintroduced in the new one.
6. **Correct honestly.** The author took the patch, made the primitive report `acked N of
   M` and surface the refusal, and -- the part that mattered -- rewrote the test to
   simulate the refusing mount, closing the guard's blind spot. Committed with credit to
   the finder.

No single actor did this well alone. The maintainer set the frozen-doc and
never-touch-`C:` guardrails; one session built and mis-used the primitive; the other
found the bug the first could not see from its own mount. The process is what made the
cooperation legible: a channel to carry the message, a courtesy to route the finding, and
gates and tests to keep the fix from rotting.

## 8. Principles, distilled

1. Git coordinates content; the process must add intent-visibility and effect-proof.
2. Match the channel to reach and persistence; the wrong rung is a silent failure.
3. Surface cross-lane impact as a pointer; never edit another owner's records.
4. Convert a forgotten rule into a fail-closed gate -- the gate is the memory.
5. A test must exercise the failure path, or it inherits the code's blind spot.
6. Count effects, not intentions; surface swallowed failures; verify against the world.
7. Verify rather than agree; disclose your error rate; own the defect, credit the finder.

## 9. Limits and honesty

This paper is descriptive of one repository's practice on one day, not a validated
methodology. Its central evidence includes the author's own three-instance failure record,
which is the point: the process earns trust by surviving its failures in the open, not by
narrating its wins. The mechanisms are cheap and filesystem-simple by design; whether they
scale past a handful of local concurrent sessions on one working tree is untested and
explicitly out of scope.
