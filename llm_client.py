import requests
from typing import Tuple, Optional, Dict

from config import Config
from prompt import SYSTEM_INSTRUCTION_NUMBER_GCN


def extract_gcn_with_llm(
    image_b64: str, 
    llm_url: str = None, 
    api_timeout: int = None,
    provider: str = None,
    model: str = None,
    api_key: str = None
) -> Tuple[str, Optional[str]]:
    """
    Call LLM to extract GCN number from base64 image
    
    Args:
        image_b64: Base64 string of image
        llm_url: LLM API URL (uses Config based on provider if not provided)
        api_timeout: API timeout in seconds (uses Config.API_TIMEOUT if not provided)
        provider: LLM provider ("lm_studio" or "openrouter", uses Config.DEFAULT_PROVIDER if not provided)
        model: Model name (uses Config based on provider if not provided)
        api_key: API key for OpenRouter (uses Config.OPENROUTER_API_KEY if not provided)
        
    Returns:
        Tuple of (GCN number extracted, error message if any)
    """
    # Determine provider
    if provider is None:
        provider = Config.DEFAULT_PROVIDER
    
    # Use provided values or fall back to config based on provider
    if provider == "openrouter":
        url = llm_url if llm_url else Config.OPENROUTER_URL
        model_name = model if model else Config.OPENROUTER_MODEL
        key = api_key if api_key else Config.OPENROUTER_API_KEY
    else:  # lm_studio
        url = llm_url if llm_url else Config.LM_STUDIO_URL
        model_name = model if model else Config.LM_STUDIO_MODEL
        key = None
    
    timeout = api_timeout if api_timeout else Config.API_TIMEOUT
    
    try:
        payload = {
            "model": model_name,
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
        
        # Setup headers
        headers = {"Content-Type": "application/json"}
        
        # Add OpenRouter specific headers
        if provider == "openrouter" and key:
            headers["Authorization"] = f"Bearer {key}"
            if Config.OPENROUTER_SITE_URL:
                headers["HTTP-Referer"] = Config.OPENROUTER_SITE_URL
            if Config.OPENROUTER_SITE_NAME:
                headers["X-Title"] = Config.OPENROUTER_SITE_NAME
        
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
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

