# services/perf_checker.py
import requests
import time
from bs4 import BeautifulSoup
from models.schemas import CheckResult

SLOW_PAGE_MS    = 3000
SLOW_TTFB_MS    = 800
SLOW_ASSET_MS   = 1500
TIMEOUT         = 15


def check_perf(url: str) -> list[CheckResult]:
    results = []

    # --- TTFB + full page load ---
    try:
        start    = time.time()
        resp     = requests.get(url, timeout=TIMEOUT, stream=True)
        ttfb_ms  = (time.time() - start) * 1000

        # consume full body
        body = b""
        for chunk in resp.iter_content(chunk_size=8192):
            body += chunk
        total_ms = (time.time() - start) * 1000

        # TTFB check
        if ttfb_ms > SLOW_TTFB_MS:
            results.append(CheckResult(
                check_type  = "perf",
                target      = url,
                passed      = False,
                issue       = f"Slow TTFB: {round(ttfb_ms)}ms (threshold: {SLOW_TTFB_MS}ms)",
                duration_ms = round(ttfb_ms, 2),
            ))

        # total load time check
        if total_ms > SLOW_PAGE_MS:
            results.append(CheckResult(
                check_type  = "perf",
                target      = url,
                passed      = False,
                issue       = f"Slow page load: {round(total_ms)}ms (threshold: {SLOW_PAGE_MS}ms)",
                duration_ms = round(total_ms, 2),
            ))
        else:
            results.append(CheckResult(
                check_type  = "perf",
                target      = url,
                passed      = True,
                issue       = None,
                duration_ms = round(total_ms, 2),
            ))

        # --- check asset load times from HTML ---
        results += _check_assets(url, body)

    except Exception as e:
        results.append(CheckResult(
            check_type = "perf",
            target     = url,
            passed     = False,
            issue      = f"Perf check failed: {str(e)}",
        ))

    return results


def _check_assets(base_url: str, html_body: bytes) -> list[CheckResult]:
    results = []
    try:
        soup   = BeautifulSoup(html_body, "html.parser")
        assets = []

        # collect JS and CSS asset URLs
        for tag in soup.find_all("script", src=True):
            assets.append(tag["src"])
        for tag in soup.find_all("link", rel="stylesheet"):
            assets.append(tag.get("href", ""))

        base = base_url.rstrip("/")
        for asset in assets[:10]:  # cap at 10 to keep it fast
            if not asset:
                continue
            full_url = asset if asset.startswith("http") else f"{base}{asset}"
            try:
                start = time.time()
                requests.get(full_url, timeout=5)
                ms = (time.time() - start) * 1000
                if ms > SLOW_ASSET_MS:
                    results.append(CheckResult(
                        check_type  = "perf",
                        target      = full_url,
                        passed      = False,
                        issue       = f"Slow asset: {round(ms)}ms",
                        duration_ms = round(ms, 2),
                    ))
            except Exception:
                results.append(CheckResult(
                    check_type = "perf",
                    target     = full_url,
                    passed     = False,
                    issue      = "Asset failed to load",
                ))
    except Exception:
        pass

    return results