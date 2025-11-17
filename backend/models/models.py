import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.config.constants import (
    DocumentType,
    TransactionStatus,
    TransactionType,
    UserRole,
)
from backend.models.database import Base
from backend.models.types import GUID


# Create a custom UUID type that works with both PostgreSQL and SQLite
def get_uuid_column():
    return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


def get_uuid_fk(table_column):
    return Column(String(36), ForeignKey(table_column))


class User(Base):
    __tablename__ = "users"

    id = get_uuid_column()
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Float, default=1000.0)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    beneficiaries = relationship("Beneficiary", back_populates="user")
    transactions_sent = relationship(
        "Transaction", foreign_keys="Transaction.sender_id", back_populates="sender"
    )
    transactions_received = relationship(
        "Transaction", foreign_keys="Transaction.receiver_id", back_populates="receiver"
    )


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = get_uuid_column()
    user_id = get_uuid_fk("users.id")
    name = Column(String(100), nullable=False)
    bank_name = Column(String(100), nullable=False)
    iban = Column(String(34), nullable=False)
    country = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="beneficiaries")


class Transaction(Base):
    __tablename__ = "transactions"

    id = get_uuid_column()
    sender_id = get_uuid_fk("users.id")
    receiver_id = get_uuid_fk("users.id")
    beneficiary_id = get_uuid_fk("beneficiaries.id")
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="BHD", nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    description = Column(Text)
    reference_number = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="transactions_sent"
    )
    receiver = relationship(
        "User", foreign_keys=[receiver_id], back_populates="transactions_received"
    )
    beneficiary = relationship("Beneficiary")


class Document(Base):
    __tablename__ = "documents"

    # was: id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    document_type = Column(String, nullable=False)

    # Make sure this matches User.id type; per your logs it’s a String UUID
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)

    file_size = Column(Float, nullable=False, default=0.0)
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    uploader = relationship("User")


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = get_uuid_column()
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)
    rule_value = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    source_document_id = get_uuid_fk("documents.id")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source_document = relationship("Document")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = get_uuid_column()
    user_id = get_uuid_fk("users.id")
    session_data = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = get_uuid_column()
    session_id = get_uuid_fk("chat_sessions.id")
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
