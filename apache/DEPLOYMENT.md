# Deploy to Apache

You have two sane options:

## Option A — Static export (recommended for simple hosting)

This produces a plain static site you can serve directly from Apache.

### 1) Build static output

```bash
npm ci
npm run build
```

This creates an `out/` folder.

### 2) Copy to Apache

Copy **the contents** of `out/` into your Apache `DocumentRoot` (or a vhost directory), for example:

```bash
rsync -av --delete out/ /var/www/example.com/public/
```

Then copy `apache/.htaccess` into that same `public/` folder (optional but recommended):

```bash
cp apache/.htaccess /var/www/example.com/public/.htaccess
```

### 3) Apache vhost

Use `apache/httpd-vhost.conf` as a starting point. Ensure your vhost has:

- `AllowOverride All` (or at least `FileInfo Options`) if you use `.htaccess`
- `DirectoryIndex index.html`

## Option B — Reverse proxy (keep Next.js server features)

If you later add server-only features (API routes, auth, server actions), use Apache as a reverse proxy.

1) Run the app on the server:

```bash
npm ci
npm run build
PORT=3000 npm run start
```

2) Configure Apache with `mod_proxy` and `mod_proxy_http` and add the reverse proxy vhost snippet in `apache/httpd-vhost.conf`.

> In this mode, Apache is not executing your app; it’s forwarding requests to the Node server.
