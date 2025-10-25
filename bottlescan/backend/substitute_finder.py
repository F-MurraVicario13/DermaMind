# Substitute Finder - Ingredient substitute recommendation engine
# Finds healthier alternatives for concerning ingredients

import json
import os
from typing import List, Dict
from pydantic import BaseModel

class Substitute(BaseModel):
    original_ingredient: str
    substitute_name: str
    substitute_score: float
    functional_role: str
    confidence: float

def load_substitute_database():
    """Load ingredient substitutes from processed dataset"""
    # Try to load from processed data first
    processed_path = "../data/processed/ingredient_substitutes.json"
    if os.path.exists(processed_path):
        with open(processed_path, 'r') as f:
            return json.load(f)
    
    # Fallback to mock database for demo
    return {
        'methylparaben': [
            {'name': 'leucidal liquid', 'score': 75, 'role': 'preservative', 'confidence': 0.85},
            {'name': 'sodium benzoate', 'score': 65, 'role': 'preservative', 'confidence': 0.80},
        ],
        'propylparaben': [
            {'name': 'potassium sorbate', 'score': 70, 'role': 'preservative', 'confidence': 0.82},
        ],
        'parfum': [
            {'name': 'fragrance-free', 'score': 95, 'role': 'remove fragrance', 'confidence': 0.95},
            {'name': 'essential oil blend', 'score': 60, 'role': 'natural fragrance', 'confidence': 0.70},
        ],
        'fragrance': [
            {'name': 'fragrance-free', 'score': 95, 'role': 'remove fragrance', 'confidence': 0.95},
        ],
        'sodium lauryl sulfate': [
            {'name': 'sodium cocoyl isethionate', 'score': 78, 'role': 'surfactant', 'confidence': 0.88},
            {'name': 'decyl glucoside', 'score': 82, 'role': 'surfactant', 'confidence': 0.85},
        ],
    }

def find_substitutes(ingredients: List[str], max_suggestions: int = 5) -> List[Substitute]:
    """Find healthier substitutes for flagged ingredients"""
    from health_scorer import load_health_database
    
    db = load_health_database()
    sub_db = load_substitute_database()
    
    substitutes = []
    
    for ing in ingredients:
        ing_lower = ing.lower().strip()
        
        # Only suggest substitutes for concerning/avoid ingredients
        if ing_lower in db and db[ing_lower]['category'] in ['concerning', 'avoid']:
            if ing_lower in sub_db:
                for sub in sub_db[ing_lower][:max_suggestions]:
                    substitutes.append(Substitute(
                        original_ingredient=ing,
                        substitute_name=sub['name'],
                        substitute_score=sub['score'],
                        functional_role=sub['role'],
                        confidence=sub['confidence']
                    ))
    
    return substitutes
