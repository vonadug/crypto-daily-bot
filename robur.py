import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

ROBUR_PRICE_URL = "https://swedbank.lv/price-provider/pub/json?identifier=75E87DE63ED8B60F6445F868AC3FB10D41DB49D30B9E83496232F968AC4CB00B41DD48D60A9E82496430F968AA48B00C41AE48D30A9D833B6444F917AC4CB17946AC48A00B9E824C6440F968AC4CB77D41D149D20B9E83496232F968AC4CB10C40DF48D40BEC823A6545F81DAC4CB17946AA49D00BEA823A6447F91BAD3FB07A41DB48DF0B9E83496232F968AC4CB00B41D948DF0B9E8349623475E87C78F838427B5176CDB05FEA704B&userId=UNKNOWN&token=23A4559EDECC46B528FAE4CB3A2E51337C990AC1929A19EA70E7F4C42228410146FB0AA3819320D427E6F4FA11675D1F46D61CFA81937BEA14C0DFEE00137F227CFB6E23A4540012605D5E4B95903B82F03387"

UNITS = 372.7126
PURCHASE_VALUE = 8870.38

response = requests.get(
    ROBUR_PRICE_URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=30
)

data = response.json()

latest_timestamp = data[-1][0]
latest_nav = data[-1][1]

previous_nav = data[-2][1]

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
message += f"NAV at {latest_date}: €{latest_nav:.4f}\n"
message += f"Units: {UNITS:.4f}\n"
message += f"Current Value: €{current_value:,.2f}\n\n"
message += f"Daily Change: {daily_emoji} €{daily_change_value:+,.2f} ({nav_change_pct:+.2f}%)\n"
message += f"Profit: {profit_emoji} €{profit:+,.2f} ({profit_pct:+.2f}%)"

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    telegram_url,
    json={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=30
)

print(response.status_code)
print(response.text)
