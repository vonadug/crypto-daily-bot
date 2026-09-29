import os
import json
import time
import requests
from portfolio_config import CRYPTO_HOLDINGS

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "portfolio_state.json"

# --------------------------------------------------
# PORTFOLIO
# --------------------------------------------------

portfolio = {
    "TRX": {
        "ticker": "TRX-USD",
        "amount": CRYPTO_HOLDINGS["TRX"],
    },
    "SOL": {
        "ticker": "SOL-USD",
        "amount": CRYPTO_HOLDINGS["SOL"],
    },
    "ADA": {
        "ticker": "ADA-USD",
        "amount": CRYPTO_HOLDINGS["ADA"],
    },
    "ETH": {
        "ticker": "ETH-USD",
        "amount": CRYPTO_HOLDINGS["ETH"],
    },
    "BNB": {
        "ticker": "BNB-USD",
        "amount": CRYPTO_HOLDINGS["BNB"],
    },
    "DOGE": {
        "ticker": "DOGE-USD",
        "amount": CRYPTO_HOLDINGS["DOGE"],
    },
}


# --------------------------------------------------
# YAHOO FINANCE
# --------------------------------------------------

def get_chart(ticker, retries=3):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{ticker}?range=5d&interval=1d"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            result = data.get("chart", {}).get("result")

            if not result:
                raise RuntimeError(
                    f"No Yahoo Finance data returned for {ticker}"
                )

            meta = result[0]["meta"]

            price = meta.get("regularMarketPrice")

            if price is None:
                raise RuntimeError(
                    f"No current price returned for {ticker}"
                )

            # Yahoo normally provides chartPreviousClose.
            # previousClose is used as fallback.
            prev_close = meta.get(
                "chartPreviousClose",
                meta.get("previousClose", price)
            )

            return float(price), float(prev_close)

        except Exception as e:
            last_error = e

            print(
                f"Yahoo attempt {attempt} failed "
                f"for {ticker}: {e}"
            )

            if attempt < retries:
                time.sleep(3)

    raise RuntimeError(
        f"Yahoo Finance failed for {ticker} "
        f"after {retries} attempts: {last_error}"
    )


# --------------------------------------------------
# EUR/USD EXCHANGE RATE
# --------------------------------------------------

eurusd, _ = get_chart("EURUSD=X")

if eurusd <= 0:
    raise RuntimeError("Invalid EUR/USD exchange rate")


# --------------------------------------------------
# CALCULATE PORTFOLIO
# --------------------------------------------------

coins = []

total_value_usd = 0
total_value_eur = 0

total_value_24h_ago_usd = 0
total_value_24h_ago_eur = 0

for symbol, data in portfolio.items():

    ticker = data["ticker"]
    amount = data["amount"]

    price_usd, previous_price_usd = get_chart(ticker)

    # Current values
    value_usd = amount * price_usd
    value_eur = value_usd / eurusd

    # Previous-close values
    previous_value_usd = amount * previous_price_usd
    previous_value_eur = previous_value_usd / eurusd

    # 24h / previous-close change
    pnl_24h_usd = value_usd - previous_value_usd
    pnl_24h_eur = value_eur - previous_value_eur

    change_24h = (
        (price_usd - previous_price_usd)
        / previous_price_usd
        * 100
        if previous_price_usd
        else 0
    )

    total_value_usd += value_usd
    total_value_eur += value_eur

    total_value_24h_ago_usd += previous_value_usd
    total_value_24h_ago_eur += previous_value_eur

    coins.append({
        "symbol": symbol,
        "ticker": ticker,
        "value_usd": value_usd,
        "value_eur": value_eur,
        "change_24h": change_24h,
        "pnl_24h_usd": pnl_24h_usd,
        "pnl_24h_eur": pnl_24h_eur,
    })


# --------------------------------------------------
# TOTAL DAILY CHANGE
# --------------------------------------------------

total_pnl_24h_usd = (
    total_value_usd - total_value_24h_ago_usd
)

total_pnl_24h_eur = (
    total_value_eur - total_value_24h_ago_eur
)

total_change_24h = (
    total_pnl_24h_usd
    / total_value_24h_ago_usd
    * 100
    if total_value_24h_ago_usd
    else 0
)


# --------------------------------------------------
# SORT PORTFOLIO
# --------------------------------------------------

coins.sort(
    key=lambda x: x["value_usd"],
    reverse=True
)

best_performer = max(
    coins,
    key=lambda x: x["pnl_24h_usd"]
)

weakest_performer = min(
    coins,
    key=lambda x: x["pnl_24h_usd"]
)

largest_position = max(
    coins,
    key=lambda x: x["value_usd"]
)

largest_share = (
    largest_position["value_usd"]
    / total_value_usd
    * 100
    if total_value_usd
    else 0
)


# --------------------------------------------------
# PREVIOUS RUN STATE
# --------------------------------------------------

previous_total_eur = 0

try:
    with open(STATE_FILE, "r") as file:
        state = json.load(file)

        # New state format
        previous_total_eur = state.get(
            "last_total_value_eur",
            0
        )

except (FileNotFoundError, json.JSONDecodeError):
    previous_total_eur = 0


# --------------------------------------------------
# SINCE LAST RUN
# --------------------------------------------------

since_last_text = "First run: no previous value yet"

if previous_total_eur > 0:

    since_last = (
        total_value_eur - previous_total_eur
    )

    since_last_percent = (
        since_last
        / previous_total_eur
        * 100
    )

    since_emoji = (
        "🟢"
        if since_last >= 0
        else "🔴"
    )

    since_last_text = (
        f"{since_emoji} "
        f"{since_last:+,.2f} € "
        f"({since_last_percent:+.2f}%)"
    )


# --------------------------------------------------
# COIN LINES
# --------------------------------------------------

lines = []

for coin in coins:

    emoji = (
        "🟢"
        if coin["pnl_24h_eur"] >= 0
        else "🔴"
    )

    share = (
        coin["value_eur"]
        / total_value_eur
        * 100
        if total_value_eur
        else 0
    )

    lines.append(
        f"{emoji} {coin['symbol']}: "
        f"{coin['value_eur']:,.2f} € | "
        f"{coin['pnl_24h_eur']:+,.2f} € | "
        f"{share:.1f}%"
    )


# --------------------------------------------------
# TELEGRAM MESSAGE
# --------------------------------------------------

day_emoji = (
    "🟢"
    if total_pnl_24h_eur >= 0
    else "🔴"
)

message = "📊 Crypto Portfolio Daily\n\n"

message += (
    f"Total Value: "
    f"{total_value_eur:,.2f} €\n"
)

message += (
    f"24h P/L: "
    f"{day_emoji} "
    f"{total_pnl_24h_eur:+,.2f} € "
    f"({total_change_24h:+.2f}%)\n"
)

message += (
    f"Since Last Run: "
    f"{since_last_text}\n\n"
)

message += (
    f"🚀 Best Performer: "
    f"{best_performer['symbol']}\n"
)

message += (
    f"🐢 Weakest Performer: "
    f"{weakest_performer['symbol']}\n"
)

message += (
    f"⚠️ Largest Position: "
    f"{largest_position['symbol']} "
    f"{largest_share:.1f}%\n\n"
)

message += "\n".join(lines)


# --------------------------------------------------
# SEND TELEGRAM
# --------------------------------------------------

telegram_url = (
    f"https://api.telegram.org/"
    f"bot{BOT_TOKEN}/sendMessage"
)

response = requests.post(
    telegram_url,
    json={
        "chat_id": CHAT_ID,
        "text": message,
    },
    timeout=30,
)

response.raise_for_status()

print(response.status_code)
print(response.text)


# --------------------------------------------------
# SAVE STATE
# --------------------------------------------------

with open(STATE_FILE, "w") as file:
    json.dump(
        {
            "last_total_value_eur": total_value_eur,
            "last_total_value_usd": total_value_usd,
        },
        file,
        indent=2,
    )
