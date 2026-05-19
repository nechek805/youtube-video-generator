from password_validator import PasswordValidator
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.session.schemas import SessionRead


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        __password_schema = PasswordValidator()
        __password_schema.min(8).has().uppercase().has().digits().has().symbols()
        if not __password_schema.validate(value):
            raise ValueError("Password must be at least 8 characters and include uppercase, digit, and symbol")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class UserReadFullInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    sessions: list[SessionRead]
