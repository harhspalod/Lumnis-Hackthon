from google_play_scraper import Sort, reviews
from typing import List, Dict, Any

def fetch_recent_reviews(app_id: str, count: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches the most recent live reviews for a given app ID.
    Returns a sorted list of reviews (newest first).
    """
    result, continuation_token = reviews(
        app_id,
        lang='en', # Language
        country='us', # Country
        sort=Sort.NEWEST, # Ensure we get the latest live reviews
        count=count # Number of reviews to fetch
    )
    
    return result

def filter_negative_reviews(review_list: List[Dict[str, Any]], max_stars: int = 3) -> List[Dict[str, Any]]:
    """
    Filters the reviews to only include those with `max_stars` or less.
    """
    return [r for r in review_list if r['score'] <= max_stars]
