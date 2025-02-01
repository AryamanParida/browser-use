import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAPI_KEY: str = os.getenv("OPENAPI_KEY", "")
    PROXY_URL: str = os.getenv("PROXY_URL", "http://localhost:8080")

settings = Settings()
