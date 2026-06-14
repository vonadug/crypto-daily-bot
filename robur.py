import os
import re
import requests
from datetime import datetime
from portfolio_config import ROBUR_UNITS, ROBUR_AVG_PRICE_EUR

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DETAILS_URL = "https://www.swedbank.lv/private/investor/funds/allFunds/list/details"
FUND_ISIN = "SE0014261764"

UNITS = ROBUR_UNITS
PURCHASE_VALUE = ROBUR_UNITS * ROBUR_AVG_PRICE_EUR


def send_telegram(text):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=30
    )
    print(response.status_code)
    print(response.text)


def fail(message, extra=""):
    text = "⚠️ Robur Bot Error\n\n"
    text += message
    if extra:
        text += "\n\n" + extra[:1000]
    send_telegram(text)
    exit(0)


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

page_response = session.get(DETAILS_URL, timeout=30)

if page_response.status_code != 200:
    fail(
        "Could not open Swedbank fund details page.",
        f"Status: {page_response.status_code}\nPreview: {page_response.text[:300]}"
    )

html = page_response.text

identifier_match = re.search(r'identifier=([A-F0-9]{80,})', html)
token_match = re.search(r'token=([A-F0-9]{80,})', html)

if not identifier_match or not token_match:
    fail(
        "Could not find fresh Robur price-provider identifier/token on Swedbank page.",
        f"HTML length: {len(html)}\nPreview: {html[:500]}"
    )

identifier = identifier_match.group(1)
token = token_match.group(1)

price_url = (
    "https://swedbank.lv/price-provider/pub/json"
    f"?identifier={identifier}"
    "&userId=UNKNOWN"
    f"&token={token}"
)

price_response = session.get(
    price_url,
    headers={
        "Accept": "application/json,*/*"
    },
    timeout=30
)

try:
    data = price_response.json()
except Exception:
    fail(
        "Could not read Robur price JSON.",
        f"Status: {price_response.status_code}\n"
        f"Content-Type: {price_response.headers.get('content-type', 'unknown')}\n"
        f"Preview: {price_response.text[:500]}"
    )

if not isinstance(data, list) or len(data) < 2:
    fail(
        "Robur price JSON was empty or invalid.",
        f"Status: {price_response.status_code}\nData: {str(data)[:500]}"
    )

latest_timestamp = data[-1][0]
latest_nav = float(data[-1][1])

previous_nav = float(data[-2][1])

nav_change = latest_nav - previous_nav
nav_change_pct = (nav_change / previous_nav) * 100

current_value = UNITS * latest_nav
previous_value = UNITS * previous_nav

daily_change_value = current_value - previous_value

profit = current_value - PURCHASE_VALUE
profit_pct = (profit / PURCHASE_VALUE) * 100

latest_date = datetime.fromtimestamp(latest_timestamp / 1000).strftime("%d.%m.%Y")

daily_emoji = "🟢" if daily_change_value >= 0 else "🔴"
profit_emoji = "🟢" if profit >= 0 else "🔴"

message = "📈 Robur Technology Daily\n\n"
message += f"NAV at {latest_date}: {latest_nav:.4f} €\n"
message += f"Units: {UNITS:.4f}\n"
message += f"Current Value: {current_value:,.2f} €\n\n"
message += f"Daily Change: {daily_emoji} {daily_change_value:+,.2f} € ({nav_change_pct:+.2f}%)\n"
message += f"Profit: {profit_emoji} {profit:+,.2f} € ({profit_pct:+.2f}%)"

send_telegram(message)
