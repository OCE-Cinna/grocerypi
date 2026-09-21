from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── Items ────────────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    quantity: Optional[str] = "1"
    unit: Optional[str] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    quantity: Optional[str] = None
    unit: Optional[str] = None
    checked: Optional[bool] = None


class ItemOut(BaseModel):
    id: int
    name: str
    quantity: str
    unit: Optional[str]
    checked: bool
    list_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Grocery Lists ────────────────────────────────────────────────────────────

class ListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ListOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    checked_count: int = 0

    model_config = {"from_attributes": True}


class ListWithItems(ListOut):
    items: list[ItemOut] = []
