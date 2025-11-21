import requests
from typing import Tuple, Optional

from config import Config
from prompt import SYSTEM_INSTRUCTION_NUMBER_GCN


def extract_gcn_with_llm(
    image_b64: str, 
    llm_url: str = None, 
    api_timeout: int = None
) -> Tuple[str, Optional[str]]:
    """
    Call LLM to extract GCN number from base64 image
    
    Args:
        image_b64: Base64 string of image
        llm_url: LLM API URL (uses Config.LM_URL if not provided)
        api_timeout: API timeout in seconds (uses Config.API_TIMEOUT if not provided)
        
    Returns:
        Tuple of (GCN number extracted, error message if any)
    """
    # Use provided values or fall back to config
    url = llm_url if llm_url else Config.LM_URL
    timeout = api_timeout if api_timeout else Config.API_TIMEOUT
    
    try:
        payload = {
            "model": Config.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": SYSTEM_INSTRUCTION_NUMBER_GCN}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract GCN number from image according to the specified format."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                        }
                    ]
                }
            ],
            "temperature": Config.TEMPERATURE,
        }
        
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        result = data["choices"][0]["message"]["content"]
        
        return result.strip(), None
        
    except requests.exceptions.Timeout:
        return "ERROR", "LLM API timeout"
    except requests.exceptions.RequestException as e:
        return "ERROR", f"LLM API error: {str(e)[:100]}"
    except Exception as e:
        return "ERROR", f"LLM error: {str(e)[:100]}"

