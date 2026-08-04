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
