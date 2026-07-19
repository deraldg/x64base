---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260719-004
  recorded_at_utc: 2026-07-19T17:50:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    website_repo: D:/dev/x64base-site
    website_branch: codex/lean-sites-publish
    website_baseline_commit: 780ffb89ad3b
    website_source_commit: 9b6e47c4
    website_source_of_record: 3c559a876f5dcc9abdb74375f1d7ee54e540a883
    gh_pages_commit: 9fc3e78dd0536dd78cb67f2010c10855b80aab89
    source_repo_branch: homegrown-cnx-20251112-branch
  authorization:
    requested_by: maintainer
    scope: >
      Refresh the source-derived website catalogs, harvest the error/messaging/
      localization surfaces into the reserved section, add drift-check tooling,
      normalize line endings, then commit/push the website source and publish to
      GitHub Pages / x64base.com.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_WEBSITE_SOURCE_DERIVED_CATALOG_HARVEST_2026-07-19.md
    kind: session_closeout
---

# Session Closeout — Website source-derived catalog refresh + error/messaging/localization harvest

Date: 2026-07-19.
Truth state: the command/function catalogs are re-derived from engine source and
the reserved error/messaging/localization section is harvested; all published.
Publish state: live on `x64base.com` (gh-pages `9fc3e78d`, source-of-record
`3c559a87`).

## What prompted this

The maintainer noticed the live command list was missing `REGRESSION`. Root
cause: the source-derived catalog pages (`command-catalog.mdx`,
`function-catalog.mdx`) are website derivatives of the engine registry +
`@dottalk.usage` blocks, and the 2026-07-18 documentation push refreshed the
manual/downloads vertical but did **not** regenerate those catalogs. They had
drifted since 2026-07-10.

## What changed (website — `D:/dev/x64base-site`, published)

- **`content/docs/dottalk/command-catalog.mdx`** — full source-derived rebuild.
  224 registered command keys; 227 rows (incl. 3 self-registered); 215 documented
  rows, 12 genuine fallbacks. Added 8 missing registry commands (`REGRESSION`,
  `EXPORTFUNCTIONS`, `SCX`, `CONCAT`, `STRCAT`, `EXITS`, `HANUKKAH`, plus RETRO/
  SORT split from joined rows); added 3 self-registered commands (`PREDHELP`,
  `STUDENTECHO`, `STUDENTHELLO`) with a "Self-registering commands (open
  architecture)" note; removed 2 dead rows (`REPLACE_MULTI`, `SNX`); reclassified
  ~47 rows that were wrongly generic-fallback; corrected `SCX` (real student
  index-lab command); escaped `<table>`/`<expr>` in the `SQLERASE` row for the
  public-content guard.
- **`content/docs/dottalk/function-catalog.mdx`** — added the self-registering
  student functions `STU_UPPER`/`STU_REPEAT` under an open-architecture note
  (the 63↔65 SYSFUNC delta was confirmed to be alias counting, not drift).
- **`content/docs/engine/error-codes.mdx`** — replaced the placeholder with the
  canonical HRESULT-style catalog harvested from `include/xbase_error_codes.hpp`:
  3 severities, 7 facilities, 20 named codes (`general/0x0001` … `io/0x0001`),
  each with identity, symbol, severity, and message. Anchor `DIAG-ERRCODE-010`.
- **`content/docs/engine/messaging-and-localization.mdx`** — new page: the
  `cli::cmdout` channel (`emit_error`/`emit_warning` + `set_last_error`), the
  `MessageId` catalog + `MSGMGR` seed tiers over `SYSTEM_MESSAGES.dbf`, the
  DBF/CDX/LMDB locale spine (`en-US` base + `de`/`es`/`fr`/`it`, requested→`en-US`
  fallback), and the `REGRESSION LANGUAGE` proof. Anchor `DIAG-MSGLOC-011`.
- **`config/sidebars.ts`** — nav entry for Messaging & Localization.
- **`README.md`** — a "Pre-publish drift checks" section wiring the checks below
  into the publish flow.
- **`.gitattributes`** — pins `content/`, `config/`, `scripts/`, `*.mdx`, `*.md`
  to LF (scoped, to avoid churning CRLF-in-HEAD `app/` code).

## What changed (source tooling — `D:/code/ccode`, dev-only, not yet promoted)

- **`tools/fullstack_docs/command_catalog_sync.py`** — a drift gate with five
  modes: `check` (command catalog vs registry + optional SYSCMD DBF cross-check),
  `fn-check` (function catalog vs `function_catalog.cpp` + self-registered fns +
  optional SYSFUNC), `err-check` (error page vs `xbase_error_codes.hpp`),
  `loc-check` (locale table vs the `REGRESSION LANGUAGE` set), and `emit`
  (re-derive the command catalog). Parser is BOM-, CRLF-, inline-`// summary:`-,
  and adjacent-block-robust, and sanitizes `<>`/`|` in Markdown cells.
- **`dottalkpp/data/scripts/ext/stu_functions_liveness.dts`** — runtime proof
  script for `STU_UPPER`/`STU_REPEAT`.

## Proof

All four checks PASS against the published pages:

```
command_catalog check=PASS registry_keys=224 catalog_rows=227 parsed=215 fallback=12 syscmd_active=190 self_registered=3
function_catalog check=PASS core=63 self_registered=2 website_rows=65 sysfunc=65
error_codes     check=PASS source_codes=20 page_rows=20
locale          check=PASS source_locales=[de,en-US,es,fr,it] page_locales=[de,en-US,es,fr,it]
```

Each check FAILs loudly on the pre-fix pages (e.g. command `MISSING_FROM_CATALOG
(7)`, error `MISSING_FROM_PAGE (20)`, function `SELF_REGISTERED_MISSING (2)`),
demonstrating the gate. Live verification: the new
`/docs/engine/messaging-and-localization` page renders at source version
`3c559a87`; the command-catalog CDN cache was still refreshing at closeout.

## Publication

- Website source: `9b6e47c4` (7 files) pushed to `codex/lean-sites-publish`;
  a follow-up commit escaped the `SQLERASE` placeholders, making source-of-record
  `3c559a87`. The pre-existing EOL churn on ~31 unrelated files was deliberately
  kept out of the commit.
- GitHub Pages: `0011f641 → 9fc3e78d`; Pages `status: building → built`;
  `https_enforced: true`, `cname: x64base.com`.

## Preserved / not regressed

- The 12 remaining catalog fallbacks are genuinely block-less (aliases, stubs,
  case-variants) — verified, not misclassifications.
- Zero rows were downgraded from documented → fallback in the rebuild.
- `app/`, `components/`, and other CRLF-in-HEAD code were left untouched.

## Open items

1. **Source tooling promotion.** `command_catalog_sync.py` and the liveness
   `.dts` are dev-only in `D:/code/ccode`; they ride the normal
   `D:/code/ccode → C:/x64base → GitHub` source promotion, not the website push.
2. **STU_UPPER/STU_REPEAT runtime liveness.** Source-confirmed (the TU is
   GLOB-linked into the executable, so its static-init runs); the `.dts` is the
   pending runtime confirmation.
3. **Whole-tree EOL normalization.** `app/`/`components/` remain CRLF in HEAD; a
   separate dedicated normalization pass can align them if desired.
4. **Messaging adoption / `SET ERRORSTOP`.** Documented honestly on the page as
   an active lane, not a finished state (per AIF-018/AIF-021).
