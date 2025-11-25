import os
from dotenv import load_dotenv
from typhoon_ocr import ocr_document

# Load environment variables
load_dotenv()

def extract_text_from_image_ollama(
    image_path: str,
    model: str = None,
    base_url: str = None,
    temperature: float = None,
    top_p: float = None,
    repetition_penalty: float = 1.1,
):
    """
    Extract text from image using Typhoon OCR

    Parameters:
    -----------
    image_path : str
        Path to the image file
    model : str, optional
        Ollama model name (reads from OLLAMA_MODEL env if not provided)
    base_url : str, optional
        Ollama server URL (reads from OLLAMA_BASE_URL env if not provided)
    temperature : float, optional
        Sampling temperature (reads from OCR_TEMPERATURE env if not provided)
    top_p : float, optional
        Top-p sampling parameter (reads from OCR_TOP_P env if not provided)
    repetition_penalty : float
        Repetition penalty (not used in current implementation)

    Returns:
    --------
    str
        Extracted text in markdown format
    """
    # Read from environment variables if not provided
    if model is None:
        model = os.getenv("OLLAMA_MODEL", "scb10x/typhoon-ocr1.5-3b:latest")
    if base_url is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:7869/v1")
    if temperature is None:
        temperature = float(os.getenv("OCR_TEMPERATURE", "0.1"))
    if top_p is None:
        top_p = float(os.getenv("OCR_TOP_P", "0.6"))

    try:
        # Use Typhoon OCR library to extract text
        result = ocr_document(
            pdf_or_image_path=image_path,
            base_url=base_url,
            api_key="ollama",
            model=model,
            options={
                "temperature": temperature,
                "top_p": top_p,
                "keep_alive": 0
            }
        )

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None

