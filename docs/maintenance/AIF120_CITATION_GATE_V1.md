---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-051
  recorded_at_utc: 2026-08-19T16:25:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 1757f141c
  authorization:
    requested_by: maintainer (member.derald), in-session, "continue, authorized" --
      wiring the citation check into the pre-push gate and making its output
      survivable.
  report:
    path: docs/maintenance/AIF120_CITATION_GATE_V1.md
    kind: ruling
---

# AIF-120 -- R43: the citation check earns its place in the gate

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R42 section 6 closed with one admission: *"Nothing checks this automatically. R42.3
names a one-command check and nothing runs it."* Commit `1757f141c` added that check
to the pre-push gate as portal check 6, advisory. It fired on its own commit -- and
was right to. This ruling is about what happened next, because a check that is right
every single time is a check nobody reads by the third day.

## 0. Correction first: "both parse" is not a test

While rewriting the extraction loop to honour the new marker, I dropped the `return`
from `cited()` in **both** tools. I then reported them as good on the evidence that
they parsed.

They did parse. `cited()` returned `None`, and the first thing either tool does with
the result is iterate it. Neither tool could have run.

R40.2 wrote, one day earlier and about the wx backend: *"for a compiled target, 'it
builds' is a syntax check."* The same sentence is true of Python and I did not apply
it to my own tooling. `python -c "import x"` proves the file is syntactically legal
and proves nothing about behaviour. The fix is one line in each file; the finding is
that this class of error survives every check that does not execute the code path.

Both tools now have a behaviour test run before shipping: a fixture document with a
suppressed citation, an unsuppressed one, and a control, asserting that the two tools
agree and that suppression is per-line. That test found nothing new -- it was written
after the defect -- but it is the check that would have.

**Correction count for this run: 28.**

## 1. Why a permanent advisory is a broken advisory

The gate's own commit reported:

```
cited-paths: 3 document(s), 58 path(s) cited, 57 tracked
  IGNORED coordination/active_sessions/COWORK-20260818-001.yaml -- `git add` on it is a no-op (R42.1)   <!-- cite-check:ignore -->
          cited by docs/maintenance/AIF120_CAPABILITY_MAPPING_V1.md
```

(The `<!-- cite-check:ignore -->` on that line is the R43.1 marker itself, appended
to the quotation so this document does not re-trigger the finding it describes. It is
the only alteration to the captured output.)

That hit is correct and permanent. `AIF120_CAPABILITY_MAPPING_V1.md` cites the
gitignored heartbeat file *on purpose*, in a note explaining that an earlier version
of the block staged it and that staging it did nothing. The document is doing exactly
what R42 asked documents to do. It will be flagged for as long as it exists.

`open-items` already carries the reasoning this violates: **a count that prints every
commit stops being read by the third day.** A gate whose output includes a line that
can never be actioned trains the reader to skip the block, and the next line -- the
real widow -- goes with it.

## 2. Ruling R43.1: a line may opt out, and the opt-out is greppable

```
the working copy at `tools/uidef/read_vfp_binary.py`  <!-- cite-check:ignore -->
```

Three properties, each chosen against a failure:

- **Per line, not per document.** A file-level marker would let one deliberate
  citation silence every accidental one in the same document. The suppression is
  scoped to the smallest unit that can carry a citation.
- **Greppable, not magic.** The marker is the literal string `cite-check:ignore`.
  `grep -rn cite-check:ignore docs/` enumerates every suppression in the tree in one
  command, so the set of exceptions is auditable without reading the tool.
- **Inert in the rendered document.** In prose it is an HTML comment and renders as
  nothing. Inside a fenced command block an HTML comment would be pasted verbatim
  into the maintainer's shell, so there it goes in the block's own comment syntax --
  the tool matches the substring, not a fixed wrapper.

Both implementations share the definition:

```python
SUPPRESS = 'cite-check:ignore'
...
for line in text.replace('\r\n', '\n').split('\n'):
    if SUPPRESS in line:
        continue
```

## 3. Ruling R43.2: suppress documentation, repair defects

Four citations in the lane resolved to untracked or ignored paths. Only three were
deliberate. The distinction is the whole ruling:

| Site | Citation | Disposition |
|---|---|---|
| `AIF120_CAPABILITY_MAPPING_V1.md:197` | the gitignored heartbeat yaml | suppressed -- the note is *about* it being ignored |
| `AIF120_SHIPPED_RULING_UNSHIPPED_CODE_V1.md:42` | `tools/uidef/read_vfp_binary.py` | suppressed -- R42's subject matter |  <!-- cite-check:ignore -->
| `AIF120_SHIPPED_RULING_UNSHIPPED_CODE_V1.md:119` | same, in "Still open" | suppressed -- same |
| `AIF120_LOCALE_AND_ENCODING_V1.md:169` | `git add tools/uidef/read_vfp_binary.py` | **repaired, not suppressed** |  <!-- cite-check:ignore -->

The fourth was not documentation. It was a live `git add` on a gitignored path inside
a shipped handoff block -- the last surviving instance of the exact defect R42.1
diagnosed. Suppressing it would have used the marker to hide the thing the check was
built to find. It was replaced with a note, in the form R42 already used one document
earlier:

```
# NOTE added 2026-08-19 by R42: this block staged tools/uidef/read_vfp_binary.py (cite-check:ignore),
# which is gitignored by design. `git add` on an ignored path is a SILENT no-op, so R33's
# reader fix never reached the repository and every gate still passed. The reader that
# ships is tools/vfp/read_vfp_binary.py, promoted by R42. The dead line is removed.
```

**The rule the marker is subject to:** a suppression is legitimate only where the
document's *subject* is the untracked path. Where the document *depends* on it -- a
command that stages it, an instruction to run it, a claim that it ships -- the
citation is a defect and the marker is a cover-up. A reviewer can tell the two apart
by reading the suppressed line, which is why the marker sits on that line.

## 4. Runtime-proven: the lane is clean

```
$ python3 tools/uidef/cite_check.py
cite_check: 43 document(s), 122 distinct path(s) cited, 122 tracked
  every cited path is tracked
exit=0
```

122 of 122. Zero widows, zero missing files, zero ignored citations. This is the
first moment in the run where every path any AIF-120 document points at is a path the
repository actually ships.

Evidence tier: **runtime-proven** for the lane sweep and for the per-line suppression
behaviour; **source-evidenced** for the gate wiring, which is proven by
`1757f141c` firing but has not yet run a commit that it passes cleanly.

## 5. What history still says

Range mode reads each document *as it read at that revision*, so the markers added
today do not retroactively clean up yesterday's commits. `HEAD~n..HEAD` still reports
R33's handoff as citing an ignored path, because on that day it did. That is
deliberate: the marker changes what the gate says about the next commit, not what the
record says about the last one.

## 6. Still open

- **The gate has not yet passed a commit.** Its only run so far is the one that
  failed advisory on itself. The commit carrying this ruling is the first real test.
- **Other lanes are still dirty and this check does not run for them.** Two widows
  were reported to the maintainer for relay:
  `AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md` cites an untracked
  `dottalkpp/data/workspaces/WORKSPACES.dbf` and a missing `EXERCISE_OUTLINE.md`;  <!-- cite-check:ignore -->
  `AIF_081_OUTPUT_CAPTURE_RUNTIME_PROOF_V1_20260731.md` cites a missing
  `scripts/index_maintenance_failure_proof.dts`. Portal gates are AIF-082's area.  <!-- cite-check:ignore -->
  This lane installed a check, not a policy for other people's documents.
- **`tools/uidef/read_vfp_binary.py` still exists locally and is inert.** A sandbox  <!-- cite-check:ignore -->
  cannot delete on this mount. The maintainer can remove it; nothing imports it.
- **The marker has no expiry.** A suppression added for a defect that later gets
  fixed will keep suppressing. `grep -rn cite-check:ignore docs/` is the audit; there
  is no automation that re-checks whether a suppression is still earned.

## 7. Good Neighbor note

- **What changed.** `tools/staging/check_cited_paths.py` and
  `tools/uidef/cite_check.py` gained a per-line `cite-check:ignore` opt-out and a
  restored `return` in `cited()`. Three AIF-120 rulings gained four markers, one of
  which replaced a dead `git add` line.
- **Whose area.** `tools/staging/` is AIF-082's (portal gates); the check there was
  authorized in-session by the maintainer, who is the gate owner. The three documents
  are AIF-120's own.
- **What authorization.** Maintainer (member.derald), in-session: "continue,
  authorized", following "who is the gate owner".
- **How to verify or undo.** Verify: `python3 tools/uidef/cite_check.py` from the
  repo root -- expect `122 tracked` and exit 0. Undo: the marker is inert text; delete
  the `SUPPRESS` block and the `if SUPPRESS in line: continue` in both tools and every
  suppressed citation is reported again. The four document markers can be removed with
  `grep -rn cite-check:ignore docs/` as the worklist. Reverting the
  `AIF120_LOCALE_AND_ENCODING_V1.md` note restores a `git add` that provably does
  nothing.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/staging/check_cited_paths.py
git add tools/uidef/cite_check.py
git add docs/maintenance/AIF120_CAPABILITY_MAPPING_V1.md
git add docs/maintenance/AIF120_LOCALE_AND_ENCODING_V1.md
git add docs/maintenance/AIF120_SHIPPED_RULING_UNSHIPPED_CODE_V1.md
git add docs/maintenance/AIF120_CITATION_GATE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R43 -- the citation check gets an opt-out so it stays readable; the last dead git add is repaired, not suppressed"
```
