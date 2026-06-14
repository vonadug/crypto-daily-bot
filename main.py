import os
import json
import requests
from portfolio_config import CRYPTO_HOLDINGS

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "portfolio_state.json"

portfolio = {
    "tron": {
        "symbol": "TRX",
        "amount": CRYPTO_HOLDINGS["TRX"]
    },
    "solana": {
        "symbol": "SOL",
        "amount": CRYPTO_HOLDINGS["SOL"]
    },
    "cardano": {
        "symbol": "ADA",
        "amount": CRYPTO_HOLDINGS["ADA"]
    },
    "ethereum": {
        "symbol": "ETH",
        "amount": CRYPTO_HOLDINGS["ETH"]
    },
    "binancecoin": {
        "symbol": "BNB",
        "amount": CRYPTO_HOLDINGS["BNB"]
    },
    "dogecoin": {
        "symbol": "DOGE",
        "amount": CRYPTO_HOLDINGS["DOGE"]
    },
}

ids = ",".join(portfolio.keys())

price_url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    "ids": ids,
    "vs_currencies": "usd,eur",
    "include_24hr_change": "true"
}

prices = requests.get(price_url, params=params, timeout=20).json()

coins = []
total_value_usd = 0
total_value_eur = 0
total_value_24h_ago = 0

for coin_id, data in portfolio.items():
    symbol = data["symbol"]
    amount = data["amount"]

    price_usd = prices[coin_id]["usd"]
    price_eur = prices[coin_id]["eur"]
    change_24h = prices[coin_id]["usd_24h_change"]

    value_usd = amount * price_usd
    value_eur = amount * price_eur

    price_24h_ago = price_usd / (1 + change_24h / 100)
    value_24h_ago = amount * price_24h_ago
    pnl_24h = value_usd - value_24h_ago

    total_value_usd += value_usd
    total_value_eur += value_eur
    total_value_24h_ago += value_24h_ago

    coins.append({
        "symbol": symbol,
        "value_usd": value_usd,
        "value_eur": value_eur,
        "change_24h": change_24h,
        "pnl_24h": pnl_24h
    })

total_pnl_24h = total_value_usd - total_value_24h_ago
total_change_24h = (total_pnl_24h / total_value_24h_ago) * 100

coins.sort(key=lambda x: x["value_usd"], reverse=True)

best_performer = max(coins, key=lambda x: x["pnl_24h"])
weakest_performer = min(coins, key=lambda x: x["pnl_24h"])
largest_position = max(coins, key=lambda x: x["value_usd"])
largest_share = (largest_position["value_usd"] / total_value_usd) * 100

previous_total = 0

try:
    with open(STATE_FILE, "r") as file:
        state = json.load(file)
        previous_total = state.get("last_total_value", 0)
except FileNotFoundError:
    previous_total = 0

since_yesterday_text = "First run: no previous value yet"

if previous_total > 0:
    since_yesterday = total_value_usd - previous_total
    since_yesterday_percent = (since_yesterday / previous_total) * 100
    since_emoji = "🟢" if since_yesterday >= 0 else "🔴"
    since_yesterday_text = f"{since_emoji} ${since_yesterday:+,.2f} ({since_yesterday_percent:+.2f}%)"

lines = []

for coin in coins:
    emoji = "🟢" if coin["change_24h"] >= 0 else "🔴"
    share = (coin["value_usd"] / total_value_usd) * 100

    pnl_24h_eur = coin["value_eur"] - (
    coin["value_eur"] / (1 + coin["change_24h"] / 100)
)

lines.append(
    f"{emoji} {coin['symbol']}: "
    f"€{coin['value_eur']:,.2f} | "
    f"{pnl_24h_eur:+,.2f}€ | "
    f"{share:.1f}%"
)
day_emoji = "🟢" if total_pnl_24h >= 0 else "🔴"

message = "📊 Crypto Portfolio Daily\n\n"
message += f"Total Value: ${total_value_usd:,.2f} / €{total_value_eur:,.2f}\n"
message += f"24h P/L: {day_emoji} ${total_pnl_24h:+,.2f} ({total_change_24h:+.2f}%)\n"
message += f"Since Last Run: {since_yesterday_text}\n\n"

message += f"🚀 Best Performer: {best_performer['symbol']} {best_performer['pnl_24h']:+.2f}$\n"
message += f"🐢 Weakest Performer: {weakest_performer['symbol']} {weakest_performer['pnl_24h']:+.2f}$\n"
message += f"⚠️ Largest Position: {largest_position['symbol']} {largest_share:.1f}%\n\n"

message += "\n".join(lines)

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    telegram_url,
    json={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=20
)

print(response.status_code)
print(response.text)

with open(STATE_FILE, "w") as file:
    json.dump({"last_total_value": total_value_usd}, file, indent=2)
