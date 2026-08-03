# Handoff - Publishing a narrow website slice from a dirty checkout

Use this when a reviewed x64base.com change must be published while unrelated
work is present in `D:/dev/x64base-site`.

## The central trap

The source checkout can contain concurrent Portal, diagram, Python, product,
and generated work. A successful build of that checkout does not prove the
publication commit contains only the authorized slice, and publishing its
`out/` directory can leak unstaged work.

Stage exact paths. For overlapping files, stage only the owned hunks and verify
both sides:

```powershell
git -C D:/dev/x64base-site diff --cached --check
git -C D:/dev/x64base-site diff --cached --stat
git -C D:/dev/x64base-site diff
git -C D:/dev/x64base-site status --short
```

After the source commit, build that commit in a disposable clean clone before
pushing. Do not reuse static output produced from the dirty source checkout.

## The maintained gates

`D:/dev/x64base-site/package.json:11` defines the build chain: diagram drift,
public-content guard, build-output cleanup, Next.js production build, and Sites
packaging. `D:/dev/x64base-site/scripts/publish-github-pages.mjs:126-155`
requires a clean source tree, rebuilds it, records release metadata, replaces
the dedicated Pages checkout, commits, and pushes.

Measure the current commands from those files rather than copying a stale
version from this handoff.

## Windows provenance line endings

The diagram checker compares each provenance sidecar as exact text at
`D:/dev/x64base-site/scripts/check-diagrams.mjs:20-26`. A normal Windows clean
clone can check JSON out as CRLF while the checker synthesizes LF, producing a
`provenance sidecar is stale` finding even when hashes and content fields agree.

For a disposable clone only:

1. set `core.autocrlf false`;
2. rewrite tracked files from the index;
3. confirm diagram checks pass;
4. if the publisher's clean-tree check now sees only line-ending-equivalent
   paths, mark those paths `assume-unchanged` in that disposable clone only;
5. run the unmodified publication script.

Do not set assume-unchanged in the maintained source checkout. Do not commit a
line-ending sweep as part of an unrelated publication.

Turbopack also rejects a `node_modules` junction pointing outside the clone.
Use locally installed dependencies inside the disposable clone when an exact
clean-clone build is required.

## What live proof means

The source push is not the deployment. The Pages commit is not yet the live
site. Report all three stages separately:

1. source branch commit and remote push;
2. `gh-pages` commit and remote push;
3. GitHub Pages API status `built`, followed by cache-bypassed HTTP checks.

Finally read `/artifacts/site-release.json` and confirm its source commit equals
the source commit that passed the build. Check scoped pages for distinctive
expected text; a 200 response alone is insufficient.

## Publication boundary

GitHub Pages is the canonical public path. `C:/x64base` is not part of ordinary
website-source publication. Treat a private Sites mirror as a separate target
and attempt it only when the request includes it.
