#!/usr/bin/env python3
"""R21.4 at CONTAINER granularity. AIF-120, R39.

R38 gave the whole window one scope, so destroying any container cancelled every
container's pending work. R21.4 says a CONTAINER's destruction cancels the work its
own handlers queued -- and this lane wrote that rule, so getting it wrong at this
granularity is a defect against ourselves.

Two panels, one handler in flight in each. Destroy one. The other must finish.
"""
import os, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef, uidef_tk


def author(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"SCOPES"')]),
            'SOURCE': uidef.props([('Alias', 'a'), ('Table', 'a.dbf'),
                                   ('Alias', 'b'), ('Table', 'b.dbf')])}]

    def obj(oid, parent, kind, ordinal, pairs=(), binding='', handlers='', flow=''):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'authored', 'PROPS': uidef.props(list(pairs)),
                    'HANDLERS': handlers})

    obj('F1', '', 'form', 1, [('Caption', '"two panels"')], flow='column')
    # Two panels, two work areas with NO relation -- so they are separate lock
    # domains and the handlers really do run at the same time.
    obj('P1', 'F1', 'panel', 1, flow='column')
    obj('B1', 'P1', 'button', 1, [('Caption', '"work in P1"')], binding='a.x',
        handlers=uidef.props([('Click', 'Slow / worker -> Done')]))
    obj('P2', 'F1', 'panel', 2, flow='column')
    obj('B2', 'P2', 'button', 1, [('Caption', '"work in P2"')], binding='b.y',
        handlers=uidef.props([('Click', 'Slow / worker -> Done')]))
    uidef.write(stem + '.DBF', stem + '.FPT', out)


def main():
    stem = '/tmp/SCOPES'
    author(stem)
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
    print("  lock domains:", rt.domains.describe())
    made['B1'].invoke()
    made['B2'].invoke()
    t0 = time.time()
    while time.time() - t0 < 0.12:
        root.update(); time.sleep(0.01)
    print("  destroying P1 while both handlers are in flight")
    made['P1'].destroy()
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
    print()
    print("  completions delivered:", done)
    print("  runtime log           :", [l for l in rt.log])
    dropped = [l for l in rt.log if l[0] == 'dropped']
    finished = [d for d in done if d[2] == 'completed' and 'P2' in str(d[1])]
    print()
    print("  R21.4  the destroyed container's work was dropped :", bool(dropped))
    print("  R21.4  the SURVIVING container's work completed   :", bool(finished))


if __name__ == '__main__':
    main()
