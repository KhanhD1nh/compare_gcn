from pathlib import Path

class Config:
    # LLM Configuration - LM Studio (Local)
    LM_STUDIO_URL: str = "http://192.168.1.69:1234/v1/chat/completions"
    LM_STUDIO_MODEL: str = "qwen2.5-vl-72b-instruct"
    
    # LLM Configuration - OpenRouter (Cloud)
    OPENROUTER_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_API_KEY: str = ""  # Add your OpenRouter API key here
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_SITE_URL: str = ""  # Optional: Your site URL
    OPENROUTER_SITE_NAME: str = "GCN Comparison Tool"  # Optional: Your site name
    
    # Default LLM Provider
    DEFAULT_PROVIDER: str = "lm_studio"  # "lm_studio" or "openrouter"
    
    # Common LLM Configuration
    TEMPERATURE: float = 0

    # Image Configuration
    RENDER_DPI: int = 300

    # Input Configuration
    INPUT_DIR: Path = Path("input")
    MAX_WORKERS: int = 5
    API_TIMEOUT: int = 120
    
    # Cache Configuration
    CACHE_DB_FILE: str = "processed_files.db"
    SKIP_PROCESSED_DEFAULT: bool = True
    
    # Backward compatibility
    LM_URL: str = "http://192.168.1.69:1234/v1/chat/completions"
    MODEL: str = "qwen2.5-vl-72b-instruct"