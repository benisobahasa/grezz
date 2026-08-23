import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Grezz"
    TAGLINE: str = "AI Search Readiness, Decoded."

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    # Ad network - set to "true" once you have an approved AdSense (or other) account
    ADS_ENABLED: bool = os.getenv("ADS_ENABLED", "false").lower() == "true"
    ADSENSE_CLIENT_ID: str = os.getenv("ADSENSE_CLIENT_ID", "")  # e.g. ca-pub-xxxxxxxxxxxxxxxx
    AD_SLOT_HEADER: str = os.getenv("AD_SLOT_HEADER", "")
    AD_SLOT_SIDEBAR: str = os.getenv("AD_SLOT_SIDEBAR", "")
    AD_SLOT_INCONTENT: str = os.getenv("AD_SLOT_INCONTENT", "")
    AD_SLOT_NATIVE: str = os.getenv("AD_SLOT_NATIVE", "")      # between recommendation cards
    AD_SLOT_FOOTER: str = os.getenv("AD_SLOT_FOOTER", "")
    AD_SLOT_STICKY: str = os.getenv("AD_SLOT_STICKY", "")      # small, dismissible bottom bar

    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))


settings = Settings()
