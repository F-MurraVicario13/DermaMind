# OCR Processor - Image preprocessing & OCR extraction
# Handles image preprocessing and text extraction from product labels

import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import re
from typing import List

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Apply preprocessing pipeline to improve OCR accuracy"""
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize if too small
    h, w = gray.shape
    if h < 500 or w < 500:
        scale = max(500/h, 500/w)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Morphological operations to connect text
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return morph

def extract_text_from_image(image_bytes: bytes) -> str:
    """Run OCR on preprocessed image"""
    preprocessed = preprocess_image(image_bytes)
    
    # Configure Tesseract
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(preprocessed, config=custom_config)
    
    return text

def parse_ingredients(raw_text: str) -> List[str]:
    """Extract and normalize ingredient list from OCR text"""
    # Common patterns: "Ingredients:", "INCI:", etc.
    text = raw_text.lower()
    
    # Find ingredients section
    markers = ['ingredients:', 'inci:', 'composition:']
    start_idx = -1
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            start_idx = idx + len(marker)
            break
    
    if start_idx == -1:
        # No marker found, use entire text
        ingredient_text = text
    else:
        ingredient_text = text[start_idx:]
    
    # Split by common delimiters
    ingredient_text = re.sub(r'[;,\n]', ',', ingredient_text)
    
    # Extract ingredients
    ingredients = [ing.strip() for ing in ingredient_text.split(',')]
    
    # Filter out empty and very short strings
    ingredients = [ing for ing in ingredients if len(ing) > 2]
    
    # Basic spell correction and standardization
    ingredients = standardize_inci_names(ingredients)
    
    return ingredients

def standardize_inci_names(ingredients: List[str]) -> List[str]:
    """Standardize ingredient names to INCI nomenclature"""
    # Dictionary of common variations -> standard INCI names
    inci_mapping = {
        'water': 'aqua',
        'vit e': 'tocopherol',
        'vit c': 'ascorbic acid',
        'vitamin e': 'tocopherol',
        'vitamin c': 'ascorbic acid',
        'ha': 'hyaluronic acid',
        'niacin': 'niacinamide',
    }
    
    standardized = []
    for ing in ingredients:
        ing_lower = ing.lower().strip()
        standardized_ing = inci_mapping.get(ing_lower, ing_lower)
        standardized.append(standardized_ing)
    
    return standardized
