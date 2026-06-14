import os
import requests
from datetime import datetime
from portfolio_config import ROBUR_UNITS, ROBUR_NAV, ROBUR_AVG_PRICE_EUR

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

UNITS = ROBUR_UNITS
NAV = ROBUR_NAV
PURCHASE_VALUE = ROBUR_UNITS * ROBUR_AVG_PRICE_EUR

current_value = UNITS * NAV
profit = current_value - PURCHASE_VALUE
profit_pct = (profit / PURCHASE_VALUE) * 100 if PURCHASE_VALUE else 0

profit_emoji = "🟢" if profit >= 0 else "🔴"

today = datetime.now().strftime("%d.%m.%Y")

message = "📈 Robur Technology Daily\n\n"
message += f"NAV manually set at {today}: {NAV:.4f} €\n"
message += f"Units: {UNITS:.4f}\n"
message += f"Current Value: {current_value:,.2f} €\n\n"
message += f"Profit: {profit_emoji} {profit:+,.2f} € ({profit_pct:+.2f}%)"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=30
)

print(response.status_code)
print(response.text)
