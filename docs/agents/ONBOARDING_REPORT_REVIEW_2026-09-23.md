# Review: onboarding experience report, re-entry after 43 days (2026-09-23)

    reviewer   : member.ai.claude.cowork, run AIPR-20260920-001
    subject    : onboarding report by the same MEMBER identity, a DIFFERENT
                 session (previously run COWORK-20260811-001), delivered by
                 owner paste 2026-09-23; the reporting session was report-only
                 and filed nothing in-tree
    method     : every checkable claim re-measured in this tree before
                 grading; fixes applied where a finding costs a sentence
    owner ask  : review against the system, with recommendations; note that
                 this system interfaces with the BBS, security, and user
                 commands, and that database and documentation must
                 co-develop, each dogfooding the other

## 1. Verification -- the report survives measurement

| Finding | Re-measured here | Verdict |
|---|---|---|
| B3: Tier 1 read-only git list not marked exhaustive | Confirmed: section 3 listed four commands with no "exhaustive" | TRUE -- FIXED this commit |
| B7: claim files split one member into two by line ending | Confirmed and WIDER: 64 of 99 claim files are CRLF, not just the post-AIF-108 set | TRUE -- .gitattributes rule added this commit; renormalization and consumer \r-stripping recommended below |
| B6: Tier 0 printed "no staleness warnings" over failed inputs | Point-in-time: today's Tier 0 correctly prints "commits behind HEAD: 5" with a warning. The silent-failure path stands as filed (P1, STATE_REFRESH_2026-09-23) | TRUE THEN, not reproducible now -- P1 remains the fix vehicle |
| B4: cached Tier 0 served 45 days stale with no warning | Mechanism confirmed by design (raw.githubusercontent caching); not re-reproducible from the sandbox | CREDIBLE -- AI_README remote-reader note added this commit |
| B1: CLAUDE.md arrives only on mount, after remote reads | Confirmed by architecture (auto-injection on mount) | TRUE -- mount-first line added to AI_README and Tier 1 this commit |
| Section 1: 39 lanes claimed by this member during the gap, none remembered | Claim ledger corroborates the counts; and one fact the report missed: claim files ALREADY carry `run_id` (e.g. AIF-168.claim: run AIPR-20260920-001), so per-run accountability data EXISTS -- only the view is missing | TRUE, and better than reported |
| B8: runs registry misses newer run-id namespaces | ai_runs.yaml is fragment-generated from runs.d/; namespace gap plausible, not re-measured here | UNVERIFIED -- registry sweep recommended |
| G1-G6 | Consistent with this session's own experience (Tier 0, staleness test, commit narrative, durable ledgers) | Concur |

The report's discipline held: nothing it asserted as measured failed
re-measurement, and one claim (B7) was understated.

## 2. Fixed in this commit (each a sentence, per the report's own costing)

- Tier 1 section 3 now says the read-only git list is EXHAUSTIVE, with the
  measured `git diff` case (B3).
- AI_README and Tier 1 open with mount-first: CLAUDE.md arrives on mount and
  supersedes remote reads (B1).
- AI_README warns remote Tier 0 readers about the cache, with the
  cache-buster and ls-remote comparison (B4).
- .gitattributes pins `coordination/aif/*.claim` to LF so new claims cannot
  re-split an identity (B7, forward half).

## 3. Recommendations, in value order

R1. THE MEMBER-IDENTITY FINDING IS THE DEEP ONE, and the data to answer it
already exists. "member.ai.claude.cowork" is one name over many amnesiac
sessions; the ledger holds it accountable for work no live session recalls.
But every claim file carries `run_id`, so the system already distinguishes
the session that did the work from the identity that owns it. What is
missing is only the projection: accountability should READ per-run and
AGGREGATE per-member. No schema change needed -- a view (R2) closes it.

R2. BUILD THE "OPEN FOR THIS MEMBER" VIEW ON THE ENGINE'S OWN SURFACE (B5)
-- this is the owner's dogfooding directive made concrete. Two stages:
  near-term : a generated Tier 0 section or recall trigger
              (trigger.my_open_lanes) listing a member's claims whose lane
              is not closed, each with its newest closeout's still-open
              lines. Generated, never hand-written, like the rest of Tier 0.
  end-state : a runtime verb served by the engine from the shared store --
              e.g. USER OPEN [<member>] or BBS AGENDA -- the way
              board.governance already projects SYSGRANT rows. The identity
              store (SYSMEMBER) models members; the BBS daemon serves the
              loopback API; claims are rows. A returning session then asks
              the DATABASE what its identity left open, through a user
              command, under the same security surface as every other
              member query. The coordination data becomes engine data; the
              documentation system (Tier 0) becomes one consumer of it
              rather than the only home it has.

R3. FILE ONBOARDING REPORTS IN-TREE AS A SERIES. G5 proved the loop closes
(the 08-11 report's finding became AIF-135); this review makes the second
closure. The reporting session filed nothing; the report reached the tree
only because the owner pasted it. The companion file beside this review
preserves it verbatim, and the convention going forward should be: an
onboarding report is a deliverable, filed under docs/agents/, and reviewed
the way this one was. The report series is itself the portal's regression
suite -- each re-entry measures what the last set of fixes bought.

R4. B7's BACK HALF NEEDS AN OWNER RULING: `git add --renormalize
coordination/aif/` converts the 64 CRLF files in one commit (blame churn,
one-time) versus leaving them and requiring every consumer to strip \r
(session_coordinator.py, aif_collision_gate.py -- one line each, and the
collision gate could WARN on a CRLF claim). Recommend both: normalize once,
and harden the consumers anyway, because the next CRLF file will arrive
from some Windows editor regardless.

R5. B6/B8 ARE TOOL LANES, NOT SENTENCES: Tier 0's generator should print
its own age and refuse to claim "no staleness warnings" when any input
failed (P1 already filed); the runs registry needs a namespace sweep before
anyone trusts it for "which runs are mine". Neither blocks re-entry today;
both lower trust in the artifacts that DO work, which is the expensive kind
of defect.

R6. B2 (the projects walk that nothing prompts) resists a doc fix by
definition -- the reporter had the instruction and did not follow it, and
said so honestly. The structural options: Tier 0 could print the five-step
walk as its closing checklist (the one artifact every session reads), or
the closeout contract could require naming which steps of the walk ran.
Recommend the Tier 0 checklist: it puts the prompt inside the artifact
that G1 proves gets read. The reporter's owed search-map row remains owed.

## 4. What this review owes

The search-map rows for this review's own scans (claim-file line-ending
census, gitattributes read, Tier 0 header read) are folded into the
PORTAL_SEARCH_MAP row cited in this commit's message rather than repeated
here.
