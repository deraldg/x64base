# Cowork session handoff -- 2026-08-06

Author: `member.ai.claude.cowork` (sandbox; no git mutation, commits handed off).
Owner: `member.derald`. Scope: a long multi-lane Cowork session spanning
`D:\code\ccode` and `D:\dev\x64base-site`. This is a rollup + open-item handoff, not
an `ai_report_audit` closeout (left un-gated on purpose). Self-documenting artifacts
carry the detail; this ties them together.

## Landed in ccode (development)

- **AI BBS M4.x (design phase complete):** M4.1 per-session identity design
  (`ac6bb1f6a`), M4.2 Ollama-agent design + egress wording fix + runsheet
  (`07ccec3f6`), M4.1 patch spec (`325e148f7`), M4.2 patch spec (`3402c2825`), lane
  pointer (`0df21d88a`). All design-only; anchors verified vs source.
- **Tree hygiene / dev-build hardening:** `.mdb` hard-blocked at prepush gate +
  `*.bak-` ignore (`0b69162c6`); triage classifier (`13ddecc58`); disposition ruling
  = ignore only `.mdb`, let all other dottalk types through, keep proof, defer `.csv`
  (`9e5e391e6`); scratch-sidecar mover + fix (`5d6d4213c`, `300a8974b`).
- **Untracked source recovered:** `schema_inventory_main.cpp` coherence fix
  (`7c755ec70`), TRANSACTION source (`b4b2359d8`), pydottalk tooling (`5e40eada0`),
  tools/schemas (`87fbf2e4a`).
- **Onboarding truths recorded where read:** sandbox may run read-only lock-free git
  (`0a79f9f83`); GPTbase derived bundle generator + flush wiring (`02d893997`,
  `650d27ec6`); truth review + Tier 1 seed edits (`a8b780e81`, `56c87f83a`);
  Phase 9 added to the flush ladder (`d897546c4`).

## Landed in x64base-site (codex/lean-sites-publish)

- Local-preview 404 fix (trailing-slash links) + live-site banner link
  (`e511add3b`); per-section metadata titles (`bfb9675c5`); current announcements x5
  (`0ccbe2ea8`, `c4d62fa23`); matrix kept current + made first onboarding read +
  AIF-032 harvest drift audited (`5e0cfe827`).

## Handed off, NOT yet committed (maintainer, on a clean tree)

- **Line-ending policy rewrite** in both repos' root `.gitattributes` (site =
  LF-everywhere with `source-lineage/** -text` guard; ccode = source LF, Windows
  tooling CRLF, proof logs binary). Apply once per repo: `git config core.autocrlf
  false` then `git add --renormalize .` as its own commit, on a clean tree. Site:
  `git checkout -- public/artifacts/source-lineage/` first (restore SHA-bound bytes).

## Open follow-ups (host-side; not doable from the sandbox)

1. **M4.x build + prove.** Run the runsheet: M4.1 (thread_local + bounded workers)
   build+prove, then M4.2 (seed `member.ai.ollama.local` + harness). Two rulings:
   harness home; owner-poked vs board-polled. `AI_BBS_M4X_BUILD_RUNSHEET_V1.md`.
2. **AIF-032 harvest drift.** Reconcile the command count in source (236 vs 243 vs
   212 vs 237), then regenerate the harvest diagram + Command/Function Catalog pages
   via the fullstack push (README `command_catalog_sync.py`); do not hand-edit.
3. **Line-ending renormalize** (item above), per repo.
4. **Tier 1 seed over budget:** `AI_TIER1_SEED_V1.md` is ~798 B over its 8 KB
   ceiling; needs a demotion pass (move detail to the trigger index / deeper docs).
5. **Ollama version pin** (WSL `0.9.5` isolated vs Windows `0.32.3`) so CHAT hits the
   isolated one -- never scoped this session.
6. **Concurrent site work:** `codex/lean-sites-publish` has another session's
   in-flight `.mdx` edits + generated-artifact drift; not mine, left untouched.

## Neighbor notes -- AIFs I affected (even where I do not own the lane)

Good-neighbor rule: flag cross-lane impact so owners are not surprised. Owners
should update their own records; these are pointers, not edits to their lanes.

- **AIF-032** (harvest diagram drift; unowned intake): audit evidence **refreshed
  2026-08-06** in the site matrix. The "real" count moved `224` -> `~236` since the
  original row; the SVG still shows the drifted `218/205` mixed with `236/215`, and
  source is unreconciled (`236`/`243`/`212`). Intake row 61 number (`224`) is now
  stale; still open; regeneration is host-side.
- **AIF-050** (commit coordination / prepush gate; `member.ai.claude.cowork`):
  extended the gate -- `.mdb` is now a hard block by suffix (`0b69162c6`), turning
  "never LMDB" into mechanism.
- **AIF-052** (AI-BBS lane; unowned intake, runtime-observed): **M4.1 + M4.2 now
  designed** (design-only, build pending) -- 5 artifacts + patches + runsheet; lane
  doc future-item repointed (`0df21d88a`). Intake row 84 could note the design
  milestone.
- **AIF-067** (dotref automation; `member.ai.claude.cowork`): `dotref_autogen.py`
  is now tracked (`87fbf2e4a`) -- was an untracked generator.
- **AIF-082** (onboarding cost / Tier 1 seed; `member.ai.claude.cowork`): seed
  gained the read-only-lock-free-git rule and format/reference truths; it is now
  ~798 B **over its 8 KB ceiling** -- a demotion pass is owed.
- **AIF-086** (AI-systems integration; `member.ai.codex.local`): heads up -- my
  NET EGRESS wording correction (`cmd_net.cpp`: "revocable egress isolation, NOT an
  air-gap") and the M4.1/M4.2 Ollama-agent designs bear on the integration model you
  are building. No edit made to your lane.
- **AIF-088** (command_catalog runtime drift; `member.derald`): the command-count
  reconciliation surfaced in the Phase 9 audit (`236` curated vs `243` registry vs
  `212` SYSCMD vs `237` on the catalog page) feeds this lane's drift scope.

## Not changed (guardrails held)

No runtime, identity, BBS, DBF, or publication mutation from the sandbox. All builds,
proofs, and git mutations were prepared as commands and handed to the maintainer.
