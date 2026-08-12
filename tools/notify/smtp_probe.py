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
#   python smtp_probe.py --probe            # login only, report OK/fail
#   python smtp_probe.py --send SUBJECT     # send body from stdin to SMTP_USER
#   add --debug for the full wire conversation (stderr)

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

    debug = "--debug" in sys.argv
    send = "--send" in sys.argv
    subject = ""
    if send:
        i = sys.argv.index("--send")
        subject = sys.argv[i + 1] if i + 1 < len(sys.argv) else "smtp probe"

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
                msg["To"] = user
                msg["Subject"] = subject
                msg.set_content(sys.stdin.read() or "probe")
                s.send_message(msg)
                print("SENT")
        return 0
    except smtplib.SMTPAuthenticationError as e:
        print(f"AUTH FAILED: {e.smtp_code} {e.smtp_error!r}", file=sys.stderr)
        return 3
    except Exception as e:  # noqa: BLE001 - probe reports everything
        print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
