import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _csv(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "unsafe-dev-only-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    cors_origins: tuple[str, ...] = tuple(_csv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"))
    case_no_key_policy: str = os.getenv("CASE_NO_KEY_POLICY", "item_only").lower()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()

if settings.case_no_key_policy not in {"item_only", "error"}:
    raise RuntimeError("CASE_NO_KEY_POLICY must be either 'item_only' or 'error'.")
