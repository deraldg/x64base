# Handoff -- publishing the ECO route to live (2026-08-13)

    status        : BLOCKER RESOLVED 2026-08-13. Clear to publish. See 1a.
    agent         : member.ai.claude.cowork
    run           : COWORK-20260813-001   <- added after peer review; see 1b
    recorded_utc  : 2026-08-14T00:37:30Z  <- last amendment. Note the filename
                    says 2026-08-13: correct at creation, host-local, and the UTC
                    clock has since rolled. The header is the resolvable one.
    site tree     : D:\dev\x64base-site, branch codex/lean-sites-publish
    site HEAD     : b126994b3 (was 095e9495a when written; ancestor, so the
                    report was accurate then and has since been overtaken)
    ccode HEAD    : da02641b1 (was 7786e63b7 when written; same relationship)
    blocking      : NONE. Section 1 records the blocker and how it closed.

## 1a. Peer review of this report, and what it changed (2026-08-13)

A hosted peer (`HOSTED-20260813-001`) reviewed the header block alone and made
three calls. All three were checked rather than accepted, and all three hold.

| Their finding | Checked | Result |
| --- | --- | --- |
| Both baselines one commit stale | `git merge-base --is-ancestor` on each pair | **correct.** `7786e63b7` is an ancestor of `da02641b1`; `095e9495a` of `b126994b3`. The report was accurate when written and has been overtaken |
| `b126994b3` changed the `const D` data line in `public/eco/index.html`, so the blocker may already have moved | `git show --stat b126994b3` | **correct.** One file, 1 insertion, 1 deletion -- the data line |
| The report carries a member id and no run id, so nobody can tell which session wrote it | header inspection | **correct, and it is a defect on a lane I steward.** AIF-050 exists because member covers a deployment, not a session. Fixed above; `COWORK-20260813-001` was verified free before use |

The blocker did indeed move, and it moved because the owner committed the fix:

    095e9495a : 2 machine path(s) in public/eco/index.html   <- the blocker
    b126994b3 : 0                                            <- fixed, committed
    HEAD      : 0
    worktree  : 0, and byte-identical to HEAD and to the generator output
                (a2972018fc69982aae4ec5b4138123f515ff0fd1fc3eae4db2e83b407eafdc31)

`check:public-content` now returns **Public content guard passed**, rc=0, and the
site working tree is clean -- so `publish-github-pages.mjs` will not refuse it.

**Section 2's step 1 is therefore obsolete.** There is nothing to commit. Skip to
the build:

```powershell
cd D:\dev\x64base-site
npm run build
npm run index:search
npm run publish:github-pages
```

## 1b. The run-id gap, recorded because it is the day's third instance

The peer could not tell whether the report came from a concurrent host-mounted
session, an earlier artifact of the same session, or itself. Neither could a
reader in a month. That is exactly the gap AIF-050 was chartered to close -- the
lane's own words are *"the agent is traceable only to the product level"* -- and
it went unfixed in an artifact written by that lane's steward.

Standing correction for this member: **every handoff, closeout, and report header
carries a `run` line.** A member id names a deployment; a run id names the
session that can be returned to.

## 1. The publish would have failed, and the site's own guard caught it

`npm run check:public-content` **FAILED** on `public/eco/index.html`:

```
Public content guard failed. Remove local machine paths before publishing.
public/eco/index.html:63 [Windows absolute path]
```

The map embeds `projects.yaml` notes verbatim, and two of them legitimately name
the roots -- `project.x64base.runtime` names the staging root, and
`project.x64base.public_staging` names the development root. Correct in the
registry, not publishable on a public asset.

**This is a defect in my generator, not in the site and not in the registry.**
The scrub belongs at the publication boundary; censoring the registry to suit the
website would be the wrong direction of travel.

### Fixed, and the fix is guarded

`tools/fullstack_docs/ecoschema_map.py` now scrubs before writing:

- a named map for the three known roots, so the text stays readable
  (`the development root`, `the staging root`, `the website root`);
- a catch-all `[A-Za-z]:[\\/]...` -> `<local path>`, because the next note to
  name a NEW path would otherwise leak silently;
- and the generator now **refuses to write** and exits 2 if any drive-letter path
  survives. A scrub nobody checks stops working the first time it is needed.

Falsified both directions before trusting it: the detector finds
`D:/code/ccode/src` and `C:/x64base` in an unscrubbed blob, and the regenerated
output contains zero drive-letter paths.

### Current state after the fix

| Check | Result |
| --- | --- |
| `check:diagrams` | PASS, 18 diagrams |
| `check:public-content` | **PASS** (was FAIL) |
| site copy vs generator output | byte-identical, `a2972018fc69...` |
| `npm run build` | **not run** -- sandbox EPERM unlinking `.next/BUILD_ID`; host only |

`public/eco/index.html` is modified in your tree: 93,611 bytes, scrubbed, versus
the 93,598-byte version committed in 095e9495a. **The committed one leaks paths
and will fail your own guard at build time.** That single file is the whole
delta.

## 1c. The drift gate the route was missing (added 2026-08-17)

Section 7 predicted this route would go stale for want of a gate. It did, in three
days: published 2026-08-14, checked 2026-08-17, by which point AIF-112..118 and
seven proof records had landed and nothing announced it.

**`ecoschema_map.py --check PATH` now closes it**, and it belongs FIRST in the
publish sequence below, ahead of the build:

```powershell
cd D:\code\ccode
python .\tools\fullstack_docs\ecoschema_map.py --check D:\dev\x64base-site\public\eco\index.html
#   rc 0 = published copy matches its authority
#   rc 3 = DRIFT; it prints what moved (claim 43 -> 50, the new lane ids)
#   rc 4 = target missing
```

On rc=3, regenerate and re-copy per section 4, then re-run `--check` until it
returns 0. It is a ccode-side step by necessity: the authority is the ccode
registries, which the site repo cannot read -- which is also why the site's own
`check-public-content` could never have caught this class.

## 2. Publish sequence, in order

`scripts/publish-github-pages.mjs` refuses a dirty source worktree, so the map
fix has to be committed before publishing -- that is the script working, not an
obstacle.

```powershell
cd D:\dev\x64base-site

# 1. the one file, named explicitly -- never -A, never .
git add public/eco/index.html
git status --short                       # expect exactly one M line
git commit -m "eco: scrub machine paths from the generated map" -m "check-public-content caught D:/ and C:/ roots embedded from projects.yaml notes.
Fixed in the generator (tools/fullstack_docs/ecoschema_map.py in x64base), which
now scrubs at the publication boundary and REFUSES to write if any drive-letter
path survives. Regenerated and re-copied byte-identical; guard passes."

# 2. build -- runs check:diagrams and check:public-content, then exports
npm run build

# 3. search index over the export
npm run index:search

# 4. publish to gh-pages via the .gh-pages-deploy worktree
npm run publish:github-pages
```

The deploy worktree exists and is on `gh-pages`; the script verifies that and the
origin before it does anything, and pushes only from there.

## 3. Before you run it -- two things worth a look

1. **Branch.** You are on `codex/lean-sites-publish`, and the live site is
   already serving `?v=c7581a605e2e` from it, so publishing from this branch is
   established practice for this lane. Flagged only because the script records
   `source_branch` in the deploy metadata and it will say `codex/...` on a
   publish the owner made.
2. **The ECO route is `generated`, and the matrix row is still owed.** The nav
   comment says so, `app/eco/` does not exist (you served it as a static drop-in
   at `/eco/index.html`, matching the `/AI/index.html` precedent, which is the
   simpler and better call), but
   `content/docs/dev/website-documentation-matrix.mdx` has no row for it yet.
   Classify-first is the rule; without the row nothing tells the next person the
   file is regenerated rather than authored.

## 4. Regenerating the map, from now on

```powershell
cd D:\code\ccode
python .\tools\fullstack_docs\ecoschema_map.py
copy .\docs\maintenance\ECOSCHEMA_MAP_V1.html D:\dev\x64base-site\public\eco\index.html
Get-FileHash .\docs\maintenance\ECOSCHEMA_MAP_V1.html, D:\dev\x64base-site\public\eco\index.html
```

Two hashes, one value, or the copy is not a copy. The map ages the moment a lane
is claimed.

## 5. Owed after publish

- Website closeout referencing the supporting x64base commit (Local Integration
  Rule -- the two repos are separate pushes).
- Matrix row for `/eco/` (section 3.2).
- `claim-aif` for the ECO route.
- The x64base-side files from this pass are all UNTRACKED and not ignored:
  `tools/fullstack_docs/ecoschema_map.py`,
  `docs/maintenance/ECOSCHEMA_MAP_V1.html`,
  `docs/maintenance/PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1.md`,
  `docs/maintenance/peer_design_review/PDR-001.../SESSION_V1.md`,
  and the handoffs in `docs/agents/`. They want a scoped, path-named commit of
  their own.

## 6. What I did not do

No build, no commit, no push, no branch operation, in either tree. The only
mutation I made anywhere was rewriting `public/eco/index.html` with the scrubbed
regeneration, which is the fix for the blocking defect and is byte-identical to
the generator's output.
