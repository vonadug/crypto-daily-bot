import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://lt.morningstar.com/api/rest.svc/klr5zyak8x/security_details?id=SE0014261764&idType=ISIN&viewIds=Portfolio&responseViewFormat=json"

response = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*"
    },
    timeout=20
)

text = response.content.decode("utf-8-sig", errors="replace")

message = "🔎 Robur Morningstar Debug\n\n"
message += f"Status code: {response.status_code}\n"
message += f"Content type: {response.headers.get('content-type')}\n"
message += f"Text length: {len(text)}\n\n"
message += "First 2500 chars:\n"
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

print(response.status_code)
print(text[:500])
