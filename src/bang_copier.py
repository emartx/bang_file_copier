#!/usr/bin/env python3
"""
Bang File Copier — CLI entrypoint (Steps 1–2)

Step 1: argparse CLI with source, --config, --dry-run
Step 2: Load & validate JSON config (fail fast)
  - Load config file (exit 2 if missing or invalid JSON)
  - Validate destinations (must exist, non-empty list of strings)
  - Validate destination folders exist (exit 2 if not)
  - Resolve log_dir (create if missing)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import re


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
        default=str(Path.home() / ".config" / "bang-copier" / "config.json"),
        help="Path to JSON config file (default: ~/.config/bang-copier/config.json)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without copying or writing logs",
    )

    return parser


def load_config(config_path: Path) -> dict:
    """Load and validate JSON config file. Exit with code 2 on failure."""
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: Failed to read config file: {e}", file=sys.stderr)
        sys.exit(2)

    return config


def validate_config(config: dict) -> dict:
    """Validate config structure and destination folders. Exit with code 2 on failure."""
    # Check destinations key exists
    if "destinations" not in config:
        print("ERROR: Config missing 'destinations' key", file=sys.stderr)
        sys.exit(2)

    destinations = config["destinations"]

    # Check it's a list
    if not isinstance(destinations, list):
        print("ERROR: 'destinations' must be a list", file=sys.stderr)
        sys.exit(2)

    # Check it's non-empty
    if not destinations:
        print("ERROR: 'destinations' list is empty", file=sys.stderr)
        sys.exit(2)

    # Check each entry is a string
    for dest in destinations:
        if not isinstance(dest, str):
            print(f"ERROR: 'destinations' contains non-string: {dest}", file=sys.stderr)
            sys.exit(2)

    # Validate destination folders exist
    for dest_str in destinations:
        dest_path = Path(dest_str).expanduser().resolve()
        if not dest_path.exists():
            print(f"ERROR: Destination folder does not exist: {dest_path}", file=sys.stderr)
            sys.exit(2)
        if not dest_path.is_dir():
            print(f"ERROR: Destination is not a directory: {dest_path}", file=sys.stderr)
            sys.exit(2)

    return config


def resolve_log_dir(config: dict) -> Path:
    """Resolve log directory from config or fallback. Create if missing."""
    if "log_dir" in config and config["log_dir"]:
        log_dir = Path(config["log_dir"]).expanduser().resolve()
    else:
        # Hardcoded fallback default
        log_dir = Path.home() / "bang-copier-logs"

    # Create if missing
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source).expanduser().resolve()

    # Step 3: Validate source folder
    if not source_path.exists() or not source_path.is_dir():
        print(f"ERROR: Source folder does not exist or is not a directory: {source_path}", file=sys.stderr)
        sys.exit(2)

    config_path = Path(args.config).expanduser().resolve()

    # Step 2: Load and validate config
    config = load_config(config_path)
    config = validate_config(config)
    log_dir = resolve_log_dir(config)

    print("✓ Config loaded and validated")
    print("  Destinations:")
    for dest in config["destinations"]:
        print(f"    - {Path(dest).expanduser().resolve()}")
    print(f"  Log directory: {log_dir}")
    print()
    print("Parsed arguments:")
    print("  source:", source_path)
    print("  config:", config_path)
    print("  dry_run:", bool(args.dry_run))

    # Step 4: Scan for eligible files (top-level only)
    # Match exactly 1..3 leading '!' followed by a non-'!' character
    pattern = re.compile(r'^(?:!{1,3})[^!].*')
    matched_files: list[Path] = []
    for item in source_path.iterdir():
        if not item.is_file():
            continue
        if pattern.match(item.name):
            matched_files.append(item)

    if not matched_files:
        print("No eligible '!' files found. Exiting.")
        return 0

    print(f"Found {len(matched_files)} eligible file(s):")
    for p in matched_files:
        print(f"  - {p.name}")

    # For now stop here; subsequent steps will compute dest names and copy.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
