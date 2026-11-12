"""
P4 AI/VQA Question Service — configuration.

All settings are read from environment variables or a .env file.
No secrets are hard-coded here.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load from apps/api/.env or current working directory .env
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()


class _Settings:
    """Lightweight settings container (no pydantic-settings dependency)."""

    @property
    def camera_api_url(self) -> str:
        return os.environ.get("AEGIS_CAMERA_API_URL", "http://127.0.0.1:8765").rstrip("/")

    @property
    def gemini_api_key(self) -> str:
        return os.environ.get("GEMINI_API_KEY", "").strip()

    @property
    def gemini_model(self) -> str:
        return os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()

    @property
    def vqa_enabled(self) -> bool:
        return os.environ.get("AEGIS_VQA_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def vqa_model(self) -> str:
        return os.environ.get("AEGIS_VQA_MODEL", "dandelin/vilt-b32-finetuned-vqa")

    @property
    def port(self) -> int:
        return int(os.environ.get("AEGIS_QA_PORT", "8001"))

    @property
    def max_question_length(self) -> int:
        return 500

    @property
    def max_body_bytes_text(self) -> int:
        return 4096  # 4 KB for text-only requests

    @property
    def max_body_bytes_vqa(self) -> int:
        return 10 * 1024 * 1024  # 10 MB for image payloads


settings = _Settings()
