<!-- Provenance: authored 2026-07-25, found untracked in src/core/ on 2026-08-30 and
     filed here unchanged in substance. src/core/ was the directory whose stale
     dbf_create.cpp caused the AIF-043 duplicate-symbol defect (AI_PORTAL.md:361);
     it is a source tree, not a document store, and these were never tracked there.
     Curly quotes converted to ASCII per house style -- seven characters, no wording
     changed. Original filename: Header Trinity and x64 Vector Metadata Contract.txt -->

# DotTalk++ Header Trinity and x64 Vector Metadata Contract

---

## 1. Header Trinity

The header codex for DotTalk++ consists of three core file-format headers:

- `xbase.hpp`
- `xbase_vfp.hpp`
- `xbase_64.hpp`

These form the canonical storage/header lineage for the engine.

### Roles

#### xbase.hpp
Core engine contract and runtime model.

- Base header/field structures
- `DbArea`
- Runtime schema caching
- Core navigation behavior

#### xbase_vfp.hpp
FoxPro / VFP lineage bridge.

- VFP header structures
- VFP field descriptors
- Compatibility mapping into runtime

#### xbase_64.hpp
x64 expansion layer.

- x64 extension blocks
- Metadata handling
- Large-file support
- Vector metadata system

---

## 2. CLI Boundary

`xbase_cli.hpp` is **not part of the storage codex**.

It exists only as a boundary layer between:

- engine
- CLI/shell

### Layering
