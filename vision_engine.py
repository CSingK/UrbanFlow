import os
import json
import google.generativeai as genai
from typing import Dict, Any

def analyze_cctv_image(image_path: str) -> Dict[str, Any]:
    """
    Analyzes a CCTV feed image using Gemini API to detect empty parking lots
    and illegal double-parking, returning congestion impact scores and coordinates.
    """
    # Ensure the API key is available
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY environment variable not set. Please set it before running."}
        
    genai.configure(api_key=api_key)
    
    # Use the model version specified in .env (e.g., gemini-2.5-flash)
    model_name = os.environ.get("AI_MODEL_NAME", "gemini-1.5-flash")
    model = genai.GenerativeModel(
        model_name,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        # Upload the file to Gemini's File API
        print(f"Uploading and analyzing: {image_path}...")
        uploaded_file = genai.upload_file(path=image_path)
        
        prompt = """
        Analyze this CCTV camera feed image.
        
        Tasks:
        1. Detect empty parking lots (spaces). Provide approximate bounding box coordinates [ymin, xmin, ymax, xmax] normalized between 0 and 1000.
        2. Detect any vehicles that are illegally double-parked on yellow lines. Provide approximate bounding box coordinates.
        3. Assess a 'Congestion Impact Score' on a scale of 1 to 10 based on how the illegally parked vehicles are affecting traffic flow.
        
        You MUST return exactly this JSON schema:
        {
          "empty_parking_lots": [{"coordinates": [ymin, xmin, ymax, xmax], "description": "str"}],
          "illegal_double_parking": [{"coordinates": [ymin, xmin, ymax, xmax], "description": "str"}],
          "congestion_impact_score": int
        }
        """
        
        response = model.generate_content([uploaded_file, prompt])
        
        # Clean up the file to manage quota limits
        genai.delete_file(uploaded_file.name)
        
        # Parse the output
        return json.loads(response.text)
        
    except Exception as e:
        return {"error": f"Failed to analyze image {image_path}: {str(e)}"}

def process_all_feeds(directory: str = "data/cctv_feeds/") -> Dict[str, Any]:
    """
    Iterates through all images in the specified directory and analyzes them using Gemini.
    """
    results = {}
    if not os.path.exists(directory):
        return {"error": f"Directory not found: {directory}"}
        
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    files_found = False
    
    for filename in os.listdir(directory):
        ext = os.path.splitext(filename)[1].lower()
        if ext in valid_extensions:
            files_found = True
            filepath = os.path.join(directory, filename)
            results[filename] = analyze_cctv_image(filepath)
            
    if not files_found:
        results["status"] = f"No images found in {directory}. Please add sample images (.jpg, .png, etc.)."
            
    return results

if __name__ == "__main__":
    # Test execution when script is run directly
    print("Initializing Vision Engine...")
    analysis_results = process_all_feeds()
    print(json.dumps(analysis_results, indent=2))
