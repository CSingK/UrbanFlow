import os
import re
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from typing import Dict

def init_vertex():
    """Initializes the Vertex AI SDK using Project & Location from .env."""
    project_id = os.environ.get("GCP_PROJECT_ID")
    location = os.environ.get("GCP_LOCATION", "asia-southeast1")
    if project_id:
        vertexai.init(project=project_id, location=location)

def get_resilient_model() -> GenerativeModel:
    """
    Attempts to load the target model from .env, 
    but falls back to the stable 1.5-flash if initialization fails.
    """
    target_model = os.environ.get("AI_MODEL_NAME", "gemini-2.5-flash")
    fallback_model = "gemini-1.5-flash-002"
    
    try:
        # Try primary model
        return GenerativeModel(target_model)
    except Exception as e:
        print(f"--- [AI ENGINEER] Falling back to {fallback_model} due to: {e} ---")
        return GenerativeModel(fallback_model)

async def analyze_station_crowd(image_data: bytes, image_path_for_mock: str = "") -> Dict:
    """
    UrbanFlow Mobility Agent: Analyzes CCTV feed for crowd count and boarding intent.
    Accepts image_data as bytes for production FastAPI integration.
    """
    init_vertex()
    default_response = {"count": 0, "boarding_probability": 0.0}
    
    try:
        model = get_resilient_model()
        
        # Agent Instruction
        prompt = """
        You are the UrbanFlow Mobility Agent. Analyze this CCTV feed from a smart bus station.
        1. Count the exact number of people waiting at the platform.
        2. Analyze their 'boarding intent' based on their proximity to the curb and posture.
        3. Provide a 'boarding_probability' between 0.0 and 1.0.
        
        Return ONLY a clean JSON object:
        {"count": int, "boarding_probability": float}
        """

        # Handle Mock Feed for local testing (if no data provided)
        if not image_data and image_path_for_mock.startswith("/mock"):
            import random
            return {"count": random.randint(5, 40), "boarding_probability": round(random.uniform(0.1, 0.9), 2)}

        # Real Multimodal Call
        if image_data:
            image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
            
            # Use async generation for production performance
            response = await model.generate_content_async(
                [image_part, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            # THE CLEAN JSON PROTOCOL
            # Strip markdown code blocks (e.g., ```json ... ```) using Regex
            raw_text = response.text
            clean_text = re.sub(r'```(?:json)?\n?|\n?```', '', raw_text).strip()
            
            try:
                result = json.loads(clean_text)
                return result
            except json.JSONDecodeError:
                print("--- [AI ERROR] JSON Parsing failed even after cleaning ---")
                return default_response

    except Exception as e:
        print(f"--- [AI ERROR] Vision Service Failure: {e} ---")
        return default_response

    return default_response