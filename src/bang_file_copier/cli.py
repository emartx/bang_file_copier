from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import (
    load_config,
    validate_config,
    resolve_log_dir,
    load_or_create_config,
    add_destination_to_config,
    remove_destination_from_config,
    clear_destinations_in_config,
)
from .operations import (
    scan_eligible_files,
    compute_rename_map,
    plan_operations,
    execute_plan,
)
from .logging_utils import write_logs
from .ui import (
    _HAS_RICH,
    Console,
    Panel,
    print_intro,
    print_config_and_args,
    print_matches_and_renames,
    print_execution_results,
    print_summary,
    print_list_destinations,
    print_add_destination,
    print_remove_destination,
    print_clear_destinations,
    print_dry_run_plan,
)




def build_parser() -> argparse.ArgumentParser:
    epilog = (
        "Examples:\n"
        "  bang <folder>                    # scan given folder\n"
        "  bang --dry-run                   # show what would happen\n"
        "  bang --list-dests                # show configured destinations\n"
        "  bang --add-dest /path/to/dir     # add a new destination\n"
        "  bang --remove-dest /path/to/dir  # remove a destination\n"
        "  bang --clear-dests               # remove all destinations\n"
    )

    parser = argparse.ArgumentParser(
        prog="bang",
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

    # Destination management
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--list-dests",
        action="store_true",
        help="Show configured destinations and exit",
    )
    group.add_argument(
        "--add-dest",
        metavar="PATH",
        help="Add a new destination directory to the config and exit",
    )
    group.add_argument(
        "--remove-dest",
        metavar="PATH",
        help="Remove a destination directory from the config and exit",
    )
    group.add_argument(
        "--clear-dests",
        action="store_true",
        help="Remove all destinations from the config and exit",
    )

    return parser


def parse_args_and_config(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    source_path = Path(args.source).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()

    # Defer loading/validation of config to main; return paths for decision-making
    return args, source_path, config_path


def main(argv: list[str] | None = None) -> int:
    print_intro()
    args, source_path, config_path = parse_args_and_config(argv)
    if not source_path.exists() or not source_path.is_dir():
        print(f"ERROR: Source folder does not exist or is not a directory: {source_path}", file=sys.stderr)
        sys.exit(2)
    # Handle destination management flags first
    if getattr(args, "list_dests", False) or getattr(args, "add_dest", None) or getattr(
        args, "remove_dest", None
    ) or getattr(args, "clear_dests", False):
        cfg = load_or_create_config(config_path)

        # List
        if getattr(args, "list_dests", False):
            print_list_destinations(cfg.get("destinations", []))
            return 0

        # Add
        if getattr(args, "add_dest", None):
            add_destination_to_config(config_path, args.add_dest)
            print_add_destination(args.add_dest)
            return 0

        # Remove
        if getattr(args, "remove_dest", None):
            before = load_or_create_config(config_path).get("destinations", [])
            remove_destination_from_config(config_path, args.remove_dest)
            after = load_or_create_config(config_path).get("destinations", [])
            removed = len(before) != len(after)
            print_remove_destination(args.remove_dest, removed)
            return 0

        # Clear
        if getattr(args, "clear_dests", False):
            clear_destinations_in_config(config_path)
            print_clear_destinations()
            return 0

    # Normal run: load config and validate
    config = load_config(config_path)
    config = validate_config(config)
    log_dir = resolve_log_dir(config)
    print_config_and_args(source_path, args, config, log_dir)
    matched_files = scan_eligible_files(source_path)
    if not matched_files:
        if _HAS_RICH:
            console = Console()
            console.print(Panel("No eligible '!' files found. Exiting.", style="yellow", expand=False))
        else:
            print("No eligible '!' files found. Exiting.")
        print_summary([], [], 0, 0, 0, dry_run=args.dry_run)
        return 0  # Success, no files matched
    rename_map = compute_rename_map(matched_files, source_path.name)
    print_matches_and_renames(matched_files, rename_map)
    plan = plan_operations(rename_map, config["destinations"])
    if args.dry_run:
        print_dry_run_plan(plan)
        print_summary(plan, matched_files, 0, 0, 0, dry_run=True)
        return 0  # Dry-run is always success
    if _HAS_RICH:
        console = Console()
        console.print("[bold]Executing plan...[/bold]")
    else:
        print("\nExecuting plan:")
    copies_performed, skips, errors = execute_plan(plan)
    print_execution_results(plan)
    log_path = write_logs(plan, config, log_dir, source_path)
    print_summary(plan, matched_files, copies_performed, skips, errors, log_path=log_path, dry_run=False)
    if errors > 0:
        return 1  # Partial failure
    return 0  # Full success
