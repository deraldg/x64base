#!/usr/bin/env python3
"""Nested-container cancellation. AIF-120, R45.

R44 proved R21.4 one container deep and said so. This is the nested case:
F1 > G1(group) > { BG, PIN(panel) > BIN }, and F1 > PSIB(panel) > BSIB, with
three DISJOINT work areas so all three handlers really are in flight together.

Destroying a container must cancel its own subtree and nothing else. Destroying
the INNER one is the discriminating case -- an implementation that resolved a
handler to the OUTERMOST container instead of the nearest passes the "destroy the
middle" test and fails this one.
"""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef, uidef_tk


def author(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"NESTED"')]),
            'SOURCE': uidef.props([('Alias', 'a'), ('Table', 'a.dbf'),
                                   ('Alias', 'b'), ('Table', 'b.dbf'),
                                   ('Alias', 'c'), ('Table', 'c.dbf')])}]

    def obj(oid, parent, kind, ordinal, pairs=(), binding='', handlers='', flow=''):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'authored', 'PROPS': uidef.props(list(pairs)),
                    'HANDLERS': handlers})

    click = uidef.props([('Click', 'Slow / worker -> Done')])
    obj('F1', '', 'form', 1, [('Caption', '"nested"')], flow='column')
    obj('G1', 'F1', 'group', 1, [('Caption', '"middle"')], flow='column')
    obj('BG', 'G1', 'button', 1, [('Caption', '"work in G1"')], binding='a.x', handlers=click)
    obj('PIN', 'G1', 'panel', 2, flow='column')
    obj('BIN', 'PIN', 'button', 1, [('Caption', '"work in PIN"')], binding='b.y', handlers=click)
    obj('PSIB', 'F1', 'panel', 2, flow='column')
    obj('BSIB', 'PSIB', 'button', 1, [('Caption', '"work in PSIB"')], binding='c.z', handlers=click)
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
    for b in ('BG', 'BIN', 'BSIB'):
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
    print("  destroyed %-5s --" % target, end=' ')
    for n in ('G1', 'PIN', 'PSIB'):
        print("%s dropped=%-5s completed=%-5s |"
              % (n, n in dropped, n in finished), end=' ')
    print()


def main():
    stem = '/tmp/NESTED_TK'
    author(stem)
    for target in ('G1', 'PIN', 'PSIB'):
        run(stem, target)


if __name__ == '__main__':
    main()
