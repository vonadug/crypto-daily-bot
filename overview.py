import os
import requests
from portfolio_config import (
    CRYPTO_HOLDINGS,
    ROBUR_UNITS,
    ROBUR_NAV,
    STOCK_POSITIONS,
    CASH_EUR,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def fmt_eur(value):
    return f"{value:,.2f} €"


def get_crypto_value_eur():
    coingecko_ids = {
        "TRX": "tron",
        "SOL": "solana",
        "ADA": "cardano",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "DOGE": "dogecoin",
    }

    ids = ",".join(coingecko_ids.values())

    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": ids,
            "vs_currencies": "eur",
        },
        timeout=30,
    )

    prices = response.json()

    total = 0

    for symbol, amount in CRYPTO_HOLDINGS.items():
        coin_id = coingecko_ids[symbol]
        total += amount * prices[coin_id]["eur"]

    return total


def get_chart(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()["chart"]["result"][0]
    meta = result["meta"]

    price = meta["regularMarketPrice"]
    currency = meta.get("currency", "")

    return price, currency


def get_fx(ticker):
    price, _ = get_chart(ticker)
    return price


def to_eur(price, currency, ticker, eurusd, gbpeur):
    if currency == "USD":
        return price / eurusd

    if currency == "GBP":
        return price * gbpeur

    if currency == "GBp":
        return (price / 100) * gbpeur

    if ticker.endswith(".L") and price > 1000:
        return (price / 100) * gbpeur

    return price


def get_trading212_value_eur():
    eurusd = get_fx("EURUSD=X")
    gbpeur = get_fx("GBPEUR=X")

    total = CASH_EUR

    for group, name, ticker, shares, avg_price, avg_currency in STOCK_POSITIONS:
        price, currency = get_chart(ticker)
        price_eur = to_eur(price, currency, ticker, eurusd, gbpeur)
        total += shares * price_eur

    return total


crypto_value = get_crypto_value_eur()
robur_value = ROBUR_UNITS * ROBUR_NAV
trading212_value = get_trading212_value_eur()

total_net_worth = crypto_value + robur_value + trading212_value

message = "💎 Portfolio Overview\n\n"
message += f"🪙 Crypto: {fmt_eur(crypto_value)}\n"
message += f"📈 Robur: {fmt_eur(robur_value)}\n"
message += f"🏦 Trading212: {fmt_eur(trading212_value)}\n\n"
message += f"💎 Total Net Worth: {fmt_eur(total_net_worth)}"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message,
    },
    timeout=30,
)

print(response.status_code)
print(response.text)
