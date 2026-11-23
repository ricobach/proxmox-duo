"""Manually invoked diagnostic client. Never use as an authentication hook."""
from __future__ import annotations

import argparse
import configparser
import os
from pathlib import Path
import stat
import sys
import time

from .push import DuoPush, Settings


def load_settings(path: str) -> Settings:
    # Require a regular, non-symlink file unreadable by group and other.
    p = Path(path)
    info = p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
        raise ValueError("Config must be a regular file with mode 0600 or stricter")
    if info.st_uid != os.geteuid():
        raise ValueError("Config must be owned by the current effective user")
    parser = configparser.ConfigParser(interpolation=None)
    with p.open(encoding="utf-8") as stream:
        parser.read_file(stream)
    return Settings(
        ikey=parser.get("duo", "ikey"),
        skey=parser.get("duo", "skey"),
        host=parser.get("duo", "host"),
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="0600 Duo INI credentials file")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Validate credentials against Duo")
    push = commands.add_parser("push", help="Send one diagnostic Push")
    push.add_argument("--user", required=True, help="Duo username, without @pam")
    push.add_argument("--confirm", action="store_true", help="Acknowledge sending a real Push")
    args = parser.parse_args(argv)

    if args.command == "push" and not args.confirm:
        parser.error("push requires --confirm to avoid accidental notifications")
    try:
        client = DuoPush(load_settings(args.config))
        if args.command == "check":
            client.check()
            print("Duo API credentials validated")
            return 0

        txid = client.start(args.user)
        print("Duo Push requested; awaiting response")
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            outcome = client.status(txid)
            if outcome["state"] == "approved":
                print("Duo Push approved (diagnostic only; no Proxmox login issued)")
                return 0
            if outcome["state"] == "denied":
                print("Duo Push denied")
                return 1
            time.sleep(min(2, max(0, deadline - time.monotonic())))
        print("Duo Push timed out")
        return 1
    except (Exception) as exc:
        # Do not disclose integration keys or raw exception messages in CLI logs.
        print(f"Duo diagnostic failed ({type(exc).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
