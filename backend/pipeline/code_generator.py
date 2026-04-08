"""
code_generator.py — Generates implementation code from engineering tasks.
Uses Google Gemini (free API).
"""
import json
import os
import logging

logger = logging.getLogger("autopm.codegen")

CODE_PROMPT = """You are a senior software engineer. Generate production-ready code to implement the following engineering task.

Task: {task_title}
Description: {description}
Technical Notes: {technical_notes}

Acceptance Criteria:
{acceptance_criteria}

Requirements:
- Write clean, well-documented code
- Include error handling
- Follow best practices
- Use Python unless the task specifically requires another language

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
  "language": "python",
  "filename": "suggested_filename.py",
  "code": "The complete implementation code as a string",
  "explanation": "Brief explanation of the implementation approach"
}}
"""


def _mock_generate_code(task: dict) -> dict:
    """Generate mock code based on task type."""
    title = task.get("task_title", "")
    labels = task.get("labels", [])

    if "bug" in labels:
        return {
            "language": "python",
            "filename": "fix_upload_handler.py",
            "code": '''"""Fix: Upload handler with proper error handling and validation."""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class UploadError(Exception):
    """Custom exception for upload failures."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def validate_file(filename: str, file_size: int) -> None:
    """Validate file extension and size before upload."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(
            f"File type '{ext}' not allowed. Accepted: {ALLOWED_EXTENSIONS}",
            status_code=415,
        )
    if file_size > MAX_FILE_SIZE:
        raise UploadError(
            f"File too large ({file_size} bytes). Maximum: {MAX_FILE_SIZE} bytes",
            status_code=413,
        )


async def upload_profile_picture(
    user_id: str,
    file_data: bytes,
    filename: str,
    storage_path: Optional[str] = None,
) -> dict:
    """
    Upload a user profile picture with full validation and error handling.

    Args:
        user_id: The ID of the user uploading the picture.
        file_data: Raw file bytes.
        filename: Original filename.
        storage_path: Optional custom storage directory.

    Returns:
        Dictionary with upload result metadata.

    Raises:
        UploadError: If validation fails or upload encounters an error.
    """
    try:
        # Validate input
        if not user_id:
            raise UploadError("User ID is required", status_code=400)
        if not file_data:
            raise UploadError("No file data provided", status_code=400)

        validate_file(filename, len(file_data))

        # Determine storage path
        base_path = Path(storage_path or "./uploads/profiles")
        base_path.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        ext = Path(filename).suffix.lower()
        safe_filename = f"{user_id}_profile{ext}"
        file_path = base_path / safe_filename

        # Write file
        file_path.write_bytes(file_data)

        logger.info("Profile picture uploaded for user %s: %s", user_id, file_path)
        return {
            "success": True,
            "user_id": user_id,
            "file_path": str(file_path),
            "file_size": len(file_data),
            "message": "Profile picture uploaded successfully",
        }

    except UploadError:
        raise
    except Exception as e:
        logger.exception("Unexpected error uploading profile picture for user %s", user_id)
        raise UploadError(
            f"Internal server error during upload: {str(e)}",
            status_code=500,
        ) from e
''',
            "explanation": "Implemented a robust file upload handler with input validation, proper error handling with custom exceptions, file type and size checks, and safe file storage with logging.",
        }

    elif "performance" in labels:
        return {
            "language": "python",
            "filename": "optimized_search.py",
            "code": '''"""Optimized search with caching, indexing hints, and pagination."""
import logging
import hashlib
import json
from typing import Optional
from functools import lru_cache
from time import perf_counter

logger = logging.getLogger(__name__)


class SearchCache:
    """Simple in-memory search cache with TTL."""

    def __init__(self, max_size: int = 1000):
        self._cache: dict = {}
        self._max_size = max_size

    def _make_key(self, query: str, filters: dict) -> str:
        raw = f"{query}:{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, query: str, filters: dict) -> Optional[dict]:
        key = self._make_key(query, filters)
        return self._cache.get(key)

    def set(self, query: str, filters: dict, result: dict) -> None:
        if len(self._cache) >= self._max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        key = self._make_key(query, filters)
        self._cache[key] = result


# Global cache instance
_search_cache = SearchCache()


async def optimized_search(
    query: str,
    filters: Optional[dict] = None,
    page: int = 1,
    page_size: int = 20,
    use_cache: bool = True,
) -> dict:
    """
    Perform optimized search with caching and pagination.

    Args:
        query: Search query string.
        filters: Optional filter dictionary.
        page: Page number (1-indexed).
        page_size: Results per page.
        use_cache: Whether to use result caching.

    Returns:
        Dictionary with results, pagination info, and timing.
    """
    start = perf_counter()
    filters = filters or {}

    # Check cache first
    if use_cache:
        cached = _search_cache.get(query, filters)
        if cached:
            elapsed = perf_counter() - start
            logger.info("Cache hit for query '%s' in %.3fs", query, elapsed)
            return {**cached, "cached": True, "response_time_ms": elapsed * 1000}

    # Build optimized query with index hints
    offset = (page - 1) * page_size

    # Simulated optimized DB query
    sql = f"""
    SELECT /*+ INDEX(items idx_search_text) */
        id, title, description, relevance_score
    FROM items
    WHERE MATCH(title, description) AGAINST(:query IN BOOLEAN MODE)
    ORDER BY relevance_score DESC
    LIMIT :limit OFFSET :offset
    """

    # Simulated results
    results = [
        {"id": i, "title": f"Result {i}", "score": 0.95 - (i * 0.05)}
        for i in range(1, min(page_size + 1, 6))
    ]

    result = {
        "query": query,
        "results": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_results": len(results),
        },
        "cached": False,
    }

    # Store in cache
    if use_cache:
        _search_cache.set(query, filters, result)

    elapsed = perf_counter() - start
    result["response_time_ms"] = round(elapsed * 1000, 2)
    logger.info("Search for '%s' completed in %.3fs", query, elapsed)
    return result
''',
            "explanation": "Implemented an optimized search with in-memory caching, pagination support, index hints for database queries, and performance timing for monitoring response times.",
        }

    else:
        return {
            "language": "python",
            "filename": "csv_export.py",
            "code": '''"""Feature: CSV export for reports with streaming support."""
import csv
import io
import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_csv_report(
    data: list[dict[str, Any]],
    columns: list[str] | None = None,
    title: str = "Report",
) -> str:
    """
    Generate a CSV report from structured data.

    Args:
        data: List of dictionaries representing rows.
        columns: Optional list of column names. If None, inferred from data.
        title: Report title for logging.

    Returns:
        CSV content as a string.
    """
    if not data:
        logger.warning("No data provided for CSV export")
        return ""

    # Infer columns from first row if not provided
    if columns is None:
        columns = list(data[0].keys())

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")

    # Write header
    writer.writeheader()

    # Write rows
    rows_written = 0
    for row in data:
        writer.writerow(row)
        rows_written += 1

    content = output.getvalue()
    logger.info(
        "CSV report '%s' generated: %d rows, %d columns",
        title, rows_written, len(columns),
    )
    return content


def export_report_to_file(
    data: list[dict[str, Any]],
    output_path: str | None = None,
    columns: list[str] | None = None,
) -> str:
    """
    Export report data to a CSV file.

    Args:
        data: List of dictionaries representing rows.
        output_path: File path for output. Auto-generated if None.
        columns: Optional column name list.

    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"report_{timestamp}.csv"

    csv_content = generate_csv_report(data, columns)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        f.write(csv_content)

    logger.info("Report exported to %s", output_path)
    return output_path
''',
            "explanation": "Implemented CSV export functionality with streaming support, automatic column inference, proper encoding, and timestamped file output for easy report generation.",
        }


def generate_code(task: dict) -> dict:
    """
    Generate implementation code for an engineering task.
    Uses Google Gemini (free API).

    Args:
        task: Output from generate_task().

    Returns:
        Dictionary with language, filename, code, and explanation.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        logger.info("No Gemini API key — using mock code generation")
        return _mock_generate_code(task)

    try:
        import google.generativeai as genai

        criteria_str = "\n".join(f"- {c}" for c in task.get("acceptance_criteria", []))

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            CODE_PROMPT.format(
                task_title=task.get("task_title", ""),
                description=task.get("description", ""),
                technical_notes=task.get("technical_notes", ""),
                acceptance_criteria=criteria_str,
            ),
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000,
            ),
        )
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]
        result = json.loads(raw.strip())
        logger.info("Code generated: %s (%s)", result.get("filename"), result.get("language"))
        return result

    except Exception as e:
        logger.error("Gemini code generation failed: %s — using mock", str(e))
        return _mock_generate_code(task)
