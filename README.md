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
