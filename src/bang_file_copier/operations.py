from __future__ import annotations

import re
import shutil
import subprocess
import platform
from pathlib import Path


def scan_eligible_files(source_path: Path) -> list[Path]:
    pattern = re.compile(r'^(?:!{1,3})[^!].*')
    matched_files = [item for item in source_path.iterdir() if item.is_file() and pattern.match(item.name)]
    return matched_files


def compute_rename_map(matched_files: list[Path], source_folder_name: str) -> list[dict]:
    rename_map = []
    for src in matched_files:
        clean_basename = src.name
        new_filename = f"{source_folder_name} {clean_basename}"
        rename_map.append({
            "src": src,
            "clean_basename": clean_basename,
            "new_filename": new_filename,
        })
    return rename_map


def plan_operations(rename_map: list[dict], destinations: list[str]) -> list[dict]:
    plan: list[dict] = []
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


def get_copy_strategy():
    if platform.system() == "Darwin":
        return copy_file
    return shutil.copy2


def copy_file(src: Path, dest: Path):
    # Ensure we pass string paths to subprocess; ditto preserves Finder tags/metadata on macOS
    subprocess.run(["ditto", str(src), str(dest)], check=True)


def execute_plan(plan: list[dict]):
    copies_performed = 0
    skips = 0
    errors = 0

    copy_method = get_copy_strategy()

    for p in plan:
        src = p["src"]
        dest_path = p["dest_path"]

        if p["action"] == "SKIP_ALREADY_EXISTS":
            skips += 1
            p["status"] = "SKIPPED_ALREADY_EXISTS"
            continue

        try:
            copy_method(src, dest_path)

            copies_performed += 1
            p["status"] = "SUCCESS"

        except Exception as e:
            errors += 1
            p["status"] = "ERROR"
            p["error"] = str(e)

    return copies_performed, skips, errors
