#!/usr/bin/env python3
"""
Bang File Copier — CLI entrypoint (argparse skeleton, Step 1)

Implements the CLI arguments required by Step 1 of the plan:
- positional `source` (optional, default `.`)
- `--config` (optional, default `./bang_copier_config.json`)
- `--dry-run` flag

This file currently only parses arguments and prints a short summary.
The full behavior will be implemented in subsequent steps.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    epilog = (
        "Examples:\n"
        "  bang_copier.py              # scan current dir\n"
        "  bang_copier.py /path/to/src  # scan given folder\n"
        "  bang_copier.py --dry-run     # show what would happen\n"
    )

    parser = argparse.ArgumentParser(
        prog="bang_copier.py",
        description="Scan a folder for files starting with '!' and copy them to destinations.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="Source directory to scan (default: current directory)",
    )

    parser.add_argument(
        "--config",
        default="./bang_copier_config.json",
        help="Path to JSON config file (default: ./bang_copier_config.json)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without copying or writing logs",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source).resolve()
    config_path = Path(args.config).resolve()

    print("Parsed arguments:")
    print("  source:", source_path)
    print("  config:", config_path)
    print("  dry_run:", bool(args.dry_run))

    # Step 1 only: do not perform filesystem changes; further steps will implement behavior.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
