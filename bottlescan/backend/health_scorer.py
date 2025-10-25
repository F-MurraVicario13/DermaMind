# Health Scorer - Ingredient health scoring system
# Computes health scores for ingredients based on safety data

import json
import os
from typing import List, Dict
from pydantic import BaseModel

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

def load_health_database():
    """Load precomputed health scores from processed dataset"""
    # Try to load from processed data first
    processed_path = "../data/processed/ingredient_health_scores.json"
    if os.path.exists(processed_path):
        with open(processed_path, 'r') as f:
            return json.load(f)
    
    # Fallback to mock database for demo
    return {
        'aqua': {'score': 95, 'reason': 'Water - safe solvent', 'category': 'beneficial'},
        'glycerin': {'score': 88, 'reason': 'Excellent humectant', 'category': 'beneficial'},
        'niacinamide': {'score': 90, 'reason': 'Vitamin B3 - brightening', 'category': 'beneficial'},
        'hyaluronic acid': {'score': 92, 'reason': 'Superior hydration', 'category': 'beneficial'},
        'tocopherol': {'score': 85, 'reason': 'Vitamin E antioxidant', 'category': 'beneficial'},
        'ascorbic acid': {'score': 88, 'reason': 'Vitamin C - brightening', 'category': 'beneficial'},
        'retinol': {'score': 82, 'reason': 'Anti-aging, can irritate', 'category': 'beneficial'},
        'butylene glycol': {'score': 70, 'reason': 'Humectant - generally safe', 'category': 'neutral'},
        'phenoxyethanol': {'score': 45, 'reason': 'Preservative with concerns', 'category': 'concerning'},
        'parfum': {'score': 20, 'reason': 'Allergen risk', 'category': 'avoid'},
        'fragrance': {'score': 20, 'reason': 'Allergen risk', 'category': 'avoid'},
        'methylparaben': {'score': 15, 'reason': 'Endocrine disruptor', 'category': 'avoid'},
        'propylparaben': {'score': 12, 'reason': 'Hormone disruptor', 'category': 'avoid'},
        'sodium lauryl sulfate': {'score': 25, 'reason': 'Harsh surfactant', 'category': 'avoid'},
    }

def compute_health_score(ingredient: str, db: Dict) -> IngredientScore:
    """Compute health score for a single ingredient"""
    ing_lower = ingredient.lower().strip()
    
    if ing_lower in db:
        data = db[ing_lower]
        return IngredientScore(
            ingredient=ingredient,
            health_score=data['score'],
            reason=data['reason'],
            category=data['category']
        )
    else:
        # Unknown ingredient - neutral score
        return IngredientScore(
            ingredient=ingredient,
            health_score=60,
            reason='Limited data available',
            category='neutral'
        )

def analyze_product(ingredients: List[str]) -> AnalysisResponse:
    """Analyze full product ingredient list"""
    db = load_health_database()
    
    scores = [compute_health_score(ing, db) for ing in ingredients]
    
    # Calculate product score (weighted by position)
    weights = [1.0 / (i + 1)**0.3 for i in range(len(scores))]  # Earlier ingredients weighted more
    total_weight = sum(weights)
    
    weighted_score = sum(s.health_score * w for s, w in zip(scores, weights)) / total_weight
    
    # Count flagged ingredients
    flagged = sum(1 for s in scores if s.category in ['concerning', 'avoid'])
    
    # Interpretation
    if weighted_score >= 76:
        interpretation = "Healthy / Preferred"
    elif weighted_score >= 51:
        interpretation = "Generally Okay"
    elif weighted_score >= 26:
        interpretation = "Use with Caution"
    else:
        interpretation = "Avoid"
    
    return AnalysisResponse(
        ingredients=scores,
        product_score=round(weighted_score, 1),
        flagged_count=flagged,
        interpretation=interpretation
    )
