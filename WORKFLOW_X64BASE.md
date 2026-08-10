# x64base Promotion Workflow

This file describes repository roles without binding commands to a particular
drive letter, mount point, user profile, or workstation layout.

The durable authority is
`docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md`. If this summary
and that contract disagree, the contract wins.

## Repository Roles

1. **Development workspace** -- the configured `development` checkout. This is
   the sole authoring workspace.
2. **Publication staging** -- a clean checkout based on current GitHub `main`.
   It receives only a reviewed source slice from development.
3. **GitHub `main`** -- receives the verified staging commit.

Never merge or push the `development` branch to `main`. Promotion copies an
explicitly reviewed file set; it does not merge branch history.

## Promotion Sequence

1. Confirm the development checkout is on `development` and identify unrelated
   dirty work that must remain untouched.
2. Confirm publication staging is based on current GitHub `main`, then create a
   main-based promotion branch.
3. Copy only the approved, named source and support files from development.
4. Reconcile intentional additions, deletions, and case-only renames.
5. Exclude reproducible runtime data and build output. In particular, do not
   promote `.mdb` files.
6. Run the applicable Windows and WSL/Linux configure, build, and test lanes in
   staging.
7. Stage named paths only, review the staged diff, and commit the verified
   promotion branch.
8. Publish through the maintained main-branch review process.

## Portability Rule

Repository launchers and build scripts must derive the repository root from
their own location or accept it as an argument. They must not embed local drive
letters, WSL mount paths, user names, or absolute toolchain locations.

Toolchains are supplied through environment variables such as `VCPKG_ROOT` or
through explicit command arguments. Build directories are relative to the
active checkout unless the caller deliberately provides another location.

## Verification Boundary

A successful development build does not verify staging. A successful staging
build does not publish anything. Work is published only after the staging diff,
commit, and remote result have each been verified.
