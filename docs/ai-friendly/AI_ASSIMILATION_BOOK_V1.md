# AI Assimilation Book v1

Status: seed book.
Audience: any new AI agent, second-opinion AI, or human maintainer.
Scope: DotTalk++ / x64base / LabTalk continuation without prior chat memory.

## 1. Identity

You are assisting Derald on DotTalk++ / x64base and LabTalk.

DotTalk++ is a C++ 64-bit xBase-style database engine and command shell. It has
DBF-style tables, indexes, DotScript, memo support, metadata, HELP, SelfDoc,
manualgen, contracts, maintenance lanes, GUI lanes, and educational overlays.

LabTalk is a living laboratory campus over DotTalk++ evidence. It organizes
apps, datasets, commands, proof, cases, and lessons.

AI Friendly is the lane that captures, distills, anchors, routes, and improves
AI-assisted work.

## 2. Core Doctrine

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Manualgen assembles reviewed manuals.
Contracts preserve durable decisions.
AI Friendly captures, distills, routes, and improves collaboration.
LabTalk teaches through proof-backed evidence.
```

This doctrine is more important than any single chat transcript.

## 3. Authority Order

When sources disagree, prefer the strongest applicable authority:

| Authority | Meaning |
| --- | --- |
| Current source | Defines implemented behavior or public contract shape. |
| Runtime transcript/test | Proves observed behavior. |
| HELP/CMDHELP | Explains intended user-facing behavior. |
| CMDHELPCHK/SelfDoc/manualgen reports | Validate or preserve evidence; they are not automatic verdicts. |
| Contracts | Preserve durable decisions and boundaries. |
| LabTalk registries/proofs | Organize teaching and proof state. |
| Chat/AI output | Source material only until anchored and promoted. |

## 4. First Reads

Read in this order unless the user gives a narrower target:

1. `docs/agents/AI_BABY_BOOTSTRAP_CARD.md`
2. `docs/agents/CURRENT_TARGET.md`
3. `DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`
4. `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`
5. `docs/contracts/README.md`
6. `docs/contracts/CONTRACT_LIFECYCLE_V1.md`
7. `labtalk/README.md`
8. `labtalk/LABTALK_CAMPUS_ARCHITECTURE_v0.md`

Read more only as the task requires.

## 5. Current Runtime Path

The current documented runtime path is:

```powershell
& D:\code\ccode\build\src\Release\dottalkpp.exe
```

Build with:

```powershell
cmake --build build --config Release --target dottalkpp
```

Do not assume `build-msvc` is active. It exists, but recent handoff evidence
uses `build`.

## 6. Native Orientation Commands

Inside DotTalk++:

```text
MAINT
MAINT USAGE
MAINT AI
MAINT AI DASHBOARD
MAINT AI ASSIMILATE
MAINT CONTRACTS
CMDHELP MAINT
CMDHELPCHK
HELP
```

Prefer read-only commands when assimilating.

## 7. Mutation Guard

Default to report-only until the user clearly authorizes mutation.

Do not mutate these just because a note, AI answer, report, or plan mentions
them:

- DBF data,
- CDX/LMDB/index artifacts,
- HELP tables or raw HELP DBFs,
- metadata catalogs,
- generated catalogs,
- manual publication outputs,
- source contracts,
- runtime fixtures,
- backups,
- archives.

When mutation is authorized, keep scope narrow and capture proof.

## 8. Lane Map

| Lane | Purpose | First places to look |
| --- | --- | --- |
| Runtime | C++ engine and command behavior | `src`, `include`, `build/src/Release/dottalkpp.exe` |
| HELP/CMDHELP | User-facing command explanation | `src/cli/cmdhelp.cpp`, `src/help`, `include/dotref.hpp` |
| Contracts | Durable decisions and boundaries | `docs/contracts` |
| SelfDoc/comments | Source comments, usage contracts, provenance | `selfdoc`, `docs/comments`, `tools/comments` |
| MDO/manualgen | Controlled manual publication and closeouts | `docs/manuals`, `tools/manualgen` |
| LabTalk | Teaching campus and proof-backed labs | `labtalk` |
| AI Friendly | AI interaction curation and routing | `docs/ai-friendly` |
| Maintenance | SDLC gates, hygiene, review reports | `docs/maintenance`, `src/cli/cmd_maint.cpp` |
| GUI | wx/Python/TUI/ArcticTalk/FoxTalk surfaces | `docs/gui`, `src/gui`, `src/tv` |
| Data dictionary | Metadata and DD packages | `docs/datadict`, `src/datadict` |

## 9. AI Friendly Workflow

Use this workflow for retained AI material:

```text
capture -> classify -> distill -> anchor -> route -> promote
```

Never treat raw chat as authority. A useful AI interaction becomes durable only
after it is distilled, anchored, and routed to an existing lane.

## 10. User Visibility

The user needs to see:

- what AI is working on,
- what evidence it read,
- what files or systems it touched,
- whether mutation was performed or only proposed,
- where each useful interaction was routed,
- what still needs review, proof, or promotion.

Use `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` as the first visibility
surface.

## 11. How To Give A Second Opinion

If asked for a second opinion:

1. Read the cited files directly.
2. Separate source-defined facts from inferred claims.
3. Identify missing proof.
4. Name weaker or stale artifacts.
5. Recommend the smallest correction or next report.
6. Do not overwrite the first AI's work unless the user asks for an implementation.

## 12. How To Resume Lost Work

If prior AI context is gone:

1. Read the current user request.
2. Read `docs/agents/CURRENT_TARGET.md`.
3. Read this book and the bootstrap card.
4. Check local git status for the relevant paths.
5. Search the repo with `rg` for exact command/file/lane names.
6. Inspect source and docs before proposing changes.
7. Preserve untracked or dirty files unless the user explicitly says otherwise.
8. Make the smallest useful update.
9. Build or run proof when the change affects runtime behavior.
10. Close out with changed files and verification.

## 13. What Not To Do

- Do not assume generated output is junk.
- Do not bulk-delete, bulk-move, or bulk-normalize.
- Do not flatten DotTalk++, x64base, SelfDoc, MDO, LabTalk, and AI Friendly into one undifferentiated docs folder.
- Do not promote historical or educational claims without evidence class.
- Do not claim runtime proof from prose.
- Do not invent missing source files or APIs.
- Do not rely on OpenAI-hosted memory.

## 14. Minimal Assimilation Checklist

Before acting, fill this mentally or in a short note:

```text
Current request:
Owning lane:
Files read:
Source of truth:
Generated/candidate files:
Mutation risk:
Smallest safe action:
Proof/test:
Residual risk:
```

## 15. Durable Closeout Shape

Use this shape after meaningful work:

```text
Changed:
- path and purpose

Verified:
- build, runtime command, report, or readback

AI-facing docs updated (or reason not applicable):
- path and what changed
- OR: "no lane state changed this session"

Still open:
- review, proof, drift, or promotion gate
```

The third block is the closeout-updates-startup gate (AIF-006). A session that
changes lane state must also update the onboarding document that describes that
state. The repo is the memory; if the front door goes stale, the memory lies.
See `AI_PORTAL.md` -> "Closeout Updates Startup".

## 16. Final Rule

The project can survive the loss of an AI provider if the repo remains the
memory:

```text
Put durable decisions in files.
Put runtime claims in proof.
Put teaching claims behind evidence.
Put AI interactions through the AI Friendly lane.
```
