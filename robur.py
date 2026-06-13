import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ОБНОВЛЯТЬ ВРУЧНУЮ
CURRENT_NAV = 26.6770

# ТВОЯ ПОЗИЦИЯ
UNITS = 372.7126
PURCHASE_PRICE = 23.80

current_value = CURRENT_NAV * UNITS
purchase_value = PURCHASE_PRICE * UNITS
profit = current_value - purchase_value
profit_pct = (profit / purchase_value) * 100

message = (
    "🟠 Robur Technology\n\n"
    f"NAV: €{CURRENT_NAV:.4f}\n\n"
    f"Position Value: €{current_value:,.2f}\n"
    f"Purchase Value: €{purchase_value:,.2f}\n"
    f"Profit: 🟢 €{profit:,.2f} (+{profit_pct:.2f}%)"
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(response.status_code)
print(response.text)
