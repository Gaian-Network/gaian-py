from __future__ import annotations

from ._core import Call, required, without_empty
from ._models import (
    CreateUserResponse,
    GetMarketRequirementsResponse,
    GetMarketsResponse,
    ListUserOrdersResponse,
    PaymentMethod,
    User,
    UserOrder,
    UserResponse,
    WalletInfo,
)


def create_user() -> Call[UserResponse[CreateUserResponse]]:
    """Creates an empty user and returns its id.

    Fill the record in later with ``submit_kyc`` and ``create_wallet``.
    """
    return Call("POST", ("users",), UserResponse[CreateUserResponse])


def get_user_by_id(*, user_id: str) -> Call[UserResponse[User]]:
    """Returns a user by id. Raises GaianAPIError with code NOT_FOUND when there is none."""
    return Call("GET", ("users", required("user_id", user_id)), UserResponse[User])


def get_user_by_wallet(*, wallet_address: str) -> Call[UserResponse[User]]:
    """Returns the user a wallet address is linked to."""
    segments = ("users", "wallet", required("wallet_address", wallet_address))
    return Call("GET", segments, UserResponse[User])


def list_user_orders(
    *,
    user_id: str,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> Call[ListUserOrdersResponse]:
    """Returns one page of a user's order history, optionally filtered by status.

    The result is not the usual envelope: ``data`` is the list and ``pagination`` sits next to it.
    """
    return Call(
        "GET",
        ("users", required("user_id", user_id), "orders"),
        ListUserOrdersResponse,
        query={"status": status, "page": page, "page_size": page_size},
    )


def get_user_order(*, user_id: str, order_id: str) -> Call[UserResponse[UserOrder]]:
    """Returns one order of a user."""
    segments = ("users", required("user_id", user_id), "orders", required("order_id", order_id))
    return Call("GET", segments, UserResponse[UserOrder])


def get_markets(*, user_id: str) -> Call[UserResponse[GetMarketsResponse]]:
    """Returns the user's gating status in every market."""
    segments = ("users", required("user_id", user_id), "markets")
    return Call("GET", segments, UserResponse[GetMarketsResponse])


def get_market_requirements(*, user_id: str) -> Call[UserResponse[GetMarketRequirementsResponse]]:
    """Returns, per market, the KYC fields required and the ones the user still has to provide."""
    segments = ("users", required("user_id", user_id), "markets", "requirements")
    return Call("GET", segments, UserResponse[GetMarketRequirementsResponse])


def get_payment_methods(*, user_id: str) -> Call[UserResponse[list[PaymentMethod]]]:
    """Returns the payment methods known for the user and the gating status of each."""
    segments = ("users", required("user_id", user_id), "payment-methods")
    return Call("GET", segments, UserResponse[list[PaymentMethod]])


def create_wallet(
    *, user_id: str, address: str, chain: str | None = None
) -> Call[UserResponse[WalletInfo]]:
    """Links a wallet to a user. The first wallet becomes the primary one."""
    return Call(
        "POST",
        ("users", required("user_id", user_id), "wallets"),
        UserResponse[WalletInfo],
        body={"address": address, **without_empty(chain=chain)},
    )


def list_wallets(*, user_id: str) -> Call[UserResponse[list[WalletInfo]]]:
    """Returns every wallet linked to a user. Not paginated."""
    segments = ("users", required("user_id", user_id), "wallets")
    return Call("GET", segments, UserResponse[list[WalletInfo]])
