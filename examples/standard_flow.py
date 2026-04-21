"""Standard payment flow: register → policy check → parse QR → place order → verify → poll."""

import asyncio
import os
import time

import gaian

API_KEY = os.environ["GAIAN_API_KEY"]
WALLET = "YOUR_WALLET_ADDRESS"
QR_STRING = "PASTE_QR_STRING_HERE"


def sync_flow() -> None:
    with gaian.GaianClient(api_key=API_KEY, env=gaian.Environment.SANDBOX) as c:
        # 1. Register (idempotent)
        try:
            user = c.user.register(WALLET)
            print(f"user {user.id}  kyc={user.kyc_status}")
        except gaian.GaianAPIError as e:
            if not gaian.is_conflict(e):
                raise

        # 2. Policy check
        policy = c.policy.check_policy(WALLET, "VN")
        if not policy.is_allowed:
            raise SystemExit(f"payment blocked: {policy.reason}")
        print(f"tier={policy.tier}  per-tx=${policy.limits.per_transaction:.0f}")

        # 3. Parse QR
        qr = c.payment.parse_qr(QR_STRING)
        amount = qr.amount or 0.0
        print(f"beneficiary={qr.beneficiary_name}  amount={amount} {qr.currency}")

        # 4. Exchange rate
        exchange = c.payment.calculate_exchange(gaian.CalculateExchangeRequest(
            amount=amount,
            country="VN",
            chain=gaian.Chain.SOLANA,
            token=gaian.CryptoCurrency.USDC,
        ))
        print(f"need {exchange.crypto_amount} {exchange.crypto_currency} (rate={exchange.exchange_rate})")

        # 5. Place order
        order = c.payment.place_order(gaian.PlaceOrderRequest(
            qr_string=QR_STRING,
            amount=amount,
            crypto_currency=gaian.CryptoCurrency.USDC,
            from_address=WALLET,
            fiat_currency=gaian.FiatCurrency.VND,
            chain=gaian.Chain.SOLANA,
        ))
        print(f"order {order.order_id}  status={order.status}")

        # 6. Sign & broadcast on-chain transaction using order.crypto_transfer_info
        tx_signature = "TRANSACTION_SIGNATURE_PLACEHOLDER"

        # 7. Verify
        result = c.payment.verify_order(order.order_id, tx_signature)
        print(f"verify={result.status}  bank={result.bank_transfer_status}")

        # 8. Poll
        while True:
            status = c.payment.get_order_status(order.order_id)
            print(f"polling: {status.status}")
            if status.status in (gaian.OrderStatus.COMPLETED, gaian.OrderStatus.FAILED):
                print(f"final: {status.status}")
                break
            time.sleep(3)


async def async_flow() -> None:
    async with gaian.AsyncGaianClient(api_key=API_KEY, env=gaian.Environment.SANDBOX) as c:
        user = await c.user.register(WALLET)
        print(f"user {user.id}")

        policy = await c.policy.check_policy(WALLET, "VN")
        if not policy.is_allowed:
            raise SystemExit(f"blocked: {policy.reason}")

        qr = await c.payment.parse_qr(QR_STRING)
        amount = qr.amount or 0.0

        order = await c.payment.place_order(gaian.PlaceOrderRequest(
            qr_string=QR_STRING,
            amount=amount,
            crypto_currency=gaian.CryptoCurrency.USDC,
            from_address=WALLET,
            fiat_currency=gaian.FiatCurrency.VND,
        ))
        print(f"order {order.order_id}")

        # Poll
        while True:
            status = await c.payment.get_order_status(order.order_id)
            if status.status in (gaian.OrderStatus.COMPLETED, gaian.OrderStatus.FAILED):
                print(f"final: {status.status}")
                break
            await asyncio.sleep(3)


if __name__ == "__main__":
    sync_flow()
