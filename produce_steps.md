# Bang File Copier — Step-by-step Implementation Plan

This plan follows the latest spec:

- Match files that start with **exactly 1, 2, or 3** exclamation marks: `!`, `!!`, `!!!`
- When renaming, **remove the leading exclamation marks** (1..3) from the original filename
- New name format: `<source_folder_name><space><filename_without_leading_bangs>`
- `destinations` (JSON) can contain **one or more** destination folders
- If **any** destination folder does not exist → **print error and exit** (do **not** create folders)
- If destination file already exists → **do not overwrite**, log `SKIPPED_ALREADY_EXISTS`
- `--dry-run` prints what would happen, does **not** copy and does **not** create logs
- Each non-dry-run execution creates a **new log file** named with timestamp
- `log_dir` comes from config; if missing, use a **hardcoded default**; log directory may be created if missing

---

## Step 0 — Project setup

1. Create a src folder in this project:

2. Suggested structure:
   - `bang_copier.py` — main CLI script  
   - `bang_copier_config.json` — sample config  
   - `README.md` — product documentation/spec  

---

## Step 1 — Build the CLI skeleton (argparse)

Implement CLI arguments using `argparse`:

- `source` (positional, optional)  
  - Default: `.` (current working directory)
- `--config` (optional)  
  - Default: `./bang_copier_config.json`
- `--dry-run` (flag)  
  - Default: `False`

Also:
- Resolve paths using `pathlib.Path(...).resolve()`
- Ensure `--help` prints useful usage examples

**Milestone:** running `python bang_copier.py --help` shows correct options.

---

## Step 2 — Load & validate JSON config (fail fast)

1. Load JSON config:
   - If config file is missing → print error → **exit code 2**
   - If JSON is invalid → print error → **exit code 2**

2. Validate `destinations`:
   - Must exist
   - Must be a list
   - Must be **non-empty**
   - Each entry must be a string path

3. Validate destination folders exist:
   - If **any** destination folder does not exist → print error → **exit code 2**
   - **Do not create** destinations in v1.

4. Resolve logging directory:
   - If `log_dir` exists in config → use it
   - Else → fallback to a hardcoded default (example: `~/bang-copier-logs`)
   - If the chosen `log_dir` does not exist → **create it** (allowed per spec)

**Milestone:** invalid config or missing destinations exits early with code 2.

---

## Step 3 — Validate the source folder

1. Resolve the source folder path.
2. Ensure it exists and is a directory:
   - If not → print error → **exit code 2**

**Milestone:** source path validation works reliably.

---

## Step 4 — Scan for eligible files (top-level only)

1. Iterate source directory **top-level only** (no recursion):
   - `for item in source_path.iterdir(): ...`

2. Keep only regular files:
   - `item.is_file()`

3. Filter names: start with **exactly** 1, 2, or 3 `!`:
   - Recommended regex: `r'^(?:!{1,3})[^!].*'`  
     (prevents matching `!!!!file` and also avoids empty names)

4. If no eligible files found:
   - Print an info message
   - Exit with **code 0**

**Milestone:** matches `!a`, `!!b`, `!!!c` but not `!!!!d`.

---

## Step 5 — Compute destination filenames (rename rules)

For each matched file:

1. Determine `source_folder_name`:
   - `source_folder_name = source_path.name`

2. Remove the leading `!` marks (only 1..3):
   - Recommended: `re.sub(r'^!{1,3}', '', original_name)`

3. Final destination filename:
   - `new_filename = f"{source_folder_name} {clean_basename}"`

**Milestone:** `vacation2026 !!img02.jpeg` becomes `vacation2026 img02.jpeg`.

---

## Step 6 — Plan operations (what to copy where)

For each eligible file and each destination directory:

1. Compute final destination path:
   - `dest_file_path = dest_dir / new_filename`

2. Decide action:
   - If `dest_file_path.exists()` → action = **SKIP_ALREADY_EXISTS**
   - Else → action = **COPY**

In `--dry-run`, print the planned actions, for example:
- `WOULD COPY: <src> -> <dest>`
- `WOULD SKIP (exists): <dest>`

**Milestone:** dry-run shows exact plan without filesystem writes.

---

## Step 7 — Copy execution (non-dry-run)

Only when not `--dry-run`:

1. For each planned COPY:
   - Use `shutil.copy2(src, dest_file_path)` (preserves timestamps/metadata)

2. For each planned SKIP:
   - Do nothing besides logging

3. Handle errors per file:
   - Catch exceptions (permission, IO errors)
   - Log `ERROR` and continue with other files/destinations

**Milestone:** copying works and errors do not crash the entire run.

---

## Step 8 — Logging: one log per execution

Only when not `--dry-run`:

1. Create a timestamped log filename:
   - `bang_copier_YYYY-MM-DD_HH-MM-SS.log`

2. Save under `log_dir` (from config or fallback).

3. Log entries should include:
   - Timestamp
   - Source directory
   - Destination directory
   - Original filename
   - New filename
   - Status: `SUCCESS`, `SKIPPED_ALREADY_EXISTS`, `ERROR`
   - Optional error message

**Milestone:** every run creates a new log file; dry-run creates none.

---

## Step 9 — Exit codes

Implement consistent exit behavior:

- `0` — Success (including “no matching files”)
- `1` — Partial failure (some copies failed, but tool completed)
- `2` — Fatal error (config invalid, source invalid, destination missing, etc.)

**Milestone:** CI-friendly exit codes.

---

## Step 10 — User-friendly output (summary)

At the end of execution print a summary:
- Number of matched files
- Number of copies performed
- Number of skips (already exists)
- Number of errors
- Log file path (only if created)

In `--dry-run`, print a dry-run summary (no log path).

**Milestone:** users can understand what happened at a glance.

---

## Step 11 — Manual test checklist

Create a sandbox folder with:
- `!a.txt`, `!!b.txt`, `!!!c.txt`, `!!!!d.txt` (should NOT match), `normal.txt`

Multiple destinations:
- Existing folders only
- Pre-create a destination file to test skip behavior

Test scenarios:
- Normal run (copies + logs)
- Dry-run (prints only)
- Missing config → exit 2
- Empty destinations → exit 2
- One missing destination folder → exit 2
- Permission error on one destination → log ERROR, exit 1

---

## Step 12 — Optional packaging improvements

- Add a shebang: `#!/usr/bin/env python3`
- Make executable: `chmod +x bang_copier.py`
- Add a wrapper/alias: `bang` → calls the script
- (Later) add `pyproject.toml` for installation as a proper CLI package

---

## Deliverables for v1

- `bang_copier.py` implementing the spec
- `bang_copier_config.json` sample config
- `README.md` with usage and behavior
- Logs produced per execution (non-dry-run)
