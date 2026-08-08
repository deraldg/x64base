# Products vs. Deliverables vs. License Units -- the anchor for licensing

**Status:** DRAFT, owner ratification owed. Date 2026-08-08. Not legal advice.
This is the definition the four license proposals hang from: **a license attaches to a
deliverable, not to a marketing name.** The site markets ~14 "products"; there are far
fewer things to actually license. This document reconciles the two.

## 1. What the site claims as products (the marketing surface)

- **Home page ecosystem (6):** x64base Engine, DotTalk++, DotScript, TupTalk, RelTalk,
  Laboratory Campus / LabTalk.
- **Products page (9):** the six above, plus TableTalk, SQLsel, Parallel GUI/TUI.
- **Named in prose / lanes:** SelfDoc, MDO (Master Documentation Organizer), DotTalk++
  Workbench, Arctic TUI.
- **Trademarks page (8 marks):** x64base(TM), xBase_64(TM), DotTalk++(TM), TupTalk(TM),
  TableTalk(TM), RelTalk(TM), Arctic(TM), LabTalk(TM).

The products page states the truth itself: these "name the major workflows in the local
DotTalk++ / x64base runtime." They are **workflows and marks, not separate deliverables.**

## 2. What actually ships (deliverables)

- **`dottalkpp.exe`** -- the single binary / runtime host. The home page says it plainly:
  "dottalkpp.exe is the full command/runtime host." It contains the engine, the DotTalk++
  shell, DotScript, TupTalk, TableTalk, RelTalk, SQLsel, the GUI/TUI surfaces, and the
  SelfDoc/MDO tooling. **One executable.**
- **LabTalk / Laboratory Campus content** -- curriculum, labs, cases, teaching docs, the
  generated manuals. Content, not a binary.
- **AI work** -- the AI Portal, coordination system, agent tooling. Internal; NOT claimed as
  a product on the site.
- **(IDLE) engine / bindings library** -- a separable, embeddable engine build and/or the
  `pydottalk` bindings. Per owner, this AIF is marked idle, so it is **not a current
  deliverable.** This is the hinge (section 4).

## 3. The map: claimed product -> deliverable -> license unit

| Claimed product | What it really is | Ships as | License unit |
| --- | --- | --- | --- |
| x64base Engine | engine code region (embeddable lib is idle) | inside `dottalkpp.exe` | **A** now; own unit only if the library ships |
| DotTalk++ | the shell / application | `dottalkpp.exe` | **A** |
| DotScript | language feature | `dottalkpp.exe` | **A** |
| TupTalk | feature + mark | `dottalkpp.exe` | **A** |
| TableTalk | feature + mark | `dottalkpp.exe` | **A** |
| RelTalk | feature + mark | `dottalkpp.exe` | **A** |
| SQLsel | feature | `dottalkpp.exe` | **A** |
| Parallel GUI/TUI | UI surface | `dottalkpp.exe` | **A** |
| Arctic TUI | feature + mark | `dottalkpp.exe` | **A** |
| SelfDoc / MDO | doc-dev system (tool) | `dottalkpp.exe` + `tools/` | **A** (tool); its OUTPUT is content -> **B** |
| LabTalk / Campus | education content | site + docs + curriculum | **B** (content) |
| AI Portal / coordination | AI tooling | repo (internal) | **C** (proprietary) |
| The 8 marks | trademarks | n/a | **D** (mark layer, spans all) |

**License units:**
- **A -- the dottalkpp binary** (engine + shell + all *Talk features + SelfDoc). One unit ->
  Proposal 2 (DotTalk++ PolyForm-Noncommercial). *Everything named 1-9 on the site rides
  this one license; they are not separately licensable as shipped.*
- **B -- LabTalk content** -> Proposal 3 (Creative Commons). SelfDoc's generated docs land
  here.
- **C -- AI work** -> Proposal 4 (proprietary).
- **D -- the marks** -> trademark layer, separate from every code/content license.

## 4. The hinge: the engine as an installable SDK

Proposal 1 (Apache engine) needs a **separately shippable engine library**. Prior-art check
(full detail + citations: `EDITIONS_LICENSING_GROUND_TRUTH_V1.md`) shows this is far closer
than "idle from scratch." x64base already has a CMake **edition system**
(`DOTTALK_PRODUCT = LEAN|PROFESSIONAL|EDUCATIONAL|DEVELOPMENT`) with a real education strip
and per-edition `config/package/*.manifest` files, the engine is already factored into
standalone static libs (`xbase`/`xindex`/`memo`/`xexpr`), and `bindings/pydottalk` already
links them with **no shell and no education** -- a working education-free embed today.

So the fork is **not** "refactor vs park." What is missing is *packaging*, not architecture:
an `install(EXPORT)` of the libs + public headers, one composed engine target, and two seams
the `X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` already scopes (Passes 2-5). The real fork:

- **Finish the SDK packaging** (bounded, plan-scoped) -> the engine becomes a real Apache-2.0
  deliverable (the LEAN edition / `x64base-lean-table`); the app sits on top. Best fit for the
  adoption priority.
- **Ship the binary edition(s) now** (PROFESSIONAL/DEVELOPMENT) under the app license, finish
  the SDK later -> one licensed deliverable today; Apache engine follows when packaged.

Either way, the deliverable boundaries are **already defined as `DOTTALK_PRODUCT` editions
with `config/package/*.manifest` files** -- you are licensing editions that exist, not
inventing units. And note: `BUILDING.md` already says the editions are blocked pending the
license decision, so this licensing work unblocks a build system that is already built.
**Nothing else in the license structure changes based on this call.**

## 5. Consequences and cleanups

- The four proposals map cleanly onto Units A-D, with Proposal 1 gated on the section-4
  hinge.
- Do NOT write per-*Talk license files -- TupTalk/TableTalk/RelTalk/etc. are features and
  marks of Unit A, licensed with the binary.
- **Site cleanups (separate from licensing):** the home page lists 6 products, the products
  page lists 9 (home omits TableTalk, SQLsel, Parallel GUI/TUI) -- they should agree. Arctic
  TUI is marketed in prose but is on neither product list. "DotScript product" is really a
  feature. These are marketing-consistency fixes, not license issues.

## 6. Recommended next step

Ratify this map (what ships), rule the section-4 hinge (revive the engine library or not),
then license the **units**, not the marketing names: Unit A -> PolyForm-NC, Unit B -> CC,
Unit C -> proprietary, Unit D -> marks, and Unit "Engine" -> Apache only if the library
returns.
