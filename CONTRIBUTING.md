# Contributing to x64base

The public `main` branch is the canonical collaboration and release branch.
Research and recovery work may happen elsewhere, but a public claim is not
considered current until its source, tests, and documentation are promoted to
`main`.

## Which branch to baseline on -- read this before you start

**Enumerate the published branches. Do not accept the default.**

```
git ls-remote --heads https://github.com/deraldg/x64base.git
```

- `main` is the **lagging public snapshot**. It is the PR target, not the
  authority for what the project currently is.
- `development` is **also published on GitHub** and is the richer, current
  integration branch. Baseline your reading, prior-art checks, and any
  feature or source work on `development`, and record the exact commit you
  used.

So the two answers differ on purpose: **read from `development`, open the pull
request against `main`.** Never propose merging `development` into `main` --
that is forbidden, and a PR shaped that way will be closed.

State the baseline commit in your change. A proposal that does not name the
commit it was built against cannot be reviewed.

## Repository roles

This project is developed across separate trees with distinct roles. You will
only ever interact with the public repository, but the roles explain why
`main` lags and why some documents you may find are not current:

| Location | Branch | Role |
| --- | --- | --- |
| the maintainer's development tree | `development` | Sole development and authoring workspace |
| the maintainer's staging tree | `main` | Sterilized publication staging; the only tree that publishes to GitHub `main` |

Work flows one way: develop -> promote -> publish. Never backward. Website
prose and published documentation are publication surfaces, never sources of
technical truth.

**Some documents on `main` are historical.** A small number of files predate
the current promotion manifest and no longer receive updates. Where any
document on `main` disagrees with this file about branches, roles, or process,
**this file is current**. If you find such a disagreement, say so in your
proposal; drift reports are welcome and useful.

## Before opening a change

1. Build from a clean checkout of your stated baseline, using a documented
   CMake preset.
2. Run CTest with `--output-on-failure`.
3. Add or update regression coverage for behavior changes.
4. Label experimental work as `canary` or `planned`; do not present it as a
   released capability.
5. Do not commit personal paths, runtime state, generated build trees, secrets,
   or scratch notes.

Small, focused pull requests are preferred. Data-format changes should include
the affected flavor, compatibility impact, and a reopen/readback test.

## If you are an AI agent, or using one

Additional expectations, because this project is developed with AI partners and
has been bitten by each of these:

- **Default to report-only.** Write access is a capability, not an
  authorization. Review, audit, and second-opinion requests do not imply
  permission to implement.
- **Name the exact files you would change**, the subsystem, the expected
  behavior change, and how you would prove it, before proposing a change to
  source.
- **Never `git add -A` or `git add .`.** Name exact paths. Verify what is
  staged with `git diff --cached --name-only` before committing.
- **Report by evidence tier and do not inflate it.** Use `planned`,
  `source-evidenced`, and `runtime-proven` precisely. A zero exit code is not
  proof; a green readback is not proof. Say what you actually ran.
- **ASCII only in new content.** Use `--` and `->`, never em-dashes,
  en-dashes, smart quotes, or Unicode arrows. Check with
  `grep -P '[^\x00-\x7F]'`.
- **The inline comment marker in DotScript is `&&`.** A single `&` is the xBase
  macro operator and is never a comment.

A proposal is rejected if it omits its baseline commit, exceeds the scope it
was asked for, includes binaries or generated data, claims proof that was not
performed, or assumes a branch that does not exist.

## Reporting evidence

Use these terms consistently:

- **runtime-evidenced**: exercised by a repeatable test or recorded runtime
  proof against the referenced commit.
- **source-evidenced**: implementation exists but public behavior is not yet
  covered by a repeatable proof.
- **planned**: design direction only.

## Licensing

By contributing, you agree that your contribution may be distributed under
the repository's current license. The root license is presently marked
tentative pending final review; contributors should read it before submitting
work.
