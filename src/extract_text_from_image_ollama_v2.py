import os
from dotenv import load_dotenv
from openai import OpenAI
from typhoon_ocr import prepare_ocr_messages

load_dotenv()

def extract_text_from_image_ollama(
    image_path: str,
    model: str = None,
    base_url: str = None,
    temperature: float = 0.1,
    top_p: float = 0.6,
    repetition_penalty: float = 1.1,
    keep_alive: str = "5m",
):
    """
    Extract text from image using Ollama with full parameter control
    
    Parameters:
    -----------
    image_path : str
        Path to the image file
    model : str, optional
        Ollama model name (default: from OLLAMA_MODEL env)
    base_url : str, optional
        Ollama server URL (default: from OLLAMA_BASE_URL env)
    temperature : float
        Sampling temperature (0.0-1.0)
    top_p : float
        Top-p sampling parameter
    repetition_penalty : float
        Repetition penalty
    keep_alive : str
        How long to keep model in memory (e.g., "5m", "10m", "-1" for always)
    
    Returns:
    --------
    str
        Extracted text in markdown format
    """
    # Read from environment variables if not provided
    if model is None:
        model = os.getenv("OLLAMA_MODEL", "scb10x/typhoon-ocr1.5-3b:latest")
    if base_url is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    try:
        # Initialize OpenAI client with Ollama endpoint
        client = OpenAI(
            base_url=base_url,
            api_key="36c33417e786cfd13ed7c883c3142436d0c552da0ace67e3e0b93463b7f5d63f"  # Ollama doesn't need real API key
            # api_key="ollama"  # Ollama doesn't need real API key
        )
        
        # Prepare messages using typhoon_ocr's helper
        messages = prepare_ocr_messages(
            pdf_or_image_path=image_path,
            task_type="v1.5",
            target_image_dim=1800,
            page_num=1,
            figure_language="Thai"
        )
        
        # Call Ollama API with custom parameters
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=16384,
            temperature=temperature,
            top_p=top_p,
            extra_body={
                "repetition_penalty": repetition_penalty,
                "keep_alive": keep_alive,
                "seed": 1
            }
        )
        
        # Extract text from response
        text_output = response.choices[0].message.content
        return text_output

    except Exception as e:
        print(f"Error extracting text: {e}")
        import traceback
        traceback.print_exc()
        return None


# # ตัวอย่างการใช้งาน
# if __name__ == "__main__":
#     # Test with an image
#     image_path = "test_image.jpg"
    
#     # แบบที่ 1: ใช้ค่า default
#     result = extract_text_from_image_ollama(image_path)
#     print("Result:", result)
    
#     # แบบที่ 2: กำหนดค่าเอง
#     result = extract_text_from_image_ollama(
#         image_path=image_path,
#         temperature=0.05,
#         top_p=0.7,
#         keep_alive="-1",  # Keep model loaded always
#     )
#     print("Result:", result)
    
#     # แบบที่ 3: Unload model ทันที
#     result = extract_text_from_image_ollama(
#         image_path=image_path,
#         keep_alive="0",  # Unload immediately after response
#     )
#     print("Result:", result)