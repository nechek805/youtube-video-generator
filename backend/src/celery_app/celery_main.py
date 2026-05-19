from celery import Celery
import os

celery_app = Celery(
    "auth_session",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    include=[
        "src.celery_app.celery_send_email",
    ],
)
