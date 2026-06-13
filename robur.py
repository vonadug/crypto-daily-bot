import os
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

message = (
    f"Robur API Test\n\n"
    f"Status: {r.status_code}\n"
    f"Length: {len(r.text)}\n\n"
    f"{r.text[:3000]}"
)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message[:3900]
    },
    timeout=30
)

print(r.status_code)
print(r.text[:1000])
