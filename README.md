# Bang File Copier (CLI Tool)

---

## Overview

**Bang File Copier** is a lightweight command-line tool written in Python that scans a given directory for files whose names start with an exclamation mark (`!`), then copies those files into one or more predefined destination directories.
During the copy process, each file is renamed by prefixing it with the source folder’s name.

I use this tool for my personal photography workflow. After each shoot, I manually review the photos and mark the best ones by adding one or more exclamation marks (`!`) at the start of the filename. This tool then automates the next step by finding those marked files and copying them into the folders I use for retouching and publishing.

---

## Development Method

This project was developed in an iterative AI-assisted workflow:

1. I first explained my project goal to an AI tool.
2. The AI generated a more complete project explanation.
3. I reviewed and edited that explanation multiple times until it was ready for `README.md`.
4. I then asked the AI to generate a step-by-step development plan, which it saved in `produce_steps.md`.
5. In my free time, I asked the AI to implement each step progressively.
6. After each implementation step, I reviewed the generated code and edited it when needed.
7. Finally, I completed the final fixes and refinements, then updated the README sections.

Tools used in this process:
* VSCode (editing and project work)
* ChatGPT (project explanation and documentation drafting)
* Copilot CLI (code generation and implementation support)

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

### 1. Install the package

Install in editable mode from the project root:

```bash
pip install -e .
```

This installs the dependencies and exposes the `bang` CLI command from `[project.scripts]`.

### 2. Run the tool

Use the installed CLI:

```bash
bang [path] [--dry-run]
```

Or run it as a Python module:

```bash
python -m bang_file_copier [path] [--dry-run]
```

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

## Future Enhancements (Optional)

* `--delete-after-copy`
* `--only-ext .jpg,.png`
* `--recursive`
* `--remove-bang`
* `--json-log`
* `--stats` summary output
* `--undo-last-run`
