# FULLSTACK-DIAGRAMS -- data-driven diagrams generated from the fullstack push (lane v1)

Status: **proposed / not started** (dev). Not promoted.
Owning lifecycle: DotTalk++ SDLC - fullstack documentation.
Truth state: problem source-verified (2026-07-20); no source yet.

## Why this lane exists

The website carries two kinds of diagram:

- **Conceptual / architectural** -- e.g. `trinity_headers_v1.svg`, the
  `x64_self_describing_dbf_v1.svg` layout, `dottalkpp_architecture_layers_v1.svg`,
  `index_order_cdx_lmdb_v1.svg`. These encode structure, not counts, and stay
  accurate across releases. They are in sync source<->site and need no generation.
- **Data-driven** -- they embed numbers harvested from source. The clear case is
  `docs/manuals/assets/diagrams/command_reference_harvest_v1.svg` ("... registered
  command keys / ... parsed usage contract blocks").

The data-driven ones are **hand-authored static SVGs with the numbers typed in**,
so they drift. Verified 2026-07-20: the harvest diagram reads `457 blocks / 197
entries` in the ccode source (2026-06-28) and `218 registered / 202 parsed` in the
site copy (2026-07-08), while the real registry is **224** registered command keys.
`tools/fullstack_docs/command_catalog_sync.py` already keeps the command-catalog
**page's** snapshot line current (`{keys}` registered / `{parsed}` parsed) -- but it
**does not emit the SVG**, and nothing else does. So the diagram is not actually
part of the fullstack documentation push; that gap is the root cause of the drift.

## Goal

Make the **data-carrying** diagrams a product of the same `tools/fullstack_docs`
generators that produce the pages, so they regenerate on the fullstack push and
cannot drift from the numbers on the page beneath them. Conceptual diagrams stay
hand-authored and out of scope.

## Design sketch

- **Template + fill, not full re-draw.** Keep each data-driven SVG as a template
  with named placeholder tokens (e.g. `{{REGISTERED}}`, `{{PARSED}}`) for the
  numeric labels only; the generator substitutes the values it already computes.
  This preserves the hand-tuned layout while making the numbers generated.
- **Single source of the numbers.** The generator computes `keys`/`parsed` once
  and writes both the page snapshot line **and** the SVG labels from that value, so
  they can never disagree.
- **Emit to source, copy to site.** Write the filled SVG to
  `docs/manuals/assets/diagrams/` (the source of record), then the existing
  site-sync step copies it into `x64base-site/public/images/...`. Verify byte-sync
  as part of the push checklist.
- **Provenance.** Record generator + inputs in `tools/diagram/diagram_provenance.py`
  so each data-driven SVG names what produced it.
- **Drift gate.** Extend the fullstack drift check so a data-driven diagram whose
  embedded numbers disagree with the current harvest **fails loudly** (same spirit
  as the command/function/error/locale catalog checks already in
  `command_catalog_sync.py`).

## Milestones

- **M1 -- harvest diagram, first target.** Turn `command_reference_harvest_v1.svg`
  into a token template; have `command_catalog_sync.py` fill `registered`/`parsed`
  (and any other harvested counts) from the value it already computes; emit to the
  diagrams source dir. Proof: run the fullstack push in the `.venv312` dev env and
  confirm the SVG shows the current `224` registered keys, matching the page.
- **M2 -- inventory + generalize.** Enumerate every data-carrying diagram (numbers
  harvested from source), template each, and route it through the owning
  fullstack generator. Leave conceptual diagrams alone.
- **M3 -- drift gate.** Add the diagram-number drift check to the fullstack
  check-modes and the pre-publish checklist.
- **M4 -- site sync + provenance.** Byte-sync generated SVGs into the website,
  record provenance, and document which diagrams are generated vs conceptual.

## Non-goals / honesty

Architectural diagrams are not auto-generated and do not need to be. This lane is
narrowly about the diagrams whose **numbers** come from the harvest, so they stop
being hand-maintained. Requires Python 3.12+ (the fullstack tools already do);
runs in the dev env, not the CI sandbox. Dev-only until built + proven.

## Provenance pointers

- Problem evidence: `docs/manuals/assets/diagrams/command_reference_harvest_v1.svg`
  vs `x64base-site/public/images/dottalk/command_reference_harvest_v1.svg`;
  `tools/fullstack_docs/command_catalog_sync.py` (page snapshot line, no SVG emit).
- Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-032).
- Related: AIF-025 (website source-derived catalog drift + 5-mode drift gate).
