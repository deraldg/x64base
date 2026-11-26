# Review: Codex onboarding report, and catch-up brief for Codex (2026-11-25)

    reviewer   : member.ai.claude (project thread, Claude Code remote)
    subject    : onboarding review by member.ai.codex, delivered by owner paste
                 2026-11-25 (~18:45Z); report-only, filed nothing in-tree
    method     : every checkable claim re-measured in D:\code\ccode, C:\x64base
                 and `git ls-remote` against GitHub, 2026-11-25 ~23:00Z
    platform   : Python scripts were run with Linux python3.10 over a mounted
                 copy of the tree, not .venv312 on Windows (see sec 4 caveat)
    AUTHORIZATION: owner asked to "evaluate the evaluation and bring codex up to
                 date". Evaluation and this brief only. No bug fixed, nothing
                 committed, nothing pushed.

## 1. Verdict on the four claims -- all four still true

| # | Claim | Status | Evidence |
| --- | --- | --- | --- |
| 1 | GitHub `main` gives two directions: AI_PORTAL redirects to `development`, AI_README still says "THIS FILE IS THE ONE FRONT DOOR" and sends you to `labtalk/ai_portal/AI_TIER1_SEED_V1.md`, absent on `main` | **Still true** | `main` was republished today (6b3cd158e, 10:28 PST, "credit Codex") and the README text is unchanged. `git cat-file -e origin/main:<path>`: seed N, Agent Laws seed N, Assimilation Portal N, Bootstrap Card N; CURRENT_TARGET Y, labtalk/ai_portal/README Y. |
| 2a | Refresh wrapper reports 7/10; Tier 0, identifier status, feed status stale | **Still true** | `refresh_portal_state.py --check` -> `7/10 ... failed: tier-0 state, identifier status, feed status`. All three say `stale` (projection older than inputs), i.e. a write-refresh was not run, not a logic failure. Tier 0 also warns 4110 B > 4096 B target. |
| 2b | Truth audit marked PASS while it found 203 missing paths | **Still true, and structural** | `labtalk/portal/labtalk_portal.py main()` returns 0 for `--audit` unconditionally unless it throws; `missing_paths` never sets the exit code. The wrapper's PASS means "did not crash". Last Windows-written report `labtalk/reports/portal/portal_truth_audit_latest.md` (2026-10-12) says 203 missing; matches Codex. |
| 2c | Mandatory-file checker drops nonexistent paths before checking | **Still true** | `check_mandatory_tracked.py` ~line 122: `docs = {f for f in docs if (root/f).is_file()}` and the same for scripts. `AI_README.md` line 656 tells you to run `.\run-wx.ps1`; no root file exists (only `labtalk/aops/run-wx.ps1`). Gate PASSes. The file's own comment documents this same failure mode from 2026-07-31. |
| 3 | "Newest closeout" can point backward; selector compares the filename date and breaks ties by path | **Still true** | `generate_tier0_state.py newest_closeout()` = `max((date_from_name, path))`. Picks `..._AIF171_PHASE8_REPAIR_PLAN_2026-10-15.md` (recorded_at_utc 16:05:02Z); the real tail is `..._AIF171_PHASE8_M4_APPLY_M5_REMEASURE_2026-10-15.md` (18:02:38Z). Both untracked. Committed TIER0_STATE.md already says the selected file "is in no commit". |
| 4 | AI Friendly README and recall reopen old paths; validator can't catch routing | **Still true** | `docs/ai-friendly/README.md` First Reads starts with `AI_ASSIMILATION_PORTAL_V1.md`, `AI_ASSIMILATION_BOOK_V1.md`. `recall.py onboard`: 14 nodes, 113116 B, includes "AI Baby Bootstrap Card (demoted)"; `entry_path` in `portal_recall_graph.yaml` is TIER0 + Tier1 seed only, so its "2 files, 13188 B" baseline omits `AI_AGENT_LAWS_SEED_V1.md`, which AI_README step 0b makes mandatory. `recall.py "review an existing lane"` -> `trigger.open_lane`, exit 0 (it does print "ambiguous ... Also matched: release_or_license" -- a warning, not a refusal). |

Codex's recommended order (entry route and readiness checks first, then
lane-specific, timestamp-based handoff selection) stands.

## 2. What Codex missed because its view was stale

1. **Published `development` does not contain Codex's own latest work.**
   `git ls-remote`: GitHub `development` = e9a20b674 (2026-10-22, R152).
   Local `D:\code\ccode` is 4 commits ahead and unpushed: 9d149820f + eef247ce4
   (AIF-173 repeatable demos, Cowork, 10-22), **e6de8233f (AIF-174, Codex,
   11-21)**, 8fcab4427 (README contributor credits, today). A "published
   development" comparison cannot see AIF-174. Also: `D:\code\ccode`'s
   `origin/main` ref is stale (48107537d, 09-13); GitHub `main` is 6b3cd158e.
   Fetch from the sandbox is blocked, so use `git ls-remote` rather than the
   local remote-tracking refs.
2. **The real newest handoff is not a `SESSION_CLOSEOUT_*` file.** AIF-174's
   handoff is `docs/maintenance/AIF174_GOOD_NEIGHBOR_CLOSEOUT_V1.md` (11-21,
   committed locally). The selector's glob can never find it. Nothing after
   10-15 is named `SESSION_CLOSEOUT_*`, so "newest closeout" is five weeks and two
   lanes behind, not just two hours.
3. **AIF-174 is a number collision.** `docs/maintenance/AIF174_COMMAND_PROVENANCE_SEARCH_LIMITER_LANE_V1.md`
   (Cowork steward, untracked, written 11-14) says it was allocated AIF-174 by
   `next_aif.py` and "NOT YET CLAIMED". Codex claimed AIF-174 on 11-21 for
   regression process groups (`coordination/aif/AIF-174.claim`). Same thing
   that happened to AIF-170 on 10-12, which that charter itself records. The
   charter needs a new number; it is the Cowork lane's to renumber, not Codex's.
4. **The shared tree is much dirtier than a plain status shows.** This repo sets
   `status.showUntrackedFiles=no`. `git --no-optional-locks status --porcelain -uall`:
   237 modified, **7,567 untracked**, of which 57 sit directly in
   `docs/maintenance/` and 18 are `SESSION_CLOSEOUT_*`. 17 of those 18 are the
   AIF-171 Phase 8 closeouts -- Codex's own lane's record that never landed.
5. **Uncommitted edit to the Tier 1 seed, today 18:31Z.** `AI_TIER1_SEED_V1.md`
   gains a rule: commits containing Codex work carry
   `Co-authored-by: Codex <codex@openai.com>`. Not committed yet; follow it.

## 3. Catch-up brief for Codex -- which handoff to pick up

No single controlling lane (CURRENT_TARGET, owner ruling 2026-07-31). The owner
picks. Codex's own open tails, in the order they cost least:

1. **AIF-174 (yours, 11-21)** -- read `AIF174_GOOD_NEIGHBOR_CLOSEOUT_V1.md`,
   `AIF174_REGRESSION_PROCESS_GROUPS_V1.md`, `AIF174_REGRESSION_VERIFICATION.json`.
   Open: commit e6de8233f is unpushed; PKDURABLE never ran (member.ai.regression
   has no live `host.shell` grant -- a prerequisite, not a pass);
   WORKSPACE_PERSISTENCE inspected, not run; generated HELP tables and manual
   catalogs still owe their governed refresh.
2. **AIF-171 (yours, 10-13)** -- the true tail is
   `SESSION_CLOSEOUT_AIF171_PHASE8_M4_APPLY_M5_REMEASURE_2026-10-15.md`
   (18:02:38Z), not the 16:05Z repair plan Tier 0 names. 17 Phase 8 closeouts are
   untracked; landing them needs owner say-so and a scoped commit.
3. **The four findings above**, if the owner wants them fixed (none fixed yet):
   entry route on `main`; audit exit code and the mandatory-file filter;
   selector by `recorded_at_utc` per lane, including non-`SESSION_CLOSEOUT`
   handoffs; AI Friendly first reads and recall `entry_path` (add Agent Laws,
   drop the demoted card).

## 4. Which checks to trust

| Check | Trust | Do instead |
| --- | --- | --- |
| `refresh_portal_state.py --check` FAIL lines | Yes | -- |
| its "Portal truth audit" PASS | **No** (exit 0 always) | read `missing_paths=` in the summary line |
| "mandatory tracked onboarding" PASS | **No** for missing files | grep the entry docs for paths and `test -e` each |
| Tier 0 "Newest closeout" | **No** | read `recorded_at_utc` in the lane's closeouts; also look for `AIF<n>_*CLOSEOUT*` |
| `recall.py` "entry path" baseline | **No** (omits Agent Laws) | AI_README steps 0 and 0b |
| `git status` (plain) | **No** (hides untracked, takes the index lock in a mounted sandbox) | `git --no-optional-locks status --porcelain -uall` |
| local `origin/*` refs | **No** (fetch blocked; refs are weeks old) | `git ls-remote --heads https://github.com/deraldg/x64base.git` |
| graph validator PASS | Structure only | not evidence of correct routing |

Caveat on my own numbers: run on Linux over a mount, the truth audit reports
`missing_paths=656`, versus 203 in the last Windows run. Path normalization and
case sensitivity differ, so trust the Windows `.venv312` count, not mine.
Also: before reading the seed's sandbox rule, this review ran plain `git status`
four times over the mount. `.git/index.lock` was checked afterwards and is absent.
