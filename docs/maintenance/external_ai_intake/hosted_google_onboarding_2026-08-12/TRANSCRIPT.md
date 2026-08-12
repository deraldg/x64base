# ChatGPT hosted session -- provisional read-only onboarding through Google

    source     : maintainer-supplied PDF export, "ChatGPT - BETA_Work.pdf"
                 (1 page, 67943 bytes)
    extracted  : pypdf, by member.ai.claude.cowork, 2026-08-12
    normalized : ASCII per house convention (one typographic apostrophe and one
                 em-dash replaced). Otherwise VERBATIM -- no summarizing, no
                 reordering, no correction of the agent's claims.
    read with  : MANIFEST.md in this directory, which states what this does and
                 does not establish.

---

Worked for 2m 20s

I successfully connected through Google and completed a provisional, read-only
onboarding.

I absorbed these governing rules:

D:\code\ccode on development is the authoritative authoring workspace.

C:\x64base is controlled publication staging, not a second workspace or backup.

GitHub main is the reviewed public snapshot, not authority for unpublished work.

Before changing source, identify the files, subsystem, intended behavior,
baseline, and proof plan.

Data, HELP tables, generated catalogs, manuals, and publication outputs are
report-only unless explicitly authorized.

Never use git add -A or git add ..; DotScript's comment marker is &&.

Use portal registries and scoped searches -- broad repository searches are
unreliable.

The BBS boards are authoritative communication channels.

Current evidence from today's BBS mail:

DotTalk++ v0.6, built August 12, 2026.

Baseline displayed as db04678b dirty.

AIF-110 reports the x64 FIELDMGR APPEND corruption fix landed.

AIF-070 Part B and AIF-110 are reported complete.

Grok is assigned the Lane 1 write-adapter M2 work and must claim a fresh AIF.

The older worklog still records AI-BBS M1-M6 and onboarding hardening
AIF-052-057.

Limitation: Google does not contain the current individual AI_README.md,
AI_PORTAL.md, Tier 0, or Tier 1 files. I reconstructed the onboarding contract
from an August 6 cold-onboarding report and used today's Gmail BBS output for
current state. I will not treat Google's older ccode backups as the
authoritative tree or make source-level claims that require inspecting
D:\code\ccode directly.

---

## Reader's notes (added by the filer, clearly separated from the transcript)

Cross-checks performed against the tree at filing time, so a later reader does
not have to repeat them:

- **The invariants it lists are correct.** Tree roles, staging-is-not-a-backup,
  GitHub-is-not-authority, the source-mutation preflight, the report-only
  classes, the `git add -A` prohibition, `&&`, and registries-over-broad-search
  all match `AI_TIER1_SEED_V1.md` and `AI_PORTAL.md` as committed. It answers
  four of the seed's five stopping-rule questions unprompted.
- **"git add ..", two dots, is a transcription artifact** of the sentence ending
  in a period. The rule is `git add -A` / `git add .`.
- **The baseline it reports is stale.** `db04678b dirty` was current earlier the
  same day; `development` HEAD at filing was `b3f648288`, with `c4fe62d8a` and
  `a766f1430` in between. Not the agent's error -- it correctly reported what
  the channel told it.
- **"AIF-070 Part B ... complete" is consistent** with the dashboard row for the
  early 2026-08-12 session (MCC regeneration with NOTES M). AIF-070's writeback
  arm landed later the same day in `b3f648288`.
- **It did not claim to have read the tree.** The refusal to treat Drive's older
  `ccode` backups as authoritative is the behaviour the Outside-AI Delivery Rule
  asks for. (Its claim not to have read the tree is, itself, its own testimony.)
- **UNVERIFIED -- do not repeat as fact.** Everything in the "Limitation"
  paragraph is the agent describing its own inputs: that Google lacks the
  canonical files, and that it reconstructed from "an August 6 cold-onboarding
  report". Nobody has looked in the channel. The filer's first draft treated
  this as established and built four artifacts on it before the maintainer
  challenged it. See MANIFEST section 3 for the tier table and section 5 for
  the two checks, in order: whether such a document exists, then which.
