"""Standard payment flow: create user -> quote -> place order -> verify -> poll.

Runs against the sandbox. Needs GAIAN_API_KEY and GAIAN_API_SECRET in the environment.
"""

import os
import time

import gaian

QR_STRING = "PASTE_QR_STRING_HERE"
WALLET = "YOUR_SOLANA_WALLET_ADDRESS"


def broadcast(encoded_transaction: str) -> str:
    """Sign and send the transaction with your own wallet code, then return its hash."""
    raise NotImplementedError


def main() -> None:
    with gaian.GaianClient(
        api_key=os.environ["GAIAN_API_KEY"],
        secret_key=os.environ["GAIAN_API_SECRET"],
    ) as client:
        try:
            user_id = client.get_user_by_wallet(wallet_address=WALLET).data.id
        except gaian.GaianAPIError as err:
            if not gaian.is_not_found(err):
                raise
            user_id = client.create_user().data.user_id
            client.create_wallet(user_id=user_id, address=WALLET, chain="solana")

        market = client.get_markets(user_id=user_id).data.markets.get("VN")
        if market is None or market.status != gaian.MarketStatus.APPROVED:
            raise SystemExit("user is not approved for VN: complete KYC first")

        quote = client.quote(
            qr_string=QR_STRING,
            amount=150000,
            chain_id=gaian.Chain.SOLANA,
            settlement_currency="USDC",
            user_id=user_id,
        ).data
        print(f"quote {quote.quote_id}: {quote.settlement_amount} {quote.settlement_currency}")

        order = client.place_order(quote_id=quote.quote_id).data
        tx_hash = broadcast(order.encoded_transaction)

        while True:
            verified = client.verify_order(order_id=order.order_id, transaction_hash=tx_hash).data
            if verified.status == gaian.VerifyStatus.VERIFIED:
                break
            if verified.status == gaian.VerifyStatus.FAILED:
                raise SystemExit(f"verification failed: {verified.message}")
            time.sleep(3)

        while True:
            status = client.get_order_status(order_id=order.order_id).data
            if gaian.is_terminal(status.status):
                print(f"order {status.order_id}: {status.status_label}")
                break
            time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except gaian.GaianAPIError as err:
        raise SystemExit(f"{err} (request id: {err.request_id})") from err
