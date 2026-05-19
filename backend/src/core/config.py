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


config = __Config()
