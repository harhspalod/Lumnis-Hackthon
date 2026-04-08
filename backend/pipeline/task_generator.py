"""
task_generator.py — Converts classified feedback into engineering tasks.
Uses Google Gemini (free API).
"""
import json
import os
import logging

logger = logging.getLogger("autopm.task")

TASK_PROMPT = """You are a senior engineering manager. Convert the following classified user feedback into a clear, actionable engineering task.

Classification:
- Issue Type: {issue_type}
- Priority: {priority}
- Summary: {summary}
- Affected Component: {affected_component}
- User Impact: {user_impact}

Original Post: "{post_text}"

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
  "task_title": "Clear, concise task title (e.g., 'Fix profile picture upload 500 error')",
  "description": "Detailed task description with context",
  "acceptance_criteria": ["List of specific, testable acceptance criteria"],
  "technical_notes": "Technical suggestions or hints for implementation",
  "estimated_effort": "Small | Medium | Large",
  "labels": ["List of relevant labels like 'bug', 'frontend', 'api', etc."]
}}
"""


def _mock_generate_task(classification: dict, post_text: str) -> dict:
    """Generate a mock engineering task."""
    issue_type = classification.get("issue_type", "Bug")
    summary = classification.get("summary", "Issue reported by user")
    component = classification.get("affected_component", "core")

    if issue_type == "Bug":
        return {
            "task_title": f"Fix: {summary}",
            "description": f"A user reported a critical bug: \"{post_text[:100]}...\"\n\nThis needs immediate investigation and resolution in the {component} component.",
            "acceptance_criteria": [
                "The reported error no longer occurs",
                "Unit tests added for the fix",
                "Error handling improved for edge cases",
                "User-facing error messages are clear and helpful",
            ],
            "technical_notes": f"Investigate the {component} module. Check error logs for stack traces. Likely a validation or exception handling issue.",
            "estimated_effort": "Medium",
            "labels": ["bug", "priority-high", component],
        }
    elif issue_type == "Performance":
        return {
            "task_title": f"Optimize: {summary}",
            "description": f"Performance issue reported: \"{post_text[:100]}...\"\n\nUsers experiencing slow response times in the {component} component.",
            "acceptance_criteria": [
                "Response time reduced to under 500ms",
                "Database queries optimized with proper indexing",
                "Performance benchmarks added",
                "No regression in functionality",
            ],
            "technical_notes": f"Profile the {component} module. Check for N+1 queries, missing indexes, or unoptimized algorithms.",
            "estimated_effort": "Medium",
            "labels": ["performance", "optimization", component],
        }
    else:
        return {
            "task_title": f"Feature: {summary}",
            "description": f"Feature request from user: \"{post_text[:100]}...\"\n\nAdd new functionality to the {component} component.",
            "acceptance_criteria": [
                "Feature implemented as described",
                "UI/UX follows existing design patterns",
                "Documentation updated",
                "Tests cover happy path and edge cases",
            ],
            "technical_notes": f"Implement in the {component} module. Follow existing patterns and ensure backward compatibility.",
            "estimated_effort": "Large",
            "labels": ["feature", "enhancement", component],
        }


def generate_task(classification: dict, post_text: str) -> dict:
    """
    Convert classified feedback into a structured engineering task.
    Uses Google Gemini (free API).

    Args:
        classification: Output from classify_feedback().
        post_text: The original post text.

    Returns:
        Dictionary with task_title, description, acceptance_criteria, etc.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        logger.info("No Gemini API key — using mock task generation")
        return _mock_generate_task(classification, post_text)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            TASK_PROMPT.format(post_text=post_text, **classification),
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                max_output_tokens=500,
            ),
        )
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]
        result = json.loads(raw.strip())
        logger.info("Task generated: %s", result.get("task_title"))
        return result

    except Exception as e:
        logger.error("Gemini task generation failed: %s — using mock", str(e))
        return _mock_generate_task(classification, post_text)
