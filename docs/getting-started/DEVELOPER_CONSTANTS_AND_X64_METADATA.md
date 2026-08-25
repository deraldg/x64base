# Developer Constants And X64 Metadata

## Why this note exists

This is a prose note for developers. It is not meant to replace source
contracts, command contracts, or generated help.

Rule:

- command/runtime contract truth belongs in source and `dotref.hpp`
- generated help/manual surfaces should harvest that truth
- prose like this exists to explain design intent, tuning points, and where to
  look in source when a developer needs to change the system

If a behavior description here disagrees with source contracts or runtime
evidence, source and runtime win.

## The short version

Not every limit in DotTalk++ is fixed forever.

Some important values are build-time engine constants. Others are carried as
runtime/file metadata. In the `x64` lane, some naming behavior is even
file-specific rather than workspace-wide.

That means:

- maximum open work areas is an engine constant
- maximum field count is an engine constant
- old DBF/VFP-compatible mirror values still exist for compatibility
- `x64` wide metrics travel in the `x64` large header extension
- `x64` authoritative table/field names can vary by file depending on whether
  that file carries `X64M` metadata
- two tables in the same workspace do not have to share identical name-vector
  conditions

## Build-time engine constants

Primary source:

- [xbase.hpp](D:/code/ccode/include/xbase.hpp)

Current top-level constants include:

- `MAX_FIELDS = 128`
- `MAX_INDEX = 5`
- `MAX_AREA = 256`
- `HEADER_TERM_BYTE = 0x0D`

These are engine build constants, not session commands. If you change them, you
are changing the compiled engine contract and should expect to rebuild and
re-test.

Practical meaning:

- `MAX_AREA` controls how many live work areas the engine can hold at once
- `MAX_FIELDS` controls the current maximum number of fields a table may expose
  through the engine layer
- `MAX_INDEX` is part of the older index-slot model and still matters in parts
  of the compatibility/runtime surface

## Compatibility mirrors versus wide x64 truth

Primary sources:

- [xbase.hpp](D:/code/ccode/include/xbase.hpp)
- [xbase_64.hpp](D:/code/ccode/include/xbase_64.hpp)

Classic header fields in `HeaderRec` still contain 16-bit-compatible mirrors
such as:

- `data_start`
- `cpr` (record length)

The `x64` lane extends that with wide metrics in `LargeHeaderExtension`:

- `record_count`
- `data_start_64`
- `record_size_64`
- `autoq_next`
- `table_flags`

Important design point:

- compatibility mirrors may saturate or fall back for older geometry
- runtime truth for `x64` should come from the wide extension values when they
  are present

That is why the `x64` matrix/metrics canary matters: it proves the runtime can
survive records beyond old 16-bit-era boundaries instead of only documenting
them.

Relevant canary:

- [x64_matrix_metrics_boundary_canary.dts](D:/code/ccode/dottalkpp/data/scripts/canaries/x64_matrix_metrics_boundary_canary.dts)

## X64 names are not just one global workspace limit

Primary source:

- [xbase_64.hpp](D:/code/ccode/include/xbase_64.hpp)

Current `x64` naming constants include:

- `X64_TABLE_NAME_LENGTH = 128`
- `X64_FIELD_NAME_LENGTH = 128`
- fallback descriptor token width stays DBF/VFP-compatible at 10 bytes

But the key point is not only the constants. The key point is policy:

- `x64` may carry authoritative table/field names in an `X64M` metadata block
- if a file has `X64M`, the runtime can prefer those names
- if a file does not have `X64M`, the runtime falls back to descriptor tokens
- fallback behavior is influenced by `table_flags`

So, within one workspace:

- one file may have authoritative long names available through metadata
- another file may only expose fallback descriptor names
- they do not have to share the same vector/name state just because they are
  opened together

That is why it is wrong to think of `x64` name behavior as one workspace-wide
switch. It is fundamentally file-owned metadata.

## Current CREATE-side practical constraint

Source:

- [cmd_create.cpp](D:/code/ccode/src/cli/cmd_create.cpp)
- [dbf_create.cpp](D:/code/ccode/src/xbase/dbf_create.cpp)

Current parser/create behavior still imposes practical construction limits,
including:

- current `CREATE X64` parsing caps a single `C` field length at `4096`
- non-character X64 fields are still constrained much more conservatively

That is a current creation-path rule, not the same thing as the full design
ambition of the `x64` file format.

In other words:

- file format capacity
- runtime open/read/write capacity
- command parser/create convenience limits

are related, but they are not the same layer.

## Where to look first

If you need to change or study these limits, start here:

- [xbase.hpp](D:/code/ccode/include/xbase.hpp)
- [xbase_64.hpp](D:/code/ccode/include/xbase_64.hpp)
- [dbf_create.cpp](D:/code/ccode/src/xbase/dbf_create.cpp)
- [dbf_file.cpp](D:/code/ccode/src/xbase/dbf_file.cpp)
- [dev-08-dbf-x32-x64-formats.md](D:/code/ccode/docs/manuals/developer/dev/dev-08-dbf-x32-x64-formats.md)

## Policy reminder

When changing any of these values:

- update source contracts first
- update `dotref.hpp` only where command/reference truth belongs there
- add prose only where explanation is needed for manuals, onboarding, or the
  website
- prove the change with canaries or focused runtime scripts, not prose alone
