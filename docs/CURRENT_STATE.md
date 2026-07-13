# Current State

Status: active beta research software.

## Demonstrated public baseline

- C++20 DBF-family runtime and command shell source.
- Portable core configuration on Windows, Linux/WSL, and macOS toolchains.
- Optional LMDB index-command, Turbo Vision, wxWidgets, and Python integration lanes.
- Public CI on `main` and CTest registration for repeatable checks.

## Important limitations

- No production-readiness claim.
- No atomic transaction guarantee spanning DBF, memo, and index persistence.
- x64 widening remains backend- and command-path-specific; it is not yet a
  universal unlimited-scale guarantee.
- GUI/TUI, education, SelfDoc, and campus surfaces mature independently and
  should not be inferred from core build success.
- The root MIT license is tentative pending final review.
- No stable binary release exists until the first GitHub beta release is
  published.

## Release gate

A beta release requires green Windows and Linux builds, passing CTest, a clean
checkout build, release notes, checksums, a known-limitations list, and an
explicit license-status statement.
