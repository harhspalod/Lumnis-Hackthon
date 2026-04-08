"""
classify.py — Classifies post feedback into issue type and priority.
Uses Google Gemini (free API).
"""
import json
import os
import logging

logger = logging.getLogger("autopm.classify")

CLASSIFY_PROMPT = """You are a product manager AI. Analyze the following user complaint/feedback post and classify it.

Post: "{post_text}"

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
  "issue_type": "Bug" | "Feature Request" | "Performance",
  "priority": "High" | "Medium" | "Low",
  "summary": "A one-line summary of the core issue",
  "affected_component": "The likely system component affected (e.g., 'auth', 'upload', 'search', 'ui')",
  "user_impact": "Brief description of how this affects users"
}}
"""


def _mock_classify(post_text: str) -> dict:
    """Mock classification for demo/no-API scenarios."""
    text_lower = post_text.lower()

    if any(word in text_lower for word in ["crash", "error", "broken", "bug", "fail", "loop"]):
        return {
            "issue_type": "Bug",
            "priority": "High",
            "summary": "Application crash or critical error reported by user",
            "affected_component": "core",
            "user_impact": "Users unable to complete critical actions",
        }
    elif any(word in text_lower for word in ["slow", "performance", "latency", "timeout", "seconds"]):
        return {
            "issue_type": "Performance",
            "priority": "Medium",
            "summary": "Slow performance or high latency reported",
            "affected_component": "api",
            "user_impact": "Degraded user experience due to slow response times",
        }
    else:
        return {
            "issue_type": "Feature Request",
            "priority": "Medium",
            "summary": "User requesting new functionality or enhancement",
            "affected_component": "ui",
            "user_impact": "Missing functionality limiting user productivity",
        }


def classify_feedback(post_text: str) -> dict:
    """
    Classify a post into issue type, priority, and summary.
    Uses Google Gemini (free API).

    Args:
        post_text: The raw post text.

    Returns:
        Dictionary with issue_type, priority, summary, affected_component, user_impact.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        logger.info("No Gemini API key — using mock classification")
        return _mock_classify(post_text)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            CLASSIFY_PROMPT.format(post_text=post_text),
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=300,
            ),
        )
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]
        result = json.loads(raw.strip())
        logger.info("Classification complete: %s / %s", result.get("issue_type"), result.get("priority"))
        return result

    except Exception as e:
        logger.error("Gemini classification failed: %s — using mock", str(e))
        return _mock_classify(post_text)
