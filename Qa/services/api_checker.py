# services/api_checker.py
import requests
import time
from models.schemas import CheckResult


TIMEOUT = 10  # seconds


def check_api(url: str) -> list[CheckResult]:
    results = []

    # --- check 1: reachability + status code ---
    try:
        start = time.time()
        resp  = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        ms    = (time.time() - start) * 1000

        passed = resp.status_code < 400
        results.append(CheckResult(
            check_type  = "api",
            target      = url,
            passed      = passed,
            issue       = None if passed else f"HTTP {resp.status_code}",
            detail      = resp.text[:300] if not passed else None,
            duration_ms = round(ms, 2),
        ))

    except requests.exceptions.ConnectionError:
        results.append(CheckResult(
            check_type = "api",
            target     = url,
            passed     = False,
            issue      = "Connection refused — server may be down",
        ))
        return results  # no point continuing

    except requests.exceptions.Timeout:
        results.append(CheckResult(
            check_type = "api",
            target     = url,
            passed     = False,
            issue      = f"Timed out after {TIMEOUT}s",
        ))
        return results

    # --- check 2: response time threshold ---
    if ms > 3000:
        results.append(CheckResult(
            check_type  = "api",
            target      = url,
            passed      = False,
            issue       = f"Slow response: {round(ms)}ms (threshold: 3000ms)",
            duration_ms = round(ms, 2),
        ))

    # --- check 3: JSON validity (if content-type is json) ---
    ct = resp.headers.get("content-type", "")
    if "json" in ct:
        try:
            resp.json()
        except Exception:
            results.append(CheckResult(
                check_type = "api",
                target     = url,
                passed     = False,
                issue      = "Response claims JSON but body is invalid",
                detail     = resp.text[:200],
            ))

    return results