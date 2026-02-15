#!/usr/bin/env python3
"""
Bang File Copier — CLI entrypoint (initial stub)

This file is a minimal starter created as part of Step 0. It will be
expanded in Step 1 to implement the full argparse-based CLI.
"""
import sys


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Bang File Copier stub: no args provided. Run with --help after Step 1 is implemented.")
    else:
        print("Bang File Copier stub received args:", argv)


if __name__ == "__main__":
    main()
