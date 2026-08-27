from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    balance: Decimal
    registered_at: datetime


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthResponse(TokenResponse):
    user: UserPublic


class ItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    steam_app_id: int
    image_url: str
    rarity: Literal["common", "rare", "epic", "legendary"]
    estimated_price: Decimal


class CaseSummary(BaseModel):
    id: int
    name: str
    description: str
    opening_price: Decimal
    image_url: str
    is_active: bool


class CaseListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CaseSummary]


class CaseItemChance(BaseModel):
    item: ItemPublic
    weight: int
    chance_percent: Decimal


class CaseDetail(CaseSummary):
    items: list[CaseItemChance]


class KeyPublic(BaseModel):
    id: int
    key: str
    status: Literal["assigned", "used"]
    item: ItemPublic
    added_at: datetime


class OpeningResult(BaseModel):
    id: int
    case: CaseSummary
    item: ItemPublic
    key: KeyPublic | None
    cost: Decimal
    opened_at: datetime
    balance_after: Decimal


class OpeningHistoryItem(BaseModel):
    id: int
    case: CaseSummary
    item: ItemPublic
    key: KeyPublic | None
    cost: Decimal
    opened_at: datetime


class OpeningHistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OpeningHistoryItem]


class InventoryResponse(BaseModel):
    total: int
    items: list[KeyPublic]


class TopUpRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)


class BalanceResponse(BaseModel):
    balance: Decimal


class TransactionPublic(BaseModel):
    id: int
    type: Literal["credit", "debit"]
    amount: Decimal
    created_at: datetime
    description: str


class TransactionListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TransactionPublic]
