# BottleScan Backend - FastAPI Main Application
# Install: pip install fastapi uvicorn pytesseract opencv-python pandas numpy sentence-transformers pillow

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os

# Import our custom modules
from ocr_processor import extract_text_from_image, parse_ingredients
from health_scorer import analyze_product, load_health_database
from substitute_finder import find_substitutes, load_substitute_database
from product_recommender import product_recommender

app = FastAPI(title="BottleScan API", version="0.1.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Data Models ====================

class AnalysisRequest(BaseModel):
    ingredients: List[str]

class SubstituteRequest(BaseModel):
    ingredients: List[str]
    max_suggestions: int = 5

class IngredientScore(BaseModel):
    ingredient: str
    health_score: float
    reason: str
    category: str  # 'beneficial', 'neutral', 'concerning', 'avoid'

class AnalysisResponse(BaseModel):
    ingredients: List[IngredientScore]
    product_score: float
    flagged_count: int
    interpretation: str

class Substitute(BaseModel):
    original_ingredient: str
    substitute_name: str
    substitute_score: float
    functional_role: str
    confidence: float

class ProductRecommendationRequest(BaseModel):
    flagged_ingredients: List[str]
    original_category: Optional[str] = None
    skin_type: Optional[List[str]] = None
    concerns: Optional[List[str]] = None
    max_results: int = 5

class ProductRecommendation(BaseModel):
    product_id: str
    brand: str
    name: str
    category: str
    skin_type: List[str]
    concerns: List[str]
    ingredients: List[str]
    health_score: float
    price_range: str
    average_price: float
    currency: str
    url: str
    image_url: str
    rating: float
    review_count: int
    availability: str
    substitute_score: float
    similarity_score: float
    health_boost: float

class PriceComparison(BaseModel):
    product_id: str
    product_name: str
    brand: str
    current_price: float
    currency: str
    price_sources: List[Dict]
    price_trend: Dict

# ==================== API Endpoints ====================

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload image and get preview"""
    try:
        contents = await file.read()
        
        # Validate image
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(contents))
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        return {
            "status": "success",
            "job_id": "mock_job_123",  # In production, generate unique ID
            "message": "Image uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_image(file: UploadFile = File(...)):
    """Run OCR on uploaded image"""
    try:
        contents = await file.read()
        
        # Extract text
        raw_text = extract_text_from_image(contents)
        
        # Parse ingredients
        ingredients = parse_ingredients(raw_text)
        
        return {
            "status": "success",
            "raw_text": raw_text,
            "ingredients": ingredients,
            "ingredient_count": len(ingredients)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_ingredients(request: AnalysisRequest):
    """Analyze ingredient health scores"""
    try:
        analysis = analyze_product(request.ingredients)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest-substitutes")
async def suggest_substitutes(request: SubstituteRequest):
    """Suggest healthier ingredient substitutes"""
    try:
        substitutes = find_substitutes(request.ingredients, request.max_suggestions)
        return {
            "status": "success",
            "substitutes": substitutes,
            "count": len(substitutes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend-products", response_model=List[ProductRecommendation])
async def recommend_products(request: ProductRecommendationRequest):
    """Find substitute products without flagged ingredients"""
    try:
        recommendations = product_recommender.find_substitute_products(
            flagged_ingredients=request.flagged_ingredients,
            original_category=request.original_category,
            skin_type=request.skin_type,
            concerns=request.concerns,
            max_results=request.max_results
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price-comparison/{product_id}", response_model=PriceComparison)
async def get_price_comparison(product_id: str):
    """Get real-time pricing comparison for a product"""
    try:
        price_data = product_recommender.get_price_comparison(product_id)
        if "error" in price_data:
            raise HTTPException(status_code=404, detail=price_data["error"])
        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingredient-alternatives/{ingredient}")
async def get_ingredient_alternatives(ingredient: str):
    """Get ingredient-level alternatives and products containing them"""
    try:
        alternatives = product_recommender.get_ingredient_alternatives(ingredient)
        return {
            "ingredient": ingredient,
            "alternatives": alternatives,
            "count": len(alternatives)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
async def get_all_products():
    """Get all available products in the database"""
    try:
        return {
            "products": product_recommender.product_database,
            "count": len(product_recommender.product_database)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}

# ==================== Startup ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
