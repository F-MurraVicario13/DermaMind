import React, { useState } from 'react';
import { Camera, Upload, CheckCircle, AlertTriangle, XCircle, Sparkles, Info, ShoppingCart, DollarSign, Star, ExternalLink, Scan, ArrowRight } from 'lucide-react';

const BottleScanDemo = () => {
  const [step, setStep] = useState('upload');
  const [analysis, setAnalysis] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [productRecommendations, setProductRecommendations] = useState([]);
  const [priceComparisons, setPriceComparisons] = useState({});
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [loadingPrices, setLoadingPrices] = useState({});
  const [apiError, setApiError] = useState(null);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = async () => {
        setImagePreview(reader.result);
        setStep('processing');
        await processImage(file);
      };
      reader.readAsDataURL(file);
    }
  };

  const processImage = async (imageFile) => {
    setLoadingAnalysis(true);
    setApiError(null);

    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const ocrResponse = await fetch('http://localhost:8000/ocr-extract', {
        method: 'POST',
        body: formData
      });

      if (!ocrResponse.ok) {
        throw new Error(`OCR failed: ${ocrResponse.status}`);
      }

      const ocrData = await ocrResponse.json();

      const analysisResponse = await fetch('http://localhost:8000/analyze-ingredients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ingredients: ocrData.ingredients
        })
      });

      if (!analysisResponse.ok) {
        throw new Error(`Analysis failed: ${analysisResponse.status}`);
      }

      const analysisData = await analysisResponse.json();
      setAnalysis(analysisData);
      setStep('results');

      if (analysisData.flaggedIngredients && analysisData.flaggedIngredients.length > 0) {
        await getProductRecommendations(analysisData.flaggedIngredients.map(i => i.ingredient));
      }

    } catch (error) {
      console.error('Error processing image:', error);
      setApiError(`Error: ${error.message}`);
      setStep('upload');
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const getProductRecommendations = async (flaggedIngredients) => {
    setLoadingRecommendations(true);
    
    try {
      const response = await fetch('http://localhost:8000/recommend-products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          flagged_ingredients: flaggedIngredients,
          original_category: 'serum',
          skin_type: ['combination', 'oily'],
          concerns: ['acne', 'texture'],
          max_results: 5
        })
      });
      
      if (response.ok) {
        const recommendations = await response.json();
        setProductRecommendations(recommendations);
        setShowRecommendations(true);
      }
    } catch (error) {
      console.error('Network Error:', error);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const getPriceComparison = async (productId) => {
    setLoadingPrices(prev => ({ ...prev, [productId]: true }));
    
    try {
      const response = await fetch(`http://localhost:8000/price-comparison/${productId}`);
      
      if (response.ok) {
        const priceData = await response.json();
        setPriceComparisons(prev => ({
          ...prev,
          [productId]: priceData
        }));
      }
    } catch (error) {
      console.error('Price comparison error:', error);
    } finally {
      setLoadingPrices(prev => ({ ...prev, [productId]: false }));
    }
  };

  const getScoreColor = (score) => {
    if (score >= 76) return '#22c55e';
    if (score >= 51) return '#f59e0b';
    if (score >= 26) return '#f97316';
    return '#ef4444';
  };

  const resetApp = () => {
    setStep('upload');
    setAnalysis(null);
    setImagePreview(null);
    setProductRecommendations([]);
    setPriceComparisons({});
    setShowRecommendations(false);
    setLoadingAnalysis(false);
    setLoadingRecommendations(false);
    setLoadingPrices({});
    setApiError(null);
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #FFB5B5 0%, #FFC9A3 50%, #FFE5B4 100%)' }}>
      {/* Floating decoration elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-16 h-16 opacity-20" style={{ transform: 'rotate(-15deg)' }}>
          <Sparkles className="w-full h-full text-indigo-500" />
        </div>
        <div className="absolute top-40 right-20 w-12 h-12 opacity-20" style={{ transform: 'rotate(25deg)' }}>
          <Camera className="w-full h-full text-indigo-500" />
        </div>
        <div className="absolute bottom-32 left-1/4 w-14 h-14 opacity-20" style={{ transform: 'rotate(45deg)' }}>
          <Scan className="w-full h-full text-indigo-500" />
        </div>
      </div>

      <div className="relative max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-block mb-4">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="40" cy="40" r="35" fill="#6366F1" opacity="0.1"/>
              <path d="M35 25 L45 25 C50 25 55 30 55 35 L55 45 C55 50 50 55 45 55 L35 55 C30 55 25 50 25 45 L25 35 C25 30 30 25 35 25 Z" stroke="#6366F1" strokeWidth="3" fill="none"/>
              <circle cx="40" cy="40" r="8" fill="#6366F1"/>
            </svg>
          </div>
          <h1 className="text-5xl font-bold mb-3" style={{ 
            background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            letterSpacing: '-0.02em'
          }}>
            DermaMind
          </h1>
          <p className="text-lg text-gray-700 font-medium">Discover Your Product's Story</p>
        </div>

        {/* Upload Section */}
        {step === 'upload' && (
          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-3xl shadow-2xl overflow-hidden" style={{ boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
              <div className="p-10">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label 
                  htmlFor="file-upload" 
                  className="block cursor-pointer"
                >
                  <div className="text-center mb-8">
                    <div className="w-32 h-32 mx-auto mb-6 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)' }}>
                      <Camera className="w-16 h-16 text-white" strokeWidth={1.5} />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-3">Take a Scan</h2>
                    <p className="text-gray-600">Photograph your product's ingredient list</p>
                  </div>
                  
                  <div className="w-full py-5 text-center rounded-2xl font-bold text-white text-lg" style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' }}>
                    Get Started
                  </div>
                </label>

                {apiError && (
                  <div className="mt-6 p-4 bg-red-50 rounded-2xl border-2 border-red-200">
                    <p className="text-red-700 text-sm">{apiError}</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Clear photos give the best results
              </p>
            </div>
          </div>
        )}

        {/* Processing */}
        {step === 'processing' && (
          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-3xl shadow-2xl p-10 text-center">
              <div className="w-24 h-24 mx-auto mb-6 rounded-full flex items-center justify-center animate-pulse" style={{ background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)' }}>
                <Scan className="w-12 h-12 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Analyzing...</h2>
              <p className="text-gray-600 mb-8">Reading ingredients</p>
              {imagePreview && (
                <img 
                  src={imagePreview} 
                  alt="Preview" 
                  className="mt-6 max-w-full mx-auto rounded-2xl shadow-lg"
                />
              )}
            </div>
          </div>
        )}

        {/* Results */}
        {step === 'results' && analysis && (
          <div className="space-y-6">
            {/* Hero Score */}
            <div className="bg-white rounded-3xl shadow-2xl p-10 text-center">
              <button
                onClick={resetApp}
                className="float-right px-6 py-2 rounded-full text-sm font-semibold" style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)', color: 'white' }}
              >
                New Scan
              </button>
              
              <div className="clear-both mb-8">
                <h2 className="text-3xl font-bold text-gray-800 mb-2">Your Results</h2>
                <p className="text-gray-600">Based on {analysis.ingredients?.length || 0} ingredients</p>
              </div>

              <div className="relative inline-block mb-8">
                <svg width="200" height="200" viewBox="0 0 200 200">
                  <circle cx="100" cy="100" r="90" fill="none" stroke="#f3f4f6" strokeWidth="12"/>
                  <circle 
                    cx="100" 
                    cy="100" 
                    r="90" 
                    fill="none" 
                    stroke={getScoreColor(analysis.productScore)}
                    strokeWidth="12"
                    strokeDasharray={`${(analysis.productScore / 100) * 565} 565`}
                    strokeLinecap="round"
                    transform="rotate(-90 100 100)"
                  />
                  <text x="100" y="110" textAnchor="middle" className="text-5xl font-bold" fill="#1f2937">
                    {analysis.productScore}
                  </text>
                </svg>
              </div>

              {analysis.flaggedIngredients && analysis.flaggedIngredients.length > 0 && (
                <div className="mt-8 p-6 rounded-2xl" style={{ background: 'linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)' }}>
                  <div className="flex items-center justify-center gap-3 mb-3">
                    <AlertTriangle className="w-6 h-6 text-amber-700" />
                    <p className="font-bold text-gray-800">
                      {analysis.flaggedIngredients.length} ingredient{analysis.flaggedIngredients.length > 1 ? 's' : ''} to avoid
                    </p>
                  </div>
                  <button
                    onClick={() => setShowRecommendations(!showRecommendations)}
                    disabled={loadingRecommendations}
                    className="mt-4 px-8 py-3 rounded-full font-bold text-white inline-flex items-center gap-2"
                    style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' }}
                  >
                    Find Better Products
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Ingredient Cards */}
            <div className="bg-white rounded-3xl shadow-2xl p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">Ingredients</h3>
              <div className="space-y-3">
                {analysis.ingredients && analysis.ingredients.map((ing, idx) => {
                  const scoreColor = getScoreColor(ing.score);
                  return (
                    <div key={idx} className="bg-gray-50 rounded-2xl p-5 hover:bg-gray-100 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-lg" style={{ backgroundColor: scoreColor + '20', color: scoreColor }}>
                          {ing.score}
                        </div>
                        <div className="flex-1">
                          <p className="font-bold text-gray-800 mb-1">{ing.ingredient}</p>
                          <p className="text-sm text-gray-600">{ing.reason}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Product Recommendations */}
            {showRecommendations && (
              <div className="bg-white rounded-3xl shadow-2xl p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Better Products</h3>
                
                {loadingRecommendations && (
                  <div className="text-center py-16">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full animate-pulse" style={{ background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)' }}></div>
                    <p className="text-gray-600">Finding alternatives...</p>
                  </div>
                )}
                
                {!loadingRecommendations && productRecommendations.length > 0 && (
                  <div className="space-y-4">
                    {productRecommendations.map((product, idx) => (
                      <div key={idx} className="bg-gray-50 rounded-2xl p-6 hover:shadow-lg transition-all">
                        <div className="flex gap-4">
                          <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-2xl font-bold text-white flex-shrink-0" style={{ background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)' }}>
                            {product.name.charAt(0)}
                          </div>
                          <div className="flex-1">
                            <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">{product.brand}</span>
                            <h4 className="font-bold text-gray-800 mt-1 mb-3">{product.name}</h4>
                            
                            <div className="flex items-center gap-4 mb-4">
                              <div className="flex items-center gap-1">
                                <Star className="w-4 h-4 text-yellow-500 fill-current" />
                                <span className="font-semibold text-sm">{product.rating}</span>
                              </div>
                              <div className="w-2 h-2 rounded-full bg-green-400"></div>
                              <span className="text-sm font-semibold text-green-600">Score: {product.health_score}</span>
                            </div>
                            
                            <div className="flex flex-wrap gap-2 mb-4">
                              {product.skin_type.slice(0, 3).map((type, i) => (
                                <span key={i} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-semibold">
                                  {type}
                                </span>
                              ))}
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <span className="text-2xl font-bold text-gray-800">${product.average_price}</span>
                              <a
                                href={product.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-6 py-2 rounded-full font-bold text-white text-sm"
                                style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' }}
                              >
                                View Product
                              </a>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default BottleScanDemo;