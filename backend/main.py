"""
AutoPM — Autonomous Code Review & Product Intelligence System
FastAPI Backend Entry Point
"""
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.fetch_reddit import fetch_reddit_posts
from pipeline.classify import classify_feedback
from pipeline.task_generator import generate_task
from pipeline.code_generator import generate_code
from pipeline.code_reviewer import review_code
from pipeline.pr_generator import generate_pr

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("autopm")

# FastAPI app
app = FastAPI(
    title="AutoPM API",
    description="Autonomous Code Review & Product Intelligence System",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---

class PostInput(BaseModel):
    id: str
    text: str
    author: str | None = None
    created_at: str | None = None
    subreddit: str | None = None
    metrics: dict | None = None


class ProcessRequest(BaseModel):
    post: PostInput


# --- Routes ---

@app.get("/")
async def root():
    return {
        "name": "AutoPM API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "posts": "/api/posts?mode=demo|live",
            "process": "POST /api/process",
            "health": "/api/health",
        },
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.get("/api/posts")
async def get_posts():
    """Fetch Reddit posts with automatic fallback to demo data."""
    try:
        logger.info("=== Fetching Reddit posts ===")
        result = fetch_reddit_posts()
        return {
            "source": result["source"],
            "error": result.get("error"),
            "count": len(result["posts"]),
            "posts": result["posts"]
        }
    except Exception as e:
        logger.exception("Failed to fetch posts")
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")


@app.post("/api/process")
async def process_post(request: ProcessRequest):
    """Run the full AI pipeline on a single Reddit post."""
    post = request.post
    logger.info("=== Processing post id=%s ===", post.id)

    pipeline_results = {"post": post.model_dump(), "stages": {}}

    try:
        # Stage 1: Classify
        logger.info("[1/5] Classifying feedback...")
        classification = classify_feedback(post.text)
        pipeline_results["stages"]["classification"] = classification
        logger.info("  → %s / %s", classification.get("issue_type"), classification.get("priority"))

        # Stage 2: Generate Task
        logger.info("[2/5] Generating engineering task...")
        task = generate_task(classification, post.text)
        pipeline_results["stages"]["task"] = task
        logger.info("  → %s", task.get("task_title"))

        # Stage 3: Generate Code
        logger.info("[3/5] Generating code...")
        code_output = generate_code(task)
        pipeline_results["stages"]["code"] = code_output
        logger.info("  → %s (%s)", code_output.get("filename"), code_output.get("language"))

        # Stage 4: Review Code
        logger.info("[4/5] Reviewing code...")
        review = review_code(code_output, task)
        pipeline_results["stages"]["review"] = review
        logger.info("  → Score: %s/10 — %s", review.get("overall_score"), review.get("verdict"))

        # Stage 5: Generate PR
        logger.info("[5/5] Generating PR summary...")
        pr = generate_pr(task, code_output, review)
        pipeline_results["stages"]["pr"] = pr
        logger.info("  → %s", pr.get("pr_title"))

        pipeline_results["success"] = True
        logger.info("=== Pipeline complete for post id=%s ===", post.id)
        return pipeline_results

    except Exception as e:
        logger.exception("Pipeline failed for post id=%s", post.id)
        pipeline_results["success"] = False
        pipeline_results["error"] = str(e)
        raise HTTPException(status_code=500, detail=pipeline_results)
