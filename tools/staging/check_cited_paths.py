#!/usr/bin/env python3
"""Portal check: a document must not cite a repo path it does not ship.

The house calls a pointer whose target does not exist on the surface it ships on a
WIDOW, and section 10 of the working rules says to sweep for them before finishing.
That sweep had no mechanism. AIF-120 R42 measured what the absence costs: a ruling
shipped asserting a fix that was not in tracked code, because `git add` on a
gitignored path is a SILENT no-op -- the commit was clean, every gate passed, and
the file never moved. Nine committed tools were unimportable on a fresh clone for
the same reason.

No existing gate can see this. `prepush-gate` inspects the staged index and an
ignored path never reaches the index; `mandatory-tracked` checks a declared list and
these paths are not on it.

SCOPE: only documents in THIS change set. A gate that reported every pre-existing
widow in the tree would print the same paragraph every commit and stop being read
by the third day -- the reasoning `open-items` already uses.

TWO MORE LANES SHARE THAT SCOPE RULE WITHOUT OBEYING IT THE SAME WAY (OI-023,
2026-09-20). The RENAME SWEEP asks the inverted question -- does anything still
cite the path this change set just REMOVED -- so its trigger is change-set scoped
and its search is tree-wide, because a widow made by a rename is never in the
commit that made it. `--audit` drops the scoping entirely and always exits 0: it
reports the whole backlog and judges none of it, so the size of what the scoping
hides is knowable without anyone being blocked by it. Precedent for that mode and
that rule: check_house_style.py --audit.

Exit codes follow the portal convention: 0 clean, 3 advisory. Never 2. A widow is
someone forgetting to stage a file, and blocking the commit that would have carried
the rest of their work is the wrong trade.
"""
import os
import re
import subprocess
import sys

# `gui/` was added by AIF-120 R81.4. AIF-120 R71 promoted that lane out of
# `tools/uidef` into `gui/uidef` and retargeted 251 citations INTO a directory
# this tuple did not list -- so the promotion commit's `cited-paths: OK` was a
# green about the paths that had NOT moved. Measured at the time of the fix: 175
# citations across 66 documents were invisible here, and turning them on costs
# exactly one advisory.
ROOTS = ('docs/', 'tools/', 'src/', 'include/', 'labtalk/', 'coordination/',
         'dottalkpp/', 'scripts/', 'smoke/', 'gui/')
EXTS = ('.md', '.py', '.png', '.txt', '.h', '.hpp', '.cpp', '.csv', '.yaml',
        '.yml', '.dts', '.html', '.json', '.dbf', '.scx', '.mnx', '.vcx', '.frx',
        '.sh', '.ps1')
# A document that DOCUMENTS an ignored path -- R33 and R42 do exactly that, and so
# does any handoff explaining why a file cannot be staged -- would otherwise be
# flagged on every commit that touches it. A permanent advisory trains people to
# skip the whole check, which is the failure `open-items` was written to avoid.
# So a line may opt out explicitly, and the marker is greppable rather than magic:
#
#     the working copy at `tools/uidef/read_vfp_binary.py`  <!-- cite-check:ignore -->
#
# It suppresses only the line it appears on, so it cannot silence a document.
SUPPRESS = 'cite-check:ignore'

PATH_RE = re.compile(r'(?<![\w/.-])((?:%s)[A-Za-z0-9_./-]+)' % '|'.join(ROOTS))

# ---------------------------------------------------------------------------
# CROSS-REPO CITATIONS (2026-09-16)
#
# The anchor map cites 19 files that live in the WEBSITE repo, not this one.
# Before this lane existed, ROOTS was wrong about them IN BOTH DIRECTIONS AT
# ONCE, and which direction you got depended on a folder name:
#
#   content/docs/engine/primary-keys.mdx     `content/` is not in ROOTS, so
#                                            PATH_RE never matched it, so this
#                                            check printed OK without looking.
#                                            Eighteen citations, never verified,
#                                            not once.
#
#   scripts/engine-capabilities-v1.json      `scripts/` IS in ROOTS and `.json`
#                                            IS in EXTS, so it matched, was
#                                            looked for HERE, and was reported
#                                            MISSING -- a true file in the wrong
#                                            repo, reported as a widow.
#
# Prefixing them `x64base-site/` silences the false failure, because the char
# before the inner `scripts/` becomes `/` and PATH_RE's lookbehind rejects it.
# That is honest, and it is still silence. It also defused a trap worth naming:
# had the site ever renamed `content/` to `docs/`, eighteen silently-passing
# citations would have become eighteen hard failures overnight with no change in
# this repo at all.
#
# This lane resolves them instead. When the sibling checkout is reachable the
# citation is verified against ITS index; when it is not, the check says
# `unverifiable` out loud rather than printing a green that means "I did not
# look". UNVERIFIABLE NEVER MOVES THE EXIT CODE -- a colleague without the site
# checkout must not be blocked by a repo they do not have.
#
# `.mdx` and `.mjs` are here and deliberately NOT in EXTS above: adding them to
# the shared tuple would make PATH_RE start matching website extensions under
# THIS repo's roots, which is a different check with different truth.
SIBLING_EXTS = EXTS + ('.mdx', '.mjs', '.ts', '.tsx', '.css', '.svg')

SIBLINGS = {
    'x64base-site/': {
        'env': 'X64BASE_SITE_ROOT',
        # Ordered. The site is NOT a directory sibling of this checkout
        # (D:/code/ccode vs D:/dev/x64base-site), so a bare `../` guess fails;
        # the real relative hop is listed first among the guesses.
        'candidates': ('../../dev/x64base-site',
                       '../x64base-site',
                       '../../x64base-site'),
    },
}

SIBLING_RE = re.compile(
    r'(?<![\w/.-])((?:%s)[A-Za-z0-9_./-]+)'
    % '|'.join(re.escape(k) for k in sorted(SIBLINGS, key=len, reverse=True)))


class GitCommandError(RuntimeError):
    """A git query the checker depends on did not produce an answer."""


def git(args, *, input_text=None, ok=(0,)):
    """Run git with deterministic decoding and explicit return-code policy.

    Git emits repository bytes, not text in the active Windows locale. Using
    ``text=True`` without an encoding made a committed 0x81 byte crash range
    checks under cp1252. Returning an empty string on failure was worse: it
    converted "the query failed" into "nothing is tracked". Both conditions
    now stay observable.
    """
    cmd = ['git', '--no-optional-locks'] + args
    try:
        out = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
    except OSError as exc:
        raise GitCommandError("could not start %r: %s" % (cmd, exc)) from exc
    if out.returncode not in ok:
        detail = out.stderr.strip() or out.stdout.strip() or 'no diagnostic'
        raise GitCommandError(
            "%r exited %d: %s" % (cmd, out.returncode, detail))
    return out.stdout


def tracked_repo_paths(paths):
    """Return cited paths present in the current index, without path argv.

    Passing every citation to one ``git ls-files -- <644 paths>`` exceeded the
    Windows CreateProcess command-line limit. The index is small enough to read
    once; set intersection is both simpler and independent of citation count.
    """
    wanted = set(paths)
    tracked = set(git(['ls-files']).splitlines())
    return wanted.intersection(tracked)


WINDOWS_ARG_BUDGET = 24000


def git_path_batches(prefix, paths, *, ok=(0,)):
    """Run a path-taking Git query in Windows-safe argv batches."""
    wanted = sorted(set(paths))
    if not wanted:
        return ''
    base_cost = sum(len(a) + 3 for a in ['git', '--no-optional-locks'] + prefix)
    chunks = []
    chunk = []
    cost = base_cost + len(' --')
    for path in wanted:
        path_cost = len(path) + 3
        if chunk and cost + path_cost > WINDOWS_ARG_BUDGET:
            chunks.append(chunk)
            chunk = []
            cost = base_cost + len(' --')
        chunk.append(path)
        cost += path_cost
    if chunk:
        chunks.append(chunk)
    return ''.join(git(prefix + ['--'] + part, ok=ok) for part in chunks)


def ignored_repo_paths(paths):
    """Return ignored paths without exceeding the Windows argv ceiling."""
    text = git_path_batches(['check-ignore'], paths, ok=(0, 1))
    return {p for p in text.splitlines() if p}


def doc_text(doc, rev=None):
    """A document's text AS IT READ at `rev`. Empty string if unreadable.

    Factored out when the sibling lane was added so that all three readers --
    cited(), suppressed_lines() and sibling_cited() -- resolve `rev` the same
    way. Two of them reading the revision and one reading the working tree is
    the exact mismatch the docstring on cited() warns about.
    """
    if rev:
        return git(['show', '%s:%s' % (rev, doc)])
    try:
        return open(doc, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''


def staged_docs(range_spec):
    if range_spec:
        names = git(['diff', '--name-only', '--diff-filter=ACMR', range_spec])
    else:
        names = git(['diff', '--cached', '--name-only', '--diff-filter=ACMR'])
    return [p for p in names.splitlines() if p.endswith('.md') and os.path.exists(p)]


def cited(doc, rev=None):
    """The paths a document cites -- AS IT READ at `rev`, not as it reads now.

    Reading today's text while resolving targets at an old revision reports every
    document written since as a widow of that commit. Both halves have to come from
    the same moment, which is the same mismatch this check exists to find.
    """
    text = doc_text(doc, rev)
    out = set()
    for line in text.replace('\r\n', '\n').split('\n'):
        if SUPPRESS in line:
            continue
        for m in PATH_RE.finditer(line):
            p = m.group(1).rstrip('.,;:)`*')
            if p.endswith(EXTS):
                out.add(p)
    return out


def suppressed_lines(doc, rev=None):
    """Marked lines, and the paths each one hides. For REPORTING only.

    THE MARKER SUPPRESSES ANY LINE CONTAINING IT -- INCLUDING A LINE THAT ONLY
    NAMES IT. The sentence in the R126 ruling saying that idcite mirrors
    `cite-check:ignore` disarms its own line, so the path cited there is not
    checked.

    CORRECTION, 2026-08-25, recorded rather than quietly edited: this docstring
    first said that had hidden a REAL WIDOW -- an untracked idcite.py cited for
    the span of one commit. IT DID NOT. Checked afterwards: at 2bca2a60a the
    ruling did not mention idcite.py at all (that section was written later),
    and at 05f232360 the citation and the file landed in the SAME commit, so
    the path was tracked at every revision that cited it. The incident was
    inferred from a file-ordering worry and never measured. There is no known
    instance of this marker hiding a real widow.

    THE MECHANISM IS STILL REAL -- an incidental mention does disarm its line
    -- but the risk is theoretical, and this check is worth having on the
    weaker ground: a marker doing no work is noise a maintainer should see.

    THE SEMANTICS ARE DELIBERATELY NOT CHANGED. Two forms are in live use --
    `<!-- cite-check:ignore -->` and a bare parenthesised `(cite-check:ignore)`
    inside fenced code blocks where an HTML comment would render literally --
    so requiring one form would break real suppressions. And "greppable, not
    magic" is a stated design property of this marker (AIF120_CITATION_GATE).

    So this REPORTS instead. A marker that hides nothing needing hiding is
    almost always an incidental mention, and that is the case worth seeing.
    """
    text = doc_text(doc, rev)
    out = []
    for n, line in enumerate(text.replace('\r\n', '\n').split('\n'), 1):
        if SUPPRESS not in line:
            continue
        hidden = set()
        for m in PATH_RE.finditer(line):
            p = m.group(1).rstrip('.,;:)`*')
            if p.endswith(EXTS):
                hidden.add(p)
        out.append((n, sorted(hidden)))
    return out


def repo_root():
    top = git(['rev-parse', '--show-toplevel']).strip()
    return top or os.getcwd()


def sibling_cited(doc, rev=None):
    """{prefix: {relative path, ...}} -- cross-repo citations in one document.

    Deliberately a second pass rather than a widened PATH_RE. The two questions
    have different authorities: PATH_RE asks "is this tracked HERE", and getting
    a wrong answer blocks a commit, while this asks "is this tracked THERE",
    where the honest answer is sometimes "cannot tell from this machine".
    """
    text = doc_text(doc, rev)
    out = {}
    for line in text.replace('\r\n', '\n').split('\n'):
        if SUPPRESS in line:
            continue
        for m in SIBLING_RE.finditer(line):
            cite = m.group(1).rstrip('.,;:)`*')
            if not cite.endswith(SIBLING_EXTS):
                continue
            for prefix in SIBLINGS:
                if cite.startswith(prefix):
                    out.setdefault(prefix, set()).add(cite[len(prefix):])
                    break
    return out


def sibling_root(prefix, root):
    """(resolved path or None, [paths tried]).

    A worktree's `.git` is a FILE, not a directory, so this tests existence and
    not isdir -- checking for a directory would silently fail to find any
    checkout someone keeps as a linked worktree.
    """
    cfg = SIBLINGS[prefix]
    tried = []
    env = os.environ.get(cfg['env'])
    if env:
        tried.append(os.path.normpath(env))
    for c in cfg['candidates']:
        tried.append(os.path.normpath(os.path.join(root, c)))
    for cand in tried:
        if os.path.exists(os.path.join(cand, '.git')):
            return cand, tried
    return None, tried


def sibling_ignored(root, rels):
    """{relative path: "source:line:pattern"} for the ones that repo excludes.

    WITHOUT THIS, an excluded file is reported as a widow and the advice
    attached to a widow -- stage it -- IS USELESS, because `git add` on an
    excluded path is a silent no-op. That is R42.1, and this check already
    distinguishes the two cases for THIS repo; it did not for the sibling, so
    the first real finding it produced came with the wrong remedy.

    `-v` is what makes the answer actionable. `.gitignore` is versioned and
    every clone shares it; `.git/info/exclude` is LOCAL TO ONE CLONE, is not in
    version control, and does not survive a fresh clone -- so the same file can
    be invisible on one machine and untracked-and-loose on another. Naming the
    source is the difference between "this repo does not ship that" and "YOUR
    repo does not ship that."
    """
    text = git_path_batches(
        ['-C', root, 'check-ignore', '-v'], rels, ok=(0, 1))
    found = {}
    for line in text.splitlines():
        if '\t' not in line:
            continue
        where, path = line.rsplit('\t', 1)
        found[path.replace('\\', '/')] = where
    return found


def sibling_tracked(root, rels):
    """The subset of `rels` that the sibling repo tracks.

    Asks the sibling's INDEX, not its HEAD. We cannot know which commit of the
    site a given commit of this repo was written against, and the index is the
    only answer that is true right now for the person running the gate.
    """
    try:
        tracked = set(git(['-C', root, 'ls-files']).splitlines())
    except GitCommandError:
        return None
    return set(rels).intersection(tracked)


def check_siblings(docs, rev, root):
    """(lines to print, problem_found).

    problem_found gates the exit code; an unresolved sibling never sets it.
    """
    every = {}
    for d in docs:
        for prefix, rels in sibling_cited(d, rev).items():
            for rel in rels:
                every.setdefault(prefix, {}).setdefault(rel, []).append(d)
    if not every:
        return [], False

    lines, problem = [], False
    for prefix in sorted(every):
        cites = every[prefix]
        root_path, tried = sibling_root(prefix, root)
        label = prefix.rstrip('/')

        if root_path is None:
            lines.append("  UNVERIFIABLE  %d citation(s) into `%s` -- that "
                         "checkout was not found, so THIS CHECK DID NOT LOOK."
                         % (len(cites), label))
            lines.append("                set %s, or place it at one of: %s"
                         % (SIBLINGS[prefix]['env'], ', '.join(tried[-3:])))
            continue

        tracked = sibling_tracked(root_path, cites)
        if tracked is None:
            lines.append("  UNVERIFIABLE  %d citation(s) into `%s` -- found at "
                         "%s but `git ls-files` failed there."
                         % (len(cites), label, root_path))
            continue

        bad = sorted(set(cites) - tracked)
        excluded = sibling_ignored(root_path, bad) if bad else {}
        lines.append("  %s: %d citation(s), %d tracked in %s"
                     % (label, len(cites), len(tracked), root_path))
        for rel in bad:
            where = excluded.get(rel)
            if where:
                lines.append("  CROSS-REPO IGNORED  %s%s -- excluded there; "
                             "`git add` on it is a no-op (R42.1)" % (prefix, rel))
                lines.append("          by %s" % where)
                if '.git/info/exclude' in where.replace('\\', '/'):
                    lines.append("          NOTE: .git/info/exclude is LOCAL TO "
                                 "THAT CLONE and is not in version control, so "
                                 "this exclusion does not exist for anyone else "
                                 "or in a fresh clone.")
            else:
                on_disk = os.path.exists(os.path.join(root_path, rel))
                kind = "on disk, NOT tracked" if on_disk else "not on disk"
                lines.append("  CROSS-REPO WIDOW  %s%s -- %s" % (prefix, rel, kind))
            for d in cites[rel]:
                lines.append("          cited by %s" % d)
            problem = True
    return lines, problem


# ---------------------------------------------------------------------------
# THE RENAME SWEEP (OI-023)
#
# Every check above asks ONE question: does the path this CHANGED DOCUMENT
# cites exist? There is a second question with the same subject and the
# opposite direction, and nothing in this tree asked it: **does anything still
# cite the path this CHANGED FILE used to live at?**
#
# The two are not the same sweep and a rename is only visible to the second.
# Moving `fields_mgr.cpp` out of `src/core/` on 2026-08-30 left EIGHT files
# naming the old location, and this check saw none of them -- correctly, by its
# own scope rule, because none of those eight documents was in the change set.
# The breakage surfaced two commits later when an unrelated edit happened to
# touch the intake register.
#
# SCOPE IS PRESERVED AND INVERTED. The trigger stays change-set scoped: this
# only speaks when the change set REMOVES a citable path. What widens is where
# it then looks -- the whole tree, because a widow made by a rename can be
# anywhere and by definition is not in the commit that made it. A gate that
# reported every pre-existing widow would stop being read by the third day
# (the reasoning in this file's own header); a gate that fires on the rare
# commit that deletes a tracked file costs nothing on every other commit.
#
# A DELETE AND A RENAME ARE THE SAME EVENT HERE, which is why `--diff-filter`
# takes both. Git pairs a rename only when the content survives the move; a
# file that was moved AND heavily edited comes through as a delete plus an add,
# and the citations it orphans are just as broken. Asking only for R would have
# missed exactly the renames big enough to be worth noticing.
#
# MEASURED BEFORE IT WAS BUILT, 2026-09-20, because the item assumed a size it
# does not have. 1,820 tracked .md documents cite 2,222 distinct repo paths;
# 334 are not tracked -- 75 IGNORED, 158 WIDOW, 101 MISSING. Of the 101
# MISSING, TWELVE ever existed in git history and 89 never did. So this sweep
# addresses twelve paths, and the other 322 are a different problem that no
# rename sweep would ever touch. That is what `--audit` below is for.


def removed_paths(range_spec):
    """Citable repo paths the change set REMOVES -- deleted or renamed away.

    Returns old paths only. A rename's new path is not interesting here: it is
    present, so nothing cites it in vain.
    """
    args = ['diff', '-M', '--diff-filter=DR', '--name-status']
    args += [range_spec] if range_spec else ['--cached']
    out = git(args)
    gone = set()
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        # D -> ['D', path];  R### -> ['R100', old, new]. Old is always [1].
        old = parts[1]
        if old.startswith(ROOTS) and old.endswith(EXTS):
            gone.add(old)
    return sorted(gone)


def all_docs(rev=None):
    """Every tracked .md in the tree -- the search space, not the change set."""
    if rev:
        names = git(['ls-tree', '-r', '--name-only', rev])
    else:
        names = git(['ls-files'])
    return [p for p in names.splitlines() if p.endswith('.md')]


def orphan_sweep(range_spec, rev):
    """Who still cites what this change set just removed?

    Returns (lines, problem). Reads the whole document surface, so it returns
    EARLY AND FREE on the overwhelming majority of commits, which remove
    nothing citable.
    """
    gone = removed_paths(range_spec)
    if not gone:
        return [], False

    docs = all_docs(rev)
    holders = {}
    for d in docs:
        hits = cited(d, rev) & set(gone)
        for p in hits:
            holders.setdefault(p, []).append(d)

    lines = ["  rename sweep: %d path(s) removed by this change set, %d document(s) searched"
             % (len(gone), len(docs))]
    if not holders:
        lines.append("  rename sweep: OK -- nothing in the tree cites a path this "
                     "change set removed")
        return lines, False

    for p in sorted(holders):
        lines.append("  ORPHANED %s -- removed here, still cited by %d document(s)"
                     % (p, len(holders[p])))
        for d in holders[p]:
            lines.append("          cited by %s" % d)
    lines.append("  A citation that was true before this commit is a LIVE POINTER or a")
    lines.append("  HISTORICAL REFERENCE, and the two want opposite repairs. Repoint the")
    lines.append("  first at where the file went; respell the second so it stops parsing")
    lines.append("  as a pointer (OI-010). Do not repoint a session record -- it was")
    lines.append("  accurate when it was written and repointing it makes it a lie.")
    return lines, True


def main(argv):
    rng = argv[0] if argv else None
    rev = (rng.split('..')[-1] or 'HEAD') if rng else None

    # THE SWEEP RUNS BEFORE THE EARLY RETURN BELOW, AND THAT IS THE WHOLE POINT.
    # A commit that moves a .cpp and touches no .md has NO DOCUMENTS IN SCOPE --
    # it would take that return and never look. That commit is precisely the one
    # that orphans citations; the fields_mgr.cpp move was exactly this shape.
    sweep_lines, sweep_problem = orphan_sweep(rng, rev)

    docs = staged_docs(rng)
    if not docs:
        print("cited-paths: no documents in scope -- nothing to check")
        for ln in sweep_lines:
            print(ln)
        return 3 if sweep_problem else 0

    # Computed BEFORE the `no repo paths cited` early return below. A document
    # that cites only website files has no repo paths at all, and returning
    # there without running this lane would skip exactly the documents the lane
    # was written for -- the anchor map is one of them.
    try:
        sib_lines, sib_problem = check_siblings(docs, rev, repo_root())
    except Exception as exc:
        # This lane reaches outside the repo, so it can fail in ways the rest of
        # the check cannot. It must never be the reason a commit stops.
        sib_lines, sib_problem = ["  note: cross-repo lane skipped (%s: %s)"
                                  % (type(exc).__name__, exc)], False

    every = {}
    for d in docs:
        for p in cited(d, rev):
            every.setdefault(p, []).append(d)
    if not every:
        print("cited-paths: %d document(s), no repo paths cited" % len(docs))
        for ln in sib_lines + sweep_lines:
            print(ln)
        return 3 if (sib_problem or sweep_problem) else 0

    paths = sorted(every)
    # Resolve tracked-ness AT THE REVISION, not now. With no range this is the
    # staged index, which is the truth at commit time. With a range it must be
    # that commit's tree -- asking today's index whether a path existed then
    # produces a false CLEAN for every widow since fixed, which is the exact
    # class of false negative this check exists to catch.
    if rng:
        tracked = {p for p in git(['ls-tree', '-r', '--name-only', rev]).splitlines()
                   if p in set(paths)}
    else:
        tracked = tracked_repo_paths(paths)
    rest = [p for p in paths if p not in tracked]
    ignored = ignored_repo_paths(rest)

    # In range mode "on disk" means the working tree today, which says nothing
    # about that commit. Report both kinds as WIDOW there rather than guessing.
    widows = [p for p in rest if p not in ignored and (rng or os.path.exists(p))]
    missing = [p for p in rest if p not in ignored and not rng and not os.path.exists(p)]

    # ADVISORY: markers that are not doing any work. Cannot move the exit code.
    inert = []
    for d in docs:
        for line_no, hidden in suppressed_lines(d, rev):
            if not hidden or all(h in tracked for h in hidden):
                inert.append((d, line_no, hidden))

    print("cited-paths: %d document(s), %d path(s) cited, %d tracked"
          % (len(docs), len(paths), len(tracked)))
    for ln in sib_lines + sweep_lines:
        print(ln)
    if inert:
        print("  advisory: %d suppression(s) hiding nothing that needed hiding "
              "-- an incidental mention of the marker suppresses its own line:"
              % len(inert))
        for d, line_no, hidden in inert[:10]:
            why = ("no citable path" if not hidden
                   else "%d path(s), all tracked" % len(hidden))
            print("    %s:%d  (%s)" % (d, line_no, why))
        if len(inert) > 10:
            print("    ... and %d more" % (len(inert) - 10))
    if not (widows or missing or ignored or sib_problem or sweep_problem):
        print("cited-paths: OK -- every cited path is tracked")
        return 0
    if not (widows or missing or ignored):
        print("cited-paths: every path cited INTO THIS REPO is tracked; "
              "the cross-repo finding above is the only one.")

    for p in widows:
        print("  WIDOW   %s -- on disk, NOT tracked" % p)
        for d in every[p]:
            print("          cited by %s" % d)
    for p in missing:
        print("  MISSING %s -- cited, not on disk" % p)
        for d in every[p]:
            print("          cited by %s" % d)
    for p in sorted(ignored):
        print("  IGNORED %s -- `git add` on it is a no-op (R42.1)" % p)
        for d in every[p]:
            print("          cited by %s" % d)
    return 3 if (widows or missing or ignored or sib_problem or sweep_problem) else 0


def looks_like_prose(path):
    """True when the token is a SENTENCE the matcher swallowed, not a path.

    `gui/uidef/workbench_session.hpp/.cpp` is one file name written as two, and
    PATH_RE takes the lot as a single path ending in `.cpp`. It has been cited
    three times and reported MISSING by every audit that ever looked, which is
    a phantom rather than a finding. The test is structural and narrow: a
    component BEFORE the last one carrying a known extension cannot be a
    directory anybody made.

    Report-only, and deliberately NOT wired into PATH_RE. Narrowing the matcher
    changes what every other lane in this file sees, and AIF-120 R81.4 is the
    record of what a quiet change to this tuple costs -- 175 citations
    invisible, never verified, not once. Name the class, leave the matcher.
    """
    parts = path.split('/')
    return any(c.endswith(EXTS) for c in parts[:-1])


def ever_deleted():
    """Every path git has ever seen removed. The slow half of --audit.

    `--diff-filter=D` with no `-M` counts a rename as a delete of the old name,
    which is what this needs: it answers "did this path ever exist", not "was
    it renamed".
    """
    out = git(['log', '--diff-filter=D', '--name-only', '--format='], ok=(0, 1))
    return {ln for ln in out.splitlines() if ln}


def audit():
    """Full-tree census of citations. ALWAYS EXITS 0 -- it reports, it does not judge.

    The gate proper is change-set scoped for a reason its own header states, and
    that scoping means nobody has ever seen the size of the backlog. This does,
    in the same vocabulary, so the two numbers are comparable. Precedent for the
    mode and the never-judge rule: check_house_style.py --audit.
    """
    docs = all_docs()
    every = {}
    for d in docs:
        for pth in cited(d):
            every.setdefault(pth, []).append(d)

    paths = sorted(every)
    tracked = tracked_repo_paths(paths)
    rest = [pth for pth in paths if pth not in tracked]
    ignored = ignored_repo_paths(rest)

    prose = [pth for pth in rest if pth not in ignored and looks_like_prose(pth)]
    body = [pth for pth in rest if pth not in ignored and pth not in prose]
    widows = [pth for pth in body if os.path.exists(pth)]
    missing = [pth for pth in body if not os.path.exists(pth)]

    print("cited-paths --audit: %d document(s), %d distinct repo path(s) cited"
          % (len(docs), len(paths)))
    print("  tracked                          : %d" % len(tracked))
    print("  IGNORED   git add is a no-op     : %d" % len(ignored))
    print("  WIDOW     on disk, not tracked   : %d" % len(widows))
    print("  MISSING   not on disk at all     : %d" % len(missing))
    print("  MALFORMED a sentence, not a path : %d" % len(prose))

    print("  (reading history for the MISSING split -- this is the slow part)")
    gone = ever_deleted()
    moved = [pth for pth in missing if pth in gone]
    never = [pth for pth in missing if pth not in gone]
    print("  of the MISSING, EXISTED ONCE (a move or a delete) : %d" % len(moved))
    print("  of the MISSING, NEVER IN HISTORY                  : %d" % len(never))
    print("  ONLY THE FIRST GROUP IS RENAME BREAKAGE. The second was wrong the day")
    print("  it was written -- a planned file, a generated output nobody tracks, or")
    print("  a typo -- and no sweep over renames will ever find it.")

    if moved:
        print("  -- MISSING that existed once, with a same-named successor if there is one --")
        by_base = {}
        for t in git(['ls-files']).splitlines():
            by_base.setdefault(os.path.basename(t), []).append(t)
        for pth in sorted(moved, key=lambda x: -len(every[x])):
            cands = by_base.get(os.path.basename(pth), [])
            where = ", ".join(cands) if cands else "(no file of that name anywhere -- deleted, not moved)"
            print("    %2d cite(s)  %s" % (len(every[pth]), pth))
            print("                -> %s" % where)
    if prose:
        print("  -- MALFORMED --")
        for pth in sorted(prose):
            print("    %2d cite(s)  %s" % (len(every[pth]), pth))
    return 0


def selftest():
    """Fixtures for the cross-repo lane. Run: check_cited_paths.py --selftest

    Every case here is a real temp git repo pair, not a mock. The lane's whole
    job is to ask another checkout a question, and a mock that answers cannot
    fail the way a missing checkout does.
    """
    import shutil
    import stat
    import tempfile

    def run(cmd, cwd):
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    def rmtree(path):
        """shutil.rmtree that survives a git object store on Windows.

        git writes loose objects with the read-only bit set. On POSIX that is
        irrelevant -- unlink needs write permission on the DIRECTORY, not the
        file -- so a plain rmtree works there and this function looks like
        superstition. On Windows os.unlink honours the read-only bit on the
        FILE and raises WinError 5, which is how the first version of this
        selftest died at case 12 of 13 on the owner machine while passing
        cleanly on Linux. Clear the bit, then retry.

        `onerror` was renamed `onexc` in Python 3.12 and the callback signature
        is three arguments either way, so the same handler serves both.
        """
        def force(func, target, _exc):
            try:
                os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
                parent = os.path.dirname(target)
                if parent:
                    os.chmod(parent, stat.S_IRWXU)
                func(target)
            except OSError:
                pass
        try:
            shutil.rmtree(path, onexc=force)
        except TypeError:
            shutil.rmtree(path, onerror=force)

    failures = []
    ran = []

    def check(name, got, want):
        ran.append(name)
        if got == want:
            print("  ok    %s" % name)
        else:
            print("  FAIL  %s\n          got  %r\n          want %r" % (name, got, want))
            failures.append(name)

    # -- pure-regex cases, no repo needed -----------------------------------
    # The prefix repair rests entirely on PATH_RE's lookbehind rejecting a
    # match whose preceding character is `/`. If that ever stops being true,
    # every website citation becomes a false MISSING again, so it is asserted
    # here rather than assumed.
    check("PATH_RE ignores a prefixed website path",
          PATH_RE.findall("see x64base-site/scripts/engine-capabilities-v1.json"),
          [])
    check("PATH_RE still catches a bare repo path",
          PATH_RE.findall("see tools/staging/prepush_gate.py"),
          ["tools/staging/prepush_gate.py"])
    check("SIBLING_RE catches the prefixed path",
          SIBLING_RE.findall("see x64base-site/content/docs/engine/primary-keys.mdx"),
          ["x64base-site/content/docs/engine/primary-keys.mdx"])
    check(".mdx is a sibling extension and not a local one",
          (".mdx" in SIBLING_EXTS, ".mdx" in EXTS),
          (True, False))

    # Exercise the remover before relying on it for cleanup. On Windows this
    # is the real thing: git's read-only object bits are what killed the first
    # version of this selftest. On POSIX AS ROOT it passes trivially, because
    # root ignores permission bits -- said plainly here so nobody reads a green
    # on a Linux CI box as evidence the Windows path works.
    probe = tempfile.mkdtemp(prefix="citecheck-rm-")
    probe_file = os.path.join(probe, "sub", "readonly.bin")
    os.makedirs(os.path.dirname(probe_file))
    open(probe_file, "wb").write(b"x")
    os.chmod(probe_file, stat.S_IREAD)
    os.chmod(os.path.dirname(probe_file), stat.S_IREAD | stat.S_IEXEC)
    rmtree(probe)
    check("rmtree clears read-only trees (git object stores)",
          os.path.exists(probe), False)

    tmp = tempfile.mkdtemp(prefix="citecheck-")
    try:
        here = os.path.join(tmp, "code", "ccode")
        site = os.path.join(tmp, "dev", "x64base-site")
        for d in (here, os.path.join(site, "content", "docs", "engine"),
                  os.path.join(site, "scripts")):
            os.makedirs(d, exist_ok=True)
        run(["git", "init", "-q"], here)
        run(["git", "init", "-q"], site)

        tracked_rel = "content/docs/engine/primary-keys.mdx"
        untracked_rel = "scripts/engine-capabilities-v1.json"
        absent_rel = "content/docs/engine/no-such-page.mdx"

        open(os.path.join(site, tracked_rel), "w").write("tracked\n")
        open(os.path.join(site, untracked_rel), "w").write("{}\n")
        run(["git", "add", "--", tracked_rel], site)

        doc = os.path.join(here, "ANCHORS.md")

        def report(body):
            open(doc, "w").write(body)
            return check_siblings([doc], None, here)

        lines, problem = report("cites `x64base-site/%s`\n" % tracked_rel)
        check("tracked sibling file is clean", problem, False)
        check("tracked sibling file is counted",
              any("1 citation(s), 1 tracked" in l for l in lines), True)

        lines, problem = report("cites `x64base-site/%s`\n" % untracked_rel)
        check("untracked-but-present sibling file is a widow", problem, True)
        check("untracked-but-present says on disk",
              any("on disk, NOT tracked" in l for l in lines), True)

        lines, problem = report("cites `x64base-site/%s`\n" % absent_rel)
        check("absent sibling file is a widow", problem, True)
        check("absent says not on disk",
              any("not on disk" in l for l in lines), True)

        lines, problem = report(
            "cites `x64base-site/%s` <!-- cite-check:ignore -->\n" % absent_rel)
        check("suppressed line is not checked", (lines, problem), ([], False))

        # -- excluded, the two sources, which need different remedies -------
        gi_rel = "content/docs/engine/gitignored-page.mdx"
        ex_rel = "content/portal/schemas.mdx"
        os.makedirs(os.path.join(site, "content", "portal"), exist_ok=True)
        open(os.path.join(site, gi_rel), "w").write("x\n")
        open(os.path.join(site, ex_rel), "w").write("x\n")
        open(os.path.join(site, ".gitignore"), "w").write("gitignored-page.mdx\n")
        os.makedirs(os.path.join(site, ".git", "info"), exist_ok=True)
        open(os.path.join(site, ".git", "info", "exclude"), "a").write(
            "content/portal/\n")

        lines, problem = report("cites `x64base-site/%s`\n" % gi_rel)
        check("gitignored sibling file reads as IGNORED not WIDOW",
              (any("CROSS-REPO IGNORED" in l for l in lines),
               any("CROSS-REPO WIDOW" in l for l in lines)), (True, False))
        check("gitignored sibling file still sets the exit code", problem, True)
        check("a versioned .gitignore carries no local-clone note",
              any("LOCAL TO" in l for l in lines), False)

        lines, problem = report("cites `x64base-site/%s`\n" % ex_rel)
        check("info/exclude sibling file reads as IGNORED",
              any("CROSS-REPO IGNORED" in l for l in lines), True)
        check("info/exclude is called out as local to that clone",
              any("LOCAL TO THAT CLONE" in l for l in lines), True)

        # -- the case that must NOT block: no sibling checkout at all --------
        # Built as a SEPARATE empty root rather than by deleting the one above.
        # Deleting it meant rmtree-ing a git object store mid-test, which is the
        # one operation in this whole file that is not portable -- and when it
        # failed on Windows it took the two most important assertions with it,
        # because they came after the delete. A case that proves the check does
        # not block must not itself be the thing that blocks.
        lonely = os.path.join(tmp, "lonely", "code", "ccode")
        os.makedirs(lonely, exist_ok=True)
        lonely_doc = os.path.join(lonely, "ANCHORS.md")
        open(lonely_doc, "w").write("cites `x64base-site/%s`\n" % tracked_rel)
        lines, problem = check_siblings([lonely_doc], None, lonely)
        check("missing sibling checkout never sets the exit code", problem, False)
        check("missing sibling checkout says it did not look",
              any("UNVERIFIABLE" in l and "DID NOT LOOK" in l for l in lines), True)
    finally:
        rmtree(tmp)

    # -- the rename sweep (OI-023) ------------------------------------------
    # Pure-function cases first, then a real repo. The sweep's whole claim is
    # that it fires on a commit with NO DOCUMENTS IN SCOPE, and only a repo
    # where that is literally true can prove it.
    check("prose with an inner extension is not a path",
          looks_like_prose("gui/uidef/workbench_session.hpp/.cpp"), True)
    check("an ordinary path is not prose",
          looks_like_prose("src/cli/table_state.cpp"), False)
    check("a dotted directory name is not prose",
          looks_like_prose("docs/v1.2/notes.md"), False)

    sweep_tmp = tempfile.mkdtemp(prefix="citecheck-sweep-")
    cwd0 = os.getcwd()
    try:
        repo = os.path.join(sweep_tmp, "repo")
        os.makedirs(os.path.join(repo, "src", "core"))
        os.makedirs(os.path.join(repo, "src", "xbase"))
        os.makedirs(os.path.join(repo, "docs"))
        open(os.path.join(repo, "src", "core", "foo.cpp"), "w").write("int foo();\n")
        doc = os.path.join(repo, "docs", "note.md")
        open(doc, "w").write("the mover lives at `src/core/foo.cpp` today\n")
        run(['git', 'init', '-q'], repo)
        run(['git', 'config', 'user.email', 'selftest@example.invalid'], repo)
        run(['git', 'config', 'user.name', 'selftest'], repo)
        run(['git', 'add', '-A'], repo)
        run(['git', 'commit', '-q', '-m', 'base'], repo)

        os.chdir(repo)

        # NOTHING REMOVED -> the sweep must cost nothing and say nothing.
        lines, problem = orphan_sweep(None, None)
        check("a commit that removes nothing produces no sweep output",
              (lines, problem), ([], False))

        run(['git', 'mv', 'src/core/foo.cpp', 'src/xbase/foo.cpp'], repo)
        run(['git', 'add', '-A'], repo)

        check("removed_paths reports the OLD path of a rename",
              removed_paths(None), ["src/core/foo.cpp"])

        # THE CASE THE ITEM IS ABOUT: the change set is one .cpp move and no
        # document at all, so `staged_docs` is empty and every other lane in
        # this file returns early.
        check("the change set has no documents in scope", staged_docs(None), [])

        lines, problem = orphan_sweep(None, None)
        check("a rename that orphans a citation is reported", problem, True)
        check("the orphaned OLD path is named",
              any("ORPHANED src/core/foo.cpp" in l for l in lines), True)
        check("the document still holding the pointer is named",
              any("cited by docs/note.md" in l for l in lines), True)

        # And main() must carry it out, not just the helper -- the early return
        # for "no documents in scope" is what swallowed this before.
        check("main() exits advisory on an orphaning rename", main([]), 3)

        open(doc, "w").write("the mover lives at `src/xbase/foo.cpp` today\n")
        run(['git', 'add', '-A'], repo)
        lines, problem = orphan_sweep(None, None)
        check("a rename whose citation followed it is clean", problem, False)
        check("the clean case still says how much it searched",
              any("rename sweep: OK" in l for l in lines), True)
    finally:
        os.chdir(cwd0)
        rmtree(sweep_tmp)

    print("cited-paths selftest: %d case(s), %d failure(s)"
          % (len(ran), len(failures)))
    return 1 if failures else 0


if __name__ == '__main__':
    # The filter below drops every dash-argument, so a flag has to be read
    # BEFORE it. `--selftest` passed to the old entry point would have been
    # silently swallowed and the check would have run a normal pass instead,
    # printing a green that answered a question nobody asked.
    if '--selftest' in sys.argv[1:]:
        sys.exit(selftest())
    if '--audit' in sys.argv[1:]:
        sys.exit(audit())
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith('-')]))
