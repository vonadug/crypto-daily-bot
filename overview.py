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

    data = response.json()

    result = data["chart"]["result"]

    if not result:
        raise RuntimeError(f"No Yahoo Finance data for {ticker}")

    meta = result[0]["meta"]

    price = meta["regularMarketPrice"]
    currency = meta.get("currency", "")

    return price, currency


def get_fx(ticker):
    price, _ = get_chart(ticker)
    return price


# =========================================================
# CRYPTO
# =========================================================

def get_crypto_value_eur():

    yahoo_tickers = {
        "TRX": "TRX-EUR",
        "SOL": "SOL-EUR",
        "ADA": "ADA-EUR",
        "ETH": "ETH-EUR",
        "BNB": "BNB-EUR",
        "DOGE": "DOGE-EUR",
    }

    total = 0

    print("Calculating crypto portfolio with Yahoo Finance...")

    for symbol, amount in CRYPTO_HOLDINGS.items():

        if symbol not in yahoo_tickers:
            raise RuntimeError(
                f"No Yahoo ticker configured for crypto: {symbol}"
            )

        ticker = yahoo_tickers[symbol]

        price, currency = get_chart(ticker)

        print(
            f"{symbol}: "
            f"{amount} x {price} {currency}"
        )

        total += amount * price

    print(f"Crypto total: {total:.2f} EUR")

    return total


# =========================================================
# TRADING 212
# =========================================================

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

    print("Calculating Trading212 portfolio...")

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

        value = shares * price_eur

        print(
            f"{name}: "
            f"{shares} x {price_eur:.4f} EUR "
            f"= {value:.2f} EUR"
        )

        total += value

    print(f"Trading212 total: {total:.2f} EUR")

    return total


# =========================================================
# CALCULATE PORTFOLIO
# =========================================================

crypto_value = get_crypto_value_eur()

robur_value = ROBUR_UNITS * ROBUR_NAV

print(
    f"Robur: {ROBUR_UNITS} x {ROBUR_NAV} "
    f"= {robur_value:.2f} EUR"
)

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

message += f"🪙 Crypto: {fmt_eur(crypto_value)}\n"
message += f"📈 Robur: {fmt_eur(robur_value)}\n"
message += f"🏦 Trading212: {fmt_eur(trading212_value)}\n\n"

message += (
    f"💎 Total Net Worth: "
    f"{fmt_eur(total_net_worth)}"
)


# =========================================================
# SEND TELEGRAM
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

print("Telegram message sent successfully.")
print(response.text)
