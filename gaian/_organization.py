from __future__ import annotations

from ._core import Call
from ._models import GetOrganizationBalanceResponse, UserResponse


def get_organization_balance() -> Call[UserResponse[GetOrganizationBalanceResponse]]:
    """Returns the prefund balance of the tenant that owns the API key."""
    return Call(
        "GET", ("organization", "me", "balance"), UserResponse[GetOrganizationBalanceResponse]
    )
