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

## Publish cycle: laptop -> C:\x64base -> GitHub Pages -> x64base.com

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
2. runs the static Next export,
3. stages the built site to `C:\x64base\dottalk-webui\public-site`,
4. refreshes `.gh-pages-deploy` from `out/`,
5. writes `CNAME` and `.nojekyll`,
6. commits and pushes `gh-pages`.

To stage only the local runtime mirror after a build:

```bash
npm run build
npm run stage:cx64base
```

After publishing, verify:

```bash
gh api repos/deraldg/x64base/pages
```

Expected state:

- `status` is `built`
- `cname` is `x64base.com`
- `https_enforced` is `true`
