---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260916-COWORK-208
  recorded_at_utc: 2026-09-16T12:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260916-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: ad6d2a6df
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "R77-PROPERTY",
      ruling the second of the three candidates R77 left open.
    scope: >
      Rules scrolling a PROPERTY rather than a KIND, distinguishes R3's silent
      drop from R22.4's visible refusal, and gives section 7 the runtime
      provenance that section 4b already has.
  report:
    path: docs/maintenance/AIF120_SCROLL_PROPERTY_V1.md
    kind: ruling
---

# AIF-120 -- R143: scrolling is a property, and a target that cannot honour it must say so

Status: **review-needed.** The author does not self-approve.
Owner: `member.derald`. Author: `member.ai.claude.cowork`. Date: 2026-09-16.
Baseline `ad6d2a6df`. R-number allocated by `tools/coordination/next_r.py`.

---

## 0. The one-paragraph version

R77 measured the Workbench against the KIND vocabulary and left three
candidates. The owner ruled the second: **`Scroll` is a property.** That ruling
is correct and, taken alone, would have reintroduced exactly the defect R85
avoided -- because section 7 says an unhonoured property is **dropped
silently**, and the charter says a target must **say what it cannot do**. This
ruling is therefore three parts, not one, and part (b) is the load-bearing half.

---

## 1. The ruling

**R143. `Scroll` is a PROPERTY of a container, valued
`none | row | column | both`. A reader that KNOWS the property and cannot
honour it must refuse and name it per R22.4. It is adopted from a running frame
this house ships, under the same runtime provenance R66 gave section 4b.**

### (a) Property, not kind

R85 made the sash a KIND, and gave its reason: *"the vocabulary does not grow,
the refusal surface does."* A sash the target cannot draw changes what the
document MEANS -- two panes and a movable boundary become something else.

Scrolling is not that case. **A target that cannot scroll still shows the
content**; what it loses is reach, not meaning. That is a property's kind of
loss, and it is why R77 leaned this way -- *"a container property rather than a
kind, most likely"* -- before anyone ruled.

### (b) R3 governs UNKNOWN properties. R22.4 governs KNOWN ones.

Section 7 currently says, without qualification:

> an unknown property is dropped silently, never rejected (R3 -- import is an
> allow-list; a deny-list cannot be written against a vocabulary every third
> party extends)

That is right for a name the reader has never heard of. It is **wrong for a name
in this contract's own vocabulary**, and the contract does not currently say so.

The house has ruled this three times in three places:

| ruling | the case | the rule |
| --- | --- | --- |
| R7 | a control that binds to nothing | must not render as an ordinary empty box |
| R22.4 | a menu item whose capability is absent | must not render as an ordinary live item |
| R85 | a sash the target cannot draw | a KIND, so the target has to say so |

One principle: **a loss must be visible.** R143 extends it to the fourth case --
a known property the target cannot honour -- and it is R22.4's mechanism, not a
new one. R22.4 already proved it at scale: Tk refused **11 of 18** capabilities
and *"the menu is still correct"*.

**Section 7 needs one sentence.** Without it, (a) is the silent drop R85
rejected, and this ruling would have made the contract inconsistent with itself.

### (c) Provenance: section 7 gains what section 4b already has

Section 7's rule is that properties are **adopted, not invented**, from R15's
FoxPro `name = value` mini-language.

**Measured 2026-09-16 at `ad6d2a6df`**, a scroll property exists in none of:

```
gui/uidef/import_scx.py                     0 hits for "scroll"
the corpus scan, 3,010 object records       no scroll property reported
the four backends                           none
101 AIF120_*_V1.md rulings                  none
```

So by section 7 as written, `Scroll` is INVENTED and forbidden.

**R66 already answered this one section up.** Its five data-frame kinds were
taken from `ERSATZ GRID`, the browser this house ships, and section 4b names
what that made them: *"the first kinds in this vocabulary with a **runtime**
provenance rather than a corpus one."*

Section 4 has two legitimate sources. Section 7 has one, and only because nobody
has needed the second yet. `Scroll`'s source is `wxScrolledWindow` in
`src/gui/wx/main_frame.cpp` -- a frame this house wrote, measured by R77. That is
adoption from a running program, which is what R66 established.

### (d) Values, mapping onto words the contract already owns

```
Scroll = none | row | column | both
```

`row` and `column` are `FLOW`'s existing axis words -- *"children left to right"*
and *"children top to bottom"*. `Scroll = row` scrolls along the row axis.

Inventing `horizontal`/`vertical` would put two vocabularies for one axis in one
document. R85's test, applied: *"the mapping is total and it is a mapping onto
words the contract already had."*

---

## 2. What this obliges

1. **Section 7** gains the R3/R22.4 distinction and the runtime provenance
   sentence. Without both, this ruling is not implementable.
2. **Each backend** declares whether it honours `Scroll`, and refuses-and-names
   when it does not. The character-cell target is the interesting one.
3. **No KIND is added.** The vocabulary stays at twenty.

---

## 3. What this does NOT do

- **It does not implement anything.** No backend was changed, no fixture
  authored, no render performed. R85's proof standard is *built AND run, all
  four backends, one document*; this ruling has not met it and does not claim to.
- **It does not settle `modal` or `combo`**, R77's other two candidates. `modal`
  in particular is NOT this shape -- R77 notes a dialog has *"different lifetime,
  and a result contract"*, and lifetime is where R88 found the splitter fatal.
- **It does not touch `MinPane`**, still absent from the contract while the
  fixtures emit it. Same section, same adoption question, different ruling.
- **The value set is a proposal.** `none | row | column | both` is argued from
  FLOW's vocabulary, not measured from a corpus, and a reviewer who wants
  `.T.`/`.F.` plus an axis elsewhere has a defensible position.

---

## 4. How to disprove this

- Find a scroll property in the VFP corpus. If one exists, (c) is unnecessary
  and the name should be whatever the corpus says, not `Scroll`.
- Show a target where failing to scroll changes what the document MEANS rather
  than what it reaches. That would make (a) wrong and R85's KIND the right call.
- Show that R3's silent drop was always meant to cover known properties too. That
  would make (b) a change rather than a clarification, and it would need the
  owner rather than this ruling.
