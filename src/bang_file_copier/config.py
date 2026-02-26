from __future__ import annotations

import json
import sys
from pathlib import Path


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
