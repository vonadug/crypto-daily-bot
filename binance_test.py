import os
import time
import hmac
import hashlib
import requests

API_KEY = os.environ["BINANCE_API_KEY"]
API_SECRET = os.environ["BINANCE_API_SECRET"]

timestamp = int(time.time() * 1000)

query_string = f"timestamp={timestamp}"

signature = hmac.new(
    API_SECRET.encode(),
    query_string.encode(),
    hashlib.sha256
).hexdigest()

url = (
    "https://api.binance.com/api/v3/account?"
    + query_string
    + "&signature="
    + signature
)

headers = {
    "X-MBX-APIKEY": API_KEY
}

response = requests.get(url, headers=headers, timeout=30)

print("Status:", response.status_code)
print(response.text)
