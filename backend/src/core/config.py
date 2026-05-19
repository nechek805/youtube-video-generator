from dotenv import load_dotenv
import json
import os

load_dotenv()

class __Config:
    def __init__(self):
        pass

    def get_database_url(self):
        return os.getenv("DATABASE_URL")

    def get_sender_email(self):
        return os.getenv("SENDER_EMAIL")

    def get_email_app_password(self):
        return os.getenv("EMAIL_APP_PASSWORD")

    def get_resend_api_key(self):
        return os.getenv("RESEND_API_KEY")

    def get_base_url(self):
        return os.getenv("BASE_URL")

    def get_origins(self) -> list[str]:
        raw = os.getenv("ORIGINS", "[]")
        return json.loads(raw)

    def get_https_redirect(self) -> bool:
        return os.getenv("HTTPS_REDIRECT", "false").lower() == "true"

    def get_openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    def get_openai_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def get_mock_video_cdn_base(self) -> str:
        return os.getenv("MOCK_VIDEO_CDN_BASE", "https://mock-cdn.example.com/videos")


config = __Config()
