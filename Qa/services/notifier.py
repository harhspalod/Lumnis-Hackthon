# services/notifier.py
import json
import logging
import os
import time
import urllib.request
import urllib.error
from models.schemas import SignalReport

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL  = os.environ.get("SLACK_WEBHOOK_URL", "")
NOTIFY_WEBHOOK_URL = os.environ.get("NOTIFY_WEBHOOK_URL", "")  # your review system callback
MAX_RETRIES        = 3
RETRY_DELAY_S      = 2


def notify(report: SignalReport) -> dict:
    """
    Send report to all configured channels.
    Never raises — always returns a status dict.
    """
    results = {}

    # always log to console
    _log_to_console(report)
    results["console"] = "ok"

    # send to Slack if configured
    if SLACK_WEBHOOK_URL:
        results["slack"] = _send_slack(report)

    # send back to review system if configured
    if NOTIFY_WEBHOOK_URL:
        results["webhook"] = _send_webhook(report)

    return results


# ── Console ───────────────────────────────────────────────────────────────────

def _log_to_console(report: SignalReport):
    status = "ISSUES FOUND" if report.total_issues > 0 else "ALL CLEAR"
    logger.info(f"[QA {status}] {report.run_id} | {report.summary}")
    for r in report.results:
        icon = "FAIL" if not r.passed else "PASS"
        logger.info(f"  [{icon}] {r.check_type.upper()} {r.target} {r.issue or ''}")


# ── Slack ─────────────────────────────────────────────────────────────────────

def _send_slack(report: SignalReport) -> str:
    color   = "#E24B4A" if report.total_issues > 0 else "#639922"
    icon    = ":warning:" if report.total_issues > 0 else ":white_check_mark:"
    issues  = [r for r in report.results if not r.passed]

    # build issue lines
    lines = ""
    for r in issues[:5]:  # cap at 5 to keep slack message clean
        lines += f"• `{r.check_type.upper()}` {r.target}\n  {r.issue}\n"
    if not lines:
        lines = "No issues found."

    payload = {
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{icon} QA Report — {report.site_url}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Run ID*\n`{report.run_id}`"},
                        {"type": "mrkdwn", "text": f"*Signal*\n`{report.signal.signal_type}`"},
                        {"type": "mrkdwn", "text": f"*Issues*\n`{report.total_issues}`"},
                        {"type": "mrkdwn", "text": f"*Checks*\n`{', '.join(report.checks_run)}`"},
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Details*\n{lines}"}
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"Summary: {report.summary}"}]
                }
            ]
        }]
    }

    return _post_json(SLACK_WEBHOOK_URL, payload, "slack")


# ── Generic webhook callback ──────────────────────────────────────────────────

def _send_webhook(report: SignalReport) -> str:
    """
    POST the full report back to your review system.
    This closes the loop — signal came in, result goes back.
    """
    payload = {
        "run_id":       report.run_id,
        "site_url":     report.site_url,
        "timestamp":    report.timestamp.isoformat(),
        "signal_type":  report.signal.signal_type,
        "total_issues": report.total_issues,
        "summary":      report.summary,
        "checks_run":   report.checks_run,
        "issues": [
            {
                "check_type": r.check_type,
                "target":     r.target,
                "issue":      r.issue,
                "detail":     r.detail,
                "duration_ms": r.duration_ms,
            }
            for r in report.results if not r.passed
        ],
    }

    return _post_json(NOTIFY_WEBHOOK_URL, payload, "webhook")


# ── HTTP helper with retries ──────────────────────────────────────────────────

def _post_json(url: str, payload: dict, channel: str) -> str:
    """
    POST JSON to a URL with retry logic.
    Returns "ok" or an error string — never raises.
    """
    data = json.dumps(payload).encode()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                data    = data,
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent":   "QA-Automation/1.0",
                },
                method = "POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status < 300:
                    logger.info(f"[{channel}] Notification sent (attempt {attempt})")
                    return "ok"
                else:
                    logger.warning(f"[{channel}] Non-2xx response: {resp.status}")
                    return f"error: HTTP {resp.status}"

        except urllib.error.HTTPError as e:
            logger.warning(f"[{channel}] HTTP error attempt {attempt}: {e.code}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)

        except urllib.error.URLError as e:
            logger.warning(f"[{channel}] URL error attempt {attempt}: {e.reason}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)

        except Exception as e:
            logger.error(f"[{channel}] Unexpected error attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)

    return f"error: failed after {MAX_RETRIES} attempts"