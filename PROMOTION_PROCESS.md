# DotTalk++ Promotion Process — `development` → `main`

_Status: formalized process. Supersedes the older `WORKFLOW_X64BASE.md`, which
describes a now-retired intermediate tree (`D:\code\ccode\x64base`) and an
outdated "C:\x64base is a mirror only" role. Reconcile or delete that file._

> **Non-negotiable:** the arrow in this title describes reviewed promotion, not
> a Git branch merge or refspec. Never push `development:main` and never merge
> the `development` branch into `main`. Original work stays in
> `D:\code\ccode`; only sterilized staging rooted at `C:\x64base` may update
> GitHub `main`.

## 1. Purpose

Define exactly how work moves from active development into the public GitHub
repository, so that:

- `main` is **canonical for downloads and pull requests**, and stays clean and
  reviewable.
- The publishable set is **explicit and auditable**, never a blanket copy.
- Drift between development and the public repo is **detectable and bounded**.

## 2. Repositories, branches, roles

| Location | Clone / branch | Role |
|---|---|---|
| `D:\code\ccode` | tracks `development` | Source of truth. All new code, fixes, data work, and docs happen here first. Formerly the `homegrown-cnx-20251112-branch`; renamed to `development` to make its role explicit and separate it from the public line. |
| `C:\x64base` | tracks `main` | Publication staging. The clone that commits and pushes to `main`. **Canonical for downloads and PRs.** Rebuildable from the verified baseline + overlay, never hand-authored as a second dev tree. |
| `github.com/deraldg/x64base` | `main` (default) | Public snapshot. `origin/HEAD → main`. |

**Authority chain (single, canonical):**

```
D:\code\ccode  (development)  --allow-list overlay-->  C:\x64base  (main)  --push-->  github/main
```

There is no intermediate curated tree. `development` is the only authoring
surface; `main` is the only public surface.

For engine source, any explicitly authorized promotion branch is created from
`main` inside the sterilized staging workflow. Only the reviewed source slice is
applied to it. It must not inherit the `development` branch or unrelated
development history.

## 3. What publishes: the two lanes

`main` is a **model / reference repo** — it serves both investigators (who
download and run) and contributors / AI agents (who read and extend). Every
promoted file belongs to exactly one **publish lane**. ("Publish lane" is the
audience axis for what leaves development; it is distinct from MDO content lanes
such as `messaging` or `metadata`.)

- **PRODUCT publish lane.** Needed to *use* the release: engine source and
  headers, runtime scaffold, help, sample data + the schemas needed to read it,
  databuild and smoke scripts, and rendered manuals.
- **MODEL/DEV publish lane.** Published because this is a model repo:
  documentation *engines* (generators), AI-/agent-facing docs, contracts, portal
  seeds, build rationale, and repo tooling. The principle: **publish the rendered
  output; keep the generator in the MODEL/DEV lane.**

Schemas are split, not one bucket: data/workspace schemas travel with the sample
data (PRODUCT); engine-internal schemas (manualgen JSON, `src/schemas/*.json`)
describe the tooling (MODEL/DEV).

## 4. The allow-list (`PROMOTE.manifest`)

Promotion is governed by `PROMOTE.manifest`, an **allow-list** (not an
ignore-list): of the clean files in development, these publish. It is the
counterpart to `.gitignore` (deny; universal) and they do not overlap.

Rules:

1. **Allow-list only.** A file publishes only if a manifest glob matches it.
   Broad blanket copies are prohibited.
2. **Lane-tagged.** Every entry lives under its PRODUCT or MODEL/DEV publish-lane section.
3. **`.gitignore` is a hard guard.** The rebuild re-applies the deny-list after
   matching, so an over-broad glob still cannot leak LMDB, `*.cdx.d`, `*.exe`,
   `og/`, `__pycache__`, or scratch.
4. **Non-publish lanes stay out.** `messaging`, `metadata`, and `sandbox` are
   versioned in development but deliberately not published. They must never
   appear in the allow-list, and must not linger in `main`.

## 5. Promotion procedure

Run from `D:\code\ccode` unless noted.

1. **Land changes on `development`.** Commit real work to the `development`
   branch. Never author directly in `C:\x64base`. Pushing `development` updates
   the integration branch only; it does not publish to `main`.
2. **Rebuild staging.** `tools/staging/rebuild-staging.ps1` clones `github/main`
   into `C:\x64base` (baseline), preserves the committed baseline + dirty layer
   in verified escrow, then overlays every `PROMOTE.manifest` match from
   development, applying `.gitignore` as a guard.
3. **Build + smoke in staging.** Build `C:\x64base` and run the release-style
   smoke/proof if path-sensitive runtime behavior matters.
4. **Drift audit (Section 6).** Confirm the only differences between development
   and `main` are intended promotions.
5. **Commit + push from `C:\x64base`** to `main`.
6. **Open PRs against `main`** — it is the canonical PR target.

## 6. Drift audit (verification)

Before each push, verify staging matches intent. Compare by **content hash, not
date** (copies/clones rewrite timestamps):

- Compare files present in both trees; classify each as identical, DIFF
  (content differs), or GONE (in staging, no dev counterpart).
- Cross-reference every DIFF against `PROMOTE.manifest`:
  - **DIFF ∧ on allow-list** → promotion will refresh; expected.
  - **DIFF ∧ off allow-list** → a gap: either add it to the manifest or purge it
    from `main`. Should trend to zero.
  - **GONE** → staging-authored files with no dev source (e.g. `CHANGELOG.md`,
    `CONTRIBUTING.md`, `SECURITY.md`, governance docs). Keep them in the manifest
    preserve set or pull them back into development so they are not orphaned.

Target state: after a promotion run, off-allow-list DIFF = 0 and no
`__pycache__` / non-publish-lane files remain in `main`.

## 7. Non-publish lanes & junk

- **Bytecode / build junk:** `__pycache__/`, `*.pyc` — gitignore and
  `git rm -r --cached` from `main`.
- **`messaging` / `metadata` / `sandbox`:** versioned in development, never
  published. If present in `main`, remove them.

## 8. Cadence & responsibilities

- Promote on a defined cadence (e.g. end of each development phase or before any
  tagged release), not ad hoc.
- No change is hand-edited in both `development` and `main`. Fix in
  `development`, then re-promote.
- After each remote change to branch names or structure, update this document
  and the `PROMOTE.manifest` header in the same commit.

## 9. Open items to reconcile

1. ~~**Retire `WORKFLOW_X64BASE.md`** or rewrite it to match this document (it
   still references the removed intermediate tree and the old branch name).~~
   **RULED 2026-08-07 (AIF-092 R4): RETIRE, do not rewrite.** It is not in
   `PROMOTE.manifest`, has no `development` source, and this document already
   supersedes it. `CONTRIBUTING.md` now carries the repository-roles table it
   partly served, and unlike this document `CONTRIBUTING.md` IS allow-listed, so
   the current statement reaches `main`. Removal happens in the
   rebuild-review-commit window. Reasoning:
   `docs/maintenance/PUBLICATION_SURFACE_RECOVERY_PDLC_LANE_V1.md` section 6c.
2. **Path mismatch:** `PROMOTE.manifest` promotes `BUILDING.md` at repo root,
   but `main` carries it at `docs/getting-started/BUILDING.md`. Pick one.
3. **Expand the allow-list** using `PROMOTE.additions.manifest` so engine source
   and active docs are owned by promotion rather than frozen in the baseline.
4. **Purge** the `__pycache__` (58) and `messaging`/`metadata` (41) files now in
   `main`.
