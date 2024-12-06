from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Assuming RecommendationEngine is in a separate module
from recommendation_engine import RecommendationEngine

# Initialize the recommendation engine
try:
    rec_engine = RecommendationEngine(
        faiss_index_path='image_vectors.index',
        product_metadata_path='processed_data.json'
    )
except Exception as e:
    print(f"Error initializing recommendation engine: {e}")
    rec_engine = None

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class RecommendationRequest(BaseModel):
    user_id: str
    colors: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    num_recommendations: int = 10

class UserInteractionRequest(BaseModel):
    user_id: str
    product_id: str
    reaction: str  # 'like' or 'dislike'

@app.post("/get-recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Get recommendations based on user tracking status
    """
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommendation engine not initialized")

    try:
        # Check if user is being tracked
        user_tracker = rec_engine.user_trackers.get(request.user_id)

        if user_tracker and user_tracker.compute_preference_vector() is not None:
            # User has interactions, get personalized recommendations
            recommendations = rec_engine.get_recommendations(
                request.user_id,
                num_recommendations=request.num_recommendations,
                color_filter=request.colors,
                category_filter=request.categories
            )
        else:
            # No user interactions, get diverse recommendations
            recommendations = rec_engine.get_recommendations(
                request.user_id,
                num_recommendations=request.num_recommendations,
                color_filter=request.colors,
                category_filter=request.categories
            )

        return {
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record-interaction")
async def record_user_interaction(request: UserInteractionRequest):
    """
    Record user interaction without returning recommendations
    """
    if rec_engine is None:
        raise HTTPException(status_code=500, detail="Recommendation engine not initialized")
    try:

        # Record user interaction
        rec_engine.record_user_interaction(
            request.user_id, 
            request.product_id,
            request.reaction
        )

        return {"status": "Interaction recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
