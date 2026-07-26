# DD-016 Next Actions

## Immediate next package

`DD-017 Static DBF Header Parser and Physical Projection Skeleton`

Goal: read DBF/x64 DBF header bytes from a provided data-root copy and emit report-only evidence for `DD_TABLE_VERIFY` and `DD_FIELD_PHYSICAL`.

## Why DD-017 before runtime execution

A static parser can verify physical table facts without launching DotTalk++ and without mutating session state. It is lower risk than running `USE`, `MEMO`, `CDX`, or `BUILDLMDB` commands.

## Required local inputs for later runtime proof

- Known disposable x64 DBF table
- Optional memo sidecar/backend artifact
- Optional CDX/tag pair
- Optional LMDB backend directory
- DotTalk++ executable path
- A data-root copy that may be mutated if optional memo/index/backend proof is authorized

## Still forbidden without explicit authorization

- Running DotTalk++ runtime proof scripts
- Rebuilding HELP DATA
- Running CMDHELPCHK mutators, if any
- Writing catalog/metadata DBFs
- Running `REPLACE` on non-disposable data
- Running `BUILDLMDB CLEAN YES` on non-disposable data
