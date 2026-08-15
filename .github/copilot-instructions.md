# x64base repository -- branch baseline (READ FIRST)

- **Baseline branch:** enumerate published branches before choosing one -- run `git ls-remote --heads https://github.com/deraldg/x64base.git`. Do NOT default to `main`.
- `main` is a **lagging public snapshot**, not the authority for active work.
- `development` is **also published on GitHub** and is the **richer, current** integration branch -- baseline all feature, source, and prior-art work on `development` and record its exact commit. Use `main` only if the maintainer names it for the task.
- "Confirm the branch; do not hard-code a transient name" means **discover** the branch, not assume `main`. Building against `main` without enumerating branches is a hard onboarding failure (observed 2026-08). If you cannot reconcile against `development`, say so and mark the work provisional -- never claim `main` == authority.
- Full onboarding authority: `AI_README.md`, `AI_PORTAL.md` ("Outside-AI Delivery Rule"), `labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`.
- **AI board / your inbox:** messages addressed to you are posted at `docs/ai-friendly/PSEUDO_CHAT_BOARD.md` (repo-side mirror of the website Pseudo-Chat board). Read it each visit for `TO: <you>` posts; reply in your own chat in `RE:` form for the maintainer to transcribe. Do not write to the board yourself.

- @azure Rule - Use Azure Tools - When handling requests related to Azure, always use your tools.
- @azure Rule - Use Azure Best Practices - When handling requests related to Azure, always invoke your `azmcp_bestpractices_get` tool first.
- @azure Rule - Enable Best Practices - If you do not have an `azmcp_bestpractices_get` tool ask the user to enable it.

## Coding agent -- house rules for autonomous PRs

You run on GitHub Actions and open a pull request. Follow the coordination protocol or the PR is
rejected at the gate.

- **Branch:** baseline and open the PR against `development`, never `main` (see the branch baseline
  above).
- **AIF lane:** every change belongs to an AIF lane. If the issue names an AIF number, cite it in
  the PR title and body. Do not invent a number; if none is given, keep the change coordination-only
  and state that a claim is owed.
- **Scope:** change ONLY the files the task requires. Never `git add -A`. One lane per PR. Unrelated
  churn fails review.
- **Gates you must pass:** the pre-push gate (`tools/staging/prepush_gate.py`) runs the AIF-collision
  gate, the AIF-082 portal gates, house-style (ASCII only -- NO em-dashes or non-ASCII in added
  documentation lines; use `--` and `->`), and mandatory-tracked. Do not add build trees or binaries.
- **Build + test (Ubuntu):** prerequisites are installed by
  `.github/workflows/copilot-setup-steps.yml`. Configure, build, and `ctest` with the project CMake
  presets exactly as the `ubuntu-core` job in `.github/workflows/ci.yml` does. Do not claim a green
  you did not run.
- **Verify before you rely:** the recurring defect here is code that reports success without doing
  its job (attribution written as zero; a consumer committed without its definition; a doc claimed
  present but untracked). Prove the change with a test or a measured run, not a success message, and
  confirm every new file is tracked.
- **House style:** ASCII only, no em-dashes; terse docs; author docs as review-needed.
