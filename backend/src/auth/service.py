from sqlalchemy.ext.asyncio import AsyncSession

from src.user.schemas import UserCreate, UserLogin, UserRead
from src.session.schemas import SessionReadFirstTime
from src.user.service import UserService
from src.session.service import SessionService
from src.user.models import EmailStatus
from src.user.exceptions import EmailNotConfirmed


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)
        self.session_service = SessionService(db)

    async def register_user(self, user: UserCreate) -> SessionReadFirstTime:
        created_user = await self.user_service.create_user(user)
        session = await self.session_service.create_session_by_user_id(created_user.id)
        await self.user_service.send_confirm_email(created_user)
        return session

    async def login_user(self, user: UserLogin) -> SessionReadFirstTime:
        user_db = await self.user_service.check_password(user.email, user.password)
        if user_db.email_status != EmailStatus.ACTIVE:
            raise EmailNotConfirmed()
        session = await self.session_service.create_session_by_user_id(user_db.id)
        return session

    async def logout_user(self, session_token: str):
        success = await self.session_service.deactivate_session(session_token)
        return success

    async def confirm_email(self, token: str) -> bool:
        success = await self.user_service.confirm_email(token)
        return success

    async def get_user_by_session_token(self, session_token: str) -> UserRead:
        user = await self.user_service.get_user_by_session_token(session_token)
        return user
