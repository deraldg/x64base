# x64base.com website

Next.js + TypeScript + Tailwind site scaffolded from the `WEB SITE DESIGN.txt` blueprint.

## Quickstart

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Content editing

Most content is in `content/**.mdx`.

- Docs: `content/docs/**`
- Products: `content/products/**`
- About: `content/about/**`
- Licensing: `content/licensing/**`
- Brand: `content/brand/**`
- News posts: `content/news/**`

## Deploy

Works well on Vercel. For other hosts, run:

```bash
npm run build
npm run start
```


## Deploy (Apache static)

This repo can be exported to plain HTML/CSS/JS and served by Apache (no Node runtime needed on the server).

```bash
npm ci
npm run build
# output goes to ./out
```

Copy `out/` contents into your Apache `DocumentRoot` (or a vhost directory). Optionally copy `apache/.htaccess` into that folder.

See `apache/DEPLOYMENT.md` for full details and reverse-proxy alternative.

## Pre-publish drift checks (source-derived pages)

Several pages are **derived from the engine source** and drift whenever the
engine changes but the page is not regenerated (missing commands, stale error
codes, etc.). Run these before every publish; each exits non-zero on drift, so
they gate the publish. They live in the source repo and read it directly.

```bash
# source repo (engine truth) and the Python 3.12 interpreter
CC="D:\code\ccode"
SYNC="$CC\tools\fullstack_docs\command_catalog_sync.py"
SYSCMD="$CC\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260716-001\metacollect_phase\candidate_v8_contracts_resolved\promotion_package_v1\SYSCMD_V8_LIVE_READBACK.csv"
SYSFUNC="$CC\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260716-001\metacollect_phase\candidate_v2_post_comments_help\SYSFUNC_IMPORT_candidate_v2.csv"

# 1. Command catalog vs registry (+ SYSCMD DBF cross-check)
python "$SYNC" check     --source-root "$CC" --catalog content\docs\dottalk\command-catalog.mdx --syscmd "$SYSCMD"

# 2. Function catalog vs function_catalog.cpp + self-registered fns (+ SYSFUNC)
python "$SYNC" fn-check  --source-root "$CC" --catalog content\docs\dottalk\function-catalog.mdx --sysfunc "$SYSFUNC"

# 3. Error-codes page vs xbase_error_codes.hpp (identity, severity, message)
python "$SYNC" err-check --source-root "$CC" --page content\docs\engine\error-codes.mdx

# 4. Messaging/localization locale table vs the REGRESSION LANGUAGE source set
python "$SYNC" loc-check --source-root "$CC" --page content\docs\engine\messaging-and-localization.mdx
```

All four must print `check=PASS`. `--syscmd` / `--sysfunc` are optional (they add
a second DBF cross-check); drop them to validate against source alone. When a
check FAILs, regenerate the page: `command_catalog_sync.py emit --source-root
"$CC" --out <file>` re-derives the command catalog, and the report lists exactly
what is missing/stale for the others.

The tool is BOM-, CRLF-, and inline-comment-robust when parsing `@dottalk.usage`
blocks; keep it that way if you extend it.

## Publish cycle: D:\dev\x64base-site -> build/public artifact -> GitHub Pages -> x64base.com

The live public site is served by GitHub Pages from:

- repository: `https://github.com/deraldg/x64base`
- branch: `gh-pages`
- folder: `/`
- local deployment worktree: `.gh-pages-deploy`
- custom domain: `x64base.com`

Use this from the laptop site root:

```bash
npm run publish:github-pages
```

That command:

1. pulls/rebases `.gh-pages-deploy` from `origin/gh-pages`,
2. refuses to publish if `D:\dev\x64base-site` has uncommitted source changes,
3. runs the static Next export,
4. writes `out/artifacts/site-release.json` with source commit provenance,
5. refreshes `.gh-pages-deploy` from `out/`,
6. writes `CNAME` and `.nojekyll`,
7. commits and pushes `gh-pages`.

Publish policy:

- source edits must be committed before publish,
- `gh-pages` is the deployed artifact history,
- `out/artifacts/site-release.json` records the source branch and commit used for a publish.

There is currently no `C:\` website mirror or staging area. If one is added
after the website workflow is hardened, it must live at the root of `C:\` as a
sibling of `C:\x64base`, never inside the source/runtime staging repository.
Its final name and policy are to be determined.

Observed maintainer source/promotion split:

- implementation/runtime truth: `D:\code\ccode`
- clean staging mirror for source/runtime promotion: `C:\x64base`
- website source truth: `D:\dev\x64base-site`

Normal flows:

```text
D:\code\ccode -> C:\x64base -> GitHub repository
D:\dev\x64base-site -> build/public artifact -> GitHub Pages -> x64base.com
```

Do not reverse the authority chain by copying website prose into manuals or
source-side technical truth.

After publishing, verify:

```bash
gh api repos/deraldg/x64base/pages
```

Expected state:

- `status` is `built`
- `cname` is `x64base.com`
- `https_enforced` is `true`
