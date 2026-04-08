# models/schemas.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class TestStatus(str, Enum):
    passed  = "passed"
    failed  = "failed"
    error   = "error"
    skipped = "skipped"


class RunTestsRequest(BaseModel):
    target_url: str
    test_file:  Optional[str]       = None  # run one file or all
    tags:       Optional[List[str]] = None  # filter by markers e.g. ["login"]

    model_config = {
        "json_schema_extra": {
            "example": {
                "target_url": "http://localhost:3000",
                "test_file":  "tests/sample_tests/test_login.py",
            }
        }
    }


class TestResult(BaseModel):
    test_name:       str
    status:          TestStatus
    duration_ms:     float
    error_message:   Optional[str] = None
    screenshot_path: Optional[str] = None
    logs:            Optional[str] = None  # ✅ ADD
    ai_analysis_id:  Optional[str] = None


class RunTestsResponse(BaseModel):
    run_id:      str
    target_url:  str
    total:       int
    passed:      int
    failed:      int
    errored:     int
    duration_ms: float
    timestamp:   datetime   # ✅ ADD THIS
    results:     List[TestResult]
    report_path: Optional[str] = None


class AnalyzeFailureRequest(BaseModel):
    run_id:    str
    test_name: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "run_id":    "run_20240408_123456_abc123",
                "test_name": "tests/sample_tests/test_login.py::test_login_valid",
            }
        }
    }

class ConfidenceLevel(str, Enum):
    high   = "high"
    medium = "medium"
    low    = "low"

class AnalyzeFailureResponse(BaseModel):
    test_name:  str
    root_cause: str
    suggestion: str
    confidence: ConfidenceLevel  # "high" / "medium" / "low"
    probable_layer:  Optional[str] = None  # frontend/backend/api/db
    fix_snippet:     Optional[str] = None  # AI generated fix

# ADD to models/schemas.py

class SignalType(str, Enum):
    slow_page    = "slow_page"
    api_error    = "api_error"
    broken_ui    = "broken_ui"
    error_500    = "500_error"
    full_scan    = "full_scan"

class Severity(str, Enum):
    low    = "low"
    medium = "medium"
    high   = "high"

class IncomingSignal(BaseModel):
    site_url:    str
    signal_type: SignalType
    page:        Optional[str] = None       # e.g. "/login"
    endpoint:    Optional[str] = None       # e.g. "/api/auth/login"
    severity:    Severity      = Severity.medium
    metadata:    Optional[dict] = None      # any extra info from your review system

    model_config = {
        "json_schema_extra": {
            "example": {
                "site_url":    "https://bharatmcp.com",
                "signal_type": "slow_page",
                "page":        "/login",
                "severity":    "high"
            }
        }
    }

class CheckResult(BaseModel):
    check_type:   str                        # "api" | "ui" | "perf"
    target:       str                        # url or endpoint checked
    passed:       bool
    issue:        Optional[str] = None       # what's wrong
    detail:       Optional[str] = None       # full detail / traceback
    duration_ms:  Optional[float] = None
    screenshot:   Optional[str] = None

class SignalReport(BaseModel):
    run_id:       str
    site_url:     str
    signal:       IncomingSignal
    timestamp:    datetime
    checks_run:   List[str]                  # which checkers fired
    results:      List[CheckResult]
    total_issues: int
    summary:      str                        # one line: "2 issues found on /login"