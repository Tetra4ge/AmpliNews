import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.environ.get("HF_API_KEY")
# HuggingFace all-MiniLM-L6-v2 produces a 384-dimensional vector
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

def generate_user_embedding(topics: list[str]) -> list[float]:
    """
    Calls HuggingFace API to generate a 384-dimensional vector for the user's selected topics.
    """
    prompt = f"A reader interested in: {', '.join(topics)}"
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        # The API returns a list of floats (the embedding)
        embedding = response.json()
        
        # Verify dimension
        if len(embedding) != 384:
            raise ValueError(f"Expected 384 dimensions, got {len(embedding)}")
            
        return embedding
    except Exception as e:
        print(f"Warning: Failed to generate vector from HuggingFace API: {e}")
        # Fallback to a zero-vector for testing if API fails
        return [0.0] * 384
