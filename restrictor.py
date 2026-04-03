#!/usr/bin/env python3
"""Embedded device website blocklist restrictor.

Usage examples:
  sudo ./restrictor.py --sync
  sudo ./restrictor.py --block example.com
  sudo ./restrictor.py --unblock example.com
  sudo ./restrictor.py --enable
  sudo ./restrictor.py --disable
  ./restrictor.py --list
"""

import argparse
import os
import sys
from pathlib import Path

BLOCK_START = "# BEGIN EMBEDDED BLOCKLIST"
BLOCK_END = "# END EMBEDDED BLOCKLIST"
DEFAULT_HOSTS = "/etc/hosts"
DEFAULT_BLOCKLIST = "blocklist.txt"
REDIRECT = "0.0.0.0"

def load_blocklist(path: Path):
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    return sorted(set(lines), key=str.lower)


def save_blocklist(path: Path, entries):
    path.write_text("""# Blocklist for embedded device restrictor
# One domain per line
""" + "\n".join(entries) + "\n", encoding="utf-8")


def read_hosts(path: Path):
    return path.read_text(encoding="utf-8").splitlines()


def write_hosts(path: Path, lines):
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def inject_blocklist_into_hosts(hosts_path: Path, domains):
    hosts = read_hosts(hosts_path)
    start = next((i for i, l in enumerate(hosts) if l.strip() == BLOCK_START), None)
    end = next((i for i, l in enumerate(hosts) if l.strip() == BLOCK_END), None)

    if start is not None and end is not None and end > start:
        # remove existing block segment
        hosts = hosts[:start] + hosts[end + 1 :]

    if not domains:
        return hosts

    new_block = [BLOCK_START]
    for d in domains:
        new_block.append(f"{REDIRECT} {d}")
        if d.startswith("www."):
            continue
        new_block.append(f"{REDIRECT} www.{d}")
    new_block.append(BLOCK_END)

    # Add to end, preserving final newline semantics
    if hosts and hosts[-1] == "":
        hosts = hosts[:-1]

    hosts += ["", *new_block]
    return hosts


def remove_blocklist_from_hosts(hosts_path: Path):
    hosts = read_hosts(hosts_path)
    start = next((i for i, l in enumerate(hosts) if l.strip() == BLOCK_START), None)
    end = next((i for i, l in enumerate(hosts) if l.strip() == BLOCK_END), None)
    if start is None or end is None or end < start:
        return hosts
    return hosts[:start] + hosts[end + 1 :]


def ensure_root():
    if os.geteuid() != 0:
        print("Error: this script requires root permissions for hosts file modifications.")
        print("Use sudo or run as root.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Embedded device website restrictor")
    parser.add_argument("--hosts", default=DEFAULT_HOSTS, help="Hosts file path")
    parser.add_argument("--blocklist", default=DEFAULT_BLOCKLIST, help="Blocklist file path")
    parser.add_argument("--list", action="store_true", help="Show blocklist domains")
    parser.add_argument("--show", action="store_true", help="Show active hosts block entries")
    parser.add_argument("--sync", action="store_true", help="Apply blocklist to hosts file")
    parser.add_argument("--enable", action="store_true", help="Enable blocking (alias for sync)")
    parser.add_argument("--disable", action="store_true", help="Remove blocking entries from hosts")
    parser.add_argument("--block", help="Add domain to blocklist")
    parser.add_argument("--unblock", help="Remove domain from blocklist")
    args = parser.parse_args()

    blocklist_path = Path(args.blocklist)
    hosts_path = Path(args.hosts)
    domains = load_blocklist(blocklist_path)

    if args.block:
        d = args.block.strip().lower()
        if d and d not in domains:
            domains.append(d)
            domains.sort(key=str.lower)
            save_blocklist(blocklist_path, domains)
            print(f"Added block domain: {d}")
        else:
            print(f"Domain already blocked or invalid: {d}")

    if args.unblock:
        d = args.unblock.strip().lower()
        if d in domains:
            domains = [x for x in domains if x != d]
            save_blocklist(blocklist_path, domains)
            print(f"Removed block domain: {d}")
        else:
            print(f"Domain not found in blocklist: {d}")

    if args.list:
        print("Blocklist domains:")
        for d in domains:
            print(f"- {d}")

    if args.show:
        hosts = read_hosts(hosts_path)
        start = next((i for i, l in enumerate(hosts) if l.strip() == BLOCK_START), None)
        end = next((i for i, l in enumerate(hosts) if l.strip() == BLOCK_END), None)
        if start is not None and end is not None and end > start:
            print("Active blocking entries in hosts:")
            for l in hosts[start : end + 1]:
                print(l)
        else:
            print("No active embedded blocklist section found in hosts file.")

    if args.sync or args.enable:
        ensure_root()
        new_hosts = inject_blocklist_into_hosts(hosts_path, domains)
        write_hosts(hosts_path, new_hosts)
        print(f"Blocklist applied to {hosts_path}")

    if args.disable:
        ensure_root()
        new_hosts = remove_blocklist_from_hosts(hosts_path)
        write_hosts(hosts_path, new_hosts)
        print(f"Blocking removed from {hosts_path}")

    if not any([args.list, args.show, args.sync, args.enable, args.disable, args.block, args.unblock]):
        parser.print_help()


if __name__ == "__main__":
    main()
