from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.category import Category
from app.schemas.contact import Contact
from app.schemas.transaction import Transaction
from app.schemas.card import Card
from uuid import UUID
import re

class UserBase(BaseModel):
    id: UUID
    sub: str
    name: str
    given_name: str
    family_name: str
    picture: str
    email: str
    email_verified: bool
    locale: str
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_blocked: Optional[bool] = False
    is_admin: Optional[bool] = False


class UserCreate(UserBase):
    pass


class User(UserBase):
    cards: List[Card] = []
    categories: List[Category] = []
    contacts: List[Contact] = []
    transactions: List[Transaction] = []

    class Config:
        from_attributes = True


class AddPhoneRequest(BaseModel):
    phone_number: str = Field(
        ...,
        min_length=13,
        max_length=13,
        pattern=r"^(\+359|0)\d{8,9}$",
    )


class VerifyPhoneRequest(BaseModel):
    code: str
