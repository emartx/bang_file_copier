from __future__ import annotations

# Optional pretty output dependencies.  Any failure means we fall back to plain text.
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    import pyfiglet
    _HAS_RICH = True
except Exception:  # pragma: no cover - noncritical
    _HAS_RICH = False
    Console = Panel = Table = box = pyfiglet = None


# Printing helpers. They rely on the rich/ui globals
# above but are kept here to keep CLI logic focused.

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


def print_list_destinations(destinations):
    """Display all configured destinations."""
    if not _HAS_RICH:
        print("Configured destinations:")
        for d in destinations:
            print(f"  - {Path(d).expanduser().resolve()}")
    else:
        console = Console()
        table = Table(show_header=False, expand=True, box=box.SIMPLE)
        table.add_column(justify="right", style="cyan", no_wrap=True, ratio=1)
        table.add_column(ratio=4)
        table.add_row("Destinations", "")
        for d in destinations:
            table.add_row("", str(Path(d).expanduser().resolve()))
        console.print(Panel(table, title="Configured Destinations"))


def print_add_destination(dest):
    """Display confirmation of added destination."""
    resolved = Path(dest).expanduser().resolve()
    if not _HAS_RICH:
        print(f"Added destination: {resolved}")
    else:
        console = Console()
        console.print(Panel(f"Added destination: {resolved}", style="green"))


def print_remove_destination(dest, was_removed):
    """Display result of destination removal attempt."""
    resolved = Path(dest).expanduser().resolve()
    if not _HAS_RICH:
        if was_removed:
            print(f"Removed destination: {resolved}")
        else:
            print(f"Destination not found: {resolved}")
    else:
        console = Console()
        msg = (
            f"Removed destination: {resolved}"
            if was_removed
            else f"Destination not found: {resolved}"
        )
        console.print(Panel(msg, style="green" if was_removed else "yellow"))


def print_clear_destinations():
    """Display confirmation of destinations cleared."""
    if not _HAS_RICH:
        print("All destinations removed from config")
    else:
        console = Console()
        console.print(Panel("All destinations removed from config", style="yellow"))


def print_dry_run_plan(plan):
    """Display the dry-run plan without executing it."""
    if not _HAS_RICH:
        print("\nDry-run plan (no files will be copied):")
        for p in plan:
            if p["action"] == "COPY":
                print(f"WOULD COPY: {p['src']} -> {p['dest_path']}")
            else:
                print(f"WOULD SKIP (exists): {p['dest_path']}")
    else:
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
