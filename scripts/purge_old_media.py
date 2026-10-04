"""
purge_old_media.py - Retention policy enforcer for road damage media.

Deletes stored video frames and crops older than retention_days (default 30 days).
Runs in DRY-RUN mode by default. Use --apply to execute file deletions.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mkv", ".webp"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def purge_old_media(
    target_dir: str | Path,
    retention_days: int = 30,
    dry_run: bool = True,
    now_timestamp: float | None = None,
) -> dict[str, Any]:
    """
    Scans target_dir for media files with mtime older than retention_days.
    If dry_run is False, deletes them.
    """
    p = Path(target_dir)
    if not p.exists():
        logger.warning(f"Target directory {p} does not exist. Nothing to purge.")
        return {
            "target_dir": str(p),
            "retention_days": retention_days,
            "dry_run": dry_run,
            "files_scanned": 0,
            "files_purged": 0,
            "files_retained": 0,
            "purged_paths": [],
        }

    now = now_timestamp if now_timestamp is not None else time.time()
    cutoff_seconds = retention_days * 86400.0

    files_scanned = 0
    files_purged = 0
    files_retained = 0
    purged_paths: list[str] = []

    for root, _dirs, files in os.walk(p):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in MEDIA_EXTENSIONS:
                continue

            files_scanned += 1
            fpath = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fpath)
                age_seconds = now - mtime

                if age_seconds > cutoff_seconds:
                    purged_paths.append(fpath)
                    if not dry_run:
                        os.remove(fpath)
                        files_purged += 1
                        logger.info(f"Deleted expired media: {fpath}")
                    else:
                        files_purged += 1
                        logger.info(f"[DRY RUN] Would delete expired media ({age_seconds / 86400:.1f} days old): {fpath}")
                else:
                    files_retained += 1
            except OSError as e:
                logger.error(f"Error accessing {fpath}: {e}")

    # Clean up empty parent directories if in apply mode
    if not dry_run and files_purged > 0:
        for root, dirs, _files in os.walk(p, topdown=False):
            for d in dirs:
                dpath = os.path.join(root, d)
                try:
                    if not os.listdir(dpath):
                        os.rmdir(dpath)
                        logger.info(f"Removed empty directory: {dpath}")
                except OSError:
                    pass

    return {
        "target_dir": str(p),
        "retention_days": retention_days,
        "dry_run": dry_run,
        "files_scanned": files_scanned,
        "files_purged": files_purged,
        "files_retained": files_retained,
        "purged_paths": purged_paths,
    }


def main():
    parser = argparse.ArgumentParser(description="Purge stored media older than retention_days.")
    parser.add_argument(
        "--target-dir",
        type=str,
        default=os.environ.get("UPLOAD_DIR", "/tmp/road_damage_uploads"),
        help="Directory containing uploaded videos and crops",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Maximum allowed media age in days before purging (default: 30)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Execute deletions. Defaults to DRY-RUN without this flag.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MEDIA RETENTION ENFORCER (Phase 9)")
    print("=" * 60)
    print(f"Target Directory : {args.target_dir}")
    print(f"Retention Window : {args.retention_days} days")
    print(f"Execution Mode   : {'APPLY (Deletions Active)' if args.apply else 'DRY RUN (Preview Only)'}")
    print("=" * 60)

    res = purge_old_media(args.target_dir, retention_days=args.retention_days, dry_run=not args.apply)

    print("\nSummary:")
    print(f"  Files Scanned  : {res['files_scanned']}")
    print(f"  Files Purged   : {res['files_purged']}")
    print(f"  Files Retained : {res['files_retained']}")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
