# SQLsel Default-Suite Promotion Proof -- 2026-09-03

Status: runtime-proven on Windows MSVC Release, review-needed.
Lane: AIF-074.
Baseline commit: `e7d6ef1309888ab8a7c4ef0b474a06bfd3b066db` plus the
promotion-only working-tree change recorded by this document.

## Change under proof

Four registered, fail-closed SQLsel validators moved from explicit-only to the
default `REGRESSION ALL` suite:

- `SQLSEL_BUFFER_VIS`
- `SQLSEL_JOIN_EDGES`
- `SQLSEL_LEFT_JOIN`
- `SQLSEL_JOIN_FAMILY`

The primary change is four `in_default_suite` values from `false` to `true`.
The associated summaries state the distinct coverage hole that justifies each
recurring cost. Promotion testing also found and repaired a pre-existing
teardown defect described below.

## Why each belongs in the default suite

| Spec | Default coverage that otherwise does not exist |
| --- | --- |
| `SQLSEL_BUFFER_VIS` | SQLsel committed truth while native TableBuffer holds a dirty preview |
| `SQLSEL_JOIN_EDGES` | CDX collision revalidation, wrong-tag scan fallback, reversed lock order, and caller FLOCK preservation |
| `SQLSEL_LEFT_JOIN` | Produced absence versus blank, LEFT extension counts, and outer-WHERE SQL UNKNOWN |
| `SQLSEL_JOIN_FAMILY` | RIGHT, FULL, and CROSS answer/path/refusal behavior |

All four fixtures are self-bootstrapping and self-erasing under SANDBOX. None
is marked `mints_catalog`, so this promotion adds no workspace-catalog rows.

## Teardown defect found by promotion

The post-run residue sweep found five ignored `<table>.cdx.meta` files carrying
SQLsel fixture names. A clean-state probe confirmed they were recreated by
`BUILDLMDB` and survived `ERASE TABLE`. Source inspection found the cause:
`build_sidecar_list()` enumerated `.cdx` and its LMDB directory but not the
adjacent `.cdx.meta` file.

`ERASE TABLE` now includes `.cdx.meta` in its existing sidecar inventory. The
INNER, adversarial INNER, LEFT, and RIGHT/FULL/CROSS validators also fail closed
if their one, two, one, or one generated metadata files survive teardown. The
gate therefore checks the cleanup result rather than trusting the ERASE success
message.

## Build and runs

The runtime was rebuilt from the changed source:

```powershell
cmake --build D:\code\ccode\build --config Release --target dottalkpp
```

Final built binary SHA-256:

```text
E49610499EE345E01E319CBF509BB8324A5D9CD5F270CA6AFB29ED3EB97929CD
```

Three post-repair fresh launcher processes ran the complete default suite. The
first began with all five previously surviving metadata files restored into the
active INDEXES/SANDBOX root; the later runs began clean. The last run followed
the final source-owned summary corrections:

```powershell
& D:\code\ccode\datarun.ps1 -CommandLines 'REGRESSION ALL'
```

Each run executed 26 default specs. They took 11.60, 12.29, and 11.42 seconds
including launcher overhead. The full temporary transcripts had these SHA-256
values:

```text
pre-populated cleanup run  99C9F3A9A115E3153EE215D6F45564C68327282F1D74B7927DBF81CC568539CA
final clean run           91209285961A003255819D9E1CA7F5546B2EE1F7FD39811947A666ED50F49841
committable-source run    A6FCB993CFECC789C8FFD9CB5CAC5CE4F011AC9F9D9402B3864A452CBF0ED249
```

## Exact repeated gate results

All three transcripts contained the following results and no gated failure line:

```text
SQLSEL BUFFER ORACLE: PASS -- 5/5 committed row sets equal SQLite; dirty preview 2/2; cursors 3/3; rollback and commit distinguished.
SQLSEL JOIN ORACLE: PASS -- 4/4 row sets equal SQLite; cursors 2/2; refusals 3/3; access paths 4/4 (CDX seek 2, scan 2); cleanup 1/1.
SQLSEL JOIN EDGES ORACLE: PASS -- 4/4 row sets equal SQLite; cursors 4/4; refusals 2/2; read transactions 4/4; caller lock preserved; access paths 4/4 (CDX seek 2, scan 2, hybrid 0); probe/candidate counts exact; cleanup 2/2.
SQLSEL LEFT JOIN ORACLE: PASS -- 7/7 row sets equal SQLite; blank and produced absence distinct; outer WHERE and UNKNOWN proven; left-extended reports 7/7; cursors 2/2; caller lock preserved; paths 3 seek/4 scan/0 hybrid; read fences 7/7; cleanup 1/1.
SQLSEL JOIN FAMILY ORACLE: PASS -- 14/14 row multisets equal SQLite; RIGHT/FULL absence and outer WHERE/UNKNOWN and CROSS product proven; cursors 2/2; caller lock preserved; refusals 3/3; paths RIGHT 3 seek/3 scan, FULL 3 seek/3 scan, CROSS 2 scan; hybrid 0; fences 14/14; extension reports 18/18; cleanup 1/1.
```

The L3 production-catalog isolation arm also passed 6/6 before and after each
suite. This proves the promoted specs executed successfully in suite order and
the suite restored the production catalog boundary. Filesystem readback after
the post-repair runs found all five named `.cdx.meta` files absent.

Native CTest also passed 22/22 in 13.36 seconds.

## WSL/GCC cross-platform run

The maintained `wsl-lean` target compiled and linked `cmd_erase.cpp`,
`cmd_regression.cpp`, and `libsqlsel.a`, then staged the Linux runtime. A fresh
Linux process executed the same 26-spec default suite with the same four
promoted validator summaries, cleanup counts, two 6/6 L3 brackets, and zero
gated failure lines.

```text
WSL runtime SHA-256  93ED18D7278CD1134E164DB011BBA085F7102540472A09AB3777F0B2E3301933
WSL transcript      2D805A3C7246A514D69F6ADA7E083ED78F0D44809411D3062DB07599E3FAEC92
```

## Mutation proof

The new `.cdx.meta` sidecar entry was temporarily disabled while the cleanup
validator remained active. `REGRESSION RUN SQLSEL_INNER_JOIN` then produced:

```text
SQLSEL JOIN ORACLE: FAIL -- cleanup left CDX metadata 'D:\code\ccode\dottalkpp\data\INDEXES\SANDBOX\SQLJENR.cdx.meta'
Message  : Invalid argument
```

Mutation transcript SHA-256:

```text
C4CE5B2707F0616B81A59AE2834994F6C558AE0A5C740CCBE8685C24BDE2ABFF
```

After restoring the sidecar entry and rebuilding, the same targeted regression
returned `cleanup 1/1`, and filesystem readback found the metadata file absent.
Restored-green transcript SHA-256:

```text
9910120FE8961CD4F23FAB727FCE929FD79107F53F739135D5E569251C65E138
```

## Disposition

The coverage gap is closed in source and runtime. Approval remains
`review-needed`; this record establishes execution and result, not maintainer
approval or publication to `main`.
