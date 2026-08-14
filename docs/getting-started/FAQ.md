# x64base FAQ

## Is this a clone of classic xBase?

No. x64base and DotTalk++ are a lineage evolution: they keep the practical clarity of xBase tables, work areas, indexes, relations, and command-driven exploration while modernizing the runtime, metadata, documentation, and GUI lanes.

## What file formats are used?

The native x64 lane uses DBF_64 for table records and FPT64 for memo data. DotTalk++ also supports older xBase-family table work, including MS-DOS/classic xBase-style DBF data, Visual FoxPro-style DBF data where implemented and tested, and x32 compatibility tables used by the sample workspaces.

Default index behavior is family-aware:

* x64 / DBF_64 workspaces use CDX as the logical index surface with LMDB as the physical backend.
* Visual FoxPro-style and MS-DOS/classic xBase x32 workspaces default to CNX.
* IDX/INX remain optional legacy/simple index paths and compatibility surfaces.

## Where do I find tunable engine constants and x64 naming/metric notes?

Start here:

- [DEVELOPER_CONSTANTS_AND_X64_METADATA.md](D:/code/ccode/docs/getting-started/DEVELOPER_CONSTANTS_AND_X64_METADATA.md)

That note points at the source-owned constants and explains the difference
between:

- build-time engine constants such as work-area count and field count
- compatibility mirrors versus wide `x64` metrics
- file-owned `x64` metadata such as authoritative table and field names
