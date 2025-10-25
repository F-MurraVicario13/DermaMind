# Kaggle Skincare Dataset Preprocessing
# This script processes the Kaggle skincare dataset to build ingredient health scores
# Install: pip install pandas numpy scikit-learn sentence-transformers

import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import json
from sentence_transformers import SentenceTransformer

# ==================== Configuration ====================

KAGGLE_CSV_PATH = "raw/skincare_products_clean.csv"  # Update with your path
OUTPUT_INGREDIENT_DB = "processed/ingredient_health_scores.json"
OUTPUT_EMBEDDINGS = "processed/ingredient_embeddings.npy"
OUTPUT_PRODUCT_DB = "processed/product_database.json"

# Known harmful ingredients (expand this list)
HARM_LIST = {
    # Parabens
    'methylparaben', 'propylparaben', 'butylparaben', 'ethylparaben',
    'isobutylparaben',
    # Sulfates
    'sodium lauryl sulfate', 'sodium laureth sulfate', 'sls', 'sles',
    # Phthalates
    'phthalate', 'dibutyl phthalate', 'dbp',
    # Fragrances
    'parfum', 'fragrance', 'synthetic fragrance',
    # Alcohols (drying types)
    'alcohol denat', 'isopropyl alcohol', 'sd alcohol',
    # Formaldehyde releasers
    'dmdm hydantoin', 'imidazolidinyl urea', 'quaternium-15',
    # Others
    'triclosan', 'triclocarban', 'toluene', 'coal tar'
}

# Known beneficial ingredients
BENEFIT_LIST = {
    'niacinamide', 'hyaluronic acid', 'glycerin', 'tocopherol', 'tocopheryl acetate',
    'ascorbic acid', 'retinol', 'retinyl palmitate', 'ceramide', 'peptide',
    'allantoin', 'panthenol', 'beta glucan', 'centella asiatica', 'aloe vera',
    'squalane', 'alpha arbutin', 'kojic acid', 'azelaic acid', 'salicylic acid',
    'lactic acid', 'mandelic acid', 'ferulic acid', 'resveratrol'
}

# ==================== Data Loading ====================

def load_kaggle_dataset(csv_path: str) -> pd.DataFrame:
    """Load the Kaggle skincare dataset"""
    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} products")
    print(f"Columns: {df.columns.tolist()}")
    
    # Expected columns: Brand, Product, Ingredients (adjust based on actual dataset)
    return df

# ==================== Ingredient Parsing ====================

def parse_ingredient_string(ingredient_str: str) -> List[str]:
    """Parse ingredient string into list - handles both comma-separated and list format"""
    if pd.isna(ingredient_str):
        return []
    
    # Check if it's a string representation of a Python list
    if ingredient_str.startswith("['") and ingredient_str.endswith("']"):
        try:
            # Use ast.literal_eval to safely parse the list
            import ast
            ingredients = ast.literal_eval(ingredient_str)
            if isinstance(ingredients, list):
                return [ing.strip().lower() for ing in ingredients if ing and len(ing) > 2]
        except:
            pass
    
    # Fallback to comma/semicolon splitting
    ingredients = re.split(r'[,;]', str(ingredient_str))
    
    # Clean each ingredient
    cleaned = []
    for ing in ingredients:
        # Remove parenthetical content (concentrations, INCIs)
        ing = re.sub(r'\([^)]*\)', '', ing)
        # Remove brackets
        ing = re.sub(r'\[[^\]]*\]', '', ing)
        # Strip whitespace and lowercase
        ing = ing.strip().lower()
        # Remove empty strings
        if ing and len(ing) > 2:
            cleaned.append(ing)
    
    return cleaned

def build_ingredient_index(df: pd.DataFrame, ingredient_col: str = 'Ingredients') -> pd.DataFrame:
    """Build index of all unique ingredients with frequency counts"""
    print("\nBuilding ingredient index...")
    
    all_ingredients = []
    product_count = defaultdict(int)
    
    for idx, row in df.iterrows():
        ingredients = parse_ingredient_string(row[ingredient_col])
        all_ingredients.extend(ingredients)
        
        # Track which products contain each ingredient
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
            'frequency_score': product_count[ing] / len(df)  # Normalize by total products
        })
    
    ingredient_df = pd.DataFrame(ingredient_data)
    ingredient_df = ingredient_df.sort_values('total_occurrences', ascending=False)
    
    print(f"Found {len(ingredient_df)} unique ingredients")
    print(f"Top 10 ingredients:\n{ingredient_df.head(10)}")
    
    return ingredient_df

# ==================== Health Score Computation ====================

def compute_health_score(ingredient: str, ingredient_df: pd.DataFrame) -> Dict:
    """Compute multi-factor health score for an ingredient"""
    
    # Get ingredient data
    ing_data = ingredient_df[ingredient_df['ingredient'] == ingredient]
    
    if len(ing_data) == 0:
        # Unknown ingredient
        return {
            'ingredient': ingredient,
            'health_score': 60,
            'frequency_score': 0,
            'harm_penalty': 0,
            'benefit_boost': 0,
            'category': 'neutral',
            'reason': 'Limited data available'
        }
    
    ing_row = ing_data.iloc[0]
    frequency_score = ing_row['frequency_score']
    
    # Component 1: Frequency score (0-35 points)
    # Common in clean products = higher score
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
    health_score = max(0, min(100, health_score))  # Clamp to 0-100
    
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

def build_health_database(ingredient_df: pd.DataFrame) -> Dict:
    """Build complete health score database"""
    print("\nComputing health scores for all ingredients...")
    
    health_db = {}
    
    for idx, row in ingredient_df.iterrows():
        ing = row['ingredient']
        score_data = compute_health_score(ing, ingredient_df)
        health_db[ing] = score_data
        
        if idx % 100 == 0:
            print(f"Processed {idx}/{len(ingredient_df)} ingredients...")
    
    print(f"Completed health scoring for {len(health_db)} ingredients")
    return health_db

# ==================== Embedding Generation ====================

def generate_embeddings(ingredients: List[str]) -> np.ndarray:
    """Generate semantic embeddings for ingredient similarity search"""
    print("\nGenerating embeddings for ingredient similarity...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    embeddings = model.encode(ingredients, show_progress_bar=True)
    
    print(f"Generated embeddings with shape: {embeddings.shape}")
    return embeddings

# ==================== Co-occurrence Analysis ====================

def analyze_ingredient_cooccurrence(df: pd.DataFrame, ingredient_col: str = 'Ingredients') -> Dict:
    """Analyze which ingredients commonly appear together"""
    print("\nAnalyzing ingredient co-occurrence patterns...")
    
    cooccurrence = defaultdict(Counter)
    
    for idx, row in df.iterrows():
        ingredients = parse_ingredient_string(row[ingredient_col])
        
        # For each pair of ingredients in the product
        for i, ing1 in enumerate(ingredients):
            for ing2 in ingredients[i+1:]:
                cooccurrence[ing1][ing2] += 1
                cooccurrence[ing2][ing1] += 1
    
    # Convert to dict of dicts
    cooccurrence_dict = {k: dict(v.most_common(10)) for k, v in cooccurrence.items()}
    
    print(f"Analyzed co-occurrence for {len(cooccurrence_dict)} ingredients")
    return cooccurrence_dict

# ==================== Substitute Suggestion Builder ====================

def build_substitute_suggestions(health_db: Dict, cooccurrence: Dict) -> Dict:
    """Build substitute suggestions for harmful ingredients"""
    print("\nBuilding substitute recommendations...")
    
    substitutes = {}
    
    # Get all harmful ingredients
    harmful_ingredients = [
        ing for ing, data in health_db.items() 
        if data['category'] in ['concerning', 'avoid']
    ]
    
    print(f"Found {len(harmful_ingredients)} ingredients needing substitutes")
    
    # For each harmful ingredient, find alternatives
    for harmful in harmful_ingredients:
        # Get co-occurring ingredients
        cooccur = cooccurrence.get(harmful, {})
        
        # Find healthier alternatives that serve similar function
        candidates = []
        for cooccur_ing, count in cooccur.items():
            if cooccur_ing in health_db:
                cooccur_data = health_db[cooccur_ing]
                if cooccur_data['health_score'] > 65:  # Only suggest healthy alternatives
                    candidates.append({
                        'name': cooccur_ing,
                        'score': cooccur_data['health_score'],
                        'role': 'Similar functional role',
                        'confidence': min(0.95, count / 100)  # Based on co-occurrence frequency
                    })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        substitutes[harmful] = candidates[:5]  # Top 5 substitutes
    
    print(f"Generated substitutes for {len(substitutes)} ingredients")
    return substitutes

# ==================== Main Processing Pipeline ====================

def main():
    """Main processing pipeline"""
    print("=" * 60)
    print("BottleScan - Kaggle Dataset Preprocessing")
    print("=" * 60)
    
    # Step 1: Load dataset
    df = load_kaggle_dataset(KAGGLE_CSV_PATH)
    
    # Detect ingredient column (common names)
    ingredient_col = None
    for col in ['clean_ingreds', 'Ingredients', 'ingredients', 'Ingredient', 'ingredient_list']:
        if col in df.columns:
            ingredient_col = col
            break
    
    if ingredient_col is None:
        print("ERROR: Could not find ingredient column. Available columns:")
        print(df.columns.tolist())
        return
    
    print(f"Using ingredient column: '{ingredient_col}'")
    
    # Step 2: Build ingredient index
    ingredient_df = build_ingredient_index(df, ingredient_col)
    
    # Step 3: Compute health scores
    health_db = build_health_database(ingredient_df)
    
    # Step 4: Analyze co-occurrence
    cooccurrence = analyze_ingredient_cooccurrence(df, ingredient_col)
    
    # Step 5: Build substitutes
    substitutes = build_substitute_suggestions(health_db, cooccurrence)
    
    # Step 6: Generate embeddings
    ingredient_list = ingredient_df['ingredient'].tolist()
    embeddings = generate_embeddings(ingredient_list)
    
    # Step 7: Save outputs
    print("\nSaving outputs...")
    
    # Save health database
    with open(OUTPUT_INGREDIENT_DB, 'w') as f:
        json.dump(health_db, f, indent=2)
    print(f"Saved health database to {OUTPUT_INGREDIENT_DB}")
    
    # Save embeddings
    np.save(OUTPUT_EMBEDDINGS, embeddings)
    print(f"Saved embeddings to {OUTPUT_EMBEDDINGS}")
    
    # Save substitute recommendations
    with open('processed/ingredient_substitutes.json', 'w') as f:
        json.dump(substitutes, f, indent=2)
    print(f"Saved substitutes to processed/ingredient_substitutes.json")
    
    # Save co-occurrence data
    with open('processed/ingredient_cooccurrence.json', 'w') as f:
        json.dump(cooccurrence, f, indent=2)
    print(f"Saved co-occurrence data to processed/ingredient_cooccurrence.json")
    
    # Step 8: Generate summary statistics
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
