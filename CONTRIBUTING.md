# Contributing to x64base

The public `main` branch is the canonical collaboration and release branch.
Research and recovery work may happen elsewhere, but a public claim is not
considered current until its source, tests, and documentation are promoted to
`main`.

## Before opening a change

1. Build from a clean checkout using a documented CMake preset.
2. Run CTest with `--output-on-failure`.
3. Add or update regression coverage for behavior changes.
4. Label experimental work as `canary` or `planned`; do not present it as a
   released capability.
5. Do not commit personal paths, runtime state, generated build trees, secrets,
   or scratch notes.

Small, focused pull requests are preferred. Data-format changes should include
the affected flavor, compatibility impact, and a reopen/readback test.

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
