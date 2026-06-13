import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

portfolio = {
    "tron": {"symbol": "TRX", "amount": 9481.90320483},
    "solana": {"symbol": "SOL", "amount": 14.53053673},
    "cardano": {"symbol": "ADA", "amount": 5088.68027346},
    "ethereum": {"symbol": "ETH", "amount": 0.30744651},
    "binancecoin": {"symbol": "BNB", "amount": 0.83274646},
    "dogecoin": {"symbol": "DOGE", "amount": 505.93792929},
}

ids = ",".join(portfolio.keys())

price_url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    "ids": ids,
    "vs_currencies": "usd",
    "include_24hr_change": "true"
}

prices = requests.get(price_url, params=params, timeout=20).json()

coins = []
total_value = 0
total_value_24h_ago = 0

for coin_id, data in portfolio.items():
    symbol = data["symbol"]
    amount = data["amount"]
    price = prices[coin_id]["usd"]
    change_24h = prices[coin_id]["usd_24h_change"]

    value = amount * price
    price_24h_ago = price / (1 + change_24h / 100)
    value_24h_ago = amount * price_24h_ago
    pnl_24h = value - value_24h_ago

    total_value += value
    total_value_24h_ago += value_24h_ago

    coins.append({
        "symbol": symbol,
        "value": value,
        "change_24h": change_24h,
        "pnl_24h": pnl_24h
    })

total_pnl_24h = total_value - total_value_24h_ago
total_change_24h = (total_pnl_24h / total_value_24h_ago) * 100

coins.sort(key=lambda x: x["value"], reverse=True)

lines = []

for coin in coins:
    emoji = "🟢" if coin["change_24h"] >= 0 else "🔴"
    share = (coin["value"] / total_value) * 100

    lines.append(
        f"{emoji} {coin['symbol']}: ${coin['value']:,.2f} | "
        f"{coin['change_24h']:+.2f}% | "
        f"{coin['pnl_24h']:+.2f}$ | "
        f"{share:.1f}%"
    )

day_emoji = "🟢" if total_pnl_24h >= 0 else "🔴"

message = "📊 Crypto Portfolio Daily\n\n"
message += f"Total Value: ${total_value:,.2f}\n"
message += f"24h P/L: {day_emoji} ${total_pnl_24h:+,.2f} ({total_change_24h:+.2f}%)\n\n"
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
