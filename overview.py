import os
import time
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


# =========================================================
# CRYPTO
# =========================================================

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

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": ids,
        "vs_currencies": "eur",
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    last_error = None

    # Try CoinGecko up to 5 times
    for attempt in range(1, 6):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
            )

            print(
                f"CoinGecko attempt {attempt}: "
                f"HTTP {response.status_code}"
            )

            response.raise_for_status()

            prices = response.json()

            total = 0

            for symbol, amount in CRYPTO_HOLDINGS.items():
                if symbol not in coingecko_ids:
                    raise ValueError(
                        f"Unknown crypto symbol in portfolio_config.py: {symbol}"
                    )

                coin_id = coingecko_ids[symbol]

                if coin_id not in prices:
                    raise ValueError(
                        f"CoinGecko missing price for "
                        f"{symbol} ({coin_id})"
                    )

                if "eur" not in prices[coin_id]:
                    raise ValueError(
                        f"CoinGecko missing EUR price for {symbol}"
                    )

                price_eur = prices[coin_id]["eur"]
                total += amount * price_eur

            print(
                f"Crypto total successfully calculated: "
                f"{total:.2f} EUR"
            )

            return total

        except (
            requests.RequestException,
            ValueError,
            KeyError,
        ) as e:
            last_error = e

            print(
                f"CoinGecko attempt {attempt} failed: {e}"
            )

            if attempt < 5:
                print("Waiting 10 seconds before retry...")
                time.sleep(10)

    raise RuntimeError(
        f"CoinGecko failed after 5 attempts: {last_error}"
    )


# =========================================================
# YAHOO FINANCE
# =========================================================

def get_chart(ticker):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{ticker}?range=5d&interval=1d"
    )

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


def to_eur(
    price,
    currency,
    ticker,
    eurusd,
    gbpeur,
):
    if currency == "USD":
        return price / eurusd

    if currency == "GBP":
        return price * gbpeur

    if currency == "GBp":
        return (price / 100) * gbpeur

    if ticker.endswith(".L") and price > 1000:
        return (price / 100) * gbpeur

    return price


# =========================================================
# TRADING212
# =========================================================

def get_trading212_value_eur():
    eurusd = get_fx("EURUSD=X")
    gbpeur = get_fx("GBPEUR=X")

    total = CASH_EUR

    for (
        group,
        name,
        ticker,
        shares,
        avg_price,
        avg_currency,
    ) in STOCK_POSITIONS:

        price, currency = get_chart(ticker)

        price_eur = to_eur(
            price,
            currency,
            ticker,
            eurusd,
            gbpeur,
        )

        position_value = shares * price_eur

        total += position_value

    return total


# =========================================================
# CALCULATE PORTFOLIO
# =========================================================

print("Calculating crypto portfolio...")
crypto_value = get_crypto_value_eur()

print("Calculating Robur portfolio...")
robur_value = ROBUR_UNITS * ROBUR_NAV

print("Calculating Trading212 portfolio...")
trading212_value = get_trading212_value_eur()

total_net_worth = (
    crypto_value
    + robur_value
    + trading212_value
)


# =========================================================
# TELEGRAM MESSAGE
# =========================================================

message = "💎 Portfolio Overview\n\n"

message += (
    f"🪙 Crypto: "
    f"{fmt_eur(crypto_value)}\n"
)

message += (
    f"📈 Robur: "
    f"{fmt_eur(robur_value)}\n"
)

message += (
    f"🏦 Trading212: "
    f"{fmt_eur(trading212_value)}\n\n"
)

message += (
    f"💎 Total Net Worth: "
    f"{fmt_eur(total_net_worth)}"
)


# =========================================================
# SEND TO TELEGRAM
# =========================================================

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message,
    },
    timeout=30,
)

response.raise_for_status()

print(
    f"Telegram response: "
    f"HTTP {response.status_code}"
)

print(response.text)

print("Portfolio Overview sent successfully.")
