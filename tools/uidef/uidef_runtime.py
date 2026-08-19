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
import contextlib, os, queue, sys, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class LockProvider:
    """How the runtime actually takes a lock on the DATA.

    R47: until now it did not. `LockDomains` held `threading.RLock`s and nothing
    ever touched a table -- a simulation of locking running BESIDE the engine's
    own locks rather than through them. x64base has had `xbase::locks` the whole
    time: owner-aware (`host:pid:nonce`), sidecar-file based, cross-process, with
    liveness and recovery, and a defect history of its own (AIF-116).

    The house verb is DotTalk++'s own:  SELECT <alias> ; LOCK [TABLE] ; UNLOCK.
    A provider issues exactly that. The default provider is None -- in-process
    exclusion only -- because a frontend with no engine attached still has to run.

    R48 -- granularity. `LOCK TABLE` locks the whole area; bare `LOCK` locks the
    CURRENT RECORD of the selected area, which is the granularity a form actually
    edits. R26's closure is what makes the record form correct: a relation has
    already moved every child area's pointer to the matching row, so locking the
    current record of every area in the domain locks exactly the row set the
    handler can reach.

    Bare `LOCK` also carries NO NUMBER, and that is not a style preference.
    AIF-116 was a record number written through a stream that picked up a grouping
    locale -- `pid=16,984`, read back by `std::stoul` as `16`. The same surface
    exists for any frontend that renders a recno into a command:

        default-constructed ostringstream : LOCK 16,984
        round-trip of the grouped form    : 16

    The house verb that needs no number does not have that surface at all. If a
    future need forces `LOCK <n>`, the number must be rendered through the classic
    locale, and `tools/uidef/lock_provider_test.py` fails if any emitted command
    contains a digit that the runtime put there.
    """

    def __init__(self, run, granularity='table'):
        self.run = run                    # run(command_text) -> bool
        # 'table' is the conservative default and what R47 shipped: a handler that
        # SCANS an area needs the whole area, and the document does not say whether
        # a handler scans or edits one row. Choosing per handler is a schema
        # question and therefore the owner's.
        #
        # R52 measured, and R54 ruled: a table lock and record locks are
        # INDEPENDENT in x64base. `LOCK TABLE` succeeds while another process holds
        # a record lock --
        #
        #     . LOCK: table locked.
        #     . Table:  LOCKED (owner Grimwood:21109:...)
        #     Record 1: LOCKED (owner Grimwood:21080:...)
        #
        # -- and that is the OWNER'S RULING, not a defect. Record locking is meant
        # to be rich, and making one record holder veto every table lock would lock
        # people out to buy a guarantee most handlers do not need.
        #
        # The consequence for this runtime is what matters here: a `table` domain
        # lock excludes other TABLE lockers and says nothing about record editors.
        # A handler that SCANS an area under it may read rows another process is
        # mid-edit. `table` remains the default because it is strictly better than
        # `record` for a scanning handler -- not because it makes one safe. R54.3
        # names the engine query that would close the gap; nothing in a frontend
        # can.
        # R50: the RELEASE verb must pair with the ACQUIRE verb. Bare `UNLOCK`
        # unlocks the current RECORD, not the table (src/cli/cmd_unlock.cpp:
        # "UNLOCK with no arguments unlocks the current record"), so releasing a
        # `LOCK TABLE` with `UNLOCK` leaves the table lock held. Measured against
        # the real binary: after UNLOCK, `LOCK STATUS` still reported
        # `Table: LOCKED (owner Grimwood:5383:...)`.
        self.verb = 'LOCK TABLE' if granularity == 'table' else 'LOCK'
        self.unverb = 'UNLOCK TABLE' if granularity == 'table' else 'UNLOCK'
        self.granularity = granularity
        self.held = []

    def try_lock(self, aliases):
        """All-or-nothing across the domain. Releases what it took on failure.

        Order is sorted, so two processes contending for the same domain take the
        areas in the same order -- but that is defence in depth, not the reason
        this is safe: `try_lock_table` never waits, so no circular wait can form.
        """
        taken = []
        for a in sorted(aliases):
            if self.run('SELECT %s' % a) and self.run(self.verb):
                taken.append(a)
            else:
                for t in reversed(taken):
                    self.run('SELECT %s' % t)
                    self.run(self.unverb)
                return False
        self.held.append(tuple(sorted(aliases)))
        return True

    def unlock(self, aliases):
        for a in reversed(sorted(aliases)):
            self.run('SELECT %s' % a)
            self.run(self.unverb)
        try:
            self.held.remove(tuple(sorted(aliases)))
        except ValueError:
            pass


class LockDomains:
    """One lock per domain, read from the document rather than assumed.

    R26 measured that locking the work area a handler NAMES is worth nothing when a
    relation moves another area's pointer for you -- 100 failures in 100 trials,
    identical to no locking at all. So the runtime never locks an area; it locks the
    domain the area belongs to.
    """

    def __init__(self, domains, granularity='domain', provider=None):
        # `area` is the WRONG reading kept runnable on purpose: it locks the work
        # area a handler names, which is what R11.4 said before R26 corrected it.
        # A runtime that can be configured wrong on request is how you show the
        # difference in the generated app rather than in a model.
        if granularity == 'area':
            domains = [{a} for d in domains for a in d]
        self.granularity = granularity
        self.domains = [frozenset(d) for d in domains]
        # A plain Lock, taken with blocking=False. NOT an RLock, and not blocking:
        # `xbase::locks::try_lock_table` is a single attempt that returns false
        # (R47), which is FLOCK()'s own semantic. Re-entry by the SAME thread is
        # handled above the lock by a depth count, because a handler calling a
        # handler on its own data is not contention.
        self.locks = {d: threading.Lock() for d in self.domains}
        self.of = {}
        for d in self.domains:
            for alias in d:
                self.of[alias] = d
        self.provider = provider
        self._held = threading.local()

    def domain_of(self, alias):
        a = (alias or '').lower()
        d = self.of.get(a)
        if d is None:                       # an area the document did not declare
            d = frozenset([a])
            self.of[a] = d
            self.locks[d] = threading.Lock()
            self.domains.append(d)
        return d

    def lock_for(self, alias):              # kept for callers that only inspect
        return self.locks[self.domain_of(alias)]

    def _depth(self):
        if not hasattr(self._held, 'depth'):
            self._held.depth = {}
        return self._held.depth

    def acquire(self, alias):
        """Try once. Return True if this thread now holds the domain.

        No path here waits, so no circular wait can form: the AB-BA case that
        deadlocks a blocking implementation is refused on the second acquisition
        instead. That is not a guard bolted on -- it is what try-semantics mean.
        """
        d = self.domain_of(alias)
        depth = self._depth()
        if depth.get(d):                    # already mine: R21.1, not contention
            depth[d] += 1
            return True
        if not self.locks[d].acquire(blocking=False):
            return False
        if self.provider is not None and not self.provider.try_lock(d):
            self.locks[d].release()
            return False
        depth[d] = 1
        return True

    def release(self, alias):
        d = self.domain_of(alias)
        depth = self._depth()
        n = depth.get(d, 0)
        if n <= 0:
            return
        if n > 1:
            depth[d] = n - 1
            return
        depth[d] = 0
        if self.provider is not None:
            self.provider.unlock(d)
        self.locks[d].release()

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
                 granularity='domain', provider=None):
        self.domains = LockDomains(domains, granularity, provider=provider)
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
            if not self.domains.acquire(alias):    # R47: one attempt, like FLOCK()
                self.note('refused', name, 'domain busy (R47)')
                return False
            try:                                   # R21.1: whole handler
                fn(scope)
            finally:
                self.domains.release(alias)
            self.note('ui', name)
            return True

        if disp == 'worker':
            if not completion:
                self.note('refused', name, 'worker with no ON_COMPLETE (R11.3)')
                return False

            def body():
                state, result = 'completed', None
                # R47: ONE attempt. A busy domain refuses the handler rather than
                # queueing it -- FLOCK() returns .F., it does not wait. Everything
                # this lane recorded about contention before R47 described a
                # blocking lock the engine does not have.
                if not self.domains.acquire(alias):
                    self.note('refused', name, 'domain busy (R47)')
                    self.post((scope, completion, 'domain busy', 'refused'))
                    return
                try:
                    # R21.1 and R26: one lock, for the whole handler, over the whole
                    # domain. Not per operation and not per work area.
                    result = fn(scope)
                    if scope.cancelled.is_set():
                        state = 'cancelled'
                except Exception as e:
                    state, result = 'failed', repr(e)
                finally:
                    self.domains.release(alias)
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
