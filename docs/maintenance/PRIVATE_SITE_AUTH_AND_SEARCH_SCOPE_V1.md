# Private-Site Auth + Site Search -- Gold-Standard Scope

**Status:** scoping / design (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-08. Not a commitment; a priced plan. Two threads, one decision: **what is public
versus gated**, and the dottalkpp gateway is the hinge.

Framing convention (house style): each choice is a GOOD / BETTER / BEST ladder, priced. **We go
gold (BEST) unless the cost is platinum** -- and where it is, it says so with the evidence.

## 0. The one decision underneath both

GitHub Pages serves static files from a CDN with **no server in the request path**. It cannot run
a search query and it cannot check a credential before handing over a file. Everything it serves
is public. So the site splits cleanly in two:

- **Public surface** -> stays on GitHub Pages. Search is solved client-side (Part A).
- **Gated surface** (the private references: `/memory`, `/portal`, the `/AI` views) -> cannot be
  gated on GitHub Pages at all. It must move behind a host that runs your own auth (Part B).

The boundary already exists: those sections are `noindex`, out of nav and sitemap. This plan just
makes the boundary enforceable instead of honor-system.

Why dottalkpp, plainly: a static host **fundamentally** cannot authenticate or search
server-side. The engine already ships a gold-standard credential system and an HTTP gateway. This
is the case where serving the site from dottalkpp is not nostalgia -- it is the only thing that
can do the job GitHub Pages structurally cannot.

## Part A -- Public static-site search

**Problem.** No server, so no server-side search. Nobody has shipped the client-side half.

**Approach (BEST): Pagefind.** A post-build step indexes the exported `out/` HTML, chunks the
index so the browser downloads only what a query needs, and provides a drop-in search box. Fully
static; nothing server-side.

- **Exclude the privates.** The index MUST skip `/memory`, `/portal`, `/AI` or search would leak
  exactly what was unlisted. Two belts: (1) Pagefind honors `data-pagefind-ignore`; (2) run the
  indexer only over the public route set, never over the private output. Because those routes are
  already `noindex` and stripped from public builds, this aligns with existing governance.
- **Build integration.** Add `pagefind --site out` after `next build` in the `build` script;
  the generated `pagefind/` bundle ships with the static export. It introduces no machine paths,
  so `check-public-content` stays green; add a matrix row for the search asset.
- **The ladder.** GOOD: a hand-built MiniSearch/FlexSearch JSON index (more code to maintain,
  full control). BETTER/BEST: Pagefind (purpose-built for static export, chunked, least code).
  Recommended: Pagefind.

**This is the recommendation Derald accepted.** Part B is the caveat he raised.

## Part B -- Private, auth-gated area (dogfood the BBS identity system)

**The auth is worthy.** Inspected 2026-08-08:
- Credentials are Argon2id PHC strings via libsodium
  (`src/identity/identity_admin.cpp` `make_credential` -> `$argon2id$...`; `security/token_crypto.hpp`).
- Agent tokens are 256-bit opaque values from the OS CSPRNG, base64url, **shown once**
  (`issue_token`, `gen_token`).
- The wire gate requires `AUTH <member.key> <token>` before any command
  (`src/bbs/bbs_server.cpp`), verified by `login()` with a deliberate **no-leak** on which half
  was wrong.
- Every action is RBAC-checked; the listener binds `127.0.0.1` only with `SO_EXCLUSIVEADDRUSE`;
  the module's own header names it the highest-risk slice and lists the review points.

**The blocker is hosting, not auth.** `bbsd` is loopback-only, speaks a raw TCP line protocol
(not HTTP), and is egress-isolated by design. A browser on the internet cannot reach it and
GitHub Pages cannot call it. To gate a private area of the live site with this auth, that area
must be served by a host that runs an HTTP front wired to the identity system.

### Architecture (BEST)

An **HTTP auth gateway** -- extend the existing `tools/reports/serve_dynamic_reports.py`
(`ThreadingHTTPServer` + `Handler`, already routes `/AI`, proxies an upstream, `--bind/--port`):

1. **Login route.** `GET /login` renders a form (member.key + token); `POST /login` validates.
2. **Validation by dogfood, zero reimplementation.** The gateway opens a loopback socket to
   `bbsd` and sends `AUTH <member.key> <token>` -- the *same* protocol agents use. If `bbsd`
   accepts (its Argon2id `login()`), the credential is good. `bbsd` stays the single source of
   auth truth; the gateway never hashes or stores a credential itself.
3. **Session.** On success, issue a signed, short-lived, `HttpOnly`/`Secure`/`SameSite=strict`
   cookie. Subsequent requests to gated paths check the cookie; no cookie -> 302 to `/login`.
4. **Serve the private build** (the `/memory`, `/portal` output) only to authenticated sessions;
   401/redirect otherwise. The public static site is untouched on GitHub Pages.

### Hosting

- A host you control that is internet-reachable: a small VPS, **or** your own machine behind a
  tunnel (Cloudflare Tunnel / Tailscale Funnel) so no home port is opened directly.
- TLS mandatory (Let's Encrypt on a VPS, or the tunnel provider's edge cert).
- DNS: a subdomain such as `private.x64base.com` points at the gateway; `x64base.com` stays on
  GitHub Pages.
- **`bbsd` stays loopback.** The hardened gateway is the ONLY internet-exposed seam and it calls
  auth locally. The raw BBS TCP protocol is never exposed.

### Hardening (this is the highest-risk slice -- treat it that way)

TLS everywhere; login rate-limiting + exponential backoff + lockout; keep the request-size caps
the code already implements; token rotation (`USER TOKEN` re-issue) and short token lifetimes;
`HttpOnly`/`Secure`/`SameSite` cookies with a signed, rotating server secret; CSRF token on
`POST /login`; audit every login via the BBS event record the engine already writes; fail closed.

### The trade-off, named

This introduces a **public, internet-facing authentication surface**, a real change from
"loopback-only, egress-blocked." Mitigation: only the minimal hardened gateway is exposed, not
`bbsd`; everything else stays local. This is a deliberate posture decision for the owner, not a
default. If the appetite for an exposed surface is zero, the honest alternative is: keep the
private area **local-only** (the current state) and share it via the tunnel on demand rather than
as a standing public endpoint. That is a legitimate BEST-for-now, not a failure.

### Milestones (each its own PDLC; engine-touching ones are maintainer/host handoffs)

| Phase | Delivers | Gate |
|---|---|---|
| M0 | Auth-relay proof: gateway validates a login by relaying `AUTH` to loopback `bbsd`; correct accept/deny, no-leak preserved | local canary: good token in, bad token out |
| M1 | Session cookies + gated static serving, all on loopback | authed session sees private build; anon gets `/login` |
| M2 | Internet exposure via tunnel + subdomain + TLS; `bbsd` still loopback | `private.x64base.com` serves login over TLS |
| M3 | Hardening: rate-limit, lockout, rotation, CSRF, audit, size caps | adversarial pass; documented review points cleared |
| M4 | Move the private content (`/memory`, `/portal`) behind the gate; public site drops any public link to them | public build has zero inbound links to gated paths |
| M5 | (Optional) server-side search for the gated area, now that a server exists | search over gated content, authed only |

## Registration

- **Claimed: AIF-097** (run COWORK-20260808-001, member.derald, 2026-08-08). The search
  interface combined with security is ONE AIF with its own lifecycle -- the phase register
  (M0-M5 above) IS that lifecycle. Do NOT reuse AIF-052. It was claimed with (host-side;
  use the repo venv `$py12`, and a real run id with NO angle brackets -- PowerShell treats `<` as
  a reserved operator):
  `$py12 = "D:\code\ccode\.venv312\Scripts\python.exe"` then
  `& $py12 tools\coordination\session_coordinator.py claim-aif --member member.derald --run RUNID --lane "private-site auth + search"`
  (replace RUNID). Then add the intake row and stamp the AIF number into this charter.
- Parent projects: `project.x64base.website` (Part A search) and `project.bbs.cooperation` /
  identity (Part B auth). Steward assigns per milestone.
- Extends the existing gateway (`tools/reports/serve_dynamic_reports.py`) and the identity system
  (`src/identity/identity_admin.cpp`, `src/bbs/bbs_server.cpp`); consumes, does not reinvent.
- Asides encountered while building this lane follow the standing **aside rule** (no PDLC unless
  promoted) -- see `labtalk/ai_portal/AI_GLOSSARY_V1.md`.

## Recommendation

- Part A now (cheap, self-contained, unblocks public search): ship Pagefind, exclude privates.
- Part B as a chartered lane when you want the private area truly live -- BEST is the dottalkpp
  auth gateway relaying to loopback `bbsd`; the deliberate cost is one hardened public seam.
