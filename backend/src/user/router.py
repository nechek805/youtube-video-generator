from fastapi import APIRouter, status, HTTPException, Depends, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.schemas import UserRead, UserReadFullInfo
from src.core.database import get_db
from src.auth.dependencies import get_current_user
from src.user.service import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/get-me")
async def get_me(
    session_token: str | None = Cookie(default=None),
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserReadFullInfo:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    service = UserService(db)
    user_full_info = await service.get_full_user_info(current_user)
    return user_full_info
