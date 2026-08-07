# Untracked authored-lane commit pass -- 2026-08-06

Owner: `member.derald`
Author: `member.ai.claude.cowork`
Status: **partial pass complete; big buckets deferred.** Companion to
`UNTRACKED_TREE_DISPOSITION_PROPOSAL_V1.md` (the 2026-08-05 ruling) -- this note
records what got committed, what remains, and the exact recipe so the next session
does not re-derive it.

## Trigger

"I can't find our LMS/Moodle work in ccode." It was on disk but half-untracked:
the `src/labtalk/lms/` engine was committed, but the lane scaffolding
(`labtalk/lms/` README + message contract + queue + tests, and
`labtalk/registries/lms.yaml`) had never been `git add`ed. That exposed a broad
backlog: ~7,000 untracked files, much of it real authored work sitting unversioned
(not backed up, invisible on GitHub, lost on a clean checkout).

## Recovered this pass (committed + pushed to origin/development)

| Lane | Commit |
| --- | --- |
| LMS lane scaffolding (registry, contract, README, queue, tests) | `222bdd6be` |
| selfdoc (policies, lineage jsons, probes) | `5618eb11c` |
| pycrud (CRUD UI, FastAPI backend, tests, schema) | `9812a8e01` |
| labtalk authored (aops, diagrams, labs, proofs, portal, docs) | `366f4ae7f` |

## Remaining (deferred -- its own dedicated pass)

~6,890 untracked, almost entirely:
- `docs/` (~4,242): authored manual source + lane docs MIXED with generated
  run artifacts (`docs/**/runs/**` audit CSVs, gate records).
- `dottalkpp/` (~2,258): runtime data + `.dts` fixtures + `dottalkpp/docs` (authored)
  + `dottalkpp/tools` (authored).

Per the ruling these are trackable (only `.mdb` is ignored) but they are mostly
regenerable data + manual output, and GitHub `main` only ever gets the
`PROMOTE.manifest` subset. So this is a hygiene commit for development history, not
urgent -- do it as a deliberate lane-by-lane pass.

## Per-lane recipe (what the prepush gate taught us -- follow exactly)

For each authored lane, before `git add <lane>`:

1. **Exclude non-source junk** the broad add would vacuum:
   - virtualenvs (`.venv/` -- already gitignored, verify),
   - bundle/archive dirs (`_bundles/`, `attic/` build dumps), `*.zip`,
     `__pycache__/` (verify gitignore),
   - use pathspec excludes: `git add <lane>/ ':(exclude)<lane>/_bundles/' ':(exclude)<lane>/**/*.zip'`.
2. **Convert Unicode to ASCII in added doc lines** (the house-style gate hard-blocks
   on non-ASCII in `.md`). Map that worked:
   `\x{2014}\x{2013}->'--'`, `\x{2192}->'->'`, `\x{2190}->'<-'`, `\x{2026}->'...'`,
   `\x{2011}\x{2010}->'-'`, `\x{2018}\x{2019}->"'"`, `\x{201C}\x{201D}->'"'`,
   `\x{2022}->'-'`, `\x{2611}->'[x]'`, `\x{00A0}->' '`, `\x{00D7}->'x'`.
   One-liner: `perl -CSD -i -pe 's/.../.../g' <file>`.
3. **Slice under 60 files per commit** (the gate WARNs > 60 and needs `--allow-mass`).
   Split a big lane into subdir commits.
4. **Fixture-flagged files** (e.g. an `.mdx` the data/fixtures classifier catches,
   like `labtalk/ai_portal/publication/ai-portal.mdx`) block with exit 3. Either
   unstage that one file (`git restore --staged <file>`) and commit the rest, or
   pass `--allow-data` on that commit.
5. `git status --short` between add and commit (scoped-slice safety check), then
   `git commit`, then `git push origin development`.

## Gotchas seen (do not repeat)

- `git add pycrud/` did NOT commit `.venv/` (it is gitignored) -- but it WOULD have
  pulled `pycrud/_bundles/*.zip` (source archives). Add `pycrud/_bundles/` to
  `.gitignore` (recommended) so it stops being untracked noise.
- Accumulating three `git add`s into one index produced a 148-file fused commit that
  tripped the mass-add warn. Commit each lane separately.

## Next actions (open)

- Add `pycrud/_bundles/` (and any stray `_bundles/`) to `.gitignore`.
- Decide `labtalk/ai_portal/publication/ai-portal.mdx` (fixture-flagged; site already
  carries the content).
- Run the deferred `docs/` + `dottalkpp/` lane-by-lane pass per the recipe above.
