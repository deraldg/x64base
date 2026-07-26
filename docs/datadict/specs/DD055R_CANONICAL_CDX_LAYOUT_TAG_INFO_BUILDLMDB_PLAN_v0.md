# DD-055R Canonical CDX Layout / TAG / INFO / BUILDLMDB Plan v0

Created UTC: `2026-05-28T03:09:13+00:00`

## Purpose

DD-055R corrects the index lane after the user clarified the actual DotTalk++ workflow:

```text
1. Create the CDX/index container/layout.
2. Add tags.
3. Inspect with INFO.
4. BUILDLMDB reads the CDX layout and creates LMDB indexes.
```

DD-055 v0 is reclassified as partial artifact evidence, not canonical CDX/LMDB proof.

## Boundary

Allowed:

```text
read DD-054/DD-055 reports
scan source/help for command syntax evidence
emit corrected CDX workflow plan
emit candidate template script
```

Not allowed:

```text
CDX/index creation
BUILDLMDB execution
active catalog mutation
staging catalog mutation
source edits
HELP/META/CMDHELPCHK mutation
promotion
```
