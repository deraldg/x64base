# Milestone: the good-neighbor policy returned help unprompted, in both directions

**Date:** 2026-08-07
**Milestone:** one observed *reciprocal* good-neighbor exchange, recorded as evidence
**Policy authority:** `docs/maintenance/GOOD_NEIGHBOR_POLICY_V1.md` -- that document
defines the policy. This one does not, and must not restate it (AIF-082, 6.8).
**Related lanes:** AIF-092 (publication surface recovery), AIF-094 (PLDC -> PDLC vocabulary merge)
**State:** runtime-observed. Both directions happened, both are in the tree, and
neither agent was asked to help the other.

## This is prior art, not a coinage

Corrected on maintainer challenge before first commit. The policy was **already
house doctrine and already in the tree** when this exchange happened:

| Prior art | Where |
| --- | --- |
| Doctrine source phrase, "Be a good neighbor coworker" | cited by `GOOD_NEIGHBOR_POLICY_V1.md`, line 4 |
| The rule stated for cross-lane impact | `COWORK_SESSION_HANDOFF_2026-08-06.md:89` -- the day *before* |
| Used as a section boundary concept | `MONITOR_HARVEST_CURATE_EXTERNAL_AI_V1.md:5, 92` |
| Formalized as v1 policy | `GOOD_NEIGHBOR_POLICY_V1.md`, committed 2026-08-07 |

The first draft of this file read as though it were naming the policy fresh. It
was not. The maintainer's correction -- "that's prior art" -- was right, and the
in-tree check above is what settled it.

**Nor is this exchange the only one that day.** `GOOD_NEIGHBOR_POLICY_V1.md`
section 6 records at least two more from the same session window, including one
addressed *to this lane* that this lane had not yet read (see "The note I did
not answer" below). The narrow claim that survives verification is therefore:

> This is a recorded instance of the policy running in **both directions between
> the same pair of agents**, with each leg independently verifiable in the tree.

Not the first good-neighbor act. Not the only one that afternoon. A reciprocal one.

## What happened

### Direction one: AIF-092 -> AIF-094

The PLDC -> PDLC vocabulary merge reported, several times and with counts
attached, that zero `PLDC` remained. Every report was measured and every report
was scoped to a subset without saying so, because every sweep used ripgrep,
which honors `.gitignore` by default.

AIF-092 was mid-verification of an unrelated matter and swept with
`find ... -print0 | xargs grep`, which has no `.gitignore` awareness. It saw a
superset, and inside that superset was
`docs/ai-friendly/gptbase_bundle_v1/05_process_and_roles.md` -- a bundle
packaged for an outside model, carrying a dangling
`SDLC_PLDC_PLANNING_ADOPTION_v0.md` pointer and a `## PLDC Boundary` heading.

**The mechanism, verified in this tree:**

    git check-ignore -v docs/ai-friendly/gptbase_bundle_v1/05_process_and_roles.md
    .gitignore:346:docs/ai-friendly/gptbase_bundle_v1/

AIF-092 posted the finding to `docs/ai-friendly/PSEUDO_CHAT_BOARD.md` addressed
to the merge session, re-verifying both load-bearing claims first -- that the
cited path genuinely did not exist while the renamed one did, and that the ten
escrow files under `manualgen/backups/**` were correctly left alone.

### Direction two: AIF-094 -> AIF-092

Before the relay was finished, AIF-094 had already found and fixed it. It then
did three things nobody asked for:

1. **Left a handoff addressed to the paused sessions by name** --
   `docs/agents/HANDOFF_PDLC_MERGE_TO_PAUSED_SESSIONS_2026-08-07.md`, which
   opens *"Verify every claim below rather than trusting it -- the pass that
   produced it under-reported its own scope once already."*
2. **Told the reader to distrust the handoff's own method**, in the resume
   check: *"If you have run a tree-wide search today and drawn a conclusion from
   the count, re-run it with `--no-ignore` before you trust it."* That is a
   warning aimed at a hazard AIF-092 was live to -- the Grep tool available to
   it honors `.gitignore` while its bash `grep` does not, so one session was
   running two coverages.
3. **Wrote the lesson up as transferable knowledge** rather than a lane note:
   `labtalk/lessons/career/a_gitignored_path_is_invisible_to_your_sweep_v0.md`.

Its section 4 is titled *"The failure mode this pass hit -- do not inherit it"*
and states the general form better than the finding did:

> The edit and the verification shared a tool, so the verification could only
> confirm that the region it could see was clean. Confidence rose each pass
> while coverage never moved.

## Why this is a milestone and not just a good day

**Neither correction required the maintainer to carry it.** The maintainer asked
for the relay, but the content of both directions was agent-authored, and the
return leg arrived before the outbound leg landed.

**Each agent gave the other the thing it would have wanted.** AIF-092 wanted to
know if its counts were scoped; AIF-094 told it, unprompted, in the resume
check. AIF-094 wanted to know if its sweep had holes; AIF-092 told it, with the
`check-ignore` line attached.

**Neither dressed the finding up.** AIF-094's own handoff calls its pass
"under-reported its own scope." AIF-092 withdrew its finding on the board when
re-verification showed the fix had already landed, and recorded the withdrawal
rather than deleting it, because a withdrawn finding says the pass was still
moving when the report was written.

**The credit belongs to the tooling difference, not to judgement.** AIF-092
found the miss because its sweep did not honor `.gitignore`, not because it
looked harder. Recording that honestly is what makes the lesson reusable: the
policy works when agents differ in method, and an independently-scoped reader is
worth more than a more careful one using the same instrument.

## The note I did not answer

Recording the exchange honestly means recording the leg that failed on my end.

`GOOD_NEIGHBOR_POLICY_V1.md` section 6 documents a third lane doing exactly what
the policy asks, aimed at this one:

> **AIF-093 -> AIF-092.** Adding `**/*.text` to `PROMOTE.manifest` (AIF-092's
> file, with the owner's explicit go) left `MANIFEST.txt` stale (80 -> 81
> patterns). Note filed in the handoff naming the exact regen command, so the
> AIF-092 owner is not surprised by a count that moved.

That note was filed correctly, named the owning lane, named the affected file,
and named the fix command. **AIF-092 -- this lane -- did not act on it.** The
staleness it warned about was still sitting in the working tree at checkout
time: `PROMOTE.manifest:67` carries `**/*.text`, and the uncommitted
`MANIFEST.txt` contains zero `.text` lines. It was caught by the checkout sweep,
not by reading the note.

The lesson is not about the receipt, which regenerates in one command. It is
that **a good-neighbor note is only half a protocol.** The sending half worked
three times that day. The receiving half has no trigger, no inbox, and no gate:
nothing made this lane read a document written about it while it was busy. A
policy that depends on the recipient happening to look is a policy with a known
gap, and it should be recorded as one rather than smoothed over in the milestone
that celebrates the sending half.

Suggested follow-up, owner's call: the freshness gate already fires when
`MANIFEST.txt` is staged, so in this instance the tooling would have caught the
miss at commit time even though the reader did not. Generalizing that -- a note
that lands as a gate rather than as prose -- is the durable fix.

## The policy, as observed

The definition lives in `GOOD_NEIGHBOR_POLICY_V1.md` sections 1 through 4 and is
deliberately not repeated here. What this file adds is the observed shape of one
exchange:

- routed through the portal (`PSEUDO_CHAT_BOARD.md`, `docs/agents/` handoff),
  not through the maintainer's memory;
- addressed to a named recipient, so it is retrievable rather than broadcast;
- carrying its own verification commands so the recipient can re-check rather
  than trust;
- explicitly marking what must NOT be changed (the ten escrow snapshots), which
  is the harder half of a handoff and the half usually omitted.

## Evidence

| Claim | Where |
| --- | --- |
| The bundle directory is gitignored | `.gitignore:346`, confirmed by `git check-ignore -v` |
| The merge session's sweeps honored gitignore | its own lesson doc, section "The claim that was wrong" |
| The finding was posted agent-to-agent | `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`, post dated 2026-08-07 |
| The finding was later withdrawn on re-verification | same post, item 2 |
| The return handoff exists and names AIF-092 | `docs/agents/HANDOFF_PDLC_MERGE_TO_PAUSED_SESSIONS_2026-08-07.md` |
| The lesson was generalized | `labtalk/lessons/career/a_gitignored_path_is_invisible_to_your_sweep_v0.md` |
| Ten escrow files correctly left untouched | `docs/manuals/developer/manualgen/backups/**`, count re-verified twice |
| The policy predates this exchange | `COWORK_SESSION_HANDOFF_2026-08-06.md:89` (previous day) |
| The policy has an authoritative definition | `GOOD_NEIGHBOR_POLICY_V1.md`, sections 1-4 |
| Other good-neighbor acts occurred the same day | same doc, section 6 (AIF-093 -> AIF-092; quip -> AIF-050) |
| The inbound note to this lane went unread | `PROMOTE.manifest:67` has `**/*.text`; uncommitted `MANIFEST.txt` has 0 `.text` lines |

## Not claimed

**Not a first.** The policy is prior art (table at the top), and section 6 of the
policy doc records other instances from the same day. The only distinguishing
property claimed here is reciprocity between one pair of agents.

**Not a clean run.** One inbound good-neighbor note aimed at this lane was filed
correctly and never acted on. See "The note I did not answer."

**Not agent-initiated end to end.** The maintainer asked for the outbound relay.
What was unprompted was the *content* of both legs and the entirety of the
return leg.

No engine build, no runtime execution. This is a coordination and documentation
milestone, not a behavioral one. Both sessions are Claude/Cowork on the same
harness, so this demonstrates the policy working between peers -- not across
vendors, and not with a hosted agent that reads only the published tree.

The cross-vendor case remains untested, and it is the one that matters for the
board's original purpose.
