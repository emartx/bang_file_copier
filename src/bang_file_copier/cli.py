from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config, validate_config, resolve_log_dir
from .operations import (
    scan_eligible_files,
    compute_rename_map,
    plan_operations,
    execute_plan,
)
from .logging_utils import write_logs
from .ui import _HAS_RICH, Console, Panel, Table, box, pyfiglet


def print_intro():
    # Fallback to plain print when rich/pyfiglet unavailable
    if not _HAS_RICH:
        print("Bang File Copier")
        return

    console = Console()
    # Large ASCII title (pyfiglet may still fail at runtime)
    try:
        title = pyfiglet.figlet_format("Bang File Copier")
    except Exception:  # pragma: no cover - pyfiglet may fail at runtime
        title = "Bang File Copier"
    # Use a Panel sized to the content to avoid breaking figlet spacing
    console.print(Panel(title, style="bold green", expand=False))


def build_parser() -> argparse.ArgumentParser:
    epilog = (
        "Examples:\n"
        "  bang <folder>              # scan given folder\n"
        "  bang --dry-run             # show what would happen\n"
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

    return parser


def parse_args_and_config(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    source_path = Path(args.source).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    config = validate_config(config)
    log_dir = resolve_log_dir(config)
    return args, source_path, config, log_dir


def print_config_and_args(source_path, args, config, log_dir):
    if not _HAS_RICH:
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
        return

    console = Console()
    # Single table with sections separated by divider rows
    table = Table(show_header=False, expand=True, box=box.SIMPLE)
    table.add_column(justify="right", style="cyan", no_wrap=True, ratio=1)
    table.add_column(ratio=4)

    # Destinations section
    table.add_row("Destinations", "")
    for d in config["destinations"]:
        table.add_row("", str(Path(d).expanduser().resolve()))

    # Divider
    table.add_row("", "[dim]" + ("—" * 48) + "[/dim]")

    # Log directory
    table.add_row("Log dir", str(log_dir))

    # Divider
    table.add_row("", "[dim]" + ("—" * 48) + "[/dim]")

    # Arguments section
    table.add_row("Source", str(source_path))
    table.add_row("Config", str(Path(args.config).expanduser().resolve()))
    table.add_row("Dry-run", str(bool(args.dry_run)))

    console.print(Panel(table, title="Run Info"))


def print_matches_and_renames(matched_files, rename_map):
    if not _HAS_RICH:
        print(f"Found {len(matched_files)} eligible file(s):")
        for p in matched_files:
            print(f"  - {p.name}")
        print("\nComputed destination filenames:")
        for entry in rename_map:
            print(f"  {entry['src'].name} -> {entry['new_filename']}")
        return

    console = Console()
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    table.add_column("Original Filename", style="cyan")
    table.add_column("New Filename", style="green")

    for entry in rename_map:
        table.add_row(entry['src'].name, entry['new_filename'])

    console.print(Panel(table, title=f"Found {len(matched_files)} File(s) to Copy"))


def print_execution_results(plan):
    if not _HAS_RICH:
        for p in plan:
            src = p["src"]
            dest_path = p["dest_path"]
            if p["action"] == "SKIP_ALREADY_EXISTS":
                print(f"SKIPPED (exists): {dest_path}")
            elif p.get("status") == "SUCCESS":
                print(f"COPIED: {src} -> {dest_path}")
            elif p.get("status") == "ERROR":
                print(f"ERROR copying {src} -> {dest_path}: {p.get('error')}", file=sys.stderr)
        return

    console = Console()
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    table.add_column("Source", style="cyan")
    table.add_column("Destination", style="cyan")
    table.add_column("Status", style="yellow")

    for p in plan:
        src = p["src"]
        dest_path = p["dest_path"]
        status = p.get("status", "UNKNOWN")
        error_msg = p.get("error", "")

        if status == "SKIPPED_ALREADY_EXISTS":
            status_display = "[yellow]SKIPPED[/yellow]"
        elif status == "SUCCESS":
            status_display = "[green]SUCCESS[/green]"
        elif status == "ERROR":
            status_display = f"[red]ERROR[/red]: {error_msg}"
        else:
            status_display = status

        table.add_row(src.name, str(dest_path), status_display)

    console.print(Panel(table, title="Execution Results"))


def print_summary(plan, matched_files, copies_performed, skips, errors, log_path=None, dry_run=False):
    if not _HAS_RICH:
        print("\nSummary:")
        print(f"  Matched files: {len(matched_files)}")
        print(f"  Copies performed: {copies_performed}")
        print(f"  Skips (already exists): {skips}")
        print(f"  Errors: {errors}")
        if dry_run:
            print("  (dry-run: no files copied, no log created)")
        elif log_path:
            print(f"  Log file: {log_path}")
        return

    console = Console()
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column(justify="right", style="cyan", no_wrap=True, ratio=1)
    table.add_column(ratio=4)

    table.add_row("Matched files", str(len(matched_files)))
    table.add_row("Copies performed", str(copies_performed))
    table.add_row("Skips (already exists)", str(skips))
    table.add_row("Errors", str(errors))

    if dry_run:
        table.add_row("Mode", "[yellow]DRY-RUN[/yellow] (no files copied)")
    elif log_path:
        table.add_row("Log file", str(log_path))

    console.print(Panel(table, title="Summary"))


def main(argv: list[str] | None = None) -> int:
    print_intro()
    args, source_path, config, log_dir = parse_args_and_config(argv)
    if not source_path.exists() or not source_path.is_dir():
        print(f"ERROR: Source folder does not exist or is not a directory: {source_path}", file=sys.stderr)
        sys.exit(2)
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
        if _HAS_RICH:
            console = Console()
            table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
            table.add_column("Source", style="cyan")
            table.add_column("Destination", style="cyan")
            table.add_column("Action", style="yellow")
            
            for p in plan:
                action = p["action"]
                action_display = "[green]WOULD COPY[/green]" if action == "COPY" else "[yellow]WOULD SKIP[/yellow]"
                table.add_row(p['src'].name, str(p['dest_path']), action_display)
            
            console.print(Panel(table, title="Dry-run Plan (no files will be copied)"))
        else:
            print("\nDry-run plan (no files will be copied):")
            for p in plan:
                if p["action"] == "COPY":
                    print(f"WOULD COPY: {p['src']} -> {p['dest_path']}")
                else:
                    print(f"WOULD SKIP (exists): {p['dest_path']}")
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
