import httpx
import json

url = "https://www.freelancer.com/api/projects/0.1/projects/40789413?full_description=true"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
resp = httpx.get(url, headers=headers, timeout=15.0)
print("Status:", resp.status_code)
data = resp.json().get("result", {})
print("Title:", data.get("title"))
print("Budget min:", data.get("budget", {}).get("minimum"))
print("Budget max:", data.get("budget", {}).get("maximum"))
print("Currency:", data.get("currency", {}).get("code"))
print("Bid count:", data.get("bid_stats", {}).get("bid_count"))
print("Owner ID:", data.get("owner_id"))
print("--- FULL DESCRIPTION ---")
print(data.get("description"))
