# AIF-128 -- the guard that names the registry tested the union, and blamed the catalogs

    Run    : COWORK-20260825-001 (member.ai.claude.cowork), for member.derald
    Claim  : coordination/aif/AIF-128.claim
    Found  : 2026-08-25, while making the adjacent authority labels agree
             (3d85320d3, 0edaa1ef9) -- the guard was four lines below the line
             being edited.
    Tier   : SOURCE-EVIDENCED at file:line, and PROVEN by fault injection.
    Status : **FIXED 2026-08-25, review-needed.** See section 6.

---

## 1. The finding

`tools/fullstack_docs/refcheck_v1.py` guarded its own precondition like this:

    commands = registry | shortcut_aliases | routed_aliases
    if not commands:
        print("refcheck: could not resolve the command registry", ...)
        return 2

The message names the registry. The test does not. It tests the UNION of the
registry with two alias sources, so it answers "fine" whenever ANY of the three
resolves -- including in the one case it exists to catch, where the registry is
the thing that failed.

Same answer for "registry absent" as for "registry fine". That is the AIF-118
shape, sitting inside the guard whose entire job is to catch a missing
authority.

## 2. Why it is worse than silence

A guard that fails open usually goes quiet. This one does not. It hands the
work to the rest of the program, which then produces a confident, precise and
completely misdirected accusation.

PROVEN 2026-08-25 by injecting an empty `registry_map` with both alias sources
left intact:

    BEFORE the fix
      (the "could not resolve the command registry" message never printed)
      GUARDED phantoms (dotref+foxref): 270
      FAIL: a native/legacy reference entry names no command, function,
            or sub-form.
      EXIT: 1

    AFTER the fix
      refcheck: could not resolve the command registry -- alias sources
      contributed 107 name(s), which is not a registry; refusing to judge
      the *ref catalogs against it
      EXIT: 2
      (stdout: 0 lines)

Before, refcheck charged 270 hand-authored `dotref`/`foxref` entries with
naming commands that do not exist. Every one of those entries was correct. The
next reader is sent to edit six reference catalogs, and the registry -- the
actual casualty -- is never mentioned.

**Exit 1 says "your catalogs are wrong". Exit 2 says "I could not measure".
The guard was turning the second into the first.**

## 3. The discriminator -- when this shape is NOT a defect

A union-then-guard is not wrong by itself, and the sweep that found this one
also found two instances that are correct. The difference is whether the union
IS the authority:

  - `tools/coordination/next_aif.py:66` -- `taken = intake_nums | claim_nums`,
    then `if not taken`. CORRECT. The module's own docstring rules that "the
    authority is the UNION", because a number taken in EITHER place is taken.
    Each source additionally reports its own absence by name before the union
    is formed.
  - `tools/coordination/next_r.py:122` -- `taken = reg | cite`, same reasoning,
    and it prints `declared: N  cited in tree: M` so a zero on either side is
    visible in the report.

In `refcheck` the union is NOT the authority. The registry is the authority;
the alias sources are supplementary spellings OF registry entries. A name
scraped from an alias table is not a registry, however many of them there are.

**The rule this yields:** guard the authority you are about to name in the
error message, not the working set you happened to build from it.

## 4. Where it came from

Not carelessness. The union was assembled for the RESOLUTION step -- an entry
resolves if it is a command, an alias, a sub-form or a function -- and the
guard was then written against the variable that was in hand. The precondition
question ("can I measure at all?") and the resolution question ("does this name
exist?") take different inputs, and one variable was serving both.

## 5. Relation to the two commits that surfaced it

This was found while fixing labels, not while looking for defects, and the
adjacency is the point. `3d85320d3` and `0edaa1ef9` split the same union into
named parts (`commands_reg` / `commands_alias`, `fn_seed` / `fn_ext` /
`fn_core`) so the summary line could say what was in each number. Once the
parts had names, the guard testing the wrong one was visible on sight.

Naming the parts of a count made a control-flow defect legible. That is worth
recording as an argument for the count discipline beyond honest reporting.

## 6. The fix

Test `commands_reg`. Report the aliases rather than counting them toward the
verdict:

    if not commands_reg:
        print("refcheck: could not resolve the command registry -- "
              f"alias sources contributed {len(commands_alias)} name(s), "
              "which is not a registry; refusing to judge the *ref catalogs "
              "against it", file=sys.stderr)
        return 2

The union check is subsumed: if `commands_reg` is non-empty then `commands` is
non-empty, so no case is lost.

## 7. Verification

  A. HEALTHY TREE -- pre-fix and post-fix run against the same tree:
     stdout byte-identical, stderr byte-identical, exit 0 both.
     No finding, count or verdict moves on a working tree.
  B. FAULT INJECTION -- empty registry, aliases intact: exit 2, the registry
     named in stderr, stdout empty. Recorded in full in section 2.
  C. `py_compile` clean; ASCII clean.

Backup of the pre-fix file: `tmp/refcheck_v1.py.bak4`.

## 8. Not done

The function half has no equivalent precondition guard at all -- `funcs` is a
union of `fn_seed | fn_ext | fn_core` with nothing testing it. This is
currently ACCEPTABLE rather than fixed: `function_state()` already
three-states SYSFUNC (absent / empty / populated), emits a finding for the
first two, and the label now prints `SYSFUNC ABSENT` instead of a number. So
the absence IS reported by name. It is recorded here because "reported
somewhere" is a weaker property than "guarded", and if the FN reporting is
ever simplified this becomes the same defect.

