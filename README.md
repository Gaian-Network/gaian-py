# gaian-py

Python client for the [Gaian Network](https://gaian.network) v2 API: user onboarding, KYC, wallets and crypto-to-fiat payments through one signed gateway.

Sync and async clients with the same methods.

> **2.0.0 is a breaking release.** Version 1 (`0.1.0`) talked to the retired v1 hosts with an `x-api-key` header and cannot call the current API. Nothing from v1 carries over unchanged: see [Upgrading from v1](#upgrading-from-v1).

## Installation

```bash
pip install gaian
```

Requires Python 3.11+. Runtime dependencies: `httpx`, `pydantic`.

## Quick start

```python
import os

import gaian

with gaian.GaianClient(
    api_key=os.environ["GAIAN_API_KEY"],
    secret_key=os.environ["GAIAN_API_SECRET"],
) as client:
    resp = client.create_user()
    print(resp.data.user_id, resp.request_id)
```

Async:

```python
async with gaian.AsyncGaianClient(api_key=..., secret_key=...) as client:
    resp = await client.create_user()
```

Every endpoint is a method on the client and takes keyword arguments only. Every method returns the API envelope: `request_id` and `data`, plus `success` on payment endpoints. `list_user_orders` is the exception: `data` is the list and `pagination` sits next to it. `data` is typed as optional because the API may send `null` (for example after `update_kyc`); under a type checker, check it before use.

## Authentication

Each request is signed with HMAC-SHA256 using the API key and secret key issued in the Client Admin Portal. The client adds `X-Gaian-Key`, `X-Gaian-Signature`, `X-Gaian-Timestamp` and a UUID `X-Request-ID`.

The secret key is shown once at creation. Keep it on your server: never ship it in a browser or a mobile app, and never commit it.

| Environment | Base URL |
|---|---|
| `Environment.SANDBOX` (default) | `https://sandbox.gaian.network` |
| `Environment.PRODUCTION` | `https://api.gaian.network` |

```python
client = gaian.GaianClient(
    api_key=...,
    secret_key=...,
    environment=gaian.Environment.PRODUCTION,
)
```

## Users, wallets and KYC

```python
user_id = client.create_user().data.user_id

client.create_wallet(user_id=user_id, address="So1anaAddr", chain="solana")
wallets = client.list_wallets(user_id=user_id).data

user = client.get_user_by_id(user_id=user_id).data
same = client.get_user_by_wallet(wallet_address="So1anaAddr").data
```

Hosted KYC, or direct submission:

```python
url = client.generate_kyc_link(user_id=user_id, callback_url="https://example.com/cb").data.url

client.submit_kyc(
    user_id=user_id,
    first_name="Nguyen",
    last_name="Van A",
    email="a@example.com",
    date_of_birth="1990-01-15",
    nationality="VN",
    national_id="012345678901",
    type=gaian.DocumentType.ID_CARD,
    expiry_date="2030-01-01",
    address_line1="123 Le Loi",
    city="HCMC",
    country_of_residence="VN",
    occupation=gaian.Occupation.PROFESSIONAL,
    phone_country_code="+84",  # optional
    phone_number="912345678",  # optional
)

client.update_kyc(user_id=user_id, phone_number="987654321")
client.import_shared_kyc(user_id=user_id, share_token="...")
```

An optional KYC field left as `None` or `""` is not sent. `update_kyc` therefore cannot clear a field.

What the user may do, and what is still missing:

```python
client.get_markets(user_id=user_id).data.markets["VN"].status  # gaian.MarketStatus value
client.get_market_requirements(user_id=user_id).data.markets["VN"].missing_fields
client.get_payment_methods(user_id=user_id).data  # list of PaymentMethod
client.get_user_limits(user_id=user_id, country="VN").data.countries[0].max_next_transaction_usd
```

## Payments

Standard flow, settled on-chain:

```
quote -> place_order -> sign and broadcast -> verify_order -> get_order_status (poll)
```

```python
qr = client.parse_qr(qr_string=qr_string).data

quote = client.quote(
    qr_string=qr_string,
    amount=150000,  # fiat amount, a JSON number
    chain_id=gaian.Chain.SOLANA,
    settlement_currency="USDC",
    user_id=user_id,  # or wallet_address=..., or email=...
).data

order = client.place_order(quote_id=quote.quote_id).data
tx_hash = broadcast(order.encoded_transaction)  # your code

verified = client.verify_order(order_id=order.order_id, transaction_hash=tx_hash).data
if verified.status != gaian.VerifyStatus.VERIFIED:
    ...  # HTTP 200 does not mean verified: PENDING means resubmit later, FAILED see message

status = client.get_order_status(order_id=order.order_id).data
done = gaian.is_terminal(status.status)
```

Prefunded flow, settled from the tenant balance with no on-chain step:

```python
quote = client.quote_prefund(
    qr_string=qr_string, amount=150000, settlement_currency="USDC", user_id=user_id
).data
order = client.place_prefunded_order(quote_id=quote.quote_id).data
balance = client.get_organization_balance().data.available_balance
```

Direct bank transfer (production only):

```python
banks = client.list_banks(country="VN").data.banks
check = client.verify_account(account_number="0123456789", code=banks[0].code, country="VN").data
if check.valid:
    client.quote_direct(
        account_number="0123456789",
        code=banks[0].code,
        amount=150000,
        country="VN",
        chain_id=gaian.Chain.SOLANA,
        settlement_currency="USDC",
        user_id=user_id,
    )
    # quote_direct_prefund takes the same arguments without chain_id
```

Indicative rates (not binding, only a quote locks a rate):

```python
client.get_exchange_rates(country="VN", settlement_currency="USDC").data.rates
```

Order history as the user service reports it:

```python
page = client.list_user_orders(user_id=user_id, status="completed", page=1, page_size=20)
page.data, page.pagination.total_count
client.get_user_order(user_id=user_id, order_id="ord_1").data
```

### Amounts

`amount` in quote requests and `fiat_amount` in responses are JSON numbers because the API requires them. Settlement amounts, fees, rates and balances are decimal strings: parse them with `decimal.Decimal`, not `float`. The USD figures of `get_user_limits` are numbers and are informational only.

## Webhooks

Verify a delivery before trusting it. Pass the body exactly as received, as `bytes`; a body that was parsed and re-serialized will not verify.

```python
try:
    gaian.verify_webhook(
        secret=os.environ["GAIAN_WEBHOOK_SECRET"],
        signature=request.headers["X-Gaian-Signature"],
        timestamp=request.headers["X-Gaian-Timestamp"],
        body=raw_body,
    )
except gaian.WebhookVerificationError:
    return 400
```

A timestamp more than 300 seconds from the local clock, past or future, is rejected. Change it with `tolerance_seconds`.

## Error handling

```python
try:
    client.place_order(quote_id=quote_id)
except gaian.GaianAPIError as err:
    print(err.status_code, err.code, err.api_code, err.message, err.request_id)
    if gaian.is_conflict(err):
        ...  # quote expired or already consumed
except gaian.GaianTimeoutError:
    ...  # no answer in time; the order may still have been created
except gaian.GaianConnectionError:
    ...  # the request did not get a response
```

| Exception | When |
|---|---|
| `GaianAPIError` | HTTP status 400 or above. `code` comes from the status (`BAD_REQUEST`, `UNAUTHORIZED`, `PAYMENT_REQUIRED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `UNPROCESSABLE_ENTITY`, `RATE_LIMITED`, `SERVER_ERROR`, `UNKNOWN`); `api_code` is the service's own code when it sends one (`IDENTITY_REQUIRED`, ...); `body` is the raw response body |
| `GaianTimeoutError` | The request timed out (subclass of `GaianConnectionError`) |
| `GaianConnectionError` | No response: DNS, refused connection, TLS |
| `GaianInvalidResponseError` | A 2xx response whose body could not be decoded. The API accepted the request |
| `WebhookVerificationError` | `verify_webhook` rejected a signature or timestamp |
| `ValueError` | A path parameter such as `user_id` is empty; raised before any request |

All of them except `ValueError` derive from `GaianError`. `is_not_found`, `is_conflict`, `is_unauthorized`, `is_forbidden` and `is_rate_limited` also recognise an error raised `from` a `GaianAPIError`.

The SDK does not retry. Quote `request_id` when you contact Gaian support.

## Configuration

```python
client = gaian.GaianClient(
    api_key=...,
    secret_key=...,
    environment=gaian.Environment.SANDBOX,  # default
    base_url=None,  # overrides environment, for a proxy or a test server
    timeout=30.0,  # seconds; ignored when http_client is given
    http_client=None,  # your own httpx.Client (AsyncClient for the async client)
    debug=False,
    logger=None,  # default logging.getLogger("gaian")
)
```

With `debug=True` the client logs the method, path and status of each call at `DEBUG` level. Headers, query strings and bodies are never logged. A client you pass as `http_client` is not closed by the SDK.

Response models are pydantic models with snake_case attributes. Unknown fields are ignored. A field the API omits or sends as `null` takes its default: `None` for a nullable field, otherwise an empty value (`""`, `0`, `False`, an empty list).

## Upgrading from v1

| v1 (`0.1.0`) | 2.0.0 |
|---|---|
| `GaianClient(api_key=..., env=...)` | `GaianClient(api_key=..., secret_key=..., environment=...)` |
| `x-api-key` header, separate user and payment hosts | HMAC-signed requests to one gateway |
| `client.user.*`, `client.payment.*`, `client.tenant.*`, `client.policy.*` | Flat methods on the client, keyword arguments only |
| Methods return the model | Methods return the envelope; the model is `.data` |
| `user.register(wallet)` | `create_user()` then `create_wallet(user_id=..., address=...)` |
| `payment.calculate_exchange`, `payment.place_order(request)` | `quote(...)` then `place_order(quote_id=...)` |
| `policy.check_policy`, `tenant.get_spend` | Removed from the API. See `get_markets`, `get_user_limits`, `get_organization_balance` |
| `GaianAPIError.error` | `GaianAPIError.code`, `.api_code`, `.request_id`, `.body` |

To stay on v1, pin `gaian==0.1.0`.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy gaian
```

The tests run against a fake gateway and need no network or keys. `tests/data/signature-vectors.json` holds the signing vectors shared with the Go and TypeScript SDKs.
