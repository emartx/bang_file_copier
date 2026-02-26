from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import sys

from .ui import _HAS_RICH, Console


def write_logs(plan: list[dict], config: dict, log_dir: Path, source_path: Path) -> Path | None:
    now = datetime.now()
    run_id = now.strftime('%Y-%m-%d_%H-%M-%S')
    formats = config.get("log_formats", ["log"]) or ["log"]
    log_path: Path | None = None
    console = Console() if _HAS_RICH else None

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
            if console:
                console.print(f"[green]✓ Log written:[/green] {log_path}")
            else:
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
            if console:
                console.print(f"[green]✓ CSV written:[/green] {csv_path}")
            else:
                print(f"CSV written: {csv_path}")
        except Exception as e:
            print(f"ERROR: Failed to write CSV log file: {e}", file=sys.stderr)
    return log_path
