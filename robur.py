import os
import re
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FUND_URL = "https://www.swedbank.lv/private/investor/funds/allFunds/list/details"

fund_name = "Swedbank Robur Technology"
units = 372.7126
purchase_value = 8870.38

headers = {
    "User-Agent": "Mozilla/5.0"
}

html = requests.get(FUND_URL, headers=headers, timeout=20).text

nav_match = re.search(
    r"NAV at\s+(\d{2}\.\d{2}\.\d{4}).*?([0-9]+[.,][0-9]+)\s*EUR",
    html,
    re.DOTALL
)

if not nav_match:
    message = "⚠️ Robur Bot Error\n\nCould not find NAV on Swedbank page."
else:
    nav_date = nav_match.group(1)
    price_per_unit = float(nav_match.group(2).replace(",", "."))

    current_value = units * price_per_unit
    profit = current_value - purchase_value
    profit_percent = (profit / purchase_value) * 100

    profit_emoji = "🟢" if profit >= 0 else "🔴"

    message = "📈 Robur Portfolio Daily\n\n"
    message += f"{fund_name}\n\n"
    message += f"NAV at {nav_date}: €{price_per_unit:.4f}\n"
    message += f"Units: {units:.4f}\n"
    message += f"Current Value: €{current_value:,.2f}\n\n"
    message += f"Purchase Value: €{purchase_value:,.2f}\n"
    message += f"Profit: {profit_emoji} €{profit:+,.2f} ({profit_percent:+.2f}%)"

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
