import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FUND_URL = "https://www.swedbank.lv/private/investor/funds/allFunds/list/details"

headers = {
    "User-Agent": "Mozilla/5.0"
}

html = requests.get(FUND_URL, headers=headers, timeout=20).text

keywords = ["NAV", "26.6770", "Technology", "SE0014261764"]

result = "🔎 Robur Debug\n\n"

for keyword in keywords:
    index = html.find(keyword)
    result += f"{keyword}: {index}\n"

result += f"\nHTML length: {len(html)}\n\n"
result += html[:1200]

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(
    telegram_url,
    json={
        "chat_id": CHAT_ID,
        "text": result[:3900]
    },
    timeout=20
)
