import os
import json
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "stocks_state.json"
CASH_EUR = 112.19

POSITIONS = [
    ("ETF", "VUSA GBP", "VUSA.L", 29.50884384, 84.0511, "GBP"),
    ("ETF", "VUSA EUR", "VUSA.AS", 22.34437608, 114.794, "EUR"),

    ("Quantum", "IONQ", "IONQ", 52.13082672, 23.28, "USD"),
    ("Quantum", "QBTS", "QBTS", 43.13487336, 3.21, "USD"),
    ("Quantum", "RGTI", "RGTI", 48.268315, 2.98, "USD"),

    ("Growth", "Alphabet", "ABEA.DE", 2.24205794, 168.64, "EUR"),
    ("Growth", "Apple", "AAPL", 1.82665938, 202.10, "USD"),
    ("Growth", "Amazon", "AMZ.DE", 1.94746704, 180.38, "EUR"),
    ("Growth", "Meta", "FB2A.DE", 0.62208621, 533.30, "EUR"),
    ("Growth", "Microsoft", "MSF.DE", 0.89746218, 399.56, "EUR"),
    ("Growth", "Nvidia", "NVD.DE", 2.70565948, 113.41, "EUR"),
]


def fmt_eur(value):
    return f"{value:+,.2f} €"


def fmt_eur_plain(value):
    return f"{value:,.2f} €"


def get_chart(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    result = r.json()["chart"]["result"][0]
    meta = result["meta"]

    price = meta["regularMarketPrice"]
    prev_close = meta.get("chartPreviousClose", price)
    currency = meta.get("currency", "")

    return price, prev_close, currency


def get_fx(ticker):
    price, _, _ = get_chart(ticker)
    return price


eurusd = get_fx("EURUSD=X")
gbpeur = get_fx("GBPEUR=X")


def to_eur(price, currency, ticker):
    if currency == "USD":
        return price / eurusd

    if currency == "GBP":
        return price * gbpeur

    if currency == "GBp":
        return (price / 100) * gbpeur

    if ticker.endswith(".L") and price > 1000:
        return (price / 100) * gbpeur

    return price


def avg_to_eur(avg_price, avg_currency):
    if avg_currency == "USD":
        return avg_price / eurusd

    if avg_currency == "GBP":
        return avg_price * gbpeur

    return avg_price


old_state = {}
try:
    with open(STATE_FILE, "r") as f:
        old_state = json.load(f)
except FileNotFoundError:
    old_state = {}

rows = []
group_costs = {}
group_values = {}

total_value = CASH_EUR
total_daily = 0
total_cost = 0

for group, name, ticker, shares, avg_price, avg_currency in POSITIONS:
    price, prev_close, currency = get_chart(ticker)

    price_eur = to_eur(price, currency, ticker)
    prev_eur = to_eur(prev_close, currency, ticker)
    avg_eur = avg_to_eur(avg_price, avg_currency)

    value = shares * price_eur
    prev_value = shares * prev_eur
    daily_value = value - prev_value
    daily_pct = (daily_value / prev_value) * 100 if prev_value else 0

    cost = shares * avg_eur
    profit = value - cost
    profit_pct = (profit / cost) * 100 if cost else 0

    group_costs[group] = group_costs.get(group, 0) + cost
    group_values[group] = group_values.get(group, 0) + value

    total_value += value
    total_daily += daily_value
    total_cost += cost

    rows.append({
        "group": group,
        "name": name,
        "ticker": ticker,
        "value": value,
        "daily_value": daily_value,
        "daily_pct": daily_pct,
        "profit": profit,
        "profit_pct": profit_pct,
    })

total_prev = total_value - total_daily
total_daily_pct = (total_daily / total_prev) * 100 if total_prev else 0

total_profit = total_value - CASH_EUR - total_cost
total_profit_pct = (total_profit / total_cost) * 100 if total_cost else 0

group_stats = {}

for group in group_values:
    g_value = group_values[group]
    g_cost = group_costs[group]
    g_profit = g_value - g_cost
    g_profit_pct = (g_profit / g_cost * 100) if g_cost else 0

    group_stats[group] = {
        "profit": g_profit,
        "profit_pct": g_profit_pct,
    }

previous_total = old_state.get("total_value")
since_last = None
since_last_pct = None

if previous_total:
    since_last = total_value - previous_total
    since_last_pct = (since_last / previous_total) * 100

best = max(rows, key=lambda x: x["daily_value"])
weakest = min(rows, key=lambda x: x["daily_value"])
largest = max(rows, key=lambda x: x["value"])
largest_pct = (largest["value"] / total_value) * 100

total_emoji = "🟢" if total_daily >= 0 else "🔴"
profit_emoji = "🟢" if total_profit >= 0 else "🔴"

message = "📈 Trading212 Portfolio Daily\n\n"

message += f"Total Value: {fmt_eur_plain(total_value)}\n"
message += f"24h P/L: {total_emoji} {fmt_eur(total_daily)} ({total_daily_pct:+.2f}%)\n"

if since_last is not None:
    since_emoji = "🟢" if since_last >= 0 else "🔴"
    message += f"Since Last Run: {since_emoji} {fmt_eur(since_last)} ({since_last_pct:+.2f}%)\n"

message += f"Profit: {profit_emoji} {fmt_eur(total_profit)} ({total_profit_pct:+.2f}%)\n\n"

message += "📈 Since Start\n\n"

for group in ["ETF", "Quantum", "Growth"]:
    g = group_stats[group]
    emoji = "🟢" if g["profit"] >= 0 else "🔴"
    group_weight = (group_values[group] / total_value) * 100

    message += (
        f"{emoji} {group}: "
        f"{fmt_eur(g['profit'])} "
        f"({g['profit_pct']:+.1f}%) | "
        f"{group_weight:.1f}%\n"
    )

message += "\n"

message += f"🚀 Best Performer: {best['name']} {fmt_eur(best['daily_value'])}\n"
message += f"🐢 Weakest Performer: {weakest['name']} {fmt_eur(weakest['daily_value'])}\n"
message += f"⚠️ Largest Position: {largest['name']} {largest_pct:.1f}%\n\n"

for group_name in ["ETF", "Quantum", "Growth"]:
    if group_name == "ETF":
        message += "📊 ETF\n"
    elif group_name == "Quantum":
        message += "⚛️ Quantum\n"
    else:
        message += "🚀 Growth\n"

    group_rows = [r for r in rows if r["group"] == group_name]

    for row in sorted(group_rows, key=lambda x: x["value"], reverse=True):
        emoji = "🟢" if row["daily_value"] >= 0 else "🔴"
        weight = (row["value"] / total_value) * 100

        message += (
    f"{emoji} {row['name']}: "
    f"{fmt_eur_plain(row['value'])} | "
    f"{fmt_eur(row['daily_value'])} | "
    f"{weight:.1f}%\n"
)

    message += "\n"



message += "────────────────\n"
message += f"💶 Cash: {fmt_eur_plain(CASH_EUR)}\n"
message += f"🏦 Total: {fmt_eur_plain(total_value)}"

with open(STATE_FILE, "w") as f:
    json.dump({
        "total_value": total_value,
        "positions": {
            row["name"]: row["value"] for row in rows
        }
    }, f, indent=2)

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
