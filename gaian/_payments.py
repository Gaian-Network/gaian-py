from __future__ import annotations

from ._core import Call, required, without_empty
from ._models import (
    GetExchangeRatesResponse,
    GetUserLimitsResponse,
    ListBanksResponse,
    Order,
    ParseQrResponse,
    PaymentResponse,
    PlaceOrderResponse,
    PlacePrefundedOrderResponse,
    QuoteDirectResponse,
    QuoteResponse,
    VerifyAccountResponse,
    VerifyOrderResponse,
)


def parse_qr(
    *,
    qr_string: str,
    country: str | None = None,
    network: str | None = None,
    user_id: str | None = None,
    email: str | None = None,
    wallet_address: str | None = None,
) -> Call[PaymentResponse[ParseQrResponse]]:
    """Decodes a QR payment code without creating a quote.

    ``country`` is an optional ISO 3166-1 alpha-2 hint; ``network`` is a QrNetwork (Peru only).
    Some markets answer 400 ``IDENTITY_REQUIRED`` unless one of ``user_id``, ``email`` or
    ``wallet_address`` identifies the payer.
    """
    return Call(
        "POST",
        ("parseQr",),
        PaymentResponse[ParseQrResponse],
        body={
            "qrString": qr_string,
            **without_empty(
                country=country,
                network=network,
                userId=user_id,
                email=email,
                walletAddress=wallet_address,
            ),
        },
    )


def quote(
    *,
    qr_string: str,
    amount: float,
    chain_id: int,
    settlement_currency: str,
    country: str | None = None,
    network: str | None = None,
    user_id: str | None = None,
    wallet_address: str | None = None,
    email: str | None = None,
    from_address: str | None = None,
) -> Call[PaymentResponse[QuoteResponse]]:
    """Creates a single-use quote (about 120 s) for a QR payment settled on-chain.

    ``amount`` is in the fiat currency of the QR and is sent as a JSON number; ``chain_id`` is
    a Chain value. Identify the payer with one of ``user_id``, ``wallet_address`` or ``email``:
    the API answers 400 otherwise. ``from_address`` is the address the deposit comes from when
    it is not a wallet linked to the payer. Consume the quote with ``place_order``.
    """
    return Call(
        "POST",
        ("quote",),
        PaymentResponse[QuoteResponse],
        body={
            "qrString": qr_string,
            "amount": amount,
            "chainId": chain_id,
            "settlementCurrency": settlement_currency,
            **without_empty(
                country=country,
                network=network,
                userId=user_id,
                walletAddress=wallet_address,
                email=email,
                fromAddress=from_address,
            ),
        },
    )


def quote_prefund(
    *,
    qr_string: str,
    amount: float,
    settlement_currency: str,
    country: str | None = None,
    network: str | None = None,
    user_id: str | None = None,
    wallet_address: str | None = None,
    email: str | None = None,
) -> Call[PaymentResponse[QuoteResponse]]:
    """Creates a single-use quote for a QR payment settled from the tenant's prefunded balance.

    Same parameters as ``quote`` without the on-chain ones. Consume it with
    ``place_prefunded_order``.
    """
    return Call(
        "POST",
        ("quote", "prefund"),
        PaymentResponse[QuoteResponse],
        body={
            "qrString": qr_string,
            "amount": amount,
            "settlementCurrency": settlement_currency,
            **without_empty(
                country=country,
                network=network,
                userId=user_id,
                walletAddress=wallet_address,
                email=email,
            ),
        },
    )


def quote_direct(
    *,
    account_number: str,
    code: str,
    amount: float,
    country: str,
    chain_id: int,
    settlement_currency: str,
    wallet_address: str | None = None,
    user_id: str | None = None,
    email: str | None = None,
    from_address: str | None = None,
    beneficiary_name: str | None = None,
) -> Call[PaymentResponse[QuoteDirectResponse]]:
    """Creates a single-use quote for a direct bank transfer settled on-chain. Production only.

    ``code`` is a bank code from ``list_banks``. ``beneficiary_name`` is accepted but ignored
    by the API: the bank-verified name wins. Consume the quote with ``place_order``.
    """
    return Call(
        "POST",
        ("quote", "direct"),
        PaymentResponse[QuoteDirectResponse],
        body={
            "accountNumber": account_number,
            "code": code,
            "amount": amount,
            "country": country,
            "chainId": chain_id,
            "settlementCurrency": settlement_currency,
            **without_empty(
                walletAddress=wallet_address,
                userId=user_id,
                email=email,
                fromAddress=from_address,
                beneficiaryName=beneficiary_name,
            ),
        },
    )


def quote_direct_prefund(
    *,
    account_number: str,
    code: str,
    amount: float,
    country: str,
    settlement_currency: str,
    wallet_address: str | None = None,
    user_id: str | None = None,
    email: str | None = None,
    beneficiary_name: str | None = None,
) -> Call[PaymentResponse[QuoteDirectResponse]]:
    """Creates a single-use quote for a direct bank transfer settled from the prefunded balance.

    Production only. Consume it with ``place_prefunded_order``.
    """
    return Call(
        "POST",
        ("quote", "direct", "prefund"),
        PaymentResponse[QuoteDirectResponse],
        body={
            "accountNumber": account_number,
            "code": code,
            "amount": amount,
            "country": country,
            "settlementCurrency": settlement_currency,
            **without_empty(
                walletAddress=wallet_address,
                userId=user_id,
                email=email,
                beneficiaryName=beneficiary_name,
            ),
        },
    )


def place_order(*, quote_id: str) -> Call[PaymentResponse[PlaceOrderResponse]]:
    """Consumes a quote from ``quote`` or ``quote_direct`` and creates an order.

    Sign and broadcast the returned transaction, then call ``verify_order``. Raises
    GaianAPIError with code CONFLICT when the quote is expired, consumed or a prefund quote.
    """
    return Call(
        "POST", ("orders",), PaymentResponse[PlaceOrderResponse], body={"quoteId": quote_id}
    )


def place_prefunded_order(*, quote_id: str) -> Call[PaymentResponse[PlacePrefundedOrderResponse]]:
    """Consumes a prefund quote and creates an order settled from the prefunded balance.

    There is no on-chain step: poll ``get_order_status`` next.
    """
    return Call(
        "POST",
        ("orders", "prefund"),
        PaymentResponse[PlacePrefundedOrderResponse],
        body={"quoteId": quote_id},
    )


def verify_order(
    *, order_id: str, transaction_hash: str
) -> Call[PaymentResponse[VerifyOrderResponse]]:
    """Submits the on-chain transaction hash of an order.

    The API answers HTTP 200 even when verification did not succeed: branch on ``data.status``.
    """
    return Call(
        "POST",
        ("orders", required("order_id", order_id), "verify"),
        PaymentResponse[VerifyOrderResponse],
        body={"transactionHash": transaction_hash},
    )


def get_order_status(*, order_id: str) -> Call[PaymentResponse[Order]]:
    """Returns the current state of an order. Poll until ``is_terminal(data.status)``."""
    return Call("GET", ("orders", required("order_id", order_id)), PaymentResponse[Order])


def list_banks(*, country: str) -> Call[PaymentResponse[ListBanksResponse]]:
    """Returns the banks supporting direct transfer in a country. Production only."""
    return Call("GET", ("banks",), PaymentResponse[ListBanksResponse], query={"country": country})


def verify_account(
    *, account_number: str, code: str, country: str
) -> Call[PaymentResponse[VerifyAccountResponse]]:
    """Checks a beneficiary bank account before a direct quote. Production only.

    A bad account is not an error: check ``data.valid``.
    """
    return Call(
        "POST",
        ("accounts", "verify"),
        PaymentResponse[VerifyAccountResponse],
        body={"accountNumber": account_number, "code": code, "country": country},
    )


def get_user_limits(
    *, user_id: str, country: str | None = None
) -> Call[PaymentResponse[GetUserLimitsResponse]]:
    """Returns how much a user can still spend, per country, and the remaining velocity allowance.

    Omit ``country`` to get every configured country.
    """
    return Call(
        "GET",
        ("limits", "user"),
        PaymentResponse[GetUserLimitsResponse],
        query={"userId": user_id, "country": country},
    )


def get_exchange_rates(
    *, country: str | None = None, settlement_currency: str | None = None
) -> Call[PaymentResponse[GetExchangeRatesResponse]]:
    """Returns indicative exchange rates. Not binding: only a quote locks a rate.

    Omit ``country`` to get every supported country; ``settlement_currency`` defaults to USDC
    on the server.
    """
    return Call(
        "GET",
        ("exchange-rate",),
        PaymentResponse[GetExchangeRatesResponse],
        query={"country": country, "settlementCurrency": settlement_currency},
    )
