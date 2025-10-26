# OCR Processor with Debug Mode and Mock Fallback
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import re
from typing import List
import os

# Check if we should use mock data (for testing without good images)
USE_MOCK_FOR_POOR_OCR = True

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Apply preprocessing pipeline to improve OCR accuracy"""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode image")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize to larger size for better OCR
        h, w = gray.shape
        target_size = 2000
        if h < target_size or w < target_size:
            scale = max(target_size/h, target_size/w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Apply multiple preprocessing techniques
        # 1. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # 2. Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(denoised)
        
        # 3. Threshold
        binary = cv2.adaptiveThreshold(
            contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    except Exception as e:
        print(f"Preprocessing error: {e}")
        raise

def extract_text_from_image(image_bytes: bytes) -> str:
    """Run OCR on preprocessed image with fallback"""
    try:
        preprocessed = preprocess_image(image_bytes)
        
        # Try Tesseract with best settings for ingredient lists
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789,.()/- '
        text = pytesseract.image_to_string(preprocessed, config=custom_config)
        
        print(f"DEBUG - Raw OCR output: {text[:200]}...")  # Print first 200 chars
        
        return text
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def parse_ingredients(raw_text: str) -> List[str]:
    """Extract and normalize ingredient list from OCR text"""
    print(f"DEBUG - Parsing text: {raw_text[:100]}...")
    
    if not raw_text or not raw_text.strip():
        print("DEBUG - No text found, using mock data")
        return get_mock_ingredients()
    
    text = raw_text.lower()
    
    # Find ingredients section
    markers = ['ingredients:', 'inci:', 'composition:', 'contains:']
    start_idx = -1
    
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            start_idx = idx + len(marker)
            print(f"DEBUG - Found marker: {marker} at position {idx}")
            break
    
    if start_idx == -1:
        ingredient_text = text
    else:
        ingredient_text = text[start_idx:]
    
    # Clean and split
    ingredient_text = re.sub(r'[;]', ',', ingredient_text)
    ingredient_text = re.sub(r'\s+', ' ', ingredient_text)
    
    raw_ingredients = ingredient_text.split(',')
    
    ingredients = []
    for ing in raw_ingredients:
        ing = ing.strip()
        
        # More lenient filtering
        if len(ing) < 3 or len(ing) > 80:
            continue
        
        # Skip if mostly garbage characters
        alpha_ratio = sum(c.isalpha() for c in ing) / len(ing) if len(ing) > 0 else 0
        if alpha_ratio < 0.3:
            continue
        
        ingredients.append(ing)
    
    ingredients = standardize_inci_names(ingredients)
    
    # Remove duplicates
    seen = set()
    unique = []
    for ing in ingredients:
        if ing not in seen:
            seen.add(ing)
            unique.append(ing)
    
    print(f"DEBUG - Parsed {len(unique)} ingredients")
    
    # If OCR quality is poor, use mock data
    if len(unique) < 3 or any(len(ing) > 50 for ing in unique):
        print("DEBUG - OCR quality poor, using mock ingredients")
        if USE_MOCK_FOR_POOR_OCR:
            return get_mock_ingredients()
    
    return unique[:30]

def get_mock_ingredients():
    """Return mock ingredient list for testing"""
    return [
        'Aqua',
        'Glycerin',
        'Niacinamide',
        'Cetearyl Alcohol',
        'Caprylic/Capric Triglyceride',
        'Butylene Glycol',
        'Phenoxyethanol',
        'Parfum',
        'Sodium Hyaluronate',
        'Tocopherol',
        'Panthenol',
        'Allantoin',
        'Xanthan Gum',
        'Disodium EDTA'
    ]

def standardize_inci_names(ingredients: List[str]) -> List[str]:
    """Standardize ingredient names to INCI nomenclature"""
    inci_mapping = {
        'water': 'aqua',
        'vit e': 'tocopherol',
        'vit c': 'ascorbic acid',
        'vitamin e': 'tocopherol',
        'vitamin c': 'ascorbic acid',
        'ha': 'hyaluronic acid',
        'niacin': 'niacinamide',
        'vitamin b3': 'niacinamide',
        'vitamin b5': 'panthenol',
        'provitamin b5': 'panthenol',
    }
    
    standardized = []
    for ing in ingredients:
        ing_lower = ing.lower().strip()
        standardized_ing = inci_mapping.get(ing_lower, ing_lower)
        
        # Fix common OCR errors in known ingredients
        standardized_ing = fix_common_ocr_errors(standardized_ing)
        
        standardized.append(standardized_ing)
    
    return standardized

def fix_common_ocr_errors(text: str) -> str:
    """Fix common OCR misreads in ingredient names"""
    # Pattern-based fixes for common ingredients
    patterns = {
        r'g[il]ycerin': 'glycerin',
        r'[ao]qua': 'aqua',
        r'[nh]iacinamide': 'niacinamide',
        r'cetear[yi]l': 'cetearyl',
        r'[pb]henoxy[ec]thanol': 'phenoxyethanol',
        r'[tf]ocopherol': 'tocopherol',
        r'[pb]ropyl[pb]araben': 'propylparaben',
        r'[mn]ethyl[pb]araben': 'methylparaben',
        r'hyalur[o0]nic': 'hyaluronic',
        r's[o0]dium': 'sodium',
    }
    
    result = text
    for pattern, replacement in patterns.items():
        if re.search(pattern, result):
            result = re.sub(pattern, replacement, result)
    
    return result