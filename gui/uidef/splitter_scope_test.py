#!/usr/bin/env python3
"""Scope containment across a SPLITTER. AIF-120, R88.

R44 proved R21.4 one container deep. R45 proved it nested -- `group > panel`.
Both of those parent their children through a SIZER, and cancellation rides on
widget destruction, so the question R45 answered was really "does destroying a
sizer-parented container destroy its subtree".

A splitter does not parent through a sizer. Its two panes go in through
`Split*()` / `PanedWindow.add()`, which is why R85 had to special-case it in
three generators. That makes it the first container in this lane whose child
ownership is NOT the mechanism R44 and R45 tested, and R85 added it to
`CONTAINER_KINDS` in every backend without proving the scope half.

The tree, four DISJOINT work areas so all four handlers are really in flight:

    F1 (form)
      WORK (splitter)
        AREAP (panel) > BAR   a.x
        INNER (splitter)
          NBK (panel) > BNB   b.y
          LOG (panel) > BLG   c.z
      PSIB (panel) > BSIB     d.w        <- outside the splitter entirely

Destroy targets and what each must prove:

    INNER   cancels NBK and LOG. AREAP and PSIB must COMPLETE -- this is the
            discriminating case, because AREAP is INNER's SIBLING inside the
            same splitter. An implementation that cancels per-splitter rather
            than per-pane fails here and passes everything else.
    WORK    cancels AREAP, NBK and LOG. PSIB must complete.
    PSIB    cancels only itself. Nothing inside the splitter may notice.
"""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef, uidef_tk

SUBTREE = {'INNER': {'NBK', 'LOG'},
           'WORK':  {'AREAP', 'NBK', 'LOG'},
           'PSIB':  {'PSIB'}}
ALL_SCOPES = ('AREAP', 'NBK', 'LOG', 'PSIB')
BUTTONS = ('BAR', 'BNB', 'BLG', 'BSIB')


def author(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"SPLITSCOPE"')]),
            'SOURCE': uidef.props([('Alias', 'a'), ('Table', 'a.dbf'),
                                   ('Alias', 'b'), ('Table', 'b.dbf'),
                                   ('Alias', 'c'), ('Table', 'c.dbf'),
                                   ('Alias', 'd'), ('Table', 'd.dbf')])}]

    def obj(oid, parent, kind, ordinal, pairs=(), binding='', handlers='', flow=''):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'authored', 'PROPS': uidef.props(list(pairs)),
                    'HANDLERS': handlers})

    click = uidef.props([('Click', 'Slow / worker -> Done')])
    obj('F1',    '',      'form',     1, [('Caption', '"splitter scope"')], flow='column')
    obj('WORK',  'F1',    'splitter', 1, [('MinPane', '40'), ('Weight', '1'), ('Fill', 'true')], flow='row')
    obj('AREAP', 'WORK',  'panel',    1, flow='column')
    obj('BAR',   'AREAP', 'button',   1, [('Caption', '"work in AREAP"')], binding='a.x', handlers=click)
    obj('INNER', 'WORK',  'splitter', 2, [('MinPane', '40')], flow='column')
    obj('NBK',   'INNER', 'panel',    1, flow='column')
    obj('BNB',   'NBK',   'button',   1, [('Caption', '"work in NBK"')], binding='b.y', handlers=click)
    obj('LOG',   'INNER', 'panel',    2, flow='column')
    obj('BLG',   'LOG',   'button',   1, [('Caption', '"work in LOG"')], binding='c.z', handlers=click)
    obj('PSIB',  'F1',    'panel',    2, flow='column')
    obj('BSIB',  'PSIB',  'button',   1, [('Caption', '"work outside"')], binding='d.w', handlers=click)
    uidef.write(stem + '.DBF', stem + '.FPT', out)


def run(stem, target):
    done = []

    def Slow(scope):
        for i in range(40):
            if scope.cancelled.is_set():
                return 'cancelled in %s at step %d' % (scope.name, i)
            time.sleep(0.01)
        return 'finished in %s' % scope.name

    def Done(scope, result, state):
        done.append((scope.name, result, state))

    root, made, rt = uidef_tk.build_window(
        stem + '.DBF', registry={'Slow': Slow, 'Done': Done})
    for b in BUTTONS:
        made[b].invoke()
    t0 = time.time()
    while time.time() - t0 < 0.12:
        root.update(); time.sleep(0.01)
    made[target].destroy()
    t0 = time.time()
    while time.time() - t0 < 1.5:
        try:
            root.update()
        except Exception:
            break
        time.sleep(0.01)
    rt.pump()
    try:
        root.destroy()
    except Exception:
        pass

    dropped = {l[2] for l in rt.log if l[0] == 'dropped'}
    finished = {d[0] for d in done if d[2] == 'completed'}
    want_dropped = SUBTREE[target]
    want_finished = set(ALL_SCOPES) - want_dropped

    ok = True
    parts = []
    for n in ALL_SCOPES:
        if n in want_dropped:
            good = n in dropped and n not in finished
            parts.append("%s=%s" % (n, 'cancelled' if good else 'NOT-CANCELLED'))
        else:
            good = n in finished
            parts.append("%s=%s" % (n, 'completed' if good else 'NOT-COMPLETED'))
        ok = ok and good
    print("  destroy %-6s %s   %s" % (target, 'PASS' if ok else 'FAIL', '  '.join(parts)))
    return ok


def main():
    stem = '/tmp/SPLITSCOPE'
    author(stem)
    results = [run(stem, t) for t in ('INNER', 'WORK', 'PSIB')]
    print("splitter-scope: %d/%d" % (sum(results), len(results)))
    return 0 if all(results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
