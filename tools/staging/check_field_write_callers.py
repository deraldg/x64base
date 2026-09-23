#!/usr/bin/env python3
"""
WHO WRITES A FIELD, AND DOES IT GO THROUGH THE FUNNEL (AIF-156).

THE CLAIM THIS EXISTS TO MAKE, WHICH NO REGRESSION MARKER CAN.
PKPOLICY proves three write paths REFUSE a write to a declared PRIMARY key.
It cannot prove those are the ONLY paths, because a runtime marker cannot
enumerate a call site -- it can only exercise the ones somebody thought to
exercise. Arms prove routes; a gate proves there are no other routes. That
second claim is static, so it needs a static check.

WHAT IT LOOKS FOR: direct calls to the engine's field-write primitives from
outside the engine --

    DbArea::replaceFieldStored   the value write
    DbArea::replaceFieldNull     the null write
    DbArea::set                  the buffer write (record-level commit follows)

anywhere under src/ except src/xbase (which OWNS them) and src/tests.

EXEMPT BY ROUTE, NOT BY FLAG, and the exemption list is three files long:

    src/cli/xbase_cli_write.cpp    IS the funnel
    src/cli/append_support.cpp     the key GENERATOR -- it must write a
                                   primary key, and it is exempted by being
                                   below the funnel rather than by passing a
                                   bypass parameter, because a parameter can
                                   be passed by anyone and a route cannot
    src/cli/cmd_validate_unique.cpp  VALIDATE UNIQUE ... REPAIR, the
                                   inherited-data renumber tool the charter's
                                   step 3 deliberately preserves

ADVISORY, WITH A BASELINE, ON PURPOSE. The backlog is real and large; a gate
that blocks every commit on day one gets disabled, and a disabled gate measures
nothing. The baseline turns a claim into a list that can only shrink.

    NEW    a call site not in the baseline. Somebody added a direct write.
    FIXED  in the baseline and gone. Drop the line; a baseline that only ever
           grows stops being a measurement.

COMMENTS AND STRING LITERALS ARE STRIPPED BEFORE MATCHING, and that is not
tidiness -- this tree's registry summaries discuss replaceFieldStored at length
in prose, and cmd_regression.cpp alone would contribute a dozen phantom hits.
A gate that counts its own documentation is worse than no gate.

THE RECEIVER IS CHECKED, NOT JUST THE ARGUMENT (2026-09-09). Every cut of the
`set(` test above discriminates by the shape of the FIRST ARGUMENT and none of
them ever looked at WHAT THE METHOD IS CALLED ON. So every object in this tree
with a `set(x)` method counted as a DbArea write, and six of the twenty-two
baseline entries were not field writes at all:

    src/tv/cmd_recordview.cpp x5    view_->set(lines) -- view_ is a LinesView*,
                                    a TScroller subclass; the file performs NO
                                    DbArea write of any kind, it is a VIEWER
    src/tv/foxtalk_command_window.cpp x1  msgLine_->set(s) -- a TMsgLine widget;
                                    the string DbArea occurs ZERO times there

The header above worries at length about UNDER-reporting and calls it "the one
failure a gate must not have". It is, and this is the other one. An
over-reporting gate inflates a number that is published on x64base.com and pads
the backlog with work that does not exist, so the list stops being a list of
things to do.

THE FIX MUST NOT INTRODUCE THE FAILURE IT CURES, so receivers land in THREE
buckets and only one of them is dropped:

    receiver is a DbArea in this file      COUNTED
    receiver is some other declared name   EXCLUDED, and the count is PRINTED
    receiver is not a plain identifier     COUNTED ANYWAY and listed as
      (arr[i].set(...), f().set(...))      UNCLASSIFIED

Unknown means counted. A gate may refuse to guess; it may never guess quiet.
"""

import os
import re
import sys

ROOT = os.getcwd()
SRC = os.path.join(ROOT, "src")
BASELINE = os.path.join("tools", "staging", "field_write_callers_baseline.txt")

SKIP_DIRS = {
    os.path.join("src", "xbase"),   # owns the primitives
    os.path.join("src", "tests"),   # asserts on them directly, by design
}

EXEMPT_FILES = {
    os.path.join("src", "cli", "xbase_cli_write.cpp"),      # is the funnel
    os.path.join("src", "cli", "append_support.cpp"),       # the generator
    os.path.join("src", "cli", "cmd_validate_unique.cpp"),  # REPAIR

    # GATED MULTI-FIELD WRITERS (AIF-156, 2026-09-07). Each of these calls
    # xbase::cli::gateFieldWrites() for EVERY field BEFORE writing ANY of them,
    # then does its own write. They are exempt because routing them through
    # replaceFieldStored() per field would be a REGRESSION, not a fix: it would
    # turn one record lock into N, one physical write into N, and one index
    # snapshot pair into N -- and it would destroy atomicity, since a refusal on
    # the third field would leave the first two already on disk.
    #
    # THE COST OF EXEMPTING A WHOLE FILE IS REAL AND IS ACCEPTED KNOWINGLY: a
    # future ungated write added to one of these files will not be seen here.
    # The reason it is still the right trade is that the alternative -- keeping
    # them in the baseline -- makes the baseline a list of things that are FINE,
    # which is how a measurement stops meaning anything.
    os.path.join("src", "cli", "cmd_replace_multi.cpp"),    # gates in multirep_validate_and_normalize
    os.path.join("src", "cli", "cmd_sql_insert.cpp"),       # legacy INSERT verb; gates before APPEND
    os.path.join("src", "cli", "cmd_sql_update.cpp"),       # legacy UPDATE verb; gates before the scan

    # src/dewey/hierarchy_service.cpp (2026-09-09). Joined the pattern above
    # rather than being routed, because it writes ROWS: create_root, add_child
    # and insert_between each set up to seven fields under one appendBlank()
    # and one writeCurrent(). It now asks gateFieldWrites() for every field of
    # a row before writing any, through a local gate_row()/write_row() pair.
    #
    # IT WAS ALSO THE ONLY FILE IN THE BASELINE WHOSE CALLERS DISCARDED EVERY
    # RETURN -- all seventeen. That was survivable while the writes could not
    # fail for a policy reason; it would not have been once they could, because
    # a dropped refusal leaves a hierarchy node with no path_key and says
    # nothing. Both helpers are [[nodiscard]] now, which is what made the
    # compiler name every site.
    os.path.join("src", "dewey", "hierarchy_service.cpp"),

    # src/cli/browse/browse_edit.cpp (AIF-156, 2026-09-23). THE SHARED EDITOR
    # COMMIT DOOR, exempted BY ROUTE like the gated multi-field writers above:
    # commit_staged() asks gateFieldWrites() about EVERY staged field before
    # writing ANY of them, then keeps its own set()+writeCurrent() apply --
    # per-field routing through replaceFieldStored() would turn one physical
    # write into N and destroy the all-or-nothing edit. Owner ruling
    # 2026-09-23: interactive editors share ONE commit function; the two
    # simple field-test editors (this helper's own caller surface plus
    # app_simple_browser, now routed through it) are the historical examples,
    # and future browsers/editors that enable editing call this door and
    # inherit the funnel without writing their own.
    os.path.join("src", "cli", "browse", "browse_edit.cpp"),

    # src/cli/table_state.cpp (2026-09-09). EXEMPT FOR A DIFFERENT REASON THAN
    # EVERY FILE ABOVE, and the difference is the point. The others are exempt
    # because gating them per field would be slower and would break atomicity.
    # This one is exempt because GATING IT AT ALL WOULD BE WRONG.
    #
    # recover_table_buffer_journal() REPLAYS A WRITE-AHEAD LOG. Every value it
    # writes was already accepted by the gate at COMMIT time and is already
    # durable in the journal; replay only puts back what a crash interrupted.
    # Asking the gate again would let a constraint added AFTER the log was
    # written refuse a write that is already committed -- and since replay ends
    # by removing the log, a refusal there loses the record permanently while
    # reporting nothing. A recovery that can disagree with the commit it is
    # recovering is not a recovery.
    #
    # THE GATE BELONGS AT THE MOMENT OF THE ORIGINAL WRITE, NOT AT REPLAY.
    os.path.join("src", "cli", "table_state.cpp"),

    # src/cli/group_log.cpp (AIF-160, 2026-09-11). The table_state.cpp reason
    # one layer further along: gating this AT ALL would be wrong, and here it
    # would also be DANGEROUS rather than merely slow.
    #
    # This file writes ONE ROW, and that row IS the instant a multi-table group
    # becomes true. Four things the funnel does are each wrong for it:
    #
    #   ATOMICITY. replaceFieldStored gates and writes PER FIELD. A refusal on
    #   the third of five leaves the first two on disk -- a HALF-WRITTEN
    #   DECISION ROW, which is the worst state this design has, because a
    #   partial row can be read as a committed group by a recovery that finds
    #   the key. The gated multi-field writers above are exempt to avoid exactly
    #   this shape; here the consequence is not an untidy record, it is a
    #   transaction that half-happened.
    #
    #   TRIGGERS. The funnel fires BEFORE/AFTER triggers (AIF-087). A trigger
    #   firing at the decision point could start a transaction, which could
    #   start a group, which would write HERE. This is the one write in the
    #   system that must be a single durable append with no reentrancy.
    #
    #   LOCKS. The funnel takes a record lock per field -- five lock FILES on
    #   engine state under the SYS slot, which is refused the table buffer for
    #   the neighbouring reason, in a lane whose locking ruling was specifically
    #   to stop creating n lock files.
    #
    #   POLICY. The funnel enforces primary-key policy over USER data.
    #   GROUPS.dbf declares no key and holds no user data. It is the engine's
    #   own ledger, written directly, the same way WORKSPACES.dbf is.
    #
    # THE WHOLE-FILE COST IS ACCEPTED KNOWINGLY, as it is for every entry above:
    # a future ungated write added to group_log.cpp will not be seen here. The
    # file is a hundred lines with one writer in it, which is the smallest that
    # cost gets.
    os.path.join("src", "cli", "group_log.cpp"),

    # ENGINE-OWNED SYSTEM STORES (AIF-156, 2026-09-23). A THIRD exemption
    # shape, distinct from by-route (gates then keeps its own write) and from
    # gating-would-be-wrong (WAL replay, the group ledger). These files are
    # CREATION-ONLY BY CONSTRUCTION: the engine is the sole author of every
    # row, every key is engine-assigned at append (next_id()-style max+1 under
    # the table lock, or serialized store state), and no path in any of them
    # aims a write at an existing key. Owner ruling 2026-09-23: a primary key
    # is assigned at record creation and never edited -- these stores are the
    # trivial case of that model, where "never edited" holds because no editing
    # door exists at all, not because a gate refuses one. Their SYS* tables are
    # engine-defined schema (create_dbf X64) that never carries a user-declared
    # SET UNIQUE FIELD ... PRIMARY designation, so the gate would consult a
    # flag that is never set.
    #
    # Verified at the CALL SITES, not the declarations, 2026-09-23:
    #
    #   src/bbs/bbs_store.cpp -- RowW::set ("Row writer over a freshly
    #   appended record") writes only rows whose ID came from next_id() under
    #   a TableLock; the two existing-row writes touch STATE (close_thread)
    #   and LASTPOST (reply_to), bookkeeping fields, never ID.
    #
    #   src/help/message_catalog.cpp -- set_field_or_throw serves the two
    #   seed-row creators (write_message_seed_row, write_text_seed_row) into
    #   SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT and throws on failure.
    #
    #   src/identity/identity_dbf_store.cpp -- RowW::set is the full-store
    #   writeback appending rows with engine-assigned IDs.
    #
    # THE WHOLE-FILE COST IS ACCEPTED KNOWINGLY, as everywhere above: a future
    # ungated write added to one of these files will not be seen here. The
    # mitigations are the same ones the pattern already relies on -- each file
    # funnels its writes through ONE local writer (RowW::set,
    # set_field_or_throw), so a new direct write would be a break of the
    # file's own idiom, not just of this gate's.
    os.path.join("src", "bbs", "bbs_store.cpp"),
    os.path.join("src", "help", "message_catalog.cpp"),
    os.path.join("src", "identity", "identity_dbf_store.cpp"),
}

# `set(` IS DISCRIMINATED BY THE SHAPE OF ITS FIRST ARGUMENT, and this took
# three cuts. DbArea::set takes a 1-BASED FIELD INDEX; the name-keyed
# row-writer wrappers in identity_dbf_store and bbs_store take a STRING
# ("ID", "UKEY"). So "the first argument is not a quote" is the whole test.
#
# The first cut demanded a bare identifier or a number and MISSED
# `a.set(i + 1, v)` -- a real DbArea write, in two files, because the argument
# is an EXPRESSION. The second widened to allow member access and still missed
# it. Requiring a SHAPE the argument might not take is how a gate
# under-reports while looking clean, which is the one failure a gate must not
# have.
PATTERNS = [
    ("replaceFieldStored", re.compile(r"(?:\.|->)\s*replaceFieldStored\s*\(")),
    ("replaceFieldNull",   re.compile(r"(?:\.|->)\s*replaceFieldNull\s*\(")),
    ("set",                re.compile(r"(?:\.|->)\s*set\s*\(\s*(?![\"'])")),
]


# A DbArea-typed name, as declared or received in this file. Deliberately
# generous -- it matches declarations, parameters, references and pointers,
# with or without namespace or const -- because a name this MISSES becomes an
# exclusion, and an exclusion is the direction that loses a real write.
DBAREA_DECL = re.compile(
    r"(?:^|[^\w:])(?:(?:::)?xbase::)?DbArea\s*(?:const\s+)?[&*\s]*([A-Za-z_]\w*)"
)

# The receiver of a `x.set(` / `x->set(` call, when it is a plain identifier.
RECEIVER = re.compile(r"([A-Za-z_]\w*)\s*(?:\.|->)\s*set\s*\(")


def dbarea_names(code_no_strings):
    """Identifiers this file declares or receives as a DbArea."""
    return set(DBAREA_DECL.findall(code_no_strings))


def strip_comments_and_strings(text, keep_strings=False):
    """Blank out // and /* */ comments and "..." literals, preserving newlines
    so reported line numbers stay true."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            out.append("  ")
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append("  ")
                i += 2
        elif c == "'":
            # CHAR LITERALS MUST BE STRIPPED BEFORE DOUBLE QUOTES, and this
            # cost a real miss: cmd_calcwrite.cpp:156 holds '"', so a stripper
            # that does not know char literals opens a string there and blanks
            # everything to the next quote -- including the direct
            # replaceFieldStored call at line 917. THE GATE UNDER-REPORTED AND
            # LOOKED CLEAN, which is the failure mode a gate must not have.
            out.append(" ")
            i += 1
            while i < n and text[i] != "'":
                if text[i] == "\\" and i + 1 < n:
                    out.append("  ")
                    i += 2
                    continue
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
        elif c == '"':
            if keep_strings:
                # KEEP THE QUOTES, BLANK THE INTERIOR. Keeping the interior was
                # the FIFTH cut's bug and it was found by this checker firing on
                # the very commit that added it: the registry summary sentence
                # explaining the w.set("ID", ...) false positive became one,
                # because `set(` inside summary PROSE stayed visible and the
                # escaped \" that followed it is a backslash, not a quote, so
                # the "first argument is not a quote" test passed.
                #
                # Blanking the interior while preserving the delimiters gives
                # both halves at once: real code reads w.set("  ", ...) and is
                # correctly excluded, while prose inside a literal disappears
                # entirely. Newlines are preserved so line numbers stay true.
                out.append(c)
                i += 1
                while i < n and text[i] != '"':
                    if text[i] == "\\" and i + 1 < n:
                        out.append("  "); i += 2
                        continue
                    out.append("\n" if text[i] == "\n" else " ")
                    i += 1
                if i < n:
                    out.append(text[i]); i += 1
                continue
            out.append(" ")
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    out.append("  ")
                    i += 2
                    continue
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)



# ---------------------------------------------------------------------------
# A CONTENT KEY, BECAUSE file:line IS A SECOND DECLARATION OF WHERE THE CODE IS
#
# The baseline recorded NINE anchor drifts before this change and a tenth
# arrived on 2026-09-18 (cmd_workspace.cpp 3057 -> 3074, a WsLock struct
# inserted above an untouched call). Its own summary: EVERY ONE OF THEM WAS A
# FALSE POSITIVE. Not one NEW line in this gate's history has been a genuine
# unrouted writer. A signal whose every firing is noise trains its reader to
# skim, and the real one then arrives in a channel nobody reads -- which is a
# worse failure than the manual re-anchoring it also cost.
#
# The remedy the baseline named nine times, now implemented: key each site by
# FILE + ENCLOSING FUNCTION + THE NORMALIZED CALL TEXT. An insertion above the
# site changes none of the three. A genuinely new writer changes at least one.
#
# THE LINE NUMBER IS STILL PRINTED, just not keyed on -- a reader needs it to
# navigate, and the failure was never that the number was shown. It was that
# the number was COMPARED.
DEF_RE = re.compile(r"^[A-Za-z_][\w:<>,&*\s]*?([A-Za-z_]\w*)\s*\([^;]*$")
CTRL = {"if", "for", "while", "switch", "catch", "return", "else", "do"}


def enclosing_function(lines, index):
    """Nearest preceding definition-shaped line, by name. Heuristic on purpose.

    It does not need to be a parser. It needs to be STABLE under insertions
    above the site, and to differ when the site genuinely moves to another
    function. A wrong-but-consistent answer still keys correctly; only a
    FLAPPING answer would reintroduce the drift, and a definition line does
    not move relative to the body it opens.
    """
    for i in range(index, -1, -1):
        line = lines[i]
        if not line or line[0].isspace():
            continue
        m = DEF_RE.match(line)
        if m and m.group(1) not in CTRL:
            return m.group(1)
    return "<file-scope>"


def call_text(line):
    return re.sub(r"\s+", " ", line.strip())


def site_key(rel_slash, func, text, label):
    return "%s :: %s :: %s :: %s" % (rel_slash, func, text, label)


def is_legacy_baseline(entries):
    # Legacy lines look like path:1234:set and carry no " :: " separator.
    return bool(entries) and not any(" :: " in e for e in entries)


def scan():
    where = {}
    hits = []
    excluded = []
    unclassified = []
    for dirpath, _dirnames, filenames in os.walk(SRC):
        rel_dir = os.path.relpath(dirpath, ROOT)
        if any(rel_dir == s or rel_dir.startswith(s + os.sep) for s in SKIP_DIRS):
            continue
        for fn in filenames:
            if not fn.endswith((".cpp", ".cc", ".cxx")):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            if rel.replace("\\", "/") in {p.replace("\\", "/") for p in EXEMPT_FILES}:
                continue
            try:
                with open(os.path.join(dirpath, fn), "r", encoding="utf-8",
                          errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            # TWO PASSES, BECAUSE THE PATTERNS WANT OPPOSITE THINGS.
            #
            # The NAME patterns need string literals GONE: this tree's registry
            # summaries are string literals that discuss replaceFieldStored at
            # length, and cmd_regression.cpp alone would contribute a dozen
            # phantom hits.
            #
            # The `set(` pattern needs them KEPT, because the whole test is
            # whether the first argument is a quote -- and a stripper that
            # blanks `w.set("ID"` to `w.set(    ` destroys the only evidence
            # that this is a name-keyed wrapper rather than a field write.
            # Stripping first made the discriminator match everything.
            no_strings = strip_comments_and_strings(text)
            with_strings = strip_comments_and_strings(text, keep_strings=True)
            areas = dbarea_names(no_strings)
            for label, pat in PATTERNS:
                code = with_strings if label == "set" else no_strings
                for lineno, line in enumerate(code.split("\n"), 1):
                    if not pat.search(line):
                        continue
                    rel_slash = rel.replace("\\", "/")
                    code_lines = code.split("\n")
                    func = enclosing_function(code_lines, lineno - 1)
                    ctext = call_text(line)
                    if label == "set":
                        m = RECEIVER.search(line)
                        if m is None:
                            # Not a plain identifier. COUNT IT and say so.
                            unclassified.append("%s:%d:%s" % (rel_slash, lineno, label))
                        elif m.group(1) not in areas:
                            excluded.append("%s:%d  (%s is not a DbArea here)"
                                            % (rel_slash, lineno, m.group(1)))
                            continue
                    hits.append(site_key(rel_slash, func, ctext, label))
                    where[site_key(rel_slash, func, ctext, label)] = "%s:%d" % (rel_slash, lineno)
    return sorted(set(hits)), sorted(set(excluded)), sorted(set(unclassified)), where



def selftest():
    """Falsify the KEY, which is the only thing this change touched.

    Two claims, and the second is the one nine drifts were waiting for:
      1. the same call in the same function keys IDENTICALLY after lines are
         inserted above it -- a relocation is silent;
      2. a genuinely different call in the same file keys DIFFERENTLY -- a new
         writer still speaks.
    """
    before = [
        "#include <a.hpp>",
        "static bool set_by_name(DbArea& a, const char* col) {",
        "    if (!a.set(i + 1, v)) { return false; }",
        "    return true;",
        "}",
    ]
    after = [
        "#include <a.hpp>",
        "#include <b.hpp>",
        "struct WsLock { int held; };",
        "",
        "static bool set_by_name(DbArea& a, const char* col) {",
        "    if (!a.set(i + 1, v)) { return false; }",
        "    return true;",
        "}",
    ]
    k1 = site_key("f.cpp", enclosing_function(before, 2), call_text(before[2]), "set")
    k2 = site_key("f.cpp", enclosing_function(after, 5), call_text(after[5]), "set")
    if k1 != k2:
        print("selftest FAIL: a relocation changed the key")
        print("  before: " + k1)
        print("  after : " + k2)
        return 2
    print("selftest: relocation is silent      OK")
    print("  key: " + k1)

    added = list(after)
    added.insert(6, "    if (!a.set(j + 1, w)) { return false; }")
    k3 = site_key("f.cpp", enclosing_function(added, 6), call_text(added[6]), "set")
    if k3 == k1:
        print("selftest FAIL: a genuinely new write did not change the key")
        return 2
    print("selftest: a new writer still speaks OK")
    print("  key: " + k3)

    moved = ["static bool other(DbArea& a) {",
             "    if (!a.set(i + 1, v)) { return false; }",
             "}"]
    k4 = site_key("f.cpp", enclosing_function(moved, 1), call_text(moved[1]), "set")
    if k4 == k1:
        print("selftest FAIL: the same text in another function kept the key")
        return 2
    print("selftest: another function differs  OK")
    return 0

def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--emit-baseline" in sys.argv:
        hits, _e, _u, _w = scan()
        for h in hits:
            print(h)
        return 0
    hits, excluded, unclassified, where = scan()

    by_file = {}
    for h in hits:
        f = h.split(" :: ")[0]
        by_file.setdefault(f, 0)
        by_file[f] += 1

    print("field-write-callers: %d direct call site(s) in %d file(s) outside the engine"
          % (len(hits), len(by_file)))
    if excluded:
        print("  %d `set(` call(s) excluded -- the receiver is not a DbArea in that file:"
              % len(excluded))
        for e in excluded:
            print("    " + e)
    if unclassified:
        print("  %d `set(` call(s) COUNTED but not attributable to a named receiver."
              % len(unclassified))
        print("  Unknown is counted, never dropped. Read these by hand:")
        for u in unclassified:
            print("    " + u)

    have_baseline = os.path.exists(BASELINE)
    if not have_baseline:
        print("  baseline %s is absent -- reporting the whole set as the backlog." % BASELINE)
        for f in sorted(by_file, key=lambda k: (-by_file[k], k)):
            print("    %4d  %s" % (by_file[f], f))
        print()
        print("  Write these lines to the baseline to freeze the backlog:")
        for h in hits:
            print(h)
        return 0

    with open(BASELINE, "r", encoding="utf-8") as f:
        base = sorted(set(l.strip() for l in f
                          if l.strip() and not l.startswith("#")))

    # A LEGACY BASELINE IS NOT COMPARED, AND SAYS SO. Keying changed from
    # file:line to file + function + call text (see the note above scan()).
    # Comparing the two shapes would report every site FIXED and every site
    # NEW at once -- thirteen false alarms in one run, which is exactly the
    # noise this change exists to end. It reports the migration instead.
    if is_legacy_baseline(base):
        print("  BASELINE IS IN THE OLD file:line SHAPE -- not compared this run.")
        print("  The key is now file + enclosing function + call text, so an")
        print("  insertion above a site no longer reads as FIXED plus NEW.")
        print("  This is a ONE-TIME migration and the count must not change.")
        print("  Regenerate, then diff the counts before committing:")
        print("    python tools/staging/check_field_write_callers.py --emit-baseline")
        print("  current site count: %d in %d file(s)" % (len(hits), len(by_file)))
        return 0

    new = [h for h in hits if h not in base]
    fixed = [b for b in base if b not in hits]

    if new:
        print("  NEW -- a direct field write that does not go through the funnel:")
        for h in new:
            print("    %s        [%s]" % (h, where.get(h, "?")))
        print("  Route it through xbase::cli::replaceFieldStored / replaceFieldNull,")
        print("  or -- if it is a deliberate below-the-funnel writer like the key")
        print("  generator -- add it to EXEMPT_FILES with the reason, not to the baseline.")
    if fixed:
        print("  FIXED -- in the baseline and now routed, drop these lines:")
        for b in fixed:
            print("    " + b)
    if not new and not fixed:
        print("  PASS -- direct-write set matches the baseline exactly.")

    # ADVISORY: never non-zero. The backlog predates the funnel and blocking on
    # it would only teach people to switch the gate off.
    return 0


if __name__ == "__main__":
    sys.exit(main())
