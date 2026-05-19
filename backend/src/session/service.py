import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.session.repository import SessionRepository
from src.session.models import Session
from src.session.schemas import SessionReadFirstTime
from src.core.security import hash_token


class SessionService:
    def __init__(self, db: AsyncSession):
        self.session_repository = SessionRepository(db)

    async def create_session_by_user_id(
            self,
            user_id: int,
            interval: timedelta = timedelta(days=30),
    ) -> SessionReadFirstTime:
        session_token = secrets.token_hex(16)
        hashed_session_token = hash_token(session_token)

        created_at = datetime.now(timezone.utc)
        expires_at = created_at + interval

        session = Session(
            hashed_session_token=hashed_session_token,
            user_id=user_id,
            created_at=created_at,
            expires_at=expires_at,
        )
        session = await self.session_repository.create_session(session)
        session_read = SessionReadFirstTime(
            session_token=session_token,
            created_at=created_at,
            expires_at=expires_at,
        )
        return session_read

    async def deactivate_session(self, session_token: str) -> bool:
        hashed_session_token = hash_token(session_token)
        session = await self.session_repository.get_session_by_hashed_session_token(hashed_session_token)
        if not session:
            return False
        await self.session_repository.deactivate_session(session)
        return True
