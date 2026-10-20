#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: tools
# layer: gate
# owns:
# project: project.x64base.runtime
# lane: x64-memo-slot-predicate-one-owner
# owner: member.derald
# status: supported
"""Refuse a second definition of the x64 memo slot predicate (R149, AIF-172).

WHY THIS EXISTS. Measured 2026-10-20 at 03673c073: the test for an x64
object-id memo slot -- x64 flavour, type 'M'/'m', and a width equal to
X64_MEMO_FIELD_LEN -- was written out TEN times in two signatures, and all ten
bodies were IDENTICAL. That is the hazard rather than the comfort. They agreed
because the copy-paste was faithful, and nothing kept them agreeing.

The predicate is not a convenience. It decides what a field READ returns
(loadFieldsFromBuffer, decodeFieldFromBuffer), whether a consumer may treat the
returned string as an object id, and whether a field WRITE lays down eight raw
bytes or text. A disagreement across those layers is silent data corruption.
So there is ONE owner -- include/xbase/x64_memo_slot.hpp -- and this gate exists
because doctrine without a gate is a comment.

WHAT COUNTS AS A HIT. One function, after comments and string literals are
blanked out, containing BOTH halves CLOSE TOGETHER:

  * a memo-TYPE TEST   -- a `.type` compared against 'M' or 'm', or a call to a
                          helper named is_memo_type; and
  * a memo-WIDTH TEST  -- a comparison involving .length against
                          X64_MEMO_FIELD_LEN, X64_MEMO_REF_TOKEN_LEN, or a bare
                          8 or 16;

within 200 characters of each other once whitespace is collapsed, because every
real copy writes them as ONE boolean expression.

`case 'M':` IS NOT A TYPE TEST -- IT IS A DISPATCH, and the distinction was
learned on this gate's first real run. Without it, two large switches over field
types were reported as copies: xbase::validateFieldDef (whose 'D' case tests
length 8) and cli::record_pack::pack_field. Neither re-derives this predicate;
both merely dispatch on a type letter and happen to test a width elsewhere in
the same function. A gate that cries wolf on a dispatcher teaches the operator
to push past it, which is how the next real copy gets through.

Both halves together are the shape. Either half alone is NOT reported, and that
is deliberate in both directions:

  * a width test with no type test is ordinary field arithmetic;
  * a TYPE TEST WITH NO WIDTH TEST IS A DIFFERENT DEFECT, not this one.
    cmd_use.cpp's attach path tests the type alone, which is why the engine
    opens a real MemoStore for an M(16) table that its own readers then refuse.
    Widening this gate to catch that would bury a real finding inside a
    duplication check. It belongs to its own item.

ACCEPTED BLIND SPOT, STATED RATHER THAN DISCOVERED LATER: a copy that puts the
type test in one function and the width test in another is not seen. The trade
is the same one the sibling gates make -- a shape-matcher that reaches across
function boundaries reports noise, and noise is how an instrument stops being
read.

COMMENTS AND STRINGS ARE BLANKED FIRST, AND THAT IS NOT COSMETIC. The files this
gate watches explain themselves at length: cmd_pack.cpp's refusal note spells
out "f.length == 8" and names X64_MEMO_FIELD_LEN in prose. Scanning raw text
would report every one of those as a copy, the gate would be waved past within a
week, and the eleventh real copy would arrive behind it.

NO BASELINE FILE, DELIBERATELY. The expected set is exactly one path. A baseline
of things that are FINE is how a measurement stops meaning anything.

Usage (PowerShell 7, from the repo root):

    $py12 tools\\staging\\check_memo_slot_predicate.py
    $py12 tools\\staging\\check_memo_slot_predicate.py --selftest

Exit codes: 0 clean, 1 cannot locate the tree, 2 a second definition exists.
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.getcwd()
SCAN_ROOTS = ("src", "include")
SUFFIXES = (".cpp", ".hpp", ".h")

# THE OWNER. Counting it would make the gate report the thing it is measuring.
OWNER = os.path.join("include", "xbase", "x64_memo_slot.hpp")

SKIP_DIRS = {
    # Tests assert on the predicate's behaviour directly, by design: a test that
    # builds an M(16) field and checks the answer must name both halves.
    os.path.join("src", "tests"),
    # Probes and cost harnesses, not engine or command code.
    os.path.join("src", "tools"),
}

# A TYPE TEST, NOT A DISPATCH. `.type == 'M'` is a predicate re-deriving this
# question; `case 'M':` is a switch arm. See the module docstring.
TYPE_TEST = re.compile(r"\.type\s*(?:==|!=)\s*'[Mm]'|'[Mm]'\s*(?:==|!=)\s*[A-Za-z_]\w*\.type|is_memo_type\s*\(")
WS = re.compile(r"\s+")
NEAR = 200
WIDTH_TEST = re.compile(
    r"\.length\s*(?:==|!=|<|>|<=|>=)\s*(?:static_cast<[^>]*>\s*\(\s*)?"
    r"(?:(?:::)?xbase::)?(?:X64_MEMO_FIELD_LEN|X64_MEMO_REF_TOKEN_LEN|8|16)\b"
    r"|(?:(?:::)?xbase::)?(?:X64_MEMO_FIELD_LEN|X64_MEMO_REF_TOKEN_LEN)\s*(?:==|!=)\s*[A-Za-z_]"
)

# A function-ish definition line: a name, an open paren, and no semicolon before
# the brace. Good enough to attribute a hit to a function; never used to exclude.
FUNC_DEF = re.compile(r"^[A-Za-z_][\w:<>,&*\s\[\]]*\b([A-Za-z_]\w*)\s*\([^;]*$")


def blank_comments_and_strings(text: str) -> str:
    """Replace // and /* */ comments and "..." / '...' literals with spaces,
    preserving every newline so reported line numbers stay true."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and nxt == "*":
            out.append("  ")
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append("  ")
                i += 2
        elif c == '"':
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


def both_halves_near(body: str) -> bool:
    """True when a type test and a width test sit within NEAR characters of each
    other once whitespace is collapsed. Collapsing is what makes the distance
    mean something: the blanked-out comments between two halves would otherwise
    push a genuine one-expression copy apart."""
    flat = WS.sub(" ", body)
    types = [m.start() for m in TYPE_TEST.finditer(flat)]
    if not types:
        return False
    widths = [m.start() for m in WIDTH_TEST.finditer(flat)]
    if not widths:
        return False
    return any(abs(t - w) <= NEAR for t in types for w in widths)


def functions(text: str):
    """Yield (name, start_line_1based, body_text) for each braced block whose
    opening line looks like a definition. Character literals are kept, so the
    type test survives; comments and strings are already blanked by the caller.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = FUNC_DEF.match(lines[i].strip())
        if not m:
            i += 1
            continue
        # find the first '{' at or after this line, then its matching '}'
        joined_from = i
        depth = 0
        started = False
        body = []
        j = i
        while j < len(lines):
            body.append(lines[j])
            for ch in lines[j]:
                if ch == "{":
                    depth += 1
                    started = True
                elif ch == "}":
                    depth -= 1
            if started and depth <= 0:
                break
            if not started and ";" in lines[j]:
                break   # a declaration, not a definition
            j += 1
        if started:
            yield m.group(1), joined_from + 1, "\n".join(body)
        i = max(j, i) + 1


def in_skip_dir(rel: str) -> bool:
    return any(rel.startswith(d + os.sep) or rel.startswith(d + "/") for d in SKIP_DIRS)


def scan():
    hits = []
    scanned = 0
    for root_name in SCAN_ROOTS:
        base = os.path.join(ROOT, root_name)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for name in sorted(files):
                if not name.endswith(SUFFIXES):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, ROOT)
                if in_skip_dir(rel) or os.path.normpath(rel) == os.path.normpath(OWNER):
                    continue
                try:
                    raw = open(full, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                scanned += 1
                if "length" not in raw:
                    continue
                clean = blank_comments_and_strings(raw)
                for fname, line, body in functions(clean):
                    if both_halves_near(body):
                        hits.append((rel.replace(os.sep, "/"), line, fname))
    return hits, scanned


def selftest() -> int:
    cases = []

    def case(label, text, expect_hit):
        clean = blank_comments_and_strings(text)
        got = any(both_halves_near(b) for _n, _l, b in functions(clean))
        cases.append((label, got == expect_hit))

    case("the collapsed shape in a stray file is a HIT", """
static bool mine(const DbArea& a, int f1) {
    const auto& f = a.fields()[f1 - 1];
    return (f.type == 'M' || f.type == 'm') && f.length == xbase::X64_MEMO_FIELD_LEN;
}
""", True)

    case("the same shape written with a bare 8 is a HIT", """
static bool mine(const FieldDef& f) {
    if (f.type != 'M') return false;
    return f.length == 8;
}
""", True)

    case("the negative spelling is a HIT", """
static bool mine(const FieldDef& f) {
    return (f.type == 'M' || f.type == 'm') &&
           f.length != static_cast<std::uint32_t>(xbase::X64_MEMO_FIELD_LEN);
}
""", True)

    case("the shape in a // comment is NOT a hit", """
static bool mine(const FieldDef& f) {
    // return (f.type == 'M' || f.type == 'm') && f.length == X64_MEMO_FIELD_LEN;
    return x64_memo_slot_kind(f, true) == X64MemoSlotKind::ObjectId8;
}
""", False)

    case("the shape in a /* */ comment is NOT a hit", """
static bool mine(const FieldDef& f) {
    /* type 'M' at f.length == 8 is the object-id slot */
    return x64_memo_slot_kind(f, true) == X64MemoSlotKind::ObjectId8;
}
""", False)

    case("the shape inside a string literal is NOT a hit", """
static void explain() {
    std::cout << "type 'M' with f.length == 8 is an object-id slot\\n";
    int n = 0; (void)n;
}
""", False)

    case("a width test with no type test is NOT a hit", """
static bool wide(const FieldDef& f) {
    return f.length == 8;
}
""", False)

    case("a type test with no width test is NOT a hit (that is cmd_use.cpp's defect)", """
static bool anymemo(const FieldDef& f) {
    return f.type == 'M' || f.type == 'm';
}
""", False)

    case("the delegation is NOT a hit", """
static inline bool is_x64_memo_field_fast(bool is_x64, const FieldDef& f) noexcept {
    return x64_memo_slot_kind(f, is_x64) == X64MemoSlotKind::ObjectId8;
}
""", False)

    # THE TWO SHAPES THIS GATE'S FIRST REAL RUN GOT WRONG. Both are real code,
    # trimmed to the arms that mattered.
    case("a switch dispatcher with a 'D' length-8 arm is NOT a hit", """
bool validateFieldDef(const xbase::FieldDef& fd, std::string& err) {
    const char t = static_cast<char>(std::toupper(static_cast<unsigned char>(fd.type)));
    switch (t) {
    case 'D':
        if (fd.length != 8) { err = "date field length must be 8"; return false; }
        return true;
    case 'M':
        if (fd.length != 8 && fd.length != 10 && fd.length != 0) { return false; }
        return true;
    default:
        return false;
    }
}
""", False)

    case("a packer dispatching on meta.type is NOT a hit", """
inline PackResult pack_field(std::vector<char>& rec, const FieldMeta& meta) {
    PackResult res;
    switch (meta.type) {
        case 'D': case 'd': { if (meta.length != 8) { res.ok=false; } return res; }
        case 'M': case 'm': { res.ok = true; return res; }
        default: { res.ok=false; return res; }
    }
}
""", False)

    case("a halves-in-two-functions copy is NOT seen (stated blind spot)", """
static bool t(const FieldDef& f) { return f.type == 'M'; }
static bool w(const FieldDef& f) { return f.length == 8; }
""", False)

    # LINE NUMBERS MUST SURVIVE THE BLANKING. A gate that names the wrong line
    # sends the reader to the wrong place, which is worse than naming no line.
    text = "// a\n/* b\n   c */\nstatic bool mine(const FieldDef& f) {\n    return f.type == 'M' && f.length == 8;\n}\n"
    clean = blank_comments_and_strings(text)
    found = [(n, l) for n, l, b in functions(clean) if both_halves_near(b)]
    cases.append(("the hit is reported at line 4, not line 1",
                  found == [("mine", 4)]))

    fails = [lab for lab, ok in cases if not ok]
    for lab, ok in cases:
        print("  %-4s %s" % ("ok" if ok else "FAIL", lab))
    print("memo-slot-predicate selftest: %d case(s), %d failure(s)"
          % (len(cases), len(fails)))
    return 0 if not fails else 2


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    if not os.path.isdir(os.path.join(ROOT, "src")):
        print("check: run this from the repository root", file=sys.stderr)
        return 1

    hits, scanned = scan()
    print("memo-slot-predicate: %d file(s) scanned, owner is %s"
          % (scanned, OWNER.replace(os.sep, "/")))
    if not hits:
        print("memo-slot-predicate: PASS -- the predicate has exactly one definition.")
        return 0

    print("memo-slot-predicate: FAIL -- %d function(s) re-derive the predicate:" % len(hits))
    for rel, line, fname in hits:
        print("  %s:%d  %s()" % (rel, line, fname))
    print("")
    print("THIS PREDICATE DECIDES HOW BYTES ARE READ AND WRITTEN, so a second")
    print("answer to it is not untidy code -- it is a disagreement waiting to")
    print("become silent data corruption (R149, AIF-172). Call")
    print("xbase::x64_memo_slot_kind() instead; it returns None, ObjectId8,")
    print("RefToken16 or UnknownWidth, and the convenience wrappers")
    print("is_x64_memo_field() and is_undecodable_x64_memo_field() sit beside it.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
