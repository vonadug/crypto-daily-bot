import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CASH_EUR = 112.19  # Growth cash + Quantum cash + 2026 Finds cash

POSITIONS = [
    # name, yahoo ticker, shares
    ("GOOGL", "GOOGL", 2.24205794),
    ("AAPL", "AAPL", 1.82665938),
    ("AMZN", "AMZN", 1.94746704),
    ("META", "META", 0.62208621),
    ("MSFT", "MSFT", 0.89746218),
    ("NVDA", "NVDA", 2.70565948),

    ("IONQ", "IONQ", 52.13082672),
    ("QBTS", "QBTS", 43.13487336),
    ("RGTI", "RGTI", 48.268315),

    ("VUSA GBP", "VUSA.L", 29.50884384),
    ("VUSA EUR", "VUSA.AS", 22.34437608),
]


def get_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    data = r.json()["chart"]["result"][0]
    meta = data["meta"]

    price = meta["regularMarketPrice"]
    prev_close = meta.get("chartPreviousClose", price)
    currency = meta.get("currency", "")

    return price, prev_close, currency


def get_fx(ticker):
    price, _, _ = get_price(ticker)
    return price


eurusd = get_fx("EURUSD=X")   # USD per 1 EUR
gbpeur = get_fx("GBPEUR=X")   # EUR per 1 GBP


def to_eur(price, currency, ticker):
    if currency == "USD":
        return price / eurusd

    if currency == "GBP":
        return price * gbpeur

    if currency == "GBp":
        return (price / 100) * gbpeur

    # Yahoo иногда отдаёт VUSA.L как GBP/GBp странно
    if ticker.endswith(".L") and price > 1000:
        return (price / 100) * gbpeur

    return price


rows = []
total_value = CASH_EUR
total_daily = 0

for name, ticker, shares in POSITIONS:
    price, prev_close, currency = get_price(ticker)

    price_eur = to_eur(price, currency, ticker)
    prev_eur = to_eur(prev_close, currency, ticker)

    value = shares * price_eur
    prev_value = shares * prev_eur
    daily_value = value - prev_value
    daily_pct = (daily_value / prev_value) * 100 if prev_value else 0

    total_value += value
    total_daily += daily_value

    rows.append({
        "name": name,
        "ticker": ticker,
        "value": value,
        "daily_value": daily_value,
        "daily_pct": daily_pct,
    })


total_prev = total_value - total_daily
total_daily_pct = (total_daily / total_prev) * 100 if total_prev else 0

best = max(rows, key=lambda x: x["daily_value"])
weakest = min(rows, key=lambda x: x["daily_value"])

total_emoji = "🟢" if total_daily >= 0 else "🔴"

message = "📈 Trading212 Portfolio Daily\n\n"
message += f"Total Value: €{total_value:,.2f}\n"
message += f"24h P/L: {total_emoji} €{total_daily:+,.2f} ({total_daily_pct:+.2f}%)\n\n"
message += f"🚀 Best Performer: {best['name']} €{best['daily_value']:+,.2f}\n"
message += f"🐢 Weakest Performer: {weakest['name']} €{weakest['daily_value']:+,.2f}\n\n"

for row in sorted(rows, key=lambda x: x["value"], reverse=True):
    emoji = "🟢" if row["daily_value"] >= 0 else "🔴"
    message += (
        f"{emoji} {row['name']}: "
        f"€{row['value']:,.2f} | "
        f"{row['daily_pct']:+.2f}% | "
        f"€{row['daily_value']:+,.2f}\n"
    )

message += f"\n💶 Cash: €{CASH_EUR:,.2f}"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=20
)

print(response.status_code)
print(response.text)
