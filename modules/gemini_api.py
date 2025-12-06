"""
modules/gemini_api.py
------------------------------------------------------
Gemini API integration for image analysis and chat functionality.
Uses Google's Gemini Vision API to analyze chest X-ray images.
------------------------------------------------------
"""

import os
import base64
from typing import Optional, Dict, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARN] google-generativeai not installed. Install with: pip install google-generativeai")


def get_available_model():
    """
    Get the best available Gemini model that supports vision.
    Tries gemini-2.0-flash-exp, gemini-1.5-flash, then falls back to gemini-pro.
    """
    if not GEMINI_AVAILABLE:
        return None
    
    # Preferred models in order (most capable first)
    preferred_models = [
        'gemini-2.5-pro',
        'gemini-2.5-flash',
        'gemini-2.5-pro-preview-06-05',
        'gemini-2.5-pro-preview-05-06',
        'gemini-2.5-pro-preview-03-25',
        'gemini-2.0-flash-exp',
        'gemini-2.0-flash',
        'gemini-2.0-flash-001',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro-vision',
        'gemini-pro'
    ]
    
    # Try to list available models
    try:
        models = genai.list_models()
        available_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                # Extract model name (e.g., "models/gemini-1.5-flash" -> "gemini-1.5-flash")
                model_name = m.name.split('/')[-1] if '/' in m.name else m.name
                available_models.append(model_name)
        
        # Find first available preferred model
        for preferred in preferred_models:
            if preferred in available_models:
                print(f"[OK] Selected model: {preferred}")
                return preferred
        
        # If none found, return first available model
        if available_models:
            print(f"[OK] Using available model: {available_models[0]}")
            return available_models[0]
    except Exception as e:
        print(f"[WARN] Could not list models: {e}, trying direct model access")
    
    # Fallback: try models directly
    for model_name in preferred_models:
        try:
            # Just check if we can create the model (doesn't mean it works, but it's a start)
            genai.GenerativeModel(model_name)
            print(f"[OK] Using fallback model: {model_name}")
            return model_name
        except Exception:
            continue
    
    # Final fallback
    print("[WARN] Using default model: gemini-2.5-flash")
    return 'gemini-2.5-flash'


def initialize_gemini(api_key: Optional[str] = None) -> bool:
    """
    Initialize Gemini API with API key.
    API key can be provided or read from GEMINI_API_KEY environment variable.
    """
    if not GEMINI_AVAILABLE:
        return False
    
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARN] GEMINI_API_KEY not found. Set it as environment variable or pass as parameter.")
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"[ERROR] Error initializing Gemini: {e}")
        return False


def analyze_xray_image(image_path: str, ssim_results: Dict, cnn_results: Optional[Dict] = None) -> Optional[str]:
    """
    Analyze chest X-ray image using Gemini Vision API.
    
    Args:
        image_path: Path to the uploaded X-ray image
        ssim_results: Dictionary containing SSIM/MSE analysis results
        cnn_results: Optional dictionary containing CNN analysis results
    
    Returns:
        Analysis text from Gemini or None if error
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        # Initialize Gemini
        if not initialize_gemini():
            return None
        
        # Import PIL for image handling
        try:
            from PIL import Image
            img = Image.open(image_path)
        except ImportError:
            print("[WARN] PIL not available, using text-only mode")
            img = None
        
        # Prepare analysis context
        context = f"""You are a medical AI assistant analyzing a chest X-ray image. Please provide a clear, educational analysis.

Analysis Results:
- SSIM/MSE Prediction: {ssim_results.get('prediction', 'Unknown')}
- Normal Similarity: {ssim_results.get('summary', {}).get('NORMAL', {}).get('similarity_percent', 0)}%
- Pneumonia Similarity: {ssim_results.get('summary', {}).get('PNEUMONIA', {}).get('similarity_percent', 0)}%
"""
        
        if cnn_results and not cnn_results.get('error'):
            context += f"""
- CNN Prediction: {cnn_results.get('label', 'Unknown')}
- CNN Confidence: {cnn_results.get('confidence', 0)}%
"""
        
        context += """

IMPORTANT DISCLAIMERS:
- This is NOT a medical diagnosis
- Results are for educational/research purposes only
- Always consult a licensed healthcare provider
- Do not use this information to make medical decisions

Please provide:
1. A brief observation of the X-ray image
2. What the analysis results suggest
3. General educational information about what to look for
4. Reminder to consult a healthcare professional

Keep the response concise, clear, and educational. Do not provide medical diagnoses.
"""
        
        # Get available model
        model_name = get_available_model()
        if not model_name:
            print("[ERROR] No Gemini models available")
            return None
        
        # Try with image if available
        try:
            if img:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([context, img])
            else:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(context)
            return response.text
        except Exception as e:
            # Try alternative models
            alternative_models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            for alt_model in alternative_models:
                try:
                    if alt_model == model_name:
                        continue
                    model = genai.GenerativeModel(alt_model)
                    if img:
                        response = model.generate_content([context, img])
                    else:
                        response = model.generate_content(context)
                    print(f"[OK] Using model: {alt_model}")
                    return response.text
                except Exception:
                    continue
            
            # Final fallback to text-only
            print(f"[WARN] Vision models not available, using text-only: {e}")
            try:
                model = genai.GenerativeModel('gemini-pro')
                full_prompt = f"{context}\n\nNote: I cannot see the image directly, but here are the analysis results from computer vision models."
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e2:
                print(f"[ERROR] All models failed: {e2}")
                return None
            
    except Exception as e:
        print(f"[ERROR] Error in Gemini analysis: {e}")
        return None


def chat_with_gemini(message: str, image_path: str, conversation_history: List[Dict] = None) -> Optional[str]:
    """
    Continue chatting with Gemini about the uploaded image.
    
    Args:
        message: User's question/message
        image_path: Path to the uploaded X-ray image
        conversation_history: Previous conversation messages
    
    Returns:
        Gemini's response or None if error
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        if not initialize_gemini():
            return None
        
        # Import PIL for image handling
        try:
            from PIL import Image
            img = Image.open(image_path)
        except ImportError:
            img = None
        
        # Prepare system context
        system_context = """You are a medical AI assistant helping to answer questions about a chest X-ray image. 
Remember:
- This is NOT a medical diagnosis
- Provide educational information only
- Always remind users to consult healthcare professionals
- Be clear and concise
"""
        
        # Build conversation context
        full_prompt = system_context
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = "User" if msg.get('role') == 'user' else "Assistant"
                full_prompt += f"\n{role}: {msg.get('content', '')}"
        
        full_prompt += f"\n\nUser: {message}\nAssistant:"
        
        # Get available model
        model_name = get_available_model()
        if not model_name:
            print("[ERROR] No Gemini models available")
            return None
        
        # Always include image in chat - it's required for context
        if not img:
            print("[WARN] No image available for chat - image is required for context")
            return "Error: Image is required for chat functionality. Please upload an image first."
        
        # Try the selected model first
        try:
            model = genai.GenerativeModel(model_name)
            # Always send image with each message for context
            response = model.generate_content([full_prompt, img])
            return response.text
        except Exception as e:
            print(f"[WARN] Model {model_name} failed: {e}, trying alternatives...")
            # Try alternative models
            alternative_models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            for alt_model in alternative_models:
                if alt_model == model_name:
                    continue
                try:
                    model = genai.GenerativeModel(alt_model)
                    # Always include image
                    response = model.generate_content([full_prompt, img])
                    print(f"[OK] Using alternative model: {alt_model}")
                    return response.text
                except Exception as alt_e:
                    print(f"  - {alt_model} failed: {alt_e}")
                    continue
            
            # Final fallback - still try to use image
            print(f"[WARN] All vision models failed, trying text-only as last resort")
            try:
                model = genai.GenerativeModel('gemini-pro')
                # Even in fallback, mention we have image context
                fallback_prompt = f"{full_prompt}\n\nNote: I have access to the X-ray image but cannot process it directly. Please answer based on the conversation context."
                response = model.generate_content(fallback_prompt)
                return response.text
            except Exception as e2:
                print(f"[ERROR] All models failed: {e2}")
                return None
            
    except Exception as e:
        print(f"[ERROR] Error in Gemini chat: {e}")
        return None

