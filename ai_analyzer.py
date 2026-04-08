import os
from google import genai
from typing import List, Dict, Any

def analyze_reviews_with_gemini(reviews_data: List[Dict[str, Any]]) -> str:
    """
    Sends the filtered reviews to Gemini and returns actionable debugging steps.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
         raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    # Format the reviews for the prompt
    reviews_text = ""
    for r in reviews_data:
        reviews_text += f"- Score: {r['score']}, Content: {r['content']}\n"
        
    prompt = f"""
    You are an expert mobile app developer and debugger. 
    Below is a list of recent negative user reviews from the Google Play Store for our application.
    
    Please analyze these reviews, identify common bugs, crashes, or usability issues, 
    and provide specific, actionable debugging steps or technical explanations to resolve them.
    If possible, suggest code-level considerations.
    
    Here are the reviews:
    {reviews_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt
    )
    return response.text
