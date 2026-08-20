---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-098
  recorded_at_utc: 2026-08-21T03:50:00Z
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
    baseline_commit: fdacdbfe9
  authorization:
    requested_by: steward (member.derald), in-session -- "the scx is a dbf
      structure, if so and we read it that is really really good dogfooding, but
      we probably would fail the suffixes on load", then "check open and create
      and close cmd_use.cpp".
    scope: >
      Read-only measurement of the extension handling in USE, CREATE and CLOSE.
      No engine source changed. Writes docs/ only.
  report:
    path: docs/maintenance/AIF120_EXTENSION_NAMESPACE_REPORT_V1.md
    kind: report
---

# Report: x64base can already open a `.scx`, but only if you spell it right

**This is a report, not a ruling.** The finding is in `src/cli/` and
`src/common/`, which AIF-120 does not own. Nothing was changed.

## 0. The short answer to the question asked

> "the scx is a dbf structure, if so and we read it that is really really good
> dogfooding, but we probably would fail the suffixes on load"

Half right, and the half that is wrong is the good news. **`DbArea::open()` never
looks at the extension at all** -- it opens the filename it is handed
(`src/xbase/dbf_file.cpp:102`). There is no suffix whitelist and nothing to fail.

What fails is NAMING. `USE` has two branches that resolve a name by two different
rules, and only one of them survives a non-`.dbf` extension:

| you type | branch | resolves to | opens |
|---|---|---|---|
| `USE form1.scx` | logical | `<DBF>/form1.scx.dbf` | **no** -- a filename nobody typed |
| `USE .\form1.scx` | explicit | `<DBF>/form1.scx` | **yes** |
| `USE forms\form1.scx` | explicit | `.../forms/form1.scx` | **yes** |
| `USE students` | logical | `<DBF>/students.dbf` | yes |
| `USE students.dbf` | logical | `<DBF>/students.dbf` | yes |

So the dogfooding already works. It is one leading `.\` away from being usable,
and that is not a discoverable thing to know.

## 1. Where the two rules diverge

`cmd_use.cpp:672-679`:

    if (looks_explicit_path(name)) {
        dbf_path = dottalk::paths::resolve_dbf(name);          // ensure_ext
    } else {
        std::string base = strip_dbf_ext_if_present(name);     // strips .dbf ONLY
        dbf_path = get_slot(Slot::DBF) / (base + ".dbf");      // appends ALWAYS
    }

`looks_explicit_path` (:145) is true for a token containing `/`, `\`, a drive
letter, or a leading `.`.

The two rules:

- **explicit** -> `resolve_dbf()` -> `ensure_ext(p, ".dbf")`
  (`path_resolver.cpp:138`), which replaces the extension **only if there is
  none**. `form1.scx` already has one, so it is left alone. Correct.
- **logical** -> strips `.dbf` if present, then appends `.dbf`
  unconditionally. `form1.scx` is not `.dbf`, so nothing is stripped and `.dbf`
  is appended anyway: `form1.scx.dbf`.

One function, one job, two rules. The explicit branch's rule is the right one and
it is already written, three files away.

## 2. The house has already ruled on this once

`path_resolver.cpp:153`:

    fs::path resolve_index(const std::string& token)
    {
        ...
        // Public index container/file root:
        //   .inx, .cnx, .cdx
        // Do not force an extension here.
        return p;
    }

Indexes got the ruling because their family visibly has three members.
`resolve_dbf` never did, because `.dbf` looked like a family of one.

**It is not.** AIF-120 R10 measured that `.scx/.sct`, `.vcx/.vct`, `.mnx/.mnt`
and `.frx/.frt` are DBF tables, and `tools/staging/prepush_gate.py:97` carries
the owner ruling of 2026-08-19 saying so in as many words: *"the FoxPro designer
extensions ... are VALID x64base extensions ... Being DBF-shaped is a fact about
the container, not about the role."*

So one gate knows the family has ten members, `resolve_index` knows its family
has three, and `resolve_dbf` still behaves as though its family has one.

## 3. CREATE and CLOSE, since both were asked about

- **CREATE** has the same shape and no explicit-path escape hatch.
  `cmd_create.cpp:618` calls `resolve_dbf_slot_path(dbNameWithExt(table))`, and
  `dbNameWithExt` (`dbf_file.cpp:94`) is unconditional:

        if (!ends_with_ci_local(s, ".dbf")) s += ".dbf";

  `CREATE TABLE form1.scx` produces `form1.scx.dbf`. Same rule as USE's logical
  branch, in a second place. `cmd_sort.cpp:777`, `cmd_copy.cpp:127` and
  `cmd_autodbf.cpp:1074` use it too, so an output table can never be written
  under a designer extension.

- **CLOSE** is clean. `a.close()` (`cmd_use.cpp:306`) and
  `xindex::ensure_manager(a).close()` (:557, :584) operate on the AREA, not on a
  name. Nothing to get wrong and nothing got wrong.

## 4. What a fix would look like -- for the engine lane, not for me

The smallest change that makes the two branches agree is to give the logical
branch the rule the explicit branch already uses: **append `.dbf` only when the
token has no extension at all.**

    // today
    std::string base = strip_dbf_ext_if_present(name);
    dbf_path = get_slot(Slot::DBF) / (base + ".dbf");

    // agreeing with resolve_dbf
    dbf_path = paths::ensure_ext(get_slot(Slot::DBF) / name, ".dbf");

**This is a behaviour change and therefore an owner call, not a cleanup.** Today
`USE students.dbg` silently becomes `students.dbg.dbf`; afterwards it fails as
not found. That is better, and it is different, and somebody's script may be
relying on the old shape.

`dbNameWithExt` is the same decision in the CREATE path and should be ruled on
with it rather than separately -- two sites, one rule, which is the pattern this
project keeps paying for when they are fixed one at a time.

## 5. Why AIF-120 cares

The design table this lane produces IS a DBF. Today it must be written `.DBF`,
which says nothing about what it is. If `resolve_dbf` learned the family, a UIDEF
document could carry an extension that names its role -- and x64base could `USE`
a VFP form file with its own engine, which is the dogfooding the steward is
pointing at.

There is also a nearer consequence, found the same day and in the same shape: a
markdown-JSX website draft named `.mdx` was refused by `prepush_gate.py` as a
runtime data fixture, because in xBase `.mdx` is a MULTIPLE INDEX file. Three
places in this repository now carry an extension list -- the gate, `resolve_dbf`,
`resolve_index` -- and no two of them agree on what the x64base extension
namespace contains.

**That namespace is not written down anywhere.** Every list is local, derived
from what its author needed that day. Naming it once, somewhere both the gates
and the resolvers can read, is the durable version of this report.
