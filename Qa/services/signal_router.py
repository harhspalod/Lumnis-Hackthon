from models.schemas import IncomingSignal, SignalType, SignalReport, CheckResult
from services.api_checker import check_api
from services.ui_crawler import check_ui
from services.perf_checker import check_perf
from services.report_store import save_report
from services.notifier import notify

from datetime import datetime
import uuid
import time


# Which checkers run for each signal type
SIGNAL_MAP = {
    SignalType.slow_page: ["perf", "ui"],
    SignalType.api_error: ["api"],
    SignalType.broken_ui: ["ui"],
    SignalType.error_500: ["api"],
    SignalType.full_scan: ["api", "ui", "perf"],
}


def route_signal(signal: IncomingSignal) -> SignalReport:
    run_id = f"sig_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    checkers = SIGNAL_MAP.get(signal.signal_type, ["api", "ui", "perf"])
    results: list[CheckResult] = []

    # build the target URL
    base = signal.site_url.rstrip("/")
    page_url = f"{base}{signal.page}" if signal.page else base
    api_url = f"{base}{signal.endpoint}" if signal.endpoint else base

    # Run selected checks
    if "api" in checkers:
        results += check_api(api_url)

    if "ui" in checkers:
        results += check_ui(page_url)

    if "perf" in checkers:
        results += check_perf(page_url)

    # Analyze results
    issues = [r for r in results if not r.passed]

    summary = (
        f"{len(issues)} issue(s) found on {signal.page or signal.site_url}"
        if issues
        else f"All checks passed on {signal.page or signal.site_url}"
    )

    # Create report object
    report = SignalReport(
        run_id=run_id,
        site_url=signal.site_url,
        signal=signal,
        timestamp=datetime.now(),
        checks_run=checkers,
        results=results,
        total_issues=len(issues),
        summary=summary,
    )

    # ✅ Save report BEFORE returning
    save_report(report)
    notify(report)
    return report