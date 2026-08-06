# Website matrix walk -- 2026-08-06 (pass 4 first pass)

Re-walk of `x64base.com` (`D:\dev\x64base-site`) using
`content/docs/dev/website-documentation-matrix.mdx` as the lens, per the matrix
entry/closeout gate. Findings by category, each with disposition. "Source-fix +
regen" items are host-side handoffs; "matrix-edit" and "site-edit" items were done
in this first pass.

## 1. Count reconciliation (AIF-032) -- OPEN, handoff

The command count disagrees across surfaces, exactly as the matrix Diagram-promotion
row warns:

- `content/dottalk/command-catalog.mdx`: 237 registered command keys.
- `content/docs/dev/roadmap.mdx` and the matrix: 236.
- `public/images/dottalk/command_reference_harvest_v1.svg` (data-carrying, must be
  generated): mixes 205 / 215 / 218 / 236 -- internally inconsistent.
- Source authority itself unreconciled: 243 registry / 212 SYSCMD / 236 curated.

Disposition: reconcile the count in source and define what each number measures,
then REGENERATE the harvest SVG + Command Catalog + roadmap from that authority via
the fullstack push. Do NOT hand-edit the SVG or catalog. `generated` lane.
Handoff (host generators).

## 2. Currency / staleness -- OPEN, handoff

- `content/docs/dev/documentation-progress.mdx`, `public/artifacts/documentation-
  progress-v1.json`, and `content/docs/dev/full-stack-documentation-push.mdx` are
  stamped 2026-07-23; `public/artifacts/current-work-v1.json` advanced to
  2026-08-05. After pass 4 the progress feed lags.
  Disposition: advance the registry `as_of_date` and re-run the progress /
  current-work generators; do not hand-edit the mdx/json. Handoff.
- `content/products/sqlsel.mdx` and `content/docs/engine/sqlsel-and-sql-
  conformance.mdx` "as of 2026-07-29": acceptable if the subject is unchanged;
  verify at next SQLsel change.

## 3. Coverage gaps in the matrix -- FIXED (matrix-edit)

- `/AI/` process-diagram gallery + AI views (BBS ERD/DFD/PFD, M4.x, the pass-4
  doc-push DFD) were not listed. Added a Website Section row: `maintained`
  gateway-served AI views, diagrams hand-authored from `labtalk/diagrams/*.mmd`.
- Private AI Portal reference (`/portal/overview`, `/portal/schemas`,
  `app/portal/[...slug]/`) was absent. It is private/unlisted BY DESIGN (robots
  noindex; not in nav/sitemap; "promotion is a later step"). Recorded as a
  `maintained` private working reference. NOTE: currently untracked -- needs a
  scoped commit (owner decision; do not promote to nav).
- `content/docs/engine/python-integration.mdx`: new, untracked, and absent from the
  engine sidebar (unreachable). Covered by the engine `/docs/engine/*` matrix row
  via wildcard. Site-edit: added a `Python Integration` entry to `config/sidebars.ts`.
  Still untracked -- needs a scoped commit.

## 4. HTTPS / AutoSSL -- pending trigger (matrix-edit)

The artifact/manual-room links and `/docs/dev/selfdoc-website-publication` gate on
"move to HTTPS after the certificate validates." AutoSSL is pending (a bad cert was
removed). Nothing to flip yet. Recorded an explicit AutoSSL trigger on the matrix
artifact/manual-room feed row so the flip (links to HTTPS, drop the "while SSL is
settling" caveats) is not forgotten when the cert lands.

## 5. Retention -- VERIFIED current, no action

- Publication checkpoint: the matrix carries only the 2026-07-18 checkpoint (commit
  `be935053`, 183-page reference, 4,118-line / 237-heading manual).
  `documentation-progress.mdx` still shows the same 4,118-line manual -- no newer
  manual acceptance was found, so the append-only checkpoint is still current. No
  new checkpoint to append this pass.
- `127.0.0.1` mentions in `current-lanes.mdx` / `ai-portal.mdx` are runtime facts
  (loopback binding), not stale links. Leave.

## 6. Design / reachability -- PARTIALLY FIXED

- `python-integration` made reachable via the engine sidebar (above).
- `portal/*` intentionally NOT added to nav -- private by design; recorded as such.
- New pages should answer the Proofed Site Checklist (source lane, proof level,
  backing artifact, regen trigger). python-integration and portal pages: verify the
  four questions before any public promotion.

## Handoffs (host-side, cannot run in sandbox)

1. Count reconciliation (source-fix) + regenerate harvest SVG / Command Catalog /
   roadmap. Blocks a clean close (AIF-032).
2. Advance documentation-progress / current-work feed `as_of_date` to the pass-4
   reconciliation date and re-run the generators.
3. Scoped commits for the untracked new pages once their class + promotion decision
   are confirmed: `content/portal/*`, `app/portal/[...slug]/`,
   `content/docs/engine/python-integration.mdx`.

## Done in this first pass (matrix-edit / site-edit)

- Matrix: added AI views/diagrams row, private AI Portal row, AutoSSL trigger note.
- Sidebar: added Python Integration (reachability).
- This note.
