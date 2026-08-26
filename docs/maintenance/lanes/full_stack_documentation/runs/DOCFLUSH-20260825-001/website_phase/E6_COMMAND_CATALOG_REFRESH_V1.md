# E6 website command catalog refresh

Run: `DOCFLUSH-20260825-001`

Recorded: 2026-08-26

State: **E6 PASS; publication not authorized or performed**

## Result

The DotTalk++ command catalog was regenerated from the development-tree command
registry and source usage contracts. The accepted catalog contains 239 registry
keys, 239 parsed rows, and zero fallback rows. The local website production build
also passed: 18 diagrams, the public-content and opacity guards, TypeScript,
171 static pages, and a Pagefind index covering 164 pages and 10,227 words.

Website source revision: `27ce68e005e42a8e1452b0bc247e8cb7ed64d14c`
on branch `codex/lean-sites-publish` in `D:\dev\x64base-site`.

No website push, deployment, live-route mutation, or `C:\x64base` mutation was
performed.

## Finding and repair

The first regeneration exposed two false fallback rows. `APPGUI` declares `GUI`
as an alias, while `BUILDVECTORS` declares `BUILD VECTORS` and `BUILD INFO`; the
shell registers their first-token router `BUILD`. The extractor read command
names but ignored declared aliases. `command_catalog_sync.py` now projects those
aliases, including the registered first token of a spaced alias, and a focused
test protects that behavior. No concurrent APPGUI implementation file was edited.

## E0 correction and restarted audit

The first catalog attempt occurred before the website documentation matrix was
consulted. It therefore does **not** satisfy E0 and is retained as a procedural
failure. E0 was restarted: the matrix and navigation were then read before a
second regeneration. The matrix classifies DotTalk++ catalog pages as reviewed
derivatives, requires implementation-to-website simplex flow, and forbids manual
editing of generated/derived output. The restarted regeneration was byte-identical
to the committed site revision and the catalog check again returned 239/239 with
zero fallback; the full site build passed afterward.

The matrix closeout half is intentionally still open. It advances only against an
owner-approved, signed-off site revision. This E6 source refresh grants no website
publication authority.

## Good Neighbor note

- **WHAT CHANGED:** hardened alias projection in the catalog generator, added a
  regression test, and regenerated the derived website command catalog.
- **WHOSE AREA:** AIF-068 full-stack documentation and the x64base-site generated
  DotTalk++ catalog, intersecting AIF-132 Portal feed hardening.
- **AUTHORIZATION:** the maintainer directed the documentation push to continue;
  this covered the local E6 source refresh, not push, deployment, or publication.
- **VERIFY OR UNDO:** run the focused generator test, regenerate and check the
  catalog for zero fallback, and run the site production build. Revert ccode's
  exact E6 commit and site commit `27ce68e...` to undo; no public rollback exists.
