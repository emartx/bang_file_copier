# Bang File Copier (CLI Tool)

---

## Overview

**Bang File Copier** is a lightweight command-line tool written in Python that scans a given directory for files whose names start with an exclamation mark (`!`), then copies those files into one or more predefined destination directories.
During the copy process, each file is renamed by prefixing it with the source folder’s name.

I use this tool for my personal photography workflow. After each shoot, I manually review the photos and mark the best ones by adding one or more exclamation marks (`!`) at the start of the filename. This tool then automates the next step by finding those marked files and copying them into the folders I use for retouching and publishing.

---

## Dependencies

### Required
* Python 3.7+

### Optional
* **`rich`** – Pretty console output with tables, panels, and styled text
* **`pyfiglet`** – ASCII art text rendering (used for the intro banner)

Both optional dependencies serve UI enhancement only. The tool will fall back to plain text output if they are unavailable.

---

## Packaging & Installation

### 1. Shebang
The script already starts with:

  #!/usr/bin/env python3

### 2. Make Executable
To make the script directly runnable:

  chmod +x src/bang_copier.py

### 3. Install Optional Dependencies
To get pretty formatted output:

  pip install rich pyfiglet

Or install with the editable package (if `pyproject.toml` includes them):

  pip install -e .

### 4. Command Alias
Add a shell alias to your `.bashrc`/`.zshrc` (optional):

  alias bang='python3 /full/path/to/src/bang_copier.py'

You can also run the package directly with the interpreter:

```bash
python -m bang_file_copier [path] [--dry-run]
```
This behaves identically to the installed ``bang`` command.
### 5. Install as CLI (optional)
With `pyproject.toml` present, install in editable mode:

  pip install -e .

This provides a `bang` command globally (if `[project.scripts]` is set).

---

## Core Features

### 1. Folder Scanning

* Accepts a target directory path as input (either explicitly or defaults to the current working directory).
* Scans only the **top-level** of the directory (no recursion in v1).
* Identifies files that:

  * Are regular files (not directories)
  * Have names starting with `!` (e.g., `!photo1.jpg`, `!note.txt`)

---

### 2. File Copying to Two Destinations

* Copies all matched files into **two destination directories**.
* Destination directories are:

  * Read from a configuration file (e.g., `config.json` or `config.yaml`)
  * Or fallback to hardcoded defaults if config is missing.

---

### 3. File Renaming Strategy

* Each copied file is renamed using the following format:

  ```
  <source_folder_name>_<original_filename>
  ```

* Example:

  ```
  Source folder:  vacation2026
  Original file: !img01.jpg
  New filename:  vacation2026_!img01.jpg
  ```

* (Optional future extension: remove `!` from filename after prefixing.)

---

### 4. Dry-Run Mode

* A `--dry-run` flag simulates all operations without copying any files.
* In dry-run mode:

  * The tool prints:

    * Which files would be copied
    * Their computed destination paths
    * Their renamed filenames
  * No filesystem writes occur.
  * No log entries are written (unless explicitly enabled with a flag like `--log-dry-run`).

---

### 5. Logging System

#### 5.1 Log File

* All real (non-dry-run) operations are recorded in a log file, e.g.:

  ```
  bang_copier.log
  ```

* Each log entry includes:

  * Timestamp
  * Source directory path
  * Destination directory path
  * Original filename
  * New filename
  * Operation status (SUCCESS / SKIPPED / ERROR)
  * Optional error message

* Example log entry:

  ```
  [2026-01-25 20:42:11]
  SOURCE: /photos/vacation2026
  DEST:   /backup/photos
  FILE:   !img01.jpg -> vacation2026_!img01.jpg
  STATUS: SUCCESS
  ```

---

### 6. Destination Directories from Log File

#### 6.1 Purpose

* The tool can optionally **reuse previously used destination directories** by reading them from the log file.
* This allows:

  * Zero-config re-runs
  * Consistency across sessions
  * Easy recovery after interruptions

#### 6.2 Behavior

* When invoked with a flag like `--use-last-dests`:

  * The tool:

    1. Reads the log file
    2. Extracts the last two destination paths used
    3. Uses them as the active destination directories for the current run
* If:

  * The log file does not exist
  * Or fewer than two destinations are found
    → The tool falls back to config file values or hardcoded defaults.

---

## CLI Interface

### Basic Usage

```bash
bang .
```

Scans the current directory and copies all `!`-prefixed files.

---

### With Explicit Folder

```bash
bang /path/to/source/folder
```

---

### Dry Run

```bash
bang . --dry-run
```

---

### Use Last Destinations from Log

```bash
bang . --use-last-dests
```

---

### Custom Config File

```bash
bang . --config ./my_config.json
```

---

### Manage Destinations

The following options allow you to inspect or mutate the list of configured destinations without performing a copy run:

```bash
bang --list-dests                 # display current destinations
bang --add-dest /path/to/dir      # append a destination
bang --remove-dest /path/to/dir   # remove a specific destination
bang --clear-dests                # delete all destinations
```

(These flags are mutually exclusive and exit immediately after performing the action.)

---

## Configuration File (Example: config.json)

```json
{
  "destinations": [
    "/mnt/backup/photos",
    "/mnt/cloud/photos"
  ],
  "log_file": "./bang_copier.log",
  "remove_bang_prefix": false,
  "scan_recursively": false
}
```

---

## Error Handling Rules

| Scenario                        | Behavior                               |
| ------------------------------- | -------------------------------------- |
| Source folder does not exist    | Exit with error message                |
| No `!` files found              | Print info message and exit gracefully |
| Destination folder missing      | Auto-create (optional flag-controlled) |
| Destination file already exists | Skip + log as SKIPPED                  |
| Permission denied               | Log ERROR and continue with next file  |
| Invalid config file             | Print error and fall back to defaults  |

---

## Exit Codes

| Code | Meaning                        |
| ---- | ------------------------------ |
| 0    | All operations successful      |
| 1    | Partial failure (some errors)  |
| 2    | Fatal error (nothing executed) |

---

## Non-Goals (v1)

* GUI interface
* Recursive directory scanning
* File deletion after copy
* File type filtering
* Parallel copy

(These can be added later if needed.)

---

## Design Philosophy

* Minimal core dependencies (standard library by default)
* Optional enhancements for prettier output (`rich`, `pyfiglet`)
* Graceful fallback to plain text when optional deps unavailable
* Human-readable logs
* Predictable behavior
* Explicit flags over magic behavior
* Safe-by-default (no destructive operations)

---

## Future Enhancements (Optional)

* `--delete-after-copy`
* `--only-ext .jpg,.png`
* `--recursive`
* `--remove-bang`
* `--json-log`
* `--stats` summary output
* `--undo-last-run`
