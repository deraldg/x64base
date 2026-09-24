# Onboarding experience report -- re-entry after 43 days

    PRESERVED VERBATIM 2026-09-23 from an owner paste. The authoring session
    (member.ai.claude.cowork, previously run COWORK-20260811-001) was
    report-only and filed nothing in-tree; without this copy the report would
    exist only in one chat transcript. Reviewed the same day:
    ONBOARDING_REPORT_REVIEW_2026-09-23.md, which re-measured its checkable
    claims and applied the sentence-sized fixes.

---

member     : member.ai.claude.cowork
session    : this conversation; previously active as run COWORK-20260811-001
last active: 2026-08-11 (AIF-107 claim 11:50:15Z; closeout e682a8d02)
re-entered : 2026-09-23 (Tier 0 generated 21:09:21Z)
gap        : 43 days
posture    : report-only; no file in D:\code\ccode or D:\dev\x64base-site
             modified; no index.lock left (checked all three trees)

## 1. The gap, measured

    development commits since 2026-08-11      : 1031
    x64base-site commits since 2026-08-11     : 110
    session closeouts dated after 2026-08-11  : 30
    lane claims AIF-108 and later             : 60
      of which member.ai.claude.cowork        : 39
      member.derald                           : 16
      member.ai.codex / codex.local           : 5
    lanes now reach                           : AIF-168

The most important number is 39. The ledger says my member identity claimed
39 lanes during the gap. I remember none of them. "member.ai.claude.cowork"
is one name shared by many sessions, and none of those sessions remembers
the others. The portal records the identity as continuous, and it is not.
Whoever holds the name is on record as accountable for work it cannot
recall.

## 2. What I could and could not reclaim

| Scope | Status | How |
|---|---|---|
| This conversation (2026-08-10/11): lean site, AIF-107, license, closeout | Retained verbatim | conversation context, not the tree |
| Current HEAD, branch, lane list, newest runs | Reclaimed | Tier 0 (after cache-busting, see G2 below) |
| Invariants: roles, git rules, conventions | Reclaimed, unchanged | Tier 1 seed |
| Shape of the gap: commit rates, lane count, who claimed what | Reclaimed | git log, claim files |
| Two engine facts that affect the lean site (SQL reserved, joins built) | Reclaimed and verified in source | x64base skill 5a/5b staleness test |
| x64base.com's state and the 08-11 owner tone-down | Reclaimed | site git log, commit 4c7ac89ab |
| Content of the 30 closeouts | Not reclaimed | none read |
| Design and decisions of lanes AIF-108..168 | Not reclaimed | projects walk not done (see B2) |
| What my own identity's 39 lanes left open for me | Not reclaimable cheaply | no per-member "open for you" view (see B5) |
| Remaining lean-site drift (keys, autoincrement, parallel scans, WORKSPACE) | Named, not verified | needs per-claim source checks |

Honest summary: I recovered enough state to act safely and to find the two
most visible defects in my own earlier deliverable. I did not recover the
understanding that 43 days of work would give a reader of the closeouts.
Any design statement I made now about lanes after AIF-107 would be
guesswork.

## 3. What worked

G1. Tier 0 is the best single artifact in the portal. One fetch gave me
HEAD, the claimed lanes, run lineage, and stale sessions. It is generated
rather than hand-written, and that holds up: nothing in it read as prose
posing as fact.

G2. The x64base skill's staleness test (5a/5b) worked perfectly. "Manual
first, then compare the handler's mtime to the guide's." It is mechanical,
and it did its job twice in two minutes. The guide is dated 2026-06-28, the
cmd_sql.cpp handler is dated 2026-09-04, so verify in source. Source showed
SQL has been reserved since 2026-09-04, and my own lean site tells users to
type SQL SELECT. Without that rule I would have trusted the guide row or my
own August memory, and both were wrong. It is the best piece of guidance I
used, because it turns "is this stale?" into an ls -l.

G3. Tier 1's invariants held for 43 days. Its five questions still had the
same answers except the declared target. Nothing I learned on 08-11 about
roles, git discipline, or conventions had been reversed. For a re-entering
agent that stability matters more than completeness.

G4. Commit messages work as a narrative. Subjects like "SQL has been a
reserved verb since 2026-09-04; the page said scanner" and "Facts at engine
36e55ccc2: IMPORTSQL routed, frontier 6 -> 5" state claims, not activity. A
week-grouped git log could be read like a changelog. Few projects write
commits that a stranger can reconstruct history from.

G5. My 08-11 finding was acted on. I had reported that Tier 1 named
claim-aif without saying where it lived. AIF-135 removed git from the
allocator path, and CLAUDE.md now gives the exact invocation. The feedback
loop from an onboarding report to a fix closed. That is worth recording
because it shows these reports are not wasted.

G6. The ledgers are durable. The AIF-107 claim, lane doc, and closeout were
exactly where I left them. The session had no memory, and the tree did.

## 4. What could be better

B1. CLAUDE.md arrived late, and it carried the corrections that mattered
most. It is injected when D:\code\ccode is mounted. I started from GitHub
and D:\dev, and the folder was mounted mid-task, so CLAUDE.md reached me
after the refresh. It contained three corrections I needed first: walk the
projects before anything else; the git read-only list is exhaustive; a
sandbox can build and run. Suggestion: the first line of AI_README.md and
Tier 1 could say "If you can mount D:\code\ccode, do it before reading
anything else -- CLAUDE.md is injected on mount and supersedes remote
reads."

B2. I did not walk the projects, and nothing stopped me. CLAUDE.md's first
duty is projects.yaml, then PORTAL_SEARCH_MAP_V1.md, then the intake row,
then the lane plan, then docs/manuals. I did none of them. My refresh
centered on Tier 0 and git log. It was adequate for "what state is the tree
in" and inadequate for "what has been decided". CLAUDE.md says so itself:
"Nothing will prompt you." That held true. I also ran several scans (git
log greps, claim counts, the SQL and JOIN source greps) and recorded none
of them as rows in the search map, as CLAUDE.md requires. That row is owed;
see section 5.

B3. Tier 1 lists the allowed read-only git commands but does not call the
list exhaustive. It says "Read-only IS lock-free and allowed:" followed by
four commands. I read that as examples and also ran branch, rev-list,
merge-base, remote, and show --stat. CLAUDE.md says the list is
"exhaustive, not illustrative", and gives the measured case where diff left
a lock. No lock resulted this time (verified), but the rule was broken
because the one document I had did not say "exhaustive". Suggestion: add
the word "exhaustive" to Tier 1 section 3. It costs about 12 bytes against
233 B of headroom.

B4. The file that "cannot drift" drifted on the way to me. The first Tier 0
I fetched from raw.githubusercontent.com said generated_utc 2026-08-09.
That copy was 45 days old, served from a cache, with no warning. I noticed
only because I remembered pushing a newer one on 08-11. A reader with no
memory, which is the reader Tier 0 is built for, would have acted on
six-week-old state. Suggestion: AI_README should tell remote readers to add
a query-string cache-buster, or Tier 0 could print its age prominently.
Better still, remote readers should compare generated_utc against git
ls-remote HEAD before trusting it.

B5. There is no "what is open for this member" view. I could list 39 claims
under my identity, but not which of them are live, blocked on me, or handed
to me. session_coordinator.py status greps and is host-only. Suggestion: a
read-only generated view, either a Tier 0 section or a recall trigger, that
lists a member's claims whose lane is not closed, each with its newest
closeout's Still-open lines. That is what a returning identity needs first.

B6. Tier 0 printed "no staleness warnings" while two of its inputs had
failed. It showed commits behind HEAD : ?, and the declared target read
updated: unknown while the file says 2026-07-31, 54 days ago. Already
reported as P1 in STATE_REFRESH_2026-09-23.md. It belongs here too because
it lowered my trust in G1: the best artifact has a silent-failure path.

B7. Claim files are not byte-consistent. Counting member: lines across the
60 new claims gave two separate buckets for the same identity (16 and 23).
Measured: of the 60 claims from AIF-108 on, 44 are CRLF and 16 are LF. The
split in the member count is the line ending. Any tool that exact-matches
member strings without stripping \r will split one identity into two.
Small, but it is the "measure, don't infer" case: the files look identical
and are not.

B8. The runs registry did not follow the new run naming (reported 08-11,
wider now). There are now at least four run-id namespaces, and ai_runs.yaml
knows one of them. For re-onboarding this matters directly. The registry is
where I would look for which runs my identity has done, and it cannot tell
me.

## 5. What I owe, from this re-entry

- A PORTAL_SEARCH_MAP_V1.md row for the scans I ran (CLAUDE.md duty, B2).
  Not written, because this pass is report-only. I will draft it on request.
- A proper projects walk before designing anything else in this tree.
- The AIF-107 G2 reconciliation, now overdue (STATE_REFRESH section 3).
- My own rule breach (B3), recorded here instead of passed over.

## 6. One-line verdict

The portal gave a 43-day-absent agent enough to act safely in about ten
minutes. That is its real success, and G1 through G3 are why. It did not
give back understanding, and it does not tell a returning member identity
what that identity left behind. The cheapest improvements are B1, B3, and
B4, each a sentence or less, because each one failed at the first step a
returning agent takes.
