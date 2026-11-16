from __future__ import annotations

from . import _kyc, _organization, _payments, _users
from ._core import AsyncGateway, SyncGateway, async_endpoint, sync_endpoint


class GaianClient(SyncGateway):
    """Blocking client for the Gaian v2 API. Every endpoint is a method on the client.

    Every request is signed with ``api_key`` and ``secret_key``. The secret key is for servers
    only: never ship it in a browser or a mobile app. ``environment`` defaults to the sandbox;
    ``base_url`` overrides it. ``timeout`` is in seconds and is ignored when ``http_client`` is
    given. With ``debug=True`` the method, path and status of each call go to ``logger``
    (default ``logging.getLogger("gaian")``) at DEBUG level; headers and bodies are never logged.

    Methods take keyword arguments only and return the API envelope (``request_id``, ``data``,
    and ``success`` on payment endpoints). They raise GaianAPIError for a status of 400 or
    above, GaianTimeoutError or GaianConnectionError when no response arrived, and ValueError
    for an empty path parameter.

    Usage::

        with GaianClient(api_key="...", secret_key="...") as client:
            user_id = client.create_user().data.user_id
    """

    create_user = sync_endpoint(_users.create_user)
    get_user_by_id = sync_endpoint(_users.get_user_by_id)
    get_user_by_wallet = sync_endpoint(_users.get_user_by_wallet)
    list_user_orders = sync_endpoint(_users.list_user_orders)
    get_user_order = sync_endpoint(_users.get_user_order)
    get_markets = sync_endpoint(_users.get_markets)
    get_market_requirements = sync_endpoint(_users.get_market_requirements)
    get_payment_methods = sync_endpoint(_users.get_payment_methods)
    create_wallet = sync_endpoint(_users.create_wallet)
    list_wallets = sync_endpoint(_users.list_wallets)

    submit_kyc = sync_endpoint(_kyc.submit_kyc)
    update_kyc = sync_endpoint(_kyc.update_kyc)
    generate_kyc_link = sync_endpoint(_kyc.generate_kyc_link)
    import_shared_kyc = sync_endpoint(_kyc.import_shared_kyc)

    get_organization_balance = sync_endpoint(_organization.get_organization_balance)

    parse_qr = sync_endpoint(_payments.parse_qr)
    quote = sync_endpoint(_payments.quote)
    quote_prefund = sync_endpoint(_payments.quote_prefund)
    quote_direct = sync_endpoint(_payments.quote_direct)
    quote_direct_prefund = sync_endpoint(_payments.quote_direct_prefund)
    place_order = sync_endpoint(_payments.place_order)
    place_prefunded_order = sync_endpoint(_payments.place_prefunded_order)
    verify_order = sync_endpoint(_payments.verify_order)
    get_order_status = sync_endpoint(_payments.get_order_status)
    list_banks = sync_endpoint(_payments.list_banks)
    verify_account = sync_endpoint(_payments.verify_account)
    get_user_limits = sync_endpoint(_payments.get_user_limits)
    get_exchange_rates = sync_endpoint(_payments.get_exchange_rates)


class AsyncGaianClient(AsyncGateway):
    """Asyncio client for the Gaian v2 API. Same options and methods as GaianClient, awaited.

    Usage::

        async with AsyncGaianClient(api_key="...", secret_key="...") as client:
            user_id = (await client.create_user()).data.user_id
    """

    create_user = async_endpoint(_users.create_user)
    get_user_by_id = async_endpoint(_users.get_user_by_id)
    get_user_by_wallet = async_endpoint(_users.get_user_by_wallet)
    list_user_orders = async_endpoint(_users.list_user_orders)
    get_user_order = async_endpoint(_users.get_user_order)
    get_markets = async_endpoint(_users.get_markets)
    get_market_requirements = async_endpoint(_users.get_market_requirements)
    get_payment_methods = async_endpoint(_users.get_payment_methods)
    create_wallet = async_endpoint(_users.create_wallet)
    list_wallets = async_endpoint(_users.list_wallets)

    submit_kyc = async_endpoint(_kyc.submit_kyc)
    update_kyc = async_endpoint(_kyc.update_kyc)
    generate_kyc_link = async_endpoint(_kyc.generate_kyc_link)
    import_shared_kyc = async_endpoint(_kyc.import_shared_kyc)

    get_organization_balance = async_endpoint(_organization.get_organization_balance)

    parse_qr = async_endpoint(_payments.parse_qr)
    quote = async_endpoint(_payments.quote)
    quote_prefund = async_endpoint(_payments.quote_prefund)
    quote_direct = async_endpoint(_payments.quote_direct)
    quote_direct_prefund = async_endpoint(_payments.quote_direct_prefund)
    place_order = async_endpoint(_payments.place_order)
    place_prefunded_order = async_endpoint(_payments.place_prefunded_order)
    verify_order = async_endpoint(_payments.verify_order)
    get_order_status = async_endpoint(_payments.get_order_status)
    list_banks = async_endpoint(_payments.list_banks)
    verify_account = async_endpoint(_payments.verify_account)
    get_user_limits = async_endpoint(_payments.get_user_limits)
    get_exchange_rates = async_endpoint(_payments.get_exchange_rates)
