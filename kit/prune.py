#!/usr/bin/env python3
"""Delete dated media folders older than N days (default 7) under social/x and social/ig.
Folder names must start with YYYY-MM-DD. Run from the repo root, then commit.
  python3 kit/prune.py [days]
"""
import sys, shutil, pathlib, datetime as dt

days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
cut = dt.date.today() - dt.timedelta(days=days)
for base in ("social/x", "social/ig"):
    for d in sorted(pathlib.Path(base).glob("*")):
        try:
            day = dt.date.fromisoformat(d.name[:10])
        except ValueError:
            continue
        if d.is_dir() and day < cut:
            shutil.rmtree(d); print("pruned", d)
