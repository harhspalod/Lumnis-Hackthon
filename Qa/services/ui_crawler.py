# services/ui_crawler.py
import requests
from bs4 import BeautifulSoup
from models.schemas import CheckResult

TIMEOUT = 10


def check_ui(url: str) -> list[CheckResult]:
    results = []

    try:
        resp = requests.get(url, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")

        results += _check_page_loads(url, resp)
        results += _check_broken_links(url, soup)
        results += _check_forms(url, soup)
        results += _check_images(url, soup)
        results += _check_meta(url, soup)

    except Exception as e:
        results.append(CheckResult(
            check_type = "ui",
            target     = url,
            passed     = False,
            issue      = f"UI check failed: {str(e)}",
        ))

    return results


def _check_page_loads(url: str, resp: requests.Response) -> list[CheckResult]:
    passed = resp.status_code == 200
    return [CheckResult(
        check_type = "ui",
        target     = url,
        passed     = passed,
        issue      = None if passed else f"Page returned {resp.status_code}",
    )]


def _check_broken_links(url: str, soup: BeautifulSoup) -> list[CheckResult]:
    results = []
    base    = url.rstrip("/")
    links   = [a["href"] for a in soup.find_all("a", href=True)]

    for href in links[:20]:  # cap at 20
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        full = href if href.startswith("http") else f"{base}{href}"
        try:
            r = requests.head(full, timeout=5, allow_redirects=True)
            if r.status_code >= 400:
                results.append(CheckResult(
                    check_type = "ui",
                    target     = full,
                    passed     = False,
                    issue      = f"Broken link: HTTP {r.status_code}",
                ))
        except Exception:
            results.append(CheckResult(
                check_type = "ui",
                target     = full,
                passed     = False,
                issue      = "Broken link: unreachable",
            ))
    return results


def _check_forms(url: str, soup: BeautifulSoup) -> list[CheckResult]:
    results = []
    for form in soup.find_all("form"):
        action  = form.get("action", "")
        method  = form.get("method", "get").upper()
        inputs  = form.find_all("input")
        has_submit = any(
            i.get("type", "").lower() in ("submit", "button")
            for i in inputs
        )
        if not has_submit:
            results.append(CheckResult(
                check_type = "ui",
                target     = url,
                passed     = False,
                issue      = f"Form with action='{action}' has no submit button",
            ))
        if not action:
            results.append(CheckResult(
                check_type = "ui",
                target     = url,
                passed     = False,
                issue      = "Form found with no action attribute",
            ))
    return results


def _check_images(url: str, soup: BeautifulSoup) -> list[CheckResult]:
    results = []
    base    = url.rstrip("/")
    for img in soup.find_all("img")[:15]:
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        full = src if src.startswith("http") else f"{base}{src}"
        try:
            r = requests.head(full, timeout=5)
            if r.status_code >= 400:
                results.append(CheckResult(
                    check_type = "ui",
                    target     = full,
                    passed     = False,
                    issue      = f"Broken image: HTTP {r.status_code}",
                ))
        except Exception:
            results.append(CheckResult(
                check_type = "ui",
                target     = full,
                passed     = False,
                issue      = "Broken image: unreachable",
            ))
    return results


def _check_meta(url: str, soup: BeautifulSoup) -> list[CheckResult]:
    results = []
    if not soup.find("title"):
        results.append(CheckResult(
            check_type = "ui", target = url,
            passed = False, issue = "Page missing <title> tag",
        ))
    if not soup.find("meta", attrs={"name": "viewport"}):
        results.append(CheckResult(
            check_type = "ui", target = url,
            passed = False, issue = "Missing viewport meta — may break mobile",
        ))
    return results