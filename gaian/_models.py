from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Base(BaseModel):
    """All API models inherit this to get camelCase ↔ snake_case mapping."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


# ── Enums ─────────────────────────────────────────────────────────────────────

class KYCStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    NOT_STARTED = "not_started"
    REJECTED = "rejected"


class OrderStatus(str, Enum):
    AWAITING_CRYPTO_TRANSFER = "awaiting_crypto_transfer"
    VERIFIED = "verified"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MarketStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    NOT_STARTED = "not_started"
    REJECTED = "rejected"


class FiatCurrency(str, Enum):
    VND = "VND"
    PHP = "PHP"
    BRL = "BRL"


class CryptoCurrency(str, Enum):
    USDC = "USDC"
    USDT = "USDT"


class Chain(str, Enum):
    SOLANA = "Solana"
    ETHEREUM = "Ethereum"
    POLYGON = "Polygon"
    ARBITRUM = "Arbitrum"
    BASE = "Base"


class PolicyTier(str, Enum):
    KYC = "KYC"
    NON_KYC = "NON_KYC"


class Route(int, Enum):
    BIDV = 1
    ALIX_PAY = 2


# ── Core entities ─────────────────────────────────────────────────────────────

class User(_Base):
    id: int
    email: Optional[str] = None
    wallet_address: Optional[str] = None
    tenant_id: Optional[int] = None
    kyc_status: KYCStatus
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    phone_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BankInfo(_Base):
    bank_bin: Optional[str] = None
    bank_number: Optional[str] = None


class ProviderInfo(_Base):
    guid: Optional[str] = None
    name: Optional[str] = None
    service: Optional[str] = None


class QRInfo(_Base):
    bank_info: BankInfo = Field(default_factory=BankInfo)
    provider_info: ProviderInfo = Field(default_factory=ProviderInfo)
    beneficiary_name: Optional[str] = None
    encoded_string: Optional[str] = None
    additional_data: Optional[str] = None
    country_code: Optional[str] = None
    amount: Optional[float] = None
    purpose: Optional[str] = None


class ParsedQRInfo(_Base):
    is_valid: bool
    encoded_string: str
    country: str
    qr_provider: Optional[str] = None
    bank_bin: Optional[str] = None
    account_number: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    purpose: Optional[str] = None
    nation: Optional[str] = None
    beneficiary_name: Optional[str] = None
    detailed_qr_info: dict[str, Any] = Field(default_factory=dict)


class BankTransactionReference(_Base):
    request_id: Optional[str] = None
    request_date: Optional[str] = None


class Order(_Base):
    id: int
    order_id: str
    status: OrderStatus
    fiat_amount: float
    fiat_currency: FiatCurrency
    crypto_amount: float
    crypto_currency: CryptoCurrency
    exchange_rate: float
    qr_info: QRInfo = Field(default_factory=QRInfo)
    crypto_transfer_info: dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[int] = None
    payment_method: str = ""
    transaction_hash: Optional[str] = None
    wallet_address: Optional[str] = None
    network: Optional[str] = None
    expires_at: datetime
    bank_transaction_reference: BankTransactionReference = Field(
        default_factory=BankTransactionReference
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_prefunded: bool = False
    transaction_reference: Optional[str] = None
    route_id: Optional[Route] = None
    created_at: datetime
    updated_at: datetime


class Pagination(_Base):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class OrderList(_Base):
    items: list[Order]
    pagination: Pagination


class ExchangeInfo(_Base):
    fiat_amount: float
    fiat_currency: str
    crypto_amount: str
    crypto_currency: CryptoCurrency
    exchange_rate: str
    chain: Chain
    token: CryptoCurrency
    fee_amount: str = ""
    timestamp: datetime


class MarketInfo(_Base):
    status: MarketStatus
    reject_reason: Optional[str] = None
    action: Optional[str] = None


class PolicyLimits(_Base):
    per_transaction: float
    per_day: float


class PolicyResult(_Base):
    is_allowed: bool
    route_id: Route
    limits: PolicyLimits
    tier: PolicyTier
    reason: Optional[str] = None


class TenantBalance(_Base):
    currency: str
    available_balance: float
    wallet_address: str
    chain: Chain


class TenantSpend(_Base):
    total_spent: float
    limit: float


class VerifyOrderResult(_Base):
    order_id: str
    status: OrderStatus
    transaction_hash: str
    message: str
    bank_transfer_status: Optional[str] = None


# ── Request models ─────────────────────────────────────────────────────────────

class PlaceOrderRequest(_Base):
    qr_string: str
    amount: float
    crypto_currency: CryptoCurrency
    from_address: str
    fiat_currency: Optional[FiatCurrency] = None
    chain: Optional[Chain] = None
    transaction_reference: Optional[str] = None
    route_id: Optional[Route] = None


class PlacePrefundedOrderRequest(_Base):
    qr_string: str
    amount: float
    crypto_currency: CryptoCurrency
    from_address: str
    fiat_currency: Optional[FiatCurrency] = None
    transaction_reference: Optional[str] = None


class CalculateExchangeRequest(_Base):
    amount: float
    country: str
    chain: Chain
    token: CryptoCurrency


class SubmitKYCRequest(_Base):
    user_wallet_address: str
    user_email: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    nationality: str
    type: str
    national_id: str
    issue_date: str
    expiry_date: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    zip_code: str
    front_id_image: str
    back_id_image: str
    hold_id_image: str
    phone_number: str
    phone_country_code: str


class PlaceOrderResponse(_Base):
    order_id: str
    status: OrderStatus
    fiat_amount: float
    fiat_currency: FiatCurrency
    crypto_amount: float
    crypto_currency: CryptoCurrency
    exchange_rate: float
    qr_info: QRInfo = Field(default_factory=QRInfo)
    crypto_transfer_info: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""
    transaction_reference: Optional[str] = None
    route_id: Route = Route.BIDV
    is_prefunded: bool = False
