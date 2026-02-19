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
import shutil
from datetime import datetime
import csv

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

    # Optional: validate log_formats
    allowed_formats = {"csv", "log", "json"}
    if "log_formats" in config:
        lf = config["log_formats"]
        if not isinstance(lf, list):
            print("ERROR: 'log_formats' must be a list", file=sys.stderr)
            sys.exit(2)
        if not lf:
            print("ERROR: 'log_formats' list is empty", file=sys.stderr)
            sys.exit(2)
        for fmt in lf:
            if not isinstance(fmt, str):
                print(f"ERROR: 'log_formats' contains non-string: {fmt}", file=sys.stderr)
                sys.exit(2)
            if fmt not in allowed_formats:
                print(f"ERROR: Unsupported log format: {fmt}", file=sys.stderr)
                sys.exit(2)
    else:
        # default to plain log only
        config["log_formats"] = ["log"]

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

def parse_args_and_config(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    source_path = Path(args.source).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    config = validate_config(config)
    log_dir = resolve_log_dir(config)
    return args, source_path, config, log_dir

def scan_eligible_files(source_path):
    pattern = re.compile(r'^(?:!{1,3})[^!].*')
    matched_files = [item for item in source_path.iterdir() if item.is_file() and pattern.match(item.name)]
    return matched_files

def compute_rename_map(matched_files, source_folder_name):
    rename_map = []
    for src in matched_files:
        clean_basename = re.sub(r'^!{1,3}', '', src.name)
        new_filename = f"{source_folder_name} {clean_basename}"
        rename_map.append({
            "src": src,
            "clean_basename": clean_basename,
            "new_filename": new_filename,
        })
    return rename_map

def plan_operations(rename_map, destinations):
    plan = []
    for entry in rename_map:
        src = entry["src"]
        new_filename = entry["new_filename"]
        for dest_str in destinations:
            dest_dir = Path(dest_str).expanduser().resolve()
            dest_file_path = dest_dir / new_filename
            if dest_file_path.exists():
                action = "SKIP_ALREADY_EXISTS"
            else:
                action = "COPY"
            plan.append({
                "src": src,
                "dest_dir": dest_dir,
                "dest_path": dest_file_path,
                "action": action,
            })
    return plan

def execute_plan(plan):
    copies_performed = 0
    skips = 0
    errors = 0
    for p in plan:
        src = p["src"]
        dest_path = p["dest_path"]
        if p["action"] == "SKIP_ALREADY_EXISTS":
            skips += 1
            p["status"] = "SKIPPED_ALREADY_EXISTS"
            continue
        try:
            shutil.copy2(src, dest_path)
            copies_performed += 1
            p["status"] = "SUCCESS"
        except Exception as e:
            errors += 1
            p["status"] = "ERROR"
            p["error"] = str(e)
    return copies_performed, skips, errors

def print_summary(plan, matched_files, copies_performed, skips, errors):
    print("\nExecution summary:")
    print(f"  Matched files: {len(matched_files)}")
    print(f"  Copies performed: {copies_performed}")
    print(f"  Skips (already exists): {skips}")
    print(f"  Errors: {errors}")

def write_logs(plan, config, log_dir, source_path):
    now = datetime.now()
    run_id = now.strftime('%Y-%m-%d_%H-%M-%S')
    formats = config.get("log_formats", ["log"]) or ["log"]
    if "log" in formats:
        try:
            log_filename = f"bang_copier_{run_id}.log"
            log_path = log_dir / log_filename
            with open(log_path, "w", encoding="utf-8") as lf:
                lf.write(f"Bang File Copier run: {now.isoformat()}\n")
                lf.write(f"Source: {source_path}\n")
                lf.write("Destinations:\n")
                for d in config["destinations"]:
                    lf.write(f"  - {Path(d).expanduser().resolve()}\n")
                lf.write("\nEntries:\n")
                lf.write("timestamp | src | dest | original_filename | new_filename | status | message\n")
                for p in plan:
                    ts = now.isoformat()
                    src = p.get("src")
                    dest = p.get("dest_path")
                    orig = src.name if src is not None else ""
                    newfn = dest.name if dest is not None else ""
                    status = p.get("status", "UNKNOWN")
                    msg = p.get("error", "")
                    lf.write(f"{ts} | {src} | {dest} | {orig} | {newfn} | {status} | {msg}\n")
            print(f"Log written: {log_path}")
        except Exception as e:
            print(f"ERROR: Failed to write log file: {e}", file=sys.stderr)
    if "csv" in formats:
        try:
            csv_filename = f"bang_copier_{run_id}.csv"
            csv_path = log_dir / csv_filename
            with open(csv_path, "w", encoding="utf-8", newline="") as cf:
                writer = csv.writer(cf)
                writer.writerow([
                    "run_id",
                    "source",
                    "original_filename",
                    "new_filename",
                    "status",
                    "destination",
                    "timestamp",
                    "message"
                ])
                for p in plan:
                    ts = now.isoformat()
                    src = p.get("src")
                    dest = p.get("dest_path")
                    orig = src.name if src is not None else ""
                    newfn = dest.name if dest is not None else ""
                    status = p.get("status", "UNKNOWN")
                    msg = p.get("error", "")
                    writer.writerow([
                        run_id,
                        str(source_path),
                        orig,
                        newfn,
                        status,
                        str(dest),
                        ts,
                        msg
                    ])
            print(f"CSV written: {csv_path}")
        except Exception as e:
            print(f"ERROR: Failed to write CSV log file: {e}", file=sys.stderr)

def main(argv: list[str] | None = None) -> int:
    args, source_path, config, log_dir = parse_args_and_config(argv)
    if not source_path.exists() or not source_path.is_dir():
        print(f"ERROR: Source folder does not exist or is not a directory: {source_path}", file=sys.stderr)
        sys.exit(2)
    print("✓ Config loaded and validated")
    print("  Destinations:")
    for dest in config["destinations"]:
        print(f"    - {Path(dest).expanduser().resolve()}")
    print(f"  Log directory: {log_dir}")
    print()
    print("Parsed arguments:")
    print("  source:", source_path)
    print("  config:", Path(args.config).expanduser().resolve())
    print("  dry_run:", bool(args.dry_run))
    matched_files = scan_eligible_files(source_path)
    if not matched_files:
        print("No eligible '!' files found. Exiting.")
        return 0
    print(f"Found {len(matched_files)} eligible file(s):")
    for p in matched_files:
        print(f"  - {p.name}")
    rename_map = compute_rename_map(matched_files, source_path.name)
    print("\nComputed destination filenames:")
    for entry in rename_map:
        print(f"  {entry['src'].name} -> {entry['new_filename']}")
    plan = plan_operations(rename_map, config["destinations"])
    if args.dry_run:
        print("\nDry-run plan (no files will be copied):")
        for p in plan:
            if p["action"] == "COPY":
                print(f"WOULD COPY: {p['src']} -> {p['dest_path']}")
            else:
                print(f"WOULD SKIP (exists): {p['dest_path']}")
        return 0
    print("\nExecuting plan:")
    for p in plan:
        src = p["src"]
        dest_path = p["dest_path"]
        if p["action"] == "SKIP_ALREADY_EXISTS":
            print(f"SKIPPED (exists): {dest_path}")
            p["status"] = "SKIPPED_ALREADY_EXISTS"
            continue
        try:
            shutil.copy2(src, dest_path)
            print(f"COPIED: {src} -> {dest_path}")
            p["status"] = "SUCCESS"
        except Exception as e:
            print(f"ERROR copying {src} -> {dest_path}: {e}", file=sys.stderr)
            p["status"] = "ERROR"
            p["error"] = str(e)
    # Count results
    copies_performed = sum(1 for p in plan if p.get("status") == "SUCCESS")
    skips = sum(1 for p in plan if p.get("status") == "SKIPPED_ALREADY_EXISTS")
    errors = sum(1 for p in plan if p.get("status") == "ERROR")
    print_summary(plan, matched_files, copies_performed, skips, errors)
    write_logs(plan, config, log_dir, source_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
