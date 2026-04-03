# proj1
first attempt

## Embedded Device Website Restrictor

A simple blocklist-based restrictor that updates `/etc/hosts` on Linux-based embedded devices.

### Usage

- `sudo ./restrictor.py --sync` (apply `blocklist.txt` to `/etc/hosts`)
- `sudo ./restrictor.py --disable` (remove blocklist entries)
- `./restrictor.py --list` (show configured domains)
- `./restrictor.py --show` (show active hosts entries)
- `sudo ./restrictor.py --block example.com` (add domain)
- `sudo ./restrictor.py --unblock example.com` (remove domain)

### Files

- `restrictor.py`: main script
- `blocklist.txt`: domain list to block (one domain per line)

