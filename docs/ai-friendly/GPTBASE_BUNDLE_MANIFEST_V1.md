# GPTbase knowledge-bundle manifest v1

Owner: `member.derald`
Author: `member.ai.claude.cowork`
Lane: AIF-058 (roles taxonomy) / AIF-060 (agency) -- advisor track
Purpose: make the GPTbase hosted-advisor knowledge bundle a **derived consumer** of
the documentation system, so it stops going stale ("goes ether"). This file is the
first in-repo record of what the bundle IS -- the producer it never had.

## What the bundle is (and is not)

- A curated, public-safe **orientation** corpus loaded into the GPTbase Custom GPT:
  "ask the project expert" -- orient, explain a subsystem, draft, rubber-duck.
- Sensitivity class: **PUBLIC**. The bundle goes to a cloud GPT that is NOT
  egress-isolated (`AI_ROLES_TAXONOMY_V1.md`). Anything local/sensitive is Ollama's
  job, never GPTbase's.
- Authority class: **orientation, not truth**. GPTbase is an advisor -- influence,
  no authority. The bundle is a consumer, never a system of record. Answers are
  verified against current source before acting.

## Normalization target

The bundle is the third stale consumer (with the website and the manual). Same fix:
**derive it from the producer, do not hand-curate a snapshot.** One authority per
source; regenerated on each flush; the only human step is the owner re-uploading the
generated bundle to the Custom GPT.

## Derivation rule (default-deny, reuse the public gate)

The bundle is assembled ONLY from content that is already cleared for the public
website (it has passed `x64base-site/scripts/check-public-content.mjs`), plus a
short list of explicitly public-safe in-repo orientation docs. Rules:

1. **Default-deny.** If a source's public-safe status is unproven, it is excluded.
2. **No internal-only material** in the bundle: no maintenance/lane docs, no local
   absolute paths, no identity/RBAC internals, no proof command lines, no registry
   dumps. Strip or exclude; do not paste-through.
3. **Public website content is the primary source** because it is already gated.
   In-repo docs enter only if public-safe after path/identity scrubbing.
4. The assembly re-runs the public-content check over the produced bundle; a
   finding fails the build closed.

## Bundle sources (v1 -- the ~20, now defined)

Primary corpus: `x64base-site/content/` (already public-gated). Paths below are
site-content paths.

| # | Bundle piece | Source (public site content) | Note |
| ---: | --- | --- | --- |
| 1 | Project identity + ecosystem | `content/products/*.mdx` (x64base-engine, dottalk, dotscript, tuptalk, reltalk, labtalk) | what the pieces are |
| 2 | Getting started / orientation | `content/docs/getting-started/*` | first-read framing |
| 3 | Engine: DBF x32/x64 formats | `content/docs/engine/*dbf*`, `*formats*` | the format truth (public) |
| 4 | Engine: indexing + memo + VDISK | `content/docs/engine/*index*`, `*memo*`, `*ram-dbf-vdisk*` | CDX/CNX/LMDB, memo model |
| 5 | Engine: feature crosswalk | `content/docs/engine/feature-crosswalk.mdx` | capability map w/ evidence labels |
| 6 | Command surface | `content/docs/dottalk/command-catalog.mdx` | the derived catalog |
| 7 | DotScript + data mutators | `content/docs/dottalk/*dotscript*`, `*data-mutator*` | language + mutation safety |
| 8 | SDLC + campus model | `content/docs/labtalk/sdlc*`, `content/docs/dottalk/sdlc*` | the process framing |
| 9 | Talk family / workbench | `content/docs/talk-family/*` | GUI/TUI naming (public) |
| 10 | History / lineage | `content/docs/dev/historical-*` | preservation pages |

In-repo public-safe orientation (scrubbed of internal paths on assembly):

| # | Bundle piece | Source (in-repo) | Scrub |
| ---: | --- | --- | --- |
| 11 | AI roles taxonomy | `docs/ai-friendly/AI_ROLES_TAXONOMY_V1.md` | already shareable; verify no internals |
| 12 | Doc-flush intent (north star) | `docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_NORTH_STAR_V1.md` | strip in-repo file paths to concepts |

Excluded by rule (examples, non-exhaustive): identity/RBAC internals, any
`docs/maintenance/**` lane mechanics, `coordination/**`, registries, proof
transcripts, anything with a local `D:\` path.

## Assembly output

The generator `tools/fullstack_docs/build_gptbase_bundle.py` produces, into
`--out`:

- **A pointer / start-here index** (`00_start_here.md`) that routes the GPT by
  intent -- "if you want X, read section Y" -- mirroring the portal recall-graph
  pattern (reach by trigger, not linear read; `portal_recall_graph.yaml`). It also
  carries the boundary reminder: local/sensitive questions are Ollama's job, not
  this cloud advisor.
- **Six consolidated section files** (not one-per-source), so the bundle stays
  under the Custom GPT knowledge-file cap and avoids same-stem collisions:
  `01_orientation`, `02_engine`, `03_command_reference`, `04_workbench`,
  `05_process_and_roles`, `06_history`. Each concatenates its scrubbed sources with
  a per-source provenance comment.
- `bundle_manifest.json` -- per-section title, its source list, SHA-256, and the
  bundle `as_of_date` (derived from `ai_portal_tasks.yaml` -- the SAME date
  authority as the current-work feed and the site banner, never typed).
- A default-deny sensitivity scan (local paths scrubbed; residual leak tokens fail
  the build closed). The AUTHORITATIVE gate remains `x64base-site`
  `scripts/check-public-content.mjs`, to run on the produced bundle before upload.

The produced `bundle/` is a regenerable build artifact (like the harvest CSVs); it
need not be tracked -- regenerate it, do not hand-keep it.

## Cadence and the one human step

- Regenerated as the website-feed step of every full-stack flush (alongside
  `build_current_work_feed.py` and `command_catalog_sync`).
- The owner re-uploads the produced `bundle/` to the GPTbase Custom GPT and records
  the bundle revision. Uploading to a hosted GPT is a human action; the assembly is
  automated.

## Boundary restated

The bundle is public orientation, derived, and non-authoritative. It never carries
local/sensitive content, never becomes a system of record, and its freshness is the
producer's, not a memory's. Verify GPTbase answers against current source.
