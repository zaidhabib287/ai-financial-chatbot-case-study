from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator, field_validator

from backend.config.constants import (
    DocumentType,
    TransactionStatus,
    TransactionType,
    UserRole,
)


# ---------------------------------------------------------------------------
# Document Schemas (DB → API)
# ---------------------------------------------------------------------------

class DocumentOut(BaseModel):
    """
    Generic document representation (e.g. for admin detail endpoints).
    """
    id: str
    filename: str
    file_path: str
    document_type: str  # exposed as plain string (enum .value)
    uploaded_by: str    # user id as string
    file_size: float
    is_processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime

    @field_validator("id", "uploaded_by", mode="before")
    @classmethod
    def cast_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """
    Response schema for /admin/documents/upload.

    Keep this minimal and stable for tests:
    - success: always bool
    - document_id: string representation of the document UUID
    - filename: original filename
    """
    success: bool
    document_id: str
    filename: str


class DocumentUpload(BaseModel):
    document_type: DocumentType


class Document(BaseModel):
    """
    Lightweight Document schema based on ORM model.
    Used where you want to expose the document row itself.
    """
    id: str
    filename: str
    document_type: DocumentType
    file_size: int
    is_processed: bool
    uploaded_by: str
    created_at: datetime
    processed_at: Optional[datetime]

    @field_validator("id", "uploaded_by", mode="before")
    @classmethod
    def cast_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# User Schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = UserRole.CUSTOMER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @validator("password")
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    daily_limit: Optional[float] = None


class User(UserBase):
    id: str  # Changed from UUID to str
    is_active: bool
    balance: float
    daily_limit: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Authentication Schemas
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------------------------------------------------------------------------
# Beneficiary Schemas
# ---------------------------------------------------------------------------

class BeneficiaryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    bank_name: str = Field(..., min_length=3, max_length=100)
    iban: str = Field(..., min_length=15, max_length=34)
    country: str = Field(..., min_length=2, max_length=50)


class BeneficiaryCreate(BeneficiaryBase):
    pass


class BeneficiaryUpdate(BaseModel):
    name: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: Optional[bool] = None


class Beneficiary(BeneficiaryBase):
    id: str  # Changed from UUID to str
    user_id: str  # Changed from UUID to str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Transaction Schemas
# ---------------------------------------------------------------------------

class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="BHD", max_length=3)
    description: Optional[str] = None


class TransferRequest(TransactionBase):
    beneficiary_id: str  # Changed from UUID to str


class TransactionResponse(TransactionBase):
    id: str  # Changed from UUID to str
    sender_id: str  # Changed from UUID to str
    beneficiary_id: Optional[str]  # Changed from UUID to str
    receiver_id: Optional[str]  # Changed from UUID to str
    type: TransactionType
    status: TransactionStatus
    reference_number: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Balance and Account Schemas
# ---------------------------------------------------------------------------

class BalanceResponse(BaseModel):
    balance: float
    currency: str = "BHD"
    daily_limit: float
    daily_spent: float
    available_today: float


class AccountOperation(BaseModel):
    user_id: str  # Changed from UUID to str
    amount: float = Field(..., gt=0)
    operation_type: str = Field(
        ...,
        pattern="^(credit|debit)$"
    )
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Mock API Responses
# ---------------------------------------------------------------------------

class MockApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Chat Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    content: str


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    session_id: str  # Changed from UUID to str
