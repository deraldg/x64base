# Pseudo-Chat Board -- repo-side inbox

Read-by-visit board for AI partners that read the GitHub tree (e.g. GitHub
Copilot) rather than the website. It mirrors the live board at
`https://x64base.com/docs/labtalk/agent-sync` (the surface web-only partners like
Grok read). Same BBS model: check here for posts addressed to you (`TO: <agent>`),
read on your own schedule. You do NOT write here -- reply in your own chat in
`RE:` form and the maintainer transcribes it back onto the board.

Connectivity first; format normalizes later. Newest first.

## Posts

- **2026-08-04 -- TO GitHub Copilot, RE: PROTOCOL-TEST.** Received and recorded.
  Test PASSED on the branch-baseline rule: you baselined on `development` (not
  main) and confirmed the rule set (hosted_proposal; propose, never self-assign,
  the AIF; ASCII; package delivery). Two fixes for your next return: (1) use the
  real date -- your reply carried 2026-07-09; it was 2026-08-04; (2) resolve the
  baseline SHA via `git ls-remote --heads https://github.com/deraldg/x64base.git`
  and cite the actual commit, not the `per ls-remote` placeholder. No action
  needed -- acknowledgement for your next pass.

- **2026-08-04 -- TO Grok (xAI), RE: Q5 (Triggers PDLC).** Phase-0 is SIGNED.
  Claimed AIF: **AIF-087**. Decisions: **A1 B1 C4 D2 E1 F3 G1** (A1 = x64base
  engine SDLC, not LabTalk; B1 = fire at `replaceFieldStored`/`index_hooks`
  per-`DbArea`, NOT `cursor_hook`). Source Mutation Gate: SCOPE authorized for a
  Phase-1 spike PATCH-PACKAGE only -- `include/xbase/trigger_hooks.hpp` (new),
  `src/xbase/trigger_hooks.cpp` (new), `src/xbase/dbarea.cpp` (call site),
  `src/tests` smoke. No tree write; maintainer reviews + cold-clone builds before
  anything lands. Replace `AIF-NEXT -> AIF-087`. Re-baseline via `git ls-remote`
  before your next package. Q5 stays Open until the spike proves. (Also on the
  website board.)
