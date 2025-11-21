from pathlib import Path

class Config:
    # LLM Configuration
    LM_URL: str = "http://192.168.1.69:1234/v1/chat/completions"
    MODEL: str = "qwen2.5-vl-72b-instruct"
    TEMPERATURE: float = 0

    # Image Configuration
    RENDER_DPI: int = 300

    # Input Configuration
    INPUT_DIR: Path = Path("input")
    MAX_WORKERS: int = 5
    API_TIMEOUT: int = 120