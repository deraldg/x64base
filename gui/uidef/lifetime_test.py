#!/usr/bin/env python3
"""Runtime test of R11.4's LIFETIME clause and the two unrun DISPATCH states.

R11.4: "Closing or destroying a container cancels the pending work its handlers
submitted. Nothing queued may outlive the window that queued it."

dispatch_test.py destroyed its window AFTER the worker finished, so the cancel
path never ran, and the `cancelled` and `failed` states never happened. This
destroys the container WHILE a worker is in flight.

Part 1 runs the naive runtime -- deliver the completion no matter what -- to see
what Tk does with it. Part 2 runs the scoped runtime R11.4 asks for.
"""
import queue, sys, threading, time, traceback
import tkinter as tk
from tkinter import ttk

LOG = []


def note(tag, msg):
    on = "UI" if threading.get_ident() == MAIN else "worker"
    LOG.append((tag, on, msg))
    print("    %-9s %-7s %s" % (tag, on, msg))


MAIN = threading.get_ident()


class Scope:
    """A container's lifetime. Destroying the container cancels the scope."""

    def __init__(self, name):
        self.name = name
        self.cancelled = threading.Event()
        self.alive = True

    def destroy(self):
        self.alive = False
        self.cancelled.set()


def SlowScan(scope, steps=20, step=0.02):
    """A worker that checks its scope between operations, as R11.4 requires."""
    for i in range(steps):
        if scope.cancelled.is_set():
            note("worker", "scope cancelled at step %d/%d -- returning early" % (i, steps))
            return None, 'cancelled'
        time.sleep(step)
    return "scanned %d" % steps, 'completed'


def Explodes(scope):
    raise ValueError("the handler body raised")


def run(part, scoped):
    print("  %s" % part)
    root = tk.Tk()
    root.geometry("320x120")
    frame = ttk.Frame(root)
    frame.pack(fill='both', expand=True)
    label = ttk.Label(frame, text="working...")
    label.pack(padx=10, pady=10)
    scope = Scope('frame1')
    q = queue.Queue()
    outcome = {}
    pending = {}

    def Done(result, state):
        # A completion handler. It touches a widget -- that is its whole job.
        note("complete", "state=%s result=%r" % (state, result))
        outcome['state'] = state
        try:
            label.configure(text="done: %s" % state)
            outcome['touched'] = 'ok'
        except tk.TclError as e:
            outcome['touched'] = 'TclError: %s' % e
            note("ERROR", "completion touched a destroyed widget: %s" % e)

    def pump():
        try:
            while True:
                sc, fn, args = q.get_nowait()
                if scoped and not sc.alive:
                    note("dropped", "completion for a dead scope %r never ran" % sc.name)
                    outcome['state'] = 'cancelled'
                    outcome['dropped'] = True
                    continue
                fn(*args)
        except queue.Empty:
            pass
        # The pump is itself queued work owned by a window. It has to obey the
        # same rule: cancel it when the window it belongs to goes away.
        try:
            pending['id'] = root.after(10, pump)
        except tk.TclError:
            pass

    def submit(fn):
        def body():
            try:
                r, st = fn(scope)
            except Exception as e:                    # the `failed` state
                r, st = repr(e), 'failed'
                note("worker", "raised: %s -- state becomes failed" % e)
            q.put((scope, Done, (r, st)))
        threading.Thread(target=body, daemon=True).start()

    submit(SlowScan)
    pump()
    # let it get in flight, then destroy the container underneath it
    t0 = time.time()
    while time.time() - t0 < 0.1:
        root.update(); time.sleep(0.01)
    note("UI", "destroying the container while the worker is in flight")
    frame.destroy()
    scope.destroy()
    t0 = time.time()
    while time.time() - t0 < 0.8:
        try:
            root.update()
        except tk.TclError:
            break
        time.sleep(0.01)
    try:
        if pending.get('id'):
            root.after_cancel(pending['id'])
    except tk.TclError:
        pass
    try:
        root.destroy()
    except tk.TclError:
        pass
    print()
    return outcome


def failed_state():
    print("  PART 3 -- the `failed` state, never previously reached")
    root = tk.Tk(); root.geometry("200x80")
    scope = Scope('f'); q = queue.Queue(); out = {}

    def Done(result, state):
        note("complete", "state=%s result=%s" % (state, result))
        out['state'] = state

    def body():
        try:
            r, st = Explodes(scope)
        except Exception as e:
            r, st = repr(e), 'failed'
            note("worker", "raised %r -- caught in the worker, NOT on the UI thread" % e)
        q.put((scope, Done, (r, st)))

    threading.Thread(target=body, daemon=True).start()
    t0 = time.time()
    while time.time() - t0 < 0.5:
        try:
            sc, fn, args = q.get_nowait(); fn(*args)
        except queue.Empty:
            pass
        root.update(); time.sleep(0.01)
    root.destroy()
    print()
    return out


print("R11.4 LIFETIME -- destroying a container with work in flight")
print()
a = run("PART 1 -- naive runtime: the completion is delivered regardless", scoped=False)
b = run("PART 2 -- scoped runtime: the pump drops a dead scope's completion", scoped=True)
c = failed_state()

print("RESULTS")
print("  worker observed cancellation          :",
      any(t == 'worker' and 'cancelled at step' in m for t, _, m in LOG))
print("  naive: completion hit a dead widget   :", a.get('touched'))
print("  scoped: completion dropped, cancelled :", b.get('dropped') is True and b.get('state') == 'cancelled')
print("  every completion ran on the UI thread :",
      all(on == 'UI' for t, on, _ in LOG if t in ('complete', 'dropped')))
print("  failed state reached on the UI thread  :", c.get('state') == 'failed')
