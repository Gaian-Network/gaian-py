from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class Chain(IntEnum):
    """Settlement chain ids accepted as ``chain_id`` by the on-chain quote endpoints."""

    ETHEREUM = 1
    OPTIMISM = 10
    BSC = 56
    SOLANA = 101
    POLYGON = 137
    STELLAR = 148
    BASE = 8453
    ARBITRUM = 42161
    AVALANCHE = 43114
    ARC = 5042002


class Gender(StrEnum):
    """Values of the KYC ``gender`` field."""

    MALE = "male"
    FEMALE = "female"


class DocumentType(StrEnum):
    """Kinds of identity document accepted as the KYC ``type`` field."""

    ID_CARD = "ID_CARD"
    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    RESIDENCE_PERMIT = "RESIDENCE_PERMIT"


class Occupation(StrEnum):
    """Codes accepted as the KYC ``occupation`` field."""

    C_SUITE_EXECUTIVE = "OCC1"
    EMPLOYEE = "OCC2"
    ENTREPRENEUR = "OCC3"
    FOREIGN_WORKER = "OCC4"
    FOREIGN_DOMESTIC_WORKER = "OCC5"
    HOME_MAKER = "OCC6"
    MIDDLE_MANAGEMENT = "OCC7"
    PILOT = "OCC8"
    PROFESSIONAL = "OCC9"
    SENIOR_MANAGEMENT = "OCC10"
    STUDENT = "OCC11"
    OTHERS = "OCC12"


class MarketStatus(StrEnum):
    """Gating status of a market or a payment method for one user. Uppercase, as the API sends."""

    APPROVED = "APPROVED"
    PENDING = "PENDING"
    NOT_STARTED = "NOT_STARTED"
    REJECTED = "REJECTED"


class PaymentMethodType(StrEnum):
    """Known payment methods. The API may add more."""

    QR = "QR_PAYMENT"
    CARD = "CARD_PAYMENT"


class QrNetwork(StrEnum):
    """Phone-payment rail for Peru. Only used when the country is PE."""

    YAPE = "YAPE"
    PLIN = "PLIN"


class OrderStatus(IntEnum):
    """Lifecycle state of an order, as returned by ``get_order_status``."""

    PENDING = 0
    AWAITING_DEPOSIT = 1
    PAYMENT_RECEIVED = 2
    QUEUED = 3
    PROCESSING = 4
    COMPLETED = 10
    FAILED = 20
    CANCELLED = 21
    EXPIRED = 22
    UNKNOWN = 99


class VerifyStatus(IntEnum):
    """Outcome of ``verify_order``. The numbers overlap with OrderStatus but mean other things."""

    PENDING = 0
    VERIFIED = 1
    FAILED = 2


_TERMINAL_STATUSES = frozenset(
    {OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED, OrderStatus.EXPIRED}
)


def is_terminal(status: int) -> bool:
    """Reports whether an order status is final. Poll ``get_order_status`` until it is."""
    return status in _TERMINAL_STATUSES


class GaianModel(BaseModel):
    """Base of every response model.

    Attributes are snake_case; the API's camelCase names are accepted when decoding. Unknown
    fields are ignored. A field the API leaves out or sends as null takes its default: None for
    a nullable field, otherwise an empty value (``""``, ``0``, ``False``, an empty list).
    Status-like fields are plain ``str``/``int`` so a new value from the API still decodes;
    compare them with the enums in this module.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _null_as_missing(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: value for key, value in data.items() if value is not None}
        return data


class UserResponse(GaianModel, Generic[T]):
    """Envelope of the user, KYC, wallet and organization endpoints."""

    request_id: str = ""
    data: T | None = None


class PaymentResponse(GaianModel, Generic[T]):
    """Envelope of the payment endpoints. Same as UserResponse plus a ``success`` flag."""

    request_id: str = ""
    success: bool = False
    data: T | None = None


class CreateUserResponse(GaianModel):
    """The server-generated id of a new user."""

    user_id: str = ""


class User(GaianModel):
    """A user record. Every field except ``id`` is None until the user provides it."""

    id: str = ""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    nationality: str | None = None
    national_id: str | None = None
    type: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone_country_code: str | None = None
    phone_number: str | None = None
    kyc_status: str | None = None
    reject_reason: str | None = None


class Pagination(GaianModel):
    """Paging metadata of a list endpoint."""

    page: int = 0
    page_size: int = 0
    total_count: int = 0
    total_pages: int = 0


class PaymentInfo(GaianModel):
    """The fiat leg of a UserOrder. ``amount`` is a decimal string."""

    amount: str = ""
    currency: str = ""
    status: str = ""
    provider: str = ""
    provider_ref: str | None = None
    paid_at: str | None = None


class CryptoTransferInfo(GaianModel):
    """The on-chain leg of a UserOrder. ``amount`` is a decimal string."""

    amount: str = ""
    chain: str = ""
    token: str = ""
    from_address: str = ""
    to_address: str = ""
    tx_hash: str = ""
    status: str = ""
    is_confirmed: bool = False
    confirmed_at: str | None = None


class UserOrder(GaianModel):
    """An order as the user service reports it. Amounts are decimal strings."""

    order_id: str = ""
    status: str = ""
    fiat_amount: str = ""
    fiat_currency: str = ""
    crypto_amount: str = ""
    crypto_currency: str = ""
    exchange_rate: str | None = None
    protocol_fee: str | None = None
    expires_at: str | None = None
    created_at: str = ""
    payment: PaymentInfo | None = None
    crypto_transfer: CryptoTransferInfo | None = None


class ListUserOrdersResponse(GaianModel):
    """One page of a user's orders. ``data`` and ``pagination`` are siblings of ``request_id``."""

    request_id: str = ""
    data: list[UserOrder] = Field(default_factory=list)
    pagination: Pagination = Field(default_factory=Pagination)


class MarketStatusResult(GaianModel):
    """Gating status of one market. ``status`` is a MarketStatus value."""

    status: str = ""
    reject_reason: str | None = None
    action: str | None = None


class GetMarketsResponse(GaianModel):
    """Maps ISO 3166-1 alpha-2 country codes to the user's status in that market."""

    markets: dict[str, MarketStatusResult] = Field(default_factory=dict)


class MarketKycRequirement(GaianModel):
    """KYC field names one market needs, and the ones the user has not provided yet."""

    required_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class GetMarketRequirementsResponse(GaianModel):
    """Maps ISO 3166-1 alpha-2 country codes to that market's KYC requirements for the user."""

    markets: dict[str, MarketKycRequirement] = Field(default_factory=dict)


class PaymentMethod(GaianModel):
    """One payment method and whether the user may use it. ``status`` is a MarketStatus value."""

    method: str = ""
    name: str = ""
    status: str = ""
    reject_reason: str | None = None
    action: str | None = None


class WalletInfo(GaianModel):
    """A wallet linked to a user."""

    address: str = ""
    chain: str = ""
    is_primary: bool = False


class SubmitKycResponse(GaianModel):
    """Result of a KYC submission."""

    user_id: str = ""
    email: str = ""
    kyc_status: str = ""


class UpdateKycResponse(GaianModel):
    """The user's full KYC record after an update. A field never provided is None."""

    user_id: str = ""
    kyc_status: str = ""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    nationality: str | None = None
    type: str | None = None
    national_id: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country_of_residence: str | None = None
    occupation: str | None = None
    phone_number: str | None = None
    phone_country_code: str | None = None


class GenerateKycLinkResponse(GaianModel):
    """The hosted KYC session URL. Time-limited: do not cache it."""

    url: str = ""


class ImportSharedKycResponse(GaianModel):
    """The imported KYC session. ``status`` is the provider's own label, not a fixed enum."""

    session_id: str = ""
    status: str = ""


class GetOrganizationBalanceResponse(GaianModel):
    """The tenant's prefund balance. Amounts are decimal strings."""

    currency: str = ""
    available_balance: str = ""
    total_spent: str = ""
    pending_settlement: str = ""
    wallet_address: str = ""
    chain: str | None = None


class QRInfo(GaianModel):
    """The parsed content of a QR payment code. ``amount`` is in ``currency``, as the API sends."""

    is_valid: bool = False
    encoded_string: str = ""
    country: str = ""
    qr_provider: str = ""
    bank_bin: str = ""
    account_number: str = ""
    amount: float | None = None
    currency: str | None = None
    purpose: str | None = None
    beneficiary_name: str = ""
    detailed_qr_info: dict[str, Any] | None = None


class ParseQrResponse(QRInfo):
    """The decoded QR content, plus the bank or wallet name when the QR carries one."""

    bank_name: str | None = None


class Route(GaianModel):
    """The payment route chosen for a quote."""

    route_id: int = 0


class QuoteResponse(GaianModel):
    """A quote for a QR payment.

    ``fiat_amount`` is a JSON number, as the API sends it; the settlement amounts and fees are
    decimal strings. ``chain_id`` is None on a prefund quote.
    """

    quote_id: str = ""
    route: Route = Field(default_factory=Route)
    fiat_amount: float = 0
    fiat_currency: str = ""
    settlement_amount: str = ""
    settlement_base_usd: str = ""
    settlement_currency: str = ""
    chain_id: int | None = None
    exchange_rate: str = ""
    protocol_fee_usd: str = ""
    minimum_fee_usd: str = ""
    tenant_fee_usd: str = ""
    qr_info: QRInfo = Field(default_factory=QRInfo)
    expires_at: str = ""


class DirectQRInfo(GaianModel):
    """The beneficiary of a direct-bank-transfer quote."""

    account_number: str = ""
    beneficiary_name: str = ""
    bank_bin: str = ""
    country: str = ""


class QuoteDirectResponse(GaianModel):
    """A quote for a direct bank transfer. Same amounts as QuoteResponse."""

    quote_id: str = ""
    route: Route = Field(default_factory=Route)
    fiat_amount: float = 0
    fiat_currency: str = ""
    settlement_amount: str = ""
    settlement_base_usd: str = ""
    settlement_currency: str = ""
    chain_id: int | None = None
    exchange_rate: str = ""
    protocol_fee_usd: str = ""
    minimum_fee_usd: str = ""
    tenant_fee_usd: str = ""
    qr_info: DirectQRInfo = Field(default_factory=DirectQRInfo)
    expires_at: str = ""


class PlaceOrderResponse(GaianModel):
    """An order awaiting its on-chain deposit.

    Sign and broadcast ``encoded_transaction``. ``settlement_amount_base_units`` is
    ``settlement_amount`` in the token's smallest unit. ``memo`` is set on chains that need one.
    """

    order_id: str = ""
    status: int = 0
    status_label: str = ""
    chain_id: int = 0
    deposit_address: str = ""
    token_address: str = ""
    settlement_amount: str = ""
    settlement_amount_base_units: str = ""
    settlement_currency: str = ""
    encoded_transaction: str = ""
    expires_at: str = ""
    memo: str | None = None


class PlacePrefundedOrderResponse(GaianModel):
    """An order settled from the tenant's prefunded balance. ``status`` is an OrderStatus value."""

    order_id: str = ""
    status: int = 0
    status_label: str = ""


class VerifyOrderResponse(GaianModel):
    """Outcome of verifying an order's transaction. ``status`` is a VerifyStatus value.

    The API answers HTTP 200 even when verification did not succeed: branch on ``status``.
    """

    order_id: str = ""
    status: int = 0
    status_label: str = ""
    transaction_hash: str = ""
    message: str = ""


class Order(GaianModel):
    """An order as the payment service reports it. ``status`` is an OrderStatus value."""

    order_id: str = ""
    status: int = 0
    status_label: str = ""
    chain_id: int | None = None
    deposit_address: str | None = None
    transaction_hash: str | None = None
    fiat_amount: float = 0
    fiat_currency: str = ""
    settlement_amount: str = ""
    settlement_currency: str = ""
    exchange_rate: str = ""
    created_at: str = ""
    updated_at: str = ""


class Bank(GaianModel):
    """A bank supporting direct transfer. ``code`` is the BIN to pass to the direct endpoints."""

    id: int = 0
    code: str = ""
    name: str = ""


class ListBanksResponse(GaianModel):
    """The banks available for direct transfer in one country."""

    country: str = ""
    banks: list[Bank] = Field(default_factory=list)


class VerifyAccountResponse(GaianModel):
    """Result of a bank account check. A bad account is HTTP 200 with ``valid`` False."""

    country: str = ""
    account_number: str = ""
    code: str = ""
    valid: bool = False
    account_name: str | None = None


class UserDailySpend(GaianModel):
    """The user's rolling 24h spend in USD, across all countries."""

    spent_usd: float = 0
    window_start: str = ""
    window_end: str = ""


class UserVelocityLimit(GaianModel):
    """The user's transaction-count allowance. ``retry_after_seconds`` is 0 while a slot is free."""

    enabled: bool = False
    max_per_window: int = 0
    window_seconds: int = 0
    used_in_window: int = 0
    remaining: int = 0
    retry_after_seconds: int = 0


class UserWeeklyLimit(GaianModel):
    """The user's weekly cap in USD (UTC Monday to Monday)."""

    cap_usd: float = 0
    spent_usd: float = 0
    remaining_usd: float = 0
    window_start: str = ""
    window_end: str = ""


class UserCountryLimit(GaianModel):
    """The user's remaining allowance in one country, in USD. Informational, not for ledger math.

    ``max_per_day_usd``, ``daily_remaining_usd`` and ``weekly`` are None when no such limit applies.
    """

    country: str = ""
    supported: bool = False
    kyc_verified: bool = False
    can_transact: bool = False
    max_per_day_usd: float | None = None
    daily_remaining_usd: float | None = None
    weekly: UserWeeklyLimit | None = None
    max_next_transaction_usd: float = 0


class GetUserLimitsResponse(GaianModel):
    """A user's limits: daily spend, velocity, and one entry per country."""

    user_id: str | None = None
    daily: UserDailySpend = Field(default_factory=UserDailySpend)
    velocity: UserVelocityLimit = Field(default_factory=UserVelocityLimit)
    countries: list[UserCountryLimit] = Field(default_factory=list)


class ExchangeRate(GaianModel):
    """One indicative rate: fiat units per settlement token, as a decimal string."""

    country: str = ""
    fiat_currency: str = ""
    settlement_currency: str = ""
    route_id: int = 0
    exchange_rate: str = ""
    captured_at: str = ""


class GetExchangeRatesResponse(GaianModel):
    """Indicative rates. A country missing from ``rates`` is not quotable right now."""

    indicative_only: bool = False
    rates: list[ExchangeRate] = Field(default_factory=list)
