# product_recommender.py
from typing import List, Optional, Dict
import json
import os

class ProductRecommender:
    def __init__(self):
        self.product_database = self._load_product_database()
    
    def _load_product_database(self):
        """Load product database - mock data for now"""
        return [
            {
                'product_id': '1',
                'brand': 'CeraVe',
                'name': 'Hydrating Facial Cleanser',
                'category': 'cleanser',
                'skin_type': ['normal', 'dry', 'combination'],
                'concerns': ['hydration', 'sensitive'],
                'ingredients': ['aqua', 'glycerin', 'niacinamide', 'hyaluronic acid'],
                'health_score': 85,
                'price_range': '$10-$20',
                'average_price': 14.99,
                'currency': 'USD',
                'url': 'https://www.cerave.com',
                'image_url': '',
                'rating': 4.5,
                'review_count': 15420,
                'availability': 'in_stock'
            },
            {
                'product_id': '2',
                'brand': 'The Ordinary',
                'name': 'Niacinamide 10% + Zinc 1%',
                'category': 'serum',
                'skin_type': ['oily', 'combination', 'acne-prone'],
                'concerns': ['acne', 'texture', 'pores'],
                'ingredients': ['aqua', 'niacinamide', 'zinc', 'hyaluronic acid'],
                'health_score': 90,
                'price_range': '$5-$10',
                'average_price': 5.99,
                'currency': 'USD',
                'url': 'https://theordinary.com',
                'image_url': '',
                'rating': 4.3,
                'review_count': 28930,
                'availability': 'in_stock'
            },
            {
                'product_id': '3',
                'brand': 'La Roche-Posay',
                'name': 'Toleriane Double Repair Face Moisturizer',
                'category': 'moisturizer',
                'skin_type': ['sensitive', 'dry', 'normal'],
                'concerns': ['sensitive', 'hydration', 'barrier'],
                'ingredients': ['aqua', 'glycerin', 'niacinamide', 'ceramide'],
                'health_score': 88,
                'price_range': '$15-$25',
                'average_price': 19.99,
                'currency': 'USD',
                'url': 'https://www.laroche-posay.us',
                'image_url': '',
                'rating': 4.6,
                'review_count': 12450,
                'availability': 'in_stock'
            }
        ]
    
    def find_substitute_products(
        self,
        flagged_ingredients: List[str],
        original_category: Optional[str] = None,
        skin_type: Optional[List[str]] = None,
        concerns: Optional[List[str]] = None,
        max_results: int = 5
    ):
        """Find products that don't contain flagged ingredients"""
        flagged_lower = [ing.lower() for ing in flagged_ingredients]
        
        # Filter products that don't have flagged ingredients
        filtered_products = []
        for product in self.product_database:
            product_ings = [ing.lower() for ing in product['ingredients']]
            if not any(flagged in product_ings for flagged in flagged_lower):
                filtered_products.append(product)
        
        # Calculate scores and add them to products
        results = []
        for product in filtered_products[:max_results]:
            substitute_score = self._calculate_substitute_score(product, flagged_ingredients)
            similarity_score = 0.85  # Mock similarity
            health_boost = product['health_score'] - 60  # Mock boost
            
            results.append({
                **product,
                'substitute_score': substitute_score,
                'similarity_score': similarity_score,
                'health_boost': health_boost
            })
        
        return results
    
    def _calculate_substitute_score(self, product, flagged_ingredients):
        """Calculate how good a substitute this product is"""
        base_score = 0.7
        base_score += (product['rating'] / 5.0) * 0.2
        base_score += (product['health_score'] / 100.0) * 0.1
        return min(base_score, 1.0)
    
    def get_price_comparison(self, product_id: str):
        """Get price comparison for a product"""
        # Find product
        product = next((p for p in self.product_database if p['product_id'] == product_id), None)
        
        if not product:
            return {"error": "Product not found"}
        
        # Mock price sources
        base_price = product['average_price']
        return {
            'product_id': product_id,
            'product_name': product['name'],
            'brand': product['brand'],
            'current_price': base_price,
            'currency': product['currency'],
            'price_sources': [
                {'retailer': 'Amazon', 'price': base_price * 0.95, 'shipping': 'Free', 'in_stock': True, 'url': '#'},
                {'retailer': 'Sephora', 'price': base_price, 'shipping': 'Free over $50', 'in_stock': True, 'url': '#'},
                {'retailer': 'Ulta', 'price': base_price * 1.05, 'shipping': '$5.95', 'in_stock': True, 'url': '#'},
                {'retailer': 'Target', 'price': base_price * 0.92, 'shipping': 'Free with RedCard', 'in_stock': False, 'url': '#'},
            ],
            'price_trend': {
                'direction': 'stable',
                'change_percent': 0,
                'lowest_30_days': base_price * 0.90
            }
        }
    
    def get_ingredient_alternatives(self, ingredient: str):
        """Get alternative ingredients and products"""
        return [
            {
                'alternative': 'sodium cocoyl isethionate',
                'score': 78,
                'reason': 'Gentle coconut-derived surfactant',
                'products_using': ['product_1', 'product_2']
            }
        ]

# Create singleton instance
product_recommender = ProductRecommender()