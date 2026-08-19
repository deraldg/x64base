#!/usr/bin/env python3
"""A live DotTalk++ shell as a request/response surface. AIF-120, R66.

R61 established that the complex commands live at the dottalkpp level, and the
maintainer's charter reminder was blunt about the consequence: *"your charter was to
write a front end gui api for an engine that is already built, I understand you need
glue, but we dogfood"*. This is the glue -- and it is the smallest glue that can
exist, because it does not translate anything. It sends a command line and returns
what the shell printed.

Why a sentinel rather than a timeout: the shell has no request/response framing, so
the only reliable end-of-response marker is one we asked it to print. `ECHO` is a
non-destructive command whose output the shell prefixes, so a sentinel round-trips
visibly and cannot be confused with a result line.

This is NOT `shell_execute_line` (R61) -- that is the in-process C++ entry point a
compiled frontend embeds. This is the same command surface reached over a pipe, for
the Python runtime and for tests. Both are the command layer; neither is console
parsing of a program that was not asked a question (the anti-pattern
`docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md` names).
"""
import os, subprocess, threading, queue


class ShellSession:
    SENTINEL = '<<AIF120-EOR>>'

    def __init__(self, binary, cwd=None, banner_timeout=20.0, timeout=20.0):
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [binary], cwd=cwd or os.path.dirname(os.path.abspath(binary)),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._pump, daemon=True)
        self.t.start()
        self._drain(banner_timeout)

    def _pump(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip('\n'))
        self.q.put(None)

    def _drain(self, t):
        """Swallow the startup banner up to the first sentinel."""
        self.proc.stdin.write('ECHO %s\n' % self.SENTINEL)
        self.proc.stdin.flush()
        self._read_to_sentinel(t)

    def _read_to_sentinel(self, t):
        out = []
        while True:
            try:
                line = self.q.get(timeout=t)
            except queue.Empty:
                raise RuntimeError('shell did not answer within %.1fs' % t)
            if line is None:
                raise RuntimeError('shell exited')
            if self.SENTINEL in line:
                return out
            out.append(line)

    def send(self, cmd):
        """Send one command line; return everything the shell printed for it."""
        self.proc.stdin.write(cmd + '\nECHO %s\n' % self.SENTINEL)
        self.proc.stdin.flush()
        return '\n'.join(self._read_to_sentinel(self.timeout))

    # The two callables uidef_runtime.LockProvider wants.
    def run(self, cmd):
        """R66: this returns whether the command was DELIVERED, not whether it
        worked. The provider confirms the effect with `observe`, because R64.1
        measured that the command layer prints success unconditionally."""
        self.send(cmd)
        return True

    def observe(self, cmd):
        return self.send(cmd)

    def close(self):
        try:
            self.proc.stdin.write('QUIT\n')
            self.proc.stdin.flush()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
