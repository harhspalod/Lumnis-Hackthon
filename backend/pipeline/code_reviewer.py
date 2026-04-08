"""
code_reviewer.py — AI-based code review that provides feedback and improved code.
Uses Google Gemini (free API).
"""
import json
import os
import logging

logger = logging.getLogger("autopm.review")

REVIEW_PROMPT = """You are a senior code reviewer. Review the following code and provide detailed feedback.

Task: {task_title}
Language: {language}
Filename: {filename}

Code:
```{language}
{code}
```

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
  "overall_score": 8,
  "verdict": "Approved" | "Changes Requested" | "Approved with Suggestions",
  "strengths": ["List of things done well"],
  "issues": [
    {{
      "severity": "Critical" | "Warning" | "Info",
      "description": "Description of the issue",
      "suggestion": "How to fix it"
    }}
  ],
  "improved_code": "The improved version of the code incorporating all suggestions",
  "summary": "Brief review summary"
}}
"""


def _mock_review_code(code_output: dict, task: dict) -> dict:
    """Generate a mock code review."""
    return {
        "overall_score": 8,
        "verdict": "Approved with Suggestions",
        "strengths": [
            "Good error handling with custom exceptions",
            "Proper input validation before processing",
            "Clear function documentation with type hints",
            "Logging implemented at appropriate levels",
        ],
        "issues": [
            {
                "severity": "Warning",
                "description": "Consider adding rate limiting to prevent abuse",
                "suggestion": "Implement a token bucket or sliding window rate limiter decorator",
            },
            {
                "severity": "Info",
                "description": "Magic numbers could be extracted to configuration",
                "suggestion": "Move MAX_FILE_SIZE and similar constants to a config module or environment variables",
            },
            {
                "severity": "Info",
                "description": "Consider adding retry logic for transient failures",
                "suggestion": "Use tenacity or a similar retry library for network/IO operations",
            },
        ],
        "improved_code": code_output.get("code", "# No code to improve"),
        "summary": "Well-structured code with solid error handling. Minor improvements suggested around configuration management and resilience patterns. Ready for production with the suggested enhancements.",
    }


def review_code(code_output: dict, task: dict) -> dict:
    """
    Perform AI-based code review.
    Uses Google Gemini (free API).

    Args:
        code_output: Output from generate_code().
        task: Output from generate_task().

    Returns:
        Dictionary with score, verdict, issues, improved code, and summary.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        logger.info("No Gemini API key — using mock code review")
        return _mock_review_code(code_output, task)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            REVIEW_PROMPT.format(
                task_title=task.get("task_title", ""),
                language=code_output.get("language", "python"),
                filename=code_output.get("filename", "unknown.py"),
                code=code_output.get("code", ""),
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
        logger.info("Code review complete: score=%s, verdict=%s", result.get("overall_score"), result.get("verdict"))
        return result

    except Exception as e:
        logger.error("Gemini code review failed: %s — using mock", str(e))
        return _mock_review_code(code_output, task)
