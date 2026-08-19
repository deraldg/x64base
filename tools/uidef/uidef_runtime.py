#!/usr/bin/env python3
"""The dispatch and locking runtime a GENERATED frontend uses. AIF-120, R37.

Everything this lane ruled about concurrency was proven in a model.
`contend_test.py` and `relate_test.py` build a `Workspace` class and drive it
directly; `dispatch_test.py` fires handlers at a Tk window that owns no data. The
contract's own open item 15 says it plainly: *"Nothing takes a lock."*

This is the missing piece -- the runtime a generated app actually runs on:

  R21.1  work is serialized at HANDLER granularity, not per operation
  R21.4  a completion is delivered AT MOST once; destroying the container drops it
  R26    the lock is per LOCK DOMAIN -- the transitive closure of related work
         areas, read from the document's own SOURCE (R36)
  R20    a `host` handler needs no thread rule, no completion and no registry
"""
import os, queue, sys, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class LockDomains:
    """One lock per domain, read from the document rather than assumed.

    R26 measured that locking the work area a handler NAMES is worth nothing when a
    relation moves another area's pointer for you -- 100 failures in 100 trials,
    identical to no locking at all. So the runtime never locks an area; it locks the
    domain the area belongs to.
    """

    def __init__(self, domains, granularity='domain'):
        # `area` is the WRONG reading kept runnable on purpose: it locks the work
        # area a handler names, which is what R11.4 said before R26 corrected it.
        # A runtime that can be configured wrong on request is how you show the
        # difference in the generated app rather than in a model.
        if granularity == 'area':
            domains = [{a} for d in domains for a in d]
        self.granularity = granularity
        self.domains = [frozenset(d) for d in domains]
        self.locks = {d: threading.RLock() for d in self.domains}
        self.of = {}
        for d in self.domains:
            for alias in d:
                self.of[alias] = d

    def lock_for(self, alias):
        d = self.of.get((alias or '').lower())
        if d is None:                       # an area the document did not declare
            d = frozenset([(alias or '').lower()])
            self.of[(alias or '').lower()] = d
            self.locks[d] = threading.RLock()
            self.domains.append(d)
        return self.locks[d]

    def describe(self):
        return [sorted(d) for d in self.domains]


class Scope:
    """A container's lifetime. R21.4: destroying it cancels what it queued."""

    def __init__(self, name):
        self.name = name
        self.cancelled = threading.Event()
        self.alive = True

    def destroy(self):
        self.alive = False
        self.cancelled.set()


class Runtime:
    def __init__(self, domains, registry, host=None, post=None,
                 granularity='domain'):
        self.domains = LockDomains(domains, granularity)
        self.registry = registry
        self.host = host or {}
        self.q = queue.Queue()
        self.post = post or self.q.put
        self.ui_thread = threading.get_ident()
        self.log = []

    def note(self, *a):
        self.log.append(a)

    # -- the three dispatch values -------------------------------------
    def fire(self, name, disp, scope, alias=None, completion=None):
        if disp == 'host':
            fn = self.host.get(name)
            if fn is None:
                self.note('refused', name, 'no host capability')
                return False
            fn()                                   # R20: no thread rule at all
            self.note('host', name)
            return True

        fn = self.registry.get(name)
        if fn is None:
            self.note('refused', name, 'not in the registry (R14)')
            return False

        if disp == 'ui':
            with self.domains.lock_for(alias):     # R21.1: whole handler
                fn(scope)
            self.note('ui', name)
            return True

        if disp == 'worker':
            if not completion:
                self.note('refused', name, 'worker with no ON_COMPLETE (R11.3)')
                return False

            def body():
                state, result = 'completed', None
                try:
                    # R21.1 and R26: one lock, for the whole handler, over the whole
                    # domain. Not per operation and not per work area.
                    with self.domains.lock_for(alias):
                        result = fn(scope)
                    if scope.cancelled.is_set():
                        state = 'cancelled'
                except Exception as e:
                    state, result = 'failed', repr(e)
                self.post((scope, completion, result, state))

            threading.Thread(target=body, daemon=True).start()
            self.note('worker', name)
            return True

        self.note('refused', name, 'unknown DISPATCH %r' % disp)
        return False

    # -- the completion pump, on the UI thread only --------------------
    def pump(self):
        delivered = 0
        try:
            while True:
                scope, comp, result, state = self.q.get_nowait()
                if not scope.alive:
                    # R21.4: at most once. The container is gone; the completion
                    # would touch a destroyed widget.
                    self.note('dropped', comp, scope.name)
                    continue
                fn = self.registry.get(comp)
                if fn is None:
                    self.note('refused', comp, 'completion not in the registry')
                    continue
                assert threading.get_ident() == self.ui_thread, \
                    "a completion ran off the UI thread -- R11.3"
                fn(scope, result, state)
                self.note('complete', comp, state)
                delivered += 1
        except queue.Empty:
            pass
        return delivered


def domains_from_source(source_text, ):
    """Read the lock domains out of a DOC record's SOURCE (R36)."""
    aliases, edges = [], []
    for line in (source_text or '').replace('\r\n', '\n').split('\n'):
        if ' = ' not in line:
            continue
        k, v = line.split(' = ', 1)
        k = k.strip().lower()
        if k == 'alias':
            aliases.append(v.strip().lower())
        elif k == 'relation':
            body, expr = (v.split(' ON ', 1) + [''])[:2]
            if ' -> ' in body:
                a, b = body.split(' -> ', 1)
                edges.append((a.strip().lower(), b.strip().lower()))
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for a in aliases:
        find(a)
    g = {}
    for x in parent:
        g.setdefault(find(x), set()).add(x)
    return sorted(g.values(), key=lambda d: (-len(d), sorted(d)))
