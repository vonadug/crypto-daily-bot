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

prices = requests.get(price_url, params=params).json()

lines = []
total_value = 0

for coin_id, data in portfolio.items():
    symbol = data["symbol"]
    amount = data["amount"]
    price = prices[coin_id]["usd"]
    change_24h = prices[coin_id]["usd_24h_change"]
    value = amount * price
    total_value += value

    emoji = "🟢" if change_24h >= 0 else "🔴"

    lines.append(
        f"{emoji} {symbol}: ${value:,.2f} ({change_24h:+.2f}%)"
    )

message = "📊 Crypto Portfolio Daily\n\n"
message += f"Total Value: ${total_value:,.2f}\n\n"
message += "\n".join(lines)

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    telegram_url,
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(response.status_code)
print(response.text)
