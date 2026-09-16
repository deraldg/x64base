# PDR-001 -- WORKSPACE OPEN scanner and WRITEBACK backup placement

    status      : DRAFTED, NOT STARTED. No seat has been notified. No clock armed.
    opened_by   : member.ai.claude.cowork (host seat)
    date        : 2026-08-12
    protocol    : docs/maintenance/PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1.md
    packet      : docs/maintenance/PEER_REVIEW_WORKSPACE_SCANNER_AND_WBAK_PLACEMENT_V1.md
    lane        : AIF-070 (coworker); ballot line L5 asks whether it needs its own
    owner       : member.derald -- rules every line; no seat decides

The packet is **not copied here**. It is already in the tree and that copy is
authoritative. A session folder holding a second copy would be the duplication
this house treats as a defect.

## 0. The host is conflicted, and says so first

`member.ai.claude.cowork` authored the packet under review. It therefore takes
the **host seat only** and is `conflicted_abstain` on every ballot line. It runs
the session, enforces turn validity, and tallies. It does not argue a position,
and it may not break a tie.

This is the independence rule binding its own author, which is the only way that
rule means anything.

## 1. Ballot

Verbatim from the packet's section 8. Options are the packet's, not the host's.

| # | Line | Options | State |
| --- | --- | --- | --- |
| L1 | Backups admitted as tables by the scanner | A1 filter in scanner / A2 sibling dir / A3 TMP-rooted / A4 A1+A2-or-A3 | open |
| L2 | `WORKSPACE OPEN <dir>` resolves CWD-relative, fails silently | B1 route through `paths::resolve_in_slot` + loud miss / B2 loud miss only / B3 document it. **Plus:** does B ride with A or land separately? | open |
| L3 | Retention contract for `.__wbak` | is depth-one-kept-forever intended? if not: expiry, depth, or a "previous backup discarded" notice | open |
| L4 | `workspace_wbak_scan.dts` | registered regression / unregistered candidate / folded into `workspace_writeback.dts` | open |
| L5 | Numbering | own AIF, or stays under AIF-070 | open |

**Undertested rule:** any line closing unanimous with no recorded dissent is
flagged `UNDERTESTED`, not agreed.

## 2. Seats and their charges

Each seat is charged with work only it can do. No seat is asked for a general
opinion.

### Reproducer -- Codex (local; builds and runs)

Confirm or falsify. **Do not opine on options.**

| # | Task | Bears on |
| --- | --- | --- |
| R1 | `REGRESSION RUN WORKSPACE_WRITEBACK` -- 12 markers | baseline |
| R2 | `dottalkpp --script data/scripts/workspace_wbak_scan.dts` -- 4 markers; and confirm 26 areas opened against a posture declaring 13 | L1 |
| R3 | **Confirm the index attachment.** Does `ROOMS.__wbak.dbf` really attach `ROOMS.cdx`? | L1 severity |
| R4 | From a cwd that is **not** DATA: `WORKSPACE OPEN DBF/x64` (expect 0, silent) vs `WORKSPACE OPEN DBF` (expect 14). **State the OS** -- Windows cannot discriminate, since `datarun.ps1` sets cwd = DATA | L2 |
| R5 | Retention census: three writebacks, look for `*.__wbak.__wbak.*` (expect absent), read the sentinel (expect last generation only) | L3 |

**R3 is the load-bearing one.** If the index does not attach, L1 drops from
"silent wrong ordering, the house's most-hunted failure shape" to "clutter in the
area list", and the urgency of L1 changes with it. It is the single claim most
worth attacking.

### Naive reader -- Ollama (isolated local brain; no member row, no tree)

Given **only** the `WORKSPACE OPEN` usage text and the live SETPATH slot list --
no source, no packet, no options:

- **N1.** What does `WORKSPACE OPEN DBF/x64` resolve against?
- **N2.** If it matches nothing, do you expect output?

The packet asserts "the runtime usage text already promises the opposite." That
is a claim about what a reader would expect. A model given only the text **is** a
reader, cheaply and repeatably. N1/N2 convert the assertion into evidence.
Its answers are data about the documentation, not about the code, and are not a
vote.

### Adversary -- Grok (hosted advisor; no tree, by design)

**Assigned to argue against the steward's preference.** The packet prefers A4 and
leans B1; this seat makes the strongest available case for A1-alone or A3-alone,
and for B2 or B3. Specifically required to attack:

- whether relocating backups (A2/A3) trades a **known** defect for an
  **unmeasured** recovery risk -- the packet concedes a swept TMP takes the undo
  with it;
- whether A1's own stated objection (encoding a naming convention into the
  scanner) is disqualifying rather than acceptable;
- **the packet's one unmeasured claim**: that B1 "changes behaviour for any caller
  relying on CWD-relative today". Nobody has counted those callers. An adversary
  with no tree can still notice that nobody counted.

Must produce at least one falsifiable objection. Agreement is not a turn.

### Precedent checker -- Copilot

- **P1.** Does B1 match how `5a4f9b3ec` treated the other four surfaces
  (`WORKSPACE WRITEBACK TO`, `ERASE DIR`, `FILE()`)? Is a fifth surface on a
  different rule defensible?
- **P2.** Prior art for suffix-filtering inside a scanner anywhere in this tree --
  and how did it age? This tests A1's stated objection against history rather
  than intuition.
- **P3.** Does the house already have an expiry or sweep mechanism for TMP that
  L3 could reuse instead of inventing one?

## 3. Transport per seat

| Seat | Carried by | Note |
| --- | --- | --- |
| Reproducer | `bbs` | loopback, auth required; owner issues the token |
| Naive reader | `harness` | isolated; no member row, correctly |
| Adversary | `pseudo_chat` | hosted; relayed by the owner in `RE:` format |
| Precedent | `pseudo_chat` | hosted; relayed |
| Host | `direct` | in-repo |

Every filed turn records `carried_by`, satisfying crosswalk reconciliation
obligation 6 by schema rather than by remembering.

## 4. Turn validity

A turn counts only with a `file:line`, a command plus its real output, or an
explicit "could not run, because". Anything else is filed and marked `void`.
The host does not exempt itself.

## 5. State

    session state : NOT STARTED
    turns filed   : 0
    lines closed  : 0 of 5
    clock         : NOT ARMED

### Log

- 2026-08-12 -- session drafted by the host. Nothing notified, nothing armed.
  Awaiting the owner's three starts in section 6.

## 6. What the owner has to do to start it

Three things, none of which a sandbox agent can do:

1. **Bring the BBS up and issue the reproducer a token.** M7 established the
   daemon refuses unauthenticated reads and posts, and that Codex correctly
   declined to guess one. That behaviour is a feature and it means the BBS leg
   starts with you.
2. **Relay the packet to the hosted seats** (Grok as adversary, Copilot as
   precedent), with their charges from section 2.
3. **Say the word to arm the clock.** The host can create the scheduled task that
   pokes outstanding seats and appends a log line on every firing -- including
   firings where nothing happened, so a dead scheduler cannot look like a quiet
   one. It will not be armed against a session that has not started, because a
   recurring task pointed at an empty session is a green light with nothing
   behind it.

Also owed host-side: `claim-aif` for this protocol, if L5 or the protocol itself
gets a number.

## 7. Close condition

The session closes when every line has: at least one reproducer-verified fact or
an explicit "not verifiable and why", at least one recorded dissent or an
`UNDERTESTED` flag, and the host's tally. Output is `DECISION_PACKET.md` -- five
lines, each with positions and evidence, for the owner to rule on.

No line is ever marked resolved by this session. Deliberation is recorded here;
the decision is recorded in the ledger, by the owner, through the normal gate.
