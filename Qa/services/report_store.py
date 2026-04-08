# services/report_store.py
import json
import os
import fcntl
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from models.schemas import SignalReport

logger    = logging.getLogger(__name__)
STORE_DIR = Path(os.environ.get("QA_STORE_DIR", "qa_reports"))


def _ensure_dir():
    try:
        STORE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.critical(f"Cannot create report store dir {STORE_DIR}: {e}")
        raise


def save_report(report: SignalReport) -> bool:
    """
    Persist a SignalReport to disk.
    Uses file locking so concurrent saves never corrupt each other.
    Returns True on success, False on failure — never raises.
    """
    _ensure_dir()
    path = STORE_DIR / f"{report.run_id}.json"

    try:
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)           # exclusive lock
            f.write(report.model_dump_json(indent=2))
            f.flush()
            os.fsync(f.fileno())                      # flush to disk
            fcntl.flock(f, fcntl.LOCK_UN)

        tmp_path.replace(path)                        # atomic rename
        logger.info(f"Report saved: {report.run_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to save report {report.run_id}: {e}")
        # clean up tmp if it exists
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def load_report(run_id: str) -> Optional[SignalReport]:
    """
    Load a report by run_id.
    Returns None if not found or file is corrupted — never raises.
    """
    _ensure_dir()

    # sanitize run_id — prevent path traversal attacks
    safe_id = Path(run_id).name
    if safe_id != run_id or ".." in run_id:
        logger.warning(f"Suspicious run_id blocked: {run_id}")
        return None

    path = STORE_DIR / f"{safe_id}.json"

    if not path.exists():
        logger.debug(f"Report not found: {run_id}")
        return None

    try:
        with open(path) as f:
            fcntl.flock(f, fcntl.LOCK_SH)            # shared read lock
            raw = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)

        if not raw.strip():
            logger.warning(f"Empty report file: {run_id}")
            return None

        return SignalReport(**json.loads(raw))

    except json.JSONDecodeError as e:
        logger.error(f"Corrupted report file {run_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load report {run_id}: {e}")
        return None


def list_reports(limit: int = 50, offset: int = 0) -> list[dict]:
    """
    List all saved reports, newest first.
    Returns lightweight metadata — not full reports.
    """
    _ensure_dir()

    try:
        files = sorted(
            STORE_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return []

    results = []
    for f in files[offset: offset + limit]:
        try:
            with open(f) as fh:
                fcntl.flock(fh, fcntl.LOCK_SH)
                raw = json.loads(fh.read())
                fcntl.flock(fh, fcntl.LOCK_UN)

            results.append({
                "run_id":       raw.get("run_id"),
                "site_url":     raw.get("site_url"),
                "timestamp":    raw.get("timestamp"),
                "total_issues": raw.get("total_issues", 0),
                "summary":      raw.get("summary"),
                "checks_run":   raw.get("checks_run", []),
                "signal_type":  raw.get("signal", {}).get("signal_type"),
            })
        except Exception as e:
            logger.warning(f"Skipping unreadable report {f.name}: {e}")
            continue

    return results


def delete_report(run_id: str) -> bool:
    """
    Delete a report by run_id.
    Returns True if deleted, False if not found or error.
    """
    safe_id = Path(run_id).name
    if safe_id != run_id or ".." in run_id:
        logger.warning(f"Suspicious delete blocked: {run_id}")
        return False

    path = STORE_DIR / f"{safe_id}.json"

    try:
        path.unlink(missing_ok=True)
        logger.info(f"Report deleted: {run_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete report {run_id}: {e}")
        return False


def purge_old_reports(keep_days: int = 30) -> int:
    """
    Delete reports older than keep_days.
    Returns number of files deleted.
    Call this from a cron or startup cleanup.
    """
    _ensure_dir()
    cutoff = datetime.now().timestamp() - (keep_days * 86400)
    deleted = 0

    for f in STORE_DIR.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
                logger.info(f"Purged old report: {f.name}")
        except Exception as e:
            logger.warning(f"Could not purge {f.name}: {e}")

    logger.info(f"Purge complete: {deleted} reports removed")
    return deleted