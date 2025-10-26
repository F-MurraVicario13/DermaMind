# BottleScan Backend - FastAPI Main Application
# Install: pip install fastapi uvicorn pytesseract opencv-python pandas numpy pillow

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os

# Import our custom modules
from ocr_processor import extract_text_from_image, parse_ingredients
from health_scorer import analyze_product
from substitute_finder import find_substitutes
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

class ProductRecommendationRequest(BaseModel):
    flagged_ingredients: List[str]
    original_category: Optional[str] = None
    skin_type: Optional[List[str]] = None
    concerns: Optional[List[str]] = None
    max_results: int = 5

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BottleScan API is running!",
        "version": "0.1.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}

# ==================== OCR & Analysis Endpoints ====================

@app.post("/ocr-extract")
async def ocr_extract(image: UploadFile = File(...)):
    """Extract ingredients from product label image using OCR"""
    try:
        contents = await image.read()
        
        # Validate image
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(contents))
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Extract text using OCR
        raw_text = extract_text_from_image(contents)
        
        # Parse ingredients
        ingredients = parse_ingredients(raw_text)
        
        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients found in image")
        
        return {
            "ingredients": ingredients,
            "raw_text": raw_text,
            "ingredient_count": len(ingredients)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/transcribe")
async def transcribe_image(file: UploadFile = File(...)):
    """Run OCR on uploaded image (alternative endpoint)"""
    return await ocr_extract(file)

@app.post("/analyze-ingredients")
async def analyze_ingredients_endpoint(request: AnalysisRequest):
    """Analyze ingredient health scores - bulletproof version"""
    try:
        print(f"DEBUG - Received ingredients: {request.ingredients}")
        
        # Simple inline analysis instead of calling health_scorer
        # This avoids import issues
        
        # Health score database
        health_db = {
            'aqua': {'score': 95, 'reason': 'Water - safe solvent', 'category': 'beneficial'},
            'water': {'score': 95, 'reason': 'Water - safe solvent', 'category': 'beneficial'},
            'glycerin': {'score': 88, 'reason': 'Excellent humectant', 'category': 'beneficial'},
            'niacinamide': {'score': 90, 'reason': 'Vitamin B3 - brightening', 'category': 'beneficial'},
            'hyaluronic acid': {'score': 92, 'reason': 'Superior hydration', 'category': 'beneficial'},
            'sodium hyaluronate': {'score': 92, 'reason': 'Hyaluronic acid salt - hydration', 'category': 'beneficial'},
            'tocopherol': {'score': 85, 'reason': 'Vitamin E antioxidant', 'category': 'beneficial'},
            'ascorbic acid': {'score': 88, 'reason': 'Vitamin C - brightening', 'category': 'beneficial'},
            'retinol': {'score': 82, 'reason': 'Anti-aging, can irritate', 'category': 'beneficial'},
            'panthenol': {'score': 87, 'reason': 'Vitamin B5 - soothing', 'category': 'beneficial'},
            'allantoin': {'score': 83, 'reason': 'Soothing and healing', 'category': 'beneficial'},
            'cetearyl alcohol': {'score': 75, 'reason': 'Fatty alcohol - emollient', 'category': 'neutral'},
            'butylene glycol': {'score': 70, 'reason': 'Humectant - generally safe', 'category': 'neutral'},
            'caprylic/capric triglyceride': {'score': 78, 'reason': 'Coconut-derived emollient', 'category': 'neutral'},
            'xanthan gum': {'score': 80, 'reason': 'Natural thickener', 'category': 'neutral'},
            'disodium edta': {'score': 65, 'reason': 'Chelating agent - helps preserve', 'category': 'neutral'},
            'phenoxyethanol': {'score': 45, 'reason': 'Preservative with concerns', 'category': 'concerning'},
            'parfum': {'score': 20, 'reason': 'Allergen risk', 'category': 'avoid'},
            'fragrance': {'score': 20, 'reason': 'Allergen risk', 'category': 'avoid'},
            'methylparaben': {'score': 15, 'reason': 'Endocrine disruptor', 'category': 'avoid'},
            'propylparaben': {'score': 12, 'reason': 'Hormone disruptor', 'category': 'avoid'},
            'sodium lauryl sulfate': {'score': 25, 'reason': 'Harsh surfactant', 'category': 'avoid'},
        }
        
        # Analyze each ingredient
        analyzed_ingredients = []
        total_score = 0
        
        for ingredient in request.ingredients:
            ing_lower = ingredient.lower().strip()
            
            # Get health data or use default
            if ing_lower in health_db:
                health_data = health_db[ing_lower]
            else:
                health_data = {
                    'score': 60,
                    'reason': 'Limited data available',
                    'category': 'neutral'
                }
            
            analyzed_ingredients.append({
                'ingredient': ingredient,
                'score': int(health_data['score']),
                'reason': health_data['reason']
            })
            
            total_score += health_data['score']
        
        # Calculate product score
        product_score = int(total_score / len(analyzed_ingredients)) if analyzed_ingredients else 60
        
        # Find flagged ingredients (score < 50)
        flagged_ingredients = [
            ing for ing in analyzed_ingredients 
            if ing['score'] < 50
        ]
        
        response = {
            'ingredients': analyzed_ingredients,
            'productScore': product_score,
            'flaggedIngredients': flagged_ingredients
        }
        
        print(f"DEBUG - Sending response: {response}")
        
        return response
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in analyze-ingredients: {error_detail}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}\n{error_detail}"
        )

@app.post("/analyze")
async def analyze_ingredients_alt(request: AnalysisRequest):
    """Analyze ingredient health scores (alternative endpoint)"""
    return await analyze_ingredients_endpoint(request)

# ==================== Product Recommendation Endpoints ====================

@app.post("/recommend-products")
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
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.get("/price-comparison/{product_id}")
async def get_price_comparison(product_id: str):
    """Get real-time pricing comparison for a product"""
    try:
        price_data = product_recommender.get_price_comparison(product_id)
        if "error" in price_data:
            raise HTTPException(status_code=404, detail=price_data["error"])
        return price_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price comparison failed: {str(e)}")

# ==================== Substitute & Alternative Endpoints ====================

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
        raise HTTPException(status_code=500, detail=f"Substitute search failed: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Alternative search failed: {str(e)}")

# ==================== Product Database Endpoints ====================

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
            "job_id": "mock_job_123",
            "message": "Image uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Startup ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)