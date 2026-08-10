# x64base AI Portal -- you are on the wrong branch

You are reading the `main` branch. `main` is a lagging, frozen public snapshot.
It is NOT the onboarding source, and nothing on this branch may be used to
derive current state (lane numbers, current targets, work status, doctrine
versions).

## Where to go

The canonical AI Portal, the onboarding corpus, and the current integration
baseline live on the `development` branch of this same repository:

    https://github.com/deraldg/x64base/tree/development

Read `AI_PORTAL.md` at the root of THAT branch and follow its Mandatory Start.

## The rule (binding for every AI partner)

Before reading source or writing any proposal or change package:

1. Enumerate the published branches -- do not trust the default:

       git ls-remote --heads https://github.com/deraldg/x64base.git

2. Baseline on `development` and record its exact commit in your package.
   Use `main` only if the maintainer names it for the task.
3. If you cannot reach `development`, say so explicitly and mark your work
   provisional. Do not present a `main`-baselined package as current.

Building against `main` without enumerating branches is a hard onboarding
failure. It has happened; it produced colliding lane numbers and proposals
against retired structure. This page exists so it does not happen again.

## Why this page is nearly empty

Anything written here would freeze the moment `main` was promoted and then
mislead every reader until the next promotion. So this page asserts nothing
perishable: it only points. The pointer stays true regardless of how far
`main` lags.

Maintainer: Derald Grimwood (member.derald). This pointer supersedes any older
full-portal text previously published on `main`.
