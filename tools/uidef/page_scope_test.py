#!/usr/bin/env python3
"""Page and pageset teardown. AIF-120, R46.

A notebook page has TWO removal verbs on every toolkit: one that destroys the page
window and one that merely detaches it. R45.2 says a lifetime rule must not depend
on which API ended the lifetime -- and detaching does not end it, so the two verbs
must differ here, and differ the same way on both targets.

  destroy the page  -> its queued work is cancelled  (R21.4)
  forget the page   -> the window is alive, so nothing is cancelled
"""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef, uidef_tk


def author(stem):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"PAGES"')]),
            'SOURCE': uidef.props([('Alias', 'a'), ('Table', 'a.dbf'),
                                   ('Alias', 'b'), ('Table', 'b.dbf'),
                                   ('Alias', 'c'), ('Table', 'c.dbf')])}]

    def obj(oid, parent, kind, ordinal, pairs=(), binding='', handlers='', flow=''):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'authored', 'PROPS': uidef.props(list(pairs)),
                    'HANDLERS': handlers})

    click = uidef.props([('Click', 'Slow / worker -> Done')])
    obj('F1', '', 'form', 1, [('Caption', '"pages"')], flow='column')
    obj('PS', 'F1', 'pageset', 1, flow='column')
    obj('PG1', 'PS', 'page', 1, [('Caption', '"one"')], flow='column')
    obj('BP1', 'PG1', 'button', 1, [('Caption', '"work in PG1"')], binding='a.x', handlers=click)
    obj('PG2', 'PS', 'page', 2, [('Caption', '"two"')], flow='column')
    obj('BP2', 'PG2', 'button', 1, [('Caption', '"work in PG2"')], binding='b.y', handlers=click)
    obj('PSIB', 'F1', 'panel', 2, flow='column')
    obj('BSIB', 'PSIB', 'button', 1, [('Caption', '"work outside"')], binding='c.z', handlers=click)
    uidef.write(stem + '.DBF', stem + '.FPT', out)


def run(stem, mode):
    verb, who = mode.split(':')
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
    for b in ('BP1', 'BP2', 'BSIB'):
        made[b].invoke()
    t0 = time.time()
    while time.time() - t0 < 0.12:
        root.update(); time.sleep(0.01)

    if verb == 'forget':
        made['PS'].forget(made[who])        # detached, window still alive
    else:
        made[who].destroy()

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
    print("  mode %-12s --" % mode, end=' ')
    for n in ('PS', 'PG1', 'PG2', 'PSIB'):
        print("%s dropped=%-5s completed=%-5s |"
              % (n, n in dropped, n in finished), end=' ')
    print()


def main():
    stem = '/tmp/PAGES_TK'
    author(stem)
    for mode in ('destroy:PG1', 'destroy:PS', 'forget:PG1'):
        run(stem, mode)


if __name__ == '__main__':
    main()
