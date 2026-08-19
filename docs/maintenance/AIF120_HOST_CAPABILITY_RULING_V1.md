---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-027
  recorded_at_utc: 2026-08-19T09:19:05Z
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
    baseline_commit: 710c02a8c
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just woke up an hour ago ---
      go go go!" -- taking the queue named at the end of the previous work, starting with
      the undecoded OBJCODE 78.
  report:
    path: docs/maintenance/AIF120_HOST_CAPABILITY_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R20: a menu item can reference a capability the HOST provides

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R18 decoded `OBJCODE = 77` and left `78` open with 21 records. It is now decoded,
and it changes the handler model.

## 1. `OBJCODE` fully decoded

| `OBJCODE` | n | `NAME` | `COMMAND` | what it is |
| --- | --- | --- | --- | --- |
| `67` | 37 | empty | **28 of 37** | a **user command** item; the action is a `COMMAND` expression |
| `77` | 9 | `_msm_*` | empty | a **submenu opener**; the submenu is the next container in document order (R18) |
| `78` | **21** | **21 of 21** | **empty** | a **host system-menu item**; the behaviour is the host's, referenced by name |

The `NAME` prefix families map one-to-one onto `OBJCODE`:

```text
_msm_  x7  -> 77      (system menu bar pads)
_med_  x13 -> 78      (Edit)
_mpr_  x5  -> 78      (Program)
_mtl_  x1  -> 78      (Tools)
_mwi_  x2  -> 78      (Window)
```

All 21 of the `78` items in `test_main.mnx`:

```text
_med_undo   \<Undo        CTRL+Z     _med_finda  Find A\<gain  CTRL+G
_med_redo   Re\<do        CTRL+R     _med_repl   R\<eplace...
_med_cut    Cu\<t         CTRL+X     _mpr_do     \<Do...
_med_copy   \<Copy        CTRL+C     _mpr_cancl  \<Cancel
_med_paste  \<Paste       CTRL+V     _mpr_resum  \<Resume
_med_clear  Cle\<ar                  _mpr_suspend \<Suspend
_med_slcta  Se\<lect All  CTRL+A     _mpr_compl  C\<ompile...
_med_find   \<Find...     CTRL+F     _mtl_browser Class \<Browser
_med_sp100  \-                       _mwi_arran  \<Arrange All
_med_sp200  \-                       _mwi_rotat  C\<ycle       CTRL+F1
_med_sp300  \-
```

**Even the separators are named host resources** -- `_med_sp100`, `sp200`, `sp300`.

## 2. R20 -- the ruling

**R20. A menu item may reference a capability the HOST provides rather than
carrying its own behaviour. `DISPATCH` therefore has a third value, `host`, whose
handler name is a well-known capability identifier, and a target that does not
provide the named capability must refuse the item and name it.**

R11 gave `DISPATCH` two values, `ui` and `worker`, both of which name a handler
the *document's* target implements. `host` is different in kind: the document is
not supplying behaviour at all, it is **selecting** behaviour the platform already
has. `_med_cut` is not a handler anyone writes; it is "whatever Cut means here",
and its accelerator (`CTRL+X`) comes with it.

Three things follow.

**R20.1 -- this is 31% of a real menu.** 21 of the 67 items in `test_main.mnx` are
host-provided. An importer that treats them as ordinary items produces a menu
whose entire Edit family does nothing, silently. That is the R7 failure -- an
empty box that looks correct -- at menu scale.

**R20.2 -- the capability vocabulary must be the DSL's, not VFP's.** `_med_cut` is
a VFP spelling. A portable table names the capability (`edit.cut`, `edit.paste`,
`window.arrange`) and the importer maps VFP's names onto it. Carrying `_med_cut`
verbatim would make every target implement VFP's naming, which is precisely the
leak the charter's stopping rule forbids.

**R20.3 -- `host` is the most portable dispatch there is.** Every platform in the
charter's table has Cut, Copy, Paste, Select All and a window list. A `host`
handler needs no thread rule, no completion path, and no registry entry -- it is
the one category where the target has *more* information than the document.

## 3. Where this sits against R14

R14 ruled method bodies never enter v1 because 86% of real procedures navigate the
object model. R20 is the complement, and a happier one: **for host capabilities
there is no body to exclude.** The document names an intent and the platform
supplies the implementation, which is the whole architecture the charter wanted and
here it arrives for free.

Combined, the handler model is:

| `DISPATCH` | who implements it | needs a thread rule |
| --- | --- | --- |
| `ui` | the target's registry, on the UI thread | yes |
| `worker` | the target's registry, off it, with a completion path | yes |
| **`host`** | **the platform itself, by capability name** | **no** |

## 4. What R20 does not settle

- **The capability vocabulary is not written.** R20.2 says it must be the DSL's
  own; it does not enumerate it. `edit.cut` is an illustration, not a decision.
- **Two menus, one author.** `test_main.mnx` supplies all 21 records; `test_go.mnx`
  has zero `OBJCODE = 78`. The corpus has nine more `.MNX` unexamined for this.
- **`SYSRES` does not encode it.** Measured `0` on all three `OBJCODE` groups in
  `test_main` and blank throughout `test_go`, so it distinguishes nothing here
  despite the name suggesting it should.
- **Not implemented.** `import_mnx.py` still imports `OBJCODE = 78` items as
  ordinary items with no handler, which per R20.1 is the silent-failure case. The
  fix is a mapping table and it is not written.
- **No accelerator conflict rule.** A `host` capability brings its own accelerator;
  what happens when the document also states one is undecided.

## 5. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_HOST_CAPABILITY_RULING_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R20 -- OBJCODE 78 decoded as host system-menu items; DISPATCH gains a third value, host"
```
