# E8 -- website publication: review packet

Run: `DOCFLUSH-20260914-001`
Gate: E8 (website publication)
Status: **REVIEW PACKET.** Everything in this file and in
`gate8_publication_evidence.json` is the author's measurement. The
AUTHORIZATION is a separate file, written by the owner. The author does not
write it.

---

## Why this packet exists at all

Release 145 was published to x64base.com on 2026-09-14 at 06:44:06Z. The owner
authorized it in conversation and the author published it. **No record was
written.**

Both harvest promotions in this same run got full records -- plan, authorization,
apply, and the refusal records retained as evidence. Gate 4 got
`gate4_apply_authorization.json`, which is how `derive_documentation_progress.py`
knows tonight's manual candidate is `MANRUN-20260914T035009Z-36CEEEFD`.

E8 got nothing. The consequence is mechanical, not ceremonial: the site's
progress authority still reports

```
"publication_state": "...publication-not-entered"
"first_open_entry": "E8"
"publication_authorized": false
```

and it is not wrong to do so. By the lane's own evidence, E8 is open. Those three
fields will stay false through every future re-derive, no matter how many times
the site publishes, because there is nothing on disk for a tool to read.

A gate whose closure leaves no artifact cannot be measured. That is the same test
the owner set on 2026-09-14: *a step whose omission produces no finding is not in
the push.*

## What is being authorized

That release 145 -- source commit `6784d3d88` on `codex/lean-sites-publish`,
deployed to `deraldg/x64base:gh-pages`, serving `x64base.com` -- is an entered
publication rather than a local candidate.

All measurements are in `gate8_publication_evidence.json` beside this file.
Summary:

| Check | Result |
| --- | --- |
| website-matrix-check | PASS on all five hard gates |
| docpush_preflight | PASS across nine steps |
| command catalog | 241 keys / 241 rows / 241 parsed / 0 fallback |
| harvest freshness E5 | 14/14 tables match current HELP/META |
| contract drift | CLEAN |
| site build | 177 static pages, 170 indexed, 12,050 words |
| live readback | artifacts, both provenance stamps and the catalog verified on the published origin |

## What this packet does NOT claim

Five items, stated rather than implied, and listed in full under
`known_open_items_this_evidence_does_not_cover`:

1. **Nine content pages carried a superseded current state when release 145
   shipped.** The chrome banner read "Full-stack docs reconciled 2026-09-02" on
   all 151 pages, and `command-reference.mdx` was headed "local, not deployed
   (2026-09-02)". Authorizing E8 does not retroactively make those pages correct;
   it records that publication was entered.

2. **The progress authority was hand-typed at publication time.** Its generator
   was written afterwards.

3. **The site documents no path layout.** Zero of 151 pages reference a path
   environment variable.

4. `validation_review_rows=1`, unexamined.

5. The 164-of-464 coverage sentence remains an owner decision.

## The measurement caveat worth carrying forward

The first uncached read of the live PK artifact returned a deploy two generations
old. The same URL with a cache-busting query returned the current file. The
publisher verifies `site-release.json` with `cache: "no-store"` -- the one file
that would have looked correct either way. A live readback that does not bust the
edge cache can read stale bytes and conclude a good publish failed.

---

## The authorization file the owner writes

Path: `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260914-001/gate8_publication_authorization.json`

Required shape, validated by `derive_documentation_progress.py`:

```json
{
  "schema": "dottalk.fullstack.gate8_publication_authorization.v1",
  "decision": "PUBLICATION_ENTERED",
  "run": "DOCFLUSH-20260914-001",
  "release_number": 145,
  "source_commit": "6784d3d8865b57cec8fa59b5b1f8fd4e34b8c3db",
  "evidence_sha256": "<sha256 of gate8_publication_evidence.json>",
  "publication_state": "<the state string the site should report>",
  "authorized_by": "<owner>"
}
```

`evidence_sha256` of the file as delivered:

```
AA3D42DE23673CFF510F1C6915A62065CC6B1341DE0043C28C4E97D21ABBCC2B
```

Recompute it rather than trusting this line:

```powershell
(Get-FileHash -Algorithm SHA256 `
  D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260914-001\gate8_publication_evidence.json).Hash
```

The binding is the point. An authorization that names a hash cannot silently come
to describe different evidence, which is the same discipline both harvest
promotions used with `plan_manifest_sha256` and `mutation_ledger_sha256`.

Once that file exists, `publication_state`, `first_open_entry` and
`publication_authorized` move from **carried** to **measured** in the progress
artifact, and the pages bound to them can stop saying E8 is open.
