import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from scraper import fetch_recent_reviews, filter_negative_reviews
from ai_analyzer import analyze_reviews_with_gemini

# Load environment variables
load_dotenv()

app = FastAPI(title="Play Store Review Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    app_id: str
    count: int = 50
    max_stars: int = 3

class AnalyzeResponse(BaseModel):
    app_id: str
    fetched_reviews_count: int
    analyzed_negative_reviews_count: int
    analysis_result: str

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    try:
        # 1. Fetch reviews
        all_reviews = fetch_recent_reviews(request.app_id, request.count)
        
        # 2. Filter for negative ones
        negative_reviews = filter_negative_reviews(all_reviews, request.max_stars)
        
        if not negative_reviews:
            return AnalyzeResponse(
                app_id=request.app_id,
                fetched_reviews_count=len(all_reviews),
                analyzed_negative_reviews_count=0,
                analysis_result="No negative reviews found to analyze."
            )

        # 3. Analyze with Gemini
        analysis = analyze_reviews_with_gemini(negative_reviews)
        
        return AnalyzeResponse(
            app_id=request.app_id,
            fetched_reviews_count=len(all_reviews),
            analyzed_negative_reviews_count=len(negative_reviews),
            analysis_result=analysis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
