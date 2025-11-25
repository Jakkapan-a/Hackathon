import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_text_from_image_api(image_path, api_key, model, task_type, max_tokens, temperature, top_p, repetition_penalty, pages=None):
    url = "https://api.opentyphoon.ai/v1/ocr"

    print(f"Calling OpenTyphoon API: {url}")
    print(f"Model: {model}, Task Type: {task_type}")

    with open(image_path, 'rb') as file:
        files = {'file': file}
        data = {
            'model': model,
            'task_type': task_type,
            'max_tokens': str(max_tokens),
            'temperature': str(temperature),
            'top_p': str(top_p),
            'repetition_penalty': str(repetition_penalty)
        }

        if pages:
            data['pages'] = json.dumps(pages)

        headers = {
            'Authorization': f'Bearer {api_key}'
        }

        print(f"Request data: {data}")
        response = requests.post(url, files=files, data=data, headers=headers)

        if response.status_code == 200:
            result = response.json()

            # Extract text from successful results
            extracted_texts = []
            for page_result in result.get('results', []):
                if page_result.get('success') and page_result.get('message'):
                    content = page_result['message']['choices'][0]['message']['content']
                    try:
                        # Try to parse as JSON if it's structured output
                        parsed_content = json.loads(content)
                        text = parsed_content.get('natural_text', content)
                    except json.JSONDecodeError:
                        text = content
                    extracted_texts.append(text)
                elif not page_result.get('success'):
                    print(f"Error processing {page_result.get('filename', 'unknown')}: {page_result.get('error', 'Unknown error')}")

            return '\n'.join(extracted_texts)
        else:
            print(f"Error 8888 : {response.status_code}")
            print(response.text)
            return None


def extract_text_from_image(
    image_path: str,
    api_key: str = None,
    model: str = None,
    task_type: str = None,
    max_tokens: int = None,
    temperature: float = None,
    top_p: float = None,
    repetition_penalty: float = None,
    pages=None
):
    """
    Extract text from image using OpenTyphoon API with environment variable support

    Parameters:
    -----------
    image_path : str
        Path to the image file
    api_key : str, optional
        API key (reads from TYPHOON_API_KEY env if not provided)
    model : str, optional
        Model name (reads from TYPHOON_MODEL env if not provided, default: "typhoon-ocr")
    task_type : str, optional
        Task type (reads from TYPHOON_TASK_TYPE env if not provided, default: "v1.5")
    max_tokens : int, optional
        Maximum tokens (reads from TYPHOON_MAX_TOKENS env if not provided, default: 16000)
    temperature : float, optional
        Temperature (reads from TYPHOON_TEMPERATURE env if not provided, default: 0.1)
    top_p : float, optional
        Top-p (reads from TYPHOON_TOP_P env if not provided, default: 0.6)
    repetition_penalty : float, optional
        Repetition penalty (reads from TYPHOON_REPETITION_PENALTY env if not provided, default: 1.1)
    pages : list, optional
        List of page numbers to process

    Returns:
    --------
    str
        Extracted text
    """
    # Read from environment variables if not provided
    if api_key is None:
        api_key = os.getenv("TYPHOON_API_KEY")
        if not api_key:
            raise ValueError("API key is required. Set TYPHOON_API_KEY environment variable or pass api_key parameter.")
    print(f"Using API Key: {'*' * (len(api_key) - 4) + api_key[-4:]}")
    if model is None:
        model = os.getenv("TYPHOON_MODEL", "typhoon-ocr-preview")
    if task_type is None:
        task_type = os.getenv("TYPHOON_TASK_TYPE", "default")
    if max_tokens is None:
        max_tokens = int(os.getenv("TYPHOON_MAX_TOKENS", "16000"))
    if temperature is None:
        temperature = float(os.getenv("TYPHOON_TEMPERATURE", "0.1"))
    if top_p is None:
        top_p = float(os.getenv("TYPHOON_TOP_P", "0.6"))
    if repetition_penalty is None:
        repetition_penalty = float(os.getenv("TYPHOON_REPETITION_PENALTY", "1.1"))

    return extract_text_from_image_api(
        image_path, api_key, model, task_type, max_tokens,
        temperature, top_p, repetition_penalty, pages
    )


# # Usage Example
# if __name__ == "__main__":
#     # Method 1: Using environment variables (recommended)
#     extracted_text = extract_text_from_image("path/to/image.jpg")
#
#     # Method 2: Passing parameters directly
#     extracted_text = extract_text_from_image(
#         image_path="path/to/image.jpg",
#         api_key="your_api_key",
#         model="typhoon-ocr",
#         task_type="v1.5"
#     )
#     print(extracted_text)