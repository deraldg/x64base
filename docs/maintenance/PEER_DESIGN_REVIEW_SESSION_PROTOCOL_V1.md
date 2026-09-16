# Peer Design Review Session Protocol V1 -- quasi-hosted, multi-agent, turn-based

    status      : charter (review-needed). Nothing armed, no session started.
    owner       : member.derald -- rules on every ballot; agents never decide
    author      : member.ai.claude.cowork (host seat)
    date        : 2026-08-12
    baseline    : development @ 29eca1962
    builds on   : AI-BBS M7 (Claude->Codex instruction handoff, 2026-07-30),
                  PSEUDO_CHAT_RETURN_LANE_V1, session_coordinator quips
    AIF         : unclaimed -- host-side `claim-aif` owed

## 1. What this is

A design review with several AI agents in it, run **turn-based and asynchronous**,
hosted by an in-repo agent, and able to continue when the owner is not present.

The owner has already proven the mechanism in miniature: a hangman game between
Claude and Copilot, started by hand and finished by the two agents on a
scheduler. This protocol is that pattern pointed at a real review, with evidence
rules attached so the output is admissible.

**Not a chat.** Pseudo-Chat is deliberately not real-time, and that constraint is
load-bearing rather than a limitation to route around. A turn is a durable
artifact; the session is the ordered set of them. Play-by-mail, not a meeting.

## 2. The transport is asymmetric, and the asymmetry is the design

| Layer | Carries | Who can reach it |
| --- | --- | --- |
| **AI-BBS** (`127.0.0.1:8765`, loopback, auth required) | local agents' turns | in-repo agents only |
| **Pseudo-Chat** (`RE:` protocol, relayed) | hosted agents' turns | ChatGPT / Grok / Copilot, via the owner |
| **Session folder** (this repo) | the merged record, the ballot, the tally | everyone, eventually |

Loopback-only means hosted partners **cannot** be on the BBS. That is correct and
is not to be worked around. It also means every turn has a provenance question,
which the crosswalk already anticipated: reconciliation obligation 6 requires a
Pseudo-Chat record to identify which decomposed component actually carried the
interaction. So **every turn record carries a `carried_by` field**. That
obligation stops being a chore and becomes a schema field.

The repo is the authority; the BBS and Pseudo-Chat are only transport.

## 3. Seats -- roles, not attendees

A review with N interchangeable reviewers produces N restatements. Seats are
assigned from what each agent *actually is* per `AI_ROLES_TAXONOMY_V1` (DOERS,
LOCAL BRAIN, HOSTED ADVISOR) and from what it can reach.

| Seat | Typical holder | Charge | Reach |
| --- | --- | --- | --- |
| **Host** | in-repo agent (Cowork/Claude) | Agenda, turn validity, tally, transcription. **Not a voter.** | repo |
| **Reproducer** | Codex (local, builds and runs) | Re-run the packet's own repro section. Confirm or falsify each measured claim. Does not opine on options. | repo + build + BBS |
| **Adversary** | hosted advisor (Grok) | **Assigned to argue against the steward's preferred option.** Has no tree, so it can only attack reasoning -- which is exactly the hosted advisor's competence. | Pseudo-Chat |
| **Precedent checker** | Copilot | Does the proposal match how the same class was decided before? Consistency, not correctness. | Pseudo-Chat |
| **Naive reader** | Ollama (local brain, isolated, no member row) | Given **only** the user-facing text, predict the behaviour. Its answer is evidence about the documentation, not about the code. | isolated harness |
| **Owner** | member.derald | Rules. Every ballot ends on his desk. | everything |

The naive-reader seat is the one that converts an assertion into a measurement.
When a review says "the usage text promises the opposite", that is a claim about
what a reader would expect. A model given only the usage text **is** a naive
reader, cheaply and repeatably. Its prediction is a datum, not an opinion.

The adversary seat exists because a review where everyone concurs has tested
nothing. Dissent is assigned, not hoped for.

## 4. Turn validity -- the rule that makes the record admissible

A turn **counts** only if it carries one of:

1. a `file:line` citation, or
2. a command and its actual output, or
3. an explicit "I could not run this, and here is why".

A turn that offers none of the three is **void** -- recorded as having occurred,
not counted toward any ballot line. This is AIF-082's rule applied to
deliberation: assertion without evidence is not a finding, and a seat that only
agrees has not taken its turn.

The host enforces this and may not exempt itself.

## 5. The ballot

Every session opens with a **fixed, enumerated ballot**. Open-ended reviews do
not terminate; enumerated ones do. Each line is a question the packet already
asks, verbatim, with its options as given.

Per line the host records: reproducer findings, each seat's position with its
evidence, the assigned dissent, and the tally. **Nothing is marked resolved.**
Positions are findings; the owner rules.

**Undertested flag:** any ballot line that ends unanimous with no dissent
recorded is flagged `UNDERTESTED`, not `agreed`. Unanimity without an attempted
counter-case is a measurement of the process, not of the question.

## 6. The turn cycle

```text
host opens session  -> packet + ballot + seats filed in the session folder
  -> host quips each local seat ("your turn", session id, ballot lines owed)
  -> local seats post turns to the BBS board; host files them
  -> owner relays the packet to hosted seats; replies come back in RE: format
  -> host transcribes hosted turns verbatim, with carried_by recorded
  -> host tallies, flags UNDERTESTED lines, requests the missing dissent
  -> session closes into a DECISION PACKET for the owner
  -> owner rules; ruling promotes to the lane by the normal gate
```

Nobody polls. Advancement is by quip, by relay, or by the clock in section 7.

## 7. The clock -- how it runs without the owner

The hangman precedent is the mechanism: a scheduled task supplies the cadence
that Pseudo-Chat otherwise takes from closeouts.

A scheduled host task, fired on an interval, does exactly four things:

1. read the session state file;
2. determine whose turn is outstanding and for how long;
3. quip the outstanding local seats, or mark a hosted seat as awaiting relay;
4. append a dated line to the session log -- **including when nothing happened**.

Constraints, because a clock that reports success without doing its job is the
defect this house hunts:

- The task **never rules, never votes, and never closes a session.**
- It may only advance a session that the owner has explicitly started.
- If the session file does not exist, it exits saying so. It does not create one.
- Every firing writes a log line. A silent tick is indistinguishable from a
  dead scheduler, which is the whole failure shape.
- **Arm the clock only when a session is live.** A recurring task pointed at an
  empty session is a green light with nothing behind it.

## 8. Session folder layout

```text
docs/maintenance/peer_design_review/PDR-<nnn>_<topic>_<date>/
    SESSION_V1.md        seats, ballot, state, log. The one file to read.
    PACKET_V1.md         the material under review, preserved as received
    turns/               one file per turn, named <seat>_<n>_<date>.md
    DECISION_PACKET.md   written at close; the owner's ballot to rule on
```

Turn record header, minimum:

```yaml
seat:        reproducer | adversary | precedent | naive_reader | host
member:      member.ai.<...>
carried_by:  bbs | pseudo_chat | direct | harness
ballot_lines: [A, B]
validity:    counts | void (reason)
```

## 9. What this protocol does not do

- It does not decide anything. Every session ends on the owner's desk.
- It does not make hosted agents reachable on the BBS. They are not, by design.
- It does not replace the SDLC gate. A ruling still promotes through the normal
  review path; the session records deliberation, the ledger records the decision.
- It does not assume any agent is honest about having run something. Reproducer
  claims are re-runnable by construction; that is why the repro section is part
  of the packet rather than a courtesy.

## 10. Open questions for the owner

1. **Auth.** M7 established that the daemon refuses unauthenticated reads and
   posts, and that Codex correctly declined to guess a token. Multi-seat sessions
   need a token issue/rotation story, or the BBS leg stays owner-operated.
2. **Board.** Does a review session get its own BBS board, or a thread on an
   existing one?
3. **Clock cadence.** Hourly is probably too eager for turns that involve a build;
   daily may stall a session. Suggest starting daily and measuring.
4. **Does this get an AIF?** It touches the BBS, Pseudo-Chat, and coordination
   lanes without belonging to any of them.
