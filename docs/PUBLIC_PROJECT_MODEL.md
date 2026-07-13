# Public Project Model

## Authority

The public `main` branch at `deraldg/x64base` is the canonical source for
collaboration, CI, releases, and public technical claims.

Maintainer implementation trees, recovery branches, staging mirrors, generated
manual trees, and website source trees may contain newer experiments. They do
not supersede `main` for an external user until the relevant source, tests, and
documentation are promoted through a reviewed change.

## Evidence order

1. A tagged release plus its checksums and known limitations.
2. A green `main` CI run for the referenced commit.
3. Repeatable tests and runtime transcripts stored with that commit.
4. Source evidence with an explicit beta/canary label.
5. Plans and design documents labeled as planned work.

Documentation and website prose explain evidence; they do not create runtime
truth by themselves.

## Branch policy

- `main`: supported public beta line.
- `codex/*` and other feature branches: review candidates.
- recovery/history branches: preservation material, not release lines.
- `gh-pages`: generated publication output only.

Changes should reach `main` through pull requests with a clean build and tests.
Direct pushes should be reserved for repository recovery or urgent security
maintenance.

## Website policy

The website should lead with the concrete DBF runtime and one runnable example.
Named research and educational lanes belong below the core explanation and
must carry their maturity status. Pages should use distinct titles and
descriptions, link only to HTTPS destinations, and identify the evidence commit
when describing observed project state.
