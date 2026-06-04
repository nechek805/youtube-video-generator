from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.youtube.models import YouTubeAccount


class YouTubeAccountRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: int) -> YouTubeAccount | None:
        result = await self.db.execute(
            select(YouTubeAccount).where(YouTubeAccount.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
        channel_id: str | None = None,
        channel_name: str | None = None,
        channel_thumbnail: str | None = None,
    ) -> YouTubeAccount:
        account = await self.get_by_user_id(user_id)
        if account is None:
            account = YouTubeAccount(user_id=user_id)
            self.db.add(account)

        account.access_token = access_token
        account.refresh_token = refresh_token
        account.token_expiry = token_expiry
        if channel_id is not None:
            account.channel_id = channel_id
        if channel_name is not None:
            account.channel_name = channel_name
        if channel_thumbnail is not None:
            account.channel_thumbnail = channel_thumbnail

        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def delete(self, user_id: int) -> bool:
        account = await self.get_by_user_id(user_id)
        if account is None:
            return False
        await self.db.delete(account)
        await self.db.commit()
        return True
