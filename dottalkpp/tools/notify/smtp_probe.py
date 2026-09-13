#!/usr/bin/env python3
# smtp_probe.py -- cross-platform SMTP probe and sender (Python 3 stdlib only,
# per the AIF-085 tooling rule; replaces a PowerShell/.NET probe that violated
# it and could not show the conversation).
#
# Credentials arrive via environment variables set by a thin PLATFORM wrapper
# (on Windows: a one-liner that decrypts the owner's DPAPI clixml; on POSIX: a
# chmod-600 env file). This script never stores or logs the password; with
# --debug the smtplib wire trace goes to stderr and DOES show the base64 AUTH
# exchange, so use --debug only in a private console.
#
#   SMTP_USER / SMTP_PASS   required
#   SMTP_HOST (default smtp.gmail.com), SMTP_PORT (default 587)
#
# Usage:
#   python smtp_probe.py --probe                   # login only, report OK/fail
#   python smtp_probe.py --send SUBJECT            # body from stdin, to SMTP_USER
#   python smtp_probe.py --send SUBJECT --to ADDR  # body from stdin, to ADDR
#   add --debug for the full wire conversation (stderr)
#
# --to defaults to SMTP_USER, which is what this did before the flag existed, so
# every previous invocation keeps its old behaviour. A comma-separated list is
# accepted and passed through unaltered; smtplib parses the header.
#
# ARGUMENT PARSING IS DELIBERATELY AD HOC and is now slightly sharper than it
# was, because two flags take values. `--send --to x@y` would read "--to" as the
# SUBJECT. Both value-taking flags therefore REFUSE a value that begins with
# "--" rather than silently accepting it: a subject or recipient that looks like
# a flag is far more likely to be a missing argument than an intended value.
# If this grows a third value-taking flag, replace the hand parsing with argparse
# (stdlib, so AIF-085 is satisfied either way).

import os
import sys
import smtplib
import ssl
from email.message import EmailMessage


def main() -> int:
    user = os.environ.get("SMTP_USER", "")
    pw = os.environ.get("SMTP_PASS", "")
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))

    if not user or not pw:
        print("SMTP_USER / SMTP_PASS not set", file=sys.stderr)
        return 2

    print(f"user: {user}")
    print(f"password length: {len(pw)}  has spaces: {' ' in pw}")
    print(f"server: {host}:{port} (STARTTLS)")

    def flag_value(name: str, default: str) -> str:
        """Value following `name`, or `default`.

        Refuses a value that looks like another flag. A subject or recipient
        beginning with "--" almost always means the value was omitted, and
        accepting it silently would send mail with a nonsense subject, or worse,
        to nobody the caller intended.
        """
        if name not in sys.argv:
            return default
        i = sys.argv.index(name)
        if i + 1 >= len(sys.argv):
            return default
        value = sys.argv[i + 1]
        if value.startswith("--"):
            print(f"{name} expects a value, found {value!r}", file=sys.stderr)
            raise SystemExit(2)
        return value

    debug = "--debug" in sys.argv
    send = "--send" in sys.argv
    subject = flag_value("--send", "smtp probe") if send else ""
    # Default preserves the pre-flag behaviour: mail to yourself.
    to = flag_value("--to", user)

    try:
        with smtplib.SMTP(host, port, timeout=30) as s:
            if debug:
                s.set_debuglevel(1)
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.ehlo()
            s.login(user, pw)
            print("LOGIN: OK")
            if send:
                msg = EmailMessage()
                msg["From"] = user
                msg["To"] = to
                msg["Subject"] = subject
                msg.set_content(sys.stdin.read() or "probe")
                s.send_message(msg)
                # Report the recipient. Mail delivered somewhere the operator
                # did not intend is the failure this line exists to make loud.
                print(f"SENT to {to}")
        return 0
    except smtplib.SMTPAuthenticationError as e:
        print(f"AUTH FAILED: {e.smtp_code} {e.smtp_error!r}", file=sys.stderr)
        return 3
    except Exception as e:  # noqa: BLE001 - probe reports everything
        print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
