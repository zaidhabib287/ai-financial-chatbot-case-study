from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SYSTEM = "system"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class TransactionType(str, Enum):
    TRANSFER = "transfer"
    CREDIT = "credit"
    DEBIT = "debit"


class DocumentType(str, Enum):
    SANCTIONS_LIST = "sanctions_list"
    COMPLIANCE_RULES = "compliance_rules"
    TERMS_CONDITIONS = "terms_conditions"
    OTHER = "other"


# Blacklisted countries (example)
BLACKLISTED_COUNTRIES = ["North Korea", "Iran", "Syria", "Cuba", "Crimea Region"]

# Supported file extensions
SUPPORTED_DOCUMENT_EXTENSIONS = [".pdf", ".docx", ".txt"]

# Chat intents
CHAT_INTENTS = {
    "add_beneficiary": ["add beneficiary", "new beneficiary", "register beneficiary"],
    "transfer_funds": ["transfer", "send money", "make payment"],
    "check_balance": ["balance", "how much", "account balance"],
    "transaction_history": ["history", "past transactions", "transaction list"],
}
