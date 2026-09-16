---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260916-COWORK-209
  recorded_at_utc: 2026-09-16T12:35:00Z
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
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- asked for an
      interpretation of `modal`, then ruled "do it" on the reading below.
    scope: >
      Settles R77's third and last candidate by splitting it: the host pickers
      are capabilities, modality is a property, and dialog lifetime stays open.
  report:
    path: docs/maintenance/AIF120_MODAL_AND_HOST_DIALOG_V1.md
    kind: ruling
---

# AIF-120 -- R144: a system picker is a capability, modality is a property, lifetime is still open

Status: **review-needed.** The author does not self-approve.
Owner: `member.derald`. Author: `member.ai.claude.cowork`. Date: 2026-09-16.
Baseline `ad6d2a6df`. R-number from `tools/coordination/next_r.py`.

---

## 0. The one-paragraph version

R77 counted four `wxDialog` constructions and concluded UIDEF had **no word** for
a dialog. Measuring the CALL SITES instead of the constructions shows it was
never one question. Five of the seven `ShowModal` sites are stock system
pickers, which the contract already describes and which are not containers at
all. Two are authored forms that block. And the part R77 named first --
*different lifetime* -- is the part that survives all of this, unsolved.

**The interesting result is that the missing word was mostly not missing.**

---

## 1. The measurement

Every `ShowModal` in `src/gui/wx/*.cpp`, 2026-09-16 at `ad6d2a6df`:

| site | dialog | authored? |
| --- | --- | --- |
| `main_frame.cpp:775` | `wxFileDialog` -- open DBF | no, host |
| `main_frame.cpp:815` | `wxDirDialog` -- choose workspace dir | no, host |
| `main_frame.cpp:839` | `wxDialog` -- workspace open options | **yes** |
| `main_frame.cpp:877` | `wxFileDialog` -- load workspace schema | no, host |
| `main_frame.cpp:898` | `wxFileDialog` -- load schema | no, host |
| `main_frame.cpp:919` | `wxFileDialog` -- save schema | no, host |
| `main_frame.cpp:959` | `wxDialog` -- SCAN editor | **yes** |

**Seven, not four.** R77's number counted `new wxDialog`; the stack-allocated
`wxFileDialog`/`wxDirDialog` sites do not construct one. R77 was not wrong about
what it counted -- it counted a different thing, and the difference is the whole
finding.

**Every site has the identical shape:**

```cpp
if (dialog.ShowModal() != wxID_OK) { return; }
<use the result>
```

---

## 2. The ruling

### (a) A system picker is a CAPABILITY, not a container

Five of seven are file and directory pickers. **Nobody lays out a file picker.**
It has no children in the document, no FLOW, no ORDINAL, no PROPS worth carrying
-- it is a host service the frontend INVOKES.

The contract already describes exactly this: `DISPATCH = host` plus a capability
identifier in `HANDLERS`, R22's machinery. R22.4 already proved the refusal half
at scale -- Tk provided 7 of 18 capabilities, **refused and named 11**, and the
menu was still correct.

So `file.open`, `file.save`, `dir.choose` join `edit.find` and `program.run`.
**No new vocabulary. Five of R77's seven were never a KIND problem.**

### (b) Modality is a PROPERTY of a form

Two authored dialogs remain, and both are *collect input, then OK or Cancel*.

**`Modal` is a property on `form`**, governed by R143: a target that cannot
block **refuses and names** it per R22.4, rather than dropping it silently per
R3.

Two reasons it is not a KIND:

1. **The result contract is one bit.** At all seven sites the return is compared
   against `wxID_OK` and nothing else is read from it. That is not a control-flow
   axis; it is a boolean outcome, and R143's refusal mechanism already carries
   losses of that size.
2. **The contract does not describe behaviour, on purpose.** No method bodies
   (R14). No expression evaluation. No live menu mutation (R9) -- *"needs a live
   object model, which the stopping rule forbids."* A KIND whose definition is a
   return value into a handler would be the first behavioural kind, and that is a
   larger change than this measurement justifies.

### (c) NOT SETTLED: what a dialog's owner does with it

R77 named two things. The result contract turned out cheap. **Lifetime did
not.**

A dialog is created, shown, closed and destroyed as a unit, repeatedly within
one session. `destroy_container()` in `uidef_rt.h` carries verbs for a notebook
(R46, `DeletePage`) and a static box (R45, detach from the sizer), and a
fallthrough for everything else. R88 established what that costs: a splitter
reaching the fallthrough is **exit 139**, and three orderings were tried without
one working.

**This ruling does not solve that, and it makes it harder to notice.**

`prove_r88.py` fails when a kind enters `CONTAINER_KINDS` with no declared
removal. Ruling modality a PROPERTY means **no new kind enters**, so the guard
stays green while a modal `form`'s lifetime differs from a top-level frame's.
**A property that changes lifetime is a blind spot in that guard.**

Named here rather than discovered by a segfault. Whether the guard should also
track lifetime-affecting properties is a question for whoever rules next; this
ruling only refuses to hide it.

---

## 3. What this obliges

1. The five host pickers get capability identifiers, not kinds. No contract
   change beyond naming them alongside R22's existing set.
2. `Modal` joins `Scroll` as a property under R143's R3/R22.4 distinction --
   both need section 7's missing sentence, which R143 already obliges.
3. Nothing is added to `CONTAINER_KINDS`. The vocabulary stays at twenty.

---

## 4. What this does NOT do

- **Nothing is implemented.** No backend changed, no capability wired, no
  fixture authored, no render performed. R85's standard is *built AND run, all
  four backends, one document*; this has not met it.
- **It does not settle dialog lifetime**, section 2(c). That is the real
  remainder of R77 and it is where R88 already drew blood.
- **It does not extend `prove_r88.py`.** The blind spot is named, not closed.
- **The capability identifiers are illustrative.** `file.open`, `file.save`,
  `dir.choose` are the obvious spellings; the actual set belongs with whoever
  owns R22's namespace.

---

## 5. How to disprove this

- Show a site that reads more than `!= wxID_OK` from a modal's return. One would
  make 2(b)'s "one bit" false and reopen the KIND argument.
- Show a target where a non-blocking dialog changes what the document MEANS
  rather than how it behaves. That is R85's test, and passing it would make
  `dialog` a KIND.
- Show that a modal `form` can reach `destroy_container()`'s fallthrough safely.
  That would close 2(c) and make the guard's blind spot harmless.
