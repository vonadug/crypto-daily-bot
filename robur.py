import os
import json
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://lt.morningstar.com/api/rest.svc/klr5zyak8x/security_details?id=SE0014261764&idType=ISIN&viewIds=Portfolio&responseViewFormat=json"

response = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20
)

data = response.json()

text = json.dumps(data, indent=2)

keywords = [
    "NAV",
    "nav",
    "Price",
    "price",
    "Close",
    "close",
    "Currency",
    "currency",
    "26.677",
    "SE0014261764",
    "Technology"
]

message = "🔎 Robur JSON Debug\n\n"

for keyword in keywords:
    index = text.find(keyword)
    message += f"{keyword}: {index}\n"

message += "\nJSON start:\n"
message += text[:2500]

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(
    telegram_url,
    json={
        "chat_id": CHAT_ID,
        "text": message[:3900]
    },
    timeout=20
)
