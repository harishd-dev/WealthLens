"""
Pydantic v2 schemas for request/response validation.
"""

from datetime import date, datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class TransactionType(str, Enum):
    debit  = "debit"
    credit = "credit"


class Category(str, Enum):
    food          = "Food"
    travel        = "Travel"
    shopping      = "Shopping"
    bills         = "Bills"
    entertainment = "Entertainment"
    health        = "Health"
    investment    = "Investment"
    income        = "Income"
    other         = "Other"


# ── Auth ──────────────────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str     = Field(min_length=2, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      str
    email:        str
    name:         Optional[str]


class PasswordResetRequest(BaseModel):
    email: EmailStr


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionBase(BaseModel):
    description: str          = Field(max_length=255)
    amount:      float        = Field(gt=0)
    type:        TransactionType
    category:    Category     = Category.other
    date:        date
    notes:       Optional[str] = None

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 2)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: Optional[str]              = None
    amount:      Optional[float]            = Field(default=None, gt=0)
    type:        Optional[TransactionType]  = None
    category:    Optional[Category]         = None
    date:        Optional[date]             = None
    notes:       Optional[str]              = None


class TransactionOut(TransactionBase):
    id:         str
    user_id:    str
    created_at: datetime
    source:     str = "manual"   # "manual" | "upload"

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    data:  List[TransactionOut]
    total: int
    page:  int
    size:  int


# ── Upload ────────────────────────────────────────────────────────────────────

class ParsedTransaction(BaseModel):
    """Intermediate model returned before user confirmation."""
    temp_id:      str
    date:         date
    description:  str
    amount:       float
    type:         TransactionType
    category:     Optional[Category]
    needs_review: bool = False   # True if category was unknown


class UploadPreviewResponse(BaseModel):
    transactions:     List[ParsedTransaction]
    total:            int
    auto_categorized: int
    needs_review:     int
    file_name:        str


class UploadConfirmRequest(BaseModel):
    """Sent back after user assigns categories to uncategorized transactions."""
    transactions:  List[TransactionCreate]
    save_mappings: List[dict] = []   # [{"merchant_key": "xyz", "category": "Food"}, ...]


class UploadConfirmResponse(BaseModel):
    imported: int
    mappings_saved: int


# ── Analytics ─────────────────────────────────────────────────────────────────

class MonthlySummary(BaseModel):
    month:   str
    year:    int
    income:  float
    expense: float
    savings: float


class CategoryBreakdown(BaseModel):
    category:   str
    total:      float
    percentage: float
    count:      int


class AnalyticsSummary(BaseModel):
    total_income:  float
    total_expense: float
    net_savings:   float
    savings_rate:  float
    monthly:       List[MonthlySummary]
    by_category:   List[CategoryBreakdown]


# ── Merchant Learning ─────────────────────────────────────────────────────────

class MerchantMappingCreate(BaseModel):
    merchant_key: str = Field(max_length=100)
    category:     Category


class MerchantMappingOut(BaseModel):
    id:          str
    user_id:     str
    merchant_key: str
    category:    str
    created_at:  datetime

    model_config = {"from_attributes": True}


# ── Insights ──────────────────────────────────────────────────────────────────

class InsightItem(BaseModel):
    title:   str
    body:    str
    type:    str   # "positive" | "warning" | "tip" | "alert"
    emoji:   str


class InsightsResponse(BaseModel):
    insights:    List[InsightItem]
    generated_at: datetime
    tx_count:    int
