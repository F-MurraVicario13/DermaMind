# Simplified preprocessing without sentence-transformers to avoid segfault
import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import json
import ast

# ==================== Configuration ====================

KAGGLE_CSV_PATH = "raw/skincare_products_clean.csv"
OUTPUT_INGREDIENT_DB = "processed/ingredient_health_scores.json"

# Known harmful ingredients
HARM_LIST = {
    'methylparaben', 'propylparaben', 'butylparaben', 'ethylparaben',
    'sodium lauryl sulfate', 'sodium laureth sulfate', 'sls', 'sles',
    'parfum', 'fragrance', 'synthetic fragrance',
    'alcohol denat', 'isopropyl alcohol', 'sd alcohol',
    'dmdm hydantoin', 'imidazolidinyl urea', 'quaternium-15',
    'triclosan', 'triclocarban', 'toluene', 'coal tar'
}

# Known beneficial ingredients
BENEFIT_LIST = {
    'niacinamide', 'hyaluronic acid', 'sodium hyaluronate', 'glycerin', 
    'tocopherol', 'tocopheryl acetate', 'ascorbic acid', 'retinol', 
    'retinyl palmitate', 'ceramide', 'peptide', 'allantoin', 'panthenol',
    'beta glucan', 'centella asiatica', 'aloe vera', 'squalane',
    'alpha arbutin', 'kojic acid', 'azelaic acid', 'salicylic acid',
    'lactic acid', 'mandelic acid', 'ferulic acid', 'resveratrol'
}

def parse_ingredient_string(ingredient_str: str) -> List[str]:
    """Parse ingredient string into list"""
    if pd.isna(ingredient_str):
        return []
    
    # Check if it's a string representation of a Python list
    if ingredient_str.startswith("['") and ingredient_str.endswith("']"):
        try:
            ingredients = ast.literal_eval(ingredient_str)
            if isinstance(ingredients, list):
                return [ing.strip().lower() for ing in ingredients if ing and len(ing) > 2]
        except:
            pass
    
    # Fallback to comma/semicolon splitting
    ingredients = re.split(r'[,;]', str(ingredient_str))
    cleaned = []
    for ing in ingredients:
        ing = re.sub(r'\([^)]*\)', '', ing)
        ing = re.sub(r'\[[^\]]*\]', '', ing)
        ing = ing.strip().lower()
        if ing and len(ing) > 2:
            cleaned.append(ing)
    
    return cleaned

def compute_health_score(ingredient: str, frequency_score: float) -> Dict:
    """Compute health score for an ingredient"""
    
    # Component 1: Frequency score (0-35 points)
    freq_points = min(frequency_score * 100 * 0.35, 35)
    
    # Component 2: Harm penalty (0-40 points deduction)
    harm_penalty = 0
    harm_reason = []
    ing_lower = ingredient.lower()
    
    for harmful in HARM_LIST:
        if harmful in ing_lower:
            harm_penalty = 40
            harm_reason.append(f"Contains {harmful}")
            break
    
    # Component 3: Benefit boost (0-15 points)
    benefit_boost = 0
    benefit_reason = []
    
    for beneficial in BENEFIT_LIST:
        if beneficial in ing_lower:
            benefit_boost = 15
            benefit_reason.append(f"Contains {beneficial}")
            break
    
    # Base score (neutral ingredients start at 60)
    base_score = 60
    
    # Final score
    health_score = base_score + freq_points - harm_penalty + benefit_boost
    health_score = max(0, min(100, health_score))
    
    # Determine category
    if health_score >= 76:
        category = 'beneficial'
    elif health_score >= 51:
        category = 'neutral'
    elif health_score >= 26:
        category = 'concerning'
    else:
        category = 'avoid'
    
    # Build reason string
    reasons = []
    if harm_reason:
        reasons.extend(harm_reason)
    if benefit_reason:
        reasons.extend(benefit_reason)
    if frequency_score > 0.5:
        reasons.append("Very common in clean products")
    elif frequency_score > 0.2:
        reasons.append("Common in skincare")
    
    reason = "; ".join(reasons) if reasons else "Standard ingredient"
    
    return {
        'ingredient': ingredient,
        'health_score': round(health_score, 1),
        'frequency_score': round(frequency_score, 4),
        'harm_penalty': harm_penalty,
        'benefit_boost': benefit_boost,
        'category': category,
        'reason': reason
    }

def main():
    """Main processing pipeline"""
    print("=" * 60)
    print("BottleScan - Simplified Dataset Preprocessing")
    print("=" * 60)
    
    # Load dataset
    print("Loading dataset...")
    df = pd.read_csv(KAGGLE_CSV_PATH)
    print(f"Loaded {len(df)} products")
    print(f"Columns: {df.columns.tolist()}")
    
    # Use clean_ingreds column
    ingredient_col = 'clean_ingreds'
    
    # Build ingredient index
    print("\nBuilding ingredient index...")
    all_ingredients = []
    product_count = defaultdict(int)
    
    for idx, row in df.iterrows():
        ingredients = parse_ingredient_string(row[ingredient_col])
        all_ingredients.extend(ingredients)
        
        for ing in set(ingredients):
            product_count[ing] += 1
    
    # Count frequency
    frequency_counter = Counter(all_ingredients)
    
    # Build dataframe
    ingredient_data = []
    for ing, freq in frequency_counter.items():
        ingredient_data.append({
            'ingredient': ing,
            'total_occurrences': freq,
            'product_count': product_count[ing],
            'frequency_score': product_count[ing] / len(df)
        })
    
    ingredient_df = pd.DataFrame(ingredient_data)
    ingredient_df = ingredient_df.sort_values('total_occurrences', ascending=False)
    
    print(f"Found {len(ingredient_df)} unique ingredients")
    print(f"Top 10 ingredients:")
    print(ingredient_df.head(10))
    
    # Compute health scores
    print("\nComputing health scores...")
    health_db = {}
    
    for idx, row in ingredient_df.iterrows():
        ing = row['ingredient']
        freq_score = row['frequency_score']
        score_data = compute_health_score(ing, freq_score)
        health_db[ing] = score_data
        
        if idx % 100 == 0:
            print(f"Processed {idx}/{len(ingredient_df)} ingredients...")
    
    print(f"Completed health scoring for {len(health_db)} ingredients")
    
    # Save health database
    print("\nSaving outputs...")
    with open(OUTPUT_INGREDIENT_DB, 'w') as f:
        json.dump(health_db, f, indent=2)
    print(f"Saved health database to {OUTPUT_INGREDIENT_DB}")
    
    # Generate summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    categories = defaultdict(int)
    for data in health_db.values():
        categories[data['category']] += 1
    
    print(f"\nTotal unique ingredients: {len(health_db)}")
    print(f"Beneficial: {categories['beneficial']}")
    print(f"Neutral: {categories['neutral']}")
    print(f"Concerning: {categories['concerning']}")
    print(f"Avoid: {categories['avoid']}")
    
    print("\nTop 10 healthiest ingredients:")
    sorted_healthy = sorted(health_db.items(), key=lambda x: x[1]['health_score'], reverse=True)
    for ing, data in sorted_healthy[:10]:
        print(f"  {ing}: {data['health_score']} - {data['reason']}")
    
    print("\nTop 10 ingredients to avoid:")
    sorted_harmful = sorted(health_db.items(), key=lambda x: x[1]['health_score'])
    for ing, data in sorted_harmful[:10]:
        print(f"  {ing}: {data['health_score']} - {data['reason']}")
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
