#!/usr/bin/env python3
"""Resolve a workspace name the way the ENGINE resolves it, and name the shadows. AIF-120 R84.

WHY THIS EXISTS, stated plainly because it is a correction to my own method.

Across this session I asked `git ls-files` which workspace file was
authoritative, got `dottalkpp/data/workspaces/mcc_x64.dtschema`, and reasoned
from it through two rulings. The file the engine actually loads is
`dottalkpp/user/default/workspaces/mcc_x64.dtschema` -- 12 areas and 15
relations against the tracked file's 13 and 0 -- and it is GITIGNORED, so no
clone can ever obtain it. The repository was the decoy.

The house rule is *a search shaped by the object you have cannot find an object
with a different schema*. Recording that a sixth time changes nothing. This
makes the question mechanical: WHICH FILE WINS is now a measurement, not a
judgement, and the answer comes from the resolver instead of from the index.

TRANSCRIBED FROM `src/cli/cmd_ersatz.cpp`, NOT FROM A SAMPLE:

  workspace_search_roots()      :455   current-user, public, default, data
  resolve_workspace_target()    :588   extension present -> try as given;
                                       otherwise `.dtschema` across ALL roots,
                                       THEN `.dtschemas` across all roots
                                       (extension is the OUTER loop -- a
                                       `.dtschemas` in the user root does NOT
                                       beat a `.dtschema` in data)
  resolve_in_roots()            :490   absolute wins; then cwd-relative; then a
                                       name containing a separator is tried
                                       DATA-relative; then each root in order
  current_profile_name()        :392   returns the literal "default" today,
                                       with the comment "Replace later with
                                       real authenticated user selection"

That last line is why the report separates ACTIVE shadowing from LATENT. Today
roots 1 and 3 are the same directory and `user/derald/` is never consulted, so
per-user divergence cannot happen yet. It happens the day that function is
implemented, silently, to everyone who already has a private copy.

THE OTHER RESOLVER. `WORKSPACE LOAD` does NOT use this path -- it resolves
relative to DATA only, which is why `ws load mcc_64` reports
`data\mcc_64.dtschema` and looks nowhere else. So one name has two answers
depending on who asks. This tool answers as ERSATZ; `--data-only` answers as
WORKSPACE LOAD, and disagreement between them is the finding.

    python resolve_workspace.py mcc_x64 --root D:/code/ccode
    python resolve_workspace.py mcc_x64 --root . --data-only
    python resolve_workspace.py --selftest
"""
import os
import subprocess
import sys

EXTS = ('.dtschema', '.dtschemas')


def search_roots(dottalk_root, profile='default'):
    """cmd_ersatz.cpp:455, in order. `app_root()/user/<profile>/workspaces` etc."""
    dp = os.path.join(dottalk_root, 'dottalkpp')
    base = os.path.join(dp, 'user')
    return [
        ('current-user', os.path.join(base, profile, 'workspaces')),
        ('public', os.path.join(base, 'public', 'workspaces')),
        ('default', os.path.join(base, 'default', 'workspaces')),
        ('data', os.path.join(dp, 'data', 'workspaces')),
    ]


def _exists(p):
    return os.path.isfile(p)


def candidates(name, dottalk_root, profile='default'):
    """Every (label, path) the resolver would TRY, in the order it tries them.

    Returned whole rather than short-circuited: the shadows are the point.
    """
    out = []
    has_ext = os.path.splitext(name)[1] != ''
    roots = search_roots(dottalk_root, profile)
    exts = [''] if has_ext else list(EXTS)
    for ext in exts:                      # extension is the OUTER loop (:602)
        for label, root in roots:
            out.append((label, os.path.normpath(os.path.join(root, name + ext))))
    return out


def data_only(name, dottalk_root):
    """How `WORKSPACE LOAD` answers: DATA-relative, one candidate, no roots."""
    n = name if os.path.splitext(name)[1] else name + '.dtschema'
    return os.path.normpath(os.path.join(dottalk_root, 'dottalkpp', 'data', n))


def git_status(path, repo):
    """tracked / untracked / ignored. `ignored` is the one that matters: R42.1
    says `git add` on it is a no-op, so a shadow that is ignored can never be
    published, only reproduced by hand."""
    rel = os.path.relpath(path, repo).replace(os.sep, '/')
    def run(args):
        return subprocess.run(['git', '--no-optional-locks'] + args, cwd=repo,
                              capture_output=True, text=True)
    if run(['check-ignore', '-q', rel]).returncode == 0:
        return 'IGNORED'
    if run(['ls-files', '--error-unmatch', rel]).returncode == 0:
        return 'tracked'
    return 'untracked'


def shape(path):
    """A cheap fingerprint so two files with one name can be told apart at a
    glance. Counting is the whole reason today's defect was visible at all."""
    if not _exists(path):
        return None
    areas = rels = 0
    ver = 0
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            for line in fh:
                u = line.strip().upper()
                if u.startswith('AREA '):
                    areas += 1
                elif u.startswith('RELATION '):
                    rels += 1
                elif u.startswith('DTSHEMA '):
                    try:
                        ver = int(u.split()[1])
                    except (IndexError, ValueError):
                        ver = 0
    except OSError:
        return None
    return {'v': ver, 'areas': areas, 'relations': rels}


def report(name, dottalk_root, repo=None, profile='default', as_data_only=False):
    repo = repo or dottalk_root
    lines = []
    if as_data_only:
        p = data_only(name, dottalk_root)
        ok = _exists(p)
        lines.append('WORKSPACE LOAD (DATA-relative, one candidate):')
        lines.append('  %-9s %s%s' % ('FOUND' if ok else 'absent', p,
                                      '   ' + str(shape(p)) if ok else ''))
        return '\n'.join(lines), (0 if ok else 1)

    found = []
    lines.append('ERSATZ resolution of %r (profile=%s):' % (name, profile))
    for label, p in candidates(name, dottalk_root, profile):
        if _exists(p):
            s = shape(p)
            found.append((label, p, s))
            lines.append('  HIT   [%-12s] %s' % (label, p))
            lines.append('        v%d  areas=%d  relations=%d  git=%s'
                         % (s['v'], s['areas'], s['relations'], git_status(p, repo)))
        else:
            lines.append('  miss  [%-12s] %s' % (label, p))

    if not found:
        lines.append('RESULT: unresolved -- ERSATZ would fall back to the '
                     'current-user root (cmd_ersatz.cpp:609)')
        return '\n'.join(lines), 1

    win_label, win_path, win_shape = found[0]
    lines.append('')
    lines.append('WINNER: %s   [%s]' % (win_path, win_label))
    shadows = found[1:]
    if not shadows:
        lines.append('No shadows. This name has one answer.')
        return '\n'.join(lines), 0

    lines.append('SHADOWED: %d other file(s) answer to this name.' % len(shadows))
    differs = [s for s in shadows if s[2] != win_shape]
    same = len(shadows) - len(differs)
    if same:
        lines.append('  %d are the same shape as the winner -- duplication, not divergence.' % same)
    for label, p, s in differs:
        lines.append('  DIVERGES [%-12s] v%d areas=%d relations=%d  git=%s'
                     % (label, s['v'], s['areas'], s['relations'], git_status(p, repo)))
        lines.append('           %s' % p)

    wg = git_status(win_path, repo)
    if wg != 'tracked' and any(git_status(p, repo) == 'tracked' for _, p, _ in shadows):
        lines.append('')
        lines.append('FINDING: the winner is %s and a LOSER is tracked. A clone gets the'
                     ' file that does not load.' % wg)
        if wg == 'IGNORED':
            lines.append('         The winner is gitignored, so it can never be staged'
                         ' (R42.1) -- only reproduced by hand.')
        return '\n'.join(lines), 2
    return '\n'.join(lines), (2 if differs else 0)


def selftest():
    fails = []
    c = candidates('mcc_x64', '/R')
    if len(c) != 8:
        fails.append('expected 8 candidates for an extensionless name, got %d' % len(c))
    if not c[0][1].endswith(os.path.normpath('user/default/workspaces/mcc_x64.dtschema')):
        fails.append('current-user root must be tried first: %r' % c[0][1])
    if not c[3][1].endswith(os.path.normpath('data/workspaces/mcc_x64.dtschema')):
        fails.append('data root must be fourth: %r' % c[3][1])
    # extension is the OUTER loop: every .dtschema before any .dtschemas
    first_s = next(i for i, (_, p) in enumerate(c) if p.endswith('.dtschemas'))
    if first_s != 4:
        fails.append('.dtschemas must not start until index 4, started at %d' % first_s)
    if len(candidates('mcc_x64.dtschema', '/R')) != 4:
        fails.append('a name WITH an extension gets one pass, not two')
    if not data_only('mcc_64', '/R').endswith(os.path.normpath('data/mcc_64.dtschema')):
        fails.append('WORKSPACE LOAD is DATA-relative: %r' % data_only('mcc_64', '/R'))
    for f in fails:
        print('FAIL -- %s' % f)
    print('%s -- 6 check(s)' % ('FAIL' if fails else 'OK'))
    return 1 if fails else 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--selftest' in args:
        sys.exit(selftest())
    if not args:
        print(__doc__.strip().split('\n\n')[-1])
        sys.exit(2)
    root = '.'
    if '--root' in args:
        root = args[args.index('--root') + 1]
    txt, rc = report(args[0], os.path.abspath(root),
                     as_data_only='--data-only' in args)
    print(txt)
    sys.exit(rc)
