#!/usr/bin/env python3
"""The Tk backend driving the shared runtime. AIF-120, R38.

R37 built `uidef_runtime.py` and left it unadopted, which is the
produced-but-never-consumed shape R24 section 4 named -- created deliberately and
recorded as such. This closes it: `uidef_tk.build_window(path, registry=...)` now
builds a `Runtime` from the document's own `SOURCE` and fires every `Click` through
it, so the backend never decides what to lock. It is told.
"""
import os, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uidef, uidef_tk


def author(stem):
    """A document with two work areas, a relation between them, and handlers."""
    src = uidef.props([('Alias', 'students'), ('Table', 'students.dbf'),
                       ('Alias', 'enroll'), ('Table', 'enroll.dbf'),
                       ('Relation', 'students -> enroll ON sid')])
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored',
            'PROPS': uidef.props([('SourceFile', '"ADOPT"')]), 'SOURCE': src}]

    def obj(oid, parent, kind, ordinal, pairs=(), binding='', handlers='', flow=''):
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'authored', 'PROPS': uidef.props(list(pairs)),
                    'HANDLERS': handlers})

    obj('F1', '', 'form', 1, [('Caption', '"runtime adoption"')], flow='column')
    obj('B1', 'F1', 'button', 1, [('Caption', '"Total GPA"')], binding='students.gpa',
        handlers=uidef.props([('Click', 'TotalGpa / worker -> Done')]))
    obj('B2', 'F1', 'button', 2, [('Caption', '"Enrolments"')], binding='enroll.cls_id',
        handlers=uidef.props([('Click', 'ListEnrolments / worker -> Done')]))
    obj('B3', 'F1', 'button', 3, [('Caption', '"Cut"')],
        handlers=uidef.props([('Click', 'edit.cut / host')]))
    obj('B4', 'F1', 'button', 4, [('Caption', '"No completion"')],
        binding='students.sid',
        handlers=uidef.props([('Click', 'TotalGpa / worker')]))
    uidef.write(stem + '.DBF', stem + '.FPT', out)
    return out


def main():
    stem = '/tmp/ADOPT'
    author(stem)
    order = []
    lock_seen = []

    def TotalGpa(scope):
        order.append(('TotalGpa', 'enter', threading.get_ident()))
        time.sleep(0.15)
        order.append(('TotalGpa', 'leave', threading.get_ident()))
        return 588.74

    def ListEnrolments(scope):
        order.append(('ListEnrolments', 'enter', threading.get_ident()))
        time.sleep(0.05)
        order.append(('ListEnrolments', 'leave', threading.get_ident()))
        return ['F25ENGL260']

    def Done(scope, result, state):
        order.append(('Done', state, threading.get_ident()))

    registry = {'TotalGpa': TotalGpa, 'ListEnrolments': ListEnrolments, 'Done': Done}
    host = {'edit.cut': lambda: order.append(('host', 'edit.cut',
                                              threading.get_ident()))}

    root, made, rt = uidef_tk.build_window(stem + '.DBF', registry=registry, host=host)
    print("  lock domains, read from the document's SOURCE:", rt.domains.describe())
    print("  UI thread:", rt.ui_thread)
    print()
    made['B1'].invoke(); made['B2'].invoke(); made['B3'].invoke(); made['B4'].invoke()
    t0 = time.time()
    while time.time() - t0 < 2.0:
        root.update()
        time.sleep(0.01)
    root.destroy()

    print("  handler timeline (thread id in brackets):")
    for what, ev, tid in order:
        print("     %-16s %-10s [%d]" % (what, ev, tid))
    print()
    workers = [o for o in order if o[0] in ('TotalGpa', 'ListEnrolments')]
    overlapped = any(workers[i][1] == 'enter' and workers[i + 1][1] == 'enter'
                     for i in range(len(workers) - 1))
    print("  R21.1  two worker handlers on one lock domain OVERLAPPED :", overlapped)
    print("  R11.3  both ran OFF the UI thread                        :",
          all(t != rt.ui_thread for _, _, t in workers))
    print("  R11.3  every completion ran ON the UI thread             :",
          all(t == rt.ui_thread for w, _, t in order if w == 'Done'))
    print("  R20    host capability ran with no thread rule           :",
          any(w == 'host' for w, _, _ in order))
    print("  R11.3  worker with no ON_COMPLETE refused                :",
          any(l[0] == 'refused' for l in rt.log))
    print()
    print("  runtime log:", [l for l in rt.log])


if __name__ == '__main__':
    main()
