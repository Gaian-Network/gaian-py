# gaian-py

Python client for the [Gaian Network](https://gaian.network) API — payment processing across Vietnam, Philippines, and Brazil via QR code and stablecoin settlement.

Supports both **sync** and **async** usage.

## Installation

```bash
pip install gaian
```

Requires Python 3.11+. Dependencies: `httpx`, `pydantic`.

## Quick start

```python
import gaian

# Sync
with gaian.GaianClient(api_key="your-api-key", env=gaian.Environment.SANDBOX) as client:
    user = client.user.register("0xWalletAddress")

# Async
async with gaian.AsyncGaianClient(api_key="your-api-key", env=gaian.Environment.SANDBOX) as client:
    user = await client.user.register("0xWalletAddress")
```

Get your API key from the [Client Admin Portal](https://client-admin.gaian-dev.network/). Keys are shown only once at creation — store them securely.

---

## Environments

| Constant | User API | Payment API |
|----------|----------|-------------|
| `Environment.SANDBOX` | `dev-user.gaian-dev.network` | `dev-payments.gaian-dev.network` |
| `Environment.PRODUCTION` | `user.gaian-dev.network` | `payments.gaian-dev.network` |

---

## Authentication

All requests require the `x-api-key` header. The client sets this automatically.

```python
import os
import gaian

client = gaian.GaianClient(
    api_key=os.environ["GAIAN_API_KEY"],
    env=gaian.Environment.SANDBOX,
)
```

> **Never** hardcode API keys or commit them to version control.

---

## Payment flows

### Standard flow (on-chain signing required)

```
Register → KYC → Check Policy → Parse QR → Calculate Exchange
→ Place Order → Sign & Broadcast Transaction → Verify Order → Poll Status
```

### Prefunded flow (no on-chain signing)

```
Place Prefunded Order → Poll Status
```

---

## Usage

### User

#### Register a user

Idempotent — returns the existing user if the wallet is already registered.

```python
try:
    user = client.user.register("0xWalletAddress")
except gaian.GaianAPIError as e:
    if not gaian.is_conflict(e):
        raise

print(user.id, user.kyc_status)
```

#### Get user by ID or wallet

```python
user = client.user.get_by_id(42)

user = client.user.get_by_wallet("0xWalletAddress")
```

#### Check market availability

```python
markets = client.user.get_markets("0xWalletAddress")

if markets["VN"].status != gaian.MarketStatus.APPROVED:
    print("Vietnam not available:", markets["VN"].reject_reason)
```

#### List orders

```python
result = client.user.list_orders_by_wallet(
    "0xWalletAddress",
    page=1,
    limit=20,
    status=gaian.OrderStatus.COMPLETED,  # optional
)

for order in result.items:
    print(order.order_id, order.status, order.fiat_amount, order.fiat_currency)

print("total:", result.pagination.total)
```

---

### KYC

#### Generate a Sumsub KYC link

The returned URL is time-limited. Generate it on demand — do not cache.

```python
url = client.user.generate_kyc_link("0xWalletAddress")
# Redirect user to url
```

#### Submit KYC information directly

```python
status = client.user.submit_kyc(gaian.SubmitKYCRequest(
    user_wallet_address="0xWalletAddress",
    user_email="user@example.com",
    first_name="Nguyen",
    last_name="Van A",
    date_of_birth="1990-01-15",
    gender="male",
    nationality="VN",
    type="national_id",
    national_id="012345678901",
    issue_date="2015-01-01",
    expiry_date="2025-01-01",
    address_line1="123 Le Loi",
    address_line2="",
    city="Ho Chi Minh City",
    state="HCM",
    zip_code="70000",
    front_id_image="<base64>",
    back_id_image="<base64>",
    hold_id_image="<base64>",
    phone_number="912345678",
    phone_country_code="+84",
))
```

---

### Policy

Check whether a wallet can make a payment in a given market and get transaction limits.

```python
policy = client.policy.check_policy("0xWalletAddress", "VN")

if not policy.is_allowed:
    raise Exception(f"payment blocked: {policy.reason}")

print(f"tier={policy.tier}  per-tx=${policy.limits.per_transaction:.0f}")
```

| Tier | Description |
|------|-------------|
| `PolicyTier.KYC` | KYC-verified, higher limits |
| `PolicyTier.NON_KYC` | Unverified, lower limits |

---

### Payment

#### Parse a QR code

Supports EMVCO QR codes from Vietnam, Philippines, Thailand, and Brazil.

```python
info = client.payment.parse_qr(qr_string)
# Optional country hint:
info = client.payment.parse_qr(qr_string, country="VN")

# Nullable fields — check before use
if info.amount and info.currency:
    print(f"{info.amount:.0f} {info.currency}")
if info.beneficiary_name:
    print(info.beneficiary_name)
```

#### Calculate exchange rate

```python
exchange = client.payment.calculate_exchange(gaian.CalculateExchangeRequest(
    amount=500000,
    country="VN",
    chain=gaian.Chain.SOLANA,
    token=gaian.CryptoCurrency.USDC,
))

print(f"need {exchange.crypto_amount} {exchange.crypto_currency}")
print(f"rate={exchange.exchange_rate}  fee={exchange.fee_amount}")
```

#### Place a standard order

```python
order = client.payment.place_order(gaian.PlaceOrderRequest(
    qr_string=qr_string,
    amount=500000,
    crypto_currency=gaian.CryptoCurrency.USDC,
    from_address="0xWalletAddress",
    fiat_currency=gaian.FiatCurrency.VND,
    chain=gaian.Chain.SOLANA,
))

# order.crypto_transfer_info contains destination wallet and amount.
# Build and sign the Solana transaction (legacy format, NOT VersionedTransaction),
# then call verify_order with the transaction signature.
```

#### Verify the on-chain transaction

```python
result = client.payment.verify_order(order.order_id, tx_signature)
print(result.status, result.bank_transfer_status)
```

#### Place a prefunded order

No on-chain signing required. Uses the tenant's prefunded balance.

```python
order = client.payment.place_prefunded_order(gaian.PlacePrefundedOrderRequest(
    qr_string=qr_string,
    amount=500000,
    crypto_currency=gaian.CryptoCurrency.USDC,
    from_address="0xWalletAddress",
    fiat_currency=gaian.FiatCurrency.VND,
))
```

#### Poll order status

Poll until the order reaches a terminal state.

```python
import time

while True:
    status = client.payment.get_order_status(order.order_id)
    print("status:", status.status)
    if status.status in (gaian.OrderStatus.COMPLETED, gaian.OrderStatus.FAILED):
        break
    time.sleep(3)
```

| Status | Description |
|--------|-------------|
| `OrderStatus.AWAITING_CRYPTO_TRANSFER` | Waiting for on-chain transaction |
| `OrderStatus.VERIFIED` | Transaction confirmed, bank transfer queued |
| `OrderStatus.PROCESSING` | Bank transfer in progress |
| `OrderStatus.COMPLETED` | Payment successful |
| `OrderStatus.FAILED` | Payment failed |

---

### Tenant

```python
# Prefunded balance
balance = client.tenant.get_balance(gaian.CryptoCurrency.USDC)
print(f"{balance.available_balance:.4f} {balance.currency} available")

# Spend cap usage
spend = client.tenant.get_total_spent()
print(f"spent ${spend.total_spent:.2f} of ${spend.limit:.2f}")
```

---

## Async usage

Every method has an async equivalent. Use `AsyncGaianClient` with `async with` and `await`.

```python
import asyncio
import gaian

async def main():
    async with gaian.AsyncGaianClient(
        api_key="your-api-key",
        env=gaian.Environment.SANDBOX,
    ) as client:
        user = await client.user.register("0xWalletAddress")

        policy = await client.policy.check_policy("0xWalletAddress", "VN")
        if not policy.is_allowed:
            return

        order = await client.payment.place_prefunded_order(
            gaian.PlacePrefundedOrderRequest(
                qr_string="...",
                amount=500000,
                crypto_currency=gaian.CryptoCurrency.USDC,
                from_address="0xWalletAddress",
                fiat_currency=gaian.FiatCurrency.VND,
            )
        )

        while True:
            status = await client.payment.get_order_status(order.order_id)
            if status.status in (gaian.OrderStatus.COMPLETED, gaian.OrderStatus.FAILED):
                break
            await asyncio.sleep(3)

asyncio.run(main())
```

---

## Error handling

All methods raise `GaianAPIError` on API errors. Use the helper functions to check the type.

```python
try:
    user = client.user.get_by_id(999)
except gaian.GaianAPIError as e:
    if gaian.is_not_found(e):
        print("user not found")
    elif gaian.is_unauthorized(e):
        print("invalid api key")
    elif gaian.is_conflict(e):
        print("resource already exists")
    elif gaian.is_forbidden(e):
        print("insufficient permissions")
    else:
        print(f"api error {e.status_code}: {e.message}")
```

---

## Configuration

```python
import httpx
import gaian

# Custom timeout
client = gaian.GaianClient(
    api_key="...",
    env=gaian.Environment.SANDBOX,
    timeout=15.0,
)

# Custom httpx client (sync) — add retries, proxies, middleware, etc.
transport = httpx.HTTPTransport(retries=3)
http_client = httpx.Client(transport=transport)

client = gaian.GaianClient(
    api_key="...",
    env=gaian.Environment.SANDBOX,
    http_client=http_client,
)

# Custom httpx.AsyncClient
async_client = gaian.AsyncGaianClient(
    api_key="...",
    env=gaian.Environment.SANDBOX,
    http_client=httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=3)),
)
```

---

## Supported currencies and chains

| Type | Values |
|------|--------|
| Fiat | `FiatCurrency.VND` (Vietnam), `FiatCurrency.PHP` (Philippines), `FiatCurrency.BRL` (Brazil) |
| Crypto | `CryptoCurrency.USDC`, `CryptoCurrency.USDT` |
| Chains | `Chain.SOLANA`, `Chain.ETHEREUM`, `Chain.POLYGON`, `Chain.ARBITRUM`, `Chain.BASE` |

> Currently only Solana is fully supported for exchange calculation and prefunded orders.

---

## License

MIT
