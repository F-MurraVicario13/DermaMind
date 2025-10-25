import React, { useState } from 'react';
import { Camera, Upload, CheckCircle, AlertTriangle, XCircle, Sparkles, Info, ShoppingCart, DollarSign, Star, ExternalLink } from 'lucide-react';

const BottleScanDemo = () => {
  const [step, setStep] = useState('upload');
  const [analysis, setAnalysis] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [productRecommendations, setProductRecommendations] = useState([]);
  const [priceComparison, setPriceComparison] = useState(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Mock health scores based on your spec
  const healthScoreDB = {
    'niacinamide': { score: 90, reason: 'Beneficial vitamin B3; skin brightening and barrier support' },
    'glycerin': { score: 88, reason: 'Excellent humectant; hydrates and improves skin barrier' },
    'hyaluronic acid': { score: 92, reason: 'Superior hydration; holds 1000x its weight in water' },
    'aqua': { score: 95, reason: 'Water - universal solvent, completely safe' },
    'butylene glycol': { score: 70, reason: 'Humectant and penetration enhancer; generally safe' },
    'tocopherol': { score: 85, reason: 'Vitamin E; antioxidant with skin-protective properties' },
    'methylparaben': { score: 15, reason: 'Preservative with endocrine disruption concerns' },
    'propylparaben': { score: 12, reason: 'Paraben preservative; potential hormone disruptor' },
    'parfum': { score: 20, reason: 'Fragrance - common allergen, often contains phthalates' },
    'fragrance': { score: 20, reason: 'Synthetic fragrance - allergen risk, no functional benefit' },
    'sodium lauryl sulfate': { score: 25, reason: 'Harsh surfactant; can strip natural oils and irritate' },
    'phenoxyethanol': { score: 45, reason: 'Preservative with moderate safety concerns' },
    'retinol': { score: 82, reason: 'Vitamin A derivative; anti-aging but can be irritating' },
    'ascorbic acid': { score: 88, reason: 'Vitamin C; brightening and antioxidant properties' }
  };

  const substitutes = {
    'methylparaben': [
      { name: 'leucidal liquid', score: 75, type: 'Fermented radish root; natural preservative' },
      { name: 'sodium benzoate', score: 65, type: 'Food-grade preservative; safer alternative' }
    ],
    'parfum': [
      { name: 'fragrance-free formulation', score: 95, type: 'Remove entirely for sensitive skin' },
      { name: 'essential oil blend', score: 60, type: 'Natural fragrance (still potential allergen)' }
    ],
    'sodium lauryl sulfate': [
      { name: 'sodium cocoyl isethionate', score: 78, type: 'Gentle coconut-derived surfactant' },
      { name: 'decyl glucoside', score: 82, type: 'Mild sugar-based cleanser' }
    ]
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        setTimeout(() => simulateOCR(), 1500);
      };
      reader.readAsDataURL(file);
      setStep('processing');
    }
  };

  const simulateOCR = () => {
    const mockIngredients = [
      'Aqua', 'Glycerin', 'Niacinamide', 'Butylene Glycol', 
      'Phenoxyethanol', 'Parfum', 'Methylparaben'
    ];
    setStep('results');
    analyzeIngredients(mockIngredients);
  };

  const analyzeIngredients = (ingList) => {
    const analyzed = ingList.map(ing => {
      const normalized = ing.toLowerCase();
      const data = healthScoreDB[normalized] || { 
        score: 60, 
        reason: 'Common ingredient; limited safety data available' 
      };
      return {
        ingredient: ing,
        normalized,
        ...data
      };
    });

    const avgScore = Math.round(
      analyzed.reduce((sum, item) => sum + item.score, 0) / analyzed.length
    );

    const flaggedIngredients = analyzed.filter(i => i.score < 50);

    setAnalysis({
      ingredients: analyzed,
      productScore: avgScore,
      flaggedIngredients: flaggedIngredients
    });

    // If there are flagged ingredients, get product recommendations
    if (flaggedIngredients.length > 0) {
      getProductRecommendations(flaggedIngredients.map(i => i.ingredient));
    }
  };

  const getProductRecommendations = async (flaggedIngredients) => {
    console.log('Fetching product recommendations for:', flaggedIngredients);
    setLoadingRecommendations(true);
    setApiError(null);
    
    try {
      const response = await fetch('http://localhost:8000/recommend-products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          flagged_ingredients: flaggedIngredients,
          original_category: 'serum', // Default category
          skin_type: ['combination', 'oily'],
          concerns: ['acne', 'texture'],
          max_results: 5
        })
      });
      
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const recommendations = await response.json();
        console.log('Received recommendations:', recommendations);
        setProductRecommendations(recommendations);
        setShowRecommendations(true);
      } else {
        const errorText = await response.text();
        console.error('API Error:', response.status, errorText);
        setApiError(`API Error: ${response.status} - ${errorText}`);
        setProductRecommendations([]);
        setShowRecommendations(true);
      }
    } catch (error) {
      console.error('Network Error fetching product recommendations:', error);
      setApiError(`Network Error: ${error.message}`);
      setProductRecommendations([]);
      setShowRecommendations(true);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const getPriceComparison = async (productId) => {
    console.log('Fetching price comparison for product:', productId);
    
    try {
      const response = await fetch(`http://localhost:8000/price-comparison/${productId}`);
      console.log('Price comparison response status:', response.status);
      
      if (response.ok) {
        const priceData = await response.json();
        console.log('Received price data:', priceData);
        setPriceComparison(priceData);
      } else {
        console.error('Price comparison API Error:', response.status, await response.text());
      }
    } catch (error) {
      console.error('Network Error fetching price comparison:', error);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 76) return 'text-green-600';
    if (score >= 51) return 'text-yellow-600';
    if (score >= 26) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score) => {
    if (score >= 76) return <CheckCircle className="w-5 h-5" />;
    if (score >= 51) return <Info className="w-5 h-5" />;
    if (score >= 26) return <AlertTriangle className="w-5 h-5" />;
    return <XCircle className="w-5 h-5" />;
  };

  const getScoreLabel = (score) => {
    if (score >= 76) return 'Healthy / Preferred';
    if (score >= 51) return 'Generally Okay';
    if (score >= 26) return 'Use with Caution';
    return 'Avoid';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-3">
            <Sparkles className="w-8 h-8 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-800">BottleScan</h1>
          </div>
          <p className="text-gray-600">Skincare OCR & Ingredient Health Advisor</p>
          <p className="text-sm text-gray-500 mt-2">Powered by Kaggle Skincare Dataset</p>
        </div>

        {/* Upload Section */}
        {step === 'upload' && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold mb-6 text-center">Upload Product Label</h2>
            
            <div className="border-3 border-dashed border-indigo-300 rounded-xl p-12 text-center hover:border-indigo-500 transition-colors">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Camera className="w-16 h-16 mx-auto mb-4 text-indigo-500" />
                <p className="text-lg font-medium text-gray-700 mb-2">
                  Take a photo or upload an image
                </p>
                <p className="text-sm text-gray-500">
                  Capture the ingredient list on your product
                </p>
              </label>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Demo Mode:</strong> This demo simulates OCR processing. 
                Full implementation uses Tesseract OCR with preprocessing pipeline.
              </p>
            </div>
          </div>
        )}

        {/* Processing */}
        {step === 'processing' && (
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="animate-pulse">
              <Upload className="w-16 h-16 mx-auto mb-4 text-indigo-500" />
              <h2 className="text-2xl font-semibold mb-2">Processing Image...</h2>
              <p className="text-gray-600">
                Applying OCR and extracting ingredients
              </p>
            </div>
            {imagePreview && (
              <img 
                src={imagePreview} 
                alt="Preview" 
                className="mt-6 max-w-sm mx-auto rounded-lg shadow"
              />
            )}
          </div>
        )}

        {/* Results */}
        {step === 'results' && analysis && (
          <div className="space-y-6">
            {/* Overall Score Card */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold">Product Analysis</h2>
                <button
                  onClick={() => {
                    setStep('upload');
                    setAnalysis(null);
                    setImagePreview(null);
                    setProductRecommendations([]);
                    setPriceComparison(null);
                    setShowRecommendations(false);
                    setLoadingRecommendations(false);
                    setApiError(null);
                  }}
                  className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors"
                >
                  Scan Another
                </button>
              </div>

              <div className="flex items-center gap-4 mb-6">
                <div className={`text-6xl font-bold ${getScoreColor(analysis.productScore)}`}>
                  {analysis.productScore}
                </div>
                <div>
                  <div className={`flex items-center gap-2 ${getScoreColor(analysis.productScore)} font-semibold`}>
                    {getScoreIcon(analysis.productScore)}
                    {getScoreLabel(analysis.productScore)}
                  </div>
                  <p className="text-gray-600 text-sm mt-1">Overall Product Score</p>
                </div>
              </div>

              {analysis.flaggedIngredients.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="font-semibold text-red-800 mb-2">
                    ⚠️ {analysis.flaggedIngredients.length} Concerning Ingredient(s) Found
                  </p>
                  <p className="text-sm text-red-700 mb-3">
                    {analysis.flaggedIngredients.map(i => i.ingredient).join(', ')}
                  </p>
                  <button
                    onClick={() => setShowRecommendations(!showRecommendations)}
                    disabled={loadingRecommendations}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <ShoppingCart className="w-4 h-4" />
                    {loadingRecommendations ? 'Loading...' : (showRecommendations ? 'Hide' : 'Find')} Product Substitutes
                  </button>
                </div>
              )}
            </div>

            {/* Ingredient Breakdown */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h3 className="text-xl font-semibold mb-4">Ingredient Breakdown</h3>
              <div className="space-y-3">
                {analysis.ingredients.map((ing, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className={`${getScoreColor(ing.score)}`}>
                          {getScoreIcon(ing.score)}
                        </span>
                        <div>
                          <p className="font-semibold text-gray-800">{ing.ingredient}</p>
                          <p className={`text-sm font-medium ${getScoreColor(ing.score)}`}>
                            Score: {ing.score}/100
                          </p>
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 pl-8">{ing.reason}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Product Recommendations */}
            {showRecommendations && (
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold">🛍️ Product Substitutes & Pricing Guide</h3>
                  <button
                    onClick={() => setShowRecommendations(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>
                
                {loadingRecommendations && (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">Loading product recommendations...</p>
                  </div>
                )}
                
                {apiError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <p className="text-red-800 font-semibold">Error loading recommendations:</p>
                    <p className="text-red-700 text-sm mt-1">{apiError}</p>
                    <button
                      onClick={() => {
                        setApiError(null);
                        const flaggedIngredients = analysis.flaggedIngredients.map(i => i.ingredient);
                        getProductRecommendations(flaggedIngredients);
                      }}
                      className="mt-2 bg-red-100 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-200"
                    >
                      Retry
                    </button>
                  </div>
                )}
                
                {!loadingRecommendations && !apiError && productRecommendations.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-600">No product substitutes found for the flagged ingredients.</p>
                    <p className="text-sm text-gray-500 mt-2">Try different ingredients or check back later.</p>
                  </div>
                )}
                
                {!loadingRecommendations && !apiError && productRecommendations.length > 0 && (
                  <div className="grid gap-6 md:grid-cols-2">
                  {productRecommendations.map((product, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium text-gray-600">{product.brand}</span>
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {product.category}
                            </span>
                          </div>
                          <h4 className="font-semibold text-gray-800 mb-2">{product.name}</h4>
                          
                          <div className="flex items-center gap-4 mb-3">
                            <div className="flex items-center gap-1">
                              <Star className="w-4 h-4 text-yellow-500 fill-current" />
                              <span className="text-sm font-medium">{product.rating}</span>
                              <span className="text-xs text-gray-500">({product.review_count.toLocaleString()})</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm text-green-600">Health Score: {product.health_score}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">Skin Type:</span>
                          <div className="flex gap-1">
                            {product.skin_type.map((type, i) => (
                              <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                {type}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">Concerns:</span>
                          <div className="flex gap-1 flex-wrap">
                            {product.concerns.map((concern, i) => (
                              <span key={i} className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                {concern}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-green-600" />
                          <span className="text-lg font-bold text-green-600">
                            ${product.average_price}
                          </span>
                          <span className="text-sm text-gray-500">{product.currency}</span>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-600">Match Score</div>
                          <div className="text-lg font-semibold text-blue-600">
                            {Math.round(product.substitute_score * 100)}%
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => getPriceComparison(product.product_id)}
                          className="flex-1 bg-blue-100 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-200 transition-colors flex items-center justify-center gap-2"
                        >
                          <DollarSign className="w-4 h-4" />
                          Compare Prices
                        </button>
                        <a
                          href={product.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                        >
                          <ExternalLink className="w-4 h-4" />
                          View Product
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
                
{priceComparison && (
  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
    <h4 className="font-semibold mb-3">
      💰 Price Comparison for {priceComparison.product_name}
    </h4>
    <div className="grid gap-3 md:grid-cols-2">
      {priceComparison.price_sources.map((source, idx) => (
        <div
          key={idx}
          className="flex items-center justify-between p-3 bg-white rounded border"
        >
          <div>
            <div className="font-medium">{source.retailer}</div>
            <div className="text-sm text-gray-600">{source.shipping}</div>
          </div>
          <div className="text-right">
            <div className="font-bold text-green-600">
              ${source.price.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500">
              {source.in_stock ? 'In Stock' : 'Out of Stock'}
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
)}              
              </div>
            )}

            {/* Substitutes */}
            {analysis.flaggedIngredients.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <h3 className="text-xl font-semibold mb-4">🧪 Ingredient-Level Substitutes</h3>
                <div className="space-y-4">
                  {analysis.flaggedIngredients.map((ing, idx) => {
                    const subs = substitutes[ing.normalized] || [];
                    return subs.length > 0 ? (
                      <div key={idx} className="border-l-4 border-green-500 pl-4">
                        <p className="font-semibold text-gray-800 mb-2">
                          Instead of: <span className="text-red-600">{ing.ingredient}</span>
                        </p>
                        {subs.map((sub, sidx) => (
                          <div key={sidx} className="bg-green-50 rounded-lg p-3 mb-2">
                            <div className="flex items-center justify-between">
                              <p className="font-medium text-green-800">{sub.name}</p>
                              <span className="text-green-700 font-semibold">{sub.score}/100</span>
                            </div>
                            <p className="text-sm text-green-700 mt-1">{sub.type}</p>
                          </div>
                        ))}
                      </div>
                    ) : null;
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer Info */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Health scores based on ingredient frequency analysis, safety databases, and clinical research</p>
          <p className="mt-1">Data source: Skincare Products Clean Dataset (Kaggle)</p>
        </div>
      </div>
    </div>
  );
};

export default BottleScanDemo;
