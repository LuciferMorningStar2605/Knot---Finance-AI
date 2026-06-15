import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1000"))
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.3"))  # Low for consistency

    # Email / SMTP
    DRY_RUN_MODE: bool = os.getenv("DRY_RUN_MODE", "true").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Finance Team")

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    AUDIT_DB_PATH: str = os.getenv("AUDIT_DB_PATH", "")
    if not AUDIT_DB_PATH:
        if os.getenv("VERCEL"):
            AUDIT_DB_PATH = "/tmp/audit_trail.db"
        else:
            AUDIT_DB_PATH = os.path.join(BASE_DIR, "output/audit_db/audit_trail.db")
    LOGS_DIR: str = os.path.join(BASE_DIR, os.getenv("LOGS_DIR", "logs/"))
    DATA_DIR: str = os.path.join(BASE_DIR, os.getenv("DATA_DIR", "data/"))
    PROMPTS_DIR: str = os.path.join(BASE_DIR, "prompts")

    # LangChain Cache
    USE_LANGCHAIN_CACHE: bool = os.getenv("USE_LANGCHAIN_CACHE", "true").lower() == "true"
    CACHE_DB_PATH: str = os.path.join(BASE_DIR, os.getenv("CACHE_DB_PATH", "output/langchain_cache.db"))

    # Agent Behaviour
    MAX_EMAIL_RETRIES: int = int(os.getenv("MAX_EMAIL_RETRIES", "2"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    SKIP_WEEKENDS: bool = os.getenv("SKIP_WEEKENDS", "false").lower() == "true"

settings = Settings()
