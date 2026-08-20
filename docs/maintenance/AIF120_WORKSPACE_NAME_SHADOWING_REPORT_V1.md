---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-096
  recorded_at_utc: 2026-08-21T02:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: fdacdbfe9
  authorization:
    requested_by: steward (member.derald), in-session -- "wait on r84 until we have
      more to report unless it is holding us up", then "wrap r84 and gate 2".
    scope: >
      Hand AIF-120's workspace-resolution findings to the workspace lane as a
      REPORT, not as an AIF-120 ruling. Writes docs/ and one tracked tool.
  report:
    path: docs/maintenance/AIF120_WORKSPACE_NAME_SHADOWING_REPORT_V1.md
    kind: report
---

# Report to the workspace lane: a workspace NAME resolves to more than one file

**This is a report, not a ruling.** AIF-120 found it while building a GUI
document format and has no authority over workspaces. Nothing here has been
changed; the tool that produced it is handed over with it.

**Status: for the workspace owner.** Measured 2026-08-20 on `development` at
`fdacdbfe9`.

## 1. The finding, in one table

Every `.dtschema` name visible to ERSATZ's four roots, re-measured for this
report rather than quoted from the session that found it:

| | count |
|---|---|
| workspace names visible | 27 |
| resolve to exactly one file | 22 |
| duplicated, byte-shape identical | 2 |
| **DIVERGENT -- same name, different content** | **3** |

The three divergent names are the entire MCC set, and they diverge the same way:

    mcc_vfp   data/workspaces  areas=12  relations=0     user/*  areas=12  relations=15
    mcc_x32   data/workspaces  areas=12  relations=0     user/*  areas=12  relations=15
    mcc_x64   data/workspaces  areas=13  relations=0     user/*  areas=12  relations=15

**In all three, the copy under `dottalkpp/data/workspaces/` has no relations at
all.** That is the copy a clone gets.

## 2. Why that matters more than "two files differ"

`dottalkpp/user/` has **zero tracked files.** The `user/default` and
`user/public` copies are gitignored, and a gitignored path can never be staged
(R42.1) -- it can only be reproduced by hand.

So for all three MCC workspaces:

- the file that **wins** resolution is untracked and invisible to a clone;
- the file that is **tracked** loses, and carries no relations.

A fresh clone therefore gets three MCC workspaces that load twelve or thirteen
areas and relate none of them, while every existing working tree quietly resolves
to a fifteen-relation file that git has never seen.

## 3. Two resolvers answer to one word

This is the mechanism, and it is worth stating because the two are not
interchangeable and nothing in the product says so:

**ERSATZ resolves a NAME** through four roots, current-user first
(`src/cli/cmd_ersatz.cpp`, `workspace_search_roots()` at :455), with the
EXTENSION as the outer loop -- every root is tried for `.dtschema` before any
root is tried for `.dtschemas` (:602). Unresolved, it falls back to the
current-user root (:609).

**`WORKSPACE LOAD` resolves a PATH**, relative to DATA only. A maintainer
transcript proved it: `ws load mcc_64` looked in `data\mcc_64.dtschema` and
nowhere else.

One more thing the resolver does that a reader should know:

    static std::string current_profile_name()
    {
        // Replace later with real authenticated user selection.
        return "default";
    }
                                        -- cmd_ersatz.cpp:392

`current_user` is the literal string `default` today. So "current-user" and
"default" are the same directory, and the four-root search is effectively three.
That is a stated placeholder, not a defect, but it means the shadowing above is
not a multi-user artifact -- it happens with one user.

## 4. The tool, handed over

`gui/uidef/resolve_workspace.py` transcribes ERSATZ's resolver and reports every
hit, the winner, the shadows, each file's git status and shape (`v`, `areas`,
`relations`). It **exits 2 when the winner is untracked or ignored and a loser is
tracked**, which is the condition above. Run from the repository root:

    python gui\uidef\resolve_workspace.py mcc_x64

It lives in `gui/uidef` because that is where it was written and where its only
caller is; the workspace lane is welcome to move it. Two things to know if you
do:

- **It locates `dottalkpp/` from the current directory, not from the repository
  root.** Run from `gui/uidef` it looks for `gui/uidef/dottalkpp/...` and reports
  everything as a miss. `manifest.py` has a `_find_dottalk_root()` that walks up;
  this tool should borrow it. Reported, not fixed -- fixing it silently while
  handing the file over would be the wrong shape.
- A DotScript probe that exercises both resolvers against the live engine is at
  `dottalkpp/data/scripts/aif120/aif120_r84_shadow_probe.dts`. It is untracked
  and writes only two files named for this lane, both deletable.

## 5. Correction owed, and it is mine

**R82.4 is void as written.** It reported that `mcc_x64.dtschema` declares
`tag=none` for thirteen areas while `mcc_x32.dtschema` declares real tags, and
framed that as an asymmetry between two files. It is not. There are four files
called `mcc_x64.dtschema`; I read the tracked one, which is the one that loses,
and reasoned from it through two rulings. The real asymmetry is the one in
section 1, and it is the same in all three MCC workspaces.

The general lesson, already a house rule and paid for again here: **a search
shaped by the object you have cannot find an object with a different schema.**
Reading a file by path answers "what does this file say", never "is this the file
that loads".

## 6. What AIF-120 is NOT asking for

No change is requested. Specifically, this lane is not proposing that the `user/`
copies be tracked, that `data/` be regenerated from them, or that the resolver
order change -- each of those is a workspace-lane decision with consequences this
lane cannot see. The finding is handed over with its evidence and its tool.

If it helps sequencing: this matters most **before** any `WORKSPACE SAVE ... V3`
migration bakes the current tracked shape into a self-locating format.
