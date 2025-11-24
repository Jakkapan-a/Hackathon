from typhoon_ocr import ocr_document

def extract_text_from_image_ollama(
    image_path: str,
    model: str = "scb10x/typhoon-ocr1.5-3b:latest",
    base_url: str = "http://localhost:7869/v1",
    temperature: float = 0.1,
    top_p: float = 0.6,
    repetition_penalty: float = 1.1,
):
    """
    Extract text from image using Typhoon OCR

    Parameters:
    -----------
    image_path : str
        Path to the image file
    model : str
        Ollama model name
    base_url : str
        Ollama server URL
    temperature : float
        Sampling temperature
    top_p : float
        Top-p sampling parameter
    repetition_penalty : float
        Repetition penalty (not used in current implementation)

    Returns:
    --------
    str
        Extracted text in markdown format
    """
    try:
        # Use Typhoon OCR library to extract text
        result = ocr_document(
            pdf_or_image_path=image_path,
            base_url=base_url,
            api_key="ollama",
            model=model,
        )

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None

