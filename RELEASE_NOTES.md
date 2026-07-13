# x64base 0.6.0-beta — draft release notes

This is an evaluation release of the DotTalk++ / x64base educational DBF
runtime. It is not production-ready and is not a drop-in replacement for a
commercial xBase product.

## Included

- Windows x64 core runtime.
- Curated runtime data required by the installed command shell.
- Source archive supplied automatically by GitHub.
- SHA-256 checksum for the Windows ZIP.

## Known limitations

- No atomic transaction guarantee spans DBF, memo, and index persistence.
- LMDB indexing, Turbo Vision, wxWidgets, and Python bindings are optional lanes
  and are not included in the core Windows artifact.
- x64 widening is not yet proven for every command and index backend.
- The MIT license designation is tentative pending final review.
- Back up data before evaluation and use disposable copies for mutation tests.
