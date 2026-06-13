import os
import json
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = "https://lt.morningstar.com/api/rest.svc/7ndqnfv9u4/securities_details?ids=SE0014261764&idType=ISIN&viewIds=Portfolio&responseViewFormat=json"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Referer": "https://www.swedbank.lv/",
    "Origin": "https://www.swedbank.lv"
}

r = requests.get(url, headers=headers, timeout=30)
text = r.content.decode("utf-8-sig", errors="replace")
data = json.loads(text)

pretty = json.dumps(data, indent=2)

keywords = [
    "26.677",
    "NAV",
    "Nav",
    "nav",
    "Price",
    "price",
    "Close",
    "close",
    "Currency",
    "Performance"
]

message = "🔎 Robur Field Search\n\n"

for keyword in keywords:
    index = pretty.find(keyword)
    message += f"{keyword}: {index}\n"

message += "\nSnippets:\n\n"

for keyword in keywords:
    index = pretty.find(keyword)
    if index != -1:
        start = max(index - 300, 0)
        end = min(index + 600, len(pretty))
        message += f"--- {keyword} ---\n"
        message += pretty[start:end]
        message += "\n\n"

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message[:3900]
    },
    timeout=30
)

print(r.status_code)
